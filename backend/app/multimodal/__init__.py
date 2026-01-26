"""
Multi-modal capabilities for FinFind.

This module provides image search and voice input features:
- Image embedding generation using CLIP/OpenCLIP
- Image similarity search against product images
- Voice-to-text conversion using Whisper
- Multi-language voice support

Components:
- ImageProcessor: CLIP-based image embedding and search
- VoiceProcessor: Whisper-based speech recognition
- MultimodalService: Unified service for multimodal operations
"""

from .config import (
    MultimodalConfig,
    ImageConfig,
    VoiceConfig,
    get_multimodal_config
)
from .schemas import (
    # Image schemas
    ImageSearchRequest,
    ImageSearchResponse,
    ImageEmbeddingResult,
    ImageSearchResult,
    SimilarProduct,
    # Voice schemas
    VoiceSearchRequest,
    VoiceSearchResponse,
    VoiceTranscriptionResult,
    # Common schemas
    MultimodalError,
    MultimodalErrorCode
)
from .image_processor import (
    ImageProcessor,
    get_image_processor
)
from .voice_processor import (
    VoiceProcessor,
    get_voice_processor
)

__all__ = [
    # Config
    "MultimodalConfig",
    "ImageConfig",
    "VoiceConfig",
    "get_multimodal_config",
    # Image schemas
    "ImageSearchRequest",
    "ImageSearchResponse",
    "ImageEmbeddingResult",
    "ImageSearchResult",
    "SimilarProduct",
    # Voice schemas
    "VoiceSearchRequest",
    "VoiceSearchResponse",
    "VoiceTranscriptionResult",
    # Common schemas
    "MultimodalError",
    "MultimodalErrorCode",
    # Processors
    "ImageProcessor",
    "get_image_processor",
    "VoiceProcessor",
    "get_voice_processor",
]
