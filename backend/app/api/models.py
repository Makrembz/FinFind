"""
Pydantic models for API requests and responses.

Organized by domain:
- Search models
- User models
- Product models
- Recommendation models
- Agent/Chat models
- Common models
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, field_validator
import uuid


# ==============================================================================
# Enums
# ==============================================================================

class InteractionType(str, Enum):
    """Types of user-product interactions."""
    VIEW = "view"
    CLICK = "click"
    ADD_TO_CART = "add_to_cart"
    REMOVE_FROM_CART = "remove_from_cart"
    PURCHASE = "purchase"
    WISHLIST = "wishlist"
    REVIEW = "review"
    SHARE = "share"


class SortOrder(str, Enum):
    """Sort order options."""
    RELEVANCE = "relevance"
    PRICE_LOW = "price_low"
    PRICE_HIGH = "price_high"
    RATING = "rating"
    NEWEST = "newest"
    POPULARITY = "popularity"


class AgentType(str, Enum):
    """Available agent types."""
    SEARCH = "search"
    RECOMMENDATION = "recommendation"
    EXPLAINABILITY = "explainability"
    ALTERNATIVE = "alternative"


# ==============================================================================
# Common Models
# ==============================================================================

class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SuccessResponse(BaseModel):
    """Standard success response."""
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None


# ==============================================================================
# Search Models
# ==============================================================================

class PriceRange(BaseModel):
    """Price range filter."""
    min: Optional[float] = Field(default=None, ge=0)
    max: Optional[float] = Field(default=None, ge=0)
    
    @field_validator("max")
    @classmethod
    def max_greater_than_min(cls, v, info):
        if v is not None and info.data.get("min") is not None:
            if v < info.data["min"]:
                raise ValueError("max must be greater than min")
        return v


class SearchFilters(BaseModel):
    """Search filter parameters."""
    categories: Optional[List[str]] = None
    brands: Optional[List[str]] = None
    price_range: Optional[PriceRange] = None
    min_rating: Optional[float] = Field(default=None, ge=0, le=5)
    in_stock: Optional[bool] = None
    payment_methods: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class SearchRequest(BaseModel):
    """Text-based search request."""
    query: str = Field(..., min_length=1, max_length=500)
    filters: Optional[SearchFilters] = None
    sort: SortOrder = Field(default=SortOrder.RELEVANCE)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=50)
    use_mmr: bool = Field(default=True, description="Use MMR for diversity")
    diversity: float = Field(default=0.3, ge=0.0, le=1.0)
    include_explanation: bool = Field(default=False)
    user_id: Optional[str] = Field(default=None, description="User ID for personalization")


class VoiceSearchRequest(BaseModel):
    """Voice-based search request (for JSON body)."""
    audio_base64: str = Field(..., description="Base64-encoded audio data")
    audio_format: str = Field(default="wav", description="Audio format")
    language: Optional[str] = Field(default=None, description="Language code or None for auto-detect")
    filters: Optional[SearchFilters] = None
    page_size: int = Field(default=20, ge=1, le=50)
    user_id: Optional[str] = None


class ImageSearchRequest(BaseModel):
    """Image-based search request (for JSON body)."""
    image_base64: Optional[str] = Field(default=None, description="Base64-encoded image")
    image_url: Optional[str] = Field(default=None, description="URL to fetch image")
    filters: Optional[SearchFilters] = None
    page_size: int = Field(default=20, ge=1, le=50)
    user_id: Optional[str] = None


class ProductSearchResult(BaseModel):
    """Single product in search results."""
    id: str
    name: str
    description: Optional[str] = None
    price: float
    original_price: Optional[float] = None
    category: str
    subcategory: Optional[str] = None
    brand: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    image_url: Optional[str] = None
    in_stock: bool = True
    relevance_score: float
    match_explanation: Optional[str] = None


class SearchResponse(BaseModel):
    """Search response."""
    success: bool = True
    query: str
    interpreted_query: Optional[str] = None
    products: List[ProductSearchResult]
    total_results: int
    page: int
    page_size: int
    total_pages: int
    filters_applied: Dict[str, Any]
    search_time_ms: float
    request_id: str


class SuggestionResponse(BaseModel):
    """Auto-complete suggestions response."""
    suggestions: List[str]
    categories: List[str] = []
    popular_searches: List[str] = []
    request_id: str


# ==============================================================================
# User Models
# ==============================================================================

class FinancialProfile(BaseModel):
    """User financial profile."""
    monthly_income: Optional[float] = Field(default=None, ge=0)
    monthly_budget: Optional[float] = Field(default=None, ge=0)
    credit_score_range: Optional[str] = None  # "poor", "fair", "good", "excellent"
    preferred_payment_methods: List[str] = Field(default_factory=list)
    risk_tolerance: Optional[str] = None  # "conservative", "moderate", "aggressive"
    savings_goal: Optional[float] = Field(default=None, ge=0)


class UserPreferences(BaseModel):
    """User shopping preferences."""
    favorite_categories: List[str] = Field(default_factory=list)
    favorite_brands: List[str] = Field(default_factory=list)
    price_sensitivity: Optional[str] = None  # "low", "medium", "high"
    quality_preference: Optional[str] = None  # "budget", "mid-range", "premium"
    eco_friendly: bool = False
    local_preference: bool = False


class UserProfile(BaseModel):
    """Complete user profile."""
    user_id: str
    email: Optional[str] = None
    name: Optional[str] = None
    financial_profile: FinancialProfile = Field(default_factory=FinancialProfile)
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class UserProfileUpdate(BaseModel):
    """User profile update request."""
    name: Optional[str] = None
    financial_profile: Optional[FinancialProfile] = None
    preferences: Optional[UserPreferences] = None


class UserProfileResponse(BaseModel):
    """User profile response."""
    success: bool = True
    profile: UserProfile
    request_id: str


class UserInteraction(BaseModel):
    """User interaction record."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    product_id: str
    interaction_type: InteractionType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None


