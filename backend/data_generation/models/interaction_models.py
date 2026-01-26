"""
Pydantic models for User Interaction data.

These models define user interactions including searches, clicks, cart actions,
and purchases with session tracking and financial context.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, field_validator
import uuid


class SearchContext(BaseModel):
    """Context for search interactions."""
    
    query: str = Field(..., min_length=1, max_length=500)
    query_type: str = Field(
        default="product_search",
        description="product_search, category_browse, brand_search, vague_intent"
    )
    
    # Parsed intent (what the agent understood)
    detected_category: Optional[str] = None
    detected_price_range: Optional[tuple] = None
    detected_intent: Optional[str] = None  # "gift", "self_use", "comparison", "research"
    
    # Search parameters used
    filters_applied: Dict[str, Any] = Field(default_factory=dict)
    sort_by: Optional[str] = None
    page_number: int = Field(default=1, ge=1)
    results_per_page: int = Field(default=20, ge=1, le=100)
    
    # Results metadata
    total_results: int = Field(default=0, ge=0)
    results_returned: int = Field(default=0, ge=0)
    
    @field_validator('query_type')
    @classmethod
    def validate_query_type(cls, v: str) -> str:
        valid = ["product_search", "category_browse", "brand_search", "vague_intent", "comparison"]
        if v not in valid:
            raise ValueError(f"query_type must be one of {valid}")
        return v


class ViewContext(BaseModel):
    """Context for product view interactions."""
    
    product_id: str = Field(...)
    product_title: str = Field(...)
    product_price: float = Field(..., gt=0)
    product_category: str = Field(...)
    
    # View details
    time_spent_seconds: int = Field(default=0, ge=0)
    scroll_depth: float = Field(default=0.0, ge=0, le=1)  # 0-1 of page scrolled
    viewed_reviews: bool = Field(default=False)
    viewed_similar_products: bool = Field(default=False)
    compared_with_products: List[str] = Field(default_factory=list)
    
    # Source of view
    source: str = Field(default="search")  # search, recommendation, direct, ad, wishlist


class CartContext(BaseModel):
    """Context for cart-related interactions."""
    
    product_id: str = Field(...)
    product_title: str = Field(...)
    product_price: float = Field(..., gt=0)
    product_category: str = Field(...)
    
    quantity: int = Field(default=1, ge=1)
    cart_total_before: float = Field(default=0.0, ge=0)
    cart_total_after: float = Field(default=0.0, ge=0)
    cart_item_count: int = Field(default=0, ge=0)
    
    # For removals
    removal_reason: Optional[str] = None  # "too_expensive", "found_better", "changed_mind"


class PurchaseContext(BaseModel):
    """Context for purchase interactions."""
    
    order_id: str = Field(default_factory=lambda: f"ord_{uuid.uuid4().hex[:12]}")
    
    # Products purchased
    products: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Order totals
    subtotal: float = Field(..., gt=0)
    discount_amount: float = Field(default=0.0, ge=0)
    tax_amount: float = Field(default=0.0, ge=0)
    shipping_amount: float = Field(default=0.0, ge=0)
    total_amount: float = Field(..., gt=0)
    
    # Payment
    payment_method: str = Field(...)
    used_installments: bool = Field(default=False)
    installment_plan: Optional[str] = None  # "3_months", "6_months", "12_months"
    
    # Discounts
    coupon_code: Optional[str] = None
    promo_applied: Optional[str] = None


class WishlistContext(BaseModel):
    """Context for wishlist interactions."""
    
    product_id: str = Field(...)
    product_title: str = Field(...)
    product_price: float = Field(..., gt=0)
    product_category: str = Field(...)
    
    action: str = Field(...)  # "add", "remove"
    wishlist_size_after: int = Field(default=0, ge=0)
    price_alert_set: bool = Field(default=False)
    target_price: Optional[float] = None  # For price alerts


class FinancialSnapshot(BaseModel):
    """User's financial context at time of interaction."""
    
    budget_remaining: float = Field(..., ge=0)
    monthly_spent: float = Field(default=0.0, ge=0)
    affordability_for_item: Optional[float] = Field(None, ge=0, le=1)
    payment_method_available: List[str] = Field(default_factory=list)
    installment_eligible: bool = Field(default=False)


