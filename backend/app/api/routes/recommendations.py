"""
Recommendation API routes.

Endpoints for:
- Personalized recommendations
- Recommendation explanations
- Alternative product suggestions
"""

import logging
import uuid
from typing import Optional, List, Dict, Any
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
    RecommendationResponse,
    ExplanationRequest,
    ExplanationResponse,
    AlternativesResponse,
    ProductSearchResult,
    ErrorResponse
)
from ...agents.services.qdrant_service import QdrantService
from ...agents.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

router = APIRouter()


# ==============================================================================
# Personalized Recommendations
# ==============================================================================

@router.get(
    "/{user_id}",
    response_model=RecommendationResponse,
    responses={404: {"model": ErrorResponse}}
)
async def get_recommendations(
    request: Request,
    user_id: str,
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(10, ge=1, le=50),
    include_reasons: bool = Query(True, description="Include recommendation reasons"),
    diversity: float = Query(0.3, ge=0.0, le=1.0, description="Diversity factor 0-1"),
    qdrant: QdrantService = Depends(get_qdrant_service),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    current_user: Optional[UserContext] = Depends(get_current_user),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    Get personalized product recommendations for a user.
    
    Uses collaborative filtering and content-based approaches:
    - User interaction history
    - User preferences/profile
    - Similar user behavior
    - Product embeddings
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    try:
        # Fetch user profile (sync method)
        user_data = qdrant.get_point(
            collection="user_profiles",
            point_id=user_id
        )
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )
        
        outer_user_payload = user_data.get("payload", {})
        user_payload = outer_user_payload.get("payload", outer_user_payload)  # Handle nested payload
        user_vector = user_data.get("vector", [])
        preferences = user_payload.get("preferences", {})
        
        # Build filters based on preferences and category
        filters = {}
        
        if category:
            filters["category"] = {"match": category}
        
        # Filter by preferred categories if set
        preferred_categories = preferences.get("preferred_categories", [])
        if preferred_categories and not category:
            filters["category"] = {"any": preferred_categories}
        
        # Price range filter
        price_pref = preferences.get("price_sensitivity")
        if price_pref == "budget":
            filters["price"] = {"lte": 100}
        elif price_pref == "mid_range":
            filters["price"] = {"gte": 50, "lte": 300}
        elif price_pref == "premium":
            filters["price"] = {"gte": 200}
        
        # Exclude brands
        excluded_brands = preferences.get("excluded_brands", [])
        if excluded_brands:
            filters["brand"] = {"not_any": excluded_brands}
        
        # Use user embedding for personalized search
        if user_vector:
            # Named vector handling
            search_vector = user_vector
            if isinstance(user_vector, dict):
                search_vector = user_vector.get("preferences_vector", user_vector.get("", []))
            
            if not search_vector:
                # Fallback: generate from preferences
                pref_text = " ".join([
                    " ".join(preferred_categories),
                    preferences.get("preferred_brands", ""),
                    preferences.get("style", "")
                ])
                if pref_text.strip():
                    search_vector = embedding_service.embed(pref_text)
                else:
                    search_vector = [0.0] * 384
        else:
            search_vector = [0.0] * 384
        
        # Get user's past interactions to avoid recommending viewed items (sync method)
        past_interactions = qdrant.scroll(
            collection="user_interactions",
            limit=100,
            filters={"user_id": {"match": user_id}},
            with_payload=True
        )
        
        viewed_product_ids = set()
        for i in past_interactions:
            outer_interaction = i.get("payload", {})
            inner_interaction = outer_interaction.get("payload", outer_interaction)
            if inner_interaction.get("product_id"):
                viewed_product_ids.add(inner_interaction.get("product_id"))
        
        # Search for recommendations using MMR for diversity (sync method)
        results = qdrant.mmr_search(
            collection="products",
            query_vector=search_vector,
            limit=limit + len(viewed_product_ids),  # Get extra to filter
            diversity=diversity,
            filters=filters if filters else None
        )
        
        # Format recommendations
        recommendations = []
        reasons_map = {}
        
        for result in results:
            product_id = result.get("id", "")
            
            # Skip already viewed products
            if product_id in viewed_product_ids:
                continue
            
            if len(recommendations) >= limit:
                break
            
            outer_payload = result.get("payload", {})
            payload = outer_payload.get("payload", outer_payload)  # Handle nested payload
            score = result.get("score", 0.0)
            
            product = ProductSearchResult(
                id=product_id,
                name=payload.get("title", payload.get("name", "Unknown")),
                description=payload.get("description"),
                price=payload.get("price", 0.0),
                original_price=payload.get("original_price"),
                category=payload.get("category", "Unknown"),
                subcategory=payload.get("subcategory"),
                brand=payload.get("brand"),
                rating=payload.get("rating_avg"),
                review_count=payload.get("review_count"),
                image_url=payload.get("image_url"),
                in_stock=payload.get("stock_status", "in_stock") == "in_stock",
                relevance_score=score
            )
            recommendations.append(product)
            
            # Generate recommendation reason
            if include_reasons:
                reasons = []
                
                if payload.get("category") in preferred_categories:
                    reasons.append(f"Matches your interest in {payload.get('category')}")
                
                if payload.get("rating_avg", 0) >= 4.5:
                    reasons.append(f"Highly rated ({payload.get('rating_avg')}/5)")
                
                if score > 0.8:
                    reasons.append("Strong match with your preferences")
                elif score > 0.6:
                    reasons.append("Good match with your preferences")
                
                brand = payload.get("brand")
                if brand and brand in preferences.get("preferred_brands", ""):
                    reasons.append(f"From brand you like: {brand}")
                
                if not reasons:
                    reasons.append("Recommended based on your profile")
                
                reasons_map[product_id] = reasons
        
        return RecommendationResponse(
            success=True,
            user_id=user_id,
            recommendations=recommendations,
            reasons=reasons_map if include_reasons else {},
            total=len(recommendations),
            request_id=request_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {str(e)}"
        )


