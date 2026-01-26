"""
A/B Testing Framework for FinFind Learning System.

Enables experimentation with different agent strategies,
ranking algorithms, and constraint thresholds.
"""

import logging
import hashlib
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
import math

from .models import (
    ABTestExperiment,
    ABTestVariant,
    MetricType,
    MetricValue
)

logger = logging.getLogger(__name__)


# ==============================================================================
# Statistical Utilities
# ==============================================================================

def calculate_z_score(
    control_conversions: int,
    control_impressions: int,
    treatment_conversions: int,
    treatment_impressions: int
) -> float:
    """
    Calculate Z-score for comparing two proportions.
    
    Uses pooled proportion for standard error calculation.
    """
    if control_impressions == 0 or treatment_impressions == 0:
        return 0.0
    
    p1 = control_conversions / control_impressions
    p2 = treatment_conversions / treatment_impressions
    
    # Pooled proportion
    p_pool = (control_conversions + treatment_conversions) / (
        control_impressions + treatment_impressions
    )
    
    # Standard error
    se = math.sqrt(
        p_pool * (1 - p_pool) * (1/control_impressions + 1/treatment_impressions)
    )
    
    if se == 0:
        return 0.0
    
    return (p2 - p1) / se


def z_to_p_value(z_score: float) -> float:
    """Convert Z-score to p-value (two-tailed)."""
    # Approximation using error function
    return 2 * (1 - 0.5 * (1 + math.erf(abs(z_score) / math.sqrt(2))))


def calculate_lift(control_rate: float, treatment_rate: float) -> float:
    """Calculate percentage lift of treatment over control."""
    if control_rate == 0:
        return 0.0
    return ((treatment_rate - control_rate) / control_rate) * 100


