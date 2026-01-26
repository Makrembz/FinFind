"""
Tests for MCP Tools.

Run with: pytest backend/app/agents/mcp/tests/test_mcp_tools.py -v
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Protocol tests
from ..protocol import (
    MCPTool, MCPToolInput, MCPToolOutput, MCPToolMetadata,
    MCPError, MCPErrorCode, mcp_tool
)
from ..registry import MCPToolRegistry, MCPToolCache, get_tool_registry
from ..registration import (
    register_all_tools, get_tools_for_agent, get_tool_catalog
)

# Tool imports
from ..tools.search_tools import (
    QdrantSemanticSearchTool,
    ApplyFinancialFiltersTool,
    InterpretVagueQueryTool
)
from ..tools.recommendation_tools import (
    CalculateAffordabilityMatchTool,
    RankProductsByConstraintsTool
)
from ..tools.explainability_tools import (
    GetSimilarityExplanationTool,
    GetFinancialFitExplanationTool
)
from ..tools.alternative_tools import (
    FindSimilarInPriceRangeTool,
    GetDowngradeOptionsTool
)


# ========================================
# Protocol Tests
# ========================================

class TestMCPError:
    """Tests for MCPError."""
    
    def test_error_creation(self):
        """Test creating MCP error."""
        error = MCPError(
            code=MCPErrorCode.INVALID_INPUT,
            message="Test error"
        )
        assert error.code == MCPErrorCode.INVALID_INPUT
        assert error.message == "Test error"
        assert error.recoverable is True
    
    def test_error_to_dict(self):
        """Test error serialization."""
        error = MCPError(
            code=MCPErrorCode.VECTOR_SEARCH_FAILED,
            message="Search failed",
            details={"query": "test"}
        )
        result = error.to_dict()
        
        assert result["error"] is True
        assert result["code"] == "VECTOR_SEARCH_FAILED"
        assert result["message"] == "Search failed"
        assert result["details"]["query"] == "test"


class TestMCPToolOutput:
    """Tests for MCPToolOutput."""
    
    def test_success_response(self):
        """Test creating success response."""
        output = MCPToolOutput.success_response(
            data={"results": [1, 2, 3]},
            execution_time_ms=100
        )
        
        assert output.success is True
        assert output.data == {"results": [1, 2, 3]}
        assert output.execution_time_ms == 100
    
    def test_error_response(self):
        """Test creating error response."""
        error = MCPError(
            code=MCPErrorCode.INTERNAL_ERROR,
            message="Something failed"
        )
        output = MCPToolOutput.error_response(error)
        
        assert output.success is False
        assert output.error == error
    
    def test_to_dict(self):
        """Test output serialization."""
        output = MCPToolOutput.success_response(
            data={"test": "value"},
            cache_hit=True
        )
        result = output.to_dict()
        
        assert result["success"] is True
        assert result["data"]["test"] == "value"
        assert result["metadata"]["cache_hit"] is True


class TestMCPToolMetadata:
    """Tests for MCPToolMetadata."""
    
    def test_metadata_creation(self):
        """Test metadata creation with defaults."""
        metadata = MCPToolMetadata(
            name="test_tool",
            description="A test tool"
        )
        
        assert metadata.name == "test_tool"
        assert metadata.version == "1.0.0"
        assert metadata.cacheable is True
    
    def test_metadata_to_dict(self):
        """Test metadata serialization."""
        metadata = MCPToolMetadata(
            name="test_tool",
            description="Test",
            requires_qdrant=True,
            requires_embedding=True
        )
        result = metadata.to_dict()
        
        assert result["name"] == "test_tool"
        assert result["dependencies"]["requires_qdrant"] is True
        assert result["dependencies"]["requires_embedding"] is True


# ========================================
# Registry Tests
# ========================================

class TestMCPToolCache:
    """Tests for MCPToolCache."""
    
    def test_cache_set_get(self):
        """Test cache set and get."""
        cache = MCPToolCache()
        
        cache.set("tool1", {"param": "value"}, {"result": 123}, ttl_seconds=300)
        result = cache.get("tool1", {"param": "value"})
        
        assert result == {"result": 123}
    
    def test_cache_miss(self):
        """Test cache miss."""
        cache = MCPToolCache()
        result = cache.get("nonexistent", {})
        assert result is None
    
    def test_cache_stats(self):
        """Test cache statistics."""
        cache = MCPToolCache()
        
        cache.set("tool", {"p": 1}, {"r": 1}, 300)
        cache.get("tool", {"p": 1})  # Hit
        cache.get("tool", {"p": 2})  # Miss
        
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1


class TestMCPToolRegistry:
    """Tests for MCPToolRegistry."""
    
    def test_register_tool(self):
        """Test tool registration."""
        registry = MCPToolRegistry()
        
        tool = ApplyFinancialFiltersTool()
        registry.register(tool)
        
        assert tool.name in registry.list_tools()
    
    def test_get_tool(self):
        """Test getting registered tool."""
        registry = MCPToolRegistry()
        
        tool = ApplyFinancialFiltersTool()
        registry.register(tool)
        
        retrieved = registry.get(tool.name)
        assert retrieved is not None
        assert retrieved.name == tool.name
    
    def test_get_by_category(self):
        """Test getting tools by category."""
        registry = MCPToolRegistry()
        
        tool1 = ApplyFinancialFiltersTool()
        tool2 = InterpretVagueQueryTool()
        
        registry.register(tool1)
        registry.register(tool2)
        
        search_tools = registry.get_by_category("search")
        assert len(search_tools) == 2
    
    def test_unregister_tool(self):
        """Test tool unregistration."""
        registry = MCPToolRegistry()
        
        tool = ApplyFinancialFiltersTool()
        registry.register(tool)
        registry.unregister(tool.name)
        
        assert tool.name not in registry.list_tools()


# ========================================
# Registration Tests
# ========================================

class TestToolRegistration:
    """Tests for tool registration functions."""
    
    def test_get_tools_for_agent(self):
        """Test getting tools for specific agent."""
        search_tools = get_tools_for_agent("search")
        assert len(search_tools) == 5
        
        rec_tools = get_tools_for_agent("recommendation")
        assert len(rec_tools) == 5
        
        exp_tools = get_tools_for_agent("explainability")
        assert len(exp_tools) == 4
        
        alt_tools = get_tools_for_agent("alternative")
        assert len(alt_tools) == 4
    
    def test_get_tool_catalog(self):
        """Test getting tool catalog."""
        catalog = get_tool_catalog()
        
        assert "search" in catalog
        assert "recommendation" in catalog
        assert "summary" in catalog
        assert catalog["summary"]["total_tools"] == 18


# ========================================
# Search Tool Tests
# ========================================

class TestApplyFinancialFiltersTool:
    """Tests for ApplyFinancialFiltersTool."""
    
    def test_filter_by_budget(self):
        """Test filtering products by budget."""
        tool = ApplyFinancialFiltersTool()
        
        products = [
            {"id": "1", "name": "Product A", "price": 100},
            {"id": "2", "name": "Product B", "price": 200},
            {"id": "3", "name": "Product C", "price": 300}
        ]
        
        result = tool._execute(
            products=products,
            budget_max=250
        )
        
        assert result.success is True
        filtered = result.data["products"]
        assert len(filtered) == 2
        assert all(p["price"] <= 250 for p in filtered)
    
    def test_empty_products(self):
        """Test with empty product list."""
        tool = ApplyFinancialFiltersTool()
        
        result = tool._execute(products=[], budget_max=100)
        
        assert result.success is True
        assert result.data["filtered_count"] == 0


class TestInterpretVagueQueryTool:
    """Tests for InterpretVagueQueryTool."""
    
    def test_detect_budget_intent(self):
        """Test detecting budget intent."""
        tool = InterpretVagueQueryTool()
        
        result = tool._execute(query="cheap laptop under $500")
        
        assert result.success is True
        data = result.data
        assert "budget" in data["interpreted"]["intents"]
        assert data["interpreted"]["budget"] == 500
    
    def test_detect_category(self):
        """Test detecting category from query."""
        tool = InterpretVagueQueryTool()
        
        result = tool._execute(query="looking for a new smartphone")
        
        assert result.success is True
        assert "electronics" in result.data["interpreted"]["categories"]
    
    def test_extract_price(self):
        """Test price extraction patterns."""
        tool = InterpretVagueQueryTool()
        
        queries_and_prices = [
            ("under $1000", 1000),
            ("less than $500", 500),
            ("budget of 300", 300)
        ]
        
        for query, expected in queries_and_prices:
            result = tool._execute(query=query)
            assert result.data["interpreted"]["budget"] == expected


# ========================================
# Recommendation Tool Tests
# ========================================

class TestCalculateAffordabilityMatchTool:
    """Tests for CalculateAffordabilityMatchTool."""
    
    def test_calculate_affordability(self):
        """Test affordability calculation."""
        tool = CalculateAffordabilityMatchTool()
        
        products = [
            {"id": "1", "price": 100},
            {"id": "2", "price": 500},
            {"id": "3", "price": 1000}
        ]
        
        user_profile = {
            "financial": {
                "budget_max": 600,
                "risk_tolerance": "medium"
            }
        }
        
        result = tool._execute(products=products, user_profile=user_profile)
        
        assert result.success is True
        scored = result.data["scored_products"]
        
        # Product 1 should have highest score (well under budget)
        assert scored[0]["id"] == "1"
        assert scored[0]["fit_level"] in ["excellent", "good"]
        
        # Product 3 should have lowest score (over budget)
        assert scored[-1]["id"] == "3"


class TestRankProductsByConstraintsTool:
    """Tests for RankProductsByConstraintsTool."""
    
    def test_ranking(self):
        """Test multi-factor ranking."""
        tool = RankProductsByConstraintsTool()
        
        products = [
            {"id": "1", "score": 0.9, "affordability_score": 0.5, "rating": 4.0},
            {"id": "2", "score": 0.7, "affordability_score": 0.9, "rating": 4.5},
            {"id": "3", "score": 0.8, "affordability_score": 0.7, "rating": 3.5}
        ]
        
        result = tool._execute(products=products)
        
        assert result.success is True
        ranked = result.data["ranked_products"]
        assert len(ranked) == 3
        assert all("ranking_score" in p for p in ranked)
    
    def test_custom_weights(self):
        """Test with custom weights."""
        tool = RankProductsByConstraintsTool()
        
        products = [{"id": "1", "score": 0.5, "affordability_score": 0.9}]
        
        result = tool._execute(
            products=products,
            weights={"relevance": 0.1, "affordability": 0.9}
        )
        
        assert result.success is True
        assert result.data["weights_used"]["affordability"] > 0.5


# ========================================
# Explainability Tool Tests
# ========================================

class TestGetFinancialFitExplanationTool:
    """Tests for GetFinancialFitExplanationTool."""
    
    def test_explain_within_budget(self):
        """Test explanation for product within budget."""
        tool = GetFinancialFitExplanationTool()
        
        product = {"id": "1", "price": 200, "rating": 4.5}
        user_profile = {
            "financial": {
                "budget_max": 500,
                "monthly_budget": 1000,
                "risk_tolerance": "medium"
            }
        }
        
        result = tool._execute(product=product, user_profile=user_profile)
        
        assert result.success is True
        assert result.data["fit_level"] in ["excellent", "good"]
        assert result.data["analysis"]["budget_analysis"]["within_budget"] is True
    
    def test_explain_over_budget(self):
        """Test explanation for product over budget."""
        tool = GetFinancialFitExplanationTool()
        
        product = {"id": "1", "price": 800}
        user_profile = {
            "financial": {"budget_max": 500}
        }
        
        result = tool._execute(product=product, user_profile=user_profile)
        
        assert result.success is True
        assert result.data["fit_level"] in ["stretch", "poor"]


# ========================================
# Alternative Tool Tests
# ========================================

class TestGetDowngradeOptionsTool:
    """Tests for GetDowngradeOptionsTool."""
    
    def test_max_price_higher_than_original(self):
        """Test when max_price exceeds original price."""
        tool = GetDowngradeOptionsTool()
        
        product = {"id": "1", "price": 500}
        
        result = tool._execute(product=product, max_price=600)
        
        assert result.success is True
        assert "consider find_similar_in_price_range" in result.data["message"]


# ========================================
# Integration Tests (Mocked)
# ========================================

class TestMockedQdrantIntegration:
    """Integration tests with mocked Qdrant."""
    
    @patch('app.agents.services.qdrant_service.QdrantService.semantic_search')
    @patch('app.agents.services.embedding_service.EmbeddingService.embed')
    def test_semantic_search_tool(self, mock_embed, mock_search):
        """Test semantic search with mocked services."""
        mock_embed.return_value = [0.1] * 384
        mock_search.return_value = [
            {"id": "1", "score": 0.9, "payload": {"name": "Test Product", "price": 100}}
        ]
        
        tool = QdrantSemanticSearchTool()
        
        # This would use the mocked services
        # In a real test, you'd verify the tool calls the services correctly


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_empty_products_list(self):
        """Test tools with empty product lists."""
        tool = CalculateAffordabilityMatchTool()
        
        result = tool._execute(
            products=[],
            user_profile={"financial": {"budget_max": 100}}
        )
        
        assert result.success is True
        assert result.data["scored_products"] == []
    
    def test_missing_price(self):
        """Test with products missing price."""
        tool = ApplyFinancialFiltersTool()
        
        products = [{"id": "1", "name": "No Price Product"}]
        result = tool._execute(products=products, budget_max=100)
        
        assert result.success is True
    
    def test_very_long_query(self):
        """Test with very long query string."""
        tool = InterpretVagueQueryTool()
        
        long_query = "find " + "laptop " * 1000
        result = tool._execute(query=long_query)
        
        assert result.success is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
