"""
ExplainabilityAgent Implementation for FinFind.

Generates transparent explanations for why products are
recommended, including semantic and financial analysis.
"""

import logging
from typing import Dict, Any, List, Optional

from langchain_core.tools import BaseTool

from ..base import BaseAgent, AgentState, ConversationContext
from ..config import AgentConfig, AgentType, get_config
from ..tools import (
    GetSimilarityScoreTool,
    ExplainFinancialFitTool,
    GenerateExplanationTool
)
from .prompts import EXPLAINABILITY_AGENT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class ExplainabilityAgent(BaseAgent):
    """
    ExplainabilityAgent for FinFind.
    
    Specializes in:
    - Explaining why products are recommended
    - Breaking down semantic similarity
    - Analyzing financial fit
    - Building user trust through transparency
    """
    
    agent_type = AgentType.EXPLAINABILITY
    agent_name = "ExplainabilityAgent"
    agent_description = "Generates transparent explanations for product recommendations"
    
    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        tools: Optional[List[BaseTool]] = None
    ):
        """Initialize the ExplainabilityAgent."""
        super().__init__(config, tools)
        self._explain_config = self.config.explainability
    
    def _create_default_tools(self) -> List[BaseTool]:
        """Create the default tools for ExplainabilityAgent."""
        return [
            GetSimilarityScoreTool(),
            ExplainFinancialFitTool(),
            GenerateExplanationTool()
        ]
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for ExplainabilityAgent."""
        return EXPLAINABILITY_AGENT_SYSTEM_PROMPT
    
    async def explain(
        self,
        product: Dict,
        state: Optional[AgentState] = None,
        context: Optional[ConversationContext] = None,
        query: Optional[str] = None,
        explanation_type: str = "detailed"
    ) -> AgentState:
        """
        Generate explanation for a product recommendation.
        
        Args:
            product: Product data to explain.
            state: Optional existing agent state.
            context: Optional conversation context.
            query: Optional original search query.
            explanation_type: Type of explanation (brief/detailed/comprehensive).
            
        Returns:
            AgentState with explanation.
        """
        # Build comprehensive input
        explain_input = f"Explain why this product is recommended:\n"
        explain_input += f"Product: {product.get('title', 'Unknown')}\n"
        explain_input += f"Price: ${product.get('price', 'N/A')}\n"
        explain_input += f"Category: {product.get('category', 'N/A')}\n"
        explain_input += f"Rating: {product.get('rating', 'N/A')}/5\n"
        
        if query:
            explain_input += f"\nOriginal search: {query}"
        
        if context and context.user:
            explain_input += f"\nUser budget: ${context.user.financial.budget_max}"
        
        explain_input += f"\n\nProvide a {explanation_type} explanation."
        
        # Run the agent
        state = await self.run(explain_input, state, context)
        
        return state
    
    def explain_sync(
        self,
        product: Dict,
        state: Optional[AgentState] = None,
        context: Optional[ConversationContext] = None,
        query: Optional[str] = None,
        explanation_type: str = "detailed"
    ) -> AgentState:
        """Synchronous version of explain()."""
        explain_input = f"Explain why this product is recommended:\n"
        explain_input += f"Product: {product.get('title', 'Unknown')}\n"
        explain_input += f"Price: ${product.get('price', 'N/A')}\n"
        
        if query:
            explain_input += f"\nOriginal search: {query}"
        
        return self.run_sync(explain_input, state, context)
    
    def get_explanation(
        self,
        product: Dict,
        user_profile: Optional[Dict] = None,
        query: Optional[str] = None,
        explanation_type: str = "detailed"
    ) -> Dict[str, Any]:
        """
        Get explanation without full agent execution.
        
        Directly calls tools for faster results.
        
        Args:
            product: Product data.
            user_profile: Optional user profile.
            query: Optional search query.
            explanation_type: Type of explanation.
            
        Returns:
            Dictionary with explanation components.
        """
        # Get tools
        similarity_tool = GetSimilarityScoreTool()
        financial_tool = ExplainFinancialFitTool()
        explanation_tool = GenerateExplanationTool()
        
        result = {
            "product_id": product.get('id') or product.get('original_id'),
            "product_title": product.get('title'),
            "components": {}
        }
        
        # Get similarity explanation if query provided
        similarity_score = None
        if query and product.get('id'):
            sim_result = similarity_tool._run(
                query=query,
                product_id=product.get('original_id', product.get('id')),
                include_matching_terms=True
            )
            if sim_result.get('success'):
                result['components']['similarity'] = {
                    'score': sim_result.get('similarity_score'),
                    'level': sim_result.get('relevance_level'),
                    'explanation': sim_result.get('explanation'),
                    'matching_terms': sim_result.get('matching_terms', [])
                }
                similarity_score = sim_result.get('similarity_score')
        
        # Get financial fit explanation if user profile provided
        affordability_score = None
        if user_profile and product.get('price'):
            financial = user_profile.get('financial_context', {})
            fin_result = financial_tool._run(
                product_price=product.get('price'),
                user_budget_max=financial.get('budget_max'),
                user_monthly_income=financial.get('monthly_budget'),
                affordability_score=product.get('affordability', {}).get('score')
            )
            if fin_result.get('success'):
                result['components']['financial_fit'] = {
                    'level': fin_result.get('fit_level'),
                    'summary': fin_result.get('summary'),
                    'factors': fin_result.get('fit_factors', []),
                    'details': fin_result.get('detailed_explanations', [])
                }
                affordability_score = fin_result.get('affordability_score')
        
        # Generate comprehensive explanation
        exp_result = explanation_tool._run(
            product=product,
            user_profile=user_profile,
            query=query,
            similarity_score=similarity_score,
            affordability_score=affordability_score,
            explanation_type=explanation_type
        )
        
        result['explanation'] = exp_result.get('explanation', '')
        result['explanation_type'] = explanation_type
        result['success'] = True
        
        return result
    
    def explain_multiple(
        self,
        products: List[Dict],
        user_profile: Optional[Dict] = None,
        query: Optional[str] = None,
        explanation_type: str = "brief"
    ) -> List[Dict]:
        """
        Generate explanations for multiple products.
        
        Args:
            products: List of products to explain.
            user_profile: Optional user profile.
            query: Optional search query.
            explanation_type: Type of explanation.
            
        Returns:
            List of explanation dictionaries.
        """
        explanations = []
        
        for product in products:
            exp = self.get_explanation(
                product=product,
                user_profile=user_profile,
                query=query,
                explanation_type=explanation_type
            )
            explanations.append(exp)
        
        return explanations
    
    def compare_products(
        self,
        products: List[Dict],
        user_profile: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Generate a comparison explanation for multiple products.
        
        Args:
            products: Products to compare.
            user_profile: Optional user profile.
            
        Returns:
            Comparison analysis.
        """
        if len(products) < 2:
            return {
                "success": False,
                "error": "Need at least 2 products to compare"
            }
        
        comparison = {
            "products": [],
            "comparison_points": []
        }
        
        # Analyze each product
        for product in products:
            analysis = {
                "id": product.get('id') or product.get('original_id'),
                "title": product.get('title'),
                "price": product.get('price'),
                "rating": product.get('rating'),
                "category": product.get('category')
            }
            
            # Calculate affordability if user profile available
            if user_profile:
                budget_max = user_profile.get('financial_context', {}).get('budget_max')
                if budget_max and product.get('price'):
                    price = product['price']
                    analysis['budget_percentage'] = round(price / budget_max * 100, 1)
                    analysis['within_budget'] = price <= budget_max
            
            comparison['products'].append(analysis)
        
        # Generate comparison points
        prices = [p.get('price', 0) for p in products]
        ratings = [p.get('rating', 0) for p in products]
        
        # Price comparison
        min_price_idx = prices.index(min(prices))
        max_price_idx = prices.index(max(prices))
        comparison['comparison_points'].append({
            "factor": "price",
            "best": products[min_price_idx].get('title'),
            "note": f"${min(prices)} vs ${max(prices)}"
        })
        
        # Rating comparison
        if any(ratings):
            max_rating_idx = ratings.index(max(ratings))
            comparison['comparison_points'].append({
                "factor": "rating",
                "best": products[max_rating_idx].get('title'),
                "note": f"{max(ratings)}/5 stars"
            })
        
        # Value score (rating / price)
        value_scores = [
            (r / p * 100) if p > 0 else 0 
            for r, p in zip(ratings, prices)
        ]
        if any(value_scores):
            best_value_idx = value_scores.index(max(value_scores))
            comparison['comparison_points'].append({
                "factor": "value",
                "best": products[best_value_idx].get('title'),
                "note": "Best rating-to-price ratio"
            })
        
        comparison['success'] = True
        return comparison
