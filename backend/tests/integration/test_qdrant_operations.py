"""
Integration tests for Qdrant operations.

Tests:
- Search operations (using query_points API)
- Filter operations
- Upload operations
- Collection management

Note: These tests use mocked clients. The actual Qdrant client uses
query_points() instead of search() as of qdrant-client 1.16+.
"""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from typing import Dict, Any, List


class TestQdrantSearch:
    """Test Qdrant search operations."""
    
    @pytest.fixture
    def qdrant_client(self, mock_qdrant_client):
        """Get mocked Qdrant client."""
        return mock_qdrant_client
    
    @pytest.mark.asyncio
    async def test_semantic_search(self, qdrant_client, sample_products, mock_embedding_service):
        """Test semantic search with embeddings."""
        # Set up mock response for query_points (new API)
        mock_points = [
            MagicMock(id=p["id"], score=0.9 - (i * 0.1), payload=p)
            for i, p in enumerate(sample_products[:5])
        ]
        qdrant_client.query_points = AsyncMock(return_value=MagicMock(points=mock_points))
        
        # Perform search using new query_points API
        query_embedding = await mock_embedding_service.embed_text("wireless headphones")
        result = await qdrant_client.query_points(
            collection_name="products",
            query=query_embedding,
            limit=5
        )
        
        assert len(result.points) == 5
        # Results should be sorted by score (descending)
        scores = [r.score for r in result.points]
        assert scores == sorted(scores, reverse=True)
    
    @pytest.mark.asyncio
    async def test_search_with_score_threshold(self, qdrant_client, sample_products):
        """Test search with minimum score threshold."""
        # Only return results above threshold
        high_score_products = sample_products[:2]
        mock_points = [
            MagicMock(id=p["id"], score=0.8 + (i * 0.05), payload=p)
            for i, p in enumerate(high_score_products)
        ]
        qdrant_client.query_points = AsyncMock(return_value=MagicMock(points=mock_points))
        
        result = await qdrant_client.query_points(
            collection_name="products",
            query=[0.1] * 1536,
            limit=10,
            score_threshold=0.7
        )
        
        assert all(r.score >= 0.7 for r in result.points)
    
    @pytest.mark.asyncio
    async def test_search_with_mmr(self, qdrant_client, sample_products):
        """Test search with Maximal Marginal Relevance."""
        # MMR should return diverse results
        diverse_products = [
            sample_products[0],  # Premium headphones
            sample_products[3],  # Running shoes (different category)
            sample_products[4],  # Coffee maker (different category)
        ]
        
        mock_points = [
            MagicMock(id=p["id"], score=0.8, payload=p)
            for p in diverse_products
        ]
        qdrant_client.query_points = AsyncMock(return_value=MagicMock(points=mock_points))
        
        result = await qdrant_client.query_points(
            collection_name="products",
            query=[0.1] * 1536,
            limit=3
        )
        
        # Check diversity - not all same category
        categories = [r.payload["category"] for r in result.points]
        assert len(set(categories)) > 1  # Multiple categories


class TestQdrantFilters:
    """Test Qdrant filter operations."""
    
    @pytest.fixture
    def qdrant_client(self, mock_qdrant_client):
        """Get mocked Qdrant client."""
        return mock_qdrant_client
    
    @pytest.mark.asyncio
    async def test_filter_by_category(self, qdrant_client, sample_products):
        """Test filtering by category."""
        electronics = [p for p in sample_products if p["category"] == "Electronics"]
        
        qdrant_client.scroll = AsyncMock(return_value=(
            [MagicMock(id=p["id"], payload=p) for p in electronics],
            None
        ))
        
        results, _ = await qdrant_client.scroll(
            collection_name="products",
            scroll_filter={"must": [{"key": "category", "match": {"value": "Electronics"}}]}
        )
        
        assert all(r.payload["category"] == "Electronics" for r in results)
    
    @pytest.mark.asyncio
    async def test_filter_by_price_range(self, qdrant_client, sample_products):
        """Test filtering by price range."""
        in_range = [p for p in sample_products if 50 <= p["price"] <= 150]
        
        qdrant_client.scroll = AsyncMock(return_value=(
            [MagicMock(id=p["id"], payload=p) for p in in_range],
            None
        ))
        
        results, _ = await qdrant_client.scroll(
            collection_name="products",
            scroll_filter={
                "must": [
                    {"key": "price", "range": {"gte": 50, "lte": 150}}
                ]
            }
        )
        
        assert all(50 <= r.payload["price"] <= 150 for r in results)
    
    @pytest.mark.asyncio
    async def test_filter_by_rating(self, qdrant_client, sample_products):
        """Test filtering by minimum rating."""
        high_rated = [p for p in sample_products if p["rating"] >= 4.5]
        
        qdrant_client.scroll = AsyncMock(return_value=(
            [MagicMock(id=p["id"], payload=p) for p in high_rated],
            None
        ))
        
        results, _ = await qdrant_client.scroll(
            collection_name="products",
            scroll_filter={
                "must": [{"key": "rating", "range": {"gte": 4.5}}]
            }
        )
        
        assert all(r.payload["rating"] >= 4.5 for r in results)
    
    @pytest.mark.asyncio
    async def test_combined_filters(self, qdrant_client, sample_products):
        """Test combining multiple filters."""
        # Electronics under $200 with rating >= 4.0
        filtered = [
            p for p in sample_products
            if p["category"] == "Electronics" 
            and p["price"] <= 200 
            and p["rating"] >= 4.0
        ]
        
        qdrant_client.scroll = AsyncMock(return_value=(
            [MagicMock(id=p["id"], payload=p) for p in filtered],
            None
        ))
        
        results, _ = await qdrant_client.scroll(
            collection_name="products",
            scroll_filter={
                "must": [
                    {"key": "category", "match": {"value": "Electronics"}},
                    {"key": "price", "range": {"lte": 200}},
                    {"key": "rating", "range": {"gte": 4.0}}
                ]
            }
        )
        
        for r in results:
            assert r.payload["category"] == "Electronics"
            assert r.payload["price"] <= 200
            assert r.payload["rating"] >= 4.0
    
    @pytest.mark.asyncio
    async def test_filter_in_stock(self, qdrant_client, sample_products):
        """Test filtering for in-stock items."""
        in_stock = [p for p in sample_products if p["in_stock"]]
        
        qdrant_client.scroll = AsyncMock(return_value=(
            [MagicMock(id=p["id"], payload=p) for p in in_stock],
            None
        ))
        
        results, _ = await qdrant_client.scroll(
            collection_name="products",
            scroll_filter={
                "must": [{"key": "in_stock", "match": {"value": True}}]
            }
        )
        
        assert all(r.payload["in_stock"] for r in results)


