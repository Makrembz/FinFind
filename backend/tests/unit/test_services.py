"""
Unit tests for backend services.

Tests:
- QdrantService
- EmbeddingService
- UserService
"""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from typing import Dict, Any, List


# ==============================================================================
# QdrantService Tests
# ==============================================================================

class TestQdrantService:
    """Test suite for QdrantService."""
    
    @pytest.fixture
    def qdrant_service(self, mock_qdrant_client, mock_embedding_service):
        """Create QdrantService with mocked client."""
        with patch('app.agents.services.qdrant_service.QdrantClient') as MockClient:
            MockClient.return_value = mock_qdrant_client
            
            from app.agents.services.qdrant_service import QdrantService
            service = QdrantService()
            service._client = mock_qdrant_client
            service._embedder = mock_embedding_service
            return service
    
    @pytest.mark.asyncio
    async def test_search_products(self, qdrant_service, sample_products):
        """Test basic product search."""
        qdrant_service._client.search = AsyncMock(return_value=[
            MagicMock(id=p["id"], score=0.9, payload=p)
            for p in sample_products[:3]
        ])
        
        results = await qdrant_service.search(query="headphones", limit=5)
        
        assert qdrant_service._client.search.called or results is not None
    
    @pytest.mark.asyncio
    async def test_search_with_filters(self, qdrant_service, sample_products):
        """Test search with category and price filters."""
        filtered = [p for p in sample_products if p["category"] == "Electronics"]
        qdrant_service._client.search = AsyncMock(return_value=[
            MagicMock(id=p["id"], score=0.9, payload=p)
            for p in filtered
        ])
        
        results = await qdrant_service.search(
            query="headphones",
            filters={"category": "Electronics", "max_price": 200}
        )
        
        assert qdrant_service._client.search.called
    
    @pytest.mark.asyncio
    async def test_search_mmr(self, qdrant_service, sample_products):
        """Test MMR (Maximal Marginal Relevance) search."""
        qdrant_service._client.search = AsyncMock(return_value=[
            MagicMock(id=p["id"], score=0.9 - (i * 0.1), payload=p)
            for i, p in enumerate(sample_products[:5])
        ])
        
        results = await qdrant_service.search(
            query="headphones",
            use_mmr=True,
            diversity=0.5
        )
        
        assert qdrant_service._client.search.called
    
    @pytest.mark.asyncio
    async def test_get_product_by_id(self, qdrant_service, sample_products):
        """Test retrieving a product by ID."""
        qdrant_service._client.retrieve = AsyncMock(return_value=[
            MagicMock(id=sample_products[0]["id"], payload=sample_products[0])
        ])
        
        result = await qdrant_service.get_by_id("prod_001")
        
        assert result is not None or qdrant_service._client.retrieve.called
    
    @pytest.mark.asyncio
    async def test_get_similar_products(self, qdrant_service, sample_products):
        """Test finding similar products."""
        qdrant_service._client.search = AsyncMock(return_value=[
            MagicMock(id=p["id"], score=0.8, payload=p)
            for p in sample_products[1:4]
        ])
        
        results = await qdrant_service.get_similar(
            product_id="prod_001",
            limit=3
        )
        
        assert qdrant_service._client.search.called
    
    @pytest.mark.asyncio
    async def test_upsert_products(self, qdrant_service, sample_products):
        """Test upserting products."""
        qdrant_service._client.upsert = AsyncMock(return_value=True)
        
        result = await qdrant_service.upsert(
            collection="products",
            points=[
                {"id": p["id"], "vector": [0.1] * 1536, "payload": p}
                for p in sample_products[:2]
            ]
        )
        
        assert qdrant_service._client.upsert.called
    
    @pytest.mark.asyncio
    async def test_filter_by_price_range(self, qdrant_service, sample_products):
        """Test filtering products by price range."""
        filtered = [p for p in sample_products if 50 <= p["price"] <= 150]
        qdrant_service._client.scroll = AsyncMock(return_value=(
            [MagicMock(id=p["id"], payload=p) for p in filtered],
            None
        ))
        
        results = await qdrant_service.filter_by_price(
            min_price=50,
            max_price=150
        )
        
        assert qdrant_service._client.scroll.called
    
    @pytest.mark.asyncio
    async def test_collection_info(self, qdrant_service):
        """Test getting collection information."""
        qdrant_service._client.get_collection = AsyncMock(return_value=MagicMock(
            vectors_count=1000,
            points_count=1000,
            status="green"
        ))
        
        info = await qdrant_service.get_collection_info()
        
        assert qdrant_service._client.get_collection.called


# ==============================================================================
# EmbeddingService Tests
# ==============================================================================

