"""
Pydantic models for Product data.

These models ensure data validation and provide serialization
for the products collection in Qdrant.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator
import uuid


class ProductAttributes(BaseModel):
    """Dynamic attributes that vary by product category."""
    
    # Common attributes
    color: Optional[str] = None
    size: Optional[str] = None
    material: Optional[str] = None
    
    # Electronics
    brand: Optional[str] = None
    model: Optional[str] = None
    processor: Optional[str] = None
    ram: Optional[str] = None
    storage: Optional[str] = None
    screen_size: Optional[str] = None
    battery_life: Optional[str] = None
    connectivity: Optional[List[str]] = None
    
    # Fashion
    style: Optional[str] = None
    fit: Optional[str] = None
    season: Optional[str] = None
    gender: Optional[str] = None
    
    # Home & Kitchen
    dimensions: Optional[str] = None
    weight: Optional[str] = None
    capacity: Optional[str] = None
    wattage: Optional[str] = None
    
    # Books
    author: Optional[str] = None
    publisher: Optional[str] = None
    pages: Optional[int] = None
    isbn: Optional[str] = None
    format: Optional[str] = None
    language: Optional[str] = None
    genre: Optional[str] = None
    
    # Sports
    sport_type: Optional[str] = None
    skill_level: Optional[str] = None
    
    # Beauty
    skin_type: Optional[str] = None
    ingredients: Optional[List[str]] = None
    volume: Optional[str] = None
    scent: Optional[str] = None
    
    class Config:
        extra = "allow"  # Allow additional dynamic attributes


class Product(BaseModel):
    """Product model for the products collection."""
    
    # Core identifiers
    id: str = Field(default_factory=lambda: f"prod_{uuid.uuid4()}")
    
    # Product information
    title: str = Field(..., min_length=10, max_length=500)
    description: str = Field(..., min_length=50, max_length=5000)
    category: str = Field(...)
    subcategory: str = Field(...)
    brand: str = Field(...)
    
    # Pricing
    price: float = Field(..., gt=0)
    original_price: Optional[float] = Field(None, gt=0)
    currency: str = Field(default="USD")
    
    # Attributes
    attributes: ProductAttributes = Field(default_factory=ProductAttributes)
    
    # Media
    image_url: str = Field(...)
    image_urls: Optional[List[str]] = None  # Additional images
    
    # Availability
    stock_status: str = Field(default="in_stock")
    stock_quantity: Optional[int] = Field(None, ge=0)
    
    # Payment options
    payment_options: List[str] = Field(default_factory=lambda: ["credit", "debit"])
    
    # Review summary (denormalized)
    rating_avg: float = Field(default=0.0, ge=0, le=5)
    review_count: int = Field(default=0, ge=0)
    
    # Discovery
    tags: List[str] = Field(default_factory=list)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    # Embedding (populated after generation)
    embedding: Optional[List[float]] = None
    image_embedding: Optional[List[float]] = None
    
    @field_validator('stock_status')
    @classmethod
    def validate_stock_status(cls, v: str) -> str:
        valid_statuses = ["in_stock", "low_stock", "out_of_stock", "preorder"]
        if v not in valid_statuses:
            raise ValueError(f"stock_status must be one of {valid_statuses}")
        return v
    
    @field_validator('payment_options')
    @classmethod
    def validate_payment_options(cls, v: List[str]) -> List[str]:
        valid_options = ["credit", "debit", "bnpl", "financing", "paypal", "crypto"]
        for option in v:
            if option not in valid_options:
                raise ValueError(f"Invalid payment option: {option}. Must be one of {valid_options}")
        return v
    
    def get_embedding_text(self) -> str:
        """Generate text for embedding creation."""
        parts = [
            self.title,
            self.description,
            f"Category: {self.category}",
            f"Subcategory: {self.subcategory}",
            f"Brand: {self.brand}",
        ]
        if self.tags:
            parts.append(f"Tags: {', '.join(self.tags)}")
        return ". ".join(parts)
    
    def to_qdrant_point(self) -> Dict[str, Any]:
        """Convert to Qdrant point format."""
        payload = self.model_dump(exclude={"embedding", "image_embedding"})
        # Convert datetime to ISO string for JSON serialization
        payload["created_at"] = self.created_at.isoformat()
        if payload["updated_at"]:
            payload["updated_at"] = self.updated_at.isoformat()
        # Convert attributes to dict
        payload["attributes"] = self.attributes.model_dump(exclude_none=True)
        
        # Build vector(s) - support named vectors for multimodal
        if self.image_embedding:
            # Use named vectors when both text and image embeddings exist
            vectors = {
                "text_vector": self.embedding,
                "image_vector": self.image_embedding
            }
        else:
            # Single unnamed vector for text-only
            vectors = self.embedding
        
        return {
            "id": self.id,
            "vector": vectors,
            "payload": payload
        }
    
    def to_qdrant_point_single_vector(self) -> Dict[str, Any]:
        """Convert to Qdrant point format with single vector (text only)."""
        payload = self.model_dump(exclude={"embedding", "image_embedding"})
        payload["created_at"] = self.created_at.isoformat()
        if payload["updated_at"]:
            payload["updated_at"] = self.updated_at.isoformat()
        payload["attributes"] = self.attributes.model_dump(exclude_none=True)
        
        return {
            "id": self.id,
            "vector": self.embedding,
            "payload": payload
        }
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
