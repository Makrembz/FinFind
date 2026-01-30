"""
Qdrant Tools for FinFind Agents.

Provides tools for interacting with Qdrant Cloud vector database
including semantic search, recommendations, and similarity queries.
"""

import os
import logging
from typing import Dict, Any, List, Optional, Type
from pydantic import BaseModel, Field

from langchain_core.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Filter, 
    FieldCondition, 
    MatchValue, 
    Range,
    SearchParams,
    ScoredPoint
)

from ..config import get_config, QdrantConfig

logger = logging.getLogger(__name__)

# Global Qdrant client
_qdrant_client: Optional[QdrantClient] = None


def get_qdrant_client() -> QdrantClient:
    """Get or create the Qdrant client."""
    global _qdrant_client
    if _qdrant_client is None:
        config = get_config().qdrant
        _qdrant_client = QdrantClient(
            url=config.url,
            api_key=config.api_key,
            timeout=30
        )
    return _qdrant_client


# Embedding model singleton
_embedding_model = None


def get_embedding_model():
    """Get or create the embedding model."""
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            config = get_config().embedding
            _embedding_model = SentenceTransformer(config.model_name)
        except ImportError:
            logger.error("sentence-transformers not installed")
            raise
    return _embedding_model


def embed_text(text: str) -> List[float]:
    """Generate embedding for text."""
    model = get_embedding_model()
    return model.encode(text).tolist()


# ========================================
# Input Schemas
# ========================================

class QdrantSearchInput(BaseModel):
    """Input schema for Qdrant search tool."""
    
    query: str = Field(description="The search query text")
    collection: str = Field(
        default="products",
        description="Collection to search: products, user_profiles, reviews, user_interactions"
    )
    limit: int = Field(default=10, description="Maximum number of results")
    category_filter: Optional[str] = Field(
        default=None, 
        description="Filter by category"
    )
    min_price: Optional[float] = Field(
        default=None,
        description="Minimum price filter"
    )
    max_price: Optional[float] = Field(
        default=None,
        description="Maximum price filter"
    )
    min_rating: Optional[float] = Field(
        default=None,
        description="Minimum rating filter"
    )
    use_mmr: bool = Field(
        default=True,
        description="Use MMR for diverse results"
    )


class QdrantRecommendInput(BaseModel):
    """Input schema for Qdrant recommend tool."""
    
    user_id: str = Field(description="User ID for personalized recommendations")
    limit: int = Field(default=5, description="Number of recommendations")
    category: Optional[str] = Field(
        default=None,
        description="Filter recommendations by category"
    )
    max_price: Optional[float] = Field(
        default=None,
        description="Maximum price for recommendations"
    )
    exclude_purchased: bool = Field(
        default=True,
        description="Exclude already purchased products"
    )


class QdrantSimilarityInput(BaseModel):
    """Input schema for similarity lookup."""
    
    product_id: str = Field(description="Product ID to find similar items for")
    limit: int = Field(default=5, description="Number of similar items")
    same_category: bool = Field(
        default=False,
        description="Only return items from the same category"
    )
    price_range_pct: Optional[float] = Field(
        default=None,
        description="Limit to products within this percentage of the original price"
    )


# ========================================
# Qdrant Search Tool
# ========================================

