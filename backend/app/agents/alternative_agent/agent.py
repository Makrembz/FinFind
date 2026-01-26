"""
AlternativeAgent Implementation for FinFind.

Finds substitute products when budget or other constraints
aren't met with the original selection.
"""

import logging
from typing import Dict, Any, List, Optional

from langchain_core.tools import BaseTool

from ..base import BaseAgent, AgentState, ConversationContext
from ..config import AgentConfig, AgentType, get_config
from ..tools import (
    FindSimilarProductsTool,
    AdjustPriceRangeTool,
    SuggestAlternativesTool
)
from .prompts import ALTERNATIVE_AGENT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class AlternativeAgent(BaseAgent):
    """
    AlternativeAgent for FinFind.
    
    Specializes in:
    - Finding budget-friendly alternatives
    - Suggesting downgrades and substitutes
    - Explaining trade-offs
    - Handling out-of-stock scenarios
    """
    
    agent_type = AgentType.ALTERNATIVE
    agent_name = "AlternativeAgent"
    agent_description = "Finds substitute products when constraints aren't met"
    
    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        tools: Optional[List[BaseTool]] = None
    ):
        """Initialize the AlternativeAgent."""
        super().__init__(config, tools)
        self._alt_config = self.config.alternative
    
    def _create_default_tools(self) -> List[BaseTool]:
        """Create the default tools for AlternativeAgent."""
        return [
            FindSimilarProductsTool(),
            AdjustPriceRangeTool(),
            SuggestAlternativesTool()
        ]
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for AlternativeAgent."""
        return ALTERNATIVE_AGENT_SYSTEM_PROMPT
    
    async def find_alternatives(
        self,
        product: Dict,
        state: Optional[AgentState] = None,
        context: Optional[ConversationContext] = None,
        reason: str = "over_budget",
        num_alternatives: int = 3
    ) -> AgentState:
        """
        Find alternatives for a product.
        
        Args:
            product: Original product that doesn't meet constraints.
            state: Optional existing agent state.
            context: Optional conversation context.
            reason: Reason for seeking alternatives.
            num_alternatives: Number of alternatives to find.
            
        Returns:
            AgentState with alternatives.
        """
        # Build comprehensive input
        alt_input = f"Find {num_alternatives} alternatives for this product:\n"
        alt_input += f"Product: {product.get('title', 'Unknown')}\n"
        alt_input += f"Price: ${product.get('price', 'N/A')}\n"
        alt_input += f"Category: {product.get('category', 'N/A')}\n"
        alt_input += f"\nReason for alternatives: {reason}\n"
        
        if context and context.user:
            if context.user.financial.budget_max:
                alt_input += f"User's budget: ${context.user.financial.budget_max}\n"
        
        alt_input += "\nFind good alternatives and explain trade-offs."
        
        # Run the agent
        state = await self.run(alt_input, state, context)
        
        return state
    
    def find_alternatives_sync(
        self,
        product: Dict,
        state: Optional[AgentState] = None,
        context: Optional[ConversationContext] = None,
        reason: str = "over_budget",
        num_alternatives: int = 3
    ) -> AgentState:
        """Synchronous version of find_alternatives()."""
        alt_input = f"Find {num_alternatives} alternatives for: {product.get('title', 'Unknown')}\n"
        alt_input += f"Price: ${product.get('price', 'N/A')}\n"
        alt_input += f"Reason: {reason}"
        
        if context and context.user:
            if context.user.financial.budget_max:
                alt_input += f"\nUser budget: ${context.user.financial.budget_max}"
        
        return self.run_sync(alt_input, state, context)
    
    def get_budget_alternatives(
        self,
        product: Dict,
        user_budget: float,
        num_alternatives: int = 3
    ) -> Dict[str, Any]:
        """
        Get alternatives within a budget without full agent execution.
        
        Directly calls tools for faster results.
        
        Args:
            product: Original product.
            user_budget: User's maximum budget.
            num_alternatives: Number of alternatives.
            
        Returns:
            Dictionary with alternatives and analysis.
        """
        # Get tools
        similar_tool = FindSimilarProductsTool()
        price_tool = AdjustPriceRangeTool()
        suggest_tool = SuggestAlternativesTool()
        
        product_id = product.get('id') or product.get('original_id')
        original_price = product.get('price', 0)
        
        # Calculate price adjustment needed
        price_analysis = price_tool._run(
            original_price=original_price,
            user_budget=user_budget,
            adjustment_step=self._alt_config.price_range_step,
            max_steps=self._alt_config.max_price_adjustments
        )
        
        # Find similar products within budget
        similar_result = similar_tool._run(
            product_id=product_id,
            max_price=user_budget,
            same_category=True,
            limit=num_alternatives,
            exclude_ids=[product_id]
        )
        
        alternatives = similar_result.get('alternatives', [])
        
        # If not enough alternatives in same category, try broader search
        if len(alternatives) < num_alternatives:
            broader_result = similar_tool._run(
                product_id=product_id,
                max_price=user_budget,
                same_category=False,
                limit=num_alternatives - len(alternatives),
                exclude_ids=[product_id] + [a['product_id'] for a in alternatives]
            )
            alternatives.extend(broader_result.get('alternatives', []))
        
        # Prepare result
        result = {
            "success": True,
            "original_product": {
                "id": product_id,
                "title": product.get('title'),
                "price": original_price,
                "category": product.get('category')
            },
            "user_budget": user_budget,
            "price_analysis": {
                "overage": price_analysis.get('overage'),
                "overage_percent": price_analysis.get('overage_percent'),
                "min_discount_needed": price_analysis.get('min_discount_needed')
            },
            "alternatives": alternatives,
            "alternatives_count": len(alternatives)
        }
        
        # Add message if no alternatives found
        if not alternatives:
            result["message"] = "No alternatives found within budget in the same category. Consider broadening your search or adjusting your budget."
        
        return result
    
    def suggest_downgrades(
        self,
        product: Dict,
        price_reduction_percent: float = 20,
        num_suggestions: int = 3
    ) -> Dict[str, Any]:
        """
        Suggest product downgrades at a lower price point.
        
        Args:
            product: Original product.
            price_reduction_percent: Target price reduction.
            num_suggestions: Number of suggestions.
            
        Returns:
            Dictionary with downgrade suggestions.
        """
        similar_tool = FindSimilarProductsTool()
        
        product_id = product.get('id') or product.get('original_id')
        original_price = product.get('price', 0)
        target_max_price = original_price * (1 - price_reduction_percent / 100)
        
        result = similar_tool._run(
            product_id=product_id,
            max_price=target_max_price,
            same_category=True,
            limit=num_suggestions
        )
        
        downgrades = result.get('alternatives', [])
        
        # Annotate with savings info
        for d in downgrades:
            d['savings'] = round(original_price - d.get('price', 0), 2)
            d['savings_percent'] = round(d['savings'] / original_price * 100, 1) if original_price > 0 else 0
        
        return {
            "success": True,
            "original": {
                "id": product_id,
                "title": product.get('title'),
                "price": original_price
            },
            "target_price_reduction": f"{price_reduction_percent}%",
            "target_max_price": round(target_max_price, 2),
            "downgrades": downgrades
        }
    
    def get_alternatives_with_explanation(
        self,
        product: Dict,
        user_profile: Optional[Dict] = None,
        reason: str = "over_budget",
        num_alternatives: int = 3
    ) -> Dict[str, Any]:
        """
        Get alternatives with detailed explanations.
        
        Args:
            product: Original product.
            user_profile: Optional user profile.
            reason: Reason for seeking alternatives.
            num_alternatives: Number of alternatives.
            
        Returns:
            Dictionary with alternatives and explanations.
        """
        suggest_tool = SuggestAlternativesTool()
        
        result = suggest_tool._run(
            original_product=product,
            user_profile=user_profile,
            reason=reason,
            num_suggestions=num_alternatives
        )
        
        return result
    
    async def handle_constraint_failure(
        self,
        constraint_type: str,
        constraint_value: Any,
        original_results: List[Dict],
        state: Optional[AgentState] = None,
        context: Optional[ConversationContext] = None
    ) -> AgentState:
        """
        Handle cases where original search/recommendation didn't meet constraints.
        
        Args:
            constraint_type: Type of constraint that failed (budget, rating, etc.)
            constraint_value: The constraint value that couldn't be met.
            original_results: Results that didn't meet constraints.
            state: Optional existing agent state.
            context: Optional conversation context.
            
        Returns:
            AgentState with alternative solutions.
        """
        # Build input based on constraint type
        if constraint_type == "budget":
            alt_input = f"""The search results exceed the user's budget of ${constraint_value}.
Found {len(original_results)} products but all are over budget.

Help find alternatives by:
1. Looking for similar but cheaper products
2. Suggesting budget-friendly alternatives
3. Explaining what trade-offs would be needed

Products over budget:
"""
            for p in original_results[:3]:
                alt_input += f"- {p.get('title')}: ${p.get('price')}\n"
        
        elif constraint_type == "rating":
            alt_input = f"""The search results have lower ratings than desired (minimum: {constraint_value}).
Help find better-rated alternatives."""
        
        else:
            alt_input = f"""Constraint '{constraint_type}' with value '{constraint_value}' couldn't be met.
Help find alternatives that better match the user's needs."""
        
        # Run the agent
        state = await self.run(alt_input, state, context)
        
        return state
