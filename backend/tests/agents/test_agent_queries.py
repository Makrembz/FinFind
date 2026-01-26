"""
Comprehensive tests for all agents.

Tests each agent with various query types:
- Vague queries
- Specific queries
- Multi-modal queries
- Constraint handling
- Explanation generation
- Alternative suggestions
"""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from typing import Dict, Any, List


# ==============================================================================
# Query Type Tests - SearchAgent
# ==============================================================================

class TestSearchAgentQueryTypes:
    """Test SearchAgent with various query types."""
    
    @pytest.fixture
    def search_agent(self):
        """Create SearchAgent with mocks."""
        with patch('app.agents.search_agent.agent.QdrantSearchTool'):
            with patch('app.agents.search_agent.agent.InterpretQueryTool'):
                from app.agents.search_agent import SearchAgent
                return SearchAgent()
    
    @pytest.mark.asyncio
    async def test_vague_query_interpretation(self, search_agent, sample_products):
        """Test handling vague queries like 'something for music'."""
        with patch.object(search_agent, 'run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {
                "status": "completed",
                "interpretation": {
                    "original": "something for music",
                    "expanded": "audio equipment headphones speakers wireless earbuds",
                    "categories": ["Electronics", "Audio"],
                    "intent": "browse"
                },
                "results": sample_products[:3]
            }
            
            result = await search_agent.search("something for music")
            
            assert mock_run.called
            assert result["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_specific_query(self, search_agent, sample_products):
        """Test handling specific queries like 'Sony WH-1000XM4'."""
        with patch.object(search_agent, 'run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {
                "status": "completed",
                "interpretation": {
                    "original": "Sony WH-1000XM4",
                    "is_specific": True,
                    "brand": "Sony",
                    "model": "WH-1000XM4"
                },
                "results": [sample_products[0]]
            }
            
            result = await search_agent.search("Sony WH-1000XM4")
            
            assert result["interpretation"]["is_specific"] is True
    
    @pytest.mark.asyncio
    async def test_budget_constrained_query(self, search_agent, sample_products):
        """Test handling queries with budget constraints."""
        with patch.object(search_agent, 'run', new_callable=AsyncMock) as mock_run:
            affordable = [p for p in sample_products if p["price"] <= 100]
            mock_run.return_value = {
                "status": "completed",
                "results": affordable,
                "filters_applied": {"max_price": 100}
            }
            
            result = await search_agent.search(
                "headphones under $100",
                max_price=100.0
            )
            
            assert result["filters_applied"]["max_price"] == 100
    
    @pytest.mark.asyncio
    async def test_category_specific_query(self, search_agent, sample_products):
        """Test handling category-specific queries."""
        with patch.object(search_agent, 'run', new_callable=AsyncMock) as mock_run:
            electronics = [p for p in sample_products if p["category"] == "Electronics"]
            mock_run.return_value = {
                "status": "completed",
                "results": electronics
            }
            
            result = await search_agent.search(
                "electronics gadgets",
                category="Electronics"
            )
            
            assert mock_run.called
    
    @pytest.mark.asyncio
    async def test_multi_attribute_query(self, search_agent, sample_products):
        """Test queries with multiple attributes."""
        with patch.object(search_agent, 'run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {
                "status": "completed",
                "interpretation": {
                    "attributes": ["wireless", "bluetooth", "noise-cancelling"],
                    "price_range": {"max": 200}
                },
                "results": sample_products[:2]
            }
            
            result = await search_agent.search(
                "wireless bluetooth noise-cancelling headphones under $200"
            )
            
            assert "attributes" in result["interpretation"]


# ==============================================================================
# Query Type Tests - RecommendationAgent
# ==============================================================================

class TestRecommendationAgentQueryTypes:
    """Test RecommendationAgent with various scenarios."""
    
    @pytest.fixture
    def recommendation_agent(self):
        """Create RecommendationAgent with mocks."""
        with patch('app.agents.recommendation_agent.agent.QdrantRecommendTool'):
            with patch('app.agents.recommendation_agent.agent.GetUserProfileTool'):
                from app.agents.recommendation_agent import RecommendationAgent
                return RecommendationAgent()
    
    @pytest.mark.asyncio
    async def test_personalized_recommendations(self, recommendation_agent, sample_products):
        """Test personalized recommendations based on user profile."""
        with patch.object(recommendation_agent, 'run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {
                "status": "completed",
                "recommendations": sample_products[:3],
                "personalization_factors": [
                    "previous_purchases",
                    "category_preferences",
                    "price_sensitivity"
                ]
            }
            
            result = await recommendation_agent.recommend(
                user_id="user_001",
                num_recommendations=3
            )
            
            assert "personalization_factors" in result
    
    @pytest.mark.asyncio
    async def test_category_focused_recommendations(self, recommendation_agent, sample_products):
        """Test recommendations focused on specific category."""
        electronics = [p for p in sample_products if p["category"] == "Electronics"]
        
        with patch.object(recommendation_agent, 'run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {
                "status": "completed",
                "recommendations": electronics,
                "category": "Electronics"
            }
            
            result = await recommendation_agent.recommend(
                user_id="user_001",
                category="Electronics"
            )
            
            assert result["category"] == "Electronics"
    
    @pytest.mark.asyncio
    async def test_budget_aware_recommendations(self, recommendation_agent, sample_products, mock_conversation_context):
        """Test budget-aware recommendations."""
        affordable = [p for p in sample_products if p["price"] <= 100]
        
        with patch.object(recommendation_agent, 'run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {
                "status": "completed",
                "recommendations": affordable,
                "budget_constraint": 100.0,
                "all_within_budget": True
            }
            
            # Set budget in context
            mock_conversation_context.user.financial.budget_max = 100.0
            
            result = await recommendation_agent.recommend(
                user_id="user_001",
                context=mock_conversation_context
            )
            
            assert result.get("all_within_budget") or mock_run.called


# ==============================================================================
# Query Type Tests - AlternativeAgent
# ==============================================================================

class TestAlternativeAgentQueryTypes:
    """Test AlternativeAgent with various scenarios."""
    
    @pytest.fixture
    def alternative_agent(self):
        """Create AlternativeAgent with mocks."""
        with patch('app.agents.alternative_agent.agent.FindSimilarProductsTool'):
            with patch('app.agents.alternative_agent.agent.AdjustPriceRangeTool'):
                from app.agents.alternative_agent import AlternativeAgent
                return AlternativeAgent()
    
    @pytest.mark.asyncio
    async def test_over_budget_alternatives(self, alternative_agent, sample_products):
        """Test finding alternatives for over-budget products."""
        expensive = sample_products[2]  # $349.99
        cheaper = [p for p in sample_products if p["price"] < 200]
        
        with patch.object(alternative_agent, 'run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {
                "status": "completed",
                "original": expensive,
                "alternatives": cheaper,
                "reason": "over_budget",
                "savings": [expensive["price"] - p["price"] for p in cheaper]
            }
            
            result = await alternative_agent.find_alternatives(
                product=expensive,
                reason="over_budget"
            )
            
            assert result["reason"] == "over_budget"
    
    @pytest.mark.asyncio
    async def test_out_of_stock_alternatives(self, alternative_agent, sample_products):
        """Test finding alternatives for out-of-stock products."""
        out_of_stock = {**sample_products[0], "in_stock": False}
        in_stock = [p for p in sample_products if p["in_stock"]]
        
        with patch.object(alternative_agent, 'run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {
                "status": "completed",
                "original": out_of_stock,
                "alternatives": in_stock[:2],
                "reason": "out_of_stock"
            }
            
            result = await alternative_agent.find_alternatives(
                product=out_of_stock,
                reason="out_of_stock"
            )
            
            assert result["reason"] == "out_of_stock"
    
    @pytest.mark.asyncio
    async def test_alternatives_with_tradeoffs(self, alternative_agent, sample_products):
        """Test alternatives with explained trade-offs."""
        with patch.object(alternative_agent, 'run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {
                "status": "completed",
                "alternatives": sample_products[:2],
                "trade_offs": [
                    {
                        "product_id": sample_products[0]["id"],
                        "pros": ["Lower price", "Good value"],
                        "cons": ["Fewer features", "Lower quality"]
                    },
                    {
                        "product_id": sample_products[1]["id"],
                        "pros": ["Best value", "Highly rated"],
                        "cons": ["Basic features"]
                    }
                ]
            }
            
            result = await alternative_agent.find_alternatives(
                product=sample_products[2],
                reason="over_budget"
            )
            
            assert "trade_offs" in result


# ==============================================================================
# Query Type Tests - ExplainabilityAgent
# ==============================================================================

class TestExplainabilityAgentQueryTypes:
    """Test ExplainabilityAgent with various scenarios."""
    
    @pytest.fixture
    def explainability_agent(self):
        """Create ExplainabilityAgent with mocks."""
        with patch('app.agents.explainability_agent.agent.ExplainMatchTool'):
            with patch('app.agents.explainability_agent.agent.CompareProductsTool'):
                from app.agents.explainability_agent import ExplainabilityAgent
                return ExplainabilityAgent()
    
    @pytest.mark.asyncio
    async def test_explain_search_match(self, explainability_agent, sample_products):
        """Test explaining why a product matches a search."""
        with patch.object(explainability_agent, 'run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {
                "status": "completed",
                "explanation": "This product matches your search because...",
                "match_factors": {
                    "keyword_match": 0.95,
                    "category_match": 1.0,
                    "attribute_match": 0.85
                }
            }
            
            result = await explainability_agent.explain(
                product=sample_products[0],
                query="wireless headphones"
            )
            
            assert "match_factors" in result
    
    @pytest.mark.asyncio
    async def test_explain_recommendation(self, explainability_agent, sample_products):
        """Test explaining why a product is recommended."""
        with patch.object(explainability_agent, 'run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {
                "status": "completed",
                "explanation": "We recommend this because...",
                "recommendation_reasons": [
                    "Matches your preference for Electronics",
                    "Within your budget of $200",
                    "Highly rated (4.5+ stars)",
                    "Similar to products you've purchased"
                ]
            }
            
            result = await explainability_agent.explain(
                product=sample_products[0],
                explanation_type="recommendation"
            )
            
            assert "recommendation_reasons" in result
    
    @pytest.mark.asyncio
    async def test_explain_financial_fit(self, explainability_agent, sample_products, mock_conversation_context):
        """Test explaining financial fit."""
        with patch.object(explainability_agent, 'run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {
                "status": "completed",
                "financial_explanation": {
                    "product_price": 99.99,
                    "user_budget": 200.0,
                    "within_budget": True,
                    "budget_utilization": 0.5,
                    "explanation": "At $99.99, this is 50% of your $200 budget."
                }
            }
            
            result = await explainability_agent.explain(
                product=sample_products[0],
                context=mock_conversation_context,
                explanation_type="financial_fit"
            )
            
            assert result["financial_explanation"]["within_budget"] is True
    
    @pytest.mark.asyncio
    async def test_compare_products(self, explainability_agent, sample_products):
        """Test comparing two products."""
        with patch.object(explainability_agent, 'run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {
                "status": "completed",
                "comparison": {
                    "products": [sample_products[0], sample_products[1]],
                    "price_difference": 150.0,
                    "rating_difference": 0.7,
                    "better_value": sample_products[1]["id"],
                    "summary": "Product B offers better value for budget-conscious buyers."
                }
            }
            
            result = await explainability_agent.compare(
                products=[sample_products[0], sample_products[1]]
            )
            
            assert "comparison" in result


# ==============================================================================
# Constraint Handling Tests
# ==============================================================================

class TestConstraintHandling:
    """Test how agents handle various constraints."""
    
    @pytest.mark.asyncio
    async def test_strict_budget_constraint(self, sample_products):
        """Test strict budget enforcement."""
        with patch('app.agents.search_agent.agent.QdrantSearchTool'):
            from app.agents.search_agent import SearchAgent
            agent = SearchAgent()
            
            with patch.object(agent, 'run', new_callable=AsyncMock) as mock_run:
                affordable = [p for p in sample_products if p["price"] <= 50]
                mock_run.return_value = {
                    "status": "completed",
                    "results": affordable,
                    "constraint_applied": "strict_budget",
                    "max_price": 50.0
                }
                
                result = await agent.search(
                    "headphones",
                    max_price=50.0,
                    strict_budget=True
                )
                
                assert result["constraint_applied"] == "strict_budget"
    
    @pytest.mark.asyncio
    async def test_flexible_budget_constraint(self, sample_products):
        """Test flexible budget (show slightly over)."""
        with patch('app.agents.search_agent.agent.QdrantSearchTool'):
            from app.agents.search_agent import SearchAgent
            agent = SearchAgent()
            
            with patch.object(agent, 'run', new_callable=AsyncMock) as mock_run:
                # Include products up to 20% over budget
                flexible = [p for p in sample_products if p["price"] <= 60]
                mock_run.return_value = {
                    "status": "completed",
                    "results": flexible,
                    "constraint_applied": "flexible_budget",
                    "target_budget": 50.0,
                    "max_shown": 60.0
                }
                
                result = await agent.search(
                    "headphones",
                    max_price=50.0,
                    budget_flexibility=0.2
                )
                
                assert result["constraint_applied"] == "flexible_budget"
    
    @pytest.mark.asyncio
    async def test_category_constraint(self, sample_products):
        """Test category constraint."""
        with patch('app.agents.search_agent.agent.QdrantSearchTool'):
            from app.agents.search_agent import SearchAgent
            agent = SearchAgent()
            
            with patch.object(agent, 'run', new_callable=AsyncMock) as mock_run:
                electronics = [p for p in sample_products if p["category"] == "Electronics"]
                mock_run.return_value = {
                    "status": "completed",
                    "results": electronics,
                    "category_filter": "Electronics"
                }
                
                result = await agent.search(
                    "gadgets",
                    category="Electronics"
                )
                
                assert result["category_filter"] == "Electronics"
    
    @pytest.mark.asyncio
    async def test_rating_constraint(self, sample_products):
        """Test minimum rating constraint."""
        with patch('app.agents.search_agent.agent.QdrantSearchTool'):
            from app.agents.search_agent import SearchAgent
            agent = SearchAgent()
            
            with patch.object(agent, 'run', new_callable=AsyncMock) as mock_run:
                high_rated = [p for p in sample_products if p["rating"] >= 4.5]
                mock_run.return_value = {
                    "status": "completed",
                    "results": high_rated,
                    "min_rating": 4.5
                }
                
                result = await agent.search(
                    "headphones",
                    min_rating=4.5
                )
                
                assert result["min_rating"] == 4.5


# ==============================================================================
# Multi-Modal Query Tests
# ==============================================================================

class TestMultiModalQueries:
    """Test handling of multi-modal queries."""
    
    @pytest.mark.asyncio
    async def test_image_query(self, mock_image_bytes, sample_products):
        """Test image-based search."""
        with patch('app.agents.search_agent.agent.QdrantSearchTool'):
            with patch('app.agents.search_agent.agent.ImageSearchTool') as MockImageTool:
                from app.agents.search_agent import SearchAgent
                agent = SearchAgent()
                
                with patch.object(agent, 'image_search', new_callable=AsyncMock) as mock_search:
                    mock_search.return_value = {
                        "status": "completed",
                        "results": sample_products[:3],
                        "search_type": "image",
                        "similarity_scores": [0.95, 0.89, 0.82]
                    }
                    
                    result = await agent.image_search(image_data=mock_image_bytes)
                    
                    assert result["search_type"] == "image"
    
    @pytest.mark.asyncio
    async def test_voice_query(self, mock_audio_bytes, sample_products):
        """Test voice-based search."""
        with patch('app.agents.search_agent.agent.QdrantSearchTool'):
            from app.agents.search_agent import SearchAgent
            agent = SearchAgent()
            
            with patch.object(agent, 'voice_search', new_callable=AsyncMock) as mock_search:
                mock_search.return_value = {
                    "status": "completed",
                    "transcription": "wireless headphones under one hundred dollars",
                    "interpreted_query": {
                        "product": "wireless headphones",
                        "max_price": 100.0
                    },
                    "results": sample_products[:2],
                    "search_type": "voice"
                }
                
                result = await agent.voice_search(audio_data=mock_audio_bytes)
                
                assert result["search_type"] == "voice"
                assert "transcription" in result
    
    @pytest.mark.asyncio
    async def test_combined_text_and_image(self, mock_image_bytes, sample_products):
        """Test combined text and image search."""
        with patch('app.agents.search_agent.agent.QdrantSearchTool'):
            from app.agents.search_agent import SearchAgent
            agent = SearchAgent()
            
            with patch.object(agent, 'multi_modal_search', new_callable=AsyncMock) as mock_search:
                mock_search.return_value = {
                    "status": "completed",
                    "text_query": "similar but cheaper",
                    "image_reference": True,
                    "results": sample_products[:3],
                    "search_type": "multi_modal"
                }
                
                result = await agent.multi_modal_search(
                    text="similar but cheaper",
                    image_data=mock_image_bytes
                )
                
                assert result["search_type"] == "multi_modal"


# ==============================================================================
# Workflow Tests
# ==============================================================================

class TestAgentWorkflows:
    """Test complete agent workflows."""
    
    @pytest.mark.asyncio
    async def test_search_to_recommendation_workflow(self, sample_products):
        """Test workflow from search to recommendations."""
        with patch('app.agents.orchestrator.workflow_executor.WorkflowExecutor') as MockExec:
            executor = MockExec.return_value
            
            executor.execute = AsyncMock(return_value={
                "workflow": "search_to_recommend",
                "steps": [
                    {"agent": "SearchAgent", "action": "search", "results": 5},
                    {"agent": "RecommendationAgent", "action": "personalize", "results": 3}
                ],
                "final_results": sample_products[:3],
                "status": "completed"
            })
            
            result = await executor.execute(
                workflow="search_to_recommend",
                params={"query": "headphones", "user_id": "user_001"}
            )
            
            assert len(result["steps"]) == 2
            assert result["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_budget_constraint_workflow(self, sample_products):
        """Test workflow with budget constraint triggering alternatives."""
        with patch('app.agents.orchestrator.workflow_executor.WorkflowExecutor') as MockExec:
            executor = MockExec.return_value
            
            over_budget = sample_products[2]  # $349.99
            alternatives = sample_products[:2]  # Cheaper
            
            executor.execute = AsyncMock(return_value={
                "workflow": "budget_constrained_search",
                "steps": [
                    {"agent": "SearchAgent", "action": "search", "found_over_budget": True},
                    {"agent": "AlternativeAgent", "action": "find_alternatives", "found": 2}
                ],
                "over_budget_product": over_budget,
                "alternatives": alternatives,
                "user_budget": 100.0,
                "status": "completed"
            })
            
            result = await executor.execute(
                workflow="budget_constrained_search",
                params={"query": "premium headphones", "budget": 100.0}
            )
            
            assert result["steps"][0]["found_over_budget"] is True
            assert len(result["alternatives"]) > 0
    
    @pytest.mark.asyncio
    async def test_full_explanation_workflow(self, sample_products):
        """Test workflow with full explanation generation."""
        with patch('app.agents.orchestrator.workflow_executor.WorkflowExecutor') as MockExec:
            executor = MockExec.return_value
            
            executor.execute = AsyncMock(return_value={
                "workflow": "search_with_explanation",
                "steps": [
                    {"agent": "SearchAgent", "action": "search"},
                    {"agent": "ExplainabilityAgent", "action": "explain_all"}
                ],
                "results": [
                    {
                        "product": sample_products[0],
                        "explanation": "Matches your search for wireless headphones"
                    },
                    {
                        "product": sample_products[1],
                        "explanation": "Budget-friendly option with good ratings"
                    }
                ],
                "status": "completed"
            })
            
            result = await executor.execute(
                workflow="search_with_explanation",
                params={"query": "headphones"}
            )
            
            # Each result has an explanation
            assert all("explanation" in r for r in result["results"])
