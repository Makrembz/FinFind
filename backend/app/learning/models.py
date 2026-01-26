"""
Learning System Data Models.

Defines all data structures for the learning and feedback system.
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
import uuid


# ==============================================================================
# Interaction Types
# ==============================================================================

class InteractionType(str, Enum):
    """Types of user interactions tracked by the system."""
    
    # Search interactions
    SEARCH = "search"
    SEARCH_REFINEMENT = "search_refinement"
    VOICE_SEARCH = "voice_search"
    IMAGE_SEARCH = "image_search"
    
    # Product interactions
    PRODUCT_VIEW = "product_view"
    PRODUCT_CLICK = "product_click"
    PRODUCT_COMPARE = "product_compare"
    PRODUCT_SHARE = "product_share"
    
    # Cart/Purchase interactions
    ADD_TO_CART = "add_to_cart"
    REMOVE_FROM_CART = "remove_from_cart"
    PURCHASE = "purchase"
    PURCHASE_COMPLETE = "purchase_complete"
    
    # Recommendation interactions
    RECOMMENDATION_VIEW = "recommendation_view"
    RECOMMENDATION_CLICK = "recommendation_click"
    RECOMMENDATION_DISMISS = "recommendation_dismiss"
    
    # Alternative interactions
    ALTERNATIVE_VIEW = "alternative_view"
    ALTERNATIVE_CLICK = "alternative_click"
    ALTERNATIVE_ACCEPT = "alternative_accept"
    ALTERNATIVE_REJECT = "alternative_reject"
    
    # Explanation interactions
    EXPLANATION_VIEW = "explanation_view"
    EXPLANATION_HELPFUL = "explanation_helpful"
    EXPLANATION_UNHELPFUL = "explanation_unhelpful"
    
    # Feedback interactions
    RATING = "rating"
    REVIEW = "review"
    FEEDBACK = "feedback"
    
    # Session interactions
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    PAGE_VIEW = "page_view"


class FeedbackSignal(str, Enum):
    """Types of feedback signals derived from interactions."""
    
    POSITIVE = "positive"           # User liked/engaged
    NEGATIVE = "negative"           # User rejected/dismissed
    NEUTRAL = "neutral"             # User viewed but no strong signal
    IMPLICIT_POSITIVE = "implicit_positive"  # Inferred from behavior
    IMPLICIT_NEGATIVE = "implicit_negative"  # Inferred from abandonment


class MetricType(str, Enum):
    """Types of metrics tracked by the learning system."""
    
    # Engagement metrics
    CTR = "click_through_rate"
    VIEW_TIME = "view_time"
    SCROLL_DEPTH = "scroll_depth"
    BOUNCE_RATE = "bounce_rate"
    
    # Conversion metrics
    CART_RATE = "add_to_cart_rate"
    PURCHASE_RATE = "purchase_rate"
    CONVERSION_RATE = "conversion_rate"
    
    # Recommendation metrics
    RECOMMENDATION_CTR = "recommendation_ctr"
    RECOMMENDATION_CONVERSION = "recommendation_conversion"
    PERSONALIZATION_SCORE = "personalization_score"
    
    # Alternative metrics
    ALTERNATIVE_ACCEPTANCE = "alternative_acceptance"
    BUDGET_COMPLIANCE = "budget_compliance"
    CONSTRAINT_VIOLATION = "constraint_violation"
    
    # Quality metrics
    SEARCH_SUCCESS_RATE = "search_success_rate"
    ZERO_RESULT_RATE = "zero_result_rate"
    EXPLANATION_HELPFULNESS = "explanation_helpfulness"
    
    # Business metrics
    REVENUE = "revenue"
    AOV = "average_order_value"
    ITEMS_PER_ORDER = "items_per_order"


# ==============================================================================
# Interaction Data Structures
# ==============================================================================

@dataclass
class InteractionContext:
    """Context captured at interaction time."""
    
    # User context
    user_id: str
    session_id: str
    device_type: str = "unknown"
    platform: str = "web"
    
    # Financial context at interaction time
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    income_bracket: Optional[str] = None
    risk_tolerance: Optional[str] = None
    
    # Search/query context
    query: Optional[str] = None
    filters_applied: Dict[str, Any] = field(default_factory=dict)
    sort_order: Optional[str] = None
    page_number: int = 1
    
    # Agent context
    agent_used: Optional[str] = None
    workflow_id: Optional[str] = None
    ab_test_variant: Optional[str] = None
    
    # Timestamp
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "device_type": self.device_type,
            "platform": self.platform,
            "budget_min": self.budget_min,
            "budget_max": self.budget_max,
            "income_bracket": self.income_bracket,
            "risk_tolerance": self.risk_tolerance,
            "query": self.query,
            "filters_applied": self.filters_applied,
            "sort_order": self.sort_order,
            "page_number": self.page_number,
            "agent_used": self.agent_used,
            "workflow_id": self.workflow_id,
            "ab_test_variant": self.ab_test_variant,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class Interaction:
    """A single user interaction with the system."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    interaction_type: InteractionType = InteractionType.PAGE_VIEW
    context: InteractionContext = field(default_factory=lambda: InteractionContext(
        user_id="anonymous", session_id="unknown"
    ))
    
    # What was shown/recommended
    items_shown: List[str] = field(default_factory=list)  # Product IDs
    recommendations_shown: List[str] = field(default_factory=list)
    alternatives_shown: List[str] = field(default_factory=list)
    
    # What user interacted with
    item_interacted: Optional[str] = None  # Product ID
    position: Optional[int] = None  # Position in list (for CTR calculation)
    
    # Interaction details
    duration_ms: Optional[int] = None
    scroll_depth: Optional[float] = None
    
    # Financial context of interaction
    item_price: Optional[float] = None
    budget_exceeded: bool = False
    constraint_violated: Optional[str] = None
    
    # Derived signals
    feedback_signal: FeedbackSignal = FeedbackSignal.NEUTRAL
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "interaction_type": self.interaction_type.value,
            "context": self.context.to_dict(),
            "items_shown": self.items_shown,
            "recommendations_shown": self.recommendations_shown,
            "alternatives_shown": self.alternatives_shown,
            "item_interacted": self.item_interacted,
            "position": self.position,
            "duration_ms": self.duration_ms,
            "scroll_depth": self.scroll_depth,
            "item_price": self.item_price,
            "budget_exceeded": self.budget_exceeded,
            "constraint_violated": self.constraint_violated,
            "feedback_signal": self.feedback_signal.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Interaction":
        context_data = data.get("context", {})
        context = InteractionContext(
            user_id=context_data.get("user_id", "anonymous"),
            session_id=context_data.get("session_id", "unknown"),
            device_type=context_data.get("device_type", "unknown"),
            platform=context_data.get("platform", "web"),
            budget_min=context_data.get("budget_min"),
            budget_max=context_data.get("budget_max"),
            income_bracket=context_data.get("income_bracket"),
            risk_tolerance=context_data.get("risk_tolerance"),
            query=context_data.get("query"),
            filters_applied=context_data.get("filters_applied", {}),
            sort_order=context_data.get("sort_order"),
            page_number=context_data.get("page_number", 1),
            agent_used=context_data.get("agent_used"),
            workflow_id=context_data.get("workflow_id"),
            ab_test_variant=context_data.get("ab_test_variant"),
        )
        
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            interaction_type=InteractionType(data.get("interaction_type", "page_view")),
            context=context,
            items_shown=data.get("items_shown", []),
            recommendations_shown=data.get("recommendations_shown", []),
            alternatives_shown=data.get("alternatives_shown", []),
            item_interacted=data.get("item_interacted"),
            position=data.get("position"),
            duration_ms=data.get("duration_ms"),
            scroll_depth=data.get("scroll_depth"),
            item_price=data.get("item_price"),
            budget_exceeded=data.get("budget_exceeded", False),
            constraint_violated=data.get("constraint_violated"),
            feedback_signal=FeedbackSignal(data.get("feedback_signal", "neutral")),
            metadata=data.get("metadata", {})
        )


