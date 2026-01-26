"""
Recommendation Tools for FinFind RecommendationAgent.

Provides tools for user profile retrieval, affordability calculation,
and constraint-based ranking.
"""

import logging
from typing import Dict, Any, List, Optional, Type
from pydantic import BaseModel, Field

from langchain_core.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range

from .qdrant_tools import get_qdrant_client
from ..config import get_config

logger = logging.getLogger(__name__)


# ========================================
# Input Schemas
# ========================================

class GetUserProfileInput(BaseModel):
    """Input schema for getting user profile."""
    
    user_id: str = Field(description="The user ID to look up")
    include_history: bool = Field(
        default=True,
        description="Include purchase and browsing history"
    )
    include_interactions: bool = Field(
        default=False,
        description="Include recent interactions"
    )


class CalculateAffordabilityInput(BaseModel):
    """Input schema for affordability calculation."""
    
    product_price: float = Field(description="Product price")
    user_budget_max: Optional[float] = Field(
        default=None,
        description="User's maximum budget"
    )
    user_monthly_income: Optional[float] = Field(
        default=None,
        description="User's monthly income"
    )
    user_disposable_income: Optional[float] = Field(
        default=None,
        description="User's disposable income"
    )
    risk_tolerance: str = Field(
        default="medium",
        description="User's risk tolerance: low, medium, high"
    )


class RankByConstraintsInput(BaseModel):
    """Input schema for constraint-based ranking."""
    
    products: List[Dict] = Field(description="Products to rank")
    user_profile: Dict = Field(description="User profile with preferences")
    weights: Optional[Dict[str, float]] = Field(
        default=None,
        description="Custom weights for ranking factors"
    )


# ========================================
# Get User Profile Tool
# ========================================

class GetUserProfileTool(BaseTool):
    """
    Tool for retrieving user profile from Qdrant.
    
    Gets user preferences, financial context, and optionally
    purchase/browsing history.
    """
    
    name: str = "get_user_profile"
    description: str = """Retrieve a user's profile and preferences from the database.
Use this to get:
- User persona type
- Financial context (budget, income, risk tolerance)
- Category and brand preferences
- Purchase history (if include_history=True)

Essential for personalized recommendations."""
    
    args_schema: Type[BaseModel] = GetUserProfileInput
    
    def _run(
        self,
        user_id: str,
        include_history: bool = True,
        include_interactions: bool = False,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """Get user profile."""
        try:
            client = get_qdrant_client()
            config = get_config().qdrant
            
            # Get user profile
            user_results = client.scroll(
                collection_name=config.user_profiles_collection,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="original_id",
                            match=MatchValue(value=user_id)
                        )
                    ]
                ),
                limit=1
            )
            
            if not user_results[0]:
                return {
                    "success": False,
                    "error": f"User {user_id} not found",
                    "profile": None
                }
            
            user_point = user_results[0][0]
            profile = user_point.payload
            
            # Get recent interactions if requested
            interactions = []
            if include_interactions:
                interaction_results = client.scroll(
                    collection_name=config.interactions_collection,
                    scroll_filter=Filter(
                        must=[
                            FieldCondition(
                                key="user_id",
                                match=MatchValue(value=user_id)
                            )
                        ]
                    ),
                    limit=20
                )
                
                if interaction_results[0]:
                    interactions = [
                        {
                            "type": p.payload.get('interaction_type'),
                            "product_id": p.payload.get('product_id'),
                            "timestamp": p.payload.get('timestamp')
                        }
                        for p in interaction_results[0]
                    ]
            
            return {
                "success": True,
                "user_id": user_id,
                "profile": {
                    "persona_type": profile.get('persona_type'),
                    "financial_context": {
                        "budget_min": profile.get('budget_min'),
                        "budget_max": profile.get('budget_max'),
                        "monthly_budget": profile.get('monthly_budget'),
                        "disposable_income": profile.get('disposable_income'),
                        "risk_tolerance": profile.get('risk_tolerance', 'medium'),
                        "affordability_score": profile.get('affordability_score')
                    },
                    "preferences": {
                        "preferred_categories": profile.get('preferred_categories', []),
                        "preferred_brands": profile.get('preferred_brands', []),
                        "category_affinity": profile.get('category_affinity', {})
                    },
                    "history": {
                        "purchase_history": profile.get('purchase_history', []) if include_history else [],
                        "total_purchases": len(profile.get('purchase_history', []))
                    }
                },
                "recent_interactions": interactions if include_interactions else None
            }
            
        except Exception as e:
            logger.exception(f"Get user profile error: {e}")
            return {
                "success": False,
                "error": str(e),
                "profile": None
            }
    
    async def _arun(self, *args, **kwargs) -> Dict[str, Any]:
        """Async version."""
        return self._run(*args, **kwargs)


