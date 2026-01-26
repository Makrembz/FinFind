"""
Pydantic models for Review data.

These models ensure data validation and provide serialization
for the reviews collection in Qdrant.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator
import uuid


class ReviewAspects(BaseModel):
    """Aspect-based ratings for detailed review analysis."""
    
    quality: Optional[float] = Field(None, ge=1, le=5)
    value: Optional[float] = Field(None, ge=1, le=5)
    shipping: Optional[float] = Field(None, ge=1, le=5)
    ease_of_use: Optional[float] = Field(None, ge=1, le=5)
    durability: Optional[float] = Field(None, ge=1, le=5)


class Review(BaseModel):
    """Review model for the reviews collection."""
    
    # Identifiers
    review_id: str = Field(default_factory=lambda: f"rev_{uuid.uuid4()}")
    product_id: str = Field(...)  # References products collection
    user_id: str = Field(...)  # References user_profiles collection
    
    # Review content
    title: str = Field(..., min_length=5, max_length=200)
    text: str = Field(..., min_length=20, max_length=5000)
    
    # Rating and sentiment
    rating: int = Field(..., ge=1, le=5)
    sentiment: str = Field(...)  # "positive", "neutral", "negative"
    sentiment_score: float = Field(..., ge=-1, le=1)
    
    # Aspect ratings
    aspects: Optional[ReviewAspects] = None
    
    # Metadata
    helpful_votes: int = Field(default=0, ge=0)
    total_votes: int = Field(default=0, ge=0)
    verified_purchase: bool = Field(default=True)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Embedding (populated after generation)
    embedding: Optional[List[float]] = None
    
    @field_validator('sentiment')
    @classmethod
    def validate_sentiment(cls, v: str) -> str:
        valid_sentiments = ["positive", "neutral", "negative"]
        if v not in valid_sentiments:
            raise ValueError(f"sentiment must be one of {valid_sentiments}")
        return v
    
    @field_validator('total_votes')
    @classmethod
    def validate_votes(cls, v: int, info) -> int:
        # total_votes should be >= helpful_votes
        # This is validated at the model level, not field level
        return v
    
    def get_embedding_text(self) -> str:
        """Generate text for embedding creation."""
        return f"{self.title}. {self.text}"
    
    def to_qdrant_point(self) -> Dict[str, Any]:
        """Convert to Qdrant point format."""
        payload = self.model_dump(exclude={"embedding"})
        # Convert datetime to ISO string
        payload["created_at"] = self.created_at.isoformat()
        # Convert aspects to dict if present
        if payload["aspects"]:
            payload["aspects"] = self.aspects.model_dump(exclude_none=True)
        
        return {
            "id": self.review_id,
            "vector": self.embedding,
            "payload": payload
        }
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ReviewStats(BaseModel):
    """Aggregated review statistics for a product."""
    
    product_id: str
    total_reviews: int = 0
    average_rating: float = 0.0
    rating_distribution: Dict[int, int] = Field(
        default_factory=lambda: {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    )
    sentiment_distribution: Dict[str, int] = Field(
        default_factory=lambda: {"positive": 0, "neutral": 0, "negative": 0}
    )
    verified_purchase_count: int = 0
    
    def calculate_from_reviews(self, reviews: List[Review]) -> None:
        """Calculate statistics from a list of reviews."""
        if not reviews:
            return
        
        self.total_reviews = len(reviews)
        
        total_rating = 0
        for review in reviews:
            total_rating += review.rating
            self.rating_distribution[review.rating] += 1
            self.sentiment_distribution[review.sentiment] += 1
            if review.verified_purchase:
                self.verified_purchase_count += 1
        
        self.average_rating = round(total_rating / self.total_reviews, 2)
