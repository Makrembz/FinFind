"""
FinFind Application Configuration.

Centralized configuration using Pydantic Settings for environment variable management.
"""

import os
from typing import Optional, List
from functools import lru_cache
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class QdrantSettings(BaseSettings):
    """Qdrant Cloud configuration."""
    
    url: str = Field(
        default="http://localhost:6333",
        alias="QDRANT_URL",
        description="Qdrant server URL"
    )
    api_key: Optional[str] = Field(
        default=None,
        alias="QDRANT_API_KEY",
        description="Qdrant API key for cloud"
    )
    collection_products: str = Field(
        default="products",
        alias="QDRANT_COLLECTION_PRODUCTS"
    )
    collection_users: str = Field(
        default="users",
        alias="QDRANT_COLLECTION_USERS"
    )
    collection_interactions: str = Field(
        default="interactions",
        alias="QDRANT_COLLECTION_INTERACTIONS"
    )
    collection_reviews: str = Field(
        default="reviews",
        alias="QDRANT_COLLECTION_REVIEWS"
    )
    
    model_config = {"env_prefix": "", "extra": "ignore"}


class GroqSettings(BaseSettings):
    """Groq API configuration."""
    
    api_key: str = Field(
        default="",
        alias="GROQ_API_KEY",
        description="Groq API key"
    )
    model: str = Field(
        default="llama-3.1-70b-versatile",
        alias="GROQ_MODEL",
        description="Default Groq model"
    )
    temperature: float = Field(
        default=0.7,
        alias="GROQ_TEMPERATURE"
    )
    max_tokens: int = Field(
        default=4096,
        alias="GROQ_MAX_TOKENS"
    )
    
    model_config = {"env_prefix": "", "extra": "ignore"}


class EmbeddingSettings(BaseSettings):
    """Embedding model configuration."""
    
    model_name: str = Field(
        default="all-MiniLM-L6-v2",
        alias="EMBEDDING_MODEL",
        description="Sentence transformer model"
    )
    dimension: int = Field(
        default=384,
        alias="EMBEDDING_DIMENSION"
    )
    device: str = Field(
        default="cpu",
        alias="EMBEDDING_DEVICE"
    )
    
    model_config = {"env_prefix": "", "extra": "ignore"}


class ImageSettings(BaseSettings):
    """Image processing configuration."""
    
    enabled: bool = Field(
        default=True,
        alias="IMAGE_SEARCH_ENABLED"
    )
    backend: str = Field(
        default="clip_local",
        alias="IMAGE_BACKEND",
        description="clip_local, openclip, or groq_vision"
    )
    model_name: str = Field(
        default="openai/clip-vit-base-patch32",
        alias="CLIP_MODEL"
    )
    embedding_dimension: int = Field(
        default=512,
        alias="IMAGE_EMBEDDING_DIM"
    )
    max_size_mb: int = Field(
        default=10,
        alias="IMAGE_MAX_SIZE_MB"
    )
    device: str = Field(
        default="cpu",
        alias="IMAGE_DEVICE"
    )
    
    model_config = {"env_prefix": "", "extra": "ignore"}


class VoiceSettings(BaseSettings):
    """Voice processing configuration."""
    
    enabled: bool = Field(
        default=True,
        alias="VOICE_INPUT_ENABLED"
    )
    backend: str = Field(
        default="whisper_local",
        alias="VOICE_BACKEND",
        description="whisper_local, whisper_api, or groq_whisper"
    )
    model_size: str = Field(
        default="base",
        alias="WHISPER_MODEL_SIZE"
    )
    max_duration_seconds: int = Field(
        default=60,
        alias="VOICE_MAX_DURATION"
    )
    device: str = Field(
        default="cpu",
        alias="WHISPER_DEVICE"
    )
    
    model_config = {"env_prefix": "", "extra": "ignore"}


class RedisSettings(BaseSettings):
    """Redis configuration for sessions and caching."""
    
    url: str = Field(
        default="redis://localhost:6379",
        alias="REDIS_URL"
    )
    password: Optional[str] = Field(
        default=None,
        alias="REDIS_PASSWORD"
    )
    db: int = Field(
        default=0,
        alias="REDIS_DB"
    )
    session_ttl: int = Field(
        default=3600,
        alias="SESSION_TTL_SECONDS",
        description="Session expiry in seconds"
    )
    
    model_config = {"env_prefix": "", "extra": "ignore"}


class CORSSettings(BaseSettings):
    """CORS configuration."""
    
    allowed_origins: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ],
        alias="CORS_ORIGINS"
    )
    allow_credentials: bool = Field(
        default=True,
        alias="CORS_CREDENTIALS"
    )
    allowed_methods: List[str] = Field(
        default=["*"],
        alias="CORS_METHODS"
    )
    allowed_headers: List[str] = Field(
        default=["*"],
        alias="CORS_HEADERS"
    )
    
    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    model_config = {"env_prefix": "", "extra": "ignore"}


class RateLimitSettings(BaseSettings):
    """Rate limiting configuration."""
    
    enabled: bool = Field(
        default=True,
        alias="RATE_LIMIT_ENABLED"
    )
    requests_per_minute: int = Field(
        default=60,
        alias="RATE_LIMIT_PER_MINUTE"
    )
    requests_per_hour: int = Field(
        default=1000,
        alias="RATE_LIMIT_PER_HOUR"
    )
    burst_limit: int = Field(
        default=10,
        alias="RATE_LIMIT_BURST"
    )
    
    model_config = {"env_prefix": "", "extra": "ignore"}


class Settings(BaseSettings):
    """Main application settings."""
    
    # Application
    app_name: str = Field(
        default="FinFind API",
        alias="APP_NAME"
    )
    app_version: str = Field(
        default="1.0.0",
        alias="APP_VERSION"
    )
    environment: str = Field(
        default="development",
        alias="ENVIRONMENT"
    )
    debug: bool = Field(
        default=False,
        alias="DEBUG"
    )
    
    # Server
    host: str = Field(
        default="0.0.0.0",
        alias="HOST"
    )
    port: int = Field(
        default=8000,
        alias="PORT"
    )
    workers: int = Field(
        default=1,
        alias="WORKERS"
    )
    
    # API
    api_prefix: str = Field(
        default="/api",
        alias="API_PREFIX"
    )
    docs_enabled: bool = Field(
        default=True,
        alias="DOCS_ENABLED"
    )
    
    # Logging
    log_level: str = Field(
        default="INFO",
        alias="LOG_LEVEL"
    )
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        alias="LOG_FORMAT"
    )
    
    # File uploads
    upload_dir: str = Field(
        default="/tmp/finfind_uploads",
        alias="UPLOAD_DIR"
    )
    max_upload_size_mb: int = Field(
        default=50,
        alias="MAX_UPLOAD_SIZE_MB"
    )
    
    # Sub-configurations
    qdrant: QdrantSettings = Field(default_factory=QdrantSettings)
    groq: GroqSettings = Field(default_factory=GroqSettings)
    embedding: EmbeddingSettings = Field(default_factory=EmbeddingSettings)
    image: ImageSettings = Field(default_factory=ImageSettings)
    voice: VoiceSettings = Field(default_factory=VoiceSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    cors: CORSSettings = Field(default_factory=CORSSettings)
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        return self.environment == "development"
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience function for agents
def get_config() -> Settings:
    """Alias for get_settings for compatibility."""
    return get_settings()
