"""
FinFind Learning System.

This module implements the learning and feedback loop system that
improves FinFind over time based on user interactions.

Components:
- InteractionLogger: Captures all user actions with context
- FeedbackAnalyzer: Analyzes patterns and calculates metrics
- ModelUpdater: Updates user profiles and rankings based on feedback
- ABTestingFramework: Tests different agent strategies
- MetricsService: Tracks KPIs and provides dashboard data
- LearningOrchestrator: Coordinates all learning components
"""

from .models import (
    InteractionType,
    Interaction,
    InteractionContext,
    FeedbackSignal,
    UserLearningProfile,
    ABTestExperiment,
    ABTestVariant,
    MetricType,
    MetricValue,
    LearningInsight
)

from .interaction_logger import InteractionLogger, get_interaction_logger
from .feedback_analyzer import FeedbackAnalyzer, get_feedback_analyzer
from .model_updater import ModelUpdater, get_model_updater
from .ab_testing import ABTestingFramework, get_ab_testing
from .metrics_service import MetricsService, get_metrics_service
from .learning_orchestrator import LearningOrchestrator, get_learning_orchestrator

__all__ = [
    # Models
    "InteractionType",
    "Interaction",
    "InteractionContext",
    "FeedbackSignal",
    "UserLearningProfile",
    "ABTestExperiment",
    "ABTestVariant",
    "MetricType",
    "MetricValue",
    "LearningInsight",
    # Services
    "InteractionLogger",
    "get_interaction_logger",
    "FeedbackAnalyzer",
    "get_feedback_analyzer",
    "ModelUpdater",
    "get_model_updater",
    "ABTestingFramework",
    "get_ab_testing",
    "MetricsService",
    "get_metrics_service",
    "LearningOrchestrator",
    "get_learning_orchestrator",
]
