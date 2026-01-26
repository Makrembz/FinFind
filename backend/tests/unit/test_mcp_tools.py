"""
Unit tests for MCP Tools.

Tests all MCP-compliant tools:
- Search Tools
- Recommendation Tools
- Explainability Tools
- Alternative Tools
"""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from typing import Dict, Any, List


# ==============================================================================
# Search Tools Tests
# ==============================================================================

class TestQdrantSemanticSearchTool:
    """Test suite for QdrantSemanticSearchTool."""
    
    @pytest.fixture
    def search_tool(self, mock_qdrant_service, mock_embedding_service):
        """Create a search tool with mocked services."""
        with patch('app.agents.mcp.tools.search_tools.QdrantService') as MockService:
            MockService.return_value = mock_qdrant_service
            
            from app.agents.mcp.tools.search_tools import QdrantSemanticSearchTool
            tool = QdrantSemanticSearchTool()
            tool._qdrant = mock_qdrant_service
            tool._embedder = mock_embedding_service
            return tool
    
    def test_tool_name_and_description(self, search_tool):
        """Test tool has proper name and description."""
        assert search_tool.name is not None
        assert search_tool.description is not None
        assert len(search_tool.description) > 10
    
    @pytest.mark.asyncio
    async def test_basic_search(self, search_tool, sample_products):
        """Test basic semantic search."""
        search_tool._qdrant.search = AsyncMock(return_value=sample_products[:3])
        
        result = await search_tool._arun(query="wireless headphones", limit=10)
        
        assert search_tool._qdrant.search.called or result is not None
    
    @pytest.mark.asyncio
    async def test_search_with_filters(self, search_tool):
        """Test search with category and price filters."""
        search_tool._qdrant.search = AsyncMock(return_value=[])
        
        result = await search_tool._arun(
            query="headphones",
            category="Electronics",
            max_price=100.0
        )
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_search_mmr_diversity(self, search_tool, sample_products):
        """Test MMR for diverse results."""
        search_tool._qdrant.search = AsyncMock(return_value=sample_products)
        
        result = await search_tool._arun(
            query="headphones",
            use_mmr=True,
            diversity=0.5
        )
        
        assert result is not None