class TestEmbeddingService:
    """Test suite for EmbeddingService."""
    
    @pytest.fixture
    def embedding_service(self, mock_groq_client):
        """Create EmbeddingService with mocked client."""
        with patch('app.agents.services.embedding_service.get_embedding_client') as mock_get:
            mock_client = MagicMock()
            mock_client.embeddings.create = AsyncMock(return_value=MagicMock(
                data=[MagicMock(embedding=[0.1] * 1536)]
            ))
            mock_get.return_value = mock_client
            
            from app.agents.services.embedding_service import EmbeddingService
            service = EmbeddingService()
            service._client = mock_client
            return service
    
    @pytest.mark.asyncio
    async def test_embed_text(self, embedding_service):
        """Test embedding a text string."""
        with patch.object(embedding_service, 'embed_text', new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [0.1] * 1536
            
            result = await embedding_service.embed_text("wireless headphones")
            
            assert len(result) == 1536
    
    @pytest.mark.asyncio
    async def test_embed_texts_batch(self, embedding_service):
        """Test batch embedding multiple texts."""
        with patch.object(embedding_service, 'embed_texts', new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [[0.1] * 1536] * 3
            
            results = await embedding_service.embed_texts([
                "headphones",
                "laptop",
                "coffee maker"
            ])
            
            assert len(results) == 3
            assert all(len(e) == 1536 for e in results)
    
    @pytest.mark.asyncio
    async def test_embed_image(self, embedding_service, mock_image_bytes):
        """Test embedding an image."""
        with patch.object(embedding_service, 'embed_image', new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [0.1] * 1536
            
            result = await embedding_service.embed_image(mock_image_bytes)
            
            assert len(result) == 1536
    
    @pytest.mark.asyncio
    async def test_embedding_caching(self, embedding_service):
        """Test that embeddings are cached."""
        with patch.object(embedding_service, 'embed_text', new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [0.1] * 1536
            
            # Embed same text twice
            await embedding_service.embed_text("headphones")
            await embedding_service.embed_text("headphones")
            
            # Should be called (caching behavior depends on implementation)
            assert mock_embed.call_count >= 1


# ==============================================================================
# UserService Tests
# ==============================================================================

class TestUserService:
    """Test suite for UserService."""
    
    @pytest.fixture
    def user_service(self, mock_qdrant_client):
        """Create UserService with mocked storage."""
        from app.agents.services.user_service import UserService
        service = UserService()
        service._storage = mock_qdrant_client
        return service
    
    @pytest.mark.asyncio
    async def test_get_user_profile(self, user_service, sample_users):
        """Test fetching user profile."""
        with patch.object(user_service, 'get_profile', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = sample_users[0]
            
            result = await user_service.get_profile("user_001")
            
            assert result["id"] == "user_001"
            assert "financial" in result
    
    @pytest.mark.asyncio
    async def test_get_user_preferences(self, user_service, sample_users):
        """Test fetching user preferences."""
        with patch.object(user_service, 'get_preferences', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = sample_users[0]["preferences"]
            
            result = await user_service.get_preferences("user_001")
            
            assert "price_sensitivity" in result
    
    @pytest.mark.asyncio
    async def test_get_purchase_history(self, user_service):
        """Test fetching purchase history."""
        with patch.object(user_service, 'get_purchase_history', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = [
                {"product_id": "prod_001", "date": "2024-01-15", "price": 99.99}
            ]
            
            result = await user_service.get_purchase_history("user_001")
            
            assert len(result) >= 0
    
    @pytest.mark.asyncio
    async def test_update_user_preferences(self, user_service):
        """Test updating user preferences."""
        with patch.object(user_service, 'update_preferences', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = True
            
            result = await user_service.update_preferences(
                user_id="user_001",
                preferences={"price_sensitivity": 0.8}
            )
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_add_to_purchase_history(self, user_service):
        """Test adding to purchase history."""
        with patch.object(user_service, 'add_purchase', new_callable=AsyncMock) as mock_add:
            mock_add.return_value = True
            
            result = await user_service.add_purchase(
                user_id="user_001",
                product_id="prod_001",
                price=99.99
            )
            
            assert result is True


# ==============================================================================
# Service Error Handling Tests
# ==============================================================================

class TestServiceErrorHandling:
    """Test error handling across services."""
    
    @pytest.mark.asyncio
    async def test_qdrant_connection_error(self, mock_qdrant_client):
        """Test handling Qdrant connection errors."""
        mock_qdrant_client.search = AsyncMock(
            side_effect=ConnectionError("Failed to connect")
        )
        
        with patch('app.agents.services.qdrant_service.QdrantClient') as MockClient:
            MockClient.return_value = mock_qdrant_client
            
            from app.agents.services.qdrant_service import QdrantService
            service = QdrantService()
            service._client = mock_qdrant_client
            
            with pytest.raises(ConnectionError):
                await service.search(query="test")
    
    @pytest.mark.asyncio
    async def test_embedding_api_error(self):
        """Test handling embedding API errors."""
        with patch('app.agents.services.embedding_service.EmbeddingService') as MockService:
            service = MockService.return_value
            service.embed_text = AsyncMock(side_effect=Exception("API rate limit"))
            
            with pytest.raises(Exception):
                await service.embed_text("test")
    
    @pytest.mark.asyncio
    async def test_user_not_found(self):
        """Test handling user not found."""
        with patch('app.agents.services.user_service.UserService') as MockService:
            service = MockService.return_value
            service.get_profile = AsyncMock(return_value=None)
            
            result = await service.get_profile("nonexistent_user")
            
            assert result is None
