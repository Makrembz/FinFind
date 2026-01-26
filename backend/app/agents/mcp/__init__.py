# MCP Module
"""
Model Context Protocol (MCP) implementation for FinFind.

Provides standardized tool interfaces for LangChain agent integration.

Usage:
    from app.agents.mcp import get_tool_registry, register_all_tools
    
    # Register all tools
    registry = register_all_tools()
    
    # Execute a tool
    result = registry.execute("qdrant_semantic_search", {
        "query": "laptop under $1000",
        "limit": 10
    })
    
    # Get tools for a specific agent
    from app.agents.mcp import get_tools_for_agent
    search_tools = get_tools_for_agent("search")
"""

from .protocol import (
    MCPTool,
    MCPToolInput,
    MCPToolOutput,
    MCPToolMetadata,
    MCPError,
    MCPErrorCode,
    mcp_tool
)
from .registry import (
    MCPToolRegistry,
    MCPToolCache,
    get_tool_registry,
    register_tool,
    execute_tool
)
from .registration import (
    register_all_tools,
    register_search_tools,
    register_recommendation_tools,
    register_explainability_tools,
    register_alternative_tools,
    get_tools_for_agent,
    get_all_tool_instances,
    get_tool_catalog,
    ensure_tools_registered,
    SEARCH_TOOLS,
    RECOMMENDATION_TOOLS,
    EXPLAINABILITY_TOOLS,
    ALTERNATIVE_TOOLS,
    ALL_TOOLS
)

# Import tool classes for direct access
from .tools import (
    # Search Tools
    QdrantSemanticSearchTool,
    ApplyFinancialFiltersTool,
    InterpretVagueQueryTool,
    ImageSimilaritySearchTool,
    VoiceToTextSearchTool,
    # Recommendation Tools
    GetUserFinancialProfileTool,
    GetUserInteractionHistoryTool,
    CalculateAffordabilityMatchTool,
    RankProductsByConstraintsTool,
    GetContextualRecommendationsTool,
    # Explainability Tools
    GetSimilarityExplanationTool,
    GetFinancialFitExplanationTool,
    GetAttributeMatchesTool,
    GenerateNaturalExplanationTool,
    # Alternative Tools
    FindSimilarInPriceRangeTool,
    FindCategoryAlternativesTool,
    GetDowngradeOptionsTool,
    GetUpgradePathTool
)

__all__ = [
    # Protocol
    "MCPTool",
    "MCPToolInput",
    "MCPToolOutput",
    "MCPToolMetadata",
    "MCPError",
    "MCPErrorCode",
    "mcp_tool",
    # Registry
    "MCPToolRegistry",
    "MCPToolCache",
    "get_tool_registry",
    "register_tool",
    "execute_tool",
    # Registration
    "register_all_tools",
    "register_search_tools",
    "register_recommendation_tools",
    "register_explainability_tools",
    "register_alternative_tools",
    "get_tools_for_agent",
    "get_all_tool_instances",
    "get_tool_catalog",
    "ensure_tools_registered",
    "SEARCH_TOOLS",
    "RECOMMENDATION_TOOLS",
    "EXPLAINABILITY_TOOLS",
    "ALTERNATIVE_TOOLS",
    "ALL_TOOLS",
    # Search Tools
    "QdrantSemanticSearchTool",
    "ApplyFinancialFiltersTool",
    "InterpretVagueQueryTool",
    "ImageSimilaritySearchTool",
    "VoiceToTextSearchTool",
    # Recommendation Tools
    "GetUserFinancialProfileTool",
    "GetUserInteractionHistoryTool",
    "CalculateAffordabilityMatchTool",
    "RankProductsByConstraintsTool",
    "GetContextualRecommendationsTool",
    # Explainability Tools
    "GetSimilarityExplanationTool",
    "GetFinancialFitExplanationTool",
    "GetAttributeMatchesTool",
    "GenerateNaturalExplanationTool",
    # Alternative Tools
    "FindSimilarInPriceRangeTool",
    "FindCategoryAlternativesTool",
    "GetDowngradeOptionsTool",
    "GetUpgradePathTool",
]
