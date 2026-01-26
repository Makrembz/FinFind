"""
Workflow Definitions for FinFind A2A Communication.

Defines the standard workflow patterns for agent collaboration:
1. Search → Recommendation Flow
2. Recommendation → Explainability Flow
3. Search → Alternative Flow
4. Multi-Agent Orchestrated Workflow
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable, Awaitable
from enum import Enum
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class WorkflowType(str, Enum):
    """Types of predefined workflows."""
    SEARCH_RECOMMEND = "search_recommend"
    RECOMMEND_EXPLAIN = "recommend_explain"
    SEARCH_ALTERNATIVE = "search_alternative"
    FULL_PIPELINE = "full_pipeline"
    CUSTOM = "custom"


class WorkflowStepStatus(str, Enum):
    """Status of a workflow step."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """
    A single step in a workflow.
    
    Attributes:
        id: Unique step identifier
        name: Human-readable step name
        agent: Name of the agent to execute this step
        task_template: Template for the task (can use {variables})
        condition: Optional condition function to determine if step should run
        transform_input: Function to transform input from previous step
        fallback_agent: Agent to use if primary fails
        timeout_seconds: Timeout for this step
        required: Whether this step is required for workflow success
    """
    id: str
    name: str
    agent: str
    task_template: str
    condition: Optional[Callable[[Dict], bool]] = None
    transform_input: Optional[Callable[[Dict], str]] = None
    fallback_agent: Optional[str] = None
    timeout_seconds: int = 30
    required: bool = True
    status: WorkflowStepStatus = WorkflowStepStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_ms: float = 0
    
    def should_run(self, context: Dict) -> bool:
        """Determine if this step should run based on condition."""
        if self.condition is None:
            return True
        try:
            return self.condition(context)
        except Exception as e:
            logger.warning(f"Step {self.id} condition check failed: {e}")
            return True  # Default to running if condition fails
    
    def get_task(self, context: Dict) -> str:
        """Get the task string with variables substituted."""
        if self.transform_input:
            return self.transform_input(context)
        
        # Simple variable substitution in template
        task = self.task_template
        for key, value in context.items():
            if isinstance(value, (str, int, float)):
                task = task.replace(f"{{{key}}}", str(value))
        return task


@dataclass
class WorkflowDefinition:
    """
    Definition of a complete workflow.
    
    Attributes:
        id: Unique workflow identifier
        name: Human-readable workflow name
        description: Workflow description
        workflow_type: Type of workflow
        steps: Ordered list of workflow steps
        parallel_steps: Steps that can run in parallel (list of step IDs)
        max_retries: Maximum retries for failed steps
        timeout_seconds: Total workflow timeout
    """
    id: str
    name: str
    description: str
    workflow_type: WorkflowType
    steps: List[WorkflowStep]
    parallel_steps: List[List[str]] = field(default_factory=list)
    max_retries: int = 2
    timeout_seconds: int = 120
    
    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """Get a step by ID."""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None


@dataclass
class WorkflowExecution:
    """
    Tracks the execution of a workflow.
    
    Attributes:
        id: Execution ID
        workflow_id: ID of the workflow being executed
        status: Current execution status
        started_at: Start timestamp
        completed_at: Completion timestamp
        context: Shared execution context
        step_results: Results from each step
        errors: List of errors encountered
        metrics: Execution metrics
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str = ""
    workflow_type: WorkflowType = WorkflowType.CUSTOM
    status: WorkflowStepStatus = WorkflowStepStatus.PENDING
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    context: Dict[str, Any] = field(default_factory=dict)
    step_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def add_step_result(self, step_id: str, result: Dict[str, Any]):
        """Add a step result."""
        self.step_results[step_id] = {
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        # Merge result into context for subsequent steps
        if isinstance(result, dict):
            self.context.update(result)
    
    def mark_complete(self, success: bool = True):
        """Mark execution as complete."""
        self.completed_at = datetime.utcnow()
        self.status = WorkflowStepStatus.COMPLETED if success else WorkflowStepStatus.FAILED
        self.metrics["total_time_ms"] = (
            self.completed_at - self.started_at
        ).total_seconds() * 1000
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "workflow_type": self.workflow_type.value,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "step_results": self.step_results,
            "errors": self.errors,
            "metrics": self.metrics
        }


