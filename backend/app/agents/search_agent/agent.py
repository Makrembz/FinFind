"""
SearchAgent Implementation for FinFind.

Handles user search queries with semantic search, query interpretation,
and financial constraint filtering.
"""

import logging
from typing import Dict, Any, List, Optional

from langchain_core.tools import BaseTool

from ..base import BaseAgent, AgentState, ConversationContext
from ..config import AgentConfig, AgentType, get_config
from ..tools import (
    QdrantSearchTool,
    InterpretQueryTool,
    ApplyBudgetFilterTool,
    ImageSearchTool
)
from .prompts import SEARCH_AGENT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class SearchAgent(BaseAgent):
    """
    SearchAgent for FinFind.
    
    Specializes in:
    - Interpreting user search queries
    - Semantic product search with MMR
    - Budget-aware filtering
    - Query expansion and refinement
    """
    
    agent_type = AgentType.SEARCH
    agent_name = "SearchAgent"
    agent_description = "Handles user search queries with semantic search and financial filtering"
    
    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        tools: Optional[List[BaseTool]] = None
    ):
        """Initialize the SearchAgent."""
        super().__init__(config, tools)
        self._search_config = self.config.search
    
    def _create_default_tools(self) -> List[BaseTool]:
        """Create the default tools for SearchAgent."""
        return [
            QdrantSearchTool(),
            InterpretQueryTool(),
            ApplyBudgetFilterTool(),
            ImageSearchTool()
        ]
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for SearchAgent."""
        return SEARCH_AGENT_SYSTEM_PROMPT
    
    async def search(
        self,
        query: str,
        state: Optional[AgentState] = None,
        context: Optional[ConversationContext] = None,
        **kwargs
    ) -> AgentState:
        """
        Perform a search operation.
        
        This is the main entry point for search requests.
        Handles the complete search flow including interpretation
        and filtering.
        
        Args:
            query: The user's search query.
            state: Optional existing agent state.
            context: Optional conversation context.
            **kwargs: Additional search parameters.
            
        Returns:
            AgentState with search results.
        """
        # Build comprehensive input
        search_input = f"Search for: {query}"
        
        # Add context if available
        if context and context.user:
            if context.user.financial.budget_max:
                search_input += f"\nUser budget: up to ${context.user.financial.budget_max}"
            if context.user.preferred_categories:
                search_input += f"\nPreferred categories: {', '.join(context.user.preferred_categories)}"
        
        # Add any additional parameters
        if kwargs.get('category'):
            search_input += f"\nCategory filter: {kwargs['category']}"
        if kwargs.get('max_price'):
            search_input += f"\nMax price: ${kwargs['max_price']}"
        
        # Run the agent
        state = await self.run(search_input, state, context)
        
        # Update search context
        if context and state.output_products:
            from ..base.context import get_context_manager
            cm = get_context_manager()
            cm.set_search_context(
                context.conversation_id,
                query=query,
                results_count=len(state.output_products)
            )
        
        return state
    
    def search_sync(
        self,
        query: str,
        state: Optional[AgentState] = None,
        context: Optional[ConversationContext] = None,
        **kwargs
    ) -> AgentState:
        """Synchronous version of search()."""
        search_input = f"Search for: {query}"
        
        if context and context.user:
            if context.user.financial.budget_max:
                search_input += f"\nUser budget: up to ${context.user.financial.budget_max}"
        
        if kwargs.get('category'):
            search_input += f"\nCategory filter: {kwargs['category']}"
        if kwargs.get('max_price'):
            search_input += f"\nMax price: ${kwargs['max_price']}"
        
        return self.run_sync(search_input, state, context)
    
    async def interpret_and_search(
        self,
        query: str,
        user_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Interpret a query and perform search in one step.
        
        Convenience method that combines query interpretation
        with search execution.
        
        Args:
            query: The user's raw query.
            user_context: Optional user context dictionary.
            
        Returns:
            Dictionary with interpretation and search results.
        """
        # Get tools
        interpret_tool = InterpretQueryTool()
        search_tool = QdrantSearchTool()
        budget_tool = ApplyBudgetFilterTool()
        
        # Interpret query
        interpretation = interpret_tool._run(
            query=query,
            user_context=user_context
        )
        
        interpreted = interpretation.get('interpreted', {})
        
        # Perform search
        search_results = search_tool._run(
            query=interpreted.get('expanded_query', query),
            collection="products",
            limit=self._search_config.max_limit,
            category_filter=interpreted.get('category'),
            min_price=interpreted.get('min_price'),
            max_price=interpreted.get('max_price'),
            use_mmr=self._search_config.search_strategy.value == 'mmr'
        )
        
        # Apply budget filter if user has budget
        products = search_results.get('results', [])
        if user_context and user_context.get('budget_max') and products:
            filtered = budget_tool._run(
                products=products,
                budget_max=user_context.get('budget_max'),
                budget_min=user_context.get('budget_min'),
                tolerance=self._search_config.budget_tolerance
            )
            products = filtered.get('products', products)
        
        return {
            "query": query,
            "interpretation": interpretation,
            "results": products,
            "count": len(products)
        }
    
    def quick_search(
        self,
        query: str,
        limit: int = 10,
        category: Optional[str] = None,
        max_price: Optional[float] = None
    ) -> List[Dict]:
        """
        Perform a quick search without full agent execution.
        
        Bypasses the LLM and directly calls tools for faster results.
        
        Args:
            query: Search query.
            limit: Maximum results.
            category: Optional category filter.
            max_price: Optional price limit.
            
        Returns:
            List of product dictionaries.
        """
        search_tool = QdrantSearchTool()
        
        result = search_tool._run(
            query=query,
            collection="products",
            limit=limit,
            category_filter=category,
            max_price=max_price,
            use_mmr=True
        )
        
        return result.get('results', [])
