"""
Pydantic models for User Profile data.

These models define user profiles with financial contexts, preferences,
and behavioral patterns for the FinFind platform.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator, computed_field
import uuid


class FinancialContext(BaseModel):
    """User's financial situation and constraints."""
    
    # Budget information
    budget_min: float = Field(..., ge=0, description="Minimum comfortable spending amount")
    budget_max: float = Field(..., gt=0, description="Maximum comfortable spending amount")
    monthly_discretionary: float = Field(..., ge=0, description="Monthly discretionary income")
    
    # Affordability metrics
    affordability_score: float = Field(
        ..., 
        ge=0, 
        le=1,
        description="0-1 score indicating financial flexibility"
    )
    
    # Risk and spending behavior
    risk_tolerance: str = Field(
        default="moderate",
        description="low, moderate, high - willingness to try new products/brands"
    )
    spending_style: str = Field(
        default="balanced",
        description="frugal, balanced, impulsive - general spending behavior"
    )
    
    # Debt and credit
    has_credit_card: bool = Field(default=True)
    credit_utilization: Optional[float] = Field(
        None, 
        ge=0, 
        le=1,
        description="Current credit utilization ratio"
    )
    prefers_installments: bool = Field(default=False)
    
    @field_validator('risk_tolerance')
    @classmethod
    def validate_risk_tolerance(cls, v: str) -> str:
        valid = ["low", "moderate", "high"]
        if v not in valid:
            raise ValueError(f"risk_tolerance must be one of {valid}")
        return v
    
    @field_validator('spending_style')
    @classmethod
    def validate_spending_style(cls, v: str) -> str:
        valid = ["frugal", "balanced", "impulsive"]
        if v not in valid:
            raise ValueError(f"spending_style must be one of {valid}")
        return v


class UserPreferences(BaseModel):
    """User's shopping preferences and behavior patterns."""
    
    # Category preferences (category -> affinity score 0-1)
    category_affinity: Dict[str, float] = Field(
        default_factory=dict,
        description="Category name to preference score mapping"
    )
    
    # Brand preferences
    preferred_brands: List[str] = Field(
        default_factory=list,
        description="Brands user has shown preference for"
    )
    avoided_brands: List[str] = Field(
        default_factory=list,
        description="Brands user tends to avoid"
    )
    brand_loyalty_score: float = Field(
        default=0.5,
        ge=0,
        le=1,
        description="How likely to stick with known brands"
    )
    
    # Shopping behavior
    price_sensitivity: float = Field(
        default=0.5,
        ge=0,
        le=1,
        description="0=price insensitive, 1=very price sensitive"
    )
    quality_preference: float = Field(
        default=0.5,
        ge=0,
        le=1,
        description="0=basic quality ok, 1=premium only"
    )
    reviews_importance: float = Field(
        default=0.7,
        ge=0,
        le=1,
        description="How much reviews influence decisions"
    )
    
    # Deal seeking
    deal_seeker: bool = Field(default=False)
    waits_for_sales: bool = Field(default=False)
    uses_coupons: bool = Field(default=False)


class PurchaseHistoryItem(BaseModel):
    """Record of a past purchase."""
    
    product_id: str = Field(...)
    category: str = Field(...)
    subcategory: str = Field(...)
    brand: str = Field(...)
    price_paid: float = Field(..., gt=0)
    payment_method: str = Field(...)
    purchased_at: datetime = Field(...)
    was_on_sale: bool = Field(default=False)
    satisfaction_score: Optional[float] = Field(None, ge=0, le=5)


