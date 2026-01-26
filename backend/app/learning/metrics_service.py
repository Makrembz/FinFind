"""
Metrics Service for FinFind Learning System.

Provides KPI tracking, dashboard data, and monitoring
for the learning and feedback system.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
from dataclasses import dataclass, field
import statistics

from .models import (
    MetricType,
    MetricValue,
    LearningInsight
)
from .interaction_logger import InteractionLogger, get_interaction_logger
from .feedback_analyzer import FeedbackAnalyzer, get_feedback_analyzer

logger = logging.getLogger(__name__)


@dataclass
class MetricSummary:
    """Summary of a metric over time."""
    
    metric_type: MetricType
    current_value: float
    previous_value: float
    change_percentage: float
    trend: str  # "up", "down", "stable"
    
    values_over_time: List[MetricValue] = field(default_factory=list)
    
    min_value: float = 0.0
    max_value: float = 0.0
    avg_value: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_type": self.metric_type.value,
            "current_value": self.current_value,
            "previous_value": self.previous_value,
            "change_percentage": self.change_percentage,
            "trend": self.trend,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "avg_value": self.avg_value,
            "data_points": len(self.values_over_time)
        }


@dataclass
class DashboardData:
    """Complete dashboard data snapshot."""
    
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Key metrics
    overall_ctr: float = 0.0
    overall_conversion: float = 0.0
    budget_compliance: float = 0.0
    recommendation_effectiveness: float = 0.0
    
    # Trends
    metric_trends: Dict[str, MetricSummary] = field(default_factory=dict)
    
    # Segments
    segment_performance: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Agent performance
    agent_metrics: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Alerts and insights
    active_insights: List[LearningInsight] = field(default_factory=list)
    
    # Experiment status
    active_experiments: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "key_metrics": {
                "overall_ctr": self.overall_ctr,
                "overall_conversion": self.overall_conversion,
                "budget_compliance": self.budget_compliance,
                "recommendation_effectiveness": self.recommendation_effectiveness
            },
            "metric_trends": {
                k: v.to_dict() for k, v in self.metric_trends.items()
            },
            "segment_performance": self.segment_performance,
            "agent_metrics": self.agent_metrics,
            "active_insights": [i.to_dict() for i in self.active_insights],
            "active_experiments": self.active_experiments
        }


class MetricsService:
    """
    Service for tracking and reporting learning system metrics.
    
    Provides:
    - Real-time KPI tracking
    - Historical metric trends
    - Dashboard data aggregation
    - Alert generation
    - Segment analysis
    """
    
    # Metric thresholds for alerts
    ALERT_THRESHOLDS = {
        MetricType.CTR: {"low": 0.05, "critical": 0.02},
        MetricType.CONVERSION_RATE: {"low": 0.02, "critical": 0.01},
        MetricType.BUDGET_COMPLIANCE: {"low": 0.8, "critical": 0.6},
        MetricType.RECOMMENDATION_CTR: {"low": 0.03, "critical": 0.01},
        MetricType.ALTERNATIVE_ACCEPTANCE: {"low": 0.15, "critical": 0.05},
    }
    
    def __init__(
        self,
        interaction_logger: Optional[InteractionLogger] = None,
        feedback_analyzer: Optional[FeedbackAnalyzer] = None
    ):
        """
        Initialize the metrics service.
        
        Args:
            interaction_logger: Logger for fetching interactions
            feedback_analyzer: Analyzer for computing metrics
        """
        self._logger = interaction_logger or get_interaction_logger()
        self._analyzer = feedback_analyzer or get_feedback_analyzer()
        
        # Metric history cache
        self._metric_history: Dict[str, List[MetricValue]] = defaultdict(list)
        
        # Cache settings
        self._cache_duration = timedelta(minutes=5)
        self._last_refresh: Optional[datetime] = None
        self._cached_dashboard: Optional[DashboardData] = None
    
    # ========================================
    # Dashboard Data
    # ========================================
    
    async def get_dashboard_data(
        self,
        force_refresh: bool = False
    ) -> DashboardData:
        """
        Get complete dashboard data.
        
        Args:
            force_refresh: Force refresh even if cache is valid
            
        Returns:
            Complete dashboard data snapshot
        """
        # Check cache
        if (
            not force_refresh and 
            self._cached_dashboard and 
            self._last_refresh and
            datetime.utcnow() - self._last_refresh < self._cache_duration
        ):
            return self._cached_dashboard
        
        # Build fresh dashboard
        dashboard = DashboardData()
        
        # Get key metrics
        try:
            funnel = await self._analyzer.calculate_conversion_funnel()
            compliance = await self._analyzer.calculate_constraint_compliance()
            rec_metrics = await self._analyzer.calculate_recommendation_metrics()
            alt_metrics = await self._analyzer.calculate_alternative_metrics()
            
            dashboard.overall_ctr = funnel["search_to_click"].value
            dashboard.overall_conversion = funnel["overall_conversion"].value
            dashboard.budget_compliance = compliance.value
            dashboard.recommendation_effectiveness = rec_metrics["recommendation_ctr"].value
            
            # Build metric trends
            dashboard.metric_trends = await self._build_metric_trends()
            
            # Agent metrics
            dashboard.agent_metrics = {
                "SearchAgent": {
                    "ctr": dashboard.overall_ctr,
                    "zero_result_rate": 0.0  # Would need to track
                },
                "RecommendationAgent": {
                    "ctr": rec_metrics["recommendation_ctr"].value,
                    "conversion": rec_metrics["recommendation_conversion"].value
                },
                "ExplainabilityAgent": {
                    "helpfulness_rate": 0.0  # Would need to track
                },
                "AlternativeAgent": {
                    "acceptance_rate": alt_metrics["alternative_acceptance"].value
                }
            }
            
            # Get insights
            dashboard.active_insights = await self._analyzer.generate_insights()
            
        except Exception as e:
            logger.error(f"Error building dashboard: {e}")
        
        # Cache and return
        self._cached_dashboard = dashboard
        self._last_refresh = datetime.utcnow()
        
        return dashboard
    
    async def _build_metric_trends(
        self,
        time_window: timedelta = timedelta(days=30)
    ) -> Dict[str, MetricSummary]:
        """Build metric trends over time."""
        trends = {}
        
        # Key metrics to trend
        metrics_to_track = [
            MetricType.CTR,
            MetricType.CONVERSION_RATE,
            MetricType.BUDGET_COMPLIANCE,
            MetricType.RECOMMENDATION_CTR,
            MetricType.ALTERNATIVE_ACCEPTANCE
        ]
        
        for metric_type in metrics_to_track:
            history = self._metric_history.get(metric_type.value, [])
            
            if len(history) < 2:
                continue
            
            # Sort by timestamp
            history.sort(key=lambda m: m.timestamp)
            
            current = history[-1].value if history else 0
            previous = history[-2].value if len(history) > 1 else current
            
            change = ((current - previous) / previous * 100) if previous != 0 else 0
            
            trend = "stable"
            if change > 5:
                trend = "up"
            elif change < -5:
                trend = "down"
            
            values = [m.value for m in history]
            
            trends[metric_type.value] = MetricSummary(
                metric_type=metric_type,
                current_value=current,
                previous_value=previous,
                change_percentage=change,
                trend=trend,
                values_over_time=history[-30:],  # Last 30 points
                min_value=min(values) if values else 0,
                max_value=max(values) if values else 0,
                avg_value=statistics.mean(values) if values else 0
            )
        
        return trends
    
    # ========================================
    # Metric Recording
    # ========================================
    
    def record_metric(
        self,
        metric_type: MetricType,
        value: float,
        user_id: Optional[str] = None,
        segment: Optional[str] = None,
        agent: Optional[str] = None
    ):
        """
        Record a metric value.
        
        Args:
            metric_type: Type of metric
            value: Metric value
            user_id: Optional user ID
            segment: Optional segment
            agent: Optional agent name
        """
        metric = MetricValue(
            metric_type=metric_type,
            value=value,
            user_id=user_id,
            segment=segment,
            agent=agent
        )
        
        key = metric_type.value
        self._metric_history[key].append(metric)
        
        # Trim history to last 1000 points
        if len(self._metric_history[key]) > 1000:
            self._metric_history[key] = self._metric_history[key][-1000:]
        
        # Check for alert conditions
        self._check_alert_threshold(metric_type, value)
    
    def _check_alert_threshold(
        self,
        metric_type: MetricType,
        value: float
    ):
        """Check if metric value triggers an alert."""
        thresholds = self.ALERT_THRESHOLDS.get(metric_type)
        
        if not thresholds:
            return
        
        if value < thresholds.get("critical", 0):
            logger.warning(f"CRITICAL: {metric_type.value} = {value:.4f} below critical threshold")
        elif value < thresholds.get("low", 0):
            logger.warning(f"LOW: {metric_type.value} = {value:.4f} below low threshold")
    
    # ========================================
    # Segment Analysis
    # ========================================
    
    async def get_segment_metrics(
        self,
        segment_by: str = "income_bracket",
        time_window: timedelta = timedelta(days=7)
    ) -> Dict[str, Dict[str, float]]:
        """
        Get metrics broken down by segment.
        
        Args:
            segment_by: Field to segment by (income_bracket, risk_tolerance, etc.)
            time_window: Time window for analysis
            
        Returns:
            Dict of segment -> metrics
        """
        interactions = await self._logger.get_user_interactions(
            user_id="*",
            limit=50000,
            since=datetime.utcnow() - time_window
        )
        
        # Group by segment
        segments: Dict[str, List] = defaultdict(list)
        
        for interaction in interactions:
            segment_value = getattr(interaction.context, segment_by, None) or "unknown"
            segments[segment_value].append(interaction)
        
        # Calculate metrics per segment
        results = {}
        
        for segment, segment_interactions in segments.items():
            clicks = sum(1 for i in segment_interactions if "click" in i.interaction_type.value)
            views = sum(1 for i in segment_interactions if "view" in i.interaction_type.value)
            purchases = sum(1 for i in segment_interactions if i.interaction_type.value == "purchase_complete")
            
            ctr = clicks / views if views > 0 else 0
            conversion = purchases / clicks if clicks > 0 else 0
            
            with_budget = [i for i in segment_interactions if i.context.budget_max]
            compliant = sum(1 for i in with_budget if not i.budget_exceeded)
            compliance = compliant / len(with_budget) if with_budget else 1.0
            
            results[segment] = {
                "interaction_count": len(segment_interactions),
                "ctr": ctr,
                "conversion_rate": conversion,
                "budget_compliance": compliance
            }
        
        return results
    
    # ========================================
    # Time Series
    # ========================================
    
    async def get_metric_time_series(
        self,
        metric_type: MetricType,
        granularity: str = "daily",
        time_window: timedelta = timedelta(days=30)
    ) -> List[Dict[str, Any]]:
        """
        Get metric values as a time series.
        
        Args:
            metric_type: Metric to retrieve
            granularity: hourly, daily, weekly
            time_window: How far back to look
            
        Returns:
            List of {timestamp, value} points
        """
        history = self._metric_history.get(metric_type.value, [])
        
        # Filter by time window
        cutoff = datetime.utcnow() - time_window
        filtered = [m for m in history if m.timestamp >= cutoff]
        
        # Aggregate by granularity
        if granularity == "hourly":
            bucket_format = "%Y-%m-%d %H:00"
        elif granularity == "weekly":
            bucket_format = "%Y-W%W"
        else:  # daily
            bucket_format = "%Y-%m-%d"
        
        buckets: Dict[str, List[float]] = defaultdict(list)
        
        for metric in filtered:
            bucket = metric.timestamp.strftime(bucket_format)
            buckets[bucket].append(metric.value)
        
        # Calculate averages per bucket
        time_series = []
        for bucket, values in sorted(buckets.items()):
            time_series.append({
                "timestamp": bucket,
                "value": statistics.mean(values),
                "count": len(values)
            })
        
        return time_series
    
    # ========================================
    # KPI Summary
    # ========================================
    
    async def get_kpi_summary(
        self,
        time_window: timedelta = timedelta(days=7)
    ) -> Dict[str, Any]:
        """
        Get a summary of key performance indicators.
        
        Returns:
            Summary dict with KPIs and their status
        """
        funnel = await self._analyzer.calculate_conversion_funnel(time_window=time_window)
        compliance = await self._analyzer.calculate_constraint_compliance(time_window=time_window)
        rec_metrics = await self._analyzer.calculate_recommendation_metrics(time_window=time_window)
        alt_metrics = await self._analyzer.calculate_alternative_metrics(time_window=time_window)
        
        def get_status(value: float, thresholds: Dict[str, float]) -> str:
            if value < thresholds.get("critical", 0):
                return "critical"
            elif value < thresholds.get("low", 0):
                return "warning"
            return "healthy"
        
        return {
            "period": f"Last {time_window.days} days",
            "kpis": {
                "search_ctr": {
                    "value": funnel["search_to_click"].value,
                    "status": get_status(
                        funnel["search_to_click"].value,
                        self.ALERT_THRESHOLDS.get(MetricType.CTR, {})
                    ),
                    "description": "Search click-through rate"
                },
                "conversion_rate": {
                    "value": funnel["overall_conversion"].value,
                    "status": get_status(
                        funnel["overall_conversion"].value,
                        self.ALERT_THRESHOLDS.get(MetricType.CONVERSION_RATE, {})
                    ),
                    "description": "Overall search to purchase conversion"
                },
                "budget_compliance": {
                    "value": compliance.value,
                    "status": get_status(
                        compliance.value,
                        self.ALERT_THRESHOLDS.get(MetricType.BUDGET_COMPLIANCE, {})
                    ),
                    "description": "Percentage of interactions within budget"
                },
                "recommendation_ctr": {
                    "value": rec_metrics["recommendation_ctr"].value,
                    "status": get_status(
                        rec_metrics["recommendation_ctr"].value,
                        self.ALERT_THRESHOLDS.get(MetricType.RECOMMENDATION_CTR, {})
                    ),
                    "description": "Recommendation click-through rate"
                },
                "alternative_acceptance": {
                    "value": alt_metrics["alternative_acceptance"].value,
                    "status": get_status(
                        alt_metrics["alternative_acceptance"].value,
                        self.ALERT_THRESHOLDS.get(MetricType.ALTERNATIVE_ACCEPTANCE, {})
                    ),
                    "description": "Alternative product acceptance rate"
                },
                "cart_abandonment": {
                    "value": 1 - funnel["cart_to_purchase"].value,
                    "status": "healthy" if funnel["cart_to_purchase"].value > 0.3 else "warning",
                    "description": "Cart abandonment rate"
                }
            }
        }
    
    # ========================================
    # Export
    # ========================================
    
    async def export_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
        metrics: Optional[List[MetricType]] = None
    ) -> Dict[str, Any]:
        """
        Export metrics for a date range.
        
        Args:
            start_date: Start of export period
            end_date: End of export period
            metrics: Specific metrics to export (None = all)
            
        Returns:
            Export data with metrics and metadata
        """
        export = {
            "export_timestamp": datetime.utcnow().isoformat(),
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "metrics": {}
        }
        
        metrics_to_export = metrics or list(MetricType)
        
        for metric_type in metrics_to_export:
            history = self._metric_history.get(metric_type.value, [])
            
            # Filter by date range
            filtered = [
                m for m in history
                if start_date <= m.timestamp <= end_date
            ]
            
            if filtered:
                values = [m.value for m in filtered]
                export["metrics"][metric_type.value] = {
                    "count": len(filtered),
                    "min": min(values),
                    "max": max(values),
                    "avg": statistics.mean(values),
                    "std": statistics.stdev(values) if len(values) > 1 else 0,
                    "data": [
                        {
                            "timestamp": m.timestamp.isoformat(),
                            "value": m.value,
                            "user_id": m.user_id,
                            "segment": m.segment
                        }
                        for m in filtered
                    ]
                }
        
        return export


# Singleton instance
_metrics_service: Optional[MetricsService] = None


def get_metrics_service() -> MetricsService:
    """Get the singleton metrics service instance."""
    global _metrics_service
    if _metrics_service is None:
        _metrics_service = MetricsService()
    return _metrics_service
