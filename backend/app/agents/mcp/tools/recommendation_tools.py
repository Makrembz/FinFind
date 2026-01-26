"""
MCP Recommendation Tools for FinFind RecommendationAgent.

Tools for user profiling, affordability scoring, and personalized recommendations.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from pydantic import BaseModel, Field

from ..protocol import (
    MCPTool, MCPToolMetadata, MCPToolOutput,
    MCPError, MCPErrorCode
)
from ...services import get_qdrant_service, get_embedding_service, get_cache_service
from ...config import get_config

logger = logging.getLogger(__name__)


# ========================================
# Input Schemas
# ========================================

class UserProfileInput(BaseModel):
    """Input for user profile retrieval."""
    user_id: str = Field(..., description="User ID to fetch profile for")
    include_preferences: bool = Field(default=True, description="Include user preferences")
    include_history: bool = Field(default=False, description="Include interaction history")


class InteractionHistoryInput(BaseModel):
    """Input for interaction history retrieval."""
    user_id: str = Field(..., description="User ID")
    limit: int = Field(default=50, ge=1, le=200, description="Max interactions to return")
    interaction_types: Optional[List[str]] = Field(
        default=None,
        description="Filter by interaction types (view, click, purchase, etc.)"
    )
    days_back: int = Field(default=30, ge=1, le=365, description="Days of history to fetch")


class AffordabilityInput(BaseModel):
    """Input for affordability calculation."""
    products: List[Dict[str, Any]] = Field(..., description="Products to score")
    user_profile: Dict[str, Any] = Field(..., description="User financial profile")
    include_financing: bool = Field(default=True, description="Consider financing options")


class RankingInput(BaseModel):
    """Input for product ranking."""
    products: List[Dict[str, Any]] = Field(..., description="Products to rank")
    user_profile: Optional[Dict[str, Any]] = Field(default=None, description="User profile")
    query: Optional[str] = Field(default=None, description="Original search query")
    weights: Optional[Dict[str, float]] = Field(
        default=None,
        description="Custom weights for ranking factors"
    )


class ContextualRecInput(BaseModel):
    """Input for contextual recommendations."""
    user_id: str = Field(..., description="User ID")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Current context")
    limit: int = Field(default=10, ge=1, le=50, description="Number of recommendations")
    exclude_ids: Optional[List[str]] = Field(default=None, description="Product IDs to exclude")


# ========================================
# Get User Financial Profile Tool
# ========================================

class GetUserFinancialProfileTool(MCPTool):
    """
    MCP tool for retrieving user financial profiles from Qdrant.
    
    Fetches comprehensive user data including:
    - Demographics
    - Financial information
    - Preferences
    - Budget constraints
    """
    
    name: str = "get_user_financial_profile"
    description: str = """
    Retrieves user's financial profile from the database.
    Includes budget range, income level, risk tolerance, and preferences.
    Essential for personalized recommendations.
    """
    args_schema: type = UserProfileInput
    
    mcp_metadata: MCPToolMetadata = MCPToolMetadata(
        name="get_user_financial_profile",
        description="Fetch user financial profile from Qdrant",
        category="recommendation",
        tags=["user", "profile", "financial", "qdrant"],
        requires_qdrant=True,
        cacheable=True,
        cache_ttl_seconds=300,
        avg_latency_ms=50
    )
    
    def _execute(
        self,
        user_id: str,
        include_preferences: bool = True,
        include_history: bool = False
    ) -> MCPToolOutput:
        """Fetch user profile."""
        
        qdrant = get_qdrant_service()
        cache = get_cache_service()
        config = get_config()
        
        # Check cache
        cache_key = f"{user_id}:{include_preferences}:{include_history}"
        cached = cache.get("user_profile", cache_key)
        if cached:
            return MCPToolOutput.success_response(
                data=cached,
                cache_hit=True
            )
        
        try:
            # Fetch from Qdrant
            result = qdrant.get_point(
                collection=config.qdrant.user_profiles_collection,
                point_id=user_id
            )
            
            if not result:
                raise MCPError(
                    code=MCPErrorCode.RESOURCE_NOT_FOUND,
                    message=f"User profile not found: {user_id}"
                )
            
            payload = result.get("payload", {})
            
            # Build profile
            profile = {
                "user_id": user_id,
                "persona_type": payload.get("persona_type"),
                "demographics": {
                    "age_group": payload.get("age_group"),
                    "location": payload.get("location"),
                    "occupation": payload.get("occupation")
                },
                "financial": {
                    "income_bracket": payload.get("income_bracket"),
                    "budget_min": payload.get("budget_min"),
                    "budget_max": payload.get("budget_max"),
                    "monthly_budget": payload.get("monthly_budget"),
                    "disposable_income": payload.get("disposable_income"),
                    "risk_tolerance": payload.get("risk_tolerance", "medium"),
                    "preferred_payment_methods": payload.get("preferred_payment_methods", [])
                }
            }
            
            if include_preferences:
                profile["preferences"] = {
                    "preferred_categories": payload.get("preferred_categories", []),
                    "preferred_brands": payload.get("preferred_brands", []),
                    "quality_preference": payload.get("quality_preference", "balanced"),
                    "price_sensitivity": payload.get("price_sensitivity", "medium")
                }
            
            # Cache result
            cache.set("user_profile", cache_key, profile, ttl=300)
            
            return MCPToolOutput.success_response(
                data={"profile": profile, "found": True}
            )
            
        except MCPError:
            raise
        except Exception as e:
            logger.exception(f"Failed to fetch user profile: {e}")
            raise MCPError(
                code=MCPErrorCode.QDRANT_ERROR,
                message=f"Failed to fetch profile: {str(e)}",
                details={"user_id": user_id}
            )


# ========================================
# Get User Interaction History Tool
# ========================================

class GetUserInteractionHistoryTool(MCPTool):
    """
    MCP tool for retrieving user interaction history.
    
    Fetches past interactions for collaborative filtering:
    - Views
    - Clicks
    - Purchases
    - Ratings
    """
    
    name: str = "get_user_interaction_history"
    description: str = """
    Retrieves user's past interactions with products.
    Includes views, clicks, purchases, and ratings.
    Used for collaborative filtering and personalization.
    """
    args_schema: type = InteractionHistoryInput
    
    mcp_metadata: MCPToolMetadata = MCPToolMetadata(
        name="get_user_interaction_history",
        description="Fetch user interaction history",
        category="recommendation",
        tags=["user", "history", "interactions", "qdrant"],
        requires_qdrant=True,
        cacheable=True,
        cache_ttl_seconds=120,
        avg_latency_ms=100
    )
    
    def _execute(
        self,
        user_id: str,
        limit: int = 50,
        interaction_types: Optional[List[str]] = None,
        days_back: int = 30
    ) -> MCPToolOutput:
        """Fetch interaction history."""
        
        qdrant = get_qdrant_service()
        config = get_config()
        
        try:
            # Build filters
            filters = {"user_id": user_id}
            
            if interaction_types:
                filters["interaction_type"] = {"any": interaction_types}
            
            # Calculate date cutoff
            cutoff = datetime.utcnow() - timedelta(days=days_back)
            filters["timestamp"] = {"range": {"gte": cutoff.isoformat()}}
            
            # Scroll through interactions
            result = qdrant.scroll(
                collection=config.qdrant.interactions_collection,
                filters=filters,
                limit=limit
            )
            
            interactions = result.get("points", [])
            
            # Aggregate by type
            by_type = {}
            product_ids = set()
            
            for interaction in interactions:
                payload = interaction.get("payload", {})
                int_type = payload.get("interaction_type", "unknown")
                
                if int_type not in by_type:
                    by_type[int_type] = []
                by_type[int_type].append(payload)
                
                if payload.get("product_id"):
                    product_ids.add(payload["product_id"])
            
            # Calculate engagement metrics
            metrics = {
                "total_interactions": len(interactions),
                "unique_products": len(product_ids),
                "interaction_breakdown": {k: len(v) for k, v in by_type.items()},
                "days_active": days_back
            }
            
            return MCPToolOutput.success_response(
                data={
                    "user_id": user_id,
                    "interactions": interactions,
                    "by_type": by_type,
                    "interacted_product_ids": list(product_ids),
                    "metrics": metrics
                }
            )
            
        except Exception as e:
            logger.exception(f"Failed to fetch interactions: {e}")
            raise MCPError(
                code=MCPErrorCode.QDRANT_ERROR,
                message=f"Failed to fetch interactions: {str(e)}"
            )


# ========================================
# Calculate Affordability Match Tool
# ========================================

class CalculateAffordabilityMatchTool(MCPTool):
    """
    MCP tool for calculating affordability scores.
    
    Scores products against user's financial profile:
    - Budget fit
    - Monthly payment feasibility
    - Risk assessment
    """
    
    name: str = "calculate_affordability_match"
    description: str = """
    Calculates how affordable each product is for a user.
    Considers budget, income, and risk tolerance.
    Returns affordability score (0-1) and explanation.
    """
    args_schema: type = AffordabilityInput
    
    mcp_metadata: MCPToolMetadata = MCPToolMetadata(
        name="calculate_affordability_match",
        description="Score products by affordability",
        category="recommendation",
        tags=["affordability", "financial", "scoring"],
        requires_qdrant=False,
        cacheable=False,
        avg_latency_ms=20
    )
    
    def _execute(
        self,
        products: List[Dict[str, Any]],
        user_profile: Dict[str, Any],
        include_financing: bool = True
    ) -> MCPToolOutput:
        """Calculate affordability for products."""
        
        if not products:
            return MCPToolOutput.success_response(
                data={"scored_products": [], "summary": {}}
            )
        
        # Extract financial data
        financial = user_profile.get("financial", {})
        budget_max = financial.get("budget_max")
        budget_min = financial.get("budget_min")
        monthly_budget = financial.get("monthly_budget")
        disposable_income = financial.get("disposable_income")
        risk_tolerance = financial.get("risk_tolerance", "medium")
        
        # Risk tolerance multipliers
        risk_multipliers = {
            "conservative": 0.7,
            "moderate": 0.85,
            "medium": 0.85,
            "aggressive": 1.0
        }
        risk_mult = risk_multipliers.get(risk_tolerance, 0.85)
        
        scored_products = []
        
        for product in products:
            price = product.get("price", 0)
            
            # Base affordability score
            affordability = 1.0
            reasons = []
            
            # Budget check
            if budget_max:
                if price > budget_max:
                    affordability *= max(0.1, budget_max / price)
                    reasons.append(f"Price exceeds budget by ${price - budget_max:.2f}")
                elif price < budget_max * 0.5:
                    affordability *= 1.0
                    reasons.append("Well within budget")
                else:
                    budget_ratio = price / budget_max
                    affordability *= (1 - (budget_ratio - 0.5))
                    reasons.append(f"Uses {budget_ratio*100:.0f}% of budget")
            
            # Monthly budget impact
            if monthly_budget and price > 0:
                monthly_impact = (price / monthly_budget) * 100
                if monthly_impact > 50:
                    affordability *= 0.7
                    reasons.append(f"High monthly impact ({monthly_impact:.0f}%)")
            
            # Disposable income check
            if disposable_income:
                income_ratio = price / disposable_income
                if income_ratio > 1:
                    affordability *= 0.5
                    reasons.append("Exceeds monthly disposable income")
                elif income_ratio > 0.5:
                    affordability *= 0.8
                    reasons.append("Significant portion of disposable income")
            
            # Apply risk tolerance
            affordability *= risk_mult
            
            # Financing option boost
            if include_financing and product.get("financing_available"):
                if affordability < 0.5:
                    affordability = min(1.0, affordability * 1.3)
                    reasons.append("Financing available")
            
            # Clamp score
            affordability = max(0, min(1, affordability))
            
            # Determine fit level
            if affordability >= 0.8:
                fit_level = "excellent"
            elif affordability >= 0.6:
                fit_level = "good"
            elif affordability >= 0.4:
                fit_level = "moderate"
            elif affordability >= 0.2:
                fit_level = "stretch"
            else:
                fit_level = "poor"
            
            scored_product = {
                **product,
                "affordability_score": round(affordability, 3),
                "fit_level": fit_level,
                "affordability_reasons": reasons
            }
            scored_products.append(scored_product)
        
        # Sort by affordability
        scored_products.sort(key=lambda x: x["affordability_score"], reverse=True)
        
        # Summary
        avg_score = sum(p["affordability_score"] for p in scored_products) / len(scored_products)
        affordable_count = sum(1 for p in scored_products if p["fit_level"] in ["excellent", "good"])
        
        return MCPToolOutput.success_response(
            data={
                "scored_products": scored_products,
                "summary": {
                    "total_products": len(scored_products),
                    "affordable_products": affordable_count,
                    "average_affordability": round(avg_score, 3),
                    "budget_used": budget_max
                }
            }
        )


# ========================================
# Rank Products By Constraints Tool
# ========================================

class RankProductsByConstraintsTool(MCPTool):
    """
    MCP tool for ranking products by multiple constraints.
    
    Combines scores from:
    - Semantic relevance
    - Financial fit
    - User preferences
    - Product quality
    """
    
    name: str = "rank_products_by_constraints"
    description: str = """
    Re-ranks products by combining semantic relevance and financial fit.
    Uses weighted scoring across multiple factors.
    Returns products in optimal order for the user.
    """
    args_schema: type = RankingInput
    
    mcp_metadata: MCPToolMetadata = MCPToolMetadata(
        name="rank_products_by_constraints",
        description="Multi-factor product ranking",
        category="recommendation",
        tags=["ranking", "scoring", "personalization"],
        requires_embedding=True,
        cacheable=False,
        avg_latency_ms=50
    )
    
    # Default weights
    DEFAULT_WEIGHTS = {
        "relevance": 0.35,
        "affordability": 0.30,
        "preference_match": 0.20,
        "quality": 0.15
    }
    
    def _execute(
        self,
        products: List[Dict[str, Any]],
        user_profile: Optional[Dict[str, Any]] = None,
        query: Optional[str] = None,
        weights: Optional[Dict[str, float]] = None
    ) -> MCPToolOutput:
        """Rank products by constraints."""
        
        if not products:
            return MCPToolOutput.success_response(
                data={"ranked_products": [], "ranking_method": "none"}
            )
        
        # Use provided weights or defaults
        w = {**self.DEFAULT_WEIGHTS, **(weights or {})}
        
        # Normalize weights
        total_weight = sum(w.values())
        w = {k: v / total_weight for k, v in w.items()}
        
        embedding_service = get_embedding_service()
        
        # Get query embedding if provided
        query_embedding = None
        if query:
            query_embedding = embedding_service.embed(query)
        
        ranked = []
        
        for product in products:
            scores = {}
            
            # Relevance score (from search or computed)
            if "score" in product:
                scores["relevance"] = product["score"]
            elif query_embedding and product.get("embedding"):
                scores["relevance"] = embedding_service.similarity(
                    query_embedding,
                    product["embedding"]
                )
            else:
                scores["relevance"] = 0.5  # Default
            
            # Affordability score
            scores["affordability"] = product.get("affordability_score", 0.5)
            
            # Preference match
            pref_score = 0.5
            if user_profile:
                prefs = user_profile.get("preferences", {})
                
                # Category match
                pref_cats = prefs.get("preferred_categories", [])
                if pref_cats and product.get("category") in pref_cats:
                    pref_score += 0.2
                
                # Brand match
                pref_brands = prefs.get("preferred_brands", [])
                if pref_brands and product.get("brand") in pref_brands:
                    pref_score += 0.2
                
                # Quality preference
                quality_pref = prefs.get("quality_preference", "balanced")
                product_tier = product.get("tier", "standard")
                
                if quality_pref == "premium" and product_tier == "premium":
                    pref_score += 0.1
                elif quality_pref == "budget" and product_tier == "budget":
                    pref_score += 0.1
            
            scores["preference_match"] = min(1.0, pref_score)
            
            # Quality score
            quality_score = 0.5
            if product.get("rating"):
                quality_score = product["rating"] / 5.0
            if product.get("review_count", 0) > 100:
                quality_score += 0.1
            scores["quality"] = min(1.0, quality_score)
            
            # Calculate weighted total
            total_score = sum(scores[k] * w[k] for k in w.keys())
            
            ranked.append({
                **product,
                "ranking_score": round(total_score, 4),
                "score_breakdown": {k: round(v, 3) for k, v in scores.items()}
            })
        
        # Sort by ranking score
        ranked.sort(key=lambda x: x["ranking_score"], reverse=True)
        
        return MCPToolOutput.success_response(
            data={
                "ranked_products": ranked,
                "ranking_method": "weighted_multi_factor",
                "weights_used": w
            }
        )


# ========================================
# Get Contextual Recommendations Tool
# ========================================

class GetContextualRecommendationsTool(MCPTool):
    """
    MCP tool for contextual recommendations using collaborative filtering.
    
    Generates recommendations based on:
    - Similar user behavior
    - Interaction patterns
    - Current context
    """
    
    name: str = "get_contextual_recommendations"
    description: str = """
    Generates personalized recommendations using collaborative filtering.
    Considers user's interaction history and similar users' preferences.
    Adapts to current context (time, session, etc.).
    """
    args_schema: type = ContextualRecInput
    
    mcp_metadata: MCPToolMetadata = MCPToolMetadata(
        name="get_contextual_recommendations",
        description="Collaborative filtering recommendations",
        category="recommendation",
        tags=["collaborative", "personalization", "context"],
        requires_qdrant=True,
        cacheable=True,
        cache_ttl_seconds=180,
        avg_latency_ms=200
    )
    
    def _execute(
        self,
        user_id: str,
        context: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        exclude_ids: Optional[List[str]] = None
    ) -> MCPToolOutput:
        """Generate contextual recommendations."""
        
        qdrant = get_qdrant_service()
        config = get_config()
        
        try:
            # Get user's interaction history
            history_result = qdrant.scroll(
                collection=config.qdrant.interactions_collection,
                filters={"user_id": user_id},
                limit=100
            )
            
            interactions = history_result.get("points", [])
            
            # Extract positive signals (purchases, high ratings, bookmarks)
            positive_product_ids = set()
            negative_product_ids = set(exclude_ids or [])
            
            for interaction in interactions:
                payload = interaction.get("payload", {})
                product_id = payload.get("product_id")
                int_type = payload.get("interaction_type")
                
                if int_type in ["purchase", "bookmark", "add_to_cart"]:
                    positive_product_ids.add(product_id)
                elif int_type == "dislike":
                    negative_product_ids.add(product_id)
            
            if not positive_product_ids:
                # Cold start - use popular items
                return self._cold_start_recommendations(
                    context=context,
                    limit=limit,
                    exclude_ids=list(negative_product_ids)
                )
            
            # Use Qdrant recommend API
            recommendations = qdrant.recommend(
                collection=config.qdrant.products_collection,
                positive_ids=list(positive_product_ids)[:10],
                negative_ids=list(negative_product_ids)[:5] if negative_product_ids else None,
                limit=limit * 2,  # Get more to filter
                filters=None
            )
            
            # Filter out already interacted
            filtered = [
                r for r in recommendations
                if r["id"] not in positive_product_ids and r["id"] not in negative_product_ids
            ][:limit]
            
            # Format results
            products = []
            for rec in filtered:
                product = {
                    "id": rec["id"],
                    "recommendation_score": rec["score"],
                    **rec.get("payload", {})
                }
                products.append(product)
            
            return MCPToolOutput.success_response(
                data={
                    "recommendations": products,
                    "method": "collaborative_filtering",
                    "based_on": {
                        "positive_signals": len(positive_product_ids),
                        "negative_signals": len(negative_product_ids)
                    }
                }
            )
            
        except Exception as e:
            logger.exception(f"Recommendation generation failed: {e}")
            raise MCPError(
                code=MCPErrorCode.QDRANT_ERROR,
                message=f"Recommendation failed: {str(e)}"
            )
    
    def _cold_start_recommendations(
        self,
        context: Optional[Dict] = None,
        limit: int = 10,
        exclude_ids: Optional[List[str]] = None
    ) -> MCPToolOutput:
        """Handle cold start with popular/trending items."""
        
        qdrant = get_qdrant_service()
        config = get_config()
        
        # Get popular items (those with high ratings/reviews)
        result = qdrant.scroll(
            collection=config.qdrant.products_collection,
            filters=None,
            limit=limit * 3
        )
        
        products = result.get("points", [])
        
        # Sort by popularity signals
        sorted_products = sorted(
            products,
            key=lambda x: (
                x.get("payload", {}).get("review_count", 0) * 
                x.get("payload", {}).get("rating", 3)
            ),
            reverse=True
        )
        
        # Filter exclusions
        if exclude_ids:
            sorted_products = [
                p for p in sorted_products
                if p["id"] not in exclude_ids
            ]
        
        recommendations = []
        for p in sorted_products[:limit]:
            recommendations.append({
                "id": p["id"],
                "recommendation_score": 0.5,  # Default score for cold start
                **p.get("payload", {})
            })
        
        return MCPToolOutput.success_response(
            data={
                "recommendations": recommendations,
                "method": "popularity_based",
                "note": "Cold start - based on overall popularity"
            }
        )
