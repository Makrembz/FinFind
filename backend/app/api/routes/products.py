"""
Product management API routes.

Endpoints for:
- Product details
- Product reviews
- User-product interactions
- Similar products
"""

import logging
import uuid
import time
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from ..dependencies import (
    get_qdrant_service,
    get_embedding_service,
    get_current_user,
    check_rate_limit,
    UserContext
)
from ..models import (
    ProductDetail,
    ProductResponse,
    ProductSearchResult,
    ProductReview,
    ReviewsResponse,
    InteractionRequest,
    ProductAttributes,
    ErrorResponse
)
from ...agents.services.qdrant_service import QdrantService
from ...agents.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

router = APIRouter()


# ==============================================================================
# Product Detail Endpoints
# ==============================================================================

@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    responses={404: {"model": ErrorResponse}}
)
async def get_product(
    request: Request,
    product_id: str,
    include_similar: bool = Query(True, description="Include similar products"),
    similar_limit: int = Query(5, ge=1, le=10),
    qdrant: QdrantService = Depends(get_qdrant_service),
    current_user: Optional[UserContext] = Depends(get_current_user),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    Get detailed product information.
    
    Returns complete product details including:
    - Basic info (name, description, price)
    - Attributes (color, size, specifications)
    - Reviews summary
    - Optionally includes similar products
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    try:
        # Fetch product from Qdrant (sync method)
        product_data = qdrant.get_point(
            collection="products",
            point_id=product_id
        )
        
        if not product_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found"
            )
        
        outer_payload = product_data.get("payload", {})
        # Handle nested payload structure
        payload = outer_payload.get("payload", outer_payload)
        vector = product_data.get("vector", [])
        
        # Build product detail
        attributes_data = payload.get("attributes", {})
        product = ProductDetail(
            id=product_id,
            name=payload.get("title", payload.get("name", "Unknown")),
            description=payload.get("description", ""),
            category=payload.get("category", "Unknown"),
            subcategory=payload.get("subcategory"),
            brand=payload.get("brand", "Unknown"),
            price=payload.get("price", 0.0),
            original_price=payload.get("original_price"),
            currency=payload.get("currency", "USD"),
            attributes=ProductAttributes(
                color=attributes_data.get("color"),
                size=attributes_data.get("size"),
                material=attributes_data.get("material"),
                brand=attributes_data.get("brand"),
                model=attributes_data.get("model"),
                weight=attributes_data.get("weight"),
                dimensions=attributes_data.get("dimensions"),
                extra={k: v for k, v in attributes_data.items() 
                       if k not in ["color", "size", "material", "brand", "model", "weight", "dimensions"]}
            ),
            image_url=payload.get("image_url", ""),
            image_urls=payload.get("image_urls") or [],
            in_stock=payload.get("stock_status", "in_stock") == "in_stock",
            stock_quantity=payload.get("stock_quantity"),
            payment_options=payload.get("payment_options") or [],
            rating_avg=payload.get("rating_avg", 0.0),
            review_count=payload.get("review_count", 0),
            tags=payload.get("tags") or [],
            created_at=datetime.fromisoformat(
                payload.get("created_at", datetime.utcnow().isoformat())
            ),
            updated_at=datetime.fromisoformat(payload["updated_at"]) 
                if payload.get("updated_at") else None
        )
        
        # Get similar products if requested
        similar_products = []
        if include_similar and vector:
            # Handle both named vectors and single vectors
            search_vector = vector
            if isinstance(vector, dict):
                search_vector = vector.get("text_vector", vector.get("", []))
            
            if search_vector:
                similar_results = qdrant.semantic_search(
                    collection="products",
                    query_vector=search_vector,
                    limit=similar_limit + 1,  # +1 to exclude self
                    score_threshold=0.5
                )
                
                for result in similar_results:
                    if result.get("id") != product_id:
                        outer_payload = result.get("payload", {})
                        p = outer_payload.get("payload", outer_payload)  # Handle nested payload
                        similar_products.append(ProductSearchResult(
                            id=result.get("id", ""),
                            name=p.get("title", p.get("name", "Unknown")),
                            description=p.get("description"),
                            price=p.get("price", 0.0),
                            original_price=p.get("original_price"),
                            category=p.get("category", "Unknown"),
                            subcategory=p.get("subcategory"),
                            brand=p.get("brand"),
                            rating=p.get("rating_avg"),
                            review_count=p.get("review_count"),
                            image_url=p.get("image_url"),
                            in_stock=p.get("stock_status", "in_stock") == "in_stock",
                            relevance_score=result.get("score", 0.0)
                        ))
                        
                        if len(similar_products) >= similar_limit:
                            break
        
        return ProductResponse(
            success=True,
            product=product,
            similar_products=similar_products,
            request_id=request_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching product: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch product: {str(e)}"
        )


