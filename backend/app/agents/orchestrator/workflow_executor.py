"""
Workflow Executor for FinFind A2A Communication.

Executes predefined and custom workflows, managing:
- Sequential and parallel step execution
- Error handling and retries
- Context propagation between steps
- Workflow metrics and debugging
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
import uuid
import traceback

from .workflows import (
    WorkflowDefinition,
    WorkflowStep,
    WorkflowExecution,
    WorkflowStepStatus,
    WorkflowType,
    get_workflow,
    WORKFLOW_REGISTRY
)
from .a2a_protocol import A2AProtocol, A2AMessage, A2AMessageType, A2AResponse
from ..base import AgentState, ConversationContext

logger = logging.getLogger(__name__)


@dataclass
class WorkflowResult:
    """Result of a workflow execution."""
    success: bool
    workflow_id: str
    execution_id: str
    output: str = ""
    products: List[Dict] = field(default_factory=list)
    explanations: Dict[str, str] = field(default_factory=dict)
    alternatives: List[Dict] = field(default_factory=list)
    step_outputs: Dict[str, Any] = field(default_factory=dict)
    agents_used: List[str] = field(default_factory=list)
    execution_time_ms: float = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "workflow_id": self.workflow_id,
            "execution_id": self.execution_id,
            "output": self.output,
            "products": self.products,
            "explanations": self.explanations,
            "alternatives": self.alternatives,
            "step_outputs": self.step_outputs,
            "agents_used": self.agents_used,
            "execution_time_ms": self.execution_time_ms,
            "errors": self.errors,
            "warnings": self.warnings
        }


class WorkflowExecutor:
    """
    Executes workflows by coordinating agent interactions.
    
    Responsibilities:
    - Execute workflow steps in order
    - Handle parallel execution where possible
    - Manage context propagation
    - Handle errors and retries
    - Track execution metrics
    """
    
    def __init__(self, a2a_protocol: A2AProtocol, agents: Dict[str, Any]):
        """
        Initialize the workflow executor.
        
        Args:
            a2a_protocol: The A2A protocol handler
            agents: Dictionary of agent instances by name
        """
        self._a2a = a2a_protocol
        self._agents = agents
        self._active_executions: Dict[str, WorkflowExecution] = {}
        self._execution_history: List[WorkflowExecution] = []
        self._max_history = 100
    
    # ========================================
    # Workflow Execution
    # ========================================
    
    async def execute_workflow(
        self,
        workflow_id: str,
        initial_context: Dict[str, Any],
        conversation_context: Optional[ConversationContext] = None
    ) -> WorkflowResult:
        """
        Execute a predefined workflow.
        
        Args:
            workflow_id: ID of the workflow to execute
            initial_context: Initial context (query, user_id, budget, etc.)
            conversation_context: Optional conversation context
            
        Returns:
            WorkflowResult with aggregated outputs
        """
        # Get workflow definition
        workflow = get_workflow(workflow_id)
        if not workflow:
            return WorkflowResult(
                success=False,
                workflow_id=workflow_id,
                execution_id="",
                errors=[f"Workflow '{workflow_id}' not found"]
            )
        
        return await self._execute_workflow_definition(
            workflow,
            initial_context,
            conversation_context
        )
    
    async def execute_custom_workflow(
        self,
        steps: List[Dict[str, Any]],
        initial_context: Dict[str, Any],
        conversation_context: Optional[ConversationContext] = None
    ) -> WorkflowResult:
        """
        Execute a custom workflow defined at runtime.
        
        Args:
            steps: List of step definitions
            initial_context: Initial context
            conversation_context: Optional conversation context
            
        Returns:
            WorkflowResult
        """
        # Convert step dicts to WorkflowStep objects
        workflow_steps = []
        for i, step_def in enumerate(steps):
            workflow_steps.append(WorkflowStep(
                id=step_def.get("id", f"step_{i}"),
                name=step_def.get("name", f"Step {i+1}"),
                agent=step_def["agent"],
                task_template=step_def.get("task", step_def.get("task_template", "{query}")),
                required=step_def.get("required", True),
                timeout_seconds=step_def.get("timeout", 30)
            ))
        
        # Create custom workflow
        workflow = WorkflowDefinition(
            id=f"custom_{uuid.uuid4().hex[:8]}",
            name="Custom Workflow",
            description="Runtime-defined workflow",
            workflow_type=WorkflowType.CUSTOM,
            steps=workflow_steps
        )
        
        return await self._execute_workflow_definition(
            workflow,
            initial_context,
            conversation_context
        )
    
    async def _execute_workflow_definition(
        self,
        workflow: WorkflowDefinition,
        initial_context: Dict[str, Any],
        conversation_context: Optional[ConversationContext] = None
    ) -> WorkflowResult:
        """Execute a workflow definition."""
        # Create execution tracker
        execution = WorkflowExecution(
            workflow_id=workflow.id,
            workflow_type=workflow.workflow_type,
            context=initial_context.copy()
        )
        self._active_executions[execution.id] = execution
        
        logger.info(f"Starting workflow '{workflow.name}' (execution: {execution.id})")
        
        result = WorkflowResult(
            success=True,
            workflow_id=workflow.id,
            execution_id=execution.id
        )
        
        try:
            # Execute steps
            for step in workflow.steps:
                step_result = await self._execute_step(
                    step,
                    execution,
                    workflow,
                    conversation_context
                )
                
                if step_result:
                    # Update result with step output
                    self._merge_step_result(result, step, step_result)
                    result.agents_used.append(step.agent)
                
                # Check if we should stop (required step failed)
                if step.required and step.status == WorkflowStepStatus.FAILED:
                    result.success = False
                    break
            
            # Calculate total time
            execution.mark_complete(result.success)
            result.execution_time_ms = execution.metrics.get("total_time_ms", 0)
            
            # Build final output
            result.output = self._build_output(result)
            
        except asyncio.TimeoutError:
            result.success = False
            result.errors.append(f"Workflow timed out after {workflow.timeout_seconds}s")
            execution.mark_complete(False)
            
        except Exception as e:
            logger.exception(f"Workflow execution error: {e}")
            result.success = False
            result.errors.append(str(e))
            execution.mark_complete(False)
        
        finally:
            # Move to history
            self._active_executions.pop(execution.id, None)
            self._execution_history.append(execution)
            self._cleanup_history()
        
        logger.info(
            f"Workflow '{workflow.name}' completed: success={result.success}, "
            f"time={result.execution_time_ms:.2f}ms, agents={result.agents_used}"
        )
        
        return result
    
    async def _execute_step(
        self,
        step: WorkflowStep,
        execution: WorkflowExecution,
        workflow: WorkflowDefinition,
        conversation_context: Optional[ConversationContext]
    ) -> Optional[Dict[str, Any]]:
        """Execute a single workflow step."""
        # Check condition
        if not step.should_run(execution.context):
            logger.info(f"Skipping step '{step.name}' - condition not met")
            step.status = WorkflowStepStatus.SKIPPED
            return None
        
        step.status = WorkflowStepStatus.RUNNING
        start_time = datetime.utcnow()
        
        logger.info(f"Executing step '{step.name}' with agent '{step.agent}'")
        
        try:
            # Get the task
            task = step.get_task(execution.context)
            
            # Get agent
            agent = self._agents.get(step.agent)
            if not agent:
                raise ValueError(f"Agent '{step.agent}' not found")
            
            # Execute with timeout
            try:
                result = await asyncio.wait_for(
                    self._run_agent(agent, task, execution.context, conversation_context),
                    timeout=step.timeout_seconds
                )
            except asyncio.TimeoutError:
                # Try fallback agent
                if step.fallback_agent:
                    logger.warning(f"Step '{step.name}' timed out, trying fallback agent")
                    fallback = self._agents.get(step.fallback_agent)
                    if fallback:
                        result = await self._run_agent(
                            fallback, task, execution.context, conversation_context
                        )
                    else:
                        raise
                else:
                    raise
            
            # Mark success
            step.status = WorkflowStepStatus.COMPLETED
            step.result = result
            step.execution_time_ms = (
                datetime.utcnow() - start_time
            ).total_seconds() * 1000
            
            # Add to execution
            execution.add_step_result(step.id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Step '{step.name}' failed: {e}")
            step.status = WorkflowStepStatus.FAILED
            step.error = str(e)
            step.execution_time_ms = (
                datetime.utcnow() - start_time
            ).total_seconds() * 1000
            
            execution.errors.append(f"Step '{step.name}': {str(e)}")
            
            # Retry if allowed
            if workflow.max_retries > 0:
                for retry in range(workflow.max_retries):
                    logger.info(f"Retrying step '{step.name}' (attempt {retry + 2})")
                    try:
                        task = step.get_task(execution.context)
                        agent = self._agents.get(step.agent)
                        result = await self._run_agent(
                            agent, task, execution.context, conversation_context
                        )
                        step.status = WorkflowStepStatus.COMPLETED
                        step.result = result
                        execution.add_step_result(step.id, result)
                        return result
                    except Exception as retry_error:
                        logger.error(f"Retry {retry + 2} failed: {retry_error}")
            
            return None
    
    async def _run_agent(
        self,
        agent: Any,
        task: str,
        context: Dict[str, Any],
        conversation_context: Optional[ConversationContext]
    ) -> Dict[str, Any]:
        """Run an agent with the given task."""
        # Create agent state
        state = AgentState(
            input_text=task,
            context=conversation_context
        )
        
        # Add context data to state
        if context.get("user_id"):
            state.user_id = context["user_id"]
        
        # Run agent
        result_state = await agent.run(task, state, conversation_context)
        
        # Extract results
        return {
            "output": result_state.output_text,
            "products": result_state.output_products,
            "explanations": result_state.output_explanations,
            "errors": result_state.errors,
            "agent": agent.agent_name
        }
    
    def _merge_step_result(
        self,
        result: WorkflowResult,
        step: WorkflowStep,
        step_result: Dict[str, Any]
    ):
        """Merge step result into workflow result."""
        # Store step output
        result.step_outputs[step.id] = step_result
        
        # Merge products (don't duplicate)
        new_products = step_result.get("products", [])
        existing_ids = {p.get("id") for p in result.products}
        for product in new_products:
            if product.get("id") not in existing_ids:
                result.products.append(product)
        
        # Merge explanations
        new_explanations = step_result.get("explanations", {})
        if isinstance(new_explanations, dict):
            result.explanations.update(new_explanations)
        
        # Collect alternatives from alternative agent
        if step.agent == "AlternativeAgent":
            result.alternatives = new_products
        
        # Collect errors
        step_errors = step_result.get("errors", [])
        result.errors.extend(step_errors)
    
    def _build_output(self, result: WorkflowResult) -> str:
        """Build final output text from workflow result."""
        parts = []
        
        # Collect outputs from steps
        for step_id, step_result in result.step_outputs.items():
            output = step_result.get("output", "")
            if output:
                parts.append(output)
        
        if parts:
            return "\n\n".join(parts)
        
        # Fallback: describe results
        if result.products:
            return f"Found {len(result.products)} products matching your criteria."
        
        return "I couldn't find any matching products."
    
    # ========================================
    # Parallel Execution
    # ========================================
    
    async def execute_parallel_steps(
        self,
        steps: List[WorkflowStep],
        execution: WorkflowExecution,
        workflow: WorkflowDefinition,
        conversation_context: Optional[ConversationContext]
    ) -> List[Tuple[WorkflowStep, Optional[Dict]]]:
        """Execute multiple steps in parallel."""
        tasks = [
            self._execute_step(step, execution, workflow, conversation_context)
            for step in steps
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return [
            (step, result if not isinstance(result, Exception) else None)
            for step, result in zip(steps, results)
        ]
    
    # ========================================
    # Convenience Methods
    # ========================================
    
    async def search_and_recommend(
        self,
        query: str,
        user_id: Optional[str] = None,
        budget_max: Optional[float] = None
    ) -> WorkflowResult:
        """Execute Search → Recommendation workflow."""
        return await self.execute_workflow(
            "search_recommend",
            {
                "query": query,
                "user_id": user_id or "anonymous",
                "budget_max": budget_max
            }
        )
    
    async def recommend_with_explanation(
        self,
        user_id: str,
        product_id: Optional[str] = None
    ) -> WorkflowResult:
        """Execute Recommendation → Explanation workflow."""
        return await self.execute_workflow(
            "recommend_explain",
            {
                "user_id": user_id,
                "product_id": product_id
            }
        )
    
    async def search_with_alternatives(
        self,
        query: str,
        budget_max: float,
        user_id: Optional[str] = None
    ) -> WorkflowResult:
        """Execute Search → Alternative workflow."""
        return await self.execute_workflow(
            "search_alternative",
            {
                "query": query,
                "budget_max": budget_max,
                "max_price": budget_max,
                "user_id": user_id or "anonymous"
            }
        )
    
    async def full_product_discovery(
        self,
        query: str,
        user_id: str,
        budget_max: Optional[float] = None
    ) -> WorkflowResult:
        """Execute the full multi-agent pipeline."""
        return await self.execute_workflow(
            "full_pipeline",
            {
                "query": query,
                "user_id": user_id,
                "budget_max": budget_max,
                "max_price": budget_max
            }
        )
    
    # ========================================
    # Status and Debugging
    # ========================================
    
    def get_active_executions(self) -> List[Dict]:
        """Get currently running workflow executions."""
        return [ex.to_dict() for ex in self._active_executions.values()]
    
    def get_execution_history(
        self,
        workflow_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """Get execution history."""
        history = self._execution_history
        
        if workflow_id:
            history = [ex for ex in history if ex.workflow_id == workflow_id]
        
        return [ex.to_dict() for ex in history[-limit:]]
    
    def get_execution(self, execution_id: str) -> Optional[Dict]:
        """Get a specific execution by ID."""
        # Check active
        if execution_id in self._active_executions:
            return self._active_executions[execution_id].to_dict()
        
        # Check history
        for ex in self._execution_history:
            if ex.id == execution_id:
                return ex.to_dict()
        
        return None
    
    def _cleanup_history(self):
        """Clean up old execution history."""
        if len(self._execution_history) > self._max_history:
            self._execution_history = self._execution_history[-self._max_history:]
