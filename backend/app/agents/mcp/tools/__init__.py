# MCP Tools Module
"""
MCP-compliant tools for FinFind agents.

Each tool follows the Model Context Protocol standards for:
- Structured input/output
- Error handling
- Logging and metrics
- Caching support
"""

from .search_tools import (
    QdrantSemanticSearchTool,
    ApplyFinancialFiltersTool,
    InterpretVagueQueryTool,
    ImageSimilaritySearchTool,
    VoiceToTextSearchTool
)
from .recommendation_tools import (
    GetUserFinancialProfileTool,
    GetUserInteractionHistoryTool,
    CalculateAffordabilityMatchTool,
    RankProductsByConstraintsTool,
    GetContextualRecommendationsTool
)
from .explainability_tools import (
    GetSimilarityExplanationTool,
    GetFinancialFitExplanationTool,
    GetAttributeMatchesTool,
    GenerateNaturalExplanationTool
)
from .alternative_tools import (
    FindSimilarInPriceRangeTool,
    FindCategoryAlternativesTool,
    GetDowngradeOptionsTool,
    GetUpgradePathTool
)

__all__ = [
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
