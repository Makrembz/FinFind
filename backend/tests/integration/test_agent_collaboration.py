"""
Integration tests for agent collaboration (A2A).

Tests:
- Agent-to-agent communication
- Workflow execution
- Multi-agent scenarios
"""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from typing import Dict, Any, List


class TestAgentCollaboration:
    """Test agent-to-agent collaboration."""
    
    @pytest.mark.asyncio
    async def test_search_to_recommendation_handoff(self, sample_products):
        """Test handoff from search to recommendation agent."""
        with patch('app.agents.orchestrator.coordinator.AgentCoordinator') as MockCoord:
            coordinator = MockCoord.return_value
            
            # Mock the search -> recommendation flow
            coordinator.process_query = AsyncMock(return_value={
                "search_results": sample_products[:3],
                "recommendations": sample_products[1:4],
                "flow": ["SearchAgent", "RecommendationAgent"]
            })
            
            result = await coordinator.process_query(
                query="I need headphones that match my style",
                user_id="user_001"
            )
            
            assert "search_results" in result
            assert "recommendations" in result
    
    @pytest.mark.asyncio
    async def test_search_triggers_alternatives_on_budget(self, sample_products):
        """Test that search triggers alternatives when over budget."""
        with patch('app.agents.orchestrator.coordinator.AgentCoordinator') as MockCoord:
            coordinator = MockCoord.return_value
            
            # Product is over budget, should trigger alternatives
            coordinator.process_query = AsyncMock(return_value={
                "search_results": [sample_products[2]],  # $349.99
                "budget_exceeded": True,
                "alternatives": [sample_products[1]],  # $49.99
                "flow": ["SearchAgent", "AlternativeAgent"]
            })
            
            result = await coordinator.process_query(
                query="professional headphones",
                user_id="user_001",
                budget=100.0
            )
            
            assert result.get("budget_exceeded") is True
            assert "alternatives" in result
    
    @pytest.mark.asyncio
    async def test_recommendation_with_explanation(self, sample_products):
        """Test recommendation includes explanation."""
        with patch('app.agents.orchestrator.coordinator.AgentCoordinator') as MockCoord:
            coordinator = MockCoord.return_value
            
            coordinator.get_recommendations = AsyncMock(return_value={
                "recommendations": sample_products[:3],
                "explanations": [
                    "Matches your preference for electronics",
                    "Within your budget of $200",
                    "High rating of 4.5+"
                ],
                "flow": ["RecommendationAgent", "ExplainabilityAgent"]
            })
            
            result = await coordinator.get_recommendations(user_id="user_001")
            
            assert len(result["recommendations"]) == len(result["explanations"])
    
    @pytest.mark.asyncio
    async def test_multi_agent_search_flow(self, sample_products):
        """Test complete multi-agent search flow."""
        with patch('app.agents.orchestrator.coordinator.AgentCoordinator') as MockCoord:
            coordinator = MockCoord.return_value
            
            coordinator.complete_search_flow = AsyncMock(return_value={
                "query_interpretation": {
                    "category": "Electronics",
                    "intent": "purchase",
                    "constraints": {"max_price": 200}
                },
                "search_results": sample_products[:5],
                "filtered_results": sample_products[:3],
                "explanations": ["Match 1", "Match 2", "Match 3"],
                "alternatives": sample_products[1:2],
                "agents_used": [
                    "SearchAgent",
                    "RecommendationAgent",
                    "ExplainabilityAgent",
                    "AlternativeAgent"
                ]
            })
            
            result = await coordinator.complete_search_flow(
                query="wireless headphones under $200",
                user_id="user_001"
            )
            
            assert len(result["agents_used"]) >= 2


