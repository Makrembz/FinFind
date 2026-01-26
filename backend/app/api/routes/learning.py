"""
Learning System API Routes.

Exposes the learning and feedback system via REST API:
- Interaction tracking
- Metrics and dashboard
- A/B testing management
- User profiles
- Manual learning triggers
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status, BackgroundTasks
from pydantic import BaseModel, Field

from ..dependencies import (
    get_current_user,
    check_rate_limit,
    UserContext
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ==============================================================================
# Dependency
# ==============================================================================

def get_learning_orchestrator():
    """Get the learning orchestrator instance."""
    from ...learning import get_learning_orchestrator
    return get_learning_orchestrator()


# ==============================================================================
# Request/Response Models
# ==============================================================================

class TrackSearchRequest(BaseModel):
    """Request to track a search interaction."""
    query: str
    results: List[str] = Field(..., description="List of product IDs returned")
    search_type: str = Field(default="text", description="text, voice, or image")
    agent_used: Optional[str] = None
    budget_max: Optional[float] = None


class TrackClickRequest(BaseModel):
    """Request to track a product click."""
    product_id: str
    position: int = Field(..., ge=0, description="Position in results (0-indexed)")
    items_shown: List[str]
    item_price: Optional[float] = None
    budget_max: Optional[float] = None
    source: str = Field(default="search", description="search, recommendation, alternative")


class TrackRecommendationRequest(BaseModel):
    """Request to track recommendation interaction."""
    recommendations_shown: List[str]
    clicked_product: Optional[str] = None
    position: Optional[int] = None
    item_price: Optional[float] = None
    dismissed: bool = False


class TrackAlternativeRequest(BaseModel):
    """Request to track alternative interaction."""
    original_product_id: str
    alternatives_shown: List[str]
    alternative_clicked: Optional[str] = None
    alternative_accepted: bool = False
    item_price: Optional[float] = None
    budget_max: Optional[float] = None


class TrackCartRequest(BaseModel):
    """Request to track cart action."""
    product_id: str
    action: str = Field(..., description="add or remove")
    item_price: Optional[float] = None
    budget_max: Optional[float] = None
    source: str = "search"


class TrackPurchaseRequest(BaseModel):
    """Request to track purchase."""
    products: List[Dict[str, Any]]
    total_amount: float = Field(..., ge=0)
    budget_max: Optional[float] = None


class TrackExplanationFeedbackRequest(BaseModel):
    """Request to track explanation feedback."""
    product_id: str
    helpful: bool


class CreateExperimentRequest(BaseModel):
    """Request to create an A/B test experiment."""
    name: str
    description: str
    test_type: str = Field(..., description="ranking, recommendation, alternative, constraint")
    target_component: str
    control_config: Dict[str, Any]
    treatment_config: Dict[str, Any]
    traffic_split: float = Field(default=50.0, ge=0, le=100)
    min_sample_size: int = Field(default=1000, ge=100)


class InteractionResponse(BaseModel):
    """Response from tracking an interaction."""
    success: bool
    interaction_id: str


class ProfileResponse(BaseModel):
    """Response containing user learning profile."""
    user_id: str
    has_profile: bool
    profile: Optional[Dict[str, Any]] = None


# ==============================================================================
# Interaction Tracking Endpoints
# ==============================================================================

@router.post(
    "/track/search",
    response_model=InteractionResponse,
    summary="Track a search interaction"
)
async def track_search(
    request: Request,
    body: TrackSearchRequest,
    current_user: Optional[UserContext] = Depends(get_current_user),
    orchestrator = Depends(get_learning_orchestrator),
    _rate_limit: None = Depends(check_rate_limit)
):
    """Track when a user performs a search."""
    user_id = current_user.user_id if current_user else "anonymous"
    session_id = getattr(request.state, "request_id", "unknown")
    
    interaction_id = await orchestrator.track_search(
        user_id=user_id,
        session_id=session_id,
        query=body.query,
        results=body.results,
        search_type=body.search_type,
        agent_used=body.agent_used,
        budget_max=body.budget_max
    )
    
    return InteractionResponse(success=True, interaction_id=interaction_id)


@router.post(
    "/track/click",
    response_model=InteractionResponse,
    summary="Track a product click"
)
async def track_click(
    request: Request,
    body: TrackClickRequest,
    current_user: Optional[UserContext] = Depends(get_current_user),
    orchestrator = Depends(get_learning_orchestrator),
    _rate_limit: None = Depends(check_rate_limit)
):
    """Track when a user clicks on a product."""
    user_id = current_user.user_id if current_user else "anonymous"
    session_id = getattr(request.state, "request_id", "unknown")
    
    interaction_id = await orchestrator.track_product_click(
        user_id=user_id,
        session_id=session_id,
        product_id=body.product_id,
        position=body.position,
        items_shown=body.items_shown,
        item_price=body.item_price,
        budget_max=body.budget_max,
        source=body.source
    )
    
    return InteractionResponse(success=True, interaction_id=interaction_id)


@router.post(
    "/track/recommendation",
    response_model=InteractionResponse,
    summary="Track recommendation interaction"
)
async def track_recommendation(
    request: Request,
    body: TrackRecommendationRequest,
    current_user: Optional[UserContext] = Depends(get_current_user),
    orchestrator = Depends(get_learning_orchestrator),
    _rate_limit: None = Depends(check_rate_limit)
):
    """Track recommendation view/click/dismiss."""
    user_id = current_user.user_id if current_user else "anonymous"
    session_id = getattr(request.state, "request_id", "unknown")
    
    interaction_id = await orchestrator.track_recommendation(
        user_id=user_id,
        session_id=session_id,
        recommendations_shown=body.recommendations_shown,
        clicked_product=body.clicked_product,
        position=body.position,
        item_price=body.item_price,
        dismissed=body.dismissed
    )
    
    return InteractionResponse(success=True, interaction_id=interaction_id)


@router.post(
    "/track/alternative",
    response_model=InteractionResponse,
    summary="Track alternative product interaction"
)
async def track_alternative(
    request: Request,
    body: TrackAlternativeRequest,
    current_user: Optional[UserContext] = Depends(get_current_user),
    orchestrator = Depends(get_learning_orchestrator),
    _rate_limit: None = Depends(check_rate_limit)
):
    """Track alternative product view/click/accept/reject."""
    user_id = current_user.user_id if current_user else "anonymous"
    session_id = getattr(request.state, "request_id", "unknown")
    
    interaction_id = await orchestrator.track_alternative(
        user_id=user_id,
        session_id=session_id,
        original_product_id=body.original_product_id,
        alternatives_shown=body.alternatives_shown,
        alternative_clicked=body.alternative_clicked,
        alternative_accepted=body.alternative_accepted,
        item_price=body.item_price,
        budget_max=body.budget_max
    )
    
    return InteractionResponse(success=True, interaction_id=interaction_id)


@router.post(
    "/track/cart",
    response_model=InteractionResponse,
    summary="Track cart action"
)
async def track_cart(
    request: Request,
    body: TrackCartRequest,
    current_user: Optional[UserContext] = Depends(get_current_user),
    orchestrator = Depends(get_learning_orchestrator),
    _rate_limit: None = Depends(check_rate_limit)
):
    """Track add/remove cart action."""
    user_id = current_user.user_id if current_user else "anonymous"
    session_id = getattr(request.state, "request_id", "unknown")
    
    interaction_id = await orchestrator.track_cart_action(
        user_id=user_id,
        session_id=session_id,
        product_id=body.product_id,
        action=body.action,
        item_price=body.item_price,
        budget_max=body.budget_max,
        source=body.source
    )
    
    return InteractionResponse(success=True, interaction_id=interaction_id)


@router.post(
    "/track/purchase",
    response_model=InteractionResponse,
    summary="Track purchase completion"
)
async def track_purchase(
    request: Request,
    body: TrackPurchaseRequest,
    current_user: Optional[UserContext] = Depends(get_current_user),
    orchestrator = Depends(get_learning_orchestrator),
    _rate_limit: None = Depends(check_rate_limit)
):
    """Track when a purchase is completed."""
    user_id = current_user.user_id if current_user else "anonymous"
    session_id = getattr(request.state, "request_id", "unknown")
    
    interaction_id = await orchestrator.track_purchase(
        user_id=user_id,
        session_id=session_id,
        products=body.products,
        total_amount=body.total_amount,
        budget_max=body.budget_max
    )
    
    return InteractionResponse(success=True, interaction_id=interaction_id)


@router.post(
    "/track/explanation-feedback",
    response_model=InteractionResponse,
    summary="Track explanation feedback"
)
async def track_explanation_feedback(
    request: Request,
    body: TrackExplanationFeedbackRequest,
    current_user: Optional[UserContext] = Depends(get_current_user),
    orchestrator = Depends(get_learning_orchestrator),
    _rate_limit: None = Depends(check_rate_limit)
):
    """Track whether an explanation was helpful."""
    user_id = current_user.user_id if current_user else "anonymous"
    session_id = getattr(request.state, "request_id", "unknown")
    
    interaction_id = await orchestrator.track_explanation_feedback(
        user_id=user_id,
        session_id=session_id,
        product_id=body.product_id,
        helpful=body.helpful
    )
    
    return InteractionResponse(success=True, interaction_id=interaction_id)


# ==============================================================================
# User Profile Endpoints
# ==============================================================================

@router.get(
    "/profile/{user_id}",
    response_model=ProfileResponse,
    summary="Get user learning profile"
)
async def get_user_profile(
    user_id: str,
    orchestrator = Depends(get_learning_orchestrator),
    _rate_limit: None = Depends(check_rate_limit)
):
    """Get the learning profile for a user."""
    profile = await orchestrator.get_user_profile(user_id)
    
    return ProfileResponse(
        user_id=user_id,
        has_profile=profile is not None,
        profile=profile.to_dict() if profile else None
    )


@router.get(
    "/profile/{user_id}/adjustments",
    summary="Get user-specific adjustments"
)
async def get_user_adjustments(
    user_id: str,
    category: Optional[str] = Query(None),
    orchestrator = Depends(get_learning_orchestrator),
    _rate_limit: None = Depends(check_rate_limit)
):
    """Get affordability and other adjustments for a user."""
    affordability = orchestrator.get_affordability_adjustment(user_id, category)
    
    return {
        "user_id": user_id,
        "category": category,
        "affordability_adjustment": affordability
    }


# ==============================================================================
# Metrics and Dashboard Endpoints
# ==============================================================================

@router.get(
    "/dashboard",
    summary="Get learning system dashboard"
)
async def get_dashboard(
    orchestrator = Depends(get_learning_orchestrator),
    _rate_limit: None = Depends(check_rate_limit)
):
    """Get complete dashboard data for the learning system."""
    return await orchestrator.get_dashboard()


@router.get(
    "/kpis",
    summary="Get KPI summary"
)
async def get_kpis(
    days: int = Query(default=7, ge=1, le=90),
    orchestrator = Depends(get_learning_orchestrator),
    _rate_limit: None = Depends(check_rate_limit)
):
    """Get key performance indicators summary."""
    return await orchestrator.get_kpi_summary()


@router.get(
    "/insights",
    summary="Get learning insights"
)
async def get_insights(
    orchestrator = Depends(get_learning_orchestrator),
    _rate_limit: None = Depends(check_rate_limit)
):
    """Get current learning insights and recommendations."""
    insights = await orchestrator.get_insights()
    return {
        "insights": [i.to_dict() for i in insights],
        "count": len(insights)
    }


@router.get(
    "/status",
    summary="Get learning system status"
)
async def get_status(
    orchestrator = Depends(get_learning_orchestrator),
    _rate_limit: None = Depends(check_rate_limit)
):
    """Get current status of the learning system."""
    return orchestrator.get_status()


# ==============================================================================
# A/B Testing Endpoints
# ==============================================================================

@router.get(
    "/experiments",
    summary="List A/B test experiments"
)
async def list_experiments(
    status: Optional[str] = Query(None, description="Filter by status"),
    orchestrator = Depends(get_learning_orchestrator),
    _rate_limit: None = Depends(check_rate_limit)
):
    """List all A/B test experiments."""
    experiments = orchestrator._ab_testing.list_experiments(status=status)
    return {"experiments": experiments}


@router.post(
    "/experiments",
    summary="Create A/B test experiment"
)
async def create_experiment(
    body: CreateExperimentRequest,
    orchestrator = Depends(get_learning_orchestrator),
    _rate_limit: None = Depends(check_rate_limit)
):
    """Create a new A/B test experiment."""
    experiment_id = orchestrator.create_experiment(
        name=body.name,
        description=body.description,
        test_type=body.test_type,
        target_component=body.target_component,
        control_config=body.control_config,
        treatment_config=body.treatment_config,
        traffic_split=body.traffic_split
    )
    
    return {"experiment_id": experiment_id, "status": "draft"}


@router.post(
    "/experiments/{experiment_id}/start",
    summary="Start an experiment"
)
async def start_experiment(
    experiment_id: str,
    orchestrator = Depends(get_learning_orchestrator),
    _rate_limit: None = Depends(check_rate_limit)
):
    """Start a draft experiment."""
    success = orchestrator.start_experiment(experiment_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not start experiment"
        )
    
    return {"experiment_id": experiment_id, "status": "running"}


@router.post(
    "/experiments/{experiment_id}/stop",
    summary="Stop an experiment"
)
async def stop_experiment(
    experiment_id: str,
    orchestrator = Depends(get_learning_orchestrator),
    _rate_limit: None = Depends(check_rate_limit)
):
    """Stop a running experiment."""
    result = orchestrator._ab_testing.stop_experiment(experiment_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experiment not found"
        )
    
    return result


@router.get(
    "/experiments/{experiment_id}/analyze",
    summary="Analyze experiment results"
)
async def analyze_experiment(
    experiment_id: str,
    orchestrator = Depends(get_learning_orchestrator),
    _rate_limit: None = Depends(check_rate_limit)
):
    """Analyze results of an A/B test experiment."""
    result = orchestrator.analyze_experiment(experiment_id)
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )
    
    return result


@router.get(
    "/experiments/{experiment_id}/variant",
    summary="Get user's experiment variant"
)
async def get_variant(
    experiment_id: str,
    user_id: str = Query(...),
    orchestrator = Depends(get_learning_orchestrator),
    _rate_limit: None = Depends(check_rate_limit)
):
    """Get which variant a user is assigned to."""
    config = orchestrator._ab_testing.get_variant_config(user_id, experiment_id)
    variant = orchestrator._ab_testing.get_user_variant(user_id, experiment_id)
    
    return {
        "user_id": user_id,
        "experiment_id": experiment_id,
        "variant": variant or "control",
        "config": config
    }


# ==============================================================================
# Manual Learning Triggers
# ==============================================================================

@router.post(
    "/trigger/profile-update",
    summary="Trigger profile updates"
)
async def trigger_profile_update(
    background_tasks: BackgroundTasks,
    user_ids: Optional[List[str]] = Query(None),
    orchestrator = Depends(get_learning_orchestrator),
    _rate_limit: None = Depends(check_rate_limit)
):
    """Manually trigger user profile updates."""
    # Run in background to not block
    background_tasks.add_task(orchestrator.trigger_profile_update, user_ids)
    
    return {
        "status": "triggered",
        "target_users": user_ids or "all_active"
    }


@router.post(
    "/trigger/ranking-update",
    summary="Trigger ranking updates"
)
async def trigger_ranking_update(
    background_tasks: BackgroundTasks,
    orchestrator = Depends(get_learning_orchestrator),
    _rate_limit: None = Depends(check_rate_limit)
):
    """Manually trigger product ranking updates."""
    background_tasks.add_task(orchestrator.trigger_ranking_update)
    
    return {"status": "triggered"}


@router.post(
    "/trigger/query-update",
    summary="Trigger query mapping updates"
)
async def trigger_query_update(
    background_tasks: BackgroundTasks,
    orchestrator = Depends(get_learning_orchestrator),
    _rate_limit: None = Depends(check_rate_limit)
):
    """Manually trigger query-product mapping updates."""
    background_tasks.add_task(orchestrator.trigger_query_update)
    
    return {"status": "triggered"}


# ==============================================================================
# Query Learning Endpoints
# ==============================================================================

@router.get(
    "/query-products",
    summary="Get learned products for query"
)
async def get_query_products(
    query: str = Query(..., min_length=1),
    limit: int = Query(default=10, ge=1, le=50),
    orchestrator = Depends(get_learning_orchestrator),
    _rate_limit: None = Depends(check_rate_limit)
):
    """Get products that historically performed well for a query."""
    products = orchestrator.get_query_products(query, limit)
    
    return {
        "query": query,
        "products": products,
        "count": len(products)
    }


@router.get(
    "/ranking-adjustment/{product_id}",
    summary="Get ranking adjustment for product"
)
async def get_ranking_adjustment(
    product_id: str,
    orchestrator = Depends(get_learning_orchestrator),
    _rate_limit: None = Depends(check_rate_limit)
):
    """Get the learned ranking adjustment for a product."""
    adjustment = orchestrator.get_ranking_adjustment(product_id)
    
    return {
        "product_id": product_id,
        "adjustment": adjustment
    }
