"""
FastAPI dependency injection.

Provides singleton instances of services for API endpoints.
"""

from typing import Optional, AsyncGenerator
from functools import lru_cache
from collections import defaultdict
import time

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Import multimodal processors
from ..multimodal.image_processor import (
    ImageProcessor,
    get_image_processor as _get_image_processor
)
from ..multimodal.voice_processor import (
    VoiceProcessor,
    get_voice_processor as _get_voice_processor
)
from ..multimodal.config import get_multimodal_config

# Import agent services
from ..agents.services.qdrant_service import (
    QdrantService,
    get_qdrant_service as _get_qdrant_service
)
from ..agents.services.embedding_service import (
    EmbeddingService,
    get_embedding_service as _get_embedding_service
)
from ..agents.orchestrator.coordinator import (
    AgentOrchestrator,
    get_orchestrator as _get_orchestrator
)

# Import session service
from .services.session_service import (
    SessionService,
    get_session_service as _get_session_service
)


# Security
security = HTTPBearer(auto_error=False)


# ==============================================================================
# Multimodal Dependencies
# ==============================================================================

async def get_image_processor() -> ImageProcessor:
    """Get image processor instance."""
    config = get_multimodal_config()
    if not config.enable_image_search:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Image search is disabled"
        )
    return _get_image_processor()


async def get_voice_processor() -> VoiceProcessor:
    """Get voice processor instance."""
    config = get_multimodal_config()
    if not config.enable_voice_input:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Voice input is disabled"
        )
    return _get_voice_processor()


# ==============================================================================
# Agent Service Dependencies
# ==============================================================================

async def get_qdrant_service() -> QdrantService:
    """Get Qdrant service instance."""
    return _get_qdrant_service()


async def get_embedding_service() -> EmbeddingService:
    """Get embedding service instance."""
    return _get_embedding_service()


async def get_orchestrator() -> AgentOrchestrator:
    """Get agent orchestrator instance."""
    return _get_orchestrator()


async def get_session_service() -> SessionService:
    """Get session service instance."""
    return _get_session_service()


# ==============================================================================
# Authentication Dependencies
# ==============================================================================

class UserContext:
    """Context for authenticated user."""
    
    def __init__(
        self,
        user_id: str,
        is_authenticated: bool = True,
        roles: list = None
    ):
        self.user_id = user_id
        self.is_authenticated = is_authenticated
        self.roles = roles or []
    
    def has_role(self, role: str) -> bool:
        return role in self.roles


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
) -> Optional[UserContext]:
    """
    Get current user from request.
    
    Supports:
    - Bearer token authentication
    - X-User-ID header (for development/testing)
    """
    # For development, allow X-User-ID header
    if x_user_id:
        return UserContext(
            user_id=x_user_id,
            is_authenticated=True
        )
    
    # Check bearer token
    if credentials:
        # In production, validate the token
        # For now, extract user_id from token (simplified)
        token = credentials.credentials
        # TODO: Implement proper token validation
        return UserContext(
            user_id=f"user_{token[:8]}",
            is_authenticated=True
        )
    
    # Anonymous user
    return None


async def require_user(
    user: Optional[UserContext] = Depends(get_current_user)
) -> UserContext:
    """Require authenticated user."""
    if not user or not user.is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user


# ==============================================================================
# Rate Limiting (Simple Implementation)
# ==============================================================================

_rate_limits: dict = defaultdict(list)


async def check_rate_limit(
    user: Optional[UserContext] = Depends(get_current_user),
    x_forwarded_for: Optional[str] = Header(None)
) -> None:
    """
    Check rate limits.
    
    Simple in-memory rate limiter. In production, use Redis.
    """
    # Get identifier
    if user:
        identifier = f"user:{user.user_id}"
    elif x_forwarded_for:
        identifier = f"ip:{x_forwarded_for.split(',')[0].strip()}"
    else:
        identifier = "anonymous"
    
    # Check limits (100 requests per minute)
    current_time = time.time()
    window_start = current_time - 60
    
    # Clean old entries
    _rate_limits[identifier] = [
        t for t in _rate_limits[identifier]
        if t > window_start
    ]
    
    # Check limit
    if len(_rate_limits[identifier]) >= 100:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )
    
    # Record request
    _rate_limits[identifier].append(current_time)
