"""
MCP Tool Registration for FinFind.

Registers all MCP tools with the global registry.
Provides tool discovery and access for agents.
"""

import logging
from typing import List, Dict, Any

from .protocol import MCPTool
from .registry import MCPToolRegistry, get_tool_registry

# Import all tools
from .tools.search_tools import (
    QdrantSemanticSearchTool,
    ApplyFinancialFiltersTool,
    InterpretVagueQueryTool,
    ImageSimilaritySearchTool,
    VoiceToTextSearchTool
)
from .tools.recommendation_tools import (
    GetUserFinancialProfileTool,
    GetUserInteractionHistoryTool,
    CalculateAffordabilityMatchTool,
    RankProductsByConstraintsTool,
    GetContextualRecommendationsTool
)
from .tools.explainability_tools import (
    GetSimilarityExplanationTool,
    GetFinancialFitExplanationTool,
    GetAttributeMatchesTool,
    GenerateNaturalExplanationTool
)
from .tools.alternative_tools import (
    FindSimilarInPriceRangeTool,
    FindCategoryAlternativesTool,
    GetDowngradeOptionsTool,
    GetUpgradePathTool
)

logger = logging.getLogger(__name__)


# ========================================
# Tool Categories
# ========================================

SEARCH_TOOLS = [
    QdrantSemanticSearchTool,
    ApplyFinancialFiltersTool,
    InterpretVagueQueryTool,
    ImageSimilaritySearchTool,
    VoiceToTextSearchTool
]

RECOMMENDATION_TOOLS = [
    GetUserFinancialProfileTool,
    GetUserInteractionHistoryTool,
    CalculateAffordabilityMatchTool,
    RankProductsByConstraintsTool,
    GetContextualRecommendationsTool
]

EXPLAINABILITY_TOOLS = [
    GetSimilarityExplanationTool,
    GetFinancialFitExplanationTool,
    GetAttributeMatchesTool,
    GenerateNaturalExplanationTool
]

ALTERNATIVE_TOOLS = [
    FindSimilarInPriceRangeTool,
    FindCategoryAlternativesTool,
    GetDowngradeOptionsTool,
    GetUpgradePathTool
]

ALL_TOOLS = (
    SEARCH_TOOLS +
    RECOMMENDATION_TOOLS +
    EXPLAINABILITY_TOOLS +
    ALTERNATIVE_TOOLS
)


# ========================================
# Registration Functions
# ========================================

def register_all_tools(registry: MCPToolRegistry = None) -> MCPToolRegistry:
    """
    Register all MCP tools with the registry.
    
    Args:
        registry: Optional registry to use. Creates new if not provided.
        
    Returns:
        The registry with all tools registered.
    """
    if registry is None:
        registry = get_tool_registry()
    
    registered = []
    failed = []
    
    for tool_class in ALL_TOOLS:
        try:
            tool = tool_class()
            registry.register(tool)
            registered.append(tool.name)
        except Exception as e:
            logger.error(f"Failed to register {tool_class.__name__}: {e}")
            failed.append(tool_class.__name__)
    
    logger.info(f"Registered {len(registered)} MCP tools")
    if failed:
        logger.warning(f"Failed to register: {failed}")
    
    return registry


def register_search_tools(registry: MCPToolRegistry = None) -> List[MCPTool]:
    """Register only search tools."""
    if registry is None:
        registry = get_tool_registry()
    
    tools = []
    for tool_class in SEARCH_TOOLS:
        tool = tool_class()
        registry.register(tool)
        tools.append(tool)
    
    return tools


def register_recommendation_tools(registry: MCPToolRegistry = None) -> List[MCPTool]:
    """Register only recommendation tools."""
    if registry is None:
        registry = get_tool_registry()
    
    tools = []
    for tool_class in RECOMMENDATION_TOOLS:
        tool = tool_class()
        registry.register(tool)
        tools.append(tool)
    
    return tools


def register_explainability_tools(registry: MCPToolRegistry = None) -> List[MCPTool]:
    """Register only explainability tools."""
    if registry is None:
        registry = get_tool_registry()
    
    tools = []
    for tool_class in EXPLAINABILITY_TOOLS:
        tool = tool_class()
        registry.register(tool)
        tools.append(tool)
    
    return tools


def register_alternative_tools(registry: MCPToolRegistry = None) -> List[MCPTool]:
    """Register only alternative tools."""
    if registry is None:
        registry = get_tool_registry()
    
    tools = []
    for tool_class in ALTERNATIVE_TOOLS:
        tool = tool_class()
        registry.register(tool)
        tools.append(tool)
    
    return tools


# ========================================
# Tool Access Functions
# ========================================

def get_tools_for_agent(agent_type: str) -> List[MCPTool]:
    """
    Get the appropriate tools for an agent type.
    
    Args:
        agent_type: One of 'search', 'recommendation', 'explainability', 'alternative'
        
    Returns:
        List of tool instances for that agent.
    """
    tool_map = {
        "search": SEARCH_TOOLS,
        "recommendation": RECOMMENDATION_TOOLS,
        "explainability": EXPLAINABILITY_TOOLS,
        "alternative": ALTERNATIVE_TOOLS
    }
    
    tool_classes = tool_map.get(agent_type.lower(), [])
    return [tool_class() for tool_class in tool_classes]


def get_all_tool_instances() -> List[MCPTool]:
    """Get instances of all tools."""
    return [tool_class() for tool_class in ALL_TOOLS]


def get_tool_catalog() -> Dict[str, Any]:
    """
    Get a catalog of all available tools.
    
    Returns:
        Dictionary with tool information organized by category.
    """
    catalog = {
        "search": [],
        "recommendation": [],
        "explainability": [],
        "alternative": []
    }
    
    for tool_class in SEARCH_TOOLS:
        tool = tool_class()
        catalog["search"].append({
            "name": tool.name,
            "description": tool.description.strip(),
            "metadata": tool.metadata.to_dict()
        })
    
    for tool_class in RECOMMENDATION_TOOLS:
        tool = tool_class()
        catalog["recommendation"].append({
            "name": tool.name,
            "description": tool.description.strip(),
            "metadata": tool.metadata.to_dict()
        })
    
    for tool_class in EXPLAINABILITY_TOOLS:
        tool = tool_class()
        catalog["explainability"].append({
            "name": tool.name,
            "description": tool.description.strip(),
            "metadata": tool.metadata.to_dict()
        })
    
    for tool_class in ALTERNATIVE_TOOLS:
        tool = tool_class()
        catalog["alternative"].append({
            "name": tool.name,
            "description": tool.description.strip(),
            "metadata": tool.metadata.to_dict()
        })
    
    catalog["summary"] = {
        "total_tools": len(ALL_TOOLS),
        "by_category": {
            "search": len(SEARCH_TOOLS),
            "recommendation": len(RECOMMENDATION_TOOLS),
            "explainability": len(EXPLAINABILITY_TOOLS),
            "alternative": len(ALTERNATIVE_TOOLS)
        }
    }
    
    return catalog


# ========================================
# Auto-registration on import
# ========================================

_registered = False


def ensure_tools_registered():
    """Ensure all tools are registered (call once at startup)."""
    global _registered
    if not _registered:
        register_all_tools()
        _registered = True