# ==============================================================================
# Product Reviews Endpoints
# ==============================================================================

@router.get(
    "/{product_id}/reviews",
    response_model=ReviewsResponse
)
async def get_product_reviews(
    request: Request,
    product_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    sort_by: str = Query("newest", description="newest, helpful, rating_high, rating_low"),
    qdrant: QdrantService = Depends(get_qdrant_service),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    Get reviews for a product.
    
    Returns paginated reviews with:
    - Rating distribution
    - Average rating
    - Individual reviews with user info
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    try:
        # Build filters
        filters = {"product_id": {"match": product_id}}
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Fetch reviews from Qdrant (sync method)
        results = qdrant.scroll(
            collection="reviews",
            limit=page_size,
            offset=offset,
            filters=filters,
            with_payload=True
        )
        
        # Format reviews
        reviews = []
        rating_counts = {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0}
        total_rating = 0.0
        
        for result in results:
            outer_payload = result.get("payload", {})
            payload = outer_payload.get("payload", outer_payload)  # Handle nested payload
            rating = payload.get("rating", 0)
            
            # Count ratings
            rating_key = str(int(rating))
            if rating_key in rating_counts:
                rating_counts[rating_key] += 1
            total_rating += rating
            
            reviews.append(ProductReview(
                id=result.get("id", ""),
                user_id=payload.get("user_id", ""),
                product_id=product_id,
                rating=rating,
                title=payload.get("title"),
                content=payload.get("text", payload.get("content", "")),
                helpful_count=payload.get("helpful_count", 0),
                verified_purchase=payload.get("verified_purchase", False),
                created_at=datetime.fromisoformat(
                    payload.get("created_at", datetime.utcnow().isoformat())
                ),
                user_name=payload.get("user_name")
            ))
        
        # Sort reviews
        if sort_by == "helpful":
            reviews.sort(key=lambda r: r.helpful_count, reverse=True)
        elif sort_by == "rating_high":
            reviews.sort(key=lambda r: r.rating, reverse=True)
        elif sort_by == "rating_low":
            reviews.sort(key=lambda r: r.rating)
        else:  # newest
            reviews.sort(key=lambda r: r.created_at, reverse=True)
        
        # Calculate average
        avg_rating = total_rating / len(reviews) if reviews else 0.0
        
        return ReviewsResponse(
            success=True,
            product_id=product_id,
            reviews=reviews,
            total=len(reviews) + offset,  # Approximate
            average_rating=round(avg_rating, 2),
            rating_distribution=rating_counts,
            page=page,
            page_size=page_size,
            request_id=request_id
        )
        
    except Exception as e:
        logger.error(f"Error fetching reviews: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch reviews: {str(e)}"
        )


# ==============================================================================
# Product Interaction Endpoints
# ==============================================================================

@router.post(
    "/{product_id}/interact",
    status_code=status.HTTP_201_CREATED
)
async def log_product_interaction(
    request: Request,
    product_id: str,
    interaction: InteractionRequest,
    qdrant: QdrantService = Depends(get_qdrant_service),
    current_user: Optional[UserContext] = Depends(get_current_user),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    Log a user interaction with this product.
    
    Tracks user behavior for:
    - Recommendations
    - Analytics
    - Personalization
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    # Get user_id from current user or metadata
    user_id = None
    if current_user:
        user_id = current_user.user_id
    elif interaction.metadata and interaction.metadata.get("user_id"):
        user_id = interaction.metadata["user_id"]
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID required for interaction logging"
        )
    
    try:
        interaction_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        # Create interaction record
        payload = {
            "user_id": user_id,
            "product_id": product_id,
            "interaction_type": interaction.interaction_type.value,
            "timestamp": timestamp.isoformat(),
            "metadata": interaction.metadata or {},
            "session_id": interaction.session_id
        }
        
        # Store in Qdrant (sync method)
        qdrant.upsert_point(
            collection="user_interactions",
            point_id=interaction_id,
            vector=[0.0] * 384,  # Placeholder for filter-only collection
            payload=payload
        )
        
        logger.info(
            f"Product interaction: product={product_id}, user={user_id}, "
            f"type={interaction.interaction_type.value}"
        )
        
        return {
            "success": True,
            "interaction_id": interaction_id,
            "product_id": product_id,
            "request_id": request_id
        }
        
    except Exception as e:
        logger.error(f"Error logging product interaction: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log interaction: {str(e)}"
        )


# ==============================================================================
# Similar Products Endpoint
# ==============================================================================

@router.get(
    "/{product_id}/similar",
    response_model=List[ProductSearchResult]
)
async def get_similar_products(
    request: Request,
    product_id: str,
    limit: int = Query(10, ge=1, le=20),
    same_category: bool = Query(False, description="Only same category"),
    price_range: Optional[str] = Query(None, description="lower, similar, higher"),
    qdrant: QdrantService = Depends(get_qdrant_service),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    Get products similar to this one.
    
    Uses vector similarity to find:
    - Visually similar products
    - Products with similar descriptions
    - Products in related categories
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    try:
        # Get original product (sync method)
        product_data = qdrant.get_point(
            collection="products",
            point_id=product_id
        )
        
        if not product_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found"
            )
        
        payload = product_data.get("payload", {})
        vector = product_data.get("vector", [])
        original_price = payload.get("price", 0.0)
        original_category = payload.get("category")
        
        # Handle named vectors
        search_vector = vector
        if isinstance(vector, dict):
            search_vector = vector.get("text_vector", vector.get("", []))
        
        if not search_vector:
            return []
        
        # Build filters
        filters = {}
        
        if same_category and original_category:
            filters["category"] = {"match": original_category}
        
        if price_range and original_price > 0:
            if price_range == "lower":
                filters["price"] = {"lte": original_price * 0.8}
            elif price_range == "higher":
                filters["price"] = {"gte": original_price * 1.2}
            elif price_range == "similar":
                filters["price"] = {
                    "gte": original_price * 0.8,
                    "lte": original_price * 1.2
                }
        
        # Search for similar products (sync method)
        results = qdrant.mmr_search(
            collection="products",
            query_vector=search_vector,
            limit=limit + 1,  # +1 to exclude self
            score_threshold=0.4,
            diversity=0.3,
            filters=filters if filters else None
        )
        
        # Format results
        similar = []
        for result in results:
            if result.get("id") != product_id:
                p = result.get("payload", {})
                similar.append(ProductSearchResult(
                    id=result.get("id", ""),
                    name=p.get("title", p.get("name", "Unknown")),
                    description=p.get("description"),
                    price=p.get("price", 0.0),
                    original_price=p.get("original_price"),
                    category=p.get("category", "Unknown"),
                    subcategory=p.get("subcategory"),
                    brand=p.get("brand"),
                    rating=p.get("rating_avg"),
                    review_count=p.get("review_count"),
                    image_url=p.get("image_url"),
                    in_stock=p.get("stock_status", "in_stock") == "in_stock",
                    relevance_score=result.get("score", 0.0)
                ))
                
                if len(similar) >= limit:
                    break
        
        return similar
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching similar products: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch similar products: {str(e)}"
        )
