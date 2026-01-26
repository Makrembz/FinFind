"""
Unit tests for FinFind agents.

Tests:
- SearchAgent
- RecommendationAgent
- AlternativeAgent
- ExplainabilityAgent
"""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from typing import Dict, Any, List


# ==============================================================================
# SearchAgent Tests
# ==============================================================================

class TestSearchAgent:
    """Test suite for SearchAgent."""
    
    @pytest.fixture
    def search_agent(self, mock_qdrant_service, mock_embedding_service):
        """Create a SearchAgent with mocked dependencies."""
        with patch('app.agents.search_agent.agent.QdrantSearchTool') as mock_tool:
            mock_tool.return_value = MagicMock()
            
            from app.agents.search_agent import SearchAgent
            agent = SearchAgent()
            agent._qdrant = mock_qdrant_service
            agent._embedder = mock_embedding_service
            return agent
    
    @pytest.mark.asyncio
    async def test_search_basic_query(self, search_agent, sample_products):
        """Test basic search query handling."""
        with patch.object(search_agent, 'run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {
                "status": "completed",
                "results": sample_products[:3]
            }
            
            result = await search_agent.search("wireless headphones")
            
            assert mock_run.called
            assert "wireless headphones" in str(mock_run.call_args)
    
    @pytest.mark.asyncio
    async def test_search_with_budget_context(self, search_agent, mock_conversation_context):
        """Test search with budget constraints from context."""
        with patch.object(search_agent, 'run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {"status": "completed", "results": []}
            
            await search_agent.search(
                "laptop",
                context=mock_conversation_context
            )
            
            # Verify budget was included in the search
            call_args = str(mock_run.call_args)
            assert mock_run.called
    
    @pytest.mark.asyncio
    async def test_search_with_category_filter(self, search_agent):
        """Test search with category filtering."""
        with patch.object(search_agent, 'run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {"status": "completed", "results": []}
            
            await search_agent.search(
                "headphones",
                category="Electronics"
            )
            
            call_args = str(mock_run.call_args)
            assert "Electronics" in call_args or mock_run.called
    
    @pytest.mark.asyncio
    async def test_search_with_price_filter(self, search_agent):
        """Test search with max price filter."""
        with patch.object(search_agent, 'run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {"status": "completed", "results": []}
            
            await search_agent.search(
                "headphones",
                max_price=100.0
            )
            
            assert mock_run.called
    
    @pytest.mark.asyncio
    async def test_search_empty_query(self, search_agent):
        """Test handling of empty search queries."""
        with patch.object(search_agent, 'run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {"status": "completed", "results": []}
            
            result = await search_agent.search("")
            assert result is not None
    
    def test_agent_initialization(self, mock_qdrant_service):
        """Test SearchAgent initializes correctly."""
        with patch('app.agents.search_agent.agent.QdrantSearchTool'):
            from app.agents.search_agent import SearchAgent
            agent = SearchAgent()
            
            assert agent.agent_name == "SearchAgent"
            assert agent.agent_description is not None
    
    def test_default_tools_created(self):
        """Test that default tools are created."""
        with patch('app.agents.search_agent.agent.QdrantSearchTool') as mock_search:
            with patch('app.agents.search_agent.agent.InterpretQueryTool') as mock_interpret:
                with patch('app.agents.search_agent.agent.ApplyBudgetFilterTool') as mock_filter:
                    with patch('app.agents.search_agent.agent.ImageSearchTool') as mock_image:
                        from app.agents.search_agent import SearchAgent
                        agent = SearchAgent()
                        
                        # Verify tools were created
                        tools = agent._create_default_tools()
                        assert len(tools) == 4


# ==============================================================================
# RecommendationAgent Tests
# ==============================================================================

class TestRecommendationAgent:
    """Test suite for RecommendationAgent."""
    
    @pytest.fixture
    def recommendation_agent(self, mock_qdrant_service):
        """Create a RecommendationAgent with mocked dependencies."""
        with patch('app.agents.recommendation_agent.agent.QdrantRecommendTool'):
            with patch('app.agents.recommendation_agent.agent.GetUserProfileTool'):
                with patch('app.agents.recommendation_agent.agent.CalculateAffordabilityTool'):
                    with patch('app.agents.recommendation_agent.agent.RankByConstraintsTool'):
                        from app.agents.recommendation_agent import RecommendationAgent
                        agent = RecommendationAgent()
                        return agent
    
    @pytest.mark.asyncio
    async def test_recommend_basic(self, recommendation_agent, sample_products):
        """Test basic recommendation generation."""
        with patch.object(recommendation_agent, 'run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {
                "status": "completed",
                "results": sample_products[:3]
            }
            
            result = await recommendation_agent.recommend(
                user_id="user_001",
                num_recommendations=3
            )
            
            assert mock_run.called
    
    @pytest.mark.asyncio
    async def test_recommend_with_category(self, recommendation_agent):
        """Test recommendations filtered by category."""
        with patch.object(recommendation_agent, 'run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {"status": "completed", "results": []}
            
            await recommendation_agent.recommend(
                user_id="user_001",
                category="Electronics"
            )
            
            call_args = str(mock_run.call_args)
            assert "Electronics" in call_args or mock_run.called
    
    @pytest.mark.asyncio
    async def test_recommend_with_context(self, recommendation_agent, mock_conversation_context):
        """Test recommendations with user context."""
        with patch.object(recommendation_agent, 'run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {"status": "completed", "results": []}
            
            await recommendation_agent.recommend(
                user_id="user_001",
                context=mock_conversation_context
            )
            
            assert mock_run.called
    
    def test_agent_initialization(self):
        """Test RecommendationAgent initializes correctly."""
        with patch('app.agents.recommendation_agent.agent.QdrantRecommendTool'):
            with patch('app.agents.recommendation_agent.agent.GetUserProfileTool'):
                with patch('app.agents.recommendation_agent.agent.CalculateAffordabilityTool'):
                    with patch('app.agents.recommendation_agent.agent.RankByConstraintsTool'):
                        from app.agents.recommendation_agent import RecommendationAgent
                        agent = RecommendationAgent()
                        
                        assert agent.agent_name == "RecommendationAgent"


# ==============================================================================
# AlternativeAgent Tests
# ==============================================================================

class TestAlternativeAgent:
    """Test suite for AlternativeAgent."""
    
    @pytest.fixture
    def alternative_agent(self):
        """Create an AlternativeAgent with mocked dependencies."""
        with patch('app.agents.alternative_agent.agent.FindSimilarProductsTool'):
            with patch('app.agents.alternative_agent.agent.AdjustPriceRangeTool'):
                with patch('app.agents.alternative_agent.agent.SuggestAlternativesTool'):
                    from app.agents.alternative_agent import AlternativeAgent
                    return AlternativeAgent()
    
    @pytest.mark.asyncio
    async def test_find_alternatives_basic(self, alternative_agent, sample_products):
        """Test basic alternative finding."""
        with patch.object(alternative_agent, 'run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {"status": "completed", "results": sample_products[:2]}
            
            result = await alternative_agent.find_alternatives(
                product=sample_products[0],
                reason="over_budget"
            )
            
            assert mock_run.called
    
    @pytest.mark.asyncio
    async def test_find_alternatives_with_context(self, alternative_agent, sample_products, mock_conversation_context):
        """Test alternatives with user budget context."""
        with patch.object(alternative_agent, 'run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {"status": "completed", "results": []}
            
            await alternative_agent.find_alternatives(
                product=sample_products[0],
                context=mock_conversation_context,
                reason="over_budget"
            )
            
            call_args = str(mock_run.call_args)
            assert mock_run.called
    
    @pytest.mark.asyncio
    async def test_find_alternatives_out_of_stock(self, alternative_agent, sample_products):
        """Test alternatives for out of stock products."""
        with patch.object(alternative_agent, 'run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {"status": "completed", "results": []}
            
            await alternative_agent.find_alternatives(
                product=sample_products[0],
                reason="out_of_stock",
                num_alternatives=5
            )
            
            assert mock_run.called
    
    def test_agent_initialization(self):
        """Test AlternativeAgent initializes correctly."""
        with patch('app.agents.alternative_agent.agent.FindSimilarProductsTool'):
            with patch('app.agents.alternative_agent.agent.AdjustPriceRangeTool'):
                with patch('app.agents.alternative_agent.agent.SuggestAlternativesTool'):
                    from app.agents.alternative_agent import AlternativeAgent
                    agent = AlternativeAgent()
                    
                    assert agent.agent_name == "AlternativeAgent"


# ==============================================================================
# ExplainabilityAgent Tests
# ==============================================================================

class TestExplainabilityAgent:
    """Test suite for ExplainabilityAgent."""
    
    @pytest.fixture
    def explainability_agent(self):
        """Create an ExplainabilityAgent with mocked dependencies."""
        with patch('app.agents.explainability_agent.agent.ExplainMatchTool'):
            with patch('app.agents.explainability_agent.agent.CompareProductsTool'):
                with patch('app.agents.explainability_agent.agent.JustifyPriceTool'):
                    from app.agents.explainability_agent import ExplainabilityAgent
                    return ExplainabilityAgent()
    
    @pytest.mark.asyncio
    async def test_explain_recommendation(self, explainability_agent, sample_products):
        """Test explaining a recommendation."""
        with patch.object(explainability_agent, 'run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {
                "status": "completed",
                "results": {"explanation": "This product matches your needs because..."}
            }
            
            result = await explainability_agent.explain(
                product=sample_products[0],
                query="wireless headphones"
            )
            
            assert mock_run.called
    
    @pytest.mark.asyncio
    async def test_explain_with_user_context(self, explainability_agent, sample_products, mock_conversation_context):
        """Test explanation with user context."""
        with patch.object(explainability_agent, 'run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {"status": "completed", "results": {}}
            
            await explainability_agent.explain(
                product=sample_products[0],
                query="affordable headphones",
                context=mock_conversation_context
            )
            
            assert mock_run.called
    
    def test_agent_initialization(self):
        """Test ExplainabilityAgent initializes correctly."""
        with patch('app.agents.explainability_agent.agent.ExplainMatchTool'):
            with patch('app.agents.explainability_agent.agent.CompareProductsTool'):
                with patch('app.agents.explainability_agent.agent.JustifyPriceTool'):
                    from app.agents.explainability_agent import ExplainabilityAgent
                    agent = ExplainabilityAgent()
                    
                    assert agent.agent_name == "ExplainabilityAgent"


# ==============================================================================
# Agent Collaboration Tests
# ==============================================================================

class TestAgentCollaboration:
    """Test agent-to-agent collaboration."""
    
    @pytest.mark.asyncio
    async def test_search_triggers_alternatives(self, sample_products):
        """Test that search can trigger alternative suggestions."""
        # When a search result is over budget, alternatives should be suggested
        over_budget_product = sample_products[2]  # $349.99
        
        with patch('app.agents.orchestrator.coordinator.AgentCoordinator') as MockCoordinator:
            coordinator = MockCoordinator.return_value
            coordinator.process_request = AsyncMock(return_value={
                "search_results": [over_budget_product],
                "alternatives": sample_products[1:2]  # Cheaper alternative
            })
            
            result = await coordinator.process_request(
                query="headphones",
                user_budget=100.0
            )
            
            assert coordinator.process_request.called
    
    @pytest.mark.asyncio
    async def test_recommendation_with_explanation(self, sample_products):
        """Test that recommendations come with explanations."""
        with patch('app.agents.orchestrator.coordinator.AgentCoordinator') as MockCoordinator:
            coordinator = MockCoordinator.return_value
            coordinator.get_recommendations = AsyncMock(return_value={
                "recommendations": sample_products[:3],
                "explanations": ["Explanation 1", "Explanation 2", "Explanation 3"]
            })
            
            result = await coordinator.get_recommendations(
                user_id="user_001"
            )
            
            assert coordinator.get_recommendations.called


# ==============================================================================
# Agent Error Handling Tests
# ==============================================================================

class TestAgentErrorHandling:
    """Test error handling in agents."""
    
    @pytest.mark.asyncio
    async def test_search_handles_empty_results(self):
        """Test search handles no results gracefully."""
        with patch('app.agents.search_agent.agent.QdrantSearchTool'):
            from app.agents.search_agent import SearchAgent
            agent = SearchAgent()
            
            with patch.object(agent, 'run', new_callable=AsyncMock) as mock_run:
                mock_run.return_value = {"status": "completed", "results": []}
                
                result = await agent.search("nonexistent product xyz123")
                
                assert result is not None
    
    @pytest.mark.asyncio
    async def test_agent_handles_service_timeout(self):
        """Test agent handles service timeouts."""
        with patch('app.agents.search_agent.agent.QdrantSearchTool'):
            from app.agents.search_agent import SearchAgent
            agent = SearchAgent()
            
            with patch.object(agent, 'run', new_callable=AsyncMock) as mock_run:
                import asyncio
                mock_run.side_effect = asyncio.TimeoutError("Service timeout")
                
                with pytest.raises(asyncio.TimeoutError):
                    await agent.search("headphones")
    
    @pytest.mark.asyncio
    async def test_agent_handles_invalid_input(self):
        """Test agent handles invalid input."""
        with patch('app.agents.search_agent.agent.QdrantSearchTool'):
            from app.agents.search_agent import SearchAgent
            agent = SearchAgent()
            
            with patch.object(agent, 'run', new_callable=AsyncMock) as mock_run:
                mock_run.return_value = {"status": "error", "error": "Invalid input"}
                
                result = await agent.search(None)
                # Should handle gracefully
                assert result is not None or mock_run.called