class UserInteraction(BaseModel):
    """Complete interaction model for the user_interactions collection."""
    
    # Core identifiers
    id: str = Field(default_factory=lambda: f"int_{uuid.uuid4()}")
    user_id: str = Field(..., description="Reference to user_profiles collection")
    session_id: str = Field(..., description="Groups interactions in a session")
    
    # Interaction type
    interaction_type: str = Field(
        ...,
        description="search, view, click, add_to_cart, remove_from_cart, purchase, wishlist"
    )
    
    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Type-specific context (only one should be populated)
    search_context: Optional[SearchContext] = None
    view_context: Optional[ViewContext] = None
    cart_context: Optional[CartContext] = None
    purchase_context: Optional[PurchaseContext] = None
    wishlist_context: Optional[WishlistContext] = None
    
    # Financial context at time of interaction
    financial_snapshot: Optional[FinancialSnapshot] = None
    
    # Session metadata
    device_type: str = Field(default="desktop")  # desktop, mobile, tablet
    session_interaction_number: int = Field(default=1, ge=1)
    time_since_session_start_seconds: int = Field(default=0, ge=0)
    
    # Outcome (populated later for ML)
    led_to_conversion: Optional[bool] = None
    
    # Embedding for query/text (searches)
    query_embedding: Optional[List[float]] = None
    
    @field_validator('interaction_type')
    @classmethod
    def validate_interaction_type(cls, v: str) -> str:
        valid = [
            "search", "view", "click", "add_to_cart", 
            "remove_from_cart", "purchase", "wishlist"
        ]
        if v not in valid:
            raise ValueError(f"interaction_type must be one of {valid}")
        return v
    
    @field_validator('device_type')
    @classmethod
    def validate_device_type(cls, v: str) -> str:
        valid = ["desktop", "mobile", "tablet"]
        if v not in valid:
            raise ValueError(f"device_type must be one of {valid}")
        return v
    
    def get_product_id(self) -> Optional[str]:
        """Extract product_id from interaction context."""
        if self.view_context:
            return self.view_context.product_id
        if self.cart_context:
            return self.cart_context.product_id
        if self.wishlist_context:
            return self.wishlist_context.product_id
        return None
    
    def get_embedding_text(self) -> Optional[str]:
        """Generate text for embedding (mainly for searches)."""
        if self.search_context:
            return self.search_context.query
        if self.view_context:
            return f"Viewing {self.view_context.product_title} in {self.view_context.product_category}"
        return None
    
    def to_qdrant_point(self) -> Dict[str, Any]:
        """Convert to Qdrant point format."""
        payload = self.model_dump(exclude={"query_embedding", "id"})
        
        # Flatten key fields for indexing
        payload["timestamp_iso"] = self.timestamp.isoformat()
        
        # Add product_id at top level for filtering
        product_id = self.get_product_id()
        if product_id:
            payload["product_id"] = product_id
        
        # Add price if available
        if self.view_context:
            payload["product_price"] = self.view_context.product_price
            payload["product_category"] = self.view_context.product_category
        elif self.cart_context:
            payload["product_price"] = self.cart_context.product_price
            payload["product_category"] = self.cart_context.product_category
        
        # Add search query at top level
        if self.search_context:
            payload["search_query"] = self.search_context.query
        
        return {
            "id": self.id,
            "vector": self.query_embedding or [],
            "payload": payload
        }


class SessionSummary(BaseModel):
    """Summary of a user session for analytics."""
    
    session_id: str = Field(...)
    user_id: str = Field(...)
    
    # Timing
    started_at: datetime = Field(...)
    ended_at: datetime = Field(...)
    duration_seconds: int = Field(default=0, ge=0)
    
    # Activity
    total_interactions: int = Field(default=0, ge=0)
    searches: int = Field(default=0, ge=0)
    product_views: int = Field(default=0, ge=0)
    cart_additions: int = Field(default=0, ge=0)
    purchases: int = Field(default=0, ge=0)
    
    # Products
    unique_products_viewed: int = Field(default=0, ge=0)
    unique_categories_browsed: int = Field(default=0, ge=0)
    
    # Conversion
    converted: bool = Field(default=False)
    revenue: float = Field(default=0.0, ge=0)
    
    # Device
    device_type: str = Field(default="desktop")