class InteractionRequest(BaseModel):
    """Request to log an interaction."""
    interaction_type: InteractionType
    metadata: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None


class InteractionHistoryResponse(BaseModel):
    """User interaction history response."""
    success: bool = True
    user_id: str
    interactions: List[UserInteraction]
    total: int
    page: int
    page_size: int
    request_id: str


# ==============================================================================
# Product Models
# ==============================================================================

class ProductAttributes(BaseModel):
    """Dynamic product attributes."""
    color: Optional[str] = None
    size: Optional[str] = None
    material: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    weight: Optional[str] = None
    dimensions: Optional[str] = None
    # Allow additional attributes
    extra: Dict[str, Any] = Field(default_factory=dict)


class ProductDetail(BaseModel):
    """Detailed product information."""
    id: str
    name: str
    description: str
    category: str
    subcategory: Optional[str] = None
    brand: str
    price: float
    original_price: Optional[float] = None
    currency: str = "USD"
    attributes: ProductAttributes = Field(default_factory=ProductAttributes)
    image_url: str
    image_urls: List[str] = Field(default_factory=list)
    in_stock: bool = True
    stock_quantity: Optional[int] = None
    payment_options: List[str] = Field(default_factory=list)
    rating_avg: float = 0.0
    review_count: int = 0
    tags: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: Optional[datetime] = None


class ProductResponse(BaseModel):
    """Product detail response."""
    success: bool = True
    product: ProductDetail
    similar_products: List[ProductSearchResult] = Field(default_factory=list)
    request_id: str


class ProductReview(BaseModel):
    """Product review."""
    id: str
    user_id: str
    product_id: str
    rating: float = Field(ge=1, le=5)
    title: Optional[str] = None
    content: str
    helpful_count: int = 0
    verified_purchase: bool = False
    created_at: datetime
    user_name: Optional[str] = None


class ReviewsResponse(BaseModel):
    """Product reviews response."""
    success: bool = True
    product_id: str
    reviews: List[ProductReview]
    total: int
    average_rating: float
    rating_distribution: Dict[str, int]  # "5": 100, "4": 50, etc.
    page: int
    page_size: int
    request_id: str


# ==============================================================================
# Recommendation Models
# ==============================================================================

class RecommendationContext(BaseModel):
    """Context for generating recommendations."""
    occasion: Optional[str] = None  # "birthday", "holiday", etc.
    budget_strict: bool = False
    exclude_categories: List[str] = Field(default_factory=list)
    exclude_products: List[str] = Field(default_factory=list)
    prefer_new: bool = False
    prefer_deals: bool = False


