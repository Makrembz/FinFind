"""
Model Updater for FinFind Learning System.

Updates user profiles, affordability scores, and rankings
based on analyzed feedback. Implements incremental learning
while maintaining diversity.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import statistics
import math

from .models import (
    Interaction,
    InteractionType,
    FeedbackSignal,
    UserLearningProfile,
    QueryProductMapping
)
from .interaction_logger import InteractionLogger, get_interaction_logger
from .feedback_analyzer import FeedbackAnalyzer, get_feedback_analyzer

logger = logging.getLogger(__name__)


class ModelUpdater:
    """
    Updates models based on user feedback for continuous improvement.
    
    Responsibilities:
    - Update user learning profiles
    - Refine affordability scores
    - Adjust product rankings
    - Update query interpretation mappings
    - Maintain diversity to avoid over-personalization
    """
    
    # Learning rate controls how fast models adapt (0-1)
    DEFAULT_LEARNING_RATE = 0.1
    
    # Diversity factor prevents over-specialization (0-1)
    DEFAULT_DIVERSITY_FACTOR = 0.2
    
    # Minimum interactions before updating profile
    MIN_INTERACTIONS_FOR_UPDATE = 5
    
    # Decay factor for old data (exponential decay)
    TIME_DECAY_FACTOR = 0.95  # Per week
    
    def __init__(
        self,
        interaction_logger: Optional[InteractionLogger] = None,
        feedback_analyzer: Optional[FeedbackAnalyzer] = None,
        learning_rate: float = DEFAULT_LEARNING_RATE,
        diversity_factor: float = DEFAULT_DIVERSITY_FACTOR
    ):
        """
        Initialize the model updater.
        
        Args:
            interaction_logger: Logger for fetching interactions
            feedback_analyzer: Analyzer for computing metrics
            learning_rate: How quickly to adapt (0-1)
            diversity_factor: How much diversity to maintain (0-1)
        """
        self._logger = interaction_logger or get_interaction_logger()
        self._analyzer = feedback_analyzer or get_feedback_analyzer()
        self._learning_rate = learning_rate
        self._diversity_factor = diversity_factor
        
        # Profile cache
        self._profiles: Dict[str, UserLearningProfile] = {}
        
        # Query mappings cache
        self._query_mappings: Dict[str, QueryProductMapping] = {}
        
        # Product ranking adjustments
        self._ranking_adjustments: Dict[str, float] = {}
        
        # Affordability score adjustments per user
        self._affordability_adjustments: Dict[str, Dict[str, float]] = {}
    
    # ========================================
    # User Profile Updates
    # ========================================
    
    async def update_user_profile(
        self,
        user_id: str,
        time_window: timedelta = timedelta(days=30)
    ) -> UserLearningProfile:
        """
        Update or create a user's learning profile based on interactions.
        
        Args:
            user_id: User to update
            time_window: How far back to look
            
        Returns:
            Updated UserLearningProfile
        """
        # Get or create profile
        profile = self._profiles.get(user_id) or UserLearningProfile(user_id=user_id)
        
        # Fetch user's interactions
        interactions = await self._logger.get_user_interactions(
            user_id=user_id,
            limit=5000,
            since=datetime.utcnow() - time_window
        )
        
        if len(interactions) < self.MIN_INTERACTIONS_FOR_UPDATE:
            logger.debug(f"Not enough interactions for user {user_id}")
            return profile
        
        # Update interaction count
        profile.interaction_count = len(interactions)
        profile.updated_at = datetime.utcnow()
        
        # Update budget behavior
        await self._update_budget_behavior(profile, interactions)
        
        # Update preferences
        await self._update_preferences(profile, interactions)
        
        # Update engagement metrics
        await self._update_engagement_metrics(profile, interactions)
        
        # Update conversion metrics
        await self._update_conversion_metrics(profile, interactions)
        
        # Store updated profile
        self._profiles[user_id] = profile
        
        logger.info(f"Updated learning profile for user {user_id}")
        return profile
    
    async def _update_budget_behavior(
        self,
        profile: UserLearningProfile,
        interactions: List[Interaction]
    ):
        """Update learned budget behavior from purchase history."""
        
        # Get purchase interactions with price data
        purchases = [
            i for i in interactions
            if i.interaction_type == InteractionType.PURCHASE_COMPLETE
            and i.item_price is not None
        ]
        
        if not purchases:
            return
        
        prices = [p.item_price for p in purchases]
        budgets = [p.context.budget_max for p in purchases if p.context.budget_max]
        
        # Update purchase statistics
        old_avg = profile.actual_purchase_avg or 0
        new_avg = statistics.mean(prices)
        profile.actual_purchase_avg = self._blend(old_avg, new_avg)
        
        old_max = profile.actual_purchase_max or 0
        new_max = max(prices)
        profile.actual_purchase_max = max(old_max, new_max)
        
        # Update stated budget
        if budgets:
            profile.stated_budget_max = statistics.mean(budgets)
        
        # Calculate budget flexibility
        if budgets and profile.stated_budget_max and profile.actual_purchase_avg:
            # Positive = user spends more than budget (flexible)
            # Negative = user spends less than budget (strict)
            flexibility = (
                (profile.actual_purchase_avg - profile.stated_budget_max) / 
                profile.stated_budget_max
            )
            # Clamp to [-1, 1]
            profile.learned_budget_flexibility = max(-1.0, min(1.0, flexibility))
        
        # Track categories where budget is stretched
        budget_exceeded = [
            i for i in purchases if i.budget_exceeded
        ]
        # Note: Would need product data to get categories
        # For now, just track overall budget flexibility
    
    async def _update_preferences(
        self,
        profile: UserLearningProfile,
        interactions: List[Interaction]
    ):
        """Update category and provider preferences from click/purchase patterns."""
        
        # Weight interactions by strength
        weights = {
            InteractionType.PURCHASE_COMPLETE: 10.0,
            InteractionType.ADD_TO_CART: 5.0,
            InteractionType.PRODUCT_CLICK: 2.0,
            InteractionType.RECOMMENDATION_CLICK: 2.0,
            InteractionType.ALTERNATIVE_ACCEPT: 3.0,
            InteractionType.PRODUCT_VIEW: 0.5
        }
        
        positive_interactions = [
            (i, weights.get(i.interaction_type, 1.0))
            for i in interactions
            if i.feedback_signal in [FeedbackSignal.POSITIVE, FeedbackSignal.IMPLICIT_POSITIVE]
        ]
        
        negative_interactions = [
            (i, -weights.get(i.interaction_type, 1.0) * 0.5)  # Half weight for negative
            for i in interactions
            if i.feedback_signal == FeedbackSignal.NEGATIVE
        ]
        
        # Note: In production, fetch product categories from Qdrant
        # For now, track by product IDs (would be replaced with categories)
        product_scores: Dict[str, float] = defaultdict(float)
        
        for interaction, weight in positive_interactions + negative_interactions:
            if interaction.item_interacted:
                # Apply time decay
                age_days = (datetime.utcnow() - interaction.timestamp).days
                age_weeks = age_days / 7
                decay = self.TIME_DECAY_FACTOR ** age_weeks
                
                product_scores[interaction.item_interacted] += weight * decay
        
        # Update preferred categories (placeholder - would map products to categories)
        # profile.preferred_categories = ...
    
    async def _update_engagement_metrics(
        self,
        profile: UserLearningProfile,
        interactions: List[Interaction]
    ):
        """Update session and engagement metrics."""
        
        # Group by session
        sessions: Dict[str, List[Interaction]] = defaultdict(list)
        for interaction in interactions:
            sessions[interaction.context.session_id].append(interaction)
        
        if not sessions:
            return
        
        # Calculate session metrics
        session_durations = []
        items_per_session = []
        search_refinements = []
        
        for session_id, session_interactions in sessions.items():
            # Session duration
            timestamps = [i.timestamp for i in session_interactions]
            if len(timestamps) >= 2:
                duration = (max(timestamps) - min(timestamps)).total_seconds()
                session_durations.append(duration)
            
            # Items viewed per session
            views = sum(
                1 for i in session_interactions
                if i.interaction_type in [
                    InteractionType.PRODUCT_VIEW,
                    InteractionType.PRODUCT_CLICK
                ]
            )
            items_per_session.append(views)
            
            # Search refinements
            searches = sum(
                1 for i in session_interactions
                if i.interaction_type in [
                    InteractionType.SEARCH,
                    InteractionType.SEARCH_REFINEMENT
                ]
            )
            search_refinements.append(max(0, searches - 1))  # -1 for initial search
        
        # Blend with existing metrics
        if session_durations:
            profile.avg_session_duration = self._blend(
                profile.avg_session_duration,
                statistics.mean(session_durations)
            )
        
        if items_per_session:
            profile.avg_items_viewed = self._blend(
                profile.avg_items_viewed,
                statistics.mean(items_per_session)
            )
        
        if search_refinements:
            profile.avg_search_refinements = self._blend(
                profile.avg_search_refinements,
                statistics.mean(search_refinements)
            )
        
        # Determine preferred search type
        search_types = [
            i.interaction_type for i in interactions
            if i.interaction_type in [
                InteractionType.SEARCH,
                InteractionType.VOICE_SEARCH,
                InteractionType.IMAGE_SEARCH
            ]
        ]
        
        if search_types:
            type_counts = defaultdict(int)
            for st in search_types:
                type_counts[st] += 1
            
            most_common = max(type_counts, key=type_counts.get)
            profile.preferred_search_type = {
                InteractionType.SEARCH: "text",
                InteractionType.VOICE_SEARCH: "voice",
                InteractionType.IMAGE_SEARCH: "image"
            }.get(most_common, "text")
    
    async def _update_conversion_metrics(
        self,
        profile: UserLearningProfile,
        interactions: List[Interaction]
    ):
        """Update conversion and engagement rate metrics."""
        
        # Count by type
        views = sum(1 for i in interactions if i.interaction_type == InteractionType.PRODUCT_VIEW)
        clicks = sum(1 for i in interactions if i.interaction_type == InteractionType.PRODUCT_CLICK)
        carts = sum(1 for i in interactions if i.interaction_type == InteractionType.ADD_TO_CART)
        purchases = sum(1 for i in interactions if i.interaction_type == InteractionType.PURCHASE_COMPLETE)
        
        # Recommendation metrics
        rec_views = sum(1 for i in interactions if i.interaction_type == InteractionType.RECOMMENDATION_VIEW)
        rec_clicks = sum(1 for i in interactions if i.interaction_type == InteractionType.RECOMMENDATION_CLICK)
        
        # Alternative metrics
        alt_views = sum(1 for i in interactions if i.interaction_type == InteractionType.ALTERNATIVE_VIEW)
        alt_accepts = sum(1 for i in interactions if i.interaction_type == InteractionType.ALTERNATIVE_ACCEPT)
        
        # Explanation metrics
        exp_views = sum(1 for i in interactions if i.interaction_type == InteractionType.EXPLANATION_VIEW)
        exp_helpful = sum(1 for i in interactions if i.interaction_type == InteractionType.EXPLANATION_HELPFUL)
        
        # Update rates with blending
        total_views = views + clicks
        if total_views > 0:
            new_vtc = carts / total_views
            profile.view_to_cart_rate = self._blend(profile.view_to_cart_rate, new_vtc)
        
        if carts > 0:
            new_ctp = purchases / carts
            profile.cart_to_purchase_rate = self._blend(profile.cart_to_purchase_rate, new_ctp)
        
        if views > 0:
            new_conv = purchases / (views + clicks)
            profile.overall_conversion_rate = self._blend(profile.overall_conversion_rate, new_conv)
        
        if rec_views > 0:
            new_rec_ctr = rec_clicks / rec_views
            profile.recommendation_ctr = self._blend(profile.recommendation_ctr, new_rec_ctr)
        
        if alt_views > 0:
            new_alt_rate = alt_accepts / alt_views
            profile.alternative_acceptance_rate = self._blend(
                profile.alternative_acceptance_rate, new_alt_rate
            )
        
        if exp_views > 0:
            new_exp_rate = exp_helpful / exp_views
            profile.explanation_engagement_rate = self._blend(
                profile.explanation_engagement_rate, new_exp_rate
            )
        
        # Update constraint compliance
        with_budget = [i for i in interactions if i.context.budget_max is not None]
        if with_budget:
            compliant = sum(1 for i in with_budget if not i.budget_exceeded)
            new_compliance = compliant / len(with_budget)
            profile.constraint_compliance = self._blend(
                profile.constraint_compliance, new_compliance
            )
    
    # ========================================
    # Affordability Score Adjustments
    # ========================================
    
    async def update_affordability_scores(
        self,
        user_id: str
    ) -> Dict[str, float]:
        """
        Update affordability score adjustments for a user based on their
        actual purchase behavior vs stated constraints.
        
        Returns:
            Dict of category -> affordability adjustment factor
        """
        profile = self._profiles.get(user_id)
        
        if not profile:
            profile = await self.update_user_profile(user_id)
        
        adjustments = {}
        
        # Base adjustment from budget flexibility
        base_adjustment = profile.learned_budget_flexibility * 0.2  # ±20%
        
        # Categories where user stretches budget get positive adjustment
        for category in profile.budget_stretch_categories:
            adjustments[category] = base_adjustment + 0.1
        
        # Categories where user is strict get negative adjustment
        for category in profile.budget_strict_categories:
            adjustments[category] = base_adjustment - 0.1
        
        # Default adjustment for unknown categories
        adjustments["default"] = base_adjustment
        
        # Store for retrieval
        self._affordability_adjustments[user_id] = adjustments
        
        return adjustments
    
    def get_affordability_adjustment(
        self,
        user_id: str,
        category: Optional[str] = None
    ) -> float:
        """
        Get the affordability score adjustment for a user/category.
        
        Returns:
            Adjustment factor (-1 to 1) to apply to base affordability
        """
        adjustments = self._affordability_adjustments.get(user_id, {})
        
        if category and category in adjustments:
            return adjustments[category]
        
        return adjustments.get("default", 0.0)
    
    # ========================================
    # Product Ranking Updates
    # ========================================
    
    async def update_product_rankings(
        self,
        time_window: timedelta = timedelta(days=7)
    ) -> Dict[str, float]:
        """
        Update product ranking adjustments based on engagement.
        
        High-engagement products get positive adjustments.
        Implements diversity to avoid over-concentration.
        
        Returns:
            Dict of product_id -> ranking adjustment factor
        """
        # Analyze query patterns for successful products
        query_mappings = await self._analyzer.analyze_query_patterns(time_window)
        
        # Calculate engagement scores per product
        product_scores: Dict[str, float] = defaultdict(float)
        
        for mapping in query_mappings:
            for product_id in mapping.product_ids:
                product_scores[product_id] += mapping.success_score
        
        if not product_scores:
            return {}
        
        # Normalize scores
        max_score = max(product_scores.values())
        min_score = min(product_scores.values())
        score_range = max_score - min_score or 1.0
        
        for product_id in product_scores:
            # Normalize to [0, 1]
            normalized = (product_scores[product_id] - min_score) / score_range
            
            # Apply diversity factor to prevent over-concentration
            # High diversity factor = more uniform rankings
            adjustment = normalized * (1 - self._diversity_factor)
            
            # Scale to reasonable adjustment range (±0.3)
            self._ranking_adjustments[product_id] = (adjustment - 0.5) * 0.6
        
        logger.info(f"Updated rankings for {len(product_scores)} products")
        return self._ranking_adjustments
    
    def get_ranking_adjustment(self, product_id: str) -> float:
        """
        Get ranking adjustment for a product.
        
        Returns:
            Adjustment factor (-0.3 to 0.3) to add to base relevance score
        """
        return self._ranking_adjustments.get(product_id, 0.0)
    
    # ========================================
    # Query Understanding Updates
    # ========================================
    
    async def update_query_mappings(
        self,
        time_window: timedelta = timedelta(days=30)
    ) -> int:
        """
        Update query-to-product mappings for better search.
        
        Returns:
            Number of mappings updated
        """
        # Get fresh mappings from analyzer
        mappings = await self._analyzer.analyze_query_patterns(time_window)
        
        # Merge with existing, applying learning rate
        for mapping in mappings:
            existing = self._query_mappings.get(mapping.query_pattern)
            
            if existing:
                # Blend scores
                existing.success_score = self._blend(
                    existing.success_score,
                    mapping.success_score
                )
                
                # Merge product lists (keep top products)
                all_products = list(set(existing.product_ids + mapping.product_ids))
                existing.product_ids = all_products[:50]  # Keep top 50
                
                existing.click_count += mapping.click_count
                existing.cart_count += mapping.cart_count
                existing.purchase_count += mapping.purchase_count
                existing.last_updated = datetime.utcnow()
            else:
                self._query_mappings[mapping.query_pattern] = mapping
        
        logger.info(f"Updated {len(mappings)} query mappings")
        return len(mappings)
    
    def get_query_products(
        self,
        query: str,
        limit: int = 10
    ) -> List[str]:
        """
        Get learned product IDs for a query pattern.
        
        Returns:
            List of product IDs that historically worked well for similar queries
        """
        normalized = query.lower().strip()
        
        # Exact match
        mapping = self._query_mappings.get(normalized)
        if mapping:
            return mapping.product_ids[:limit]
        
        # Partial match (simple substring)
        matches = []
        for pattern, mapping in self._query_mappings.items():
            if normalized in pattern or pattern in normalized:
                matches.append((mapping.success_score, mapping.product_ids))
        
        if matches:
            # Sort by score and flatten
            matches.sort(key=lambda x: x[0], reverse=True)
            products = []
            for _, pids in matches:
                for pid in pids:
                    if pid not in products:
                        products.append(pid)
                    if len(products) >= limit:
                        return products
            return products
        
        return []
    
    # ========================================
    # Batch Updates
    # ========================================
    
    async def run_batch_update(
        self,
        user_ids: Optional[List[str]] = None,
        update_rankings: bool = True,
        update_queries: bool = True,
        time_window: timedelta = timedelta(days=30)
    ) -> Dict[str, Any]:
        """
        Run batch updates for multiple users and global models.
        
        Args:
            user_ids: Specific users to update (None = active users)
            update_rankings: Whether to update product rankings
            update_queries: Whether to update query mappings
            time_window: How far back to analyze
            
        Returns:
            Summary of updates performed
        """
        results = {
            "users_updated": 0,
            "rankings_updated": 0,
            "queries_updated": 0,
            "errors": []
        }
        
        # Update user profiles
        if user_ids:
            for user_id in user_ids:
                try:
                    await self.update_user_profile(user_id, time_window)
                    await self.update_affordability_scores(user_id)
                    results["users_updated"] += 1
                except Exception as e:
                    results["errors"].append(f"User {user_id}: {str(e)}")
        
        # Update product rankings
        if update_rankings:
            try:
                adjustments = await self.update_product_rankings(time_window)
                results["rankings_updated"] = len(adjustments)
            except Exception as e:
                results["errors"].append(f"Rankings: {str(e)}")
        
        # Update query mappings
        if update_queries:
            try:
                count = await self.update_query_mappings(time_window)
                results["queries_updated"] = count
            except Exception as e:
                results["errors"].append(f"Queries: {str(e)}")
        
        logger.info(f"Batch update complete: {results}")
        return results
    
    # ========================================
    # Helper Methods
    # ========================================
    
    def _blend(self, old_value: float, new_value: float) -> float:
        """Blend old and new values using learning rate."""
        if old_value == 0:
            return new_value
        return old_value * (1 - self._learning_rate) + new_value * self._learning_rate
    
    def get_user_profile(self, user_id: str) -> Optional[UserLearningProfile]:
        """Get cached user learning profile."""
        return self._profiles.get(user_id)
    
    def set_learning_rate(self, rate: float):
        """Set the learning rate (0-1)."""
        self._learning_rate = max(0.0, min(1.0, rate))
    
    def set_diversity_factor(self, factor: float):
        """Set the diversity factor (0-1)."""
        self._diversity_factor = max(0.0, min(1.0, factor))


# Singleton instance
_model_updater: Optional[ModelUpdater] = None


def get_model_updater() -> ModelUpdater:
    """Get the singleton model updater instance."""
    global _model_updater
    if _model_updater is None:
        _model_updater = ModelUpdater()
    return _model_updater
