"""
Feedback Analyzer for FinFind Learning System.

Analyzes user interaction patterns to calculate success metrics,
identify improvement opportunities, and generate insights for
agent tuning.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import statistics

from .models import (
    Interaction,
    InteractionType,
    FeedbackSignal,
    MetricType,
    MetricValue,
    LearningInsight,
    QueryProductMapping,
    AlternativeEffectiveness
)
from .interaction_logger import InteractionLogger, get_interaction_logger

logger = logging.getLogger(__name__)


class FeedbackAnalyzer:
    """
    Analyzes interaction feedback to derive insights and metrics.
    
    Responsibilities:
    - Calculate engagement metrics (CTR, conversion rates)
    - Identify search patterns and query-product mappings
    - Analyze constraint compliance
    - Generate improvement insights
    - Track recommendation and alternative effectiveness
    """
    
    def __init__(self, interaction_logger: Optional[InteractionLogger] = None):
        """
        Initialize the feedback analyzer.
        
        Args:
            interaction_logger: Logger to fetch interactions from
        """
        self._logger = interaction_logger or get_interaction_logger()
        
        # Caches for computed metrics
        self._query_mappings: Dict[str, QueryProductMapping] = {}
        self._alternative_effectiveness: Dict[str, AlternativeEffectiveness] = {}
        
        # Aggregated metrics cache
        self._metrics_cache: Dict[str, MetricValue] = {}
        self._cache_ttl = timedelta(minutes=15)
        self._last_cache_update: Optional[datetime] = None
    
    # ========================================
    # Core Metric Calculations
    # ========================================
    
    async def calculate_ctr(
        self,
        user_id: Optional[str] = None,
        agent: Optional[str] = None,
        time_window: timedelta = timedelta(days=7)
    ) -> MetricValue:
        """
        Calculate Click-Through Rate.
        
        CTR = clicks / impressions
        """
        since = datetime.utcnow() - time_window
        
        # Get view and click interactions
        view_types = [
            InteractionType.RECOMMENDATION_VIEW,
            InteractionType.ALTERNATIVE_VIEW,
            InteractionType.SEARCH
        ]
        click_types = [
            InteractionType.PRODUCT_CLICK,
            InteractionType.RECOMMENDATION_CLICK,
            InteractionType.ALTERNATIVE_CLICK
        ]
        
        interactions = await self._logger.get_user_interactions(
            user_id=user_id or "*",
            interaction_types=view_types + click_types,
            limit=10000,
            since=since
        )
        
        # Filter by agent if specified
        if agent:
            interactions = [i for i in interactions if i.context.agent_used == agent]
        
        # Count views and clicks
        views = sum(1 for i in interactions if i.interaction_type in view_types)
        clicks = sum(1 for i in interactions if i.interaction_type in click_types)
        
        ctr = clicks / views if views > 0 else 0.0
        
        return MetricValue(
            metric_type=MetricType.CTR,
            value=ctr,
            user_id=user_id,
            agent=agent,
            time_window="weekly"
        )
    
    async def calculate_conversion_funnel(
        self,
        user_id: Optional[str] = None,
        time_window: timedelta = timedelta(days=30)
    ) -> Dict[str, MetricValue]:
        """
        Calculate full conversion funnel metrics.
        
        Returns:
            Dict with search→click, click→cart, cart→purchase rates
        """
        since = datetime.utcnow() - time_window
        
        interactions = await self._logger.get_user_interactions(
            user_id=user_id or "*",
            limit=50000,
            since=since
        )
        
        # Count by type
        counts = defaultdict(int)
        for interaction in interactions:
            counts[interaction.interaction_type] += 1
        
        # Calculate funnel metrics
        searches = counts[InteractionType.SEARCH] + counts[InteractionType.VOICE_SEARCH] + counts[InteractionType.IMAGE_SEARCH]
        clicks = counts[InteractionType.PRODUCT_CLICK]
        carts = counts[InteractionType.ADD_TO_CART]
        purchases = counts[InteractionType.PURCHASE_COMPLETE]
        
        search_to_click = clicks / searches if searches > 0 else 0.0
        click_to_cart = carts / clicks if clicks > 0 else 0.0
        cart_to_purchase = purchases / carts if carts > 0 else 0.0
        overall_conversion = purchases / searches if searches > 0 else 0.0
        
        return {
            "search_to_click": MetricValue(
                metric_type=MetricType.CTR,
                value=search_to_click,
                user_id=user_id,
                time_window="monthly"
            ),
            "click_to_cart": MetricValue(
                metric_type=MetricType.CART_RATE,
                value=click_to_cart,
                user_id=user_id,
                time_window="monthly"
            ),
            "cart_to_purchase": MetricValue(
                metric_type=MetricType.PURCHASE_RATE,
                value=cart_to_purchase,
                user_id=user_id,
                time_window="monthly"
            ),
            "overall_conversion": MetricValue(
                metric_type=MetricType.CONVERSION_RATE,
                value=overall_conversion,
                user_id=user_id,
                time_window="monthly"
            )
        }
    
    async def calculate_constraint_compliance(
        self,
        user_id: Optional[str] = None,
        time_window: timedelta = timedelta(days=30)
    ) -> MetricValue:
        """
        Calculate how often budget constraints are respected.
        
        Compliance = interactions_within_budget / total_interactions_with_budget
        """
        since = datetime.utcnow() - time_window
        
        interactions = await self._logger.get_user_interactions(
            user_id=user_id or "*",
            interaction_types=[
                InteractionType.PRODUCT_CLICK,
                InteractionType.ADD_TO_CART,
                InteractionType.PURCHASE_COMPLETE
            ],
            limit=10000,
            since=since
        )
        
        # Only consider interactions where budget was set
        with_budget = [i for i in interactions if i.context.budget_max is not None]
        
        if not with_budget:
            return MetricValue(
                metric_type=MetricType.BUDGET_COMPLIANCE,
                value=1.0,
                user_id=user_id,
                time_window="monthly"
            )
        
        compliant = sum(1 for i in with_budget if not i.budget_exceeded)
        compliance_rate = compliant / len(with_budget)
        
        return MetricValue(
            metric_type=MetricType.BUDGET_COMPLIANCE,
            value=compliance_rate,
            user_id=user_id,
            time_window="monthly"
        )
    
    async def calculate_recommendation_metrics(
        self,
        user_id: Optional[str] = None,
        time_window: timedelta = timedelta(days=7)
    ) -> Dict[str, MetricValue]:
        """Calculate recommendation-specific metrics."""
        since = datetime.utcnow() - time_window
        
        interactions = await self._logger.get_user_interactions(
            user_id=user_id or "*",
            interaction_types=[
                InteractionType.RECOMMENDATION_VIEW,
                InteractionType.RECOMMENDATION_CLICK,
                InteractionType.RECOMMENDATION_DISMISS,
                InteractionType.ADD_TO_CART,
                InteractionType.PURCHASE_COMPLETE
            ],
            limit=10000,
            since=since
        )
        
        views = sum(1 for i in interactions if i.interaction_type == InteractionType.RECOMMENDATION_VIEW)
        clicks = sum(1 for i in interactions if i.interaction_type == InteractionType.RECOMMENDATION_CLICK)
        dismisses = sum(1 for i in interactions if i.interaction_type == InteractionType.RECOMMENDATION_DISMISS)
        
        # Track which recommended products were added to cart/purchased
        recommended_products = set()
        for i in interactions:
            if i.interaction_type == InteractionType.RECOMMENDATION_CLICK and i.item_interacted:
                recommended_products.add(i.item_interacted)
        
        rec_carts = sum(
            1 for i in interactions 
            if i.interaction_type == InteractionType.ADD_TO_CART 
            and i.item_interacted in recommended_products
        )
        rec_purchases = sum(
            1 for i in interactions 
            if i.interaction_type == InteractionType.PURCHASE_COMPLETE
            and any(pid in recommended_products for pid in i.items_shown)
        )
        
        ctr = clicks / views if views > 0 else 0.0
        dismiss_rate = dismisses / (views + dismisses) if (views + dismisses) > 0 else 0.0
        conversion = rec_purchases / clicks if clicks > 0 else 0.0
        
        return {
            "recommendation_ctr": MetricValue(
                metric_type=MetricType.RECOMMENDATION_CTR,
                value=ctr,
                user_id=user_id,
                agent="RecommendationAgent",
                time_window="weekly"
            ),
            "recommendation_dismiss_rate": MetricValue(
                metric_type=MetricType.BOUNCE_RATE,
                value=dismiss_rate,
                user_id=user_id,
                agent="RecommendationAgent",
                time_window="weekly"
            ),
            "recommendation_conversion": MetricValue(
                metric_type=MetricType.RECOMMENDATION_CONVERSION,
                value=conversion,
                user_id=user_id,
                agent="RecommendationAgent",
                time_window="weekly"
            )
        }
    
    async def calculate_alternative_metrics(
        self,
        user_id: Optional[str] = None,
        time_window: timedelta = timedelta(days=7)
    ) -> Dict[str, MetricValue]:
        """Calculate alternative suggestion effectiveness."""
        since = datetime.utcnow() - time_window
        
        interactions = await self._logger.get_user_interactions(
            user_id=user_id or "*",
            interaction_types=[
                InteractionType.ALTERNATIVE_VIEW,
                InteractionType.ALTERNATIVE_CLICK,
                InteractionType.ALTERNATIVE_ACCEPT,
                InteractionType.ALTERNATIVE_REJECT
            ],
            limit=10000,
            since=since
        )
        
        views = sum(1 for i in interactions if i.interaction_type == InteractionType.ALTERNATIVE_VIEW)
        clicks = sum(1 for i in interactions if i.interaction_type == InteractionType.ALTERNATIVE_CLICK)
        accepts = sum(1 for i in interactions if i.interaction_type == InteractionType.ALTERNATIVE_ACCEPT)
        rejects = sum(1 for i in interactions if i.interaction_type == InteractionType.ALTERNATIVE_REJECT)
        
        ctr = clicks / views if views > 0 else 0.0
        acceptance_rate = accepts / (accepts + rejects) if (accepts + rejects) > 0 else 0.0
        
        return {
            "alternative_ctr": MetricValue(
                metric_type=MetricType.CTR,
                value=ctr,
                user_id=user_id,
                agent="AlternativeAgent",
                time_window="weekly"
            ),
            "alternative_acceptance": MetricValue(
                metric_type=MetricType.ALTERNATIVE_ACCEPTANCE,
                value=acceptance_rate,
                user_id=user_id,
                agent="AlternativeAgent",
                time_window="weekly"
            )
        }
    
    # ========================================
    # Query Learning
    # ========================================
    
    async def analyze_query_patterns(
        self,
        time_window: timedelta = timedelta(days=30)
    ) -> List[QueryProductMapping]:
        """
        Analyze search→click patterns to learn query-product mappings.
        
        Returns:
            List of query patterns with their successful products
        """
        since = datetime.utcnow() - time_window
        
        # Get search and click interactions
        search_interactions = await self._logger.get_user_interactions(
            user_id="*",
            interaction_types=[InteractionType.SEARCH],
            limit=10000,
            since=since
        )
        
        click_interactions = await self._logger.get_user_interactions(
            user_id="*",
            interaction_types=[
                InteractionType.PRODUCT_CLICK,
                InteractionType.ADD_TO_CART,
                InteractionType.PURCHASE_COMPLETE
            ],
            limit=50000,
            since=since
        )
        
        # Build session-to-query mapping
        session_queries: Dict[str, str] = {}
        for interaction in search_interactions:
            if interaction.context.query:
                session_queries[interaction.context.session_id] = self._normalize_query(
                    interaction.context.query
                )
        
        # Map queries to successful products
        query_products: Dict[str, QueryProductMapping] = {}
        
        for interaction in click_interactions:
            session_id = interaction.context.session_id
            query = session_queries.get(session_id) or interaction.context.query
            
            if not query or not interaction.item_interacted:
                continue
            
            normalized = self._normalize_query(query)
            
            if normalized not in query_products:
                query_products[normalized] = QueryProductMapping(query_pattern=normalized)
            
            mapping = query_products[normalized]
            product_id = interaction.item_interacted
            
            if product_id not in mapping.product_ids:
                mapping.product_ids.append(product_id)
            
            # Update counts based on interaction type
            if interaction.interaction_type == InteractionType.PRODUCT_CLICK:
                mapping.click_count += 1
            elif interaction.interaction_type == InteractionType.ADD_TO_CART:
                mapping.cart_count += 1
            elif interaction.interaction_type == InteractionType.PURCHASE_COMPLETE:
                mapping.purchase_count += 1
            
            mapping.last_updated = datetime.utcnow()
            mapping.calculate_score()
        
        # Sort by success score and return top mappings
        mappings = list(query_products.values())
        mappings.sort(key=lambda m: m.success_score, reverse=True)
        
        # Cache for later use
        self._query_mappings = query_products
        
        return mappings[:1000]  # Top 1000 patterns
    
    async def analyze_alternative_effectiveness(
        self,
        time_window: timedelta = timedelta(days=30)
    ) -> List[AlternativeEffectiveness]:
        """
        Analyze which alternative product suggestions work best.
        
        Returns:
            List of alternative effectiveness records
        """
        since = datetime.utcnow() - time_window
        
        interactions = await self._logger.get_user_interactions(
            user_id="*",
            interaction_types=[
                InteractionType.ALTERNATIVE_VIEW,
                InteractionType.ALTERNATIVE_CLICK,
                InteractionType.ALTERNATIVE_ACCEPT,
                InteractionType.ALTERNATIVE_REJECT
            ],
            limit=10000,
            since=since
        )
        
        # Group by original→alternative pairs
        pairs: Dict[str, AlternativeEffectiveness] = {}
        
        for interaction in interactions:
            original_id = interaction.metadata.get("original_product_id")
            alternative_id = interaction.item_interacted
            
            if not original_id:
                continue
            
            for alt_id in interaction.alternatives_shown:
                pair_key = f"{original_id}:{alt_id}"
                
                if pair_key not in pairs:
                    pairs[pair_key] = AlternativeEffectiveness(
                        original_product_id=original_id,
                        alternative_product_id=alt_id
                    )
                
                eff = pairs[pair_key]
                eff.times_shown += 1
                
                if interaction.interaction_type == InteractionType.ALTERNATIVE_CLICK:
                    if interaction.item_interacted == alt_id:
                        eff.times_clicked += 1
                elif interaction.interaction_type == InteractionType.ALTERNATIVE_ACCEPT:
                    if interaction.item_interacted == alt_id:
                        eff.times_accepted += 1
                elif interaction.interaction_type == InteractionType.ALTERNATIVE_REJECT:
                    if interaction.item_interacted == alt_id:
                        eff.times_rejected += 1
                
                eff.update_metrics()
        
        # Cache and return
        self._alternative_effectiveness = pairs
        
        effectiveness = list(pairs.values())
        effectiveness.sort(key=lambda e: e.acceptance_rate, reverse=True)
        
        return effectiveness
    
    def _normalize_query(self, query: str) -> str:
        """Normalize a query for pattern matching."""
        # Simple normalization - in production, use more sophisticated NLP
        normalized = query.lower().strip()
        # Remove extra whitespace
        normalized = " ".join(normalized.split())
        return normalized
    
    # ========================================
    # Insight Generation
    # ========================================
    
    async def generate_insights(
        self,
        time_window: timedelta = timedelta(days=7)
    ) -> List[LearningInsight]:
        """
        Generate actionable insights from interaction analysis.
        
        Returns:
            List of insights for system improvement
        """
        insights = []
        
        # Get metrics
        funnel = await self.calculate_conversion_funnel(time_window=time_window)
        compliance = await self.calculate_constraint_compliance(time_window=time_window)
        rec_metrics = await self.calculate_recommendation_metrics(time_window=time_window)
        alt_metrics = await self.calculate_alternative_metrics(time_window=time_window)
        
        # Check for low CTR
        ctr_value = funnel["search_to_click"].value
        if ctr_value < 0.1:  # Less than 10% CTR
            insights.append(LearningInsight(
                insight_type="alert",
                title="Low Search Click-Through Rate",
                description=f"Search CTR is {ctr_value:.1%}, below the 10% threshold. "
                           "Search results may not be matching user intent.",
                severity="high",
                potential_impact="Users not finding relevant products from search",
                recommended_action="Review search ranking algorithm and improve query understanding",
                metrics=[funnel["search_to_click"]],
                auto_actionable=False
            ))
        
        # Check for budget constraint violations
        if compliance.value < 0.8:  # Less than 80% compliance
            insights.append(LearningInsight(
                insight_type="alert",
                title="High Budget Constraint Violations",
                description=f"Only {compliance.value:.1%} of interactions respect budget constraints. "
                           "Users are frequently clicking on items above their stated budget.",
                severity="medium",
                potential_impact="User frustration and lower conversion",
                recommended_action="Adjust constraint strictness or improve budget-aware filtering",
                metrics=[compliance],
                auto_actionable=True
            ))
        
        # Check recommendation performance
        rec_ctr = rec_metrics["recommendation_ctr"].value
        if rec_ctr < 0.05:  # Less than 5% CTR
            insights.append(LearningInsight(
                insight_type="recommendation",
                title="Underperforming Recommendations",
                description=f"Recommendation CTR is {rec_ctr:.1%}. "
                           "Personalization may need improvement.",
                severity="medium",
                potential_impact="Missed cross-sell opportunities",
                recommended_action="Consider A/B testing different recommendation strategies",
                metrics=[rec_metrics["recommendation_ctr"]],
                auto_actionable=False
            ))
        
        # Check alternative acceptance
        alt_acceptance = alt_metrics["alternative_acceptance"].value
        if alt_acceptance < 0.2:  # Less than 20% acceptance
            insights.append(LearningInsight(
                insight_type="observation",
                title="Low Alternative Acceptance Rate",
                description=f"Only {alt_acceptance:.1%} of alternatives are accepted. "
                           "Alternative suggestions may not be meeting user needs.",
                severity="low",
                potential_impact="Missed opportunity to serve budget-conscious users",
                recommended_action="Improve alternative selection algorithm",
                metrics=[alt_metrics["alternative_acceptance"]],
                auto_actionable=False
            ))
        
        # Check for conversion drop-offs
        cart_to_purchase = funnel["cart_to_purchase"].value
        if cart_to_purchase < 0.3:  # Less than 30% complete purchase
            insights.append(LearningInsight(
                insight_type="alert",
                title="High Cart Abandonment",
                description=f"Cart to purchase rate is {cart_to_purchase:.1%}. "
                           "Many users are abandoning their carts.",
                severity="high",
                potential_impact="Significant revenue loss from abandoned carts",
                recommended_action="Investigate checkout friction and implement cart recovery",
                metrics=[funnel["cart_to_purchase"]],
                auto_actionable=False
            ))
        
        # Positive insights
        overall_conversion = funnel["overall_conversion"].value
        if overall_conversion > 0.05:  # Greater than 5% overall conversion
            insights.append(LearningInsight(
                insight_type="trend",
                title="Strong Overall Conversion",
                description=f"Overall conversion rate is {overall_conversion:.1%}, "
                           "indicating good product-market fit.",
                severity="info",
                metrics=[funnel["overall_conversion"]]
            ))
        
        return insights
    
    async def analyze_user_behavior(
        self,
        user_id: str,
        time_window: timedelta = timedelta(days=30)
    ) -> Dict[str, Any]:
        """
        Analyze a specific user's behavior patterns.
        
        Returns comprehensive analysis for personalizing their experience.
        """
        interactions = await self._logger.get_user_interactions(
            user_id=user_id,
            limit=1000,
            since=datetime.utcnow() - time_window
        )
        
        if not interactions:
            return {"user_id": user_id, "has_data": False}
        
        # Analyze behavior
        analysis = {
            "user_id": user_id,
            "has_data": True,
            "interaction_count": len(interactions),
            "time_window_days": time_window.days
        }
        
        # Budget behavior
        purchases_with_budget = [
            i for i in interactions 
            if i.interaction_type == InteractionType.PURCHASE_COMPLETE
            and i.context.budget_max is not None
        ]
        
        if purchases_with_budget:
            prices = [i.item_price for i in purchases_with_budget if i.item_price]
            budgets = [i.context.budget_max for i in purchases_with_budget if i.context.budget_max]
            
            if prices and budgets:
                analysis["budget_behavior"] = {
                    "avg_purchase_price": statistics.mean(prices),
                    "max_purchase_price": max(prices),
                    "avg_stated_budget": statistics.mean(budgets),
                    "budget_utilization": statistics.mean(prices) / statistics.mean(budgets),
                    "times_exceeded_budget": sum(1 for i in purchases_with_budget if i.budget_exceeded)
                }
        
        # Search patterns
        searches = [i for i in interactions if i.interaction_type in [
            InteractionType.SEARCH, InteractionType.VOICE_SEARCH, InteractionType.IMAGE_SEARCH
        ]]
        
        if searches:
            search_types = [i.interaction_type.value for i in searches]
            analysis["search_patterns"] = {
                "total_searches": len(searches),
                "preferred_type": max(set(search_types), key=search_types.count),
                "queries": [i.context.query for i in searches if i.context.query][:20]
            }
        
        # Engagement metrics
        clicks = [i for i in interactions if "click" in i.interaction_type.value]
        carts = [i for i in interactions if i.interaction_type == InteractionType.ADD_TO_CART]
        purchases = [i for i in interactions if i.interaction_type == InteractionType.PURCHASE_COMPLETE]
        
        analysis["engagement"] = {
            "total_clicks": len(clicks),
            "total_carts": len(carts),
            "total_purchases": len(purchases),
            "view_to_cart_rate": len(carts) / len(clicks) if clicks else 0,
            "cart_to_purchase_rate": len(purchases) / len(carts) if carts else 0
        }
        
        # Category preferences (from clicked/purchased items)
        # Note: Would need product data to get categories
        analysis["category_affinity"] = {}  # Placeholder
        
        return analysis


# Singleton instance
_feedback_analyzer: Optional[FeedbackAnalyzer] = None


def get_feedback_analyzer() -> FeedbackAnalyzer:
    """Get the singleton feedback analyzer instance."""
    global _feedback_analyzer
    if _feedback_analyzer is None:
        _feedback_analyzer = FeedbackAnalyzer()
    return _feedback_analyzer