class UserProfile(BaseModel):
    """Complete user profile model for the user_profiles collection."""
    
    # Core identifiers
    id: str = Field(default_factory=lambda: f"user_{uuid.uuid4()}")
    
    # Basic demographics
    persona_type: str = Field(
        ...,
        description="User persona: student, young_professional, family, affluent, senior"
    )
    age_range: str = Field(...)  # "18-24", "25-34", "35-44", "45-54", "55+"
    
    # Financial context
    financial_context: FinancialContext = Field(...)
    
    # Payment preferences
    payment_methods: List[str] = Field(
        ...,
        description="Preferred payment methods: credit_card, debit_card, installments, bnpl, cash"
    )
    primary_payment_method: str = Field(...)
    
    # Shopping preferences
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    
    # Financial goals (affects purchase decisions)
    financial_goals: List[str] = Field(
        default_factory=list,
        description="Current financial goals affecting spending"
    )
    
    # Purchase history (denormalized for recommendations)
    purchase_history: List[PurchaseHistoryItem] = Field(
        default_factory=list,
        max_length=50
    )
    total_lifetime_value: float = Field(default=0.0, ge=0)
    purchase_count: int = Field(default=0, ge=0)
    avg_order_value: float = Field(default=0.0, ge=0)
    
    # Activity metrics
    days_since_last_purchase: Optional[int] = Field(None, ge=0)
    days_since_registration: int = Field(default=0, ge=0)
    session_count: int = Field(default=0, ge=0)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    # Embedding (populated after generation)
    embedding: Optional[List[float]] = None
    
    @field_validator('persona_type')
    @classmethod
    def validate_persona_type(cls, v: str) -> str:
        valid = [
            "student", "young_professional", "family", 
            "affluent", "senior", "budget_conscious", "luxury_shopper"
        ]
        if v not in valid:
            raise ValueError(f"persona_type must be one of {valid}")
        return v
    
    @field_validator('age_range')
    @classmethod
    def validate_age_range(cls, v: str) -> str:
        valid = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
        if v not in valid:
            raise ValueError(f"age_range must be one of {valid}")
        return v
    
    @field_validator('payment_methods')
    @classmethod
    def validate_payment_methods(cls, v: List[str]) -> List[str]:
        valid = ["credit_card", "debit_card", "installments", "bnpl", "cash", "bank_transfer"]
        for method in v:
            if method not in valid:
                raise ValueError(f"Invalid payment method: {method}. Must be one of {valid}")
        return v
    
    def get_embedding_text(self) -> str:
        """Generate text representation for embedding."""
        parts = [
            f"User profile: {self.persona_type}",
            f"Age: {self.age_range}",
            f"Budget: ${self.financial_context.budget_min:.0f} to ${self.financial_context.budget_max:.0f}",
            f"Affordability: {'high' if self.financial_context.affordability_score > 0.7 else 'medium' if self.financial_context.affordability_score > 0.4 else 'low'}",
            f"Risk tolerance: {self.financial_context.risk_tolerance}",
            f"Spending style: {self.financial_context.spending_style}",
            f"Payment preference: {self.primary_payment_method}",
        ]
        
        # Add category preferences
        if self.preferences.category_affinity:
            top_categories = sorted(
                self.preferences.category_affinity.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            parts.append(f"Preferred categories: {', '.join(c[0] for c in top_categories)}")
        
        # Add financial goals
        if self.financial_goals:
            parts.append(f"Financial goals: {', '.join(self.financial_goals[:3])}")
        
        return ". ".join(parts)
    
    def to_qdrant_point(self) -> Dict[str, Any]:
        """Convert to Qdrant point format."""
        payload = self.model_dump(exclude={"embedding", "id"})
        
        # Flatten financial context for indexing
        payload["budget_min"] = self.financial_context.budget_min
        payload["budget_max"] = self.financial_context.budget_max
        payload["affordability_score"] = self.financial_context.affordability_score
        payload["price_sensitivity"] = self.preferences.price_sensitivity
        
        # Convert datetime objects to ISO strings
        payload["created_at"] = self.created_at.isoformat()
        if self.updated_at:
            payload["updated_at"] = self.updated_at.isoformat()
        
        # Convert purchase history dates
        for i, item in enumerate(payload.get("purchase_history", [])):
            if isinstance(item.get("purchased_at"), datetime):
                payload["purchase_history"][i]["purchased_at"] = item["purchased_at"].isoformat()
        
        return {
            "id": self.id,
            "vector": self.embedding or [],
            "payload": payload
        }
