"""
FastAPI main application.

Sets up the FastAPI app with routes, middleware, and error handling.
"""

import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .routes import multimodal, search, agents, users, products, recommendations, workflows, learning
from .services.session_service import get_session_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ==============================================================================
# Lifespan Management
# ==============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting FinFind API...")
    
    # Initialize services (lazy loading, but validate configs)
    from ..multimodal.config import get_multimodal_config
    config = get_multimodal_config()
    logger.info(f"Image search enabled: {config.enable_image_search}")
    logger.info(f"Voice input enabled: {config.enable_voice_input}")
    
    # Initialize session service
    session_service = get_session_service()
    await session_service.initialize()
    logger.info("Session service initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down FinFind API...")
    await session_service.shutdown()
    logger.info("Session service shutdown complete")


# ==============================================================================
# Application Setup
# ==============================================================================

def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="FinFind API",
        description="""
        Context-Aware FinCommerce Engine API
        
        ## Features
        
        - **Product Search**: Semantic search with financial context
        - **Image Search**: Find products by uploading images
        - **Voice Search**: Search using voice input
        - **Recommendations**: Personalized product recommendations
        - **Explainability**: Understand why products are recommended
        
        ## Authentication
        
        Use the `X-User-ID` header for development or Bearer token for production.
        """,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    
    # ==============================================================================
    # Middleware
    # ==============================================================================
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Request ID middleware
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration:.3f}s"
        
        logger.info(
            f"{request.method} {request.url.path} - "
            f"{response.status_code} - {duration:.3f}s - {request_id}"
        )
        
        return response
    
    # ==============================================================================
    # Exception Handlers
    # ==============================================================================
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.status_code,
                    "message": exc.detail,
                    "request_id": getattr(request.state, "request_id", None)
                }
            }
        )
    
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": 400,
                    "message": str(exc),
                    "request_id": getattr(request.state, "request_id", None)
                }
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": 500,
                    "message": "Internal server error",
                    "request_id": getattr(request.state, "request_id", None)
                }
            }
        )
    
    # ==============================================================================
    # Routes
    # ==============================================================================
    
    # Health check
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "version": "1.0.0",
            "timestamp": time.time()
        }
    
    # API info
    @app.get("/", tags=["Info"])
    async def api_info():
        """API information."""
        return {
            "name": "FinFind API",
            "version": "1.0.0",
            "description": "Context-Aware FinCommerce Engine",
            "features": [
                "Product Search",
                "Image Search",
                "Voice Search",
                "Recommendations",
                "Explainability"
            ]
        }
    
    # Include routers
    app.include_router(
        multimodal.router,
        prefix="/api/v1/multimodal",
        tags=["Multimodal"]
    )
    
    app.include_router(
        search.router,
        prefix="/api/v1/search",
        tags=["Search"]
    )
    
    app.include_router(
        agents.router,
        prefix="/api/v1/agents",
        tags=["Agents"]
    )
    
    app.include_router(
        users.router,
        prefix="/api/v1/users",
        tags=["Users"]
    )
    
    app.include_router(
        products.router,
        prefix="/api/v1/products",
        tags=["Products"]
    )
    
    app.include_router(
        recommendations.router,
        prefix="/api/v1/recommendations",
        tags=["Recommendations"]
    )
    
    app.include_router(
        workflows.router,
        prefix="/api/v1/workflows",
        tags=["Workflows"]
    )
    
    app.include_router(
        learning.router,
        prefix="/api/v1/learning",
        tags=["Learning"]
    )
    
    return app


# Create application instance
app = create_app()


def get_app() -> FastAPI:
    """Get the FastAPI application instance."""
    return app
