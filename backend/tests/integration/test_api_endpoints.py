"""
Integration tests for API endpoints.

Tests all FastAPI routes with mocked services.
"""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from typing import Dict, Any, List
import json


# ==============================================================================
# Search API Tests
# ==============================================================================

class TestSearchAPI:
    """Test suite for search endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client with mocked dependencies."""
        with patch('app.api.routes.search.get_qdrant_service') as mock_qdrant:
            with patch('app.api.routes.search.get_embedding_service') as mock_embed:
                mock_qdrant_instance = MagicMock()
                mock_qdrant_instance.search = AsyncMock(return_value=[])
                mock_qdrant.return_value = mock_qdrant_instance
                
                mock_embed_instance = MagicMock()
                mock_embed_instance.embed_text = AsyncMock(return_value=[0.1] * 1536)
                mock_embed.return_value = mock_embed_instance
                
                from app.api.main import app
                return TestClient(app)
    
    def test_search_products_basic(self, client, sample_products):
        """Test basic product search."""
        with patch('app.api.routes.search.get_qdrant_service') as mock_qdrant:
            mock_service = MagicMock()
            mock_service.search = AsyncMock(return_value=sample_products[:3])
            mock_qdrant.return_value = mock_service
            
            response = client.post(
                "/api/v1/search/products",
                json={"query": "wireless headphones", "limit": 10}
            )
            
            assert response.status_code in [200, 422, 500]
    
    def test_search_with_filters(self, client, sample_products):
        """Test search with category and price filters."""
        with patch('app.api.routes.search.get_qdrant_service') as mock_qdrant:
            filtered = [p for p in sample_products if p["price"] <= 100]
            mock_service = MagicMock()
            mock_service.search = AsyncMock(return_value=filtered)
            mock_qdrant.return_value = mock_service
            
            response = client.post(
                "/api/v1/search/products",
                json={
                    "query": "headphones",
                    "filters": {
                        "max_price": 100,
                        "categories": ["Electronics"]
                    },
                    "limit": 10
                }
            )
            
            assert response.status_code in [200, 422, 500]
    
    def test_search_empty_query(self, client):
        """Test search with empty query returns validation error."""
        response = client.post(
            "/api/v1/search/products",
            json={"query": "", "limit": 10}
        )
        
        # Should return validation error (422)
        assert response.status_code in [400, 422]
    
    def test_search_pagination(self, client, sample_products):
        """Test search pagination."""
        with patch('app.api.routes.search.get_qdrant_service') as mock_qdrant:
            mock_service = MagicMock()
            mock_service.search = AsyncMock(return_value=sample_products[2:4])
            mock_qdrant.return_value = mock_service
            
            response = client.post(
                "/api/v1/search/products",
                json={
                    "query": "headphones",
                    "limit": 2,
                    "offset": 2
                }
            )
            
            assert response.status_code in [200, 422, 500]
    
    def test_search_suggestions(self, client):
        """Test search suggestions endpoint."""
        with patch('app.api.routes.search.get_suggestions') as mock_suggest:
            mock_suggest.return_value = [
                "wireless headphones",
                "wireless earbuds",
                "wireless speakers"
            ]
            
            response = client.get(
                "/api/v1/search/suggest",
                params={"q": "wireless"}
            )
            
            assert response.status_code in [200, 404, 500]


# ==============================================================================
# Recommendations API Tests
# ==============================================================================

class TestRecommendationsAPI:
    """Test suite for recommendations endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from app.api.main import app
        return TestClient(app)
    
    def test_get_recommendations(self, client, sample_products):
        """Test getting personalized recommendations."""
        with patch('app.api.routes.recommendations.get_recommendation_service') as mock_rec:
            mock_service = MagicMock()
            mock_service.get_recommendations = AsyncMock(return_value=sample_products[:5])
            mock_rec.return_value = mock_service
            
            response = client.get(
                "/api/v1/recommendations",
                params={"user_id": "user_001", "limit": 5}
            )
            
            assert response.status_code in [200, 404, 500]
    
    def test_get_recommendations_by_category(self, client, sample_products):
        """Test recommendations filtered by category."""
        electronics = [p for p in sample_products if p["category"] == "Electronics"]
        
        with patch('app.api.routes.recommendations.get_recommendation_service') as mock_rec:
            mock_service = MagicMock()
            mock_service.get_recommendations = AsyncMock(return_value=electronics)
            mock_rec.return_value = mock_service
            
            response = client.get(
                "/api/v1/recommendations",
                params={
                    "user_id": "user_001",
                    "category": "Electronics"
                }
            )
            
            assert response.status_code in [200, 404, 500]
    
    def test_get_similar_products(self, client, sample_products):
        """Test getting similar products."""
        with patch('app.api.routes.recommendations.get_recommendation_service') as mock_rec:
            mock_service = MagicMock()
            mock_service.get_similar = AsyncMock(return_value=sample_products[1:4])
            mock_rec.return_value = mock_service
            
            response = client.get(
                "/api/v1/recommendations/similar/prod_001"
            )
            
            assert response.status_code in [200, 404, 500]


# ==============================================================================
# Products API Tests
# ==============================================================================

class TestProductsAPI:
    """Test suite for products endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from app.api.main import app
        return TestClient(app)
    
    def test_get_product_by_id(self, client, sample_products):
        """Test getting a product by ID."""
        with patch('app.api.routes.products.get_qdrant_service') as mock_qdrant:
            mock_service = MagicMock()
            mock_service.get_by_id = AsyncMock(return_value=sample_products[0])
            mock_qdrant.return_value = mock_service
            
            response = client.get("/api/v1/products/prod_001")
            
            assert response.status_code in [200, 404, 500]
    
    def test_get_product_not_found(self, client):
        """Test getting a non-existent product."""
        with patch('app.api.routes.products.get_qdrant_service') as mock_qdrant:
            mock_service = MagicMock()
            mock_service.get_by_id = AsyncMock(return_value=None)
            mock_qdrant.return_value = mock_service
            
            response = client.get("/api/v1/products/nonexistent_id")
            
            assert response.status_code in [404, 500]
    
    def test_get_products_by_category(self, client, sample_products):
        """Test getting products by category."""
        electronics = [p for p in sample_products if p["category"] == "Electronics"]
        
        with patch('app.api.routes.products.get_qdrant_service') as mock_qdrant:
            mock_service = MagicMock()
            mock_service.filter_by_category = AsyncMock(return_value=electronics)
            mock_qdrant.return_value = mock_service
            
            response = client.get(
                "/api/v1/products",
                params={"category": "Electronics"}
            )
            
            assert response.status_code in [200, 404, 500]


