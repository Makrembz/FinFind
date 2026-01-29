"""
User management API routes.

Endpoints for:
- User profile management
- Financial profile
- Interaction history
- Preferences
"""

import logging
import uuid
import time
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel

from ..dependencies import (
    get_qdrant_service,
    get_embedding_service,
    get_current_user,
    check_rate_limit,
    UserContext
)
from ..models import (
    UserProfile,
    UserProfileUpdate,
    UserProfileResponse,
    UserInteraction,
    InteractionRequest,
    InteractionHistoryResponse,
    FinancialProfile,
    UserPreferences,
    ErrorResponse
)
from ...agents.services.qdrant_service import QdrantService
from ...agents.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

router = APIRouter()


# ==============================================================================
# User Profile Endpoints
# ==============================================================================

@router.get(
    "/{user_id}/profile",
    response_model=UserProfileResponse,
    responses={404: {"model": ErrorResponse}}
)
async def get_user_profile(
    request: Request,
    user_id: str,
    qdrant: QdrantService = Depends(get_qdrant_service),
    current_user: Optional[UserContext] = Depends(get_current_user),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    Get user financial profile and preferences.
    
    Retrieves the complete user profile including:
    - Financial information (income, budget, credit score range)
    - Shopping preferences
    - Favorite categories and brands
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    try:
        # Fetch user from Qdrant (sync method)
        user_data = qdrant.get_point(
            collection="user_profiles",
            point_id=user_id
        )
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )
        
        outer_payload = user_data.get("payload", {})
        payload = outer_payload.get("payload", outer_payload)  # Handle nested payload
        
        # Build profile from payload
        # Extract financial context if present
        financial_context = payload.get("financial_context", {})
        preferences = payload.get("preferences", {})
        
        # Convert price_sensitivity and quality_preference to strings if they are floats
        price_sensitivity = preferences.get("price_sensitivity", payload.get("price_sensitivity"))
        if isinstance(price_sensitivity, (int, float)):
            if price_sensitivity < 0.33:
                price_sensitivity = "low"
            elif price_sensitivity < 0.66:
                price_sensitivity = "medium"
            else:
                price_sensitivity = "high"
        
        quality_preference = preferences.get("quality_preference", payload.get("quality_preference"))
        if isinstance(quality_preference, (int, float)):
            if quality_preference < 0.33:
                quality_preference = "basic"
            elif quality_preference < 0.66:
                quality_preference = "standard"
            else:
                quality_preference = "premium"
        
        profile = UserProfile(
            user_id=user_id,
            email=payload.get("email"),
            name=payload.get("name", payload.get("persona_type", "Unknown")),
            financial_profile=FinancialProfile(
                monthly_income=financial_context.get("monthly_income", payload.get("monthly_income")),
                monthly_budget=payload.get("budget_max", payload.get("monthly_budget")),
                credit_score_range=financial_context.get("credit_score_range", payload.get("credit_score_range")),
                preferred_payment_methods=financial_context.get("preferred_payment_methods", payload.get("preferred_payment_methods", [])),
                risk_tolerance=financial_context.get("risk_tolerance", payload.get("risk_tolerance")),
                savings_goal=financial_context.get("savings_goal", payload.get("savings_goal"))
            ),
            preferences=UserPreferences(
                favorite_categories=preferences.get("categories", payload.get("favorite_categories", [])),
                favorite_brands=preferences.get("brands", payload.get("favorite_brands", [])),
                price_sensitivity=price_sensitivity if isinstance(price_sensitivity, str) else None,
                quality_preference=quality_preference if isinstance(quality_preference, str) else None,
                eco_friendly=preferences.get("eco_friendly", payload.get("eco_friendly", False)),
                local_preference=preferences.get("local_preference", payload.get("local_preference", False))
            ),
            created_at=datetime.fromisoformat(payload.get("created_at", datetime.utcnow().isoformat())),
            updated_at=datetime.fromisoformat(payload["updated_at"]) if payload.get("updated_at") else None
        )
        
        return UserProfileResponse(
            success=True,
            profile=profile,
            request_id=request_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user profile: {str(e)}"
        )


