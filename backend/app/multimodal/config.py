"""
Configuration for multi-modal capabilities.

Supports multiple backends:
- CLIP (local via transformers)
- OpenCLIP (local with more model options)
- Groq Vision API (cloud-based)
- OpenAI Whisper (local or API)
- Groq Whisper (cloud-based)
"""

import os
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
from functools import lru_cache


class ImageBackend(str, Enum):
    """Available image embedding backends."""
    CLIP_LOCAL = "clip_local"  # OpenAI CLIP via transformers
    OPENCLIP = "openclip"  # OpenCLIP with more models
    GROQ_VISION = "groq_vision"  # Groq LLaVA or similar
    OPENAI_VISION = "openai_vision"  # OpenAI GPT-4 Vision


class VoiceBackend(str, Enum):
    """Available voice processing backends."""
    WHISPER_LOCAL = "whisper_local"  # Local Whisper model
    WHISPER_API = "whisper_api"  # OpenAI Whisper API
    GROQ_WHISPER = "groq_whisper"  # Groq Whisper API


class ImageConfig(BaseModel):
    """Configuration for image processing."""
    
    # Backend selection
    backend: ImageBackend = Field(
        default=ImageBackend.CLIP_LOCAL,
        description="Image embedding backend to use"
    )
    
    # CLIP local settings
    clip_model_name: str = Field(
        default="openai/clip-vit-base-patch32",
        description="HuggingFace model name for CLIP"
    )
    clip_processor_name: str = Field(
        default="openai/clip-vit-base-patch32",
        description="HuggingFace processor name for CLIP"
    )
    
    # OpenCLIP settings
    openclip_model_name: str = Field(
        default="ViT-B-32",
        description="OpenCLIP model architecture"
    )
    openclip_pretrained: str = Field(
        default="laion2b_s34b_b79k",
        description="OpenCLIP pretrained weights"
    )
    
    # API settings (for Groq/OpenAI vision)
    vision_api_key: Optional[str] = Field(
        default=None,
        description="API key for cloud vision services"
    )
    vision_api_base: Optional[str] = Field(
        default=None,
        description="Base URL for vision API"
    )
    
    # Embedding settings
    embedding_dimension: int = Field(
        default=512,
        description="Dimension of image embeddings"
    )
    normalize_embeddings: bool = Field(
        default=True,
        description="Whether to L2-normalize embeddings"
    )
    
    # Processing settings
    max_image_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="Maximum image file size in bytes"
    )
    allowed_formats: List[str] = Field(
        default=["jpeg", "jpg", "png", "webp", "gif"],
        description="Allowed image formats"
    )
    resize_for_processing: bool = Field(
        default=True,
        description="Resize images before processing"
    )
    processing_size: int = Field(
        default=224,
        description="Image size for processing"
    )
    
    # Cache settings
    enable_cache: bool = Field(
        default=True,
        description="Cache image embeddings"
    )
    cache_ttl: int = Field(
        default=3600,
        description="Cache TTL in seconds"
    )
    
    # Device settings
    device: str = Field(
        default="cpu",
        description="Device for inference (cpu/cuda)"
    )
    
    class Config:
        use_enum_values = True


