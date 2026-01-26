"""
Pytest configuration and fixtures for FinFind tests.

Provides:
- Mock services (Qdrant, Groq, Embedding)
- Test data factories
- Async test utilities
- Environment setup
"""

import os
import sys
import asyncio
import pytest
from typing import Dict, Any, List, Optional, AsyncGenerator
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from dataclasses import dataclass
from datetime import datetime
import json

# Ensure backend module is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ==============================================================================
# Environment Setup
# ==============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    os.environ.setdefault("TESTING", "true")
    os.environ.setdefault("GROQ_API_KEY", "test-groq-api-key")
    os.environ.setdefault("QDRANT_URL", "http://localhost:6333")
    os.environ.setdefault("QDRANT_API_KEY", "test-qdrant-api-key")
    os.environ.setdefault("COLLECTION_NAME", "test_products")
    os.environ.setdefault("LOG_LEVEL", "DEBUG")
    yield


# ==============================================================================
# Event Loop Configuration
# ==============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ==============================================================================
# Mock Data Factories
# ==============================================================================

@dataclass
class MockProduct:
    """Factory for creating mock products."""
    
    @staticmethod
    def create(
        id: str = "prod_001",
        name: str = "Test Product",
        price: float = 99.99,
        category: str = "Electronics",
        brand: str = "TestBrand",
        rating: float = 4.5,
        description: str = "A great test product",
        in_stock: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        return {
            "id": id,
            "name": name,
            "title": name,
            "price": price,
            "category": category,
            "brand": brand,
            "rating": rating,
            "description": description,
            "in_stock": in_stock,
            "image_url": f"https://example.com/images/{id}.jpg",
            "features": kwargs.get("features", ["Feature 1", "Feature 2"]),
            "specs": kwargs.get("specs", {"weight": "1kg", "dimensions": "10x10x10cm"}),
            **kwargs
        }
    
    @staticmethod
    def create_batch(count: int = 5, category: str = "Electronics") -> List[Dict]:
        """Create multiple mock products."""
        return [
            MockProduct.create(
                id=f"prod_{i:03d}",
                name=f"Test Product {i}",
                price=50.0 + (i * 25),
                category=category,
                rating=3.5 + (i * 0.2)
            )
            for i in range(1, count + 1)
        ]


@dataclass
class MockUser:
    """Factory for creating mock users."""
    
    @staticmethod
    def create(
        id: str = "user_001",
        name: str = "Test User",
        budget_min: float = 50.0,
        budget_max: float = 500.0,
        preferred_categories: List[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        return {
            "id": id,
            "name": name,
            "email": f"{id}@test.com",
            "financial": {
                "budget_min": budget_min,
                "budget_max": budget_max,
                "monthly_limit": kwargs.get("monthly_limit", 1000.0),
                "spending_style": kwargs.get("spending_style", "moderate")
            },
            "preferred_categories": preferred_categories or ["Electronics", "Home"],
            "purchase_history": kwargs.get("purchase_history", []),
            "preferences": kwargs.get("preferences", {
                "price_sensitivity": 0.7,
                "brand_preference": 0.5,
                "quality_preference": 0.8
            }),
            **kwargs
        }


@dataclass
class MockSearchResult:
    """Factory for creating mock search results."""
    
    @staticmethod
    def create(
        products: List[Dict] = None,
        total: int = 10,
        query: str = "test query",
        score_threshold: float = 0.3
    ) -> Dict[str, Any]:
        if products is None:
            products = MockProduct.create_batch(5)
        
        return {
            "products": [
                {**p, "relevance_score": 0.9 - (i * 0.1)}
                for i, p in enumerate(products)
            ],
            "total_results": total,
            "query": query,
            "filters_applied": {},
            "search_time_ms": 45.5
        }


# ==============================================================================
# Mock Services
# ==============================================================================

@pytest.fixture
def mock_qdrant_client():
    """Create a mock Qdrant client."""
    client = MagicMock()
    
    # Mock search
    client.search = AsyncMock(return_value=[
        MagicMock(
            id=f"prod_{i:03d}",
            score=0.9 - (i * 0.1),
            payload=MockProduct.create(id=f"prod_{i:03d}")
        )
        for i in range(1, 6)
    ])
    
    # Mock scroll
    client.scroll = AsyncMock(return_value=([
        MagicMock(id="prod_001", payload=MockProduct.create())
    ], None))
    
    # Mock upsert
    client.upsert = AsyncMock(return_value=True)
    
    # Mock get collection
    client.get_collection = AsyncMock(return_value=MagicMock(
        vectors_count=1000,
        points_count=1000
    ))
    
    return client


@pytest.fixture
def mock_embedding_service():
    """Create a mock embedding service."""
    service = MagicMock()
    
    # Mock embed_text - returns 1536-dim vector
    async def mock_embed(text: str) -> List[float]:
        return [0.1] * 1536
    
    service.embed_text = AsyncMock(side_effect=mock_embed)
    service.embed_texts = AsyncMock(return_value=[[0.1] * 1536] * 5)
    service.embed_image = AsyncMock(return_value=[0.1] * 1536)
    
    return service


@pytest.fixture
def mock_groq_client():
    """Create a mock Groq LLM client."""
    client = MagicMock()
    
    # Mock chat completion
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="This is a test response from the LLM."))
    ]
    
    client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    return client