# ========================================
# Calculate Affordability Tool
# ========================================

class CalculateAffordabilityTool(BaseTool):
    """
    Tool for calculating product affordability.
    
    Determines how affordable a product is for a user
    based on their financial context.
    """
    
    name: str = "calculate_affordability"
    description: str = """Calculate how affordable a product is for a user.
Returns an affordability score (0-1) and detailed breakdown.
Considers:
- Price vs budget
- Price vs income ratio
- Risk tolerance

Score interpretation:
- 1.0: Very affordable
- 0.7+: Comfortable
- 0.4-0.7: Stretch budget
- <0.4: May not be affordable"""
    
    args_schema: Type[BaseModel] = CalculateAffordabilityInput
    
    def _run(
        self,
        product_price: float,
        user_budget_max: Optional[float] = None,
        user_monthly_income: Optional[float] = None,
        user_disposable_income: Optional[float] = None,
        risk_tolerance: str = "medium",
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """Calculate affordability."""
        try:
            scores = []
            breakdown = {}
            
            # Budget score
            if user_budget_max:
                budget_ratio = product_price / user_budget_max
                if budget_ratio <= 0.5:
                    budget_score = 1.0
                elif budget_ratio <= 1.0:
                    budget_score = 1.0 - (budget_ratio - 0.5) * 0.6
                elif budget_ratio <= 1.2:
                    budget_score = 0.4 - (budget_ratio - 1.0) * 1.5
                else:
                    budget_score = max(0, 0.1 - (budget_ratio - 1.2) * 0.5)
                
                scores.append(budget_score)
                breakdown['budget_score'] = round(budget_score, 3)
                breakdown['budget_ratio'] = round(budget_ratio, 3)
            
            # Income score
            if user_monthly_income:
                income_ratio = product_price / user_monthly_income
                if income_ratio <= 0.1:
                    income_score = 1.0
                elif income_ratio <= 0.25:
                    income_score = 1.0 - (income_ratio - 0.1) * 2
                elif income_ratio <= 0.5:
                    income_score = 0.7 - (income_ratio - 0.25) * 2
                else:
                    income_score = max(0, 0.2 - (income_ratio - 0.5))
                
                scores.append(income_score)
                breakdown['income_score'] = round(income_score, 3)
                breakdown['income_ratio'] = round(income_ratio, 3)
            
            # Disposable income score
            if user_disposable_income:
                disposable_ratio = product_price / user_disposable_income
                if disposable_ratio <= 0.3:
                    disposable_score = 1.0
                elif disposable_ratio <= 0.6:
                    disposable_score = 1.0 - (disposable_ratio - 0.3) * 1.5
                else:
                    disposable_score = max(0, 0.5 - (disposable_ratio - 0.6))
                
                scores.append(disposable_score)
                breakdown['disposable_score'] = round(disposable_score, 3)
            
            # Calculate final score
            if scores:
                base_score = sum(scores) / len(scores)
            else:
                base_score = 0.5  # Unknown financial context
            
            # Adjust for risk tolerance
            risk_adjustments = {
                "low": -0.1,
                "medium": 0,
                "high": 0.1
            }
            adjusted_score = base_score + risk_adjustments.get(risk_tolerance, 0)
            final_score = max(0, min(1, adjusted_score))
            
            # Determine affordability level
            if final_score >= 0.8:
                level = "very_affordable"
                recommendation = "Well within budget"
            elif final_score >= 0.6:
                level = "affordable"
                recommendation = "Comfortable purchase"
            elif final_score >= 0.4:
                level = "stretch"
                recommendation = "Consider carefully - stretches budget"
            else:
                level = "not_affordable"
                recommendation = "May not be affordable - consider alternatives"
            
            return {
                "success": True,
                "product_price": product_price,
                "affordability_score": round(final_score, 3),
                "affordability_level": level,
                "recommendation": recommendation,
                "breakdown": breakdown,
                "risk_tolerance": risk_tolerance
            }
            
        except Exception as e:
            logger.exception(f"Affordability calculation error: {e}")
            return {
                "success": False,
                "error": str(e),
                "affordability_score": None
            }
    
    async def _arun(self, *args, **kwargs) -> Dict[str, Any]:
        """Async version."""
        return self._run(*args, **kwargs)


# ========================================
# Rank By Constraints Tool
# ========================================

class RankByConstraintsTool(BaseTool):
    """
    Tool for ranking products by multiple constraints.
    
    Combines relevance, affordability, rating, and user
    preferences into a single ranking score.
    """
    
    name: str = "rank_by_constraints"
    description: str = """Rank products using multiple weighted factors.
Combines:
- Semantic relevance score
- Affordability score
- Product rating
- Category/brand preference match
- Popularity

Customize weights or use defaults:
- relevance: 0.4
- affordability: 0.3
- rating: 0.2
- popularity: 0.1"""
    
    args_schema: Type[BaseModel] = RankByConstraintsInput
    
    def _run(
        self,
        products: List[Dict],
        user_profile: Dict,
        weights: Optional[Dict[str, float]] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """Rank products by constraints."""
        try:
            # Default weights
            default_weights = {
                "relevance": 0.4,
                "affordability": 0.3,
                "rating": 0.2,
                "preference_match": 0.1
            }
            w = weights or default_weights
            
            # Normalize weights
            total_weight = sum(w.values())
            w = {k: v / total_weight for k, v in w.items()}
            
            # Get user preferences
            preferred_categories = set(
                user_profile.get('preferences', {}).get('preferred_categories', [])
            )
            preferred_brands = set(
                user_profile.get('preferences', {}).get('preferred_brands', [])
            )
            budget_max = user_profile.get('financial_context', {}).get('budget_max')
            
            ranked_products = []
            
            for product in products:
                # Relevance score (from search)
                relevance_score = product.get('score', product.get('similarity_score', 0.5))
                
                # Affordability score
                price = product.get('price', 0)
                if budget_max and budget_max > 0:
                    if price <= budget_max:
                        affordability_score = 1.0 - (price / budget_max) * 0.3
                    else:
                        affordability_score = max(0, 0.7 - (price - budget_max) / budget_max)
                else:
                    affordability_score = 0.5
                
                # Rating score (normalize to 0-1)
                rating = product.get('rating', 3.0)
                rating_score = (rating - 1) / 4  # Convert 1-5 to 0-1
                
                # Preference match score
                category = product.get('category', '')
                brand = product.get('brand', '')
                preference_score = 0.5
                if category in preferred_categories:
                    preference_score += 0.25
                if brand.lower() in [b.lower() for b in preferred_brands]:
                    preference_score += 0.25
                
                # Calculate final score
                final_score = (
                    w.get('relevance', 0) * relevance_score +
                    w.get('affordability', 0) * affordability_score +
                    w.get('rating', 0) * rating_score +
                    w.get('preference_match', 0) * preference_score
                )
                
                ranked_products.append({
                    **product,
                    "ranking_score": round(final_score, 4),
                    "score_breakdown": {
                        "relevance": round(relevance_score, 3),
                        "affordability": round(affordability_score, 3),
                        "rating": round(rating_score, 3),
                        "preference_match": round(preference_score, 3)
                    }
                })
            
            # Sort by ranking score
            ranked_products.sort(key=lambda x: -x['ranking_score'])
            
            return {
                "success": True,
                "count": len(ranked_products),
                "weights_used": w,
                "products": ranked_products
            }
            
        except Exception as e:
            logger.exception(f"Ranking error: {e}")
            return {
                "success": False,
                "error": str(e),
                "products": products
            }
    
    async def _arun(self, *args, **kwargs) -> Dict[str, Any]:
        """Async version."""
        return self._run(*args, **kwargs)
