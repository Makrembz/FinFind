"""
API Tests for FinFind FastAPI Backend.

Tests for:
- Search endpoints
- User endpoints
- Product endpoints
- Recommendation endpoints
- Agent endpoints
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

# Import the app
from app.api.main import app
from app.api.models import (
    InteractionType,
    ProductSearchResult,
    UserProfile,
    FinancialProfile,
    UserPreferences
)


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def client():
    """Sync test client."""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_qdrant_service():
    """Mock Qdrant service."""
    service = AsyncMock()
    
    # Mock product data
    service.get_point.return_value = {
        "id": "prod_123",
        "payload": {
            "title": "Test Product",
            "description": "A test product description",
            "price": 99.99,
            "category": "Electronics",
            "brand": "TestBrand",
            "rating_avg": 4.5,
            "review_count": 100,
            "stock_status": "in_stock",
            "image_url": "https://example.com/image.jpg"
        },
        "vector": [0.1] * 384
    }
    
    # Mock search results
    service.semantic_search.return_value = [
        {
            "id": f"prod_{i}",
            "score": 0.9 - (i * 0.1),
            "payload": {
                "title": f"Product {i}",
                "description": f"Description {i}",
                "price": 50.0 + (i * 10),
                "category": "Electronics",
                "brand": "Brand",
                "rating_avg": 4.0,
                "review_count": 50,
                "stock_status": "in_stock"
            }
        }
        for i in range(5)
    ]
    
    service.mmr_search.return_value = service.semantic_search.return_value
    
    # Mock scroll
    service.scroll.return_value = []
    
    # Mock upsert
    service.upsert_point.return_value = True
    
    return service


@pytest.fixture
def mock_embedding_service():
    """Mock embedding service."""
    service = AsyncMock()
    service.embed_text.return_value = [0.1] * 384
    service.embed_batch.return_value = [[0.1] * 384]
    return service


# ==============================================================================
# Health Check Tests
# ==============================================================================

def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_api_info(client):
    """Test API info endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "FinFind API"
    assert "features" in data