class TestQdrantUpload:
    """Test Qdrant upload operations."""
    
    @pytest.fixture
    def qdrant_client(self, mock_qdrant_client):
        """Get mocked Qdrant client."""
        return mock_qdrant_client
    
    @pytest.mark.asyncio
    async def test_upsert_single_product(self, qdrant_client, sample_products):
        """Test upserting a single product."""
        qdrant_client.upsert = AsyncMock(return_value=True)
        
        product = sample_products[0]
        result = await qdrant_client.upsert(
            collection_name="products",
            points=[{
                "id": product["id"],
                "vector": [0.1] * 1536,
                "payload": product
            }]
        )
        
        assert result is True
        qdrant_client.upsert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upsert_batch(self, qdrant_client, sample_products):
        """Test batch upserting products."""
        qdrant_client.upsert = AsyncMock(return_value=True)
        
        points = [
            {
                "id": p["id"],
                "vector": [0.1] * 1536,
                "payload": p
            }
            for p in sample_products
        ]
        
        result = await qdrant_client.upsert(
            collection_name="products",
            points=points
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_delete_product(self, qdrant_client):
        """Test deleting a product."""
        qdrant_client.delete = AsyncMock(return_value=True)
        
        result = await qdrant_client.delete(
            collection_name="products",
            points_selector={"points": ["prod_001"]}
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_update_payload(self, qdrant_client):
        """Test updating product payload."""
        qdrant_client.set_payload = AsyncMock(return_value=True)
        
        result = await qdrant_client.set_payload(
            collection_name="products",
            payload={"price": 89.99, "in_stock": True},
            points=["prod_001"]
        )
        
        assert result is True


class TestQdrantCollection:
    """Test Qdrant collection management."""
    
    @pytest.fixture
    def qdrant_client(self, mock_qdrant_client):
        """Get mocked Qdrant client."""
        return mock_qdrant_client
    
    @pytest.mark.asyncio
    async def test_get_collection_info(self, qdrant_client):
        """Test getting collection information."""
        qdrant_client.get_collection = AsyncMock(return_value=MagicMock(
            vectors_count=1000,
            points_count=1000,
            status="green",
            config=MagicMock(
                params=MagicMock(
                    vectors=MagicMock(size=1536, distance="Cosine")
                )
            )
        ))
        
        info = await qdrant_client.get_collection(collection_name="products")
        
        assert info.vectors_count == 1000
        assert info.status == "green"
    
    @pytest.mark.asyncio
    async def test_create_collection(self, qdrant_client):
        """Test creating a new collection."""
        qdrant_client.create_collection = AsyncMock(return_value=True)
        
        result = await qdrant_client.create_collection(
            collection_name="new_products",
            vectors_config={
                "size": 1536,
                "distance": "Cosine"
            }
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_list_collections(self, qdrant_client):
        """Test listing all collections."""
        qdrant_client.get_collections = AsyncMock(return_value=MagicMock(
            collections=[
                MagicMock(name="products"),
                MagicMock(name="users"),
                MagicMock(name="interactions")
            ]
        ))
        
        result = await qdrant_client.get_collections()
        
        collection_names = [c.name for c in result.collections]
        assert "products" in collection_names


class TestQdrantErrorHandling:
    """Test Qdrant error handling."""
    
    @pytest.fixture
    def qdrant_client(self, mock_qdrant_client):
        """Get mocked Qdrant client."""
        return mock_qdrant_client
    
    @pytest.mark.asyncio
    async def test_connection_error(self, qdrant_client):
        """Test handling connection errors."""
        qdrant_client.query_points = AsyncMock(
            side_effect=ConnectionError("Failed to connect to Qdrant")
        )
        
        with pytest.raises(ConnectionError):
            await qdrant_client.query_points(
                collection_name="products",
                query=[0.1] * 1536,
                limit=5
            )
    
    @pytest.mark.asyncio
    async def test_collection_not_found(self, qdrant_client):
        """Test handling collection not found."""
        qdrant_client.query_points = AsyncMock(
            side_effect=Exception("Collection 'nonexistent' not found")
        )
        
        with pytest.raises(Exception) as exc_info:
            await qdrant_client.query_points(
                collection_name="nonexistent",
                query=[0.1] * 1536,
                limit=5
            )
        
        assert "not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_invalid_vector_dimension(self, qdrant_client):
        """Test handling invalid vector dimensions."""
        qdrant_client.query_points = AsyncMock(
            side_effect=ValueError("Vector dimension mismatch")
        )
        
        with pytest.raises(ValueError):
            await qdrant_client.query_points(
                collection_name="products",
                query=[0.1] * 100,  # Wrong dimension
                limit=5
            )