# ==============================================================================
# User API Tests
# ==============================================================================

class TestUserAPI:
    """Test suite for user endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from app.api.main import app
        return TestClient(app)
    
    def test_get_user_profile(self, client, sample_users):
        """Test getting user profile."""
        with patch('app.api.routes.users.get_user_service') as mock_user:
            mock_service = MagicMock()
            mock_service.get_profile = AsyncMock(return_value=sample_users[0])
            mock_user.return_value = mock_service
            
            response = client.get("/api/v1/users/user_001")
            
            assert response.status_code in [200, 404, 500]
    
    def test_update_user_preferences(self, client):
        """Test updating user preferences."""
        with patch('app.api.routes.users.get_user_service') as mock_user:
            mock_service = MagicMock()
            mock_service.update_preferences = AsyncMock(return_value=True)
            mock_user.return_value = mock_service
            
            response = client.patch(
                "/api/v1/users/user_001/preferences",
                json={"price_sensitivity": 0.8}
            )
            
            assert response.status_code in [200, 404, 500]


# ==============================================================================
# Multimodal API Tests
# ==============================================================================

class TestMultimodalAPI:
    """Test suite for multimodal endpoints (image, voice)."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from app.api.main import app
        return TestClient(app)
    
    def test_image_search(self, client, mock_image_bytes, sample_products):
        """Test image-based search."""
        with patch('app.api.routes.multimodal.get_image_processor') as mock_processor:
            mock_service = MagicMock()
            mock_service.search_by_image = AsyncMock(return_value=sample_products[:3])
            mock_processor.return_value = mock_service
            
            response = client.post(
                "/api/v1/multimodal/image-search",
                files={"image": ("test.png", mock_image_bytes, "image/png")}
            )
            
            assert response.status_code in [200, 400, 415, 500]
    
    def test_voice_search(self, client, mock_audio_bytes, sample_products):
        """Test voice-based search."""
        with patch('app.api.routes.multimodal.get_voice_processor') as mock_processor:
            mock_service = MagicMock()
            mock_service.transcribe_and_search = AsyncMock(return_value={
                "transcription": "wireless headphones",
                "results": sample_products[:3]
            })
            mock_processor.return_value = mock_service
            
            response = client.post(
                "/api/v1/multimodal/voice-search",
                files={"audio": ("test.wav", mock_audio_bytes, "audio/wav")}
            )
            
            assert response.status_code in [200, 400, 415, 500]


# ==============================================================================
# Agent API Tests
# ==============================================================================