@router.put(
    "/{user_id}/profile",
    response_model=UserProfileResponse,
    responses={404: {"model": ErrorResponse}}
)
async def update_user_profile(
    request: Request,
    user_id: str,
    update: UserProfileUpdate,
    qdrant: QdrantService = Depends(get_qdrant_service),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    current_user: Optional[UserContext] = Depends(get_current_user),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    Update user profile.
    
    Updates the user's:
    - Name
    - Financial profile (income, budget, payment methods)
    - Shopping preferences
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    try:
        # Fetch existing user (sync method)
        existing = qdrant.get_point(
            collection="user_profiles",
            point_id=user_id
        )
        
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )
        
        payload = existing.get("payload", {})
        
        # Update fields
        if update.name is not None:
            payload["name"] = update.name
        
        if update.financial_profile is not None:
            fp = update.financial_profile
            if fp.monthly_income is not None:
                payload["monthly_income"] = fp.monthly_income
            if fp.monthly_budget is not None:
                payload["monthly_budget"] = fp.monthly_budget
            if fp.credit_score_range is not None:
                payload["credit_score_range"] = fp.credit_score_range
            if fp.preferred_payment_methods:
                payload["preferred_payment_methods"] = fp.preferred_payment_methods
            if fp.risk_tolerance is not None:
                payload["risk_tolerance"] = fp.risk_tolerance
            if fp.savings_goal is not None:
                payload["savings_goal"] = fp.savings_goal
        
        if update.preferences is not None:
            prefs = update.preferences
            if prefs.favorite_categories:
                payload["favorite_categories"] = prefs.favorite_categories
            if prefs.favorite_brands:
                payload["favorite_brands"] = prefs.favorite_brands
            if prefs.price_sensitivity is not None:
                payload["price_sensitivity"] = prefs.price_sensitivity
            if prefs.quality_preference is not None:
                payload["quality_preference"] = prefs.quality_preference
            payload["eco_friendly"] = prefs.eco_friendly
            payload["local_preference"] = prefs.local_preference
        
        payload["updated_at"] = datetime.utcnow().isoformat()
        
        # Generate new embedding based on updated preferences (sync method)
        preference_text = _build_user_preference_text(payload)
        new_embedding = embedding_service.embed(preference_text)
        
        # Update in Qdrant (sync method)
        qdrant.upsert_point(
            collection="user_profiles",
            point_id=user_id,
            vector=new_embedding,
            payload=payload
        )
        
        # Return updated profile
        # Handle price_sensitivity conversion (might be float in old data)
        price_sensitivity = payload.get("price_sensitivity")
        if isinstance(price_sensitivity, (int, float)):
            if price_sensitivity <= 0.33:
                price_sensitivity = "low"
            elif price_sensitivity <= 0.66:
                price_sensitivity = "medium"
            else:
                price_sensitivity = "high"
        
        profile = UserProfile(
            user_id=user_id,
            email=payload.get("email"),
            name=payload.get("name"),
            financial_profile=FinancialProfile(
                monthly_income=payload.get("monthly_income"),
                monthly_budget=payload.get("monthly_budget"),
                credit_score_range=payload.get("credit_score_range"),
                preferred_payment_methods=payload.get("preferred_payment_methods", []),
                risk_tolerance=payload.get("risk_tolerance"),
                savings_goal=payload.get("savings_goal")
            ),
            preferences=UserPreferences(
                favorite_categories=payload.get("favorite_categories", []),
                favorite_brands=payload.get("favorite_brands", []),
                price_sensitivity=price_sensitivity,
                quality_preference=payload.get("quality_preference"),
                eco_friendly=payload.get("eco_friendly", False),
                local_preference=payload.get("local_preference", False)
            ),
            created_at=datetime.fromisoformat(payload.get("created_at", datetime.utcnow().isoformat())),
            updated_at=datetime.fromisoformat(payload["updated_at"])
        )
        
        return UserProfileResponse(
            success=True,
            profile=profile,
            request_id=request_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user profile: {str(e)}"
        )


# ==============================================================================
# Interaction History Endpoints
# ==============================================================================