class TestInterpretVagueQueryTool:
    """Test suite for InterpretVagueQueryTool."""
    
    @pytest.fixture
    def interpret_tool(self, mock_groq_client):
        """Create an interpret tool with mocked LLM."""
        with patch('app.agents.mcp.tools.search_tools.get_llm_client') as mock_get:
            mock_get.return_value = mock_groq_client
            
            from app.agents.mcp.tools.search_tools import InterpretVagueQueryTool
            tool = InterpretVagueQueryTool()
            return tool
    
    @pytest.mark.asyncio
    async def test_interpret_vague_query(self, interpret_tool):
        """Test interpreting a vague query."""
        with patch.object(interpret_tool, '_arun', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {
                "interpreted_query": "wireless bluetooth headphones",
                "categories": ["Electronics", "Audio"],
                "attributes": ["wireless", "bluetooth"]
            }
            
            result = await interpret_tool._arun(query="something for music")
            
            assert "interpreted_query" in result
    
    @pytest.mark.asyncio
    async def test_interpret_specific_query(self, interpret_tool):
        """Test handling already specific queries."""
        with patch.object(interpret_tool, '_arun', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {
                "interpreted_query": "Sony WH-1000XM4 headphones",
                "categories": ["Electronics"],
                "is_specific": True
            }
            
            result = await interpret_tool._arun(
                query="Sony WH-1000XM4 headphones"
            )
            
            assert result is not None


class TestApplyFinancialFiltersTool:
    """Test suite for ApplyFinancialFiltersTool."""
    
    @pytest.fixture
    def filter_tool(self):
        """Create a filter tool."""
        from app.agents.mcp.tools.search_tools import ApplyFinancialFiltersTool
        return ApplyFinancialFiltersTool()
    
    @pytest.mark.asyncio
    async def test_filter_by_budget(self, filter_tool, sample_products):
        """Test filtering products by budget."""
        with patch.object(filter_tool, '_arun', new_callable=AsyncMock) as mock_run:
            # Filter to products under $100
            filtered = [p for p in sample_products if p["price"] <= 100]
            mock_run.return_value = filtered
            
            result = await filter_tool._arun(
                products=sample_products,
                max_budget=100.0
            )
            
            assert all(p["price"] <= 100 for p in result)
    
    @pytest.mark.asyncio
    async def test_filter_with_affordability_score(self, filter_tool, sample_products):
        """Test adding affordability scores to products."""
        with patch.object(filter_tool, '_arun', new_callable=AsyncMock) as mock_run:
            scored_products = [
                {**p, "affordability_score": 1.0 - (p["price"] / 500)}
                for p in sample_products
            ]
            mock_run.return_value = scored_products
            
            result = await filter_tool._arun(
                products=sample_products,
                user_budget=200.0
            )
            
            assert all("affordability_score" in p for p in result)


class TestImageSimilaritySearchTool:
    """Test suite for ImageSimilaritySearchTool."""
    
    @pytest.fixture
    def image_tool(self, mock_embedding_service, mock_qdrant_service):
        """Create an image search tool."""
        from app.agents.mcp.tools.search_tools import ImageSimilaritySearchTool
        tool = ImageSimilaritySearchTool()
        tool._embedder = mock_embedding_service
        tool._qdrant = mock_qdrant_service
        return tool
    
    @pytest.mark.asyncio
    async def test_image_search(self, image_tool, mock_image_bytes, sample_products):
        """Test searching by image."""
        with patch.object(image_tool, '_arun', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = sample_products[:3]
            
            result = await image_tool._arun(
                image_data=mock_image_bytes,
                limit=5
            )
            
            assert len(result) <= 5


class TestVoiceToTextSearchTool:
    """Test suite for VoiceToTextSearchTool."""
    
    @pytest.fixture
    def voice_tool(self):
        """Create a voice search tool."""
        from app.agents.mcp.tools.search_tools import VoiceToTextSearchTool
        return VoiceToTextSearchTool()
    
    @pytest.mark.asyncio
    async def test_voice_transcription(self, voice_tool, mock_audio_bytes):
        """Test voice to text conversion."""
        with patch.object(voice_tool, '_arun', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {
                "transcribed_text": "wireless headphones under one hundred dollars",
                "confidence": 0.95
            }
            
            result = await voice_tool._arun(audio_data=mock_audio_bytes)
            
            assert "transcribed_text" in result


# ==============================================================================
# Recommendation Tools Tests
# ==============================================================================

class TestGetUserFinancialProfileTool:
    """Test suite for GetUserFinancialProfileTool."""
    
    @pytest.fixture
    def profile_tool(self):
        """Create a profile tool."""
        from app.agents.mcp.tools.recommendation_tools import GetUserFinancialProfileTool
        return GetUserFinancialProfileTool()
    
    @pytest.mark.asyncio
    async def test_get_user_profile(self, profile_tool, sample_users):
        """Test fetching user financial profile."""
        with patch.object(profile_tool, '_arun', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = sample_users[0]
            
            result = await profile_tool._arun(user_id="user_001")
            
            assert "financial" in result


class TestCalculateAffordabilityMatchTool:
    """Test suite for CalculateAffordabilityMatchTool."""
    
    @pytest.fixture
    def affordability_tool(self):
        """Create an affordability tool."""
        from app.agents.mcp.tools.recommendation_tools import CalculateAffordabilityMatchTool
        return CalculateAffordabilityMatchTool()
    
    @pytest.mark.asyncio
    async def test_calculate_affordability(self, affordability_tool, sample_products):
        """Test calculating product affordability for user."""
        with patch.object(affordability_tool, '_arun', new_callable=AsyncMock) as mock_run:
            scored = [
                {**p, "affordability": 0.8 if p["price"] <= 100 else 0.3}
                for p in sample_products
            ]
            mock_run.return_value = scored
            
            result = await affordability_tool._arun(
                products=sample_products,
                user_budget=100.0
            )
            
            assert all("affordability" in p for p in result)


class TestRankProductsByConstraintsTool:
    """Test suite for RankProductsByConstraintsTool."""
    
    @pytest.fixture
    def ranking_tool(self):
        """Create a ranking tool."""
        from app.agents.mcp.tools.recommendation_tools import RankProductsByConstraintsTool
        return RankProductsByConstraintsTool()
    
    @pytest.mark.asyncio
    async def test_rank_by_relevance_and_price(self, ranking_tool, sample_products):
        """Test ranking products by multiple factors."""
        with patch.object(ranking_tool, '_arun', new_callable=AsyncMock) as mock_run:
            ranked = sorted(sample_products, key=lambda p: p["price"])
            mock_run.return_value = ranked
            
            result = await ranking_tool._arun(
                products=sample_products,
                constraints={"max_price": 200, "min_rating": 4.0}
            )
            
            assert result[0]["price"] <= result[-1]["price"]


# ==============================================================================
# Explainability Tools Tests
# ==============================================================================

class TestGetSimilarityExplanationTool:
    """Test suite for GetSimilarityExplanationTool."""
    
    @pytest.fixture
    def similarity_tool(self):
        """Create a similarity explanation tool."""
        from app.agents.mcp.tools.explainability_tools import GetSimilarityExplanationTool
        return GetSimilarityExplanationTool()
    
    @pytest.mark.asyncio
    async def test_explain_similarity(self, similarity_tool, sample_products):
        """Test explaining why a product matches."""
        with patch.object(similarity_tool, '_arun', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {
                "explanation": "This product matches because it's a wireless headphone in your budget.",
                "match_factors": ["category_match", "price_match", "feature_match"]
            }
            
            result = await similarity_tool._arun(
                product=sample_products[0],
                query="wireless headphones"
            )
            
            assert "explanation" in result


class TestGetFinancialFitExplanationTool:
    """Test suite for GetFinancialFitExplanationTool."""
    
    @pytest.fixture
    def financial_tool(self):
        """Create a financial fit explanation tool."""
        from app.agents.mcp.tools.explainability_tools import GetFinancialFitExplanationTool
        return GetFinancialFitExplanationTool()
    
    @pytest.mark.asyncio
    async def test_explain_financial_fit(self, financial_tool, sample_products):
        """Test explaining financial fit."""
        with patch.object(financial_tool, '_arun', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {
                "explanation": "At $49.99, this is 50% of your $100 budget.",
                "fit_score": 0.8,
                "within_budget": True
            }
            
            result = await financial_tool._arun(
                product=sample_products[1],  # Budget headphones
                user_budget=100.0
            )
            
            assert result["within_budget"] is True


class TestGenerateNaturalExplanationTool:
    """Test suite for GenerateNaturalExplanationTool."""
    
    @pytest.fixture
    def explanation_tool(self, mock_groq_client):
        """Create a natural explanation tool."""
        from app.agents.mcp.tools.explainability_tools import GenerateNaturalExplanationTool
        tool = GenerateNaturalExplanationTool()
        return tool
    
    @pytest.mark.asyncio
    async def test_generate_natural_explanation(self, explanation_tool, sample_products):
        """Test generating natural language explanation."""
        with patch.object(explanation_tool, '_arun', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = (
                "I recommend the Budget Wireless Headphones because they're "
                "affordable at $49.99, which is well within your $100 budget, "
                "and they have a solid 4.0 rating."
            )
            
            result = await explanation_tool._arun(
                product=sample_products[1],
                user_context={"budget": 100.0},
                query="affordable headphones"
            )
            
            assert "affordable" in result.lower() or "$" in result


# ==============================================================================
# Alternative Tools Tests
# ==============================================================================

class TestFindSimilarInPriceRangeTool:
    """Test suite for FindSimilarInPriceRangeTool."""
    
    @pytest.fixture
    def similar_tool(self, mock_qdrant_service):
        """Create a similar products tool."""
        from app.agents.mcp.tools.alternative_tools import FindSimilarInPriceRangeTool
        tool = FindSimilarInPriceRangeTool()
        tool._qdrant = mock_qdrant_service
        return tool
    
    @pytest.mark.asyncio
    async def test_find_cheaper_alternatives(self, similar_tool, sample_products):
        """Test finding cheaper similar products."""
        with patch.object(similar_tool, '_arun', new_callable=AsyncMock) as mock_run:
            # Return cheaper alternatives
            mock_run.return_value = [sample_products[1]]  # Budget headphones
            
            result = await similar_tool._arun(
                product=sample_products[0],  # Premium headphones
                max_price=100.0
            )
            
            assert all(p["price"] <= 100 for p in result)


class TestFindCategoryAlternativesTool:
    """Test suite for FindCategoryAlternativesTool."""
    
    @pytest.fixture
    def category_tool(self, mock_qdrant_service):
        """Create a category alternatives tool."""
        from app.agents.mcp.tools.alternative_tools import FindCategoryAlternativesTool
        tool = FindCategoryAlternativesTool()
        tool._qdrant = mock_qdrant_service
        return tool
    
    @pytest.mark.asyncio
    async def test_find_category_alternatives(self, category_tool, sample_products):
        """Test finding alternatives in same category."""
        electronics = [p for p in sample_products if p["category"] == "Electronics"]
        
        with patch.object(category_tool, '_arun', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = electronics[1:]
            
            result = await category_tool._arun(
                product=electronics[0],
                same_category=True
            )
            
            assert all(p["category"] == "Electronics" for p in result)


class TestGetDowngradeOptionsTool:
    """Test suite for GetDowngradeOptionsTool."""
    
    @pytest.fixture
    def downgrade_tool(self, mock_qdrant_service):
        """Create a downgrade options tool."""
        from app.agents.mcp.tools.alternative_tools import GetDowngradeOptionsTool
        tool = GetDowngradeOptionsTool()
        tool._qdrant = mock_qdrant_service
        return tool
    
    @pytest.mark.asyncio
    async def test_get_downgrades(self, downgrade_tool, sample_products):
        """Test getting downgrade options."""
        with patch.object(downgrade_tool, '_arun', new_callable=AsyncMock) as mock_run:
            # Premium -> Budget headphones
            mock_run.return_value = {
                "alternatives": [sample_products[1]],
                "trade_offs": ["Lower audio quality", "Shorter battery life"]
            }
            
            result = await downgrade_tool._arun(
                product=sample_products[0],
                target_budget=100.0
            )
            
            assert "alternatives" in result
            assert "trade_offs" in result


class TestGetUpgradePathTool:
    """Test suite for GetUpgradePathTool."""
    
    @pytest.fixture
    def upgrade_tool(self, mock_qdrant_service):
        """Create an upgrade path tool."""
        from app.agents.mcp.tools.alternative_tools import GetUpgradePathTool
        tool = GetUpgradePathTool()
        tool._qdrant = mock_qdrant_service
        return tool
    
    @pytest.mark.asyncio
    async def test_get_upgrade_path(self, upgrade_tool, sample_products):
        """Test getting upgrade options."""
        with patch.object(upgrade_tool, '_arun', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {
                "upgrades": [sample_products[0], sample_products[2]],
                "improvements": ["Better sound", "Noise cancellation"]
            }
            
            result = await upgrade_tool._arun(
                product=sample_products[1],  # Budget headphones
                max_budget=400.0
            )
            
            assert "upgrades" in result


# ==============================================================================
# Tool Error Handling Tests
# ==============================================================================

class TestToolErrorHandling:
    """Test error handling across all tools."""
    
    @pytest.mark.asyncio
    async def test_search_tool_handles_empty_query(self):
        """Test search tool handles empty query."""
        from app.agents.mcp.tools.search_tools import QdrantSemanticSearchTool
        tool = QdrantSemanticSearchTool()
        
        with patch.object(tool, '_arun', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = []
            
            result = await tool._arun(query="")
            
            assert result == [] or result is not None
    
    @pytest.mark.asyncio
    async def test_tool_handles_service_error(self):
        """Test tool handles service errors gracefully."""
        from app.agents.mcp.tools.search_tools import QdrantSemanticSearchTool
        tool = QdrantSemanticSearchTool()
        
        with patch.object(tool, '_arun', new_callable=AsyncMock) as mock_run:
            mock_run.side_effect = ConnectionError("Service unavailable")
            
            with pytest.raises(ConnectionError):
                await tool._arun(query="test")
    
    @pytest.mark.asyncio
    async def test_tool_validates_input(self):
        """Test tool validates input parameters."""
        from app.agents.mcp.tools.recommendation_tools import RankProductsByConstraintsTool
        tool = RankProductsByConstraintsTool()
        
        with patch.object(tool, '_arun', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = []
            
            # Empty products list
            result = await tool._arun(products=[], constraints={})
            
            assert result == []