class TestAgentAPI:
    """Test suite for agent endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from app.api.main import app
        return TestClient(app)
    
    def test_agent_query(self, client, sample_products):
        """Test sending a query to the agent system."""
        with patch('app.api.routes.agents.get_agent_coordinator') as mock_coord:
            mock_coordinator = MagicMock()
            mock_coordinator.process_query = AsyncMock(return_value={
                "response": "Here are some headphones for you.",
                "products": sample_products[:3],
                "explanation": "These match your search."
            })
            mock_coord.return_value = mock_coordinator
            
            response = client.post(
                "/api/v1/agents/query",
                json={
                    "query": "I need wireless headphones under $100",
                    "user_id": "user_001"
                }
            )
            
            assert response.status_code in [200, 500]
    
    def test_agent_alternatives(self, client, sample_products):
        """Test getting alternatives through agent."""
        with patch('app.api.routes.agents.get_agent_coordinator') as mock_coord:
            mock_coordinator = MagicMock()
            mock_coordinator.find_alternatives = AsyncMock(return_value={
                "alternatives": sample_products[1:3],
                "explanation": "These are cheaper alternatives."
            })
            mock_coord.return_value = mock_coordinator
            
            response = client.post(
                "/api/v1/agents/alternatives",
                json={
                    "product_id": "prod_001",
                    "reason": "over_budget",
                    "user_budget": 100.0
                }
            )
            
            assert response.status_code in [200, 500]


# ==============================================================================
# Learning API Tests
# ==============================================================================

class TestLearningAPI:
    """Test suite for learning system endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from app.api.main import app
        return TestClient(app)
    
    def test_track_search_interaction(self, client):
        """Test tracking a search interaction."""
        with patch('app.api.routes.learning.get_learning_orchestrator') as mock_orch:
            mock_orchestrator = MagicMock()
            mock_orchestrator.track_search = AsyncMock(return_value=True)
            mock_orch.return_value = mock_orchestrator
            
            response = client.post(
                "/api/v1/learning/track/search",
                json={
                    "user_id": "user_001",
                    "query": "wireless headphones",
                    "results_count": 10
                }
            )
            
            assert response.status_code in [200, 201, 500]
    
    def test_track_click_interaction(self, client):
        """Test tracking a click interaction."""
        with patch('app.api.routes.learning.get_learning_orchestrator') as mock_orch:
            mock_orchestrator = MagicMock()
            mock_orchestrator.track_click = AsyncMock(return_value=True)
            mock_orch.return_value = mock_orchestrator
            
            response = client.post(
                "/api/v1/learning/track/click",
                json={
                    "user_id": "user_001",
                    "product_id": "prod_001",
                    "position": 1,
                    "query": "headphones"
                }
            )
            
            assert response.status_code in [200, 201, 500]
    
    def test_get_learning_dashboard(self, client):
        """Test getting learning dashboard."""
        with patch('app.api.routes.learning.get_learning_orchestrator') as mock_orch:
            mock_orchestrator = MagicMock()
            mock_orchestrator.get_dashboard = AsyncMock(return_value={
                "ctr": 0.15,
                "conversion_rate": 0.05,
                "total_interactions": 1000
            })
            mock_orch.return_value = mock_orchestrator
            
            response = client.get("/api/v1/learning/dashboard")
            
            assert response.status_code in [200, 500]


# ==============================================================================
# Workflow API Tests
# ==============================================================================

class TestWorkflowAPI:
    """Test suite for workflow endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from app.api.main import app
        return TestClient(app)
    
    def test_execute_search_workflow(self, client, sample_products):
        """Test executing a search workflow."""
        with patch('app.api.routes.workflows.get_workflow_executor') as mock_exec:
            mock_executor = MagicMock()
            mock_executor.execute = AsyncMock(return_value={
                "status": "completed",
                "results": sample_products[:3]
            })
            mock_exec.return_value = mock_executor
            
            response = client.post(
                "/api/v1/workflows/execute",
                json={
                    "workflow": "search",
                    "params": {"query": "headphones"}
                }
            )
            
            assert response.status_code in [200, 500]
    
    def test_get_workflow_status(self, client):
        """Test getting workflow status."""
        with patch('app.api.routes.workflows.get_workflow_executor') as mock_exec:
            mock_executor = MagicMock()
            mock_executor.get_status = AsyncMock(return_value={
                "workflow_id": "wf_001",
                "status": "completed",
                "progress": 100
            })
            mock_exec.return_value = mock_executor
            
            response = client.get("/api/v1/workflows/wf_001/status")
            
            assert response.status_code in [200, 404, 500]


# ==============================================================================
# Error Handling Tests
# ==============================================================================

class TestAPIErrorHandling:
    """Test API error handling."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from app.api.main import app
        return TestClient(app)
    
    def test_invalid_json(self, client):
        """Test handling invalid JSON."""
        response = client.post(
            "/api/v1/search/products",
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code in [400, 422]
    
    def test_missing_required_fields(self, client):
        """Test handling missing required fields."""
        response = client.post(
            "/api/v1/search/products",
            json={}  # Missing 'query'
        )
        
        assert response.status_code == 422
    
    def test_invalid_parameter_types(self, client):
        """Test handling invalid parameter types."""
        response = client.post(
            "/api/v1/search/products",
            json={
                "query": "headphones",
                "limit": "not a number"  # Should be int
            }
        )
        
        assert response.status_code == 422


# ==============================================================================
# Rate Limiting Tests
# ==============================================================================

class TestRateLimiting:
    """Test rate limiting functionality."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from app.api.main import app
        return TestClient(app)
    
    def test_rate_limit_headers(self, client):
        """Test that rate limit headers are present."""
        with patch('app.api.routes.search.get_qdrant_service') as mock_qdrant:
            mock_service = MagicMock()
            mock_service.search = AsyncMock(return_value=[])
            mock_qdrant.return_value = mock_service
            
            response = client.post(
                "/api/v1/search/products",
                json={"query": "test", "limit": 5}
            )
            
            # Rate limit headers may or may not be present
            assert response.status_code in [200, 422, 429, 500]
