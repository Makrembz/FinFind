# FinFind Agent System
"""
LangChain-based multi-agent system for FinFind.

This module provides 4 specialized agents:
- SearchAgent: Handles user search queries with semantic search
- RecommendationAgent: Generates personalized product recommendations
- ExplainabilityAgent: Explains why products are recommended
- AlternativeAgent: Finds substitute products when constraints fail

Agents communicate via A2A protocol and use MCP for tool integration.

Usage:
    from app.agents import get_orchestrator
    
    orchestrator = get_orchestrator()
    result = await orchestrator.process_request(
        "Find me a laptop under $1000",
        user_id="user123"
    )
    
    # MCP Tools
    from app.agents.mcp import get_tools_for_agent, register_all_tools
    
    search_tools = get_tools_for_agent("search")
"""

from .config import (
    AgentConfig,
    get_config,
    AgentType,
    LLMConfig,
    QdrantConfig,
    EmbeddingConfig
)
from .base import (
    BaseAgent,
    AgentState,
    ConversationContext,
    ContextManager,
    get_context_manager,
    UserContext,
    FinancialContext
)
from .orchestrator import (
    AgentOrchestrator,
    A2AProtocol,
    A2AMessage,
    A2AMessageType,
    get_orchestrator
)
from .search_agent import SearchAgent
from .recommendation_agent import RecommendationAgent
from .explainability_agent import ExplainabilityAgent
from .alternative_agent import AlternativeAgent

# MCP imports
from .mcp import (
    MCPTool,
    MCPToolOutput,
    MCPError,
    MCPErrorCode,
    get_tool_registry,
    register_all_tools,
    get_tools_for_agent,
    get_tool_catalog
)

# Services
from .services import (
    QdrantService,
    get_qdrant_service,
    EmbeddingService,
    get_embedding_service,
    CacheService,
    get_cache_service
)

__all__ = [
    # Config
    "AgentConfig",
    "get_config",
    "AgentType",
    "LLMConfig",
    "QdrantConfig",
    "EmbeddingConfig",
    # Base
    "BaseAgent",
    "AgentState",
    "ConversationContext",
    "ContextManager",
    "get_context_manager",
    "UserContext",
    "FinancialContext",
    # Orchestrator
    "AgentOrchestrator",
    "A2AProtocol",
    "A2AMessage",
    "A2AMessageType",
    "get_orchestrator",
    # Agents
    "SearchAgent",
    "RecommendationAgent", 
    "ExplainabilityAgent",
    "AlternativeAgent",
    # MCP
    "MCPTool",
    "MCPToolOutput",
    "MCPError",
    "MCPErrorCode",
    "get_tool_registry",
    "register_all_tools",
    "get_tools_for_agent",
    "get_tool_catalog",
    # Services
    "QdrantService",
    "get_qdrant_service",
    "EmbeddingService",
    "get_embedding_service",
    "CacheService",
    "get_cache_service",
]
