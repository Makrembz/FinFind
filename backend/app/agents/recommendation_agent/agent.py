"""
RecommendationAgent Implementation for FinFind.

Generates personalized product recommendations based on user profile,
preferences, and financial context.
"""

import logging
from typing import Dict, Any, List, Optional

from langchain_core.tools import BaseTool

from ..base import BaseAgent, AgentState, ConversationContext
from ..config import AgentConfig, AgentType, get_config
from ..tools import (
    QdrantRecommendTool,
    GetUserProfileTool,
    CalculateAffordabilityTool,
    RankByConstraintsTool
)
from .prompts import RECOMMENDATION_AGENT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class RecommendationAgent(BaseAgent):
    """
    RecommendationAgent for FinFind.
    
    Specializes in:
    - Retrieving and understanding user profiles
    - Generating personalized recommendations
    - Ranking by relevance + affordability
    - Considering purchase history
    """
    
    agent_type = AgentType.RECOMMENDATION
    agent_name = "RecommendationAgent"
    agent_description = "Generates personalized product recommendations based on user profile"
    
    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        tools: Optional[List[BaseTool]] = None
    ):
        """Initialize the RecommendationAgent."""
        super().__init__(config, tools)
        self._rec_config = self.config.recommendation
    
    def _create_default_tools(self) -> List[BaseTool]:
        """Create the default tools for RecommendationAgent."""
        return [
            QdrantRecommendTool(),
            GetUserProfileTool(),
            CalculateAffordabilityTool(),
            RankByConstraintsTool()
        ]
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for RecommendationAgent."""
        return RECOMMENDATION_AGENT_SYSTEM_PROMPT
    
    async def recommend(
        self,
        user_id: str,
        state: Optional[AgentState] = None,
        context: Optional[ConversationContext] = None,
        category: Optional[str] = None,
        num_recommendations: int = 5
    ) -> AgentState:
        """
        Generate personalized recommendations for a user.
        
        Args:
            user_id: The user ID to generate recommendations for.
            state: Optional existing agent state.
            context: Optional conversation context.
            category: Optional category to focus on.
            num_recommendations: Number of recommendations to generate.
            
        Returns:
            AgentState with recommendations.
        """
        # Build comprehensive input
        rec_input = f"Generate {num_recommendations} personalized product recommendations for user {user_id}."
        
        if category:
            rec_input += f"\nFocus on category: {category}"
        
        if context and context.user:
            if context.user.financial.budget_max:
                rec_input += f"\nUser's budget: up to ${context.user.financial.budget_max}"
            if context.user.preferred_categories:
                rec_input += f"\nPreferred categories: {', '.join(context.user.preferred_categories)}"
        
        rec_input += "\nEnsure recommendations fit the user's financial situation and preferences."
        
        # Run the agent
        state = await self.run(rec_input, state, context)
        
        return state
    
    def recommend_sync(
        self,
        user_id: str,
        state: Optional[AgentState] = None,
        context: Optional[ConversationContext] = None,
        category: Optional[str] = None,
        num_recommendations: int = 5
    ) -> AgentState:
        """Synchronous version of recommend()."""
        rec_input = f"Generate {num_recommendations} personalized product recommendations for user {user_id}."
        
        if category:
            rec_input += f"\nFocus on category: {category}"
        
        if context and context.user:
            if context.user.financial.budget_max:
                rec_input += f"\nUser's budget: up to ${context.user.financial.budget_max}"
        
        return self.run_sync(rec_input, state, context)
    
    def get_recommendations(
        self,
        user_id: str,
        category: Optional[str] = None,
        max_price: Optional[float] = None,
        num_recommendations: int = 5
    ) -> Dict[str, Any]:
        """
        Get recommendations without full agent execution.
        
        Directly calls tools for faster results.
        
        Args:
            user_id: User ID.
            category: Optional category filter.
            max_price: Optional price limit.
            num_recommendations: Number of recommendations.
            
        Returns:
            Dictionary with recommendations and user profile.
        """
        # Get tools
        profile_tool = GetUserProfileTool()
        recommend_tool = QdrantRecommendTool()
        affordability_tool = CalculateAffordabilityTool()
        rank_tool = RankByConstraintsTool()
        
        # Get user profile
        profile_result = profile_tool._run(
            user_id=user_id,
            include_history=True
        )
        
        if not profile_result.get('success'):
            return {
                "success": False,
                "error": profile_result.get('error', "Failed to get user profile"),
                "recommendations": []
            }
        
        user_profile = profile_result['profile']
        
        # Determine max price
        effective_max_price = max_price
        if not effective_max_price:
            effective_max_price = user_profile.get('financial_context', {}).get('budget_max')
        
        # Get recommendations
        rec_result = recommend_tool._run(
            user_id=user_id,
            limit=num_recommendations * 2,  # Get more for ranking
            category=category,
            max_price=effective_max_price
        )
        
        if not rec_result.get('success'):
            return {
                "success": False,
                "error": rec_result.get('error', "Failed to get recommendations"),
                "recommendations": []
            }
        
        recommendations = rec_result.get('recommendations', [])
        
        # Calculate affordability for each
        budget_max = user_profile.get('financial_context', {}).get('budget_max')
        monthly_income = user_profile.get('financial_context', {}).get('monthly_budget')
        
        for rec in recommendations:
            aff_result = affordability_tool._run(
                product_price=rec.get('price', 0),
                user_budget_max=budget_max,
                user_monthly_income=monthly_income,
                risk_tolerance=user_profile.get('financial_context', {}).get('risk_tolerance', 'medium')
            )
            rec['affordability'] = {
                'score': aff_result.get('affordability_score'),
                'level': aff_result.get('affordability_level'),
                'recommendation': aff_result.get('recommendation')
            }
        
        # Rank by constraints
        if recommendations:
            ranked_result = rank_tool._run(
                products=recommendations,
                user_profile=user_profile,
                weights={
                    "relevance": self._rec_config.relevance_weight,
                    "affordability": self._rec_config.affordability_weight,
                    "rating": self._rec_config.rating_weight,
                    "preference_match": self._rec_config.popularity_weight
                }
            )
            recommendations = ranked_result.get('products', recommendations)
        
        # Return top recommendations
        return {
            "success": True,
            "user_id": user_id,
            "user_persona": user_profile.get('persona_type'),
            "budget_max": budget_max,
            "recommendations": recommendations[:num_recommendations]
        }
    
    async def recommend_with_explanation(
        self,
        user_id: str,
        num_recommendations: int = 5
    ) -> Dict[str, Any]:
        """
        Get recommendations with detailed explanations.
        
        Combines RecommendationAgent with ExplainabilityAgent.
        
        Args:
            user_id: User ID.
            num_recommendations: Number of recommendations.
            
        Returns:
            Dictionary with recommendations and explanations.
        """
        # First get recommendations
        rec_result = self.get_recommendations(
            user_id=user_id,
            num_recommendations=num_recommendations
        )
        
        if not rec_result.get('success'):
            return rec_result
        
        # Check if ExplainabilityAgent is registered
        if 'ExplainabilityAgent' in self._other_agents:
            # Delegate explanation generation
            state = AgentState(input_text="Generate explanations")
            state.results['recommendations'] = rec_result['recommendations']
            state.results['user_profile'] = {'user_id': user_id}
            
            state = await self.delegate_to(
                'ExplainabilityAgent',
                f"Explain why these {len(rec_result['recommendations'])} products are recommended",
                state
            )
            
            # Merge explanations
            if state.output_explanations:
                for i, rec in enumerate(rec_result['recommendations']):
                    if i < len(state.output_explanations):
                        rec['explanation'] = state.output_explanations[i]
        
        return rec_result