# ==============================================================================
# User Learning Profile
# ==============================================================================

@dataclass
class UserLearningProfile:
    """
    Learning profile for a user, updated based on interactions.
    
    This captures learned preferences and behaviors that improve
    personalization over time.
    """
    
    user_id: str
    
    # Learned budget behavior
    stated_budget_max: Optional[float] = None
    actual_purchase_avg: Optional[float] = None
    actual_purchase_max: Optional[float] = None
    budget_stretch_categories: List[str] = field(default_factory=list)
    budget_strict_categories: List[str] = field(default_factory=list)
    learned_budget_flexibility: float = 0.0  # -1 to 1, negative = strict
    
    # Learned preferences
    preferred_categories: Dict[str, float] = field(default_factory=dict)  # category -> affinity score
    preferred_providers: Dict[str, float] = field(default_factory=dict)
    preferred_features: Dict[str, float] = field(default_factory=dict)
    
    # Interaction patterns
    avg_session_duration: float = 0.0
    avg_items_viewed: float = 0.0
    avg_search_refinements: float = 0.0
    preferred_search_type: str = "text"  # text, voice, image
    
    # Recommendation engagement
    recommendation_ctr: float = 0.0
    alternative_acceptance_rate: float = 0.0
    explanation_engagement_rate: float = 0.0
    
    # Conversion metrics
    view_to_cart_rate: float = 0.0
    cart_to_purchase_rate: float = 0.0
    overall_conversion_rate: float = 0.0
    
    # Quality scores
    personalization_effectiveness: float = 0.0  # How well recommendations match
    constraint_compliance: float = 1.0  # How often constraints are respected
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    interaction_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "stated_budget_max": self.stated_budget_max,
            "actual_purchase_avg": self.actual_purchase_avg,
            "actual_purchase_max": self.actual_purchase_max,
            "budget_stretch_categories": self.budget_stretch_categories,
            "budget_strict_categories": self.budget_strict_categories,
            "learned_budget_flexibility": self.learned_budget_flexibility,
            "preferred_categories": self.preferred_categories,
            "preferred_providers": self.preferred_providers,
            "preferred_features": self.preferred_features,
            "avg_session_duration": self.avg_session_duration,
            "avg_items_viewed": self.avg_items_viewed,
            "avg_search_refinements": self.avg_search_refinements,
            "preferred_search_type": self.preferred_search_type,
            "recommendation_ctr": self.recommendation_ctr,
            "alternative_acceptance_rate": self.alternative_acceptance_rate,
            "explanation_engagement_rate": self.explanation_engagement_rate,
            "view_to_cart_rate": self.view_to_cart_rate,
            "cart_to_purchase_rate": self.cart_to_purchase_rate,
            "overall_conversion_rate": self.overall_conversion_rate,
            "personalization_effectiveness": self.personalization_effectiveness,
            "constraint_compliance": self.constraint_compliance,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "interaction_count": self.interaction_count
        }