@router.get(
    "/{user_id}/interactions",
    response_model=InteractionHistoryResponse
)
async def get_user_interactions(
    request: Request,
    user_id: str,
    interaction_type: Optional[str] = Query(None, description="Filter by interaction type"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    qdrant: QdrantService = Depends(get_qdrant_service),
    current_user: Optional[UserContext] = Depends(get_current_user),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    Get user interaction history.
    
    Returns the user's interactions with products including:
    - Views, clicks, cart additions
    - Purchases
    - Reviews and wishlist items
    
    Can be filtered by interaction type.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    try:
        # Build filters
        filters = {"user_id": {"match": user_id}}
        if interaction_type:
            filters["interaction_type"] = {"match": interaction_type}
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Fetch interactions from Qdrant (sync method)
        results = qdrant.scroll(
            collection="user_interactions",
            limit=page_size,
            offset=offset,
            filters=filters,
            with_payload=True
        )
        
        # Format interactions
        interactions = []
        for result in results:
            outer_payload = result.get("payload", {})
            payload = outer_payload.get("payload", outer_payload)  # Handle nested payload
            interactions.append(UserInteraction(
                id=result.get("id", ""),
                user_id=payload.get("user_id", user_id),
                product_id=payload.get("product_id", ""),
                interaction_type=payload.get("interaction_type", "view"),
                timestamp=datetime.fromisoformat(
                    payload.get("timestamp", datetime.utcnow().isoformat())
                ),
                metadata=payload.get("metadata"),
                session_id=payload.get("session_id")
            ))
        
        # Get total count (simplified - in production use count endpoint)
        total = len(interactions) + offset  # Approximate
        
        return InteractionHistoryResponse(
            success=True,
            user_id=user_id,
            interactions=interactions,
            total=total,
            page=page,
            page_size=page_size,
            request_id=request_id
        )
        
    except Exception as e:
        logger.error(f"Error fetching interactions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch interactions: {str(e)}"
        )


@router.post(
    "/{user_id}/interactions",
    response_model=dict,
    status_code=status.HTTP_201_CREATED
)
async def log_user_interaction(
    request: Request,
    user_id: str,
    product_id: str,
    interaction: InteractionRequest,
    qdrant: QdrantService = Depends(get_qdrant_service),
    current_user: Optional[UserContext] = Depends(get_current_user),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    Log a user interaction with a product.
    
    Records interactions like:
    - view, click
    - add_to_cart, remove_from_cart
    - purchase
    - wishlist, review, share
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
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
        
        # Store in Qdrant (sync method, using zero vector for filtering-only collection)
        # In production, you might use a separate database for interactions
        qdrant.upsert_point(
            collection="user_interactions",
            point_id=interaction_id,
            vector=[0.0] * 384,  # Placeholder vector
            payload=payload
        )
        
        logger.info(
            f"Logged interaction: user={user_id}, product={product_id}, "
            f"type={interaction.interaction_type.value}"
        )
        
        return {
            "success": True,
            "interaction_id": interaction_id,
            "request_id": request_id
        }
        
    except Exception as e:
        logger.error(f"Error logging interaction: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log interaction: {str(e)}"
        )


# ==============================================================================
# Helper Functions
# ==============================================================================

def _build_user_preference_text(payload: dict) -> str:
    """Build text representation of user preferences for embedding."""
    parts = []
    
    if payload.get("favorite_categories"):
        parts.append(f"Interested in: {', '.join(payload['favorite_categories'])}")
    
    if payload.get("favorite_brands"):
        parts.append(f"Prefers brands: {', '.join(payload['favorite_brands'])}")
    
    if payload.get("price_sensitivity"):
        parts.append(f"Price sensitivity: {payload['price_sensitivity']}")
    
    if payload.get("quality_preference"):
        parts.append(f"Quality preference: {payload['quality_preference']}")
    
    if payload.get("eco_friendly"):
        parts.append("Prefers eco-friendly products")
    
    if payload.get("monthly_budget"):
        parts.append(f"Budget around ${payload['monthly_budget']}")
    
    return ". ".join(parts) if parts else "General user preferences"
