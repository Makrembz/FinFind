"""
FastAPI Application for FinFind.

This module provides the REST API for:
- Multimodal search (image and voice)
- Product search and recommendations
- Agent interactions
- User management
"""

from .main import app, get_app
from .dependencies import (
    get_image_processor,
    get_voice_processor,
    get_qdrant_service,
    get_embedding_service,
    get_orchestrator,
    get_current_user,
    get_session_service,
    check_rate_limit,
    UserContext
)

__all__ = [
    "app",
    "get_app",
    "get_image_processor",
    "get_voice_processor",
    "get_qdrant_service",
    "get_embedding_service",
    "get_orchestrator",
    "get_current_user",
    "get_session_service",
    "check_rate_limit",
    "UserContext",
]