# ==============================================================================
# A/B Testing Models
# ==============================================================================

@dataclass
class ABTestVariant:
    """A variant in an A/B test experiment."""
    
    id: str
    name: str
    description: str
    
    # Configuration for this variant
    config: Dict[str, Any] = field(default_factory=dict)
    
    # Traffic allocation (0-100)
    traffic_percentage: float = 50.0
    
    # Results
    impressions: int = 0
    conversions: int = 0
    total_revenue: float = 0.0
    
    # Calculated metrics
    conversion_rate: float = 0.0
    revenue_per_impression: float = 0.0
    
    def update_metrics(self):
        """Recalculate metrics based on current data."""
        if self.impressions > 0:
            self.conversion_rate = self.conversions / self.impressions
            self.revenue_per_impression = self.total_revenue / self.impressions
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "config": self.config,
            "traffic_percentage": self.traffic_percentage,
            "impressions": self.impressions,
            "conversions": self.conversions,
            "total_revenue": self.total_revenue,
            "conversion_rate": self.conversion_rate,
            "revenue_per_impression": self.revenue_per_impression
        }


@dataclass
class ABTestExperiment:
    """An A/B test experiment."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    
    # What is being tested
    test_type: str = "ranking"  # ranking, recommendation, alternative, constraint
    target_component: str = ""  # Agent or component being tested
    
    # Variants
    control: ABTestVariant = field(default_factory=lambda: ABTestVariant(
        id="control", name="Control", description="Original behavior"
    ))
    treatment: ABTestVariant = field(default_factory=lambda: ABTestVariant(
        id="treatment", name="Treatment", description="New behavior"
    ))
    
    # Experiment state
    status: str = "draft"  # draft, running, paused, completed, cancelled
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    # Statistical settings
    min_sample_size: int = 1000
    confidence_level: float = 0.95
    
    # Results
    winner: Optional[str] = None  # control or treatment
    statistical_significance: Optional[float] = None
    lift: Optional[float] = None  # Percentage improvement
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "system"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "test_type": self.test_type,
            "target_component": self.target_component,
            "control": self.control.to_dict(),
            "treatment": self.treatment.to_dict(),
            "status": self.status,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "min_sample_size": self.min_sample_size,
            "confidence_level": self.confidence_level,
            "winner": self.winner,
            "statistical_significance": self.statistical_significance,
            "lift": self.lift,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by
        }


# ==============================================================================
# Metrics and Insights
# ==============================================================================

@dataclass
class MetricValue:
    """A single metric measurement."""
    
    metric_type: MetricType
    value: float
    
    # Dimensions
    user_id: Optional[str] = None
    segment: Optional[str] = None
    agent: Optional[str] = None
    category: Optional[str] = None
    
    # Time context
    timestamp: datetime = field(default_factory=datetime.utcnow)
    time_window: str = "hourly"  # hourly, daily, weekly, monthly
    
    # Comparison
    previous_value: Optional[float] = None
    change_percentage: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_type": self.metric_type.value,
            "value": self.value,
            "user_id": self.user_id,
            "segment": self.segment,
            "agent": self.agent,
            "category": self.category,
            "timestamp": self.timestamp.isoformat(),
            "time_window": self.time_window,
            "previous_value": self.previous_value,
            "change_percentage": self.change_percentage
        }


@dataclass
class LearningInsight:
    """An insight generated by the learning system."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Insight details
    insight_type: str = "observation"  # observation, recommendation, alert, trend
    title: str = ""
    description: str = ""
    
    # Impact
    severity: str = "info"  # info, low, medium, high, critical
    potential_impact: Optional[str] = None
    
    # Supporting data
    metrics: List[MetricValue] = field(default_factory=list)
    affected_users: int = 0
    affected_segments: List[str] = field(default_factory=list)
    
    # Actionability
    recommended_action: Optional[str] = None
    auto_actionable: bool = False
    
    # Timestamps
    generated_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    acknowledged: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "insight_type": self.insight_type,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "potential_impact": self.potential_impact,
            "metrics": [m.to_dict() for m in self.metrics],
            "affected_users": self.affected_users,
            "affected_segments": self.affected_segments,
            "recommended_action": self.recommended_action,
            "auto_actionable": self.auto_actionable,
            "generated_at": self.generated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "acknowledged": self.acknowledged
        }