class RecommendationRequest(BaseModel):
    """Request for recommendations."""
    user_id: str
    context: Optional[RecommendationContext] = None
    limit: int = Field(default=10, ge=1, le=50)
    include_explanation: bool = Field(default=True)


class RecommendedProduct(BaseModel):
    """Recommended product with explanation."""
    product: ProductSearchResult
    recommendation_score: float
    recommendation_reason: str
    affordability_score: Optional[float] = None
    personalization_factors: List[str] = Field(default_factory=list)


class RecommendationResponse(BaseModel):
    """Recommendations response."""
    success: bool = True
    user_id: str
    recommendations: List[RecommendedProduct]
    personalization_summary: Optional[str] = None
    request_id: str


class ExplainRequest(BaseModel):
    """Request explanation for a recommendation."""
    user_id: str
    product_id: str
    include_alternatives: bool = Field(default=False)
    detail_level: str = Field(default="standard")  # "brief", "standard", "detailed"


class ExplainResponse(BaseModel):
    """Explanation response."""
    success: bool = True
    product_id: str
    explanation: str
    key_factors: List[Dict[str, Any]]
    financial_fit: Dict[str, Any]
    alternatives: List[ProductSearchResult] = Field(default_factory=list)
    request_id: str


class AlternativesRequest(BaseModel):
    """Request for product alternatives."""
    price_range: Optional[str] = None  # "lower", "similar", "higher"
    same_category: bool = Field(default=True)
    limit: int = Field(default=10, ge=1, le=20)
    user_id: Optional[str] = None


class AlternativesResponse(BaseModel):
    """Alternatives response."""
    success: bool = True
    original_product_id: str
    criteria: str = "balanced"
    alternatives: List[ProductSearchResult]
    reasons: Dict[str, str] = Field(default_factory=dict)
    total: int = 0
    request_id: str


class RecommendationResponse(BaseModel):
    """Recommendations response."""
    success: bool = True
    user_id: str
    recommendations: List[ProductSearchResult]
    reasons: Dict[str, List[str]] = Field(default_factory=dict)
    total: int = 0
    request_id: str


class ExplanationRequest(BaseModel):
    """Request explanation for a recommendation."""
    user_id: str
    product_id: str
    include_alternatives: bool = Field(default=False)
    detail_level: str = Field(default="standard")  # "brief", "standard", "detailed"


class ExplanationResponse(BaseModel):
    """Explanation response."""
    success: bool = True
    user_id: str
    product_id: str
    summary: str
    factors: List[Dict[str, Any]]
    factor_scores: Dict[str, float] = Field(default_factory=dict)
    confidence_score: float = 0.0
    request_id: str


# ==============================================================================
# Agent/Chat Models
# ==============================================================================

class ChatMessage(BaseModel):
    """Chat message."""
    role: str = Field(..., description="user or assistant")
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    """Chat request."""
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = Field(default=None)
    user_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    include_products: bool = Field(default=True)
    preferred_agent: Optional[AgentType] = None


class ChatResponse(BaseModel):
    """Chat response."""
    success: bool = True
    message: str
    session_id: str
    agent_used: Optional[str] = None
    products: List[ProductSearchResult] = Field(default_factory=list)
    follow_up_suggestions: List[str] = Field(default_factory=list)
    confidence: Optional[float] = None
    processing_time_ms: float
    request_id: str


class SessionHistory(BaseModel):
    """Conversation session history."""
    session_id: str
    user_id: Optional[str] = None
    messages: List[ChatMessage]
    created_at: datetime
    last_activity: datetime
    context: Dict[str, Any] = Field(default_factory=dict)


class SessionResponse(BaseModel):
    """Session history response."""
    success: bool = True
    session: SessionHistory
    request_id: str


# ==============================================================================
# Health Check Models
# ==============================================================================

class ServiceHealth(BaseModel):
    """Health status of a service."""
    name: str
    status: str  # "healthy", "degraded", "unhealthy"
    latency_ms: Optional[float] = None
    details: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str  # "healthy", "degraded", "unhealthy"
    version: str
    environment: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: List[ServiceHealth] = Field(default_factory=list)
    uptime_seconds: Optional[float] = None