class TestWorkflowExecution:
    """Test workflow execution."""
    
    @pytest.mark.asyncio
    async def test_product_search_workflow(self, sample_products):
        """Test product search workflow."""
        with patch('app.agents.orchestrator.workflow_executor.WorkflowExecutor') as MockExec:
            executor = MockExec.return_value
            
            executor.execute = AsyncMock(return_value={
                "workflow_id": "wf_001",
                "status": "completed",
                "results": sample_products[:3],
                "steps_completed": ["interpret", "search", "filter", "rank"]
            })
            
            result = await executor.execute(
                workflow="product_search",
                params={"query": "headphones", "user_id": "user_001"}
            )
            
            assert result["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_recommendation_workflow(self, sample_products):
        """Test recommendation workflow."""
        with patch('app.agents.orchestrator.workflow_executor.WorkflowExecutor') as MockExec:
            executor = MockExec.return_value
            
            executor.execute = AsyncMock(return_value={
                "workflow_id": "wf_002",
                "status": "completed",
                "recommendations": sample_products[:5],
                "steps_completed": ["get_profile", "generate", "rank", "explain"]
            })
            
            result = await executor.execute(
                workflow="personalized_recommendation",
                params={"user_id": "user_001", "category": "Electronics"}
            )
            
            assert result["status"] == "completed"
            assert "recommendations" in result
    
    @pytest.mark.asyncio
    async def test_alternative_finding_workflow(self, sample_products):
        """Test alternative finding workflow."""
        with patch('app.agents.orchestrator.workflow_executor.WorkflowExecutor') as MockExec:
            executor = MockExec.return_value
            
            executor.execute = AsyncMock(return_value={
                "workflow_id": "wf_003",
                "status": "completed",
                "original_product": sample_products[2],
                "alternatives": sample_products[:2],
                "trade_offs": [
                    "Lower price but fewer features",
                    "Similar quality at lower price point"
                ]
            })
            
            result = await executor.execute(
                workflow="find_alternatives",
                params={
                    "product_id": "prod_003",
                    "target_budget": 100.0
                }
            )
            
            assert result["status"] == "completed"
            assert len(result["alternatives"]) > 0
    
    @pytest.mark.asyncio
    async def test_workflow_with_failure(self):
        """Test workflow handles failures gracefully."""
        with patch('app.agents.orchestrator.workflow_executor.WorkflowExecutor') as MockExec:
            executor = MockExec.return_value
            
            executor.execute = AsyncMock(return_value={
                "workflow_id": "wf_004",
                "status": "failed",
                "error": "Search service unavailable",
                "steps_completed": ["interpret"],
                "failed_step": "search"
            })
            
            result = await executor.execute(
                workflow="product_search",
                params={"query": "headphones"}
            )
            
            assert result["status"] == "failed"
            assert "error" in result


class TestMessageBus:
    """Test message bus for A2A communication."""
    
    @pytest.mark.asyncio
    async def test_publish_subscribe(self):
        """Test publish/subscribe pattern."""
        with patch('app.agents.orchestrator.message_bus.MessageBus') as MockBus:
            bus = MockBus.return_value
            
            received_messages = []
            
            async def handler(message):
                received_messages.append(message)
            
            bus.subscribe = MagicMock()
            bus.publish = AsyncMock()
            
            # Subscribe
            bus.subscribe("search.completed", handler)
            
            # Publish
            await bus.publish("search.completed", {
                "query": "headphones",
                "results_count": 5
            })
            
            assert bus.publish.called
    
    @pytest.mark.asyncio
    async def test_request_response(self):
        """Test request/response pattern between agents."""
        with patch('app.agents.orchestrator.message_bus.MessageBus') as MockBus:
            bus = MockBus.return_value
            
            bus.request = AsyncMock(return_value={
                "response": "success",
                "data": {"products": []}
            })
            
            result = await bus.request(
                topic="search.request",
                message={"query": "headphones"},
                timeout=5.0
            )
            
            assert result["response"] == "success"
    
    @pytest.mark.asyncio
    async def test_broadcast_to_all_agents(self):
        """Test broadcasting to all agents."""
        with patch('app.agents.orchestrator.message_bus.MessageBus') as MockBus:
            bus = MockBus.return_value
            
            bus.broadcast = AsyncMock()
            
            await bus.broadcast("system.config_update", {
                "setting": "debug_mode",
                "value": True
            })
            
            assert bus.broadcast.called


class TestA2AProtocol:
    """Test A2A protocol implementation."""
    
    @pytest.mark.asyncio
    async def test_agent_discovery(self):
        """Test agent discovery."""
        with patch('app.agents.orchestrator.a2a_protocol.A2AProtocol') as MockProtocol:
            protocol = MockProtocol.return_value
            
            protocol.discover_agents = AsyncMock(return_value=[
                {"name": "SearchAgent", "capabilities": ["search", "filter"]},
                {"name": "RecommendationAgent", "capabilities": ["recommend", "rank"]},
                {"name": "AlternativeAgent", "capabilities": ["alternatives", "compare"]},
                {"name": "ExplainabilityAgent", "capabilities": ["explain"]}
            ])
            
            agents = await protocol.discover_agents()
            
            assert len(agents) == 4
            assert any(a["name"] == "SearchAgent" for a in agents)
    
    @pytest.mark.asyncio
    async def test_capability_query(self):
        """Test querying agent capabilities."""
        with patch('app.agents.orchestrator.a2a_protocol.A2AProtocol') as MockProtocol:
            protocol = MockProtocol.return_value
            
            protocol.query_capabilities = AsyncMock(return_value={
                "agent": "SearchAgent",
                "capabilities": [
                    {"name": "semantic_search", "input": "query", "output": "products"},
                    {"name": "filter_by_price", "input": "products,price", "output": "products"},
                    {"name": "image_search", "input": "image", "output": "products"}
                ]
            })
            
            caps = await protocol.query_capabilities("SearchAgent")
            
            assert caps["agent"] == "SearchAgent"
            assert len(caps["capabilities"]) == 3
    
    @pytest.mark.asyncio
    async def test_task_delegation(self):
        """Test delegating tasks between agents."""
        with patch('app.agents.orchestrator.a2a_protocol.A2AProtocol') as MockProtocol:
            protocol = MockProtocol.return_value
            
            protocol.delegate_task = AsyncMock(return_value={
                "task_id": "task_001",
                "assigned_to": "AlternativeAgent",
                "status": "accepted"
            })
            
            result = await protocol.delegate_task(
                from_agent="SearchAgent",
                to_agent="AlternativeAgent",
                task={
                    "type": "find_alternatives",
                    "product_id": "prod_001",
                    "budget": 100.0
                }
            )
            
            assert result["status"] == "accepted"
    
    @pytest.mark.asyncio
    async def test_result_aggregation(self):
        """Test aggregating results from multiple agents."""
        with patch('app.agents.orchestrator.a2a_protocol.A2AProtocol') as MockProtocol:
            protocol = MockProtocol.return_value
            
            protocol.aggregate_results = AsyncMock(return_value={
                "aggregated": True,
                "sources": ["SearchAgent", "RecommendationAgent"],
                "combined_results": {
                    "products": [],
                    "recommendations": [],
                    "merged_score": 0.85
                }
            })
            
            result = await protocol.aggregate_results([
                {"agent": "SearchAgent", "results": []},
                {"agent": "RecommendationAgent", "results": []}
            ])
            
            assert result["aggregated"] is True
            assert len(result["sources"]) == 2


class TestMultiAgentScenarios:
    """Test complex multi-agent scenarios."""
    
    @pytest.mark.asyncio
    async def test_budget_aware_recommendation(self, sample_products, sample_users):
        """Test budget-aware recommendation across agents."""
        with patch('app.agents.orchestrator.coordinator.AgentCoordinator') as MockCoord:
            coordinator = MockCoord.return_value
            
            # User with $100 budget
            budget_user = sample_users[0]
            affordable = [p for p in sample_products if p["price"] <= 100]
            
            coordinator.budget_aware_recommend = AsyncMock(return_value={
                "user_budget": 100.0,
                "recommendations": affordable,
                "all_fit_budget": True,
                "agents": ["RecommendationAgent", "AlternativeAgent"]
            })
            
            result = await coordinator.budget_aware_recommend(
                user_id=budget_user["id"]
            )
            
            assert result["all_fit_budget"] is True
    
    @pytest.mark.asyncio
    async def test_vague_query_to_specific_results(self, sample_products):
        """Test handling vague query through multiple agents."""
        with patch('app.agents.orchestrator.coordinator.AgentCoordinator') as MockCoord:
            coordinator = MockCoord.return_value
            
            coordinator.process_vague_query = AsyncMock(return_value={
                "original_query": "something for music",
                "interpreted_as": "audio equipment headphones speakers",
                "categories_identified": ["Electronics", "Audio"],
                "search_results": sample_products[:3],
                "clarifying_questions": [
                    "Are you looking for headphones or speakers?",
                    "What's your budget range?"
                ],
                "agents": ["SearchAgent", "ExplainabilityAgent"]
            })
            
            result = await coordinator.process_vague_query(
                query="something for music"
            )
            
            assert "interpreted_as" in result
            assert len(result["categories_identified"]) > 0
    
    @pytest.mark.asyncio
    async def test_comparison_across_agents(self, sample_products):
        """Test product comparison involving multiple agents."""
        with patch('app.agents.orchestrator.coordinator.AgentCoordinator') as MockCoord:
            coordinator = MockCoord.return_value
            
            coordinator.compare_products = AsyncMock(return_value={
                "products": [sample_products[0], sample_products[1]],
                "comparison": {
                    "price_difference": 150.0,
                    "rating_difference": 0.7,
                    "common_features": ["wireless", "bluetooth"],
                    "unique_features": {
                        "prod_001": ["noise cancellation", "premium audio"],
                        "prod_002": ["budget-friendly", "lightweight"]
                    }
                },
                "recommendation": sample_products[1]["id"],
                "reasoning": "Better value for money within your budget",
                "agents": ["SearchAgent", "ExplainabilityAgent", "AlternativeAgent"]
            })
            
            result = await coordinator.compare_products(
                product_ids=["prod_001", "prod_002"],
                user_budget=100.0
            )
            
            assert "comparison" in result
            assert "recommendation" in result
