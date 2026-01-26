"""
Agent API routes.

Provides endpoints for interacting with the agent system.
"""

import logging
import uuid
import time
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from ..dependencies import (
    get_orchestrator,
    get_current_user,
    check_rate_limit,
    UserContext
)
from ...agents.orchestrator.coordinator import AgentOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter()


# ==============================================================================
# Request/Response Models
# ==============================================================================

class AgentQueryRequest(BaseModel):
    """Request to query the agent system."""
    query: str = Field(..., min_length=1, max_length=2000)
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional context for the query"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for conversation continuity"
    )
    preferred_agent: Optional[str] = Field(
        default=None,
        description="Preferred agent to handle the query"
    )
    include_explanations: bool = Field(
        default=True,
        description="Include explanation of the response"
    )


class AgentResponse(BaseModel):
    """Response from agent system."""
    success: bool
    response: Optional[str] = None
    agent_used: Optional[str] = None
    products: Optional[List[Dict[str, Any]]] = None
    explanation: Optional[str] = None
    confidence: Optional[float] = None
    processing_time_ms: float
    request_id: str
    session_id: str
    
    # Additional context
    follow_up_suggestions: Optional[List[str]] = None
    related_queries: Optional[List[str]] = None


class ConversationMessage(BaseModel):
    """A message in the conversation."""
    role: str = Field(..., description="user or assistant")
    content: str
    timestamp: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class ConversationRequest(BaseModel):
    """Request for multi-turn conversation."""
    messages: List[ConversationMessage]
    context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None


class AgentInfo(BaseModel):
    """Information about an agent."""
    name: str
    description: str
    capabilities: List[str]
    supported_queries: List[str]


class AgentListResponse(BaseModel):
    """Response listing available agents."""
    agents: List[AgentInfo]


# ==============================================================================
# Agent Endpoints
# ==============================================================================

