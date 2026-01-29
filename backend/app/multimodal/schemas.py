"""
Pydantic schemas for multimodal operations.

Defines request/response models for image and voice processing.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ==============================================================================
# Error Handling
# ==============================================================================

class MultimodalErrorCode(str, Enum):
    """Error codes for multimodal operations."""
    # Image errors
    IMAGE_TOO_LARGE = "image_too_large"
    INVALID_IMAGE_FORMAT = "invalid_image_format"
    IMAGE_PROCESSING_FAILED = "image_processing_failed"
    IMAGE_EMBEDDING_FAILED = "image_embedding_failed"
    IMAGE_CORRUPTED = "image_corrupted"
    
    # Voice errors
    AUDIO_TOO_LONG = "audio_too_long"
    AUDIO_TOO_LARGE = "audio_too_large"
    INVALID_AUDIO_FORMAT = "invalid_audio_format"
    TRANSCRIPTION_FAILED = "transcription_failed"
    LANGUAGE_NOT_SUPPORTED = "language_not_supported"
    AUDIO_CORRUPTED = "audio_corrupted"
    
    # General errors
    SERVICE_UNAVAILABLE = "service_unavailable"
    RATE_LIMITED = "rate_limited"
    INTERNAL_ERROR = "internal_error"
    FEATURE_DISABLED = "feature_disabled"


class MultimodalError(BaseModel):
    """Error response for multimodal operations."""
    code: MultimodalErrorCode
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ==============================================================================
# Image Search Schemas
# ==============================================================================

class ImageSearchRequest(BaseModel):
    """Request for image-based product search."""
    # Image can be provided as base64 or via file upload
    image_base64: Optional[str] = Field(
        default=None,
        description="Base64-encoded image data"
    )
    image_url: Optional[str] = Field(
        default=None,
        description="URL to fetch image from"
    )
    
    # Search parameters
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of results"
    )
    score_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score"
    )
    
    # Financial filters
    max_price: Optional[float] = Field(
        default=None,
        ge=0,
        description="Maximum price filter"
    )
    min_price: Optional[float] = Field(
        default=None,
        ge=0,
        description="Minimum price filter"
    )
    
    # Category filters
    categories: Optional[List[str]] = Field(
        default=None,
        description="Filter by product categories"
    )
    
    # User context
    user_id: Optional[str] = Field(
        default=None,
        description="User ID for personalization"
    )
    
    # Diversity settings
    use_mmr: bool = Field(
        default=True,
        description="Use MMR for diverse results"
    )
    diversity_factor: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Diversity factor for MMR"
    )


class ImageEmbeddingResult(BaseModel):
    """Result of image embedding generation."""
    embedding: List[float]
    dimension: int
    model_used: str
    processing_time_ms: float
    image_size: Optional[tuple] = Field(
        default=None,
        description="Original image dimensions (width, height)"
    )


class SimilarProduct(BaseModel):
    """A similar product found via image search."""
    product_id: str
    name: str
    description: Optional[str] = None
    price: float
    category: str
    
    # Similarity info
    similarity_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Visual similarity score"
    )
    
    # Ranking info
    ranking_score: Optional[float] = Field(
        default=None,
        description="Combined ranking score"
    )
    rank: Optional[int] = Field(
        default=None,
        description="Position in ranked results"
    )
    
    # Visual match details
    visual_match_reasons: Optional[List[str]] = Field(
        default=None,
        description="Reasons for visual similarity"
    )
    
    # Product details
    image_url: Optional[str] = None
    brand: Optional[str] = None
    rating: Optional[float] = None
    
    # Financial context
    price_comparison: Optional[str] = Field(
        default=None,
        description="Price comparison to search context"
    )
    affordability_score: Optional[float] = Field(
        default=None,
        description="Affordability score if user context provided"
    )


class ImageSearchResult(BaseModel):
    """Complete result of image search."""
    products: List[SimilarProduct]
    total_found: int
    
    # Search metadata
    embedding_time_ms: float
    search_time_ms: float
    total_time_ms: float
    
    # Query info
    filters_applied: Dict[str, Any]
    diversity_used: bool
    
    # Helpful context
    search_summary: Optional[str] = Field(
        default=None,
        description="Natural language summary of search"
    )


class ImageSearchResponse(BaseModel):
    """API response for image search."""
    success: bool
    result: Optional[ImageSearchResult] = None
    error: Optional[MultimodalError] = None
    request_id: str = Field(
        description="Unique request identifier for tracking"
    )


# ==============================================================================
# Voice Input Schemas
# ==============================================================================

class VoiceSearchRequest(BaseModel):
    """Request for voice-based search."""
    # Audio can be provided as base64 or via file upload
    audio_base64: Optional[str] = Field(
        default=None,
        description="Base64-encoded audio data"
    )
    audio_format: str = Field(
        default="wav",
        description="Audio format (wav, mp3, m4a, etc.)"
    )
    
    # Language settings
    language: Optional[str] = Field(
        default=None,
        description="Language code (e.g., 'en', 'es'). None for auto-detect"
    )
    translate_to_english: bool = Field(
        default=False,
        description="Translate non-English to English"
    )
    
    # Processing options
    include_timestamps: bool = Field(
        default=False,
        description="Include word-level timestamps"
    )
    
    # Search parameters (applied after transcription)
    auto_search: bool = Field(
        default=True,
        description="Automatically search after transcription"
    )
    search_limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum search results"
    )
    
    # User context
    user_id: Optional[str] = Field(
        default=None,
        description="User ID for personalization"
    )
    
    # Financial context
    max_budget: Optional[float] = Field(
        default=None,
        description="Maximum budget for search"
    )


class WordTimestamp(BaseModel):
    """Timestamp for a transcribed word."""
    word: str
    start: float = Field(description="Start time in seconds")
    end: float = Field(description="End time in seconds")
    confidence: Optional[float] = Field(
        default=None,
        description="Confidence score for this word"
    )


class VoiceTranscriptionResult(BaseModel):
    """Result of voice transcription."""
    text: str = Field(description="Transcribed text")
    
    # Language detection
    detected_language: str = Field(
        description="Detected or specified language code"
    )
    language_confidence: Optional[float] = Field(
        default=None,
        description="Confidence in language detection"
    )
    
    # Translation (if requested)
    original_text: Optional[str] = Field(
        default=None,
        description="Original text before translation"
    )
    was_translated: bool = Field(
        default=False,
        description="Whether translation was performed"
    )
    
    # Timestamps (if requested)
    word_timestamps: Optional[List[WordTimestamp]] = None
    
    # Processing metadata
    audio_duration_seconds: float
    processing_time_ms: float
    model_used: str
    
    # Confidence
    overall_confidence: Optional[float] = Field(
        default=None,
        description="Overall transcription confidence"
    )


class VoiceSearchResponse(BaseModel):
    """API response for voice search."""
    success: bool
    
    # Transcription result
    transcription: Optional[VoiceTranscriptionResult] = None
    
    # Search results (if auto_search was True)
    search_results: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Search results from transcribed query"
    )
    
    # Error handling
    error: Optional[MultimodalError] = None
    
    # Request tracking
    request_id: str
    
    # User-friendly summary
    summary: Optional[str] = Field(
        default=None,
        description="Summary of what was understood and found"
    )


# ==============================================================================
# Combined Multimodal Request/Response
# ==============================================================================

class MultimodalSearchRequest(BaseModel):
    """Combined request that can include both image and voice."""
    # Image input
    image: Optional[ImageSearchRequest] = None
    
    # Voice input
    voice: Optional[VoiceSearchRequest] = None
    
    # Combined search parameters
    combine_results: bool = Field(
        default=False,
        description="Combine image and voice search results"
    )
    
    # User context
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    # Financial constraints
    max_budget: Optional[float] = None
    
    # Agent routing
    prefer_agent: Optional[str] = Field(
        default=None,
        description="Preferred agent for processing"
    )


class MultimodalSearchResponse(BaseModel):
    """Combined response for multimodal search."""
    success: bool
    
    # Individual results
    image_result: Optional[ImageSearchResponse] = None
    voice_result: Optional[VoiceSearchResponse] = None
    
    # Combined results
    combined_products: Optional[List[SimilarProduct]] = None
    
    # Error
    error: Optional[MultimodalError] = None
    
    # Metadata
    request_id: str
    processing_time_ms: float
    
    # Natural language summary
    summary: str = Field(
        description="Human-readable summary of multimodal search"
    )


# ==============================================================================
# Internal Processing Schemas
# ==============================================================================

class ProcessedImage(BaseModel):
    """Internally processed image data."""
    original_size: tuple
    processed_size: tuple
    format: str
    file_size_bytes: int
    is_valid: bool
    error_message: Optional[str] = None


class ProcessedAudio(BaseModel):
    """Internally processed audio data."""
    duration_seconds: float
    sample_rate: int
    channels: int
    format: str
    file_size_bytes: int
    is_valid: bool
    error_message: Optional[str] = None
