"""
Tests for the FinFind Learning System.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from backend.app.learning.models import (
    InteractionType,
    Interaction,
    InteractionContext,
    FeedbackSignal,
    UserLearningProfile,
    ABTestExperiment,
    ABTestVariant,
    MetricType,
    MetricValue,
    LearningInsight,
    QueryProductMapping
)
from backend.app.learning.interaction_logger import InteractionLogger
from backend.app.learning.feedback_analyzer import FeedbackAnalyzer
from backend.app.learning.model_updater import ModelUpdater
from backend.app.learning.ab_testing import (
    ABTestingFramework,
    calculate_z_score,
    z_to_p_value,
    calculate_lift,
    required_sample_size
)
from backend.app.learning.metrics_service import MetricsService
from backend.app.learning.learning_orchestrator import LearningOrchestrator, LearningConfig


# ==============================================================================
# Model Tests
# ==============================================================================

class TestModels:
    """Tests for data models."""
    
    def test_interaction_type_values(self):
        """Test all interaction types have string values."""
        assert InteractionType.SEARCH.value == "search"
        assert InteractionType.PRODUCT_CLICK.value == "product_click"
        assert InteractionType.PURCHASE_COMPLETE.value == "purchase_complete"
    
    def test_interaction_context_to_dict(self):
        """Test InteractionContext serialization."""
        context = InteractionContext(
            user_id="user-123",
            session_id="session-456",
            budget_max=1000.0,
            query="savings account"
        )
        
        data = context.to_dict()
        
        assert data["user_id"] == "user-123"
        assert data["session_id"] == "session-456"
        assert data["budget_max"] == 1000.0
        assert data["query"] == "savings account"
    
    def test_interaction_to_dict(self):
        """Test Interaction serialization."""
        interaction = Interaction(
            interaction_type=InteractionType.PRODUCT_CLICK,
            context=InteractionContext(user_id="user-1", session_id="sess-1"),
            item_interacted="prod-123",
            position=2,
            budget_exceeded=True
        )
        
        data = interaction.to_dict()
        
        assert data["interaction_type"] == "product_click"
        assert data["item_interacted"] == "prod-123"
        assert data["position"] == 2
        assert data["budget_exceeded"] is True
    
    def test_interaction_from_dict(self):
        """Test Interaction deserialization."""
        data = {
            "id": "int-123",
            "interaction_type": "search",
            "context": {
                "user_id": "user-1",
                "session_id": "sess-1",
                "query": "credit card"
            },
            "items_shown": ["prod-1", "prod-2"],
            "feedback_signal": "positive"
        }
        
        interaction = Interaction.from_dict(data)
        
        assert interaction.id == "int-123"
        assert interaction.interaction_type == InteractionType.SEARCH
        assert interaction.context.query == "credit card"
        assert len(interaction.items_shown) == 2
    
    def test_user_learning_profile_to_dict(self):
        """Test UserLearningProfile serialization."""
        profile = UserLearningProfile(
            user_id="user-123",
            actual_purchase_avg=500.0,
            recommendation_ctr=0.15,
            preferred_search_type="voice"
        )
        
        data = profile.to_dict()
        
        assert data["user_id"] == "user-123"
        assert data["actual_purchase_avg"] == 500.0
        assert data["recommendation_ctr"] == 0.15
        assert data["preferred_search_type"] == "voice"
    
    def test_ab_test_variant_update_metrics(self):
        """Test ABTestVariant metric calculation."""
        variant = ABTestVariant(
            id="treatment",
            name="Treatment",
            description="New ranking",
            impressions=1000,
            conversions=50,
            total_revenue=5000.0
        )
        
        variant.update_metrics()
        
        assert variant.conversion_rate == 0.05
        assert variant.revenue_per_impression == 5.0
    
    def test_query_product_mapping_calculate_score(self):
        """Test QueryProductMapping score calculation."""
        mapping = QueryProductMapping(
            query_pattern="savings account",
            product_ids=["prod-1", "prod-2"],
            click_count=100,
            cart_count=20,
            purchase_count=5
        )
        
        mapping.calculate_score()
        
        # score = clicks*1 + carts*3 + purchases*10
        assert mapping.success_score == 100 + 60 + 50


# ==============================================================================
# Interaction Logger Tests
# ==============================================================================

class TestInteractionLogger:
    """Tests for InteractionLogger."""
    
    @pytest.fixture
    def logger(self):
        """Create a test logger."""
        return InteractionLogger(buffer_size=10, flush_interval_seconds=60.0)
    
    @pytest.mark.asyncio
    async def test_log_interaction_basic(self, logger):
        """Test basic interaction logging."""
        context = InteractionContext(
            user_id="user-1",
            session_id="sess-1"
        )
        
        interaction_id = await logger.log_interaction(
            interaction_type=InteractionType.SEARCH,
            context=context,
            items_shown=["prod-1", "prod-2", "prod-3"]
        )
        
        assert interaction_id is not None
        assert logger._total_logged == 1
    
    @pytest.mark.asyncio
    async def test_log_search(self, logger):
        """Test search logging."""
        interaction_id = await logger.log_search(
            user_id="user-1",
            session_id="sess-1",
            query="savings account",
            results=["prod-1", "prod-2"],
            search_type="text"
        )
        
        assert interaction_id is not None
    
    @pytest.mark.asyncio
    async def test_log_product_click(self, logger):
        """Test product click logging."""
        interaction_id = await logger.log_product_click(
            user_id="user-1",
            session_id="sess-1",
            product_id="prod-123",
            position=2,
            items_shown=["prod-1", "prod-123", "prod-3"],
            item_price=500.0,
            budget_max=400.0
        )
        
        assert interaction_id is not None
        # Should have detected budget exceeded
        assert logger._buffer[-1].budget_exceeded is True
    
    @pytest.mark.asyncio
    async def test_feedback_signal_derivation(self, logger):
        """Test that feedback signals are correctly derived."""
        # Positive signal for purchase
        context = InteractionContext(user_id="u1", session_id="s1")
        await logger.log_interaction(
            interaction_type=InteractionType.PURCHASE_COMPLETE,
            context=context
        )
        assert logger._buffer[-1].feedback_signal == FeedbackSignal.POSITIVE
        
        # Negative signal for dismissal
        await logger.log_interaction(
            interaction_type=InteractionType.RECOMMENDATION_DISMISS,
            context=context
        )
        assert logger._buffer[-1].feedback_signal == FeedbackSignal.NEGATIVE
        
        # Click at position 1 should be positive
        await logger.log_interaction(
            interaction_type=InteractionType.PRODUCT_CLICK,
            context=context,
            position=1
        )
        assert logger._buffer[-1].feedback_signal == FeedbackSignal.POSITIVE
    
    @pytest.mark.asyncio
    async def test_buffer_flush_on_size(self, logger):
        """Test that buffer flushes when full."""
        context = InteractionContext(user_id="u1", session_id="s1")
        
        # Log enough to trigger flush (buffer_size=10)
        for i in range(12):
            await logger.log_interaction(
                interaction_type=InteractionType.PAGE_VIEW,
                context=context
            )
        
        # Buffer should have been flushed
        assert len(logger._buffer) < 12
    
    def test_get_stats(self, logger):
        """Test stats reporting."""
        stats = logger.get_stats()
        
        assert "total_logged" in stats
        assert "total_flushed" in stats
        assert "buffer_size" in stats
        assert "running" in stats


# ==============================================================================
# Feedback Analyzer Tests
# ==============================================================================

class TestFeedbackAnalyzer:
    """Tests for FeedbackAnalyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create a test analyzer."""
        mock_logger = MagicMock()
        mock_logger.get_user_interactions = AsyncMock(return_value=[])
        return FeedbackAnalyzer(interaction_logger=mock_logger)
    
    @pytest.mark.asyncio
    async def test_calculate_ctr_empty(self, analyzer):
        """Test CTR calculation with no data."""
        result = await analyzer.calculate_ctr()
        
        assert result.metric_type == MetricType.CTR
        assert result.value == 0.0
    
    @pytest.mark.asyncio
    async def test_calculate_ctr_with_data(self, analyzer):
        """Test CTR calculation with data."""
        # Mock interactions
        interactions = [
            Interaction(
                interaction_type=InteractionType.SEARCH,
                context=InteractionContext(user_id="u1", session_id="s1")
            ),
            Interaction(
                interaction_type=InteractionType.SEARCH,
                context=InteractionContext(user_id="u1", session_id="s1")
            ),
            Interaction(
                interaction_type=InteractionType.PRODUCT_CLICK,
                context=InteractionContext(user_id="u1", session_id="s1")
            )
        ]
        
        analyzer._logger.get_user_interactions = AsyncMock(return_value=interactions)
        
        result = await analyzer.calculate_ctr()
        
        # 1 click / 2 searches = 0.5
        assert result.value == 0.5
    
    @pytest.mark.asyncio
    async def test_calculate_constraint_compliance(self, analyzer):
        """Test constraint compliance calculation."""
        interactions = [
            Interaction(
                interaction_type=InteractionType.PRODUCT_CLICK,
                context=InteractionContext(user_id="u1", session_id="s1", budget_max=100),
                budget_exceeded=False
            ),
            Interaction(
                interaction_type=InteractionType.PRODUCT_CLICK,
                context=InteractionContext(user_id="u1", session_id="s1", budget_max=100),
                budget_exceeded=True
            ),
            Interaction(
                interaction_type=InteractionType.PRODUCT_CLICK,
                context=InteractionContext(user_id="u1", session_id="s1", budget_max=100),
                budget_exceeded=False
            )
        ]
        
        analyzer._logger.get_user_interactions = AsyncMock(return_value=interactions)
        
        result = await analyzer.calculate_constraint_compliance()
        
        # 2 compliant / 3 total = 0.667
        assert round(result.value, 2) == 0.67
    
    def test_normalize_query(self, analyzer):
        """Test query normalization."""
        assert analyzer._normalize_query("  Savings Account  ") == "savings account"
        assert analyzer._normalize_query("CREDIT   CARD") == "credit card"
    
    @pytest.mark.asyncio
    async def test_generate_insights_low_ctr(self, analyzer):
        """Test insight generation for low CTR."""
        # Mock low metrics
        async def mock_funnel(*args, **kwargs):
            return {
                "search_to_click": MetricValue(metric_type=MetricType.CTR, value=0.05),
                "click_to_cart": MetricValue(metric_type=MetricType.CART_RATE, value=0.2),
                "cart_to_purchase": MetricValue(metric_type=MetricType.PURCHASE_RATE, value=0.5),
                "overall_conversion": MetricValue(metric_type=MetricType.CONVERSION_RATE, value=0.01)
            }
        
        analyzer.calculate_conversion_funnel = mock_funnel
        analyzer.calculate_constraint_compliance = AsyncMock(
            return_value=MetricValue(metric_type=MetricType.BUDGET_COMPLIANCE, value=0.9)
        )
        analyzer.calculate_recommendation_metrics = AsyncMock(return_value={
            "recommendation_ctr": MetricValue(metric_type=MetricType.RECOMMENDATION_CTR, value=0.1),
            "recommendation_dismiss_rate": MetricValue(metric_type=MetricType.BOUNCE_RATE, value=0.1),
            "recommendation_conversion": MetricValue(metric_type=MetricType.RECOMMENDATION_CONVERSION, value=0.05)
        })
        analyzer.calculate_alternative_metrics = AsyncMock(return_value={
            "alternative_ctr": MetricValue(metric_type=MetricType.CTR, value=0.1),
            "alternative_acceptance": MetricValue(metric_type=MetricType.ALTERNATIVE_ACCEPTANCE, value=0.3)
        })
        
        insights = await analyzer.generate_insights()
        
        # Should have insight about low CTR
        ctr_insights = [i for i in insights if "CTR" in i.title or "ctr" in i.title.lower()]
        assert len(ctr_insights) > 0


# ==============================================================================
# Model Updater Tests
# ==============================================================================

class TestModelUpdater:
    """Tests for ModelUpdater."""
    
    @pytest.fixture
    def updater(self):
        """Create a test updater."""
        mock_logger = MagicMock()
        mock_logger.get_user_interactions = AsyncMock(return_value=[])
        mock_analyzer = MagicMock()
        return ModelUpdater(
            interaction_logger=mock_logger,
            feedback_analyzer=mock_analyzer,
            learning_rate=0.2
        )
    
    def test_blend_values(self, updater):
        """Test value blending with learning rate."""
        # With learning rate 0.2:
        # new = old * 0.8 + new * 0.2
        result = updater._blend(100.0, 200.0)
        assert result == 100 * 0.8 + 200 * 0.2  # 120
    
    def test_blend_from_zero(self, updater):
        """Test blending when old value is zero."""
        result = updater._blend(0.0, 100.0)
        assert result == 100.0
    
    @pytest.mark.asyncio
    async def test_update_user_profile_insufficient_data(self, updater):
        """Test profile update with insufficient interactions."""
        # Default is empty list, which is < MIN_INTERACTIONS_FOR_UPDATE
        profile = await updater.update_user_profile("user-1")
        
        assert profile.user_id == "user-1"
        assert profile.interaction_count == 0
    
    @pytest.mark.asyncio
    async def test_update_user_profile_with_data(self, updater):
        """Test profile update with sufficient data."""
        # Create mock interactions
        interactions = []
        for i in range(20):
            interactions.append(Interaction(
                interaction_type=InteractionType.PRODUCT_CLICK,
                context=InteractionContext(
                    user_id="user-1",
                    session_id=f"sess-{i // 5}"
                ),
                item_interacted=f"prod-{i}",
                feedback_signal=FeedbackSignal.POSITIVE
            ))
        
        # Add some purchases
        interactions.append(Interaction(
            interaction_type=InteractionType.PURCHASE_COMPLETE,
            context=InteractionContext(
                user_id="user-1",
                session_id="sess-5",
                budget_max=1000
            ),
            item_price=800.0
        ))
        
        updater._logger.get_user_interactions = AsyncMock(return_value=interactions)
        
        profile = await updater.update_user_profile("user-1")
        
        assert profile.interaction_count == 21
        assert profile.actual_purchase_avg == 800.0
    
    def test_get_ranking_adjustment(self, updater):
        """Test ranking adjustment retrieval."""
        updater._ranking_adjustments["prod-123"] = 0.15
        
        assert updater.get_ranking_adjustment("prod-123") == 0.15
        assert updater.get_ranking_adjustment("unknown") == 0.0
    
    def test_get_query_products(self, updater):
        """Test query-product lookup."""
        updater._query_mappings["savings account"] = QueryProductMapping(
            query_pattern="savings account",
            product_ids=["prod-1", "prod-2", "prod-3"],
            success_score=100
        )
        
        products = updater.get_query_products("savings account", limit=2)
        
        assert len(products) == 2
        assert "prod-1" in products


# ==============================================================================
# A/B Testing Tests
# ==============================================================================

class TestABTesting:
    """Tests for A/B Testing Framework."""
    
    @pytest.fixture
    def framework(self):
        """Create a test framework."""
        return ABTestingFramework()
    
    def test_calculate_z_score(self):
        """Test Z-score calculation."""
        # Control: 100/1000 = 10%
        # Treatment: 120/1000 = 12%
        z = calculate_z_score(100, 1000, 120, 1000)
        
        # Should be positive (treatment > control)
        assert z > 0
    
    def test_calculate_lift(self):
        """Test lift calculation."""
        lift = calculate_lift(0.10, 0.12)
        assert lift == 20.0  # 20% improvement
        
        lift = calculate_lift(0.10, 0.08)
        assert lift == -20.0  # 20% decrease
    
    def test_required_sample_size(self):
        """Test sample size calculation."""
        n = required_sample_size(
            baseline_rate=0.10,
            minimum_detectable_effect=0.10  # 10% lift
        )
        
        # Should be reasonable number for detecting 10% lift
        assert 1000 < n < 20000
    
    def test_create_experiment(self, framework):
        """Test experiment creation."""
        experiment = framework.create_experiment(
            name="Test Ranking",
            description="Test new ranking weights",
            test_type="ranking",
            target_component="SearchAgent",
            control_config={"weight": 0.5},
            treatment_config={"weight": 0.7},
            traffic_split=50.0
        )
        
        assert experiment.name == "Test Ranking"
        assert experiment.status == "draft"
        assert experiment.control.traffic_percentage == 50.0
        assert experiment.treatment.traffic_percentage == 50.0
    
    def test_start_experiment(self, framework):
        """Test starting an experiment."""
        experiment = framework.create_experiment(
            name="Test",
            description="Test",
            test_type="ranking",
            target_component="SearchAgent",
            control_config={},
            treatment_config={}
        )
        
        assert framework.start_experiment(experiment.id)
        assert experiment.status == "running"
        assert experiment.start_date is not None
    
    def test_assign_variant_deterministic(self, framework):
        """Test that variant assignment is deterministic."""
        experiment = framework.create_experiment(
            name="Test",
            description="Test",
            test_type="ranking",
            target_component="SearchAgent",
            control_config={},
            treatment_config={},
            traffic_split=50.0
        )
        framework.start_experiment(experiment.id)
        
        # Same user should always get same variant
        variant1 = framework.assign_variant("user-123", experiment.id)
        variant2 = framework.assign_variant("user-123", experiment.id)
        
        assert variant1 == variant2
    
    def test_record_metrics(self, framework):
        """Test recording impressions and conversions."""
        experiment = framework.create_experiment(
            name="Test",
            description="Test",
            test_type="ranking",
            target_component="SearchAgent",
            control_config={},
            treatment_config={}
        )
        framework.start_experiment(experiment.id)
        
        framework.record_impression(experiment.id, "control")
        framework.record_impression(experiment.id, "control")
        framework.record_conversion(experiment.id, "control", revenue=100.0)
        
        assert experiment.control.impressions == 2
        assert experiment.control.conversions == 1
        assert experiment.control.total_revenue == 100.0
    
    def test_analyze_experiment(self, framework):
        """Test experiment analysis."""
        experiment = framework.create_experiment(
            name="Test",
            description="Test",
            test_type="ranking",
            target_component="SearchAgent",
            control_config={},
            treatment_config={},
            min_sample_size=10
        )
        framework.start_experiment(experiment.id)
        
        # Add data
        for _ in range(100):
            framework.record_impression(experiment.id, "control")
        for _ in range(10):
            framework.record_conversion(experiment.id, "control")
        
        for _ in range(100):
            framework.record_impression(experiment.id, "treatment")
        for _ in range(15):
            framework.record_conversion(experiment.id, "treatment")
        
        result = framework.analyze_experiment(experiment.id)
        
        assert "control" in result
        assert "treatment" in result
        assert "analysis" in result
        assert result["control"]["conversion_rate"] == 0.10
        assert result["treatment"]["conversion_rate"] == 0.15


# ==============================================================================
# Metrics Service Tests
# ==============================================================================

class TestMetricsService:
    """Tests for MetricsService."""
    
    @pytest.fixture
    def service(self):
        """Create a test service."""
        mock_logger = MagicMock()
        mock_analyzer = MagicMock()
        return MetricsService(
            interaction_logger=mock_logger,
            feedback_analyzer=mock_analyzer
        )
    
    def test_record_metric(self, service):
        """Test metric recording."""
        service.record_metric(
            MetricType.CTR,
            value=0.15,
            agent="SearchAgent"
        )
        
        assert MetricType.CTR.value in service._metric_history
        assert len(service._metric_history[MetricType.CTR.value]) == 1
    
    def test_metric_history_limit(self, service):
        """Test metric history is limited."""
        # Record more than 1000 metrics
        for i in range(1100):
            service.record_metric(MetricType.CTR, value=0.1 + i * 0.0001)
        
        # Should be trimmed to 1000
        assert len(service._metric_history[MetricType.CTR.value]) == 1000
    
    @pytest.mark.asyncio
    async def test_get_metric_time_series(self, service):
        """Test time series generation."""
        # Record some metrics
        for i in range(10):
            service.record_metric(MetricType.CTR, value=0.1 + i * 0.01)
        
        series = await service.get_metric_time_series(
            MetricType.CTR,
            granularity="daily"
        )
        
        assert len(series) > 0
        assert "timestamp" in series[0]
        assert "value" in series[0]


# ==============================================================================
# Learning Orchestrator Tests
# ==============================================================================

class TestLearningOrchestrator:
    """Tests for LearningOrchestrator."""
    
    @pytest.fixture
    def orchestrator(self):
        """Create a test orchestrator."""
        config = LearningConfig(
            profile_update_interval=timedelta(hours=24),  # Disable background tasks
            ranking_update_interval=timedelta(hours=24),
            query_mapping_interval=timedelta(hours=24),
            insight_generation_interval=timedelta(hours=24),
            enable_ab_testing=True
        )
        return LearningOrchestrator(config=config)
    
    @pytest.mark.asyncio
    async def test_track_search(self, orchestrator):
        """Test search tracking."""
        interaction_id = await orchestrator.track_search(
            user_id="user-1",
            session_id="sess-1",
            query="savings account",
            results=["prod-1", "prod-2"]
        )
        
        assert interaction_id is not None
        assert "user-1" in orchestrator._active_users
    
    @pytest.mark.asyncio
    async def test_track_product_click(self, orchestrator):
        """Test click tracking."""
        interaction_id = await orchestrator.track_product_click(
            user_id="user-1",
            session_id="sess-1",
            product_id="prod-123",
            position=1,
            items_shown=["prod-1", "prod-123", "prod-3"]
        )
        
        assert interaction_id is not None
    
    def test_get_ab_variant(self, orchestrator):
        """Test A/B variant retrieval."""
        # Create and start an experiment
        orchestrator.create_experiment(
            name="Test",
            description="Test",
            test_type="ranking",
            target_component="SearchAgent",
            control_config={},
            treatment_config={"boost": 1.2}
        )
        
        # Start it
        exp_list = orchestrator._ab_testing.list_experiments()
        orchestrator.start_experiment(exp_list[0]["id"])
        
        # Get variant
        variant_info = orchestrator.get_ab_variant("user-123", "SearchAgent")
        
        assert variant_info is not None
        assert "variant" in variant_info
        assert "config" in variant_info
    
    def test_get_status(self, orchestrator):
        """Test status reporting."""
        status = orchestrator.get_status()
        
        assert "running" in status
        assert "config" in status
        assert "caches" in status
        assert "active_experiments" in status


# ==============================================================================
# Integration Tests
# ==============================================================================

class TestLearningIntegration:
    """Integration tests for the learning system."""
    
    @pytest.mark.asyncio
    async def test_full_interaction_flow(self):
        """Test a complete interaction flow."""
        orchestrator = LearningOrchestrator()
        
        user_id = "integration-user"
        session_id = "integration-session"
        
        # 1. User searches
        await orchestrator.track_search(
            user_id=user_id,
            session_id=session_id,
            query="high yield savings",
            results=["prod-1", "prod-2", "prod-3"]
        )
        
        # 2. User clicks on result
        await orchestrator.track_product_click(
            user_id=user_id,
            session_id=session_id,
            product_id="prod-2",
            position=1,
            items_shown=["prod-1", "prod-2", "prod-3"],
            item_price=100.0,
            budget_max=500.0
        )
        
        # 3. User adds to cart
        await orchestrator.track_cart_action(
            user_id=user_id,
            session_id=session_id,
            product_id="prod-2",
            action="add",
            item_price=100.0
        )
        
        # 4. User purchases
        await orchestrator.track_purchase(
            user_id=user_id,
            session_id=session_id,
            products=[{"id": "prod-2", "price": 100.0}],
            total_amount=100.0
        )
        
        # Verify tracking
        assert user_id in orchestrator._active_users
        stats = orchestrator._interaction_logger.get_stats()
        assert stats["total_logged"] >= 4
    
    @pytest.mark.asyncio
    async def test_ab_test_flow(self):
        """Test A/B test creation and analysis."""
        framework = ABTestingFramework()
        
        # Create experiment
        experiment = framework.create_ranking_experiment(
            name="New Ranking Weights",
            treatment_weights={
                "relevance": 0.5,
                "affordability": 0.25,
                "popularity": 0.15,
                "recency": 0.1
            }
        )
        
        # Start experiment
        framework.start_experiment(experiment.id)
        
        # Simulate traffic
        import random
        for i in range(200):
            user_id = f"user-{i}"
            variant = framework.assign_variant(user_id, experiment.id)
            framework.record_impression(experiment.id, variant)
            
            # Treatment converts slightly better
            conversion_prob = 0.10 if variant == "control" else 0.12
            if random.random() < conversion_prob:
                framework.record_conversion(experiment.id, variant, revenue=100.0)
        
        # Analyze
        result = framework.analyze_experiment(experiment.id)
        
        assert result["analysis"]["has_min_samples"] is False  # Need more samples
        assert "recommendation" in result