class VoiceConfig(BaseModel):
    """Configuration for voice processing."""
    
    # Backend selection
    backend: VoiceBackend = Field(
        default=VoiceBackend.WHISPER_LOCAL,
        description="Voice processing backend to use"
    )
    
    # Whisper local settings
    whisper_model_size: str = Field(
        default="base",
        description="Whisper model size (tiny, base, small, medium, large)"
    )
    whisper_device: str = Field(
        default="cpu",
        description="Device for Whisper inference"
    )
    
    # API settings
    whisper_api_key: Optional[str] = Field(
        default=None,
        description="API key for Whisper API"
    )
    groq_api_key: Optional[str] = Field(
        default=None,
        description="API key for Groq Whisper"
    )
    groq_api_base: str = Field(
        default="https://api.groq.com/openai/v1",
        description="Base URL for Groq API"
    )
    
    # Audio settings
    max_audio_duration: int = Field(
        default=60,
        description="Maximum audio duration in seconds"
    )
    max_audio_size: int = Field(
        default=25 * 1024 * 1024,  # 25MB
        description="Maximum audio file size in bytes"
    )
    allowed_audio_formats: List[str] = Field(
        default=["mp3", "wav", "m4a", "webm", "ogg", "flac"],
        description="Allowed audio formats"
    )
    sample_rate: int = Field(
        default=16000,
        description="Audio sample rate for processing"
    )
    
    # Language settings
    default_language: Optional[str] = Field(
        default=None,
        description="Default language (None for auto-detect)"
    )
    supported_languages: List[str] = Field(
        default=[
            "en", "es", "fr", "de", "it", "pt", "nl", "ru",
            "zh", "ja", "ko", "ar", "hi", "tr", "pl", "vi"
        ],
        description="Supported languages for transcription"
    )
    
    # Processing settings
    enable_timestamps: bool = Field(
        default=False,
        description="Include word-level timestamps"
    )
    enable_translation: bool = Field(
        default=False,
        description="Translate to English if different language"
    )
    
    class Config:
        use_enum_values = True


class MultimodalConfig(BaseModel):
    """Combined configuration for all multimodal features."""
    
    image: ImageConfig = Field(
        default_factory=ImageConfig,
        description="Image processing configuration"
    )
    voice: VoiceConfig = Field(
        default_factory=VoiceConfig,
        description="Voice processing configuration"
    )
    
    # General settings
    enable_image_search: bool = Field(
        default=True,
        description="Enable image search feature"
    )
    enable_voice_input: bool = Field(
        default=True,
        description="Enable voice input feature"
    )
    
    # File storage settings
    temp_dir: str = Field(
        default="/tmp/finfind_multimodal",
        description="Temporary directory for file processing"
    )
    cleanup_temp_files: bool = Field(
        default=True,
        description="Clean up temporary files after processing"
    )
    
    # Logging
    log_multimodal_requests: bool = Field(
        default=True,
        description="Log multimodal requests for debugging"
    )
    
    @classmethod
    def from_env(cls) -> "MultimodalConfig":
        """Create configuration from environment variables."""
        image_config = ImageConfig(
            backend=ImageBackend(
                os.getenv("IMAGE_BACKEND", "clip_local")
            ),
            clip_model_name=os.getenv(
                "CLIP_MODEL", "openai/clip-vit-base-patch32"
            ),
            vision_api_key=os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY"),
            device=os.getenv("IMAGE_DEVICE", "cpu"),
            embedding_dimension=int(os.getenv("IMAGE_EMBEDDING_DIM", "512")),
        )
        
        voice_config = VoiceConfig(
            backend=VoiceBackend(
                os.getenv("VOICE_BACKEND", "whisper_local")
            ),
            whisper_model_size=os.getenv("WHISPER_MODEL_SIZE", "base"),
            whisper_api_key=os.getenv("OPENAI_API_KEY"),
            groq_api_key=os.getenv("GROQ_API_KEY"),
            whisper_device=os.getenv("WHISPER_DEVICE", "cpu"),
        )
        
        return cls(
            image=image_config,
            voice=voice_config,
            enable_image_search=os.getenv("ENABLE_IMAGE_SEARCH", "true").lower() == "true",
            enable_voice_input=os.getenv("ENABLE_VOICE_INPUT", "true").lower() == "true",
            temp_dir=os.getenv("MULTIMODAL_TEMP_DIR", "/tmp/finfind_multimodal"),
        )


@lru_cache()
def get_multimodal_config() -> MultimodalConfig:
    """Get singleton multimodal configuration."""
    return MultimodalConfig.from_env()