def required_sample_size(
    baseline_rate: float,
    minimum_detectable_effect: float,
    power: float = 0.8,
    significance: float = 0.05
) -> int:
    """
    Calculate required sample size per variant for A/B test.
    
    Args:
        baseline_rate: Expected conversion rate in control
        minimum_detectable_effect: Minimum lift to detect (e.g., 0.1 for 10%)
        power: Statistical power (default 0.8)
        significance: Significance level (default 0.05)
        
    Returns:
        Required sample size per variant
    """
    # Z-scores for power and significance
    z_alpha = 1.96  # For 95% confidence (two-tailed)
    z_beta = 0.84   # For 80% power
    
    p1 = baseline_rate
    p2 = baseline_rate * (1 + minimum_detectable_effect)
    
    pooled_p = (p1 + p2) / 2
    
    n = (
        (z_alpha * math.sqrt(2 * pooled_p * (1 - pooled_p)) + 
         z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
    ) / ((p2 - p1) ** 2)
    
    return int(math.ceil(n))


# ==============================================================================
# A/B Testing Framework
# ==============================================================================

class ABTestingFramework:
    """
    Framework for running A/B tests on FinFind components.
    
    Supports:
    - Experiment lifecycle management
    - User assignment to variants
    - Metric tracking per variant
    - Statistical analysis
    - Auto-conclusion based on significance
    """
    
    def __init__(self):
        """Initialize the A/B testing framework."""
        self._experiments: Dict[str, ABTestExperiment] = {}
        self._user_assignments: Dict[str, Dict[str, str]] = {}  # user_id -> {exp_id -> variant}
        
        # Callbacks for variant application
        self._variant_callbacks: Dict[str, Callable] = {}
    
    # ========================================
    # Experiment Management
    # ========================================
    
    def create_experiment(
        self,
        name: str,
        description: str,
        test_type: str,
        target_component: str,
        control_config: Dict[str, Any],
        treatment_config: Dict[str, Any],
        traffic_split: float = 50.0,
        min_sample_size: int = 1000,
        confidence_level: float = 0.95
    ) -> ABTestExperiment:
        """
        Create a new A/B test experiment.
        
        Args:
            name: Experiment name
            description: What is being tested
            test_type: Type of test (ranking, recommendation, alternative, constraint)
            target_component: Component being tested
            control_config: Configuration for control variant
            treatment_config: Configuration for treatment variant
            traffic_split: Percentage of traffic to treatment (0-100)
            min_sample_size: Minimum samples per variant
            confidence_level: Required confidence for conclusion
            
        Returns:
            Created experiment
        """
        experiment = ABTestExperiment(
            name=name,
            description=description,
            test_type=test_type,
            target_component=target_component,
            control=ABTestVariant(
                id="control",
                name="Control",
                description="Original behavior",
                config=control_config,
                traffic_percentage=100 - traffic_split
            ),
            treatment=ABTestVariant(
                id="treatment",
                name="Treatment",
                description="New behavior",
                config=treatment_config,
                traffic_percentage=traffic_split
            ),
            min_sample_size=min_sample_size,
            confidence_level=confidence_level
        )
        
        self._experiments[experiment.id] = experiment
        logger.info(f"Created experiment: {experiment.id} - {name}")
        
        return experiment
    
    def start_experiment(self, experiment_id: str) -> bool:
        """Start an experiment."""
        experiment = self._experiments.get(experiment_id)
        if not experiment:
            logger.error(f"Experiment not found: {experiment_id}")
            return False
        
        if experiment.status not in ["draft", "paused"]:
            logger.error(f"Cannot start experiment in status: {experiment.status}")
            return False
        
        experiment.status = "running"
        experiment.start_date = datetime.utcnow()
        
        logger.info(f"Started experiment: {experiment_id}")
        return True
    
    def pause_experiment(self, experiment_id: str) -> bool:
        """Pause a running experiment."""
        experiment = self._experiments.get(experiment_id)
        if not experiment or experiment.status != "running":
            return False
        
        experiment.status = "paused"
        logger.info(f"Paused experiment: {experiment_id}")
        return True
    
    def stop_experiment(self, experiment_id: str, conclude: bool = True) -> Optional[Dict[str, Any]]:
        """
        Stop an experiment and optionally conclude it.
        
        Args:
            experiment_id: Experiment to stop
            conclude: Whether to run final analysis
            
        Returns:
            Experiment results if concluded
        """
        experiment = self._experiments.get(experiment_id)
        if not experiment:
            return None
        
        experiment.status = "completed"
        experiment.end_date = datetime.utcnow()
        
        if conclude:
            return self.analyze_experiment(experiment_id)
        
        return experiment.to_dict()
    
    # ========================================
    # User Assignment
    # ========================================
    
    def assign_variant(
        self,
        user_id: str,
        experiment_id: str,
        force_variant: Optional[str] = None
    ) -> str:
        """
        Assign a user to an experiment variant.
        
        Uses deterministic hashing for consistent assignment.
        
        Args:
            user_id: User to assign
            experiment_id: Experiment to assign to
            force_variant: Force specific variant (for testing)
            
        Returns:
            Variant ID ("control" or "treatment")
        """
        experiment = self._experiments.get(experiment_id)
        if not experiment or experiment.status != "running":
            return "control"  # Default to control if experiment not running
        
        # Check existing assignment
        user_assignments = self._user_assignments.get(user_id, {})
        if experiment_id in user_assignments and not force_variant:
            return user_assignments[experiment_id]
        
        # Force variant if specified
        if force_variant:
            variant = force_variant
        else:
            # Deterministic assignment based on user_id + experiment_id
            hash_input = f"{user_id}:{experiment_id}"
            hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
            bucket = hash_value % 100
            
            variant = "treatment" if bucket < experiment.treatment.traffic_percentage else "control"
        
        # Store assignment
        if user_id not in self._user_assignments:
            self._user_assignments[user_id] = {}
        self._user_assignments[user_id][experiment_id] = variant
        
        return variant
    
    def get_user_variant(
        self,
        user_id: str,
        experiment_id: str
    ) -> Optional[str]:
        """Get a user's assigned variant for an experiment."""
        return self._user_assignments.get(user_id, {}).get(experiment_id)
    
    def get_variant_config(
        self,
        user_id: str,
        experiment_id: str
    ) -> Dict[str, Any]:
        """
        Get the configuration for a user's assigned variant.
        
        Returns:
            Variant configuration dict
        """
        experiment = self._experiments.get(experiment_id)
        if not experiment:
            return {}
        
        variant_id = self.assign_variant(user_id, experiment_id)
        
        if variant_id == "treatment":
            return experiment.treatment.config
        return experiment.control.config
    
    # ========================================
    # Metric Tracking
    # ========================================
    
    def record_impression(
        self,
        experiment_id: str,
        variant_id: str
    ):
        """Record an impression for a variant."""
        experiment = self._experiments.get(experiment_id)
        if not experiment:
            return
        
        variant = experiment.treatment if variant_id == "treatment" else experiment.control
        variant.impressions += 1
        variant.update_metrics()
    
    def record_conversion(
        self,
        experiment_id: str,
        variant_id: str,
        revenue: float = 0.0
    ):
        """Record a conversion for a variant."""
        experiment = self._experiments.get(experiment_id)
        if not experiment:
            return
        
        variant = experiment.treatment if variant_id == "treatment" else experiment.control
        variant.conversions += 1
        variant.total_revenue += revenue
        variant.update_metrics()
    
    def record_interaction(
        self,
        user_id: str,
        experiment_id: str,
        is_conversion: bool,
        revenue: float = 0.0
    ):
        """
        Record a user interaction in an experiment.
        
        Automatically determines variant and records metrics.
        """
        variant_id = self.get_user_variant(user_id, experiment_id)
        if not variant_id:
            return
        
        self.record_impression(experiment_id, variant_id)
        
        if is_conversion:
            self.record_conversion(experiment_id, variant_id, revenue)
    
    # ========================================
    # Analysis
    # ========================================
    
    def analyze_experiment(
        self,
        experiment_id: str
    ) -> Dict[str, Any]:
        """
        Analyze experiment results and determine winner.
        
        Returns:
            Analysis results including statistical significance
        """
        experiment = self._experiments.get(experiment_id)
        if not experiment:
            return {"error": "Experiment not found"}
        
        control = experiment.control
        treatment = experiment.treatment
        
        # Update metrics
        control.update_metrics()
        treatment.update_metrics()
        
        # Check minimum sample size
        total_impressions = control.impressions + treatment.impressions
        has_min_samples = (
            control.impressions >= experiment.min_sample_size and
            treatment.impressions >= experiment.min_sample_size
        )
        
        # Calculate Z-score
        z_score = calculate_z_score(
            control.conversions, control.impressions,
            treatment.conversions, treatment.impressions
        )
        
        # Calculate p-value
        p_value = z_to_p_value(z_score)
        
        # Determine significance
        significance_threshold = 1 - experiment.confidence_level
        is_significant = p_value < significance_threshold
        
        # Calculate lift
        lift = calculate_lift(control.conversion_rate, treatment.conversion_rate)
        
        # Determine winner
        winner = None
        if is_significant:
            if treatment.conversion_rate > control.conversion_rate:
                winner = "treatment"
            else:
                winner = "control"
        
        # Update experiment
        experiment.statistical_significance = 1 - p_value
        experiment.lift = lift
        experiment.winner = winner
        
        return {
            "experiment_id": experiment_id,
            "name": experiment.name,
            "status": experiment.status,
            "control": {
                "impressions": control.impressions,
                "conversions": control.conversions,
                "conversion_rate": control.conversion_rate,
                "revenue": control.total_revenue,
                "rpi": control.revenue_per_impression
            },
            "treatment": {
                "impressions": treatment.impressions,
                "conversions": treatment.conversions,
                "conversion_rate": treatment.conversion_rate,
                "revenue": treatment.total_revenue,
                "rpi": treatment.revenue_per_impression
            },
            "analysis": {
                "z_score": z_score,
                "p_value": p_value,
                "is_significant": is_significant,
                "confidence": 1 - p_value,
                "lift_percentage": lift,
                "has_min_samples": has_min_samples,
                "winner": winner
            },
            "recommendation": self._generate_recommendation(
                experiment, is_significant, lift, has_min_samples
            )
        }
    
    def _generate_recommendation(
        self,
        experiment: ABTestExperiment,
        is_significant: bool,
        lift: float,
        has_min_samples: bool
    ) -> str:
        """Generate a recommendation based on analysis."""
        
        if not has_min_samples:
            remaining = max(
                experiment.min_sample_size - experiment.control.impressions,
                experiment.min_sample_size - experiment.treatment.impressions
            )
            return f"Continue running. Need {remaining} more impressions for minimum sample size."
        
        if not is_significant:
            return "Results not statistically significant. Continue running or increase traffic."
        
        if lift > 0:
            return f"Treatment is winning with {lift:.1f}% lift. Consider rolling out treatment."
        else:
            return f"Control is winning. Treatment shows {lift:.1f}% decrease. Keep control."
    
    # ========================================
    # Predefined Experiments
    # ========================================
    
    def create_ranking_experiment(
        self,
        name: str,
        treatment_weights: Dict[str, float]
    ) -> ABTestExperiment:
        """
        Create an experiment for testing ranking algorithm changes.
        
        Args:
            name: Experiment name
            treatment_weights: New ranking weights to test
        """
        return self.create_experiment(
            name=name,
            description="Testing new ranking weights",
            test_type="ranking",
            target_component="SearchAgent",
            control_config={
                "weights": {
                    "relevance": 0.4,
                    "affordability": 0.3,
                    "popularity": 0.2,
                    "recency": 0.1
                }
            },
            treatment_config={
                "weights": treatment_weights
            }
        )
    
    def create_recommendation_experiment(
        self,
        name: str,
        treatment_strategy: str,
        treatment_params: Dict[str, Any]
    ) -> ABTestExperiment:
        """
        Create an experiment for testing recommendation strategies.
        
        Args:
            name: Experiment name
            treatment_strategy: New recommendation strategy
            treatment_params: Strategy parameters
        """
        return self.create_experiment(
            name=name,
            description=f"Testing {treatment_strategy} recommendation strategy",
            test_type="recommendation",
            target_component="RecommendationAgent",
            control_config={
                "strategy": "collaborative_filtering",
                "params": {"similarity_threshold": 0.7}
            },
            treatment_config={
                "strategy": treatment_strategy,
                "params": treatment_params
            }
        )
    
    def create_constraint_experiment(
        self,
        name: str,
        budget_flexibility: float
    ) -> ABTestExperiment:
        """
        Create an experiment for testing constraint thresholds.
        
        Args:
            name: Experiment name
            budget_flexibility: New budget flexibility factor (0-1)
        """
        return self.create_experiment(
            name=name,
            description=f"Testing {budget_flexibility:.0%} budget flexibility",
            test_type="constraint",
            target_component="SearchAgent",
            control_config={
                "budget_flexibility": 0.0,  # Strict budget
                "show_slightly_over": False
            },
            treatment_config={
                "budget_flexibility": budget_flexibility,
                "show_slightly_over": budget_flexibility > 0
            }
        )
    
    # ========================================
    # Utility Methods
    # ========================================
    
    def list_experiments(
        self,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List all experiments, optionally filtered by status."""
        experiments = []
        
        for exp in self._experiments.values():
            if status is None or exp.status == status:
                experiments.append({
                    "id": exp.id,
                    "name": exp.name,
                    "status": exp.status,
                    "test_type": exp.test_type,
                    "target_component": exp.target_component,
                    "total_impressions": exp.control.impressions + exp.treatment.impressions,
                    "created_at": exp.created_at.isoformat()
                })
        
        return experiments
    
    def get_experiment(self, experiment_id: str) -> Optional[ABTestExperiment]:
        """Get an experiment by ID."""
        return self._experiments.get(experiment_id)
    
    def get_active_experiments_for_component(
        self,
        component: str
    ) -> List[ABTestExperiment]:
        """Get all running experiments for a component."""
        return [
            exp for exp in self._experiments.values()
            if exp.status == "running" and exp.target_component == component
        ]


# Singleton instance
_ab_testing: Optional[ABTestingFramework] = None


def get_ab_testing() -> ABTestingFramework:
    """Get the singleton A/B testing framework instance."""
    global _ab_testing
    if _ab_testing is None:
        _ab_testing = ABTestingFramework()
    return _ab_testing