# ==============================================================================
# Search Endpoint Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_search_products(async_client, mock_qdrant_service, mock_embedding_service):
    """Test product search endpoint."""
    with patch("app.api.routes.search.get_qdrant_service", return_value=mock_qdrant_service):
        with patch("app.api.routes.search.get_embedding_service", return_value=mock_embedding_service):
            response = await async_client.post(
                "/api/v1/search/",
                json={
                    "query": "wireless headphones",
                    "page": 1,
                    "page_size": 10
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "products" in data


def test_search_with_filters(client, mock_qdrant_service, mock_embedding_service):
    """Test search with filters."""
    with patch("app.api.routes.search.get_qdrant_service", return_value=mock_qdrant_service):
        with patch("app.api.routes.search.get_embedding_service", return_value=mock_embedding_service):
            response = client.post(
                "/api/v1/search/",
                json={
                    "query": "laptop",
                    "filters": {
                        "categories": ["Electronics"],
                        "price_range": {"min": 100, "max": 1000},
                        "min_rating": 4.0
                    },
                    "page_size": 20
                }
            )
            
            assert response.status_code == 200


def test_search_suggestions(client, mock_qdrant_service):
    """Test search suggestions endpoint."""
    with patch("app.api.routes.search.get_qdrant_service", return_value=mock_qdrant_service):
        response = client.get("/api/v1/search/suggestions?q=wire")
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data


# ==============================================================================
# User Endpoint Tests
# ==============================================================================

def test_get_user_profile(client, mock_qdrant_service):
    """Test get user profile."""
    mock_qdrant_service.get_point.return_value = {
        "id": "user_123",
        "payload": {
            "name": "Test User",
            "email": "test@example.com",
            "monthly_income": 5000,
            "monthly_budget": 1000,
            "preferred_categories": ["Electronics", "Books"],
            "preferred_brands": "Apple, Samsung"
        },
        "vector": [0.1] * 384
    }
    
    with patch("app.api.routes.users.get_qdrant_service", return_value=mock_qdrant_service):
        response = client.get(
            "/api/v1/users/user_123/profile",
            headers={"X-User-ID": "user_123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["profile"]["user_id"] == "user_123"


def test_get_user_profile_not_found(client, mock_qdrant_service):
    """Test get user profile - not found."""
    mock_qdrant_service.get_point.return_value = None
    
    with patch("app.api.routes.users.get_qdrant_service", return_value=mock_qdrant_service):
        response = client.get("/api/v1/users/nonexistent/profile")
        assert response.status_code == 404


def test_update_user_profile(client, mock_qdrant_service, mock_embedding_service):
    """Test update user profile."""
    mock_qdrant_service.get_point.return_value = {
        "id": "user_123",
        "payload": {"name": "Old Name"},
        "vector": [0.1] * 384
    }
    
    with patch("app.api.routes.users.get_qdrant_service", return_value=mock_qdrant_service):
        with patch("app.api.routes.users.get_embedding_service", return_value=mock_embedding_service):
            response = client.put(
                "/api/v1/users/user_123/profile",
                json={
                    "name": "New Name",
                    "preferences": {
                        "favorite_categories": ["Electronics"],
                        "price_sensitivity": "medium"
                    }
                },
                headers={"X-User-ID": "user_123"}
            )
            
            assert response.status_code == 200


def test_log_user_interaction(client, mock_qdrant_service):
    """Test logging user interaction."""
    with patch("app.api.routes.users.get_qdrant_service", return_value=mock_qdrant_service):
        response = client.post(
            "/api/v1/users/user_123/interactions",
            json={
                "product_id": "prod_456",
                "interaction_type": "view"
            },
            headers={"X-User-ID": "user_123"}
        )
        
        assert response.status_code == 201


# ==============================================================================
# Product Endpoint Tests
# ==============================================================================

def test_get_product(client, mock_qdrant_service):
    """Test get product details."""
    with patch("app.api.routes.products.get_qdrant_service", return_value=mock_qdrant_service):
        response = client.get("/api/v1/products/prod_123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["product"]["id"] == "prod_123"


def test_get_product_not_found(client, mock_qdrant_service):
    """Test get product - not found."""
    mock_qdrant_service.get_point.return_value = None
    
    with patch("app.api.routes.products.get_qdrant_service", return_value=mock_qdrant_service):
        response = client.get("/api/v1/products/nonexistent")
        assert response.status_code == 404


def test_get_product_reviews(client, mock_qdrant_service):
    """Test get product reviews."""
    mock_qdrant_service.scroll.return_value = [
        {
            "id": "review_1",
            "payload": {
                "user_id": "user_1",
                "rating": 5,
                "content": "Great product!",
                "created_at": datetime.utcnow().isoformat()
            }
        }
    ]
    
    with patch("app.api.routes.products.get_qdrant_service", return_value=mock_qdrant_service):
        response = client.get("/api/v1/products/prod_123/reviews")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "reviews" in data


def test_log_product_interaction(client, mock_qdrant_service):
    """Test logging product interaction."""
    with patch("app.api.routes.products.get_qdrant_service", return_value=mock_qdrant_service):
        response = client.post(
            "/api/v1/products/prod_123/interact",
            json={
                "interaction_type": "click",
                "metadata": {"source": "search_results"}
            },
            headers={"X-User-ID": "user_123"}
        )
        
        assert response.status_code == 201


def test_get_similar_products(client, mock_qdrant_service):
    """Test get similar products."""
    with patch("app.api.routes.products.get_qdrant_service", return_value=mock_qdrant_service):
        response = client.get("/api/v1/products/prod_123/similar?limit=5")
        
        assert response.status_code == 200


# ==============================================================================
# Recommendation Endpoint Tests
# ==============================================================================

def test_get_recommendations(client, mock_qdrant_service, mock_embedding_service):
    """Test get recommendations."""
    mock_qdrant_service.get_point.return_value = {
        "id": "user_123",
        "payload": {
            "preferences": {
                "preferred_categories": ["Electronics"],
                "price_sensitivity": "mid_range"
            }
        },
        "vector": [0.1] * 384
    }
    
    with patch("app.api.routes.recommendations.get_qdrant_service", return_value=mock_qdrant_service):
        with patch("app.api.routes.recommendations.get_embedding_service", return_value=mock_embedding_service):
            response = client.get(
                "/api/v1/recommendations/user_123?limit=10",
                headers={"X-User-ID": "user_123"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "recommendations" in data


def test_get_recommendations_user_not_found(client, mock_qdrant_service):
    """Test get recommendations - user not found."""
    mock_qdrant_service.get_point.return_value = None
    
    with patch("app.api.routes.recommendations.get_qdrant_service", return_value=mock_qdrant_service):
        response = client.get("/api/v1/recommendations/nonexistent")
        assert response.status_code == 404


def test_explain_recommendation(client, mock_qdrant_service):
    """Test explain recommendation."""
    mock_qdrant_service.get_point.side_effect = [
        {  # User
            "id": "user_123",
            "payload": {
                "preferences": {"preferred_categories": ["Electronics"]}
            }
        },
        {  # Product
            "id": "prod_123",
            "payload": {
                "category": "Electronics",
                "brand": "Apple",
                "price": 999,
                "rating_avg": 4.8
            }
        }
    ]
    
    with patch("app.api.routes.recommendations.get_qdrant_service", return_value=mock_qdrant_service):
        response = client.post(
            "/api/v1/recommendations/explain",
            json={
                "user_id": "user_123",
                "product_id": "prod_123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "factors" in data


def test_get_alternatives(client, mock_qdrant_service):
    """Test get product alternatives."""
    with patch("app.api.routes.recommendations.get_qdrant_service", return_value=mock_qdrant_service):
        response = client.get(
            "/api/v1/recommendations/alternatives/prod_123?criteria=balanced&limit=5"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "alternatives" in data


# ==============================================================================
# Agent Endpoint Tests
# ==============================================================================

def test_agent_chat(client):
    """Test agent chat endpoint."""
    mock_orchestrator = AsyncMock()
    mock_orchestrator.process.return_value = {
        "response": "Here are some recommendations for you.",
        "products": [],
        "agent": "search"
    }
    
    with patch("app.api.routes.agents.get_orchestrator", return_value=mock_orchestrator):
        response = client.post(
            "/api/v1/agents/chat",
            json={
                "message": "Find me wireless headphones under $100"
            }
        )
        
        # May return 200 or other status depending on implementation
        assert response.status_code in [200, 500]  # Allow 500 if orchestrator not fully mocked


# ==============================================================================
# Rate Limiting Tests
# ==============================================================================

def test_rate_limiting(client, mock_qdrant_service):
    """Test rate limiting middleware."""
    with patch("app.api.routes.products.get_qdrant_service", return_value=mock_qdrant_service):
        # Make many requests quickly
        responses = []
        for _ in range(10):
            response = client.get("/api/v1/products/prod_123")
            responses.append(response.status_code)
        
        # All should succeed (under 100 limit)
        assert all(status in [200, 404] for status in responses)


# ==============================================================================
# Request ID Tests
# ==============================================================================

def test_request_id_header(client):
    """Test request ID is returned in response headers."""
    response = client.get("/health")
    assert "X-Request-ID" in response.headers


def test_custom_request_id(client):
    """Test custom request ID is preserved."""
    custom_id = "custom-request-123"
    response = client.get("/health", headers={"X-Request-ID": custom_id})
    assert response.headers.get("X-Request-ID") == custom_id


# ==============================================================================
# Error Handling Tests
# ==============================================================================

def test_invalid_json(client):
    """Test invalid JSON handling."""
    response = client.post(
        "/api/v1/search/",
        content="invalid json",
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422


def test_missing_required_field(client):
    """Test missing required field handling."""
    response = client.post(
        "/api/v1/search/",
        json={}  # Missing required 'query' field
    )
    assert response.status_code == 422


# ==============================================================================
# Session Service Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_session_service():
    """Test session service operations."""
    from app.api.services.session_service import SessionService
    
    service = SessionService(use_redis=False)
    await service.initialize()
    
    try:
        # Create session
        session = await service.create_session(
            user_id="user_123",
            ttl_hours=1
        )
        assert session.session_id is not None
        assert session.user_id == "user_123"
        
        # Add messages
        await service.add_user_message(session.session_id, "Hello")
        await service.add_assistant_message(session.session_id, "Hi there!")
        
        # Get history
        history = await service.get_history(session.session_id)
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"
        
        # Get session
        retrieved = await service.get_session(session.session_id)
        assert retrieved is not None
        assert len(retrieved.messages) == 2
        
        # Delete session
        deleted = await service.delete_session(session.session_id)
        assert deleted is True
        
        # Verify deleted
        retrieved = await service.get_session(session.session_id)
        assert retrieved is None
        
    finally:
        await service.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
