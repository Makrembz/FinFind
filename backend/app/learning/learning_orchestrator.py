"""
Learning Orchestrator for FinFind.

Coordinates all learning components and manages the feedback loop
for continuous improvement.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from .models import (
    InteractionType,
    InteractionContext,
    UserLearningProfile,
    LearningInsight
)
from .interaction_logger import InteractionLogger, get_interaction_logger
from .feedback_analyzer import FeedbackAnalyzer, get_feedback_analyzer
from .model_updater import ModelUpdater, get_model_updater
from .ab_testing import ABTestingFramework, get_ab_testing
from .metrics_service import MetricsService, get_metrics_service

logger = logging.getLogger(__name__)


@dataclass
class LearningConfig:
    """Configuration for the learning system."""
    
    # Update intervals
    profile_update_interval: timedelta = timedelta(hours=1)
    ranking_update_interval: timedelta = timedelta(hours=6)
    query_mapping_interval: timedelta = timedelta(hours=24)
    insight_generation_interval: timedelta = timedelta(hours=4)
    
    # Learning parameters
    learning_rate: float = 0.1
    diversity_factor: float = 0.2
    min_interactions_for_learning: int = 10
    
    # Data retention
    interaction_retention_days: int = 90
    metric_retention_days: int = 365
    
    # Feature flags
    enable_profile_learning: bool = True
    enable_ranking_learning: bool = True
    enable_query_learning: bool = True
    enable_ab_testing: bool = True
    enable_auto_insights: bool = True


class LearningOrchestrator:
    """
    Central coordinator for the FinFind learning system.
    
    Manages:
    - Interaction logging and tracking
    - Periodic feedback analysis
    - Model updates based on feedback
    - A/B testing coordination
    - Metrics and monitoring
    - Background learning tasks
    """
    
    def __init__(self, config: Optional[LearningConfig] = None):
        """
        Initialize the learning orchestrator.
        
        Args:
            config: Learning configuration
        """
        self._config = config or LearningConfig()
        
        # Initialize components
        self._interaction_logger = get_interaction_logger()
        self._feedback_analyzer = get_feedback_analyzer()
        self._model_updater = get_model_updater()
        self._ab_testing = get_ab_testing()
        self._metrics_service = get_metrics_service()
        
        # Set learning parameters
        self._model_updater.set_learning_rate(self._config.learning_rate)
        self._model_updater.set_diversity_factor(self._config.diversity_factor)
        
        # Background task handles
        self._background_tasks: List[asyncio.Task] = []
        self._running = False
        
        # Last update timestamps
        self._last_profile_update: Optional[datetime] = None
        self._last_ranking_update: Optional[datetime] = None
        self._last_query_update: Optional[datetime] = None
        self._last_insight_generation: Optional[datetime] = None
        
        # Active users for updates
        self._active_users: set = set()
    
    # ========================================
    # Lifecycle Management
    # ========================================
    
    async def start(self):
        """Start the learning system with background tasks."""
        if self._running:
            logger.warning("Learning orchestrator already running")
            return
        
        self._running = True
        
        # Start interaction logger
        await self._interaction_logger.start()
        
        # Start background learning tasks
        if self._config.enable_profile_learning:
            self._background_tasks.append(
                asyncio.create_task(self._profile_update_loop())
            )
        
        if self._config.enable_ranking_learning:
            self._background_tasks.append(
                asyncio.create_task(self._ranking_update_loop())
            )
        
        if self._config.enable_query_learning:
            self._background_tasks.append(
                asyncio.create_task(self._query_mapping_loop())
            )
        
        if self._config.enable_auto_insights:
            self._background_tasks.append(
                asyncio.create_task(self._insight_generation_loop())
            )
        
        logger.info("Learning orchestrator started with background tasks")
    
    async def stop(self):
        """Stop the learning system gracefully."""
        self._running = False
        
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        self._background_tasks.clear()
        
        # Stop interaction logger
        await self._interaction_logger.stop()
        
        logger.info("Learning orchestrator stopped")
    
    # ========================================
    # Interaction Tracking
    # ========================================
    
    async def track_search(
        self,
        user_id: str,
        session_id: str,
        query: str,
        results: List[str],
        search_type: str = "text",
        agent_used: Optional[str] = None,
        budget_max: Optional[float] = None
    ) -> str:
        """Track a search interaction."""
        # Get A/B test variant if any active experiments
        ab_variant = None
        if self._config.enable_ab_testing:
            for exp in self._ab_testing.get_active_experiments_for_component("SearchAgent"):
                ab_variant = self._ab_testing.assign_variant(user_id, exp.id)
                self._ab_testing.record_impression(exp.id, ab_variant)
        
        interaction_id = await self._interaction_logger.log_search(
            user_id=user_id,
            session_id=session_id,
            query=query,
            results=results,
            search_type=search_type,
            agent_used=agent_used,
            budget_max=budget_max,
            ab_variant=ab_variant
        )
        
        self._active_users.add(user_id)
        return interaction_id
    
    async def track_product_click(
        self,
        user_id: str,
        session_id: str,
        product_id: str,
        position: int,
        items_shown: List[str],
        item_price: Optional[float] = None,
        budget_max: Optional[float] = None,
        source: str = "search"
    ) -> str:
        """Track a product click."""
        interaction_id = await self._interaction_logger.log_product_click(
            user_id=user_id,
            session_id=session_id,
            product_id=product_id,
            position=position,
            items_shown=items_shown,
            item_price=item_price,
            budget_max=budget_max,
            source=source
        )
        
        # Record conversion for A/B tests
        if self._config.enable_ab_testing:
            for exp in self._ab_testing.get_active_experiments_for_component("SearchAgent"):
                self._ab_testing.record_interaction(
                    user_id=user_id,
                    experiment_id=exp.id,
                    is_conversion=False
                )
        
        self._active_users.add(user_id)
        return interaction_id
    
    async def track_recommendation(
        self,
        user_id: str,
        session_id: str,
        recommendations_shown: List[str],
        clicked_product: Optional[str] = None,
        position: Optional[int] = None,
        item_price: Optional[float] = None,
        dismissed: bool = False
    ) -> str:
        """Track recommendation view/click/dismiss."""
        return await self._interaction_logger.log_recommendation_interaction(
            user_id=user_id,
            session_id=session_id,
            recommendations_shown=recommendations_shown,
            clicked_product=clicked_product,
            position=position,
            item_price=item_price,
            dismissed=dismissed
        )
    
    async def track_alternative(
        self,
        user_id: str,
        session_id: str,
        original_product_id: str,
        alternatives_shown: List[str],
        alternative_clicked: Optional[str] = None,
        alternative_accepted: bool = False,
        item_price: Optional[float] = None,
        budget_max: Optional[float] = None
    ) -> str:
        """Track alternative product interaction."""
        return await self._interaction_logger.log_alternative_interaction(
            user_id=user_id,
            session_id=session_id,
            original_product_id=original_product_id,
            alternatives_shown=alternatives_shown,
            alternative_clicked=alternative_clicked,
            alternative_accepted=alternative_accepted,
            item_price=item_price,
            budget_max=budget_max
        )
    
    async def track_cart_action(
        self,
        user_id: str,
        session_id: str,
        product_id: str,
        action: str,
        item_price: Optional[float] = None,
        budget_max: Optional[float] = None,
        source: str = "search"
    ) -> str:
        """Track add/remove cart action."""
        return await self._interaction_logger.log_cart_action(
            user_id=user_id,
            session_id=session_id,
            product_id=product_id,
            action=action,
            item_price=item_price,
            budget_max=budget_max,
            source=source
        )
    
    async def track_purchase(
        self,
        user_id: str,
        session_id: str,
        products: List[Dict[str, Any]],
        total_amount: float,
        budget_max: Optional[float] = None
    ) -> str:
        """Track purchase completion."""
        interaction_id = await self._interaction_logger.log_purchase(
            user_id=user_id,
            session_id=session_id,
            products=products,
            total_amount=total_amount,
            budget_max=budget_max
        )
        
        # Record conversion for A/B tests
        if self._config.enable_ab_testing:
            for exp in self._ab_testing.list_experiments(status="running"):
                variant = self._ab_testing.get_user_variant(user_id, exp["id"])
                if variant:
                    self._ab_testing.record_conversion(
                        experiment_id=exp["id"],
                        variant_id=variant,
                        revenue=total_amount
                    )
        
        self._active_users.add(user_id)
        return interaction_id
    
    async def track_explanation_feedback(
        self,
        user_id: str,
        session_id: str,
        product_id: str,
        helpful: bool
    ) -> str:
        """Track feedback on explanations."""
        return await self._interaction_logger.log_explanation_feedback(
            user_id=user_id,
            session_id=session_id,
            product_id=product_id,
            helpful=helpful
        )
    
    # ========================================
    # Learning Queries
    # ========================================
    
    async def get_user_profile(
        self,
        user_id: str
    ) -> Optional[UserLearningProfile]:
        """Get a user's learning profile."""
        profile = self._model_updater.get_user_profile(user_id)
        
        if not profile:
            # Try to build from history
            profile = await self._model_updater.update_user_profile(user_id)
        
        return profile
    
    def get_affordability_adjustment(
        self,
        user_id: str,
        category: Optional[str] = None
    ) -> float:
        """Get affordability score adjustment for user."""
        return self._model_updater.get_affordability_adjustment(user_id, category)
    
    def get_ranking_adjustment(
        self,
        product_id: str
    ) -> float:
        """Get ranking adjustment for a product."""
        return self._model_updater.get_ranking_adjustment(product_id)
    
    def get_query_products(
        self,
        query: str,
        limit: int = 10
    ) -> List[str]:
        """Get learned product IDs for a query."""
        return self._model_updater.get_query_products(query, limit)
    
    # ========================================
    # A/B Testing
    # ========================================
    
    def get_ab_variant(
        self,
        user_id: str,
        component: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get A/B test configuration for a user/component.
        
        Returns variant config if user is in an active experiment.
        """
        if not self._config.enable_ab_testing:
            return None
        
        for exp in self._ab_testing.get_active_experiments_for_component(component):
            variant_id = self._ab_testing.assign_variant(user_id, exp.id)
            return {
                "experiment_id": exp.id,
                "variant": variant_id,
                "config": self._ab_testing.get_variant_config(user_id, exp.id)
            }
        
        return None
    
    def create_experiment(
        self,
        name: str,
        description: str,
        test_type: str,
        target_component: str,
        control_config: Dict[str, Any],
        treatment_config: Dict[str, Any],
        traffic_split: float = 50.0
    ) -> str:
        """Create a new A/B test experiment."""
        experiment = self._ab_testing.create_experiment(
            name=name,
            description=description,
            test_type=test_type,
            target_component=target_component,
            control_config=control_config,
            treatment_config=treatment_config,
            traffic_split=traffic_split
        )
        return experiment.id
    
    def start_experiment(self, experiment_id: str) -> bool:
        """Start an A/B test experiment."""
        return self._ab_testing.start_experiment(experiment_id)
    
    def analyze_experiment(self, experiment_id: str) -> Dict[str, Any]:
        """Analyze A/B test results."""
        return self._ab_testing.analyze_experiment(experiment_id)
    
    # ========================================
    # Metrics and Dashboard
    # ========================================
    
    async def get_dashboard(self) -> Dict[str, Any]:
        """Get learning system dashboard data."""
        dashboard = await self._metrics_service.get_dashboard_data()
        
        # Add learning-specific stats
        dashboard_dict = dashboard.to_dict()
        dashboard_dict["learning_stats"] = {
            "active_users": len(self._active_users),
            "interaction_logger_stats": self._interaction_logger.get_stats(),
            "last_profile_update": self._last_profile_update.isoformat() if self._last_profile_update else None,
            "last_ranking_update": self._last_ranking_update.isoformat() if self._last_ranking_update else None,
            "profiles_cached": len(self._model_updater._profiles),
            "query_mappings_cached": len(self._model_updater._query_mappings)
        }
        
        return dashboard_dict
    
    async def get_kpi_summary(self) -> Dict[str, Any]:
        """Get KPI summary."""
        return await self._metrics_service.get_kpi_summary()
    
    async def get_insights(self) -> List[LearningInsight]:
        """Get current learning insights."""
        return await self._feedback_analyzer.generate_insights()
    
    # ========================================
    # Manual Triggers
    # ========================================
    
    async def trigger_profile_update(
        self,
        user_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Manually trigger profile updates."""
        users = user_ids or list(self._active_users)
        
        result = await self._model_updater.run_batch_update(
            user_ids=users,
            update_rankings=False,
            update_queries=False
        )
        
        self._last_profile_update = datetime.utcnow()
        return result
    
    async def trigger_ranking_update(self) -> Dict[str, Any]:
        """Manually trigger ranking updates."""
        result = await self._model_updater.run_batch_update(
            update_rankings=True,
            update_queries=False
        )
        
        self._last_ranking_update = datetime.utcnow()
        return result
    
    async def trigger_query_update(self) -> Dict[str, Any]:
        """Manually trigger query mapping updates."""
        result = await self._model_updater.run_batch_update(
            update_rankings=False,
            update_queries=True
        )
        
        self._last_query_update = datetime.utcnow()
        return result
    
    # ========================================
    # Background Learning Loops
    # ========================================
    
    async def _profile_update_loop(self):
        """Background loop for updating user profiles."""
        while self._running:
            await asyncio.sleep(self._config.profile_update_interval.total_seconds())
            
            try:
                users = list(self._active_users)
                if users:
                    logger.info(f"Updating profiles for {len(users)} active users")
                    await self._model_updater.run_batch_update(
                        user_ids=users[:100],  # Batch limit
                        update_rankings=False,
                        update_queries=False
                    )
                    self._last_profile_update = datetime.utcnow()
                    
                    # Clear processed users
                    for user in users[:100]:
                        self._active_users.discard(user)
                        
            except Exception as e:
                logger.error(f"Profile update error: {e}")
    
    async def _ranking_update_loop(self):
        """Background loop for updating product rankings."""
        while self._running:
            await asyncio.sleep(self._config.ranking_update_interval.total_seconds())
            
            try:
                logger.info("Updating product rankings")
                await self._model_updater.update_product_rankings()
                self._last_ranking_update = datetime.utcnow()
            except Exception as e:
                logger.error(f"Ranking update error: {e}")
    
    async def _query_mapping_loop(self):
        """Background loop for updating query mappings."""
        while self._running:
            await asyncio.sleep(self._config.query_mapping_interval.total_seconds())
            
            try:
                logger.info("Updating query mappings")
                await self._model_updater.update_query_mappings()
                self._last_query_update = datetime.utcnow()
            except Exception as e:
                logger.error(f"Query mapping update error: {e}")
    
    async def _insight_generation_loop(self):
        """Background loop for generating insights."""
        while self._running:
            await asyncio.sleep(self._config.insight_generation_interval.total_seconds())
            
            try:
                logger.info("Generating learning insights")
                insights = await self._feedback_analyzer.generate_insights()
                self._last_insight_generation = datetime.utcnow()
                
                # Log high-severity insights
                for insight in insights:
                    if insight.severity in ["high", "critical"]:
                        logger.warning(f"Learning insight: {insight.title} - {insight.description}")
                        
            except Exception as e:
                logger.error(f"Insight generation error: {e}")
    
    # ========================================
    # Status
    # ========================================
    
    def get_status(self) -> Dict[str, Any]:
        """Get learning system status."""
        return {
            "running": self._running,
            "config": {
                "learning_rate": self._config.learning_rate,
                "diversity_factor": self._config.diversity_factor,
                "profile_learning_enabled": self._config.enable_profile_learning,
                "ranking_learning_enabled": self._config.enable_ranking_learning,
                "query_learning_enabled": self._config.enable_query_learning,
                "ab_testing_enabled": self._config.enable_ab_testing
            },
            "active_users": len(self._active_users),
            "background_tasks": len(self._background_tasks),
            "last_updates": {
                "profile": self._last_profile_update.isoformat() if self._last_profile_update else None,
                "ranking": self._last_ranking_update.isoformat() if self._last_ranking_update else None,
                "query_mapping": self._last_query_update.isoformat() if self._last_query_update else None,
                "insights": self._last_insight_generation.isoformat() if self._last_insight_generation else None
            },
            "caches": {
                "profiles": len(self._model_updater._profiles),
                "query_mappings": len(self._model_updater._query_mappings),
                "ranking_adjustments": len(self._model_updater._ranking_adjustments)
            },
            "active_experiments": len(self._ab_testing.list_experiments(status="running")),
            "interaction_logger": self._interaction_logger.get_stats()
        }


# Singleton instance
_learning_orchestrator: Optional[LearningOrchestrator] = None


def get_learning_orchestrator() -> LearningOrchestrator:
    """Get the singleton learning orchestrator instance."""
    global _learning_orchestrator
    if _learning_orchestrator is None:
        _learning_orchestrator = LearningOrchestrator()
    return _learning_orchestrator