# ==============================================================================
# Recommendation Explanation
# ==============================================================================

@router.post(
    "/explain",
    response_model=ExplanationResponse
)
async def explain_recommendation(
    request: Request,
    explanation_req: ExplanationRequest,
    qdrant: QdrantService = Depends(get_qdrant_service),
    current_user: Optional[UserContext] = Depends(get_current_user),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    Explain why a product was recommended to a user.
    
    Returns detailed reasoning including:
    - Similarity factors
    - User preference matches
    - Historical behavior patterns
    - Product characteristics
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    try:
        # Fetch user and product data (sync methods)
        user_data = qdrant.get_point(
            collection="user_profiles",
            point_id=explanation_req.user_id
        )
        
        product_data = qdrant.get_point(
            collection="products",
            point_id=explanation_req.product_id
        )
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {explanation_req.user_id} not found"
            )
        
        if not product_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {explanation_req.product_id} not found"
            )
        
        outer_user_payload = user_data.get("payload", {})
        outer_product_payload = product_data.get("payload", {})
        user_payload = outer_user_payload.get("payload", outer_user_payload)  # Handle nested payload
        product_payload = outer_product_payload.get("payload", outer_product_payload)  # Handle nested payload
        preferences = user_payload.get("preferences", {})
        
        # Analyze match factors
        factors = []
        factor_scores = {}
        
        # Category match
        preferred_cats = preferences.get("preferred_categories", [])
        product_cat = product_payload.get("category")
        if product_cat in preferred_cats:
            factors.append({
                "type": "category_match",
                "description": f"This product is in your preferred category: {product_cat}",
                "weight": 0.25
            })
            factor_scores["category_match"] = 1.0
        else:
            factor_scores["category_match"] = 0.3
        
        # Brand preference
        preferred_brands = preferences.get("preferred_brands", [])
        product_brand = product_payload.get("brand", "")
        # Handle both list and string formats
        if isinstance(preferred_brands, str):
            preferred_brands = [preferred_brands] if preferred_brands else []
        brand_match = product_brand and any(
            product_brand.lower() == b.lower() for b in preferred_brands
        )
        if brand_match:
            factors.append({
                "type": "brand_preference",
                "description": f"This product is from a brand you prefer: {product_brand}",
                "weight": 0.2
            })
            factor_scores["brand_preference"] = 1.0
        else:
            factor_scores["brand_preference"] = 0.5
        
        # Price sensitivity
        price_pref = preferences.get("price_sensitivity", "mid_range")
        product_price = product_payload.get("price", 0)
        
        price_match = False
        if price_pref == "budget" and product_price < 100:
            price_match = True
            factors.append({
                "type": "price_match",
                "description": f"Budget-friendly price at ${product_price}",
                "weight": 0.15
            })
        elif price_pref == "mid_range" and 50 <= product_price <= 300:
            price_match = True
            factors.append({
                "type": "price_match",
                "description": f"Price matches your mid-range preference at ${product_price}",
                "weight": 0.15
            })
        elif price_pref == "premium" and product_price >= 200:
            price_match = True
            factors.append({
                "type": "price_match",
                "description": f"Premium product at ${product_price}",
                "weight": 0.15
            })
        factor_scores["price_match"] = 1.0 if price_match else 0.4
        
        # Rating quality
        rating = product_payload.get("rating_avg", 0)
        if rating >= 4.5:
            factors.append({
                "type": "high_rating",
                "description": f"Highly rated product with {rating}/5 stars",
                "weight": 0.15
            })
            factor_scores["quality"] = 1.0
        elif rating >= 4.0:
            factors.append({
                "type": "good_rating",
                "description": f"Well-rated product with {rating}/5 stars",
                "weight": 0.1
            })
            factor_scores["quality"] = 0.8
        else:
            factor_scores["quality"] = 0.5
        
        # Analyze interaction history (sync method)
        interactions = qdrant.scroll(
            collection="user_interactions",
            limit=50,
            filters={"user_id": {"match": explanation_req.user_id}},
            with_payload=True
        )
        
        # Check if user has interacted with similar products
        similar_category_interactions = sum(
            1 for i in interactions
            if i.get("payload", {}).get("category") == product_cat
        )
        
        if similar_category_interactions > 3:
            factors.append({
                "type": "behavioral_pattern",
                "description": f"You've shown interest in {similar_category_interactions}+ similar products",
                "weight": 0.2
            })
            factor_scores["behavioral"] = 1.0
        else:
            factor_scores["behavioral"] = 0.5
        
        # Calculate overall confidence
        total_weight = sum(f.get("weight", 0) for f in factors)
        confidence_score = min(total_weight / 0.8, 1.0)  # Normalize to max 1.0
        
        # Generate summary explanation
        if confidence_score >= 0.7:
            summary = f"Strong recommendation - This {product_cat} from {product_brand or 'a trusted brand'} closely matches your preferences and browsing history."
        elif confidence_score >= 0.4:
            summary = f"Good match - This {product_cat} aligns with several of your preferences."
        else:
            summary = f"You might like - This {product_cat} was selected based on general similarity to your interests."
        
        return ExplanationResponse(
            success=True,
            user_id=explanation_req.user_id,
            product_id=explanation_req.product_id,
            summary=summary,
            factors=factors,
            factor_scores=factor_scores,
            confidence_score=round(confidence_score, 2),
            request_id=request_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error explaining recommendation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to explain recommendation: {str(e)}"
        )


