"""
Qdrant Service for FinFind.

Provides optimized Qdrant Cloud operations with:
- Connection pooling
- Batch operations
- MMR search
- Efficient filtering
- Error handling
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import os

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import (
    Filter, FieldCondition, MatchValue, Range,
    SearchParams, QuantizationSearchParams,
    RecommendStrategy
)

from ..config import get_config, QdrantConfig
from ..mcp.protocol import MCPError, MCPErrorCode

logger = logging.getLogger(__name__)


class QdrantService:
    """
    Centralized Qdrant service for all agent operations.
    
    Features:
    - Singleton client management
    - Collection-specific operations
    - MMR (Maximal Marginal Relevance) search
    - Efficient batch operations
    - Automatic retries
    """
    
    def __init__(self, config: Optional[QdrantConfig] = None):
        """Initialize Qdrant service."""
        self._config = config or get_config().qdrant
        self._client: Optional[QdrantClient] = None
        self._connected = False
    
    @property
    def client(self) -> QdrantClient:
        """Get or create Qdrant client."""
        if self._client is None:
            self._connect()
        return self._client
    
    def _connect(self):
        """Establish connection to Qdrant Cloud."""
        try:
            self._client = QdrantClient(
                url=self._config.url,
                api_key=self._config.api_key,
                timeout=60,
                prefer_grpc=False  # Use HTTP for better compatibility
            )
            self._connected = True
            logger.info(f"Connected to Qdrant at {self._config.url}")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise MCPError(
                code=MCPErrorCode.SERVICE_UNAVAILABLE,
                message=f"Failed to connect to Qdrant: {e}",
                recoverable=True,
                retry_after=5
            )
    
    def is_connected(self) -> bool:
        """Check if connected to Qdrant."""
        try:
            if self._client:
                self._client.get_collections()
                return True
        except:
            pass
        return False
    
    # ========================================
    # Collection Access
    # ========================================
    
    @property
    def products_collection(self) -> str:
        return self._config.products_collection
    
    @property
    def user_profiles_collection(self) -> str:
        return self._config.user_profiles_collection
    
    @property
    def reviews_collection(self) -> str:
        return self._config.reviews_collection
    
    @property
    def interactions_collection(self) -> str:
        return self._config.interactions_collection
    
    # ========================================
    # Search Operations
    # ========================================
    
    def semantic_search(
        self,
        collection: str,
        query_vector: List[float],
        limit: int = 10,
        filters: Optional[Dict] = None,
        score_threshold: Optional[float] = None,
        with_payload: bool = True,
        with_vectors: bool = False,
        vector_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search on a collection.
        
        Args:
            collection: Collection name.
            query_vector: Query embedding vector.
            limit: Maximum results to return.
            filters: Qdrant filter conditions.
            score_threshold: Minimum similarity score.
            with_payload: Include payload in results.
            with_vectors: Include vectors in results.
            vector_name: Named vector to search (e.g., "text", "image"). None for default.
            
        Returns:
            List of search results with scores.
        """
        try:
            # Build filter if provided
            qdrant_filter = self._build_filter(filters) if filters else None
            
            # Build query params
            query_params = {
                "collection_name": collection,
                "query": query_vector,
                "limit": limit,
                "query_filter": qdrant_filter,
                "score_threshold": score_threshold or self._config.score_threshold,
                "with_payload": with_payload,
                "with_vectors": with_vectors
            }
            
            # Add named vector if specified
            if vector_name:
                query_params["using"] = vector_name
            
            # Use query_points for qdrant-client 1.16+
            results = self.client.query_points(**query_params)
            
            return [
                {
                    "id": str(r.id),
                    "score": r.score,
                    "payload": dict(r.payload) if r.payload else {},
                    "vector": r.vector if with_vectors else None
                }
                for r in results.points
            ]
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            raise MCPError(
                code=MCPErrorCode.VECTOR_SEARCH_FAILED,
                message=f"Search failed: {e}",
                details={"collection": collection}
            )
    
    def mmr_search(
        self,
        collection: str,
        query_vector: List[float],
        limit: int = 10,
        diversity: float = 0.3,
        filters: Optional[Dict] = None,
        prefetch_limit: int = 50,
        vector_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        MMR (Maximal Marginal Relevance) search for diverse results.
        
        Balances relevance with diversity in results.
        
        Args:
            collection: Collection name.
            query_vector: Query embedding vector.
            limit: Final number of results.
            diversity: Diversity factor (0-1, higher = more diverse).
            filters: Qdrant filter conditions.
            prefetch_limit: Number of candidates to consider.
            vector_name: Named vector to search (e.g., "text", "image"). None for default.
            
        Returns:
            List of diverse search results.
        """
        try:
            qdrant_filter = self._build_filter(filters) if filters else None
            
            # Build query params
            query_params = {
                "collection_name": collection,
                "query": query_vector,
                "limit": prefetch_limit,
                "query_filter": qdrant_filter,
                "with_vectors": True,
                "with_payload": True
            }
            
            # Add named vector if specified
            if vector_name:
                query_params["using"] = vector_name
            
            # First, get more candidates than needed using query_points
            result = self.client.query_points(**query_params)
            
            candidates = result.points
            if not candidates:
                return []
            
            # Apply MMR selection
            selected = self._apply_mmr(
                query_vector=query_vector,
                candidates=candidates,
                k=limit,
                lambda_param=1 - diversity,
                vector_name=vector_name
            )
            
            return [
                {
                    "id": str(r.id),
                    "score": r.score,
                    "payload": dict(r.payload) if r.payload else {},
                    "mmr_score": r.score * (1 - diversity)  # Adjusted score
                }
                for r in selected
            ]
            
        except Exception as e:
            logger.error(f"MMR search failed: {e}")
            raise MCPError(
                code=MCPErrorCode.VECTOR_SEARCH_FAILED,
                message=f"MMR search failed: {e}"
            )
    
    def _apply_mmr(
        self,
        query_vector: List[float],
        candidates: List,
        k: int,
        lambda_param: float = 0.7,
        vector_name: Optional[str] = None
    ) -> List:
        """
        Apply MMR algorithm to select diverse results.
        
        MMR = λ * sim(d, q) - (1-λ) * max(sim(d, d_selected))
        """
        import numpy as np
        
        if len(candidates) <= k:
            return candidates
        
        query_vec = np.array(query_vector)
        selected = []
        remaining = list(candidates)
        
        def get_vector(point) -> np.ndarray:
            """Extract vector from point, handling named vectors."""
            vec = point.vector
            # Named vectors return a dict like {"text": [...], "image": [...]}
            if isinstance(vec, dict):
                if vector_name and vector_name in vec:
                    return np.array(vec[vector_name])
                # If no specific vector_name, use the first available
                first_key = next(iter(vec.keys()), None)
                if first_key:
                    return np.array(vec[first_key])
                return np.array([])
            return np.array(vec) if vec else np.array([])
        
        # Select first by pure relevance
        first = max(remaining, key=lambda x: x.score)
        selected.append(first)
        remaining.remove(first)
        
        # Iteratively select remaining
        while len(selected) < k and remaining:
            best_score = -float('inf')
            best_candidate = None
            
            for candidate in remaining:
                # Relevance to query
                relevance = candidate.score
                
                # Max similarity to already selected
                candidate_vec = get_vector(candidate)
                if len(candidate_vec) == 0:
                    continue
                    
                max_sim = max(
                    self._cosine_similarity(candidate_vec, get_vector(s))
                    for s in selected
                )
                
                # MMR score
                mmr = lambda_param * relevance - (1 - lambda_param) * max_sim
                
                if mmr > best_score:
                    best_score = mmr
                    best_candidate = candidate
            
            if best_candidate:
                selected.append(best_candidate)
                remaining.remove(best_candidate)
        
        return selected
    
    def _cosine_similarity(self, vec1, vec2) -> float:
        """Compute cosine similarity between two vectors."""
        import numpy as np
        dot = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)
    
    def recommend(
        self,
        collection: str,
        positive_ids: List[str],
        negative_ids: Optional[List[str]] = None,
        limit: int = 10,
        filters: Optional[Dict] = None,
        strategy: str = "average_vector"
    ) -> List[Dict[str, Any]]:
        """
        Get recommendations based on example points using Qdrant's query API.
        
        Uses the average vector approach: computes a centroid from positive examples
        and searches for similar items, while avoiding items similar to negative examples.
        
        Args:
            collection: Collection name.
            positive_ids: IDs of positive examples (products user liked).
            negative_ids: IDs of negative examples (products user disliked).
            limit: Number of recommendations.
            filters: Additional filters.
            strategy: Recommendation strategy (unused, kept for compatibility).
            
        Returns:
            List of recommended items.
        """
        try:
            qdrant_filter = self._build_filter(filters) if filters else None
            
            # Use query_points with recommend approach
            # First get the vectors for positive examples
            positive_points = self.client.retrieve(
                collection_name=collection,
                ids=positive_ids,
                with_vectors=True,
                with_payload=False
            )
            
            if not positive_points:
                logger.warning(f"No valid positive points found for IDs: {positive_ids}")
                return []
            
            # Extract vectors and compute average (centroid)
            import numpy as np
            
            vectors = []
            for point in positive_points:
                if point.vector:
                    # Handle named vectors
                    if isinstance(point.vector, dict):
                        # Use 'text' vector if available, else use first available
                        vec = point.vector.get('text', list(point.vector.values())[0] if point.vector else None)
                    else:
                        vec = point.vector
                    if vec:
                        vectors.append(vec)
            
            if not vectors:
                logger.warning("No vectors found in positive points")
                return []
            
            # Compute centroid (average vector)
            centroid = np.mean(vectors, axis=0).tolist()
            
            # If we have negative examples, we can adjust the centroid
            if negative_ids:
                negative_points = self.client.retrieve(
                    collection_name=collection,
                    ids=negative_ids[:5],  # Limit negative examples
                    with_vectors=True,
                    with_payload=False
                )
                
                neg_vectors = []
                for point in negative_points:
                    if point.vector:
                        if isinstance(point.vector, dict):
                            vec = point.vector.get('text', list(point.vector.values())[0] if point.vector else None)
                        else:
                            vec = point.vector
                        if vec:
                            neg_vectors.append(vec)
                
                # Subtract negative centroid from positive centroid
                if neg_vectors:
                    neg_centroid = np.mean(neg_vectors, axis=0)
                    centroid = (np.array(centroid) - 0.3 * neg_centroid).tolist()
            
            # Search using the computed centroid
            # Exclude the original positive IDs from results
            exclude_filter = models.Filter(
                must_not=[
                    models.HasIdCondition(has_id=positive_ids)
                ]
            )
            
            # Combine with user filters if provided
            if qdrant_filter:
                combined_filter = models.Filter(
                    must=qdrant_filter.must if hasattr(qdrant_filter, 'must') and qdrant_filter.must else [],
                    must_not=(qdrant_filter.must_not or []) + exclude_filter.must_not
                )
            else:
                combined_filter = exclude_filter
            
            # Use query_points for the search
            results = self.client.query_points(
                collection_name=collection,
                query=centroid,
                using="text",  # Use the text vector
                limit=limit,
                query_filter=combined_filter,
                with_payload=True
            )
            
            return [
                {
                    "id": str(r.id),
                    "score": r.score,
                    "payload": dict(r.payload) if r.payload else {}
                }
                for r in results.points
            ]
            
        except Exception as e:
            logger.error(f"Recommendation failed: {e}", exc_info=True)
            # Return empty list instead of raising to allow fallback to content-based
            return []
    
    # ========================================
    # Point Operations
    # ========================================
    
    def get_point(
        self,
        collection: str,
        point_id: str,
        with_vector: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Get a single point by ID."""
        try:
            results = self.client.retrieve(
                collection_name=collection,
                ids=[point_id],
                with_payload=True,
                with_vectors=with_vector
            )
            
            if not results:
                return None
            
            point = results[0]
            return {
                "id": str(point.id),
                "payload": dict(point.payload) if point.payload else {},
                "vector": point.vector if with_vector else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get point {point_id}: {e}")
            return None
    
    def get_user_profile(
        self,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get user profile by user ID.
        
        Args:
            user_id: The user's ID (also the point ID in user_profiles collection)
            
        Returns:
            User profile data including financial context and preferences
        """
        try:
            return self.get_point(
                collection=self.user_profiles_collection,
                point_id=user_id,
                with_vector=False
            )
        except Exception as e:
            logger.warning(f"Failed to get user profile {user_id}: {e}")
            return None
    
    def get_points_batch(
        self,
        collection: str,
        point_ids: List[str],
        with_vectors: bool = False
    ) -> List[Dict[str, Any]]:
        """Get multiple points by IDs."""
        try:
            results = self.client.retrieve(
                collection_name=collection,
                ids=point_ids,
                with_payload=True,
                with_vectors=with_vectors
            )
            
            return [
                {
                    "id": str(point.id),
                    "payload": dict(point.payload) if point.payload else {},
                    "vector": point.vector if with_vectors else None
                }
                for point in results
            ]
            
        except Exception as e:
            logger.error(f"Failed to get points batch: {e}")
            return []
    
    def upsert_point(
        self,
        collection: str,
        point_id: str,
        vector: List[float],
        payload: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Insert or update a single point.
        
        Args:
            collection: Collection name.
            point_id: Unique point ID.
            vector: Embedding vector.
            payload: Optional payload data.
            
        Returns:
            True if successful.
        """
        try:
            self.client.upsert(
                collection_name=collection,
                points=[
                    models.PointStruct(
                        id=point_id,
                        vector=vector,
                        payload=payload or {}
                    )
                ]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to upsert point {point_id}: {e}")
            raise MCPError(
                code=MCPErrorCode.QDRANT_ERROR,
                message=f"Upsert failed: {e}"
            )
    
    def scroll(
        self,
        collection: str,
        filters: Optional[Dict] = None,
        limit: int = 100,
        offset: Optional[str] = None,
        with_payload: Union[bool, List[str]] = True
    ) -> List[Dict[str, Any]]:
        """
        Scroll through collection with filters.
        
        Returns:
            List of points with id and payload.
        """
        try:
            qdrant_filter = self._build_filter(filters) if filters else None
            
            results, next_offset = self.client.scroll(
                collection_name=collection,
                scroll_filter=qdrant_filter,
                limit=limit,
                offset=offset,
                with_payload=with_payload,
                with_vectors=False
            )
            
            return [
                {
                    "id": str(point.id),
                    "payload": dict(point.payload) if point.payload else {}
                }
                for point in results
            ]
            
        except Exception as e:
            logger.error(f"Scroll failed: {e}")
            return []  # Return empty list instead of raising to allow graceful degradation
    
    # ========================================
    # Filter Building
    # ========================================
    
    def _build_filter(self, filter_dict: Dict) -> Filter:
        """
        Build Qdrant filter from dictionary.
        
        Supports:
        - match: Exact match
        - range: Numeric range
        - any: Match any of values
        - none: Match none of values
        """
        must_conditions = []
        must_not_conditions = []
        should_conditions = []
        
        for field, condition in filter_dict.items():
            if isinstance(condition, dict):
                if "match" in condition:
                    must_conditions.append(
                        FieldCondition(
                            key=field,
                            match=MatchValue(value=condition["match"])
                        )
                    )
                
                if "range" in condition:
                    range_cond = condition["range"]
                    must_conditions.append(
                        FieldCondition(
                            key=field,
                            range=Range(
                                gte=range_cond.get("gte"),
                                gt=range_cond.get("gt"),
                                lte=range_cond.get("lte"),
                                lt=range_cond.get("lt")
                            )
                        )
                    )
                
                if "any" in condition:
                    for val in condition["any"]:
                        should_conditions.append(
                            FieldCondition(
                                key=field,
                                match=MatchValue(value=val)
                            )
                        )
                
                if "none" in condition:
                    for val in condition["none"]:
                        must_not_conditions.append(
                            FieldCondition(
                                key=field,
                                match=MatchValue(value=val)
                            )
                        )
            else:
                # Simple equality
                must_conditions.append(
                    FieldCondition(
                        key=field,
                        match=MatchValue(value=condition)
                    )
                )
        
        return Filter(
            must=must_conditions if must_conditions else None,
            must_not=must_not_conditions if must_not_conditions else None,
            should=should_conditions if should_conditions else None
        )
    
    # ========================================
    # Collection Info
    # ========================================
    
    def get_collection_info(self, collection: str) -> Dict[str, Any]:
        """Get collection statistics."""
        try:
            info = self.client.get_collection(collection)
            return {
                "name": collection,
                "points_count": info.points_count,
                "vectors_count": info.vectors_count,
                "status": info.status.value
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {"name": collection, "error": str(e)}
    
    def list_collections(self) -> List[str]:
        """List all collection names."""
        try:
            result = self.client.get_collections()
            return [c.name for c in result.collections]
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []


# Global service instance
_qdrant_service: Optional[QdrantService] = None


def get_qdrant_service() -> QdrantService:
    """Get or create the global Qdrant service."""
    global _qdrant_service
    if _qdrant_service is None:
        _qdrant_service = QdrantService()
    return _qdrant_service