# ==============================================================================
# Query Learning Models
# ==============================================================================

@dataclass
class QueryProductMapping:
    """Mapping from query patterns to successful products."""
    
    query_pattern: str  # Normalized query or pattern
    product_ids: List[str] = field(default_factory=list)
    
    # Success metrics
    click_count: int = 0
    cart_count: int = 0
    purchase_count: int = 0
    
    # Derived score
    success_score: float = 0.0
    
    # Timestamps
    first_seen: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def calculate_score(self):
        """Calculate success score based on engagement."""
        # Weighted score: purchases > carts > clicks
        self.success_score = (
            self.click_count * 1.0 +
            self.cart_count * 3.0 +
            self.purchase_count * 10.0
        )


@dataclass 
class AlternativeEffectiveness:
    """Tracks effectiveness of alternative product suggestions."""
    
    original_product_id: str
    alternative_product_id: str
    
    # Contexts where this alternative was shown
    price_difference: float = 0.0
    category_match: bool = True
    feature_overlap_score: float = 0.0
    
    # User reactions
    times_shown: int = 0
    times_clicked: int = 0
    times_accepted: int = 0  # User chose alternative over original
    times_rejected: int = 0
    
    # Calculated metrics
    click_rate: float = 0.0
    acceptance_rate: float = 0.0
    
    def update_metrics(self):
        """Update calculated metrics."""
        if self.times_shown > 0:
            self.click_rate = self.times_clicked / self.times_shown
        if self.times_clicked > 0:
            self.acceptance_rate = self.times_accepted / self.times_clicked