# ==============================================================================
# Alternative Products
# ==============================================================================

@router.get(
    "/alternatives/{product_id}",
    response_model=AlternativesResponse
)
async def get_alternatives(
    request: Request,
    product_id: str,
    limit: int = Query(5, ge=1, le=20),
    criteria: str = Query("balanced", description="cheaper, better_rated, similar, balanced"),
    qdrant: QdrantService = Depends(get_qdrant_service),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    Get alternative products to the specified product.
    
    Alternatives are selected based on criteria:
    - cheaper: Lower-priced alternatives with similar features
    - better_rated: Higher-rated alternatives
    - similar: Most similar products regardless of price
    - balanced: Mix of price, rating, and similarity
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    try:
        # Get original product (sync method) - need vector for similarity search
        original = qdrant.get_point(
            collection="products",
            point_id=product_id,
            with_vector=True
        )
        
        if not original:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found"
            )
        
        outer_original_payload = original.get("payload", {})
        original_payload = outer_original_payload.get("payload", outer_original_payload)  # Handle nested payload
        original_vector = original.get("vector", [])
        original_price = original_payload.get("price", 0)
        original_rating = original_payload.get("rating_avg", 0)
        original_category = original_payload.get("category")
        
        # Handle named vectors
        search_vector = original_vector
        if isinstance(original_vector, dict):
            search_vector = original_vector.get("text_vector", original_vector.get("", []))
        
        if not search_vector:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product has no embedding vector"
            )
        
        # Build filters based on criteria
        filters = {"category": {"match": original_category}}
        
        if criteria == "cheaper":
            filters["price"] = {"lt": original_price}
        elif criteria == "better_rated":
            filters["rating_avg"] = {"gt": original_rating}
        
        # Search for alternatives (sync method)
        results = qdrant.mmr_search(
            collection="products",
            query_vector=search_vector,
            limit=limit * 2 + 1,  # Get extra for filtering
            diversity=0.4,
            filters=filters
        )
        
        # Score and rank alternatives
        alternatives = []
        
        for result in results:
            if result.get("id") == product_id:
                continue
            
            outer_payload = result.get("payload", {})
            payload = outer_payload.get("payload", outer_payload)  # Handle nested payload
            alt_price = payload.get("price", 0)
            alt_rating = payload.get("rating_avg", 0)
            similarity = result.get("score", 0)
            
            # Calculate composite score based on criteria
            if criteria == "cheaper":
                # Prioritize price savings with similarity
                price_factor = max(0, (original_price - alt_price) / original_price) if original_price > 0 else 0
                composite_score = 0.6 * price_factor + 0.4 * similarity
                reason = f"${alt_price} - Save ${original_price - alt_price:.2f} ({price_factor*100:.0f}% off)"
            elif criteria == "better_rated":
                # Prioritize rating improvement
                rating_factor = (alt_rating - original_rating) / 5 if original_rating > 0 else 0
                composite_score = 0.6 * max(0, rating_factor * 5) + 0.4 * similarity
                reason = f"{alt_rating}/5 stars - {alt_rating - original_rating:+.1f} rating improvement"
            elif criteria == "similar":
                # Pure similarity
                composite_score = similarity
                reason = f"{similarity*100:.0f}% similar"
            else:  # balanced
                # Balance all factors
                price_factor = 1 - (abs(alt_price - original_price) / max(original_price, 1))
                rating_factor = alt_rating / 5
                composite_score = 0.4 * similarity + 0.3 * rating_factor + 0.3 * max(0, price_factor)
                reason = f"${alt_price}, {alt_rating}/5 stars, {similarity*100:.0f}% similar"
            
            alternatives.append({
                "product": ProductSearchResult(
                    id=result.get("id", ""),
                    name=payload.get("title", payload.get("name", "Unknown")),
                    description=payload.get("description"),
                    price=alt_price,
                    original_price=payload.get("original_price"),
                    category=payload.get("category", "Unknown"),
                    subcategory=payload.get("subcategory"),
                    brand=payload.get("brand"),
                    rating=alt_rating,
                    review_count=payload.get("review_count"),
                    image_url=payload.get("image_url"),
                    in_stock=payload.get("stock_status", "in_stock") == "in_stock",
                    relevance_score=similarity
                ),
                "composite_score": composite_score,
                "reason": reason
            })
        
        # Sort by composite score and take top results
        alternatives.sort(key=lambda x: x["composite_score"], reverse=True)
        alternatives = alternatives[:limit]
        
        # Format response
        return AlternativesResponse(
            success=True,
            original_product_id=product_id,
            criteria=criteria,
            alternatives=[a["product"] for a in alternatives],
            reasons={a["product"].id: a["reason"] for a in alternatives},
            total=len(alternatives),
            request_id=request_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching alternatives: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch alternatives: {str(e)}"
        )
