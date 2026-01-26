"""
Tests for A2A Communication and Workflow System.

Tests:
- A2A Protocol message passing
- Workflow definitions and execution
- Message bus pub/sub
- Multi-agent coordination
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.agents.orchestrator.a2a_protocol import (
    A2AProtocol,
    A2AMessage,
    A2AMessageType,
    A2AResponse
)
from app.agents.orchestrator.workflows import (
    WorkflowDefinition,
    WorkflowStep,
    WorkflowExecution,
    WorkflowStepStatus,
    WorkflowType,
    get_workflow,
    list_workflows,
    SEARCH_RECOMMEND_WORKFLOW,
    FULL_PIPELINE_WORKFLOW
)
from app.agents.orchestrator.workflow_executor import (
    WorkflowExecutor,
    WorkflowResult
)
from app.agents.orchestrator.message_bus import (
    A2AMessageBus,
    A2AEvent,
    A2AEventTypes,
    CompressedContext,
    MessagePriority
)


# ==============================================================================
# A2A Protocol Tests
# ==============================================================================

class TestA2AProtocol:
    """Tests for A2A Protocol."""
    
    @pytest.fixture
    def protocol(self):
        return A2AProtocol(log_communications=False)
    
    @pytest.fixture
    def mock_agent(self):
        agent = AsyncMock()
        agent.agent_name = "TestAgent"
        agent.run = AsyncMock(return_value=MagicMock(
            output_text="Test output",
            output_products=[{"id": "prod_1", "name": "Test Product"}],
            agent_chain=["TestAgent"],
            errors=[]
        ))
        return agent
    
    def test_register_agent(self, protocol, mock_agent):
        """Test agent registration."""
        protocol.register_agent("TestAgent", mock_agent)
        
        assert "TestAgent" in protocol.list_agents()
        assert protocol.get_agent("TestAgent") == mock_agent
    
    def test_unregister_agent(self, protocol, mock_agent):
        """Test agent unregistration."""
        protocol.register_agent("TestAgent", mock_agent)
        protocol.unregister_agent("TestAgent")
        
        assert "TestAgent" not in protocol.list_agents()
    
    @pytest.mark.asyncio
    async def test_send_message(self, protocol, mock_agent):
        """Test sending a message."""
        protocol.register_agent("TestAgent", mock_agent)
        
        message = A2AMessage(
            type=A2AMessageType.PING,
            sender="Orchestrator",
            recipient="TestAgent",
            payload={}
        )
        
        response = await protocol.send_message(message)
        
        assert response.success
        assert response.message_id == message.id
    
    @pytest.mark.asyncio
    async def test_delegate_task(self, protocol, mock_agent):
        """Test task delegation."""
        protocol.register_agent("TestAgent", mock_agent)
        
        response = await protocol.delegate_task(
            sender="Orchestrator",
            recipient="TestAgent",
            task="Find products",
            context={"user_id": "user_123"}
        )
        
        assert response.success
        mock_agent.run.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_agent_not_found(self, protocol):
        """Test message to non-existent agent."""
        message = A2AMessage(
            type=A2AMessageType.DELEGATE_TASK,
            sender="Orchestrator",
            recipient="NonExistentAgent",
            payload={"task": "Test"}
        )
        
        response = await protocol.send_message(message)
        
        assert not response.success
        assert "not found" in response.error
    
    def test_message_history(self, protocol):
        """Test message history tracking."""
        # Send some messages
        for i in range(5):
            msg = A2AMessage(
                type=A2AMessageType.PING,
                sender="Agent1",
                recipient="broadcast",
                payload={"count": i}
            )
            protocol._message_history.append(msg)
        
        history = protocol.get_message_history(limit=3)
        assert len(history) == 3


# ==============================================================================
# Workflow Tests
# ==============================================================================

class TestWorkflows:
    """Tests for workflow definitions."""
    
    def test_get_workflow(self):
        """Test getting a workflow by ID."""
        workflow = get_workflow("search_recommend")
        
        assert workflow is not None
        assert workflow.id == "search_recommend"
        assert workflow.workflow_type == WorkflowType.SEARCH_RECOMMEND
    
    def test_list_workflows(self):
        """Test listing all workflows."""
        workflows = list_workflows()
        
        assert len(workflows) >= 4
        assert any(w["id"] == "search_recommend" for w in workflows)
        assert any(w["id"] == "full_pipeline" for w in workflows)
    
    def test_workflow_steps(self):
        """Test workflow step definitions."""
        workflow = SEARCH_RECOMMEND_WORKFLOW
        
        assert len(workflow.steps) == 2
        assert workflow.steps[0].agent == "SearchAgent"
        assert workflow.steps[1].agent == "RecommendationAgent"
    
    def test_step_condition(self):
        """Test workflow step conditions."""
        workflow = SEARCH_RECOMMEND_WORKFLOW
        recommend_step = workflow.steps[1]
        
        # Should not run without products
        assert not recommend_step.should_run({})
        assert not recommend_step.should_run({"products": []})
        
        # Should run with products
        assert recommend_step.should_run({"products": [{"id": "1"}]})
    
    def test_step_task_generation(self):
        """Test task generation from template."""
        step = WorkflowStep(
            id="test",
            name="Test Step",
            agent="TestAgent",
            task_template="Search for {query} under ${budget_max}"
        )
        
        task = step.get_task({
            "query": "laptop",
            "budget_max": 1000
        })
        
        assert "laptop" in task
        assert "1000" in task


class TestWorkflowExecution:
    """Tests for workflow execution tracking."""
    
    def test_execution_creation(self):
        """Test creating an execution."""
        execution = WorkflowExecution(
            workflow_id="test",
            workflow_type=WorkflowType.CUSTOM
        )
        
        assert execution.id is not None
        assert execution.status == WorkflowStepStatus.PENDING
    
    def test_add_step_result(self):
        """Test adding step results."""
        execution = WorkflowExecution()
        
        execution.add_step_result("step1", {
            "products": [{"id": "1"}],
            "output": "Found products"
        })
        
        assert "step1" in execution.step_results
        assert "products" in execution.context
    
    def test_mark_complete(self):
        """Test marking execution complete."""
        execution = WorkflowExecution()
        execution.mark_complete(success=True)
        
        assert execution.status == WorkflowStepStatus.COMPLETED
        assert execution.completed_at is not None
        assert "total_time_ms" in execution.metrics


# ==============================================================================
# Workflow Executor Tests
# ==============================================================================

class TestWorkflowExecutor:
    """Tests for workflow executor."""
    
    @pytest.fixture
    def mock_agents(self):
        """Create mock agents."""
        agents = {}
        
        for name in ["SearchAgent", "RecommendationAgent", "ExplainabilityAgent", "AlternativeAgent"]:
            agent = AsyncMock()
            agent.agent_name = name
            agent.run = AsyncMock(return_value=MagicMock(
                output_text=f"Output from {name}",
                output_products=[{"id": f"prod_{name[:3]}", "name": f"Product from {name}", "price": 100}],
                output_explanations={},
                errors=[]
            ))
            agents[name] = agent
        
        return agents
    
    @pytest.fixture
    def executor(self, mock_agents):
        """Create workflow executor with mock agents."""
        protocol = A2AProtocol(log_communications=False)
        for name, agent in mock_agents.items():
            protocol.register_agent(name, agent)
        return WorkflowExecutor(protocol, mock_agents)
    
    @pytest.mark.asyncio
    async def test_execute_search_recommend(self, executor, mock_agents):
        """Test search → recommend workflow."""
        result = await executor.execute_workflow(
            "search_recommend",
            {
                "query": "laptop",
                "user_id": "user_123"
            }
        )
        
        assert result.success
        assert "SearchAgent" in result.agents_used
        mock_agents["SearchAgent"].run.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_full_pipeline(self, executor, mock_agents):
        """Test full pipeline workflow."""
        result = await executor.execute_workflow(
            "full_pipeline",
            {
                "query": "laptop under $800",
                "user_id": "user_123",
                "budget_max": 800
            }
        )
        
        assert result.success
        assert "SearchAgent" in result.agents_used
    
    @pytest.mark.asyncio
    async def test_execute_custom_workflow(self, executor):
        """Test custom workflow execution."""
        result = await executor.execute_custom_workflow(
            steps=[
                {
                    "id": "step1",
                    "name": "Search",
                    "agent": "SearchAgent",
                    "task": "Find laptops"
                }
            ],
            initial_context={"query": "laptop"}
        )
        
        assert result.success
        assert result.workflow_id.startswith("custom_")
    
    @pytest.mark.asyncio
    async def test_workflow_with_failed_step(self, executor, mock_agents):
        """Test workflow with a failing step."""
        # Make search agent fail
        mock_agents["SearchAgent"].run = AsyncMock(side_effect=Exception("Search failed"))
        
        result = await executor.execute_workflow(
            "search_recommend",
            {"query": "laptop"}
        )
        
        assert not result.success
        assert len(result.errors) > 0


# ==============================================================================
# Message Bus Tests
# ==============================================================================

class TestMessageBus:
    """Tests for A2A message bus."""
    
    @pytest.fixture
    def message_bus(self):
        return A2AMessageBus()
    
    @pytest.fixture
    def mock_agent(self):
        agent = MagicMock()
        agent.test_action = AsyncMock(return_value={"status": "ok"})
        return agent
    
    def test_register_agent(self, message_bus, mock_agent):
        """Test agent registration with bus."""
        message_bus.register_agent("TestAgent", mock_agent)
        assert "TestAgent" in message_bus._agents
    
    @pytest.mark.asyncio
    async def test_publish_subscribe(self, message_bus):
        """Test pub/sub pattern."""
        received_events = []
        
        async def handler(event: A2AEvent):
            received_events.append(event)
        
        message_bus.subscribe(A2AEventTypes.SEARCH_COMPLETED, handler)
        
        await message_bus.publish(
            A2AEventTypes.SEARCH_COMPLETED,
            "SearchAgent",
            {"products_count": 5}
        )
        
        assert len(received_events) == 1
        assert received_events[0].event_type == A2AEventTypes.SEARCH_COMPLETED
    
    def test_compressed_context(self):
        """Test context compression."""
        full_context = {
            "user_id": "user_123",
            "query": "laptop",
            "budget_max": 1000,
            "products": [{"id": "1"}, {"id": "2"}],
            "extra_data": "should be ignored"
        }
        
        compressed = CompressedContext.from_full_context(full_context)
        
        assert compressed.user_id == "user_123"
        assert compressed.query == "laptop"
        assert compressed.budget_max == 1000
        assert "1" in compressed.product_ids
    
    def test_context_compression_decompression(self):
        """Test context round-trip compression."""
        original = CompressedContext(
            user_id="user_123",
            query="laptop",
            budget_max=1000,
            categories=["Electronics"]
        )
        
        compressed = original.compress()
        decompressed = CompressedContext.decompress(compressed)
        
        assert decompressed.user_id == original.user_id
        assert decompressed.query == original.query
        assert decompressed.budget_max == original.budget_max


# ==============================================================================
# Integration Tests
# ==============================================================================

class TestA2AIntegration:
    """Integration tests for A2A system."""
    
    @pytest.mark.asyncio
    async def test_search_to_recommendation_flow(self):
        """Test Search → Recommendation A2A flow."""
        # Create mock agents
        search_agent = AsyncMock()
        search_agent.agent_name = "SearchAgent"
        search_agent.run = AsyncMock(return_value=MagicMock(
            output_text="Found 5 laptops",
            output_products=[
                {"id": "1", "name": "Laptop A", "price": 800},
                {"id": "2", "name": "Laptop B", "price": 900}
            ],
            output_explanations={},
            errors=[]
        ))
        
        rec_agent = AsyncMock()
        rec_agent.agent_name = "RecommendationAgent"
        rec_agent.run = AsyncMock(return_value=MagicMock(
            output_text="Personalized recommendations",
            output_products=[
                {"id": "1", "name": "Laptop A", "price": 800, "recommendation_score": 0.95}
            ],
            output_explanations={"1": "Best match for your budget"},
            errors=[]
        ))
        
        # Setup executor
        protocol = A2AProtocol(log_communications=False)
        agents = {
            "SearchAgent": search_agent,
            "RecommendationAgent": rec_agent
        }
        for name, agent in agents.items():
            protocol.register_agent(name, agent)
        
        executor = WorkflowExecutor(protocol, agents)
        
        # Execute workflow
        result = await executor.search_and_recommend(
            query="laptop for coding",
            user_id="user_123",
            budget_max=1000
        )
        
        assert result.success
        assert len(result.products) > 0
        search_agent.run.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_budget_exceeded_triggers_alternatives(self):
        """Test that budget exceeded triggers alternative agent."""
        # Search returns products over budget
        search_agent = AsyncMock()
        search_agent.agent_name = "SearchAgent"
        search_agent.run = AsyncMock(return_value=MagicMock(
            output_text="Found laptops",
            output_products=[
                {"id": "1", "name": "Expensive Laptop", "price": 1500}
            ],
            output_explanations={},
            errors=[]
        ))
        
        alt_agent = AsyncMock()
        alt_agent.agent_name = "AlternativeAgent"
        alt_agent.run = AsyncMock(return_value=MagicMock(
            output_text="Found alternatives",
            output_products=[
                {"id": "2", "name": "Budget Laptop", "price": 800}
            ],
            output_explanations={},
            errors=[]
        ))
        
        protocol = A2AProtocol(log_communications=False)
        agents = {
            "SearchAgent": search_agent,
            "AlternativeAgent": alt_agent
        }
        for name, agent in agents.items():
            protocol.register_agent(name, agent)
        
        executor = WorkflowExecutor(protocol, agents)
        
        result = await executor.search_with_alternatives(
            query="laptop",
            budget_max=1000,
            user_id="user_123"
        )
        
        assert result.success
        # Alternative agent should be called because all products over budget
        alt_agent.run.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