class QdrantSearchTool(BaseTool):
    """
    Tool for semantic search on Qdrant collections.
    
    Supports:
    - Text-based semantic search
    - Payload filtering (category, price, rating)
    - MMR for result diversity
    """
    
    name: str = "qdrant_search"
    description: str = """Search for products or other items using semantic similarity.
Use this to find products matching a user's query.
You can filter by category, price range, and minimum rating.
Set use_mmr=True for diverse results."""
    
    args_schema: Type[BaseModel] = QdrantSearchInput
    
    def _run(
        self,
        query: str,
        collection: str = "products",
        limit: int = 10,
        category_filter: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_rating: Optional[float] = None,
        use_mmr: bool = True,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """Execute the search."""
        try:
            client = get_qdrant_client()
            config = get_config().qdrant
            
            # Get collection name
            collection_map = {
                "products": config.products_collection,
                "user_profiles": config.user_profiles_collection,
                "reviews": config.reviews_collection,
                "user_interactions": config.interactions_collection
            }
            collection_name = collection_map.get(collection, collection)
            
            # Generate query embedding
            query_vector = embed_text(query)
            
            # Build filters
            filter_conditions = []
            
            if category_filter:
                filter_conditions.append(
                    FieldCondition(
                        key="category",
                        match=MatchValue(value=category_filter)
                    )
                )
            
            if min_price is not None or max_price is not None:
                price_range = Range(
                    gte=min_price,
                    lte=max_price
                )
                filter_conditions.append(
                    FieldCondition(key="price", range=price_range)
                )
            
            if min_rating is not None:
                filter_conditions.append(
                    FieldCondition(
                        key="rating",
                        range=Range(gte=min_rating)
                    )
                )
            
            search_filter = Filter(must=filter_conditions) if filter_conditions else None
            
            # Execute search using query_points (qdrant-client 1.16+)
            # Use "text" named vector since products collection has dual vectors
            results = client.query_points(
                collection_name=collection_name,
                query=query_vector,
                query_filter=search_filter,
                limit=limit,
                with_payload=True,
                using="text"  # Use the "text" named vector for semantic search
            )
            
            # Format results
            formatted_results = []
            for result in results.points:
                item = {
                    "id": str(result.id),
                    "score": round(result.score, 4),
                    **result.payload
                }
                formatted_results.append(item)
            
            return {
                "success": True,
                "query": query,
                "collection": collection_name,
                "count": len(formatted_results),
                "results": formatted_results
            }
            
        except Exception as e:
            logger.exception(f"Qdrant search error: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": []
            }
    
    async def _arun(self, *args, **kwargs) -> Dict[str, Any]:
        """Async version - delegates to sync for now."""
        return self._run(*args, **kwargs)


# ========================================
# Qdrant Recommend Tool
# ========================================

class QdrantRecommendTool(BaseTool):
    """
    Tool for generating personalized recommendations.
    
    Uses user profile and interaction history to find
    relevant products.
    """
    
    name: str = "qdrant_recommend"
    description: str = """Generate personalized product recommendations for a user.
Uses the user's profile, preferences, and history to find relevant products.
Can filter by category and price."""
    
    args_schema: Type[BaseModel] = QdrantRecommendInput
    
    def _run(
        self,
        user_id: str,
        limit: int = 5,
        category: Optional[str] = None,
        max_price: Optional[float] = None,
        exclude_purchased: bool = True,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """Generate recommendations."""
        try:
            client = get_qdrant_client()
            config = get_config().qdrant
            
            # First, get user profile
            user_results = client.scroll(
                collection_name=config.user_profiles_collection,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="original_id",
                            match=MatchValue(value=user_id)
                        )
                    ]
                ),
                limit=1,
                with_vectors=True
            )
            
            if not user_results[0]:
                return {
                    "success": False,
                    "error": f"User {user_id} not found",
                    "recommendations": []
                }
            
            user_point = user_results[0][0]
            user_profile = user_point.payload
            user_vector = user_point.vector
            
            # Get user's budget if not specified
            if max_price is None:
                max_price = user_profile.get('budget_max')
            
            # Build filter for products
            filter_conditions = []
            
            if category:
                filter_conditions.append(
                    FieldCondition(
                        key="category",
                        match=MatchValue(value=category)
                    )
                )
            
            if max_price:
                filter_conditions.append(
                    FieldCondition(
                        key="price",
                        range=Range(lte=max_price)
                    )
                )
            
            search_filter = Filter(must=filter_conditions) if filter_conditions else None
            
            # Search for products similar to user profile
            # Use query_points with named vector since products collection has dual vectors
            # Extract the 'text' vector if user profile has named vectors
            if isinstance(user_vector, dict) and 'text' in user_vector:
                query_vector = user_vector['text']
            else:
                query_vector = user_vector
            
            results = client.query_points(
                collection_name=config.products_collection,
                query=query_vector,
                query_filter=search_filter,
                limit=limit * 2,  # Get more to filter
                with_payload=True,
                using="text"  # Use the "text" named vector
            )
            
            # Filter out purchased products if needed
            purchased = set(user_profile.get('purchased_products', []))
            recommendations = []
            
            for result in results.points:
                product_id = result.payload.get('original_id', str(result.id))
                if exclude_purchased and product_id in purchased:
                    continue
                
                recommendations.append({
                    "id": str(result.id),
                    "product_id": product_id,
                    "score": round(result.score, 4),
                    **result.payload
                })
                
                if len(recommendations) >= limit:
                    break
            
            return {
                "success": True,
                "user_id": user_id,
                "user_persona": user_profile.get('persona_type'),
                "count": len(recommendations),
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.exception(f"Qdrant recommend error: {e}")
            return {
                "success": False,
                "error": str(e),
                "recommendations": []
            }
    
    async def _arun(self, *args, **kwargs) -> Dict[str, Any]:
        """Async version."""
        return self._run(*args, **kwargs)


# ========================================
# Qdrant Similarity Tool
# ========================================

class QdrantSimilarityTool(BaseTool):
    """
    Tool for finding similar products.
    
    Given a product ID, finds similar products optionally
    constrained by category or price range.
    """
    
    name: str = "qdrant_similarity"
    description: str = """Find products similar to a given product.
Use this when a user wants alternatives or similar items.
Can filter to same category or price range."""
    
    args_schema: Type[BaseModel] = QdrantSimilarityInput
    
    def _run(
        self,
        product_id: str,
        limit: int = 5,
        same_category: bool = False,
        price_range_pct: Optional[float] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """Find similar products."""
        try:
            client = get_qdrant_client()
            config = get_config().qdrant
            
            # Get the source product
            source_results = client.scroll(
                collection_name=config.products_collection,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="original_id",
                            match=MatchValue(value=product_id)
                        )
                    ]
                ),
                limit=1,
                with_vectors=True
            )
            
            if not source_results[0]:
                return {
                    "success": False,
                    "error": f"Product {product_id} not found",
                    "similar_products": []
                }
            
            source_point = source_results[0][0]
            source_product = source_point.payload
            source_vector = source_point.vector
            
            # Build filters
            filter_conditions = []
            
            if same_category:
                filter_conditions.append(
                    FieldCondition(
                        key="category",
                        match=MatchValue(value=source_product.get('category'))
                    )
                )
            
            if price_range_pct and source_product.get('price'):
                original_price = source_product['price']
                min_price = original_price * (1 - price_range_pct)
                max_price = original_price * (1 + price_range_pct)
                filter_conditions.append(
                    FieldCondition(
                        key="price",
                        range=Range(gte=min_price, lte=max_price)
                    )
                )
            
            search_filter = Filter(must=filter_conditions) if filter_conditions else None
            
            # Search for similar products using query_points with named vector
            # Extract the 'text' vector if source has named vectors
            if isinstance(source_vector, dict) and 'text' in source_vector:
                query_vector = source_vector['text']
            else:
                query_vector = source_vector
            
            results = client.query_points(
                collection_name=config.products_collection,
                query=query_vector,
                query_filter=search_filter,
                limit=limit + 1,  # +1 to exclude self
                with_payload=True,
                using="text"  # Use the "text" named vector
            )
            
            # Format results (excluding the source product)
            similar_products = []
            for result in results.points:
                result_id = result.payload.get('original_id', str(result.id))
                if result_id == product_id:
                    continue
                
                similar_products.append({
                    "id": str(result.id),
                    "product_id": result_id,
                    "similarity_score": round(result.score, 4),
                    **result.payload
                })
                
                if len(similar_products) >= limit:
                    break
            
            return {
                "success": True,
                "source_product": {
                    "id": product_id,
                    "title": source_product.get('title'),
                    "category": source_product.get('category'),
                    "price": source_product.get('price')
                },
                "count": len(similar_products),
                "similar_products": similar_products
            }
            
        except Exception as e:
            logger.exception(f"Qdrant similarity error: {e}")
            return {
                "success": False,
                "error": str(e),
                "similar_products": []
            }
    
    async def _arun(self, *args, **kwargs) -> Dict[str, Any]:
        """Async version."""
        return self._run(*args, **kwargs)
