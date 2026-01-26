"""
Workflow API Routes.

Exposes the A2A workflow system via REST API:
- List available workflows
- Execute workflows
- Get workflow status
- Debug workflow executions
"""

import logging
import uuid
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from ..dependencies import (
    get_orchestrator,
    get_current_user,
    check_rate_limit,
    UserContext
)
from ...agents.orchestrator import (
    AgentOrchestrator,
    list_workflows,
    WorkflowType
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ==============================================================================
# Request/Response Models
# ==============================================================================

class WorkflowExecuteRequest(BaseModel):
    """Request to execute a workflow."""
    workflow_id: str = Field(..., description="ID of the workflow to execute")
    query: str = Field(..., min_length=1, max_length=1000)
    user_id: Optional[str] = None
    budget_max: Optional[float] = Field(default=None, ge=0)
    additional_context: Optional[Dict[str, Any]] = None


class CustomWorkflowStep(BaseModel):
    """Definition for a custom workflow step."""
    id: Optional[str] = None
    name: str
    agent: str = Field(..., description="Agent name: SearchAgent, RecommendationAgent, etc.")
    task: str = Field(..., description="Task for the agent")
    required: bool = True
    timeout: int = Field(default=30, ge=5, le=120)


class CustomWorkflowRequest(BaseModel):
    """Request to execute a custom workflow."""
    steps: List[CustomWorkflowStep]
    query: str
    user_id: Optional[str] = None
    budget_max: Optional[float] = None


class WorkflowResponse(BaseModel):
    """Response from workflow execution."""
    success: bool
    workflow_id: str
    execution_id: str
    output: str
    products: List[Dict[str, Any]]
    explanations: Dict[str, str] = {}
    alternatives: List[Dict[str, Any]] = []
    agents_used: List[str]
    execution_time_ms: float
    errors: List[str] = []
    warnings: List[str] = []
    request_id: str


class WorkflowInfo(BaseModel):
    """Information about a workflow."""
    id: str
    name: str
    description: str
    type: str
    steps: List[str]


class WorkflowListResponse(BaseModel):
    """Response listing available workflows."""
    workflows: List[WorkflowInfo]


# ==============================================================================
# Workflow Endpoints
# ==============================================================================

@router.get(
    "/",
    response_model=WorkflowListResponse,
    summary="List available workflows"
)
async def list_available_workflows(
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    List all available predefined workflows.
    
    Returns workflows for:
    - Search and personalize
    - Recommend with explanation
    - Search with budget fallback
    - Full discovery pipeline
    """
    workflows_data = list_workflows()
    
    return WorkflowListResponse(
        workflows=[
            WorkflowInfo(
                id=w["id"],
                name=w["name"],
                description=w["description"],
                type=w["type"],
                steps=w["steps"]
            )
            for w in workflows_data
        ]
    )


@router.post(
    "/execute",
    response_model=WorkflowResponse,
    summary="Execute a predefined workflow"
)
async def execute_workflow(
    request: Request,
    body: WorkflowExecuteRequest,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
    current_user: Optional[UserContext] = Depends(get_current_user),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    Execute a predefined workflow.
    
    Workflows:
    - **search_recommend**: Search then personalize results
    - **recommend_explain**: Get recommendations with explanations
    - **search_alternative**: Search with budget fallback
    - **full_pipeline**: Complete multi-agent pipeline
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    # Use current user if available
    user_id = body.user_id
    if current_user and not user_id:
        user_id = current_user.user_id
    
    try:
        result = await orchestrator.execute_workflow(
            workflow_id=body.workflow_id,
            query=body.query,
            user_id=user_id,
            budget_max=body.budget_max,
            additional_context=body.additional_context
        )
        
        return WorkflowResponse(
            success=result["success"],
            workflow_id=result.get("workflow_id", body.workflow_id),
            execution_id=result.get("execution_id", ""),
            output=result.get("output", ""),
            products=result.get("products", []),
            explanations=result.get("explanations", {}),
            alternatives=result.get("alternatives", []),
            agents_used=result.get("agents_used", []),
            execution_time_ms=result.get("execution_time_ms", 0),
            errors=result.get("errors", []),
            warnings=result.get("warnings", []),
            request_id=request_id
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Workflow execution error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow execution failed: {str(e)}"
        )


@router.post(
    "/execute/custom",
    response_model=WorkflowResponse,
    summary="Execute a custom workflow"
)
async def execute_custom_workflow(
    request: Request,
    body: CustomWorkflowRequest,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
    current_user: Optional[UserContext] = Depends(get_current_user),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    Execute a custom workflow with user-defined steps.
    
    Define your own agent pipeline by specifying:
    - Agent to use at each step
    - Task for each agent
    - Whether step is required
    - Timeout for each step
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    user_id = body.user_id
    if current_user and not user_id:
        user_id = current_user.user_id
    
    # Validate agents
    valid_agents = ["SearchAgent", "RecommendationAgent", "ExplainabilityAgent", "AlternativeAgent"]
    for step in body.steps:
        if step.agent not in valid_agents:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid agent '{step.agent}'. Must be one of: {valid_agents}"
            )
    
    try:
        # Convert to step dicts
        steps = [
            {
                "id": step.id or f"step_{i}",
                "name": step.name,
                "agent": step.agent,
                "task": step.task,
                "required": step.required,
                "timeout": step.timeout
            }
            for i, step in enumerate(body.steps)
        ]
        
        # Execute via workflow executor
        if not orchestrator._initialized:
            orchestrator.initialize()
        
        result = await orchestrator._workflow_executor.execute_custom_workflow(
            steps=steps,
            initial_context={
                "query": body.query,
                "user_id": user_id or "anonymous",
                "budget_max": body.budget_max
            }
        )
        
        return WorkflowResponse(
            success=result.success,
            workflow_id=result.workflow_id,
            execution_id=result.execution_id,
            output=result.output,
            products=result.products,
            explanations=result.explanations,
            alternatives=result.alternatives,
            agents_used=result.agents_used,
            execution_time_ms=result.execution_time_ms,
            errors=result.errors,
            warnings=result.warnings,
            request_id=request_id
        )
        
    except Exception as e:
        logger.exception(f"Custom workflow error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Custom workflow failed: {str(e)}"
        )


# ==============================================================================
# Convenience Endpoints for Common Workflows
# ==============================================================================

@router.post(
    "/search-and-personalize",
    response_model=WorkflowResponse,
    summary="Search and personalize results"
)
async def search_and_personalize(
    request: Request,
    query: str = Query(..., min_length=1),
    user_id: Optional[str] = Query(None),
    budget_max: Optional[float] = Query(None, ge=0),
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
    current_user: Optional[UserContext] = Depends(get_current_user),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    Execute Search → Recommendation workflow.
    
    1. SearchAgent finds products matching query
    2. RecommendationAgent personalizes results for user
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    uid = user_id or (current_user.user_id if current_user else None)
    
    result = await orchestrator.search_and_personalize(
        query=query,
        user_id=uid,
        budget_max=budget_max
    )
    
    return WorkflowResponse(
        success=result["success"],
        workflow_id="search_recommend",
        execution_id=result.get("execution_id", ""),
        output=result.get("output", ""),
        products=result.get("products", []),
        explanations=result.get("explanations", {}),
        alternatives=result.get("alternatives", []),
        agents_used=result.get("agents_used", []),
        execution_time_ms=result.get("execution_time_ms", 0),
        errors=result.get("errors", []),
        warnings=result.get("warnings", []),
        request_id=request_id
    )


@router.post(
    "/recommend-with-explanation",
    response_model=WorkflowResponse,
    summary="Get recommendations with explanations"
)
async def recommend_with_explanation(
    request: Request,
    user_id: str = Query(...),
    query: Optional[str] = Query(None),
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    Execute Recommendation → Explainability workflow.
    
    1. RecommendationAgent gets personalized recommendations
    2. ExplainabilityAgent explains why each was chosen
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    result = await orchestrator.recommend_with_explanation(
        user_id=user_id,
        query=query
    )
    
    return WorkflowResponse(
        success=result["success"],
        workflow_id="recommend_explain",
        execution_id=result.get("execution_id", ""),
        output=result.get("output", ""),
        products=result.get("products", []),
        explanations=result.get("explanations", {}),
        alternatives=result.get("alternatives", []),
        agents_used=result.get("agents_used", []),
        execution_time_ms=result.get("execution_time_ms", 0),
        errors=result.get("errors", []),
        warnings=result.get("warnings", []),
        request_id=request_id
    )


@router.post(
    "/search-with-fallback",
    response_model=WorkflowResponse,
    summary="Search with budget fallback"
)
async def search_with_budget_fallback(
    request: Request,
    query: str = Query(..., min_length=1),
    budget_max: float = Query(..., ge=0),
    user_id: Optional[str] = Query(None),
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
    current_user: Optional[UserContext] = Depends(get_current_user),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    Execute Search → Alternative workflow.
    
    1. SearchAgent searches for products
    2. If results exceed budget, AlternativeAgent finds affordable alternatives
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    uid = user_id or (current_user.user_id if current_user else None)
    
    result = await orchestrator.search_with_budget_fallback(
        query=query,
        budget_max=budget_max,
        user_id=uid
    )
    
    return WorkflowResponse(
        success=result["success"],
        workflow_id="search_alternative",
        execution_id=result.get("execution_id", ""),
        output=result.get("output", ""),
        products=result.get("products", []),
        explanations=result.get("explanations", {}),
        alternatives=result.get("alternatives", []),
        agents_used=result.get("agents_used", []),
        execution_time_ms=result.get("execution_time_ms", 0),
        errors=result.get("errors", []),
        warnings=result.get("warnings", []),
        request_id=request_id
    )


@router.post(
    "/full-discovery",
    response_model=WorkflowResponse,
    summary="Full product discovery pipeline"
)
async def full_discovery_pipeline(
    request: Request,
    query: str = Query(..., min_length=1),
    user_id: str = Query(...),
    budget_max: Optional[float] = Query(None, ge=0),
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    Execute the complete multi-agent pipeline.
    
    1. SearchAgent searches for products
    2. RecommendationAgent personalizes results
    3. ExplainabilityAgent adds match explanations
    4. AlternativeAgent prepares budget fallbacks (if needed)
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    result = await orchestrator.full_discovery_pipeline(
        query=query,
        user_id=user_id,
        budget_max=budget_max
    )
    
    return WorkflowResponse(
        success=result["success"],
        workflow_id="full_pipeline",
        execution_id=result.get("execution_id", ""),
        output=result.get("output", ""),
        products=result.get("products", []),
        explanations=result.get("explanations", {}),
        alternatives=result.get("alternatives", []),
        agents_used=result.get("agents_used", []),
        execution_time_ms=result.get("execution_time_ms", 0),
        errors=result.get("errors", []),
        warnings=result.get("warnings", []),
        request_id=request_id
    )


# ==============================================================================
# Debug/Status Endpoints
# ==============================================================================

@router.get(
    "/status",
    summary="Get workflow system status"
)
async def get_workflow_status(
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
    _rate_limit: None = Depends(check_rate_limit)
):
    """Get status of the workflow system including active executions."""
    status = orchestrator.get_status()
    return {
        "initialized": status["initialized"],
        "agents": list(status["agents"].keys()),
        "available_workflows": status["available_workflows"],
        "active_executions": status["active_workflow_executions"],
        "pending_a2a_tasks": status["pending_tasks"]
    }
