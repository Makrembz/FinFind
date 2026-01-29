"""
Search API routes.

Provides endpoints for product search with various filters and modes.
"""

import logging
import uuid
import time
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from ..dependencies import (
    get_qdrant_service,
    get_embedding_service,
    get_current_user,
    check_rate_limit,
    UserContext
)
from ...agents.services.qdrant_service import QdrantService
from ...agents.services.embedding_service import EmbeddingService
from ...agents.services.ranking_service import (
    ProductRankingService,
    RankingStrategy,
    UserContext as RankingUserContext,
    rank_search_results
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ==============================================================================
# Request/Response Models
# ==============================================================================

class SearchFilters(BaseModel):
    """Search filter parameters."""
    min_price: Optional[float] = Field(default=None, ge=0)
    max_price: Optional[float] = Field(default=None, ge=0)
    categories: Optional[List[str]] = None
    brands: Optional[List[str]] = None
    min_rating: Optional[float] = Field(default=None, ge=0, le=5)
    in_stock: Optional[bool] = None


class SearchRequest(BaseModel):
    """Text search request."""
    query: str = Field(..., min_length=1, max_length=500)
    filters: Optional[SearchFilters] = None
    limit: int = Field(default=10, ge=1, le=50)
    offset: int = Field(default=0, ge=0)
    use_mmr: bool = Field(default=True, description="Use MMR for diverse results")
    diversity: float = Field(default=0.3, ge=0.0, le=1.0)
    score_threshold: float = Field(default=0.3, ge=0.0, le=1.0)
    ranking_strategy: str = Field(
        default="balanced",
        description="Ranking strategy: relevance, popularity, balanced, personalized, value"
    )
    apply_ranking: bool = Field(
        default=True,
        description="Apply intelligent ranking to results"
    )


class ProductResult(BaseModel):
    """Product search result."""
    id: str
    name: str
    description: Optional[str] = None
    price: float
    category: str
    brand: Optional[str] = None
    rating: Optional[float] = None
    image_url: Optional[str] = None
    relevance_score: float
    
    # Ranking info
    ranking_score: Optional[float] = None
    rank: Optional[int] = None
    score_breakdown: Optional[dict] = None
    
    # Explanation
    match_reason: Optional[str] = None
    ranking_explanation: Optional[str] = None


class SearchResponse(BaseModel):
    """Search response."""
    success: bool
    query: str
    products: List[ProductResult]
    total_results: int
    search_time_ms: float
    filters_applied: dict
    request_id: str


class SuggestResponse(BaseModel):
    """Search suggestion response."""
    suggestions: List[str]
    request_id: str


# ==============================================================================
# Search Endpoints
# ==============================================================================

@router.post("/products", response_model=SearchResponse)
async def search_products(
    request: Request,
    body: SearchRequest,
    qdrant: QdrantService = Depends(get_qdrant_service),
    embedder: EmbeddingService = Depends(get_embedding_service),
    user: Optional[UserContext] = Depends(get_current_user),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    Search for products using semantic search.
    
    Performs vector similarity search on product descriptions and names,
    with optional filters and MMR diversity.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    start_time = time.time()
    
    try:
        # Generate query embedding (sync method)
        query_embedding = embedder.embed(body.query)
        
        # Build Qdrant filters - use "range" wrapper for numeric conditions
        filters = {}
        if body.filters:
            if body.filters.min_price is not None or body.filters.max_price is not None:
                price_range = {}
                if body.filters.min_price is not None:
                    price_range["gte"] = body.filters.min_price
                if body.filters.max_price is not None:
                    price_range["lte"] = body.filters.max_price
                filters["price"] = {"range": price_range}
            
            if body.filters.categories:
                filters["category"] = {"any": body.filters.categories}
            
            if body.filters.brands:
                filters["brand"] = {"any": body.filters.brands}
            
            if body.filters.min_rating is not None:
                filters["rating_avg"] = {"range": {"gte": body.filters.min_rating}}
            
            if body.filters.in_stock is not None:
                filters["stock_status"] = {"match": "in_stock" if body.filters.in_stock else "out_of_stock"}
        
        # Perform search (sync methods)
        if body.use_mmr:
            results = qdrant.mmr_search(
                collection="products",
                query_vector=query_embedding,
                limit=body.limit * 2 if body.apply_ranking else body.limit,  # Fetch more for ranking
                diversity=body.diversity,
                filters=filters if filters else None,
                vector_name="text"  # Use text embedding vector
            )
        else:
            results = qdrant.semantic_search(
                collection="products",
                query_vector=query_embedding,
                limit=body.limit * 2 if body.apply_ranking else body.limit,  # Fetch more for ranking
                score_threshold=body.score_threshold,
                filters=filters if filters else None,
                vector_name="text"  # Use text embedding vector
            )
        
        # Apply intelligent ranking if enabled
        if body.apply_ranking and results:
            # Build user context for personalized ranking with financial profile
            ranking_context = None
            if user:
                # Try to fetch user's financial profile from Qdrant
                financial_profile = {}
                try:
                    user_profile = qdrant.get_user_profile(user.user_id)
                    if user_profile:
                        profile_payload = user_profile.get("payload", {})
                        financial_ctx = profile_payload.get("financial_context", {})
                        financial_profile = {
                            "monthly_income": financial_ctx.get("monthly_income"),
                            "monthly_budget": financial_ctx.get("monthly_budget"),
                            "savings_goal": financial_ctx.get("savings_goal"),
                            "risk_tolerance": financial_ctx.get("risk_tolerance", "moderate"),
                        }
                        # Get user preferences
                        preferences = profile_payload.get("preferences", {})
                except Exception as e:
                    logger.warning(f"Could not fetch user profile for ranking: {e}")
                
                ranking_context = {
                    "user_id": user.user_id,
                    "budget_max": body.filters.max_price if body.filters else None,
                    "budget_min": body.filters.min_price if body.filters else None,
                    "monthly_income": financial_profile.get("monthly_income"),
                    "monthly_budget": financial_profile.get("monthly_budget"),
                    "savings_goal": financial_profile.get("savings_goal"),
                    "risk_tolerance": financial_profile.get("risk_tolerance", "moderate"),
                    "preferred_categories": body.filters.categories if body.filters and body.filters.categories else [],
                    "preferred_brands": body.filters.brands if body.filters and body.filters.brands else [],
                    "price_sensitivity": 0.5
                }
            
            # Get ranking strategy
            try:
                strategy = RankingStrategy(body.ranking_strategy)
            except ValueError:
                strategy = RankingStrategy.BALANCED
            
            # Rank results
            ranked_results = rank_search_results(
                products=results,
                strategy=strategy,
                user_context=ranking_context,
                diversity_factor=body.diversity if body.use_mmr else 0,
                query=body.query
            )
            
            # Limit to requested count after ranking
            results = ranked_results[:body.limit]
        
        # Format results
        products = []
        for idx, result in enumerate(results):
            outer_payload = result.get("payload", {})
            # Handle nested payload structure from data generation
            payload = outer_payload.get("payload", outer_payload)
            products.append(ProductResult(
                id=result.get("id", ""),
                name=payload.get("title", payload.get("name", "Unknown")),
                description=payload.get("description"),
                price=payload.get("price", 0.0),
                category=payload.get("category", "Unknown"),
                brand=payload.get("brand"),
                rating=payload.get("rating_avg", payload.get("rating")),
                image_url=payload.get("image_url"),
                relevance_score=result.get("score", 0.0),
                ranking_score=result.get("ranking_score"),
                rank=idx + 1,
                score_breakdown=result.get("score_breakdown"),
                match_reason=_generate_match_reason(body.query, payload),
                ranking_explanation=result.get("ranking_explanation", "")
            ))
        
        search_time = (time.time() - start_time) * 1000
        
        return SearchResponse(
            success=True,
            query=body.query,
            products=products,
            total_results=len(products),
            search_time_ms=search_time,
            filters_applied=body.filters.dict() if body.filters else {},
            request_id=request_id
        )
        
    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/products", response_model=SearchResponse)
async def search_products_get(
    request: Request,
    q: str = Query(..., min_length=1, max_length=500, description="Search query"),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    category: Optional[str] = Query(None),
    brand: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    qdrant: QdrantService = Depends(get_qdrant_service),
    embedder: EmbeddingService = Depends(get_embedding_service),
    user: Optional[UserContext] = Depends(get_current_user),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    Search for products using GET request.
    
    Simpler interface for direct URL-based searches.
    """
    # Convert to SearchRequest
    filters = SearchFilters(
        min_price=min_price,
        max_price=max_price,
        categories=[category] if category else None,
        brands=[brand] if brand else None
    )
    
    body = SearchRequest(
        query=q,
        filters=filters,
        limit=limit
    )
    
    return await search_products(
        request=request,
        body=body,
        qdrant=qdrant,
        embedder=embedder,
        user=user,
        _rate_limit=_rate_limit
    )


@router.get("/suggest", response_model=SuggestResponse)
async def search_suggestions(
    request: Request,
    q: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(5, ge=1, le=10),
    qdrant: QdrantService = Depends(get_qdrant_service),
    embedder: EmbeddingService = Depends(get_embedding_service),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    Get search suggestions based on partial query.
    
    Returns related search terms for autocomplete.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    try:
        # Generate embedding for partial query (sync method)
        query_embedding = embedder.embed(q)
        
        # Search for similar products (sync method)
        results = qdrant.semantic_search(
            collection="products",
            query_vector=query_embedding,
            limit=limit * 2,  # Get more to extract unique names
            score_threshold=0.3,
            vector_name="text"  # Use text embedding vector
        )
        
        # Extract unique product names/categories as suggestions
        suggestions = []
        seen = set()
        
        for result in results:
            outer_payload = result.get("payload", {})
            # Handle nested payload structure
            payload = outer_payload.get("payload", outer_payload)
            name = payload.get("title", payload.get("name", ""))
            category = payload.get("category", "")
            
            # Add product name
            if name and name not in seen:
                suggestions.append(name)
                seen.add(name)
            
            # Add category
            if category and category not in seen and len(suggestions) < limit:
                suggestions.append(category)
                seen.add(category)
            
            if len(suggestions) >= limit:
                break
        
        return SuggestResponse(
            suggestions=suggestions[:limit],
            request_id=request_id
        )
        
    except Exception as e:
        logger.error(f"Suggestion error: {e}")
        return SuggestResponse(
            suggestions=[],
            request_id=request_id
        )


@router.get("/categories")
async def get_categories(
    qdrant: QdrantService = Depends(get_qdrant_service)
):
    """
    Get all available product categories.
    """
    try:
        # Scroll through products to get unique categories (sync method)
        results = qdrant.scroll(
            collection="products",
            limit=1000,
            with_payload=True
        )
        
        categories = set()
        for result in results:
            outer_payload = result.get("payload", {})
            # Handle nested payload structure
            payload = outer_payload.get("payload", outer_payload)
            category = payload.get("category")
            if category:
                categories.add(category)
        
        return {
            "categories": sorted(list(categories))
        }
        
    except Exception as e:
        logger.error(f"Categories error: {e}")
        return {"categories": []}


@router.get("/brands")
async def get_brands(
    category: Optional[str] = Query(None),
    qdrant: QdrantService = Depends(get_qdrant_service)
):
    """
    Get available brands, optionally filtered by category.
    """
    try:
        filters = None
        if category:
            filters = {"category": {"match": category}}
        
        results = qdrant.scroll(
            collection="products",
            limit=1000,
            with_payload=True,
            filters=filters
        )
        
        brands = set()
        for result in results:
            outer_payload = result.get("payload", {})
            # Handle nested payload structure
            payload = outer_payload.get("payload", outer_payload)
            brand = payload.get("brand")
            if brand:
                brands.add(brand)
        
        return {
            "brands": sorted(list(brands))
        }
        
    except Exception as e:
        logger.error(f"Brands error: {e}")
        return {"brands": []}


# ==============================================================================
# Helper Functions
# ==============================================================================

def _generate_match_reason(query: str, payload: dict) -> str:
    """Generate a human-readable match reason."""
    name = payload.get("title", payload.get("name", "")).lower()
    category = payload.get("category", "").lower()
    description = payload.get("description", "").lower()
    query_lower = query.lower()
    
    reasons = []
    
    # Check for direct matches
    query_words = query_lower.split()
    for word in query_words:
        if len(word) > 2:
            if word in name:
                reasons.append(f"Name contains '{word}'")
            elif word in category:
                reasons.append(f"Category: {payload.get('category', '')}")
            elif word in description:
                reasons.append(f"Description matches")
    
    if not reasons:
        reasons.append("Semantic similarity match")
    
    return "; ".join(reasons[:2])