@router.post("/query", response_model=AgentResponse)
async def query_agents(
    request: Request,
    body: AgentQueryRequest,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
    user: Optional[UserContext] = Depends(get_current_user),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    Send a query to the agent system.
    
    The orchestrator will route the query to the appropriate agent(s)
    and return a combined response.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    start_time = time.time()
    session_id = body.session_id or str(uuid.uuid4())
    
    try:
        # Build context
        context = body.context or {}
        if user:
            context["user_id"] = user.user_id
        
        # Process query through orchestrator
        result = await orchestrator.process(
            query=body.query,
            context=context,
            session_id=session_id,
            preferred_agent=body.preferred_agent
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        # Extract products if present
        products = None
        if result.get("products"):
            products = result["products"]
        
        # Generate follow-up suggestions
        follow_ups = _generate_follow_ups(body.query, result)
        
        return AgentResponse(
            success=True,
            response=result.get("response", ""),
            agent_used=result.get("agent_used"),
            products=products,
            explanation=result.get("explanation") if body.include_explanations else None,
            confidence=result.get("confidence"),
            processing_time_ms=processing_time,
            request_id=request_id,
            session_id=session_id,
            follow_up_suggestions=follow_ups
        )
        
    except Exception as e:
        logger.error(f"Agent query error: {e}", exc_info=True)
        processing_time = (time.time() - start_time) * 1000
        return AgentResponse(
            success=False,
            response=f"An error occurred: {str(e)}",
            processing_time_ms=processing_time,
            request_id=request_id,
            session_id=session_id
        )


@router.post("/conversation", response_model=AgentResponse)
async def multi_turn_conversation(
    request: Request,
    body: ConversationRequest,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
    user: Optional[UserContext] = Depends(get_current_user),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    Handle multi-turn conversation with agents.
    
    Maintains conversation history for context-aware responses.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    start_time = time.time()
    session_id = body.session_id or str(uuid.uuid4())
    
    try:
        # Build conversation context
        context = body.context or {}
        if user:
            context["user_id"] = user.user_id
        
        # Add conversation history to context
        context["conversation_history"] = [
            {"role": msg.role, "content": msg.content}
            for msg in body.messages
        ]
        
        # Get the latest user message
        user_messages = [m for m in body.messages if m.role == "user"]
        if not user_messages:
            raise HTTPException(
                status_code=400,
                detail="No user message in conversation"
            )
        
        latest_query = user_messages[-1].content
        
        # Process through orchestrator
        result = await orchestrator.process(
            query=latest_query,
            context=context,
            session_id=session_id
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        return AgentResponse(
            success=True,
            response=result.get("response", ""),
            agent_used=result.get("agent_used"),
            products=result.get("products"),
            explanation=result.get("explanation"),
            processing_time_ms=processing_time,
            request_id=request_id,
            session_id=session_id,
            follow_up_suggestions=_generate_follow_ups(latest_query, result)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Conversation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Conversation failed: {str(e)}"
        )


@router.get("/list", response_model=AgentListResponse)
async def list_agents(
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
):
    """
    List all available agents and their capabilities.
    """
    agents = [
        AgentInfo(
            name="SearchAgent",
            description="Handles product search queries with semantic understanding",
            capabilities=[
                "Semantic product search",
                "Filter by price, category, brand",
                "Interpret vague queries",
                "Image-based search",
                "Voice search"
            ],
            supported_queries=[
                "Find me a laptop under $1000",
                "Show me running shoes",
                "What's similar to this product?"
            ]
        ),
        AgentInfo(
            name="RecommendationAgent",
            description="Provides personalized product recommendations",
            capabilities=[
                "Personalized recommendations",
                "Budget-aware suggestions",
                "Collaborative filtering",
                "Context-aware picks"
            ],
            supported_queries=[
                "What would you recommend for me?",
                "Products within my budget",
                "Similar to what I've liked before"
            ]
        ),
        AgentInfo(
            name="ExplainabilityAgent",
            description="Explains why products are recommended",
            capabilities=[
                "Explain product matches",
                "Financial fit analysis",
                "Attribute comparisons",
                "Natural language explanations"
            ],
            supported_queries=[
                "Why is this recommended?",
                "How does this fit my budget?",
                "Compare these products"
            ]
        ),
        AgentInfo(
            name="AlternativeAgent",
            description="Finds product alternatives and upgrades",
            capabilities=[
                "Find cheaper alternatives",
                "Suggest upgrades",
                "Category alternatives",
                "Price range search"
            ],
            supported_queries=[
                "Find me a cheaper alternative",
                "What's a better version of this?",
                "Similar products in a different price range"
            ]
        )
    ]
    
    return AgentListResponse(agents=agents)


@router.get("/health")
async def agent_health(
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
):
    """
    Check health of agent system.
    """
    try:
        # Basic health check
        is_healthy = orchestrator is not None
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "agents_available": 4,
            "orchestrator_ready": is_healthy
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# ==============================================================================
# Specialized Agent Endpoints
# ==============================================================================

@router.post("/search")
async def search_agent_query(
    request: Request,
    query: str,
    max_price: Optional[float] = None,
    category: Optional[str] = None,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
    user: Optional[UserContext] = Depends(get_current_user),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    Direct query to SearchAgent.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    context = {}
    if user:
        context["user_id"] = user.user_id
    if max_price:
        context["max_price"] = max_price
    if category:
        context["category"] = category
    
    result = await orchestrator.process(
        query=query,
        context=context,
        preferred_agent="search"
    )
    
    return {
        "products": result.get("products", []),
        "response": result.get("response"),
        "request_id": request_id
    }


@router.post("/recommend")
async def recommendation_agent_query(
    request: Request,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
    user: UserContext = Depends(get_current_user),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    Get personalized recommendations.
    
    Requires authentication.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required for recommendations"
        )
    
    result = await orchestrator.process(
        query="What products would you recommend for me?",
        context={"user_id": user.user_id},
        preferred_agent="recommendation"
    )
    
    return {
        "recommendations": result.get("products", []),
        "response": result.get("response"),
        "explanation": result.get("explanation"),
        "request_id": request_id
    }


@router.post("/explain")
async def explain_product(
    request: Request,
    product_id: str,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
    user: Optional[UserContext] = Depends(get_current_user),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    Get explanation for a product recommendation.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    context = {"product_id": product_id}
    if user:
        context["user_id"] = user.user_id
    
    result = await orchestrator.process(
        query=f"Why would you recommend product {product_id}?",
        context=context,
        preferred_agent="explainability"
    )
    
    return {
        "explanation": result.get("response"),
        "factors": result.get("factors", []),
        "request_id": request_id
    }


@router.post("/alternatives")
async def find_alternatives(
    request: Request,
    product_id: str,
    price_range: Optional[str] = None,  # "lower", "higher", "similar"
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
    user: Optional[UserContext] = Depends(get_current_user),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    Find alternatives to a product.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    context = {"product_id": product_id}
    if user:
        context["user_id"] = user.user_id
    if price_range:
        context["price_range"] = price_range
    
    query = f"Find alternatives to product {product_id}"
    if price_range == "lower":
        query = f"Find cheaper alternatives to product {product_id}"
    elif price_range == "higher":
        query = f"Find upgrades for product {product_id}"
    
    result = await orchestrator.process(
        query=query,
        context=context,
        preferred_agent="alternative"
    )
    
    return {
        "alternatives": result.get("products", []),
        "response": result.get("response"),
        "request_id": request_id
    }


# ==============================================================================
# Helper Functions
# ==============================================================================

def _generate_follow_ups(query: str, result: Dict[str, Any]) -> List[str]:
    """Generate follow-up suggestions based on query and results."""
    suggestions = []
    
    # Based on products found
    products = result.get("products", [])
    if products:
        suggestions.append("Tell me more about the top result")
        suggestions.append("Find cheaper alternatives")
        suggestions.append("Why is this recommended for me?")
    else:
        suggestions.append("Try a broader search")
        suggestions.append("Show me popular products")
    
    # Based on query type
    query_lower = query.lower()
    if "cheap" in query_lower or "budget" in query_lower:
        suggestions.append("Show me mid-range options")
    elif "best" in query_lower or "premium" in query_lower:
        suggestions.append("Show me budget-friendly alternatives")
    
    return suggestions[:3]