# ==============================================================================
# Predefined Workflow Definitions
# ==============================================================================

def _has_products(ctx: Dict) -> bool:
    """Check if context has products."""
    products = ctx.get("products", ctx.get("output_products", []))
    return len(products) > 0


def _has_budget(ctx: Dict) -> bool:
    """Check if context has budget constraint."""
    return ctx.get("budget_max") is not None or ctx.get("max_price") is not None


def _products_over_budget(ctx: Dict) -> bool:
    """Check if any products exceed budget."""
    budget = ctx.get("budget_max") or ctx.get("max_price")
    if not budget:
        return False
    products = ctx.get("products", ctx.get("output_products", []))
    return any(p.get("price", 0) > budget for p in products)


def _all_products_over_budget(ctx: Dict) -> bool:
    """Check if ALL products exceed budget."""
    budget = ctx.get("budget_max") or ctx.get("max_price")
    if not budget:
        return False
    products = ctx.get("products", ctx.get("output_products", []))
    if not products:
        return False
    return all(p.get("price", 0) > budget for p in products)


def _transform_search_to_recommend(ctx: Dict) -> str:
    """Transform search results for recommendation agent."""
    products = ctx.get("products", ctx.get("output_products", []))[:5]
    query = ctx.get("query", ctx.get("input_text", ""))
    user_id = ctx.get("user_id", "")
    
    product_summaries = []
    for p in products:
        summary = f"- {p.get('name', p.get('title', 'Unknown'))}: ${p.get('price', 0)}"
        product_summaries.append(summary)
    
    return f"""Personalize these search results for user {user_id}:

Original query: {query}

Products found:
{chr(10).join(product_summaries)}

Rerank based on user preferences and add personalization explanations."""


def _transform_for_explanation(ctx: Dict) -> str:
    """Transform context for explainability agent."""
    product = ctx.get("product") or (ctx.get("products", [{}])[0] if ctx.get("products") else {})
    user_id = ctx.get("user_id", "")
    query = ctx.get("query", ctx.get("input_text", ""))
    
    return f"""Explain why this product was recommended:

Product: {product.get('name', product.get('title', 'Unknown'))}
Price: ${product.get('price', 0)}
Category: {product.get('category', 'Unknown')}

User: {user_id}
Original query: {query}

Provide a clear, user-friendly explanation of the match."""


def _transform_for_alternatives(ctx: Dict) -> str:
    """Transform context for alternative agent."""
    products = ctx.get("products", ctx.get("output_products", []))[:3]
    budget = ctx.get("budget_max") or ctx.get("max_price", 0)
    query = ctx.get("query", ctx.get("input_text", ""))
    
    product_info = []
    for p in products:
        product_info.append(f"- {p.get('name', p.get('title', 'Unknown'))}: ${p.get('price', 0)}")
    
    return f"""Find budget-friendly alternatives for these products:

Original products (over budget):
{chr(10).join(product_info)}

User's budget: ${budget}
Original query: {query}

Find similar products within budget and explain the trade-offs."""


# Search → Recommendation Workflow
SEARCH_RECOMMEND_WORKFLOW = WorkflowDefinition(
    id="search_recommend",
    name="Search and Personalize",
    description="Search for products then personalize results based on user profile",
    workflow_type=WorkflowType.SEARCH_RECOMMEND,
    steps=[
        WorkflowStep(
            id="search",
            name="Product Search",
            agent="SearchAgent",
            task_template="{query}",
            required=True
        ),
        WorkflowStep(
            id="recommend",
            name="Personalize Results",
            agent="RecommendationAgent",
            task_template="",  # Uses transform
            condition=_has_products,
            transform_input=_transform_search_to_recommend,
            required=False
        )
    ]
)