@pytest.fixture
def mock_qdrant_service(mock_qdrant_client, mock_embedding_service):
    """Create a mock QdrantService."""
    service = MagicMock()
    service.client = mock_qdrant_client
    service.embedder = mock_embedding_service
    
    async def mock_search(query: str, **kwargs) -> List[Dict]:
        return MockProduct.create_batch(kwargs.get("limit", 5))
    
    async def mock_get_by_id(id: str) -> Optional[Dict]:
        return MockProduct.create(id=id)
    
    service.search = AsyncMock(side_effect=mock_search)
    service.search_products = AsyncMock(side_effect=mock_search)
    service.get_by_id = AsyncMock(side_effect=mock_get_by_id)
    service.get_similar = AsyncMock(return_value=MockProduct.create_batch(3))
    service.filter_by_price = AsyncMock(return_value=MockProduct.create_batch(3))
    
    return service


# ==============================================================================
# Agent Fixtures
# ==============================================================================

@pytest.fixture
def mock_agent_state():
    """Create a mock agent state."""
    return {
        "messages": [],
        "context": {},
        "status": "idle",
        "results": None,
        "error": None,
        "metadata": {
            "agent_name": "TestAgent",
            "started_at": datetime.now().isoformat()
        }
    }


@pytest.fixture
def mock_conversation_context():
    """Create a mock conversation context."""
    from app.agents.base import ConversationContext, UserContext, FinancialContext
    
    return ConversationContext(
        session_id="test-session-001",
        user=UserContext(
            id="user_001",
            name="Test User",
            financial=FinancialContext(
                budget_min=50.0,
                budget_max=500.0,
                monthly_limit=1000.0
            ),
            preferred_categories=["Electronics", "Home"]
        ),
        history=[]
    )


# ==============================================================================
# API Test Client
# ==============================================================================

@pytest.fixture
def test_client():
    """Create a FastAPI test client."""
    from fastapi.testclient import TestClient
    from app.api.main import app
    
    # Override dependencies with mocks
    return TestClient(app)


@pytest.fixture
async def async_test_client():
    """Create an async test client for async endpoints."""
    from httpx import AsyncClient, ASGITransport
    from app.api.main import app
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client


# ==============================================================================
# Database/Storage Fixtures
# ==============================================================================

@pytest.fixture
def sample_products() -> List[Dict]:
    """Get a list of sample products for testing."""
    return [
        MockProduct.create(
            id="prod_001",
            name="Premium Wireless Headphones",
            price=199.99,
            category="Electronics",
            brand="SoundMax",
            rating=4.7
        ),
        MockProduct.create(
            id="prod_002",
            name="Budget Wireless Headphones",
            price=49.99,
            category="Electronics",
            brand="AudioBasic",
            rating=4.0
        ),
        MockProduct.create(
            id="prod_003",
            name="Professional Studio Headphones",
            price=349.99,
            category="Electronics",
            brand="ProAudio",
            rating=4.9
        ),
        MockProduct.create(
            id="prod_004",
            name="Running Shoes",
            price=129.99,
            category="Sports",
            brand="FastRun",
            rating=4.5
        ),
        MockProduct.create(
            id="prod_005",
            name="Coffee Maker",
            price=79.99,
            category="Home",
            brand="BrewMaster",
            rating=4.3
        ),
    ]


@pytest.fixture
def sample_users() -> List[Dict]:
    """Get a list of sample users for testing."""
    return [
        MockUser.create(
            id="user_001",
            name="Budget Buyer",
            budget_max=100.0,
            preferred_categories=["Electronics"]
        ),
        MockUser.create(
            id="user_002",
            name="Mid-Range Shopper",
            budget_max=300.0,
            preferred_categories=["Electronics", "Home"]
        ),
        MockUser.create(
            id="user_003",
            name="Premium Customer",
            budget_max=1000.0,
            preferred_categories=["Electronics", "Sports"]
        ),
    ]


# ==============================================================================
# Utility Fixtures
# ==============================================================================

@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file for testing."""
    file_path = tmp_path / "test_file.txt"
    file_path.write_text("Test content")
    return file_path


@pytest.fixture
def mock_image_bytes():
    """Create mock image bytes for testing image uploads."""
    # Simple 1x1 PNG image
    import base64
    png_1x1 = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )
    return png_1x1


@pytest.fixture
def mock_audio_bytes():
    """Create mock audio bytes for testing voice uploads."""
    # Return empty bytes for mock audio
    return b'\x00' * 1000


# ==============================================================================
# Async Utilities
# ==============================================================================

@pytest.fixture
def run_async():
    """Utility to run async functions in sync tests."""
    def _run_async(coro):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
    return _run_async


# ==============================================================================
# Cleanup Fixtures
# ==============================================================================

@pytest.fixture(autouse=True)
async def cleanup_after_test():
    """Clean up after each test."""
    yield
    # Any cleanup logic here
    await asyncio.sleep(0)  # Allow pending tasks to complete