# Recommendation → Explainability Workflow
RECOMMEND_EXPLAIN_WORKFLOW = WorkflowDefinition(
    id="recommend_explain",
    name="Recommend with Explanation",
    description="Get recommendations and explain why they were chosen",
    workflow_type=WorkflowType.RECOMMEND_EXPLAIN,
    steps=[
        WorkflowStep(
            id="recommend",
            name="Get Recommendations",
            agent="RecommendationAgent",
            task_template="Get personalized recommendations for user {user_id}",
            required=True
        ),
        WorkflowStep(
            id="explain",
            name="Add Explanations",
            agent="ExplainabilityAgent",
            task_template="",
            condition=_has_products,
            transform_input=_transform_for_explanation,
            required=False
        )
    ]
)


# Search → Alternative Workflow (when budget exceeded)
SEARCH_ALTERNATIVE_WORKFLOW = WorkflowDefinition(
    id="search_alternative",
    name="Search with Budget Fallback",
    description="Search for products, find alternatives if over budget",
    workflow_type=WorkflowType.SEARCH_ALTERNATIVE,
    steps=[
        WorkflowStep(
            id="search",
            name="Product Search",
            agent="SearchAgent",
            task_template="{query}",
            required=True
        ),
        WorkflowStep(
            id="alternatives",
            name="Find Alternatives",
            agent="AlternativeAgent",
            task_template="",
            condition=_all_products_over_budget,
            transform_input=_transform_for_alternatives,
            required=False
        )
    ]
)


# Full Multi-Agent Pipeline
FULL_PIPELINE_WORKFLOW = WorkflowDefinition(
    id="full_pipeline",
    name="Full Product Discovery Pipeline",
    description="Complete workflow: Search → Personalize → Explain → Alternatives",
    workflow_type=WorkflowType.FULL_PIPELINE,
    steps=[
        WorkflowStep(
            id="search",
            name="Product Search",
            agent="SearchAgent",
            task_template="{query}",
            required=True
        ),
        WorkflowStep(
            id="recommend",
            name="Personalize Results",
            agent="RecommendationAgent",
            task_template="",
            condition=_has_products,
            transform_input=_transform_search_to_recommend,
            required=False
        ),
        WorkflowStep(
            id="explain",
            name="Add Explanations",
            agent="ExplainabilityAgent",
            task_template="",
            condition=_has_products,
            transform_input=_transform_for_explanation,
            required=False
        ),
        WorkflowStep(
            id="alternatives",
            name="Budget Alternatives",
            agent="AlternativeAgent",
            task_template="",
            condition=_products_over_budget,
            transform_input=_transform_for_alternatives,
            required=False
        )
    ],
    parallel_steps=[["explain", "alternatives"]]  # These can run in parallel
)


# Registry of all predefined workflows
WORKFLOW_REGISTRY: Dict[str, WorkflowDefinition] = {
    "search_recommend": SEARCH_RECOMMEND_WORKFLOW,
    "recommend_explain": RECOMMEND_EXPLAIN_WORKFLOW,
    "search_alternative": SEARCH_ALTERNATIVE_WORKFLOW,
    "full_pipeline": FULL_PIPELINE_WORKFLOW,
}


def get_workflow(workflow_id: str) -> Optional[WorkflowDefinition]:
    """Get a workflow by ID."""
    return WORKFLOW_REGISTRY.get(workflow_id)


def list_workflows() -> List[Dict[str, Any]]:
    """List all available workflows."""
    return [
        {
            "id": w.id,
            "name": w.name,
            "description": w.description,
            "type": w.workflow_type.value,
            "steps": [s.name for s in w.steps]
        }
        for w in WORKFLOW_REGISTRY.values()
    ]
