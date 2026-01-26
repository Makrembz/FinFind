"""
Embedding Service for FinFind.

Provides text embedding generation with:
- Batch processing
- Caching
- Multiple model support
"""

import logging
from typing import List, Optional, Dict, Any
import hashlib
import numpy as np

from ..config import get_config, EmbeddingConfig
from ..mcp.protocol import MCPError, MCPErrorCode

logger = logging.getLogger(__name__)


class EmbeddingCache:
    """Simple in-memory cache for embeddings."""
    
    def __init__(self, max_size: int = 10000):
        self._cache: Dict[str, List[float]] = {}
        self._max_size = max_size
    
    def _make_key(self, text: str, model: str) -> str:
        """Create cache key."""
        hash_str = hashlib.md5(f"{model}:{text}".encode()).hexdigest()
        return hash_str
    
    def get(self, text: str, model: str) -> Optional[List[float]]:
        """Get cached embedding."""
        key = self._make_key(text, model)
        return self._cache.get(key)
    
    def set(self, text: str, model: str, embedding: List[float]):
        """Cache an embedding."""
        if len(self._cache) >= self._max_size:
            # Remove random 10% when full
            keys_to_remove = list(self._cache.keys())[:self._max_size // 10]
            for key in keys_to_remove:
                del self._cache[key]
        
        key = self._make_key(text, model)
        self._cache[key] = embedding
    
    def clear(self):
        """Clear the cache."""
        self._cache.clear()


class EmbeddingService:
    """
    Centralized embedding service.
    
    Features:
    - Lazy model loading
    - Batch embedding
    - Caching
    - Normalization
    """
    
    def __init__(self, config: Optional[EmbeddingConfig] = None):
        """Initialize embedding service."""
        self._config = config or get_config().embedding
        self._model = None
        self._cache = EmbeddingCache()
        self._loaded = False
    
    def _load_model(self):
        """Lazy load the embedding model."""
        if self._loaded:
            return
        
        try:
            from sentence_transformers import SentenceTransformer
            
            logger.info(f"Loading embedding model: {self._config.model_name}")
            self._model = SentenceTransformer(self._config.model_name)
            self._loaded = True
            logger.info("Embedding model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise MCPError(
                code=MCPErrorCode.DEPENDENCY_FAILED,
                message=f"Failed to load embedding model: {e}",
                recoverable=False
            )
    
    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        return self._config.dimension
    
    def embed(
        self,
        text: str,
        use_cache: bool = True,
        normalize: bool = True
    ) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed.
            use_cache: Whether to use caching.
            normalize: Whether to L2 normalize.
            
        Returns:
            Embedding vector as list of floats.
        """
        # Check cache
        if use_cache:
            cached = self._cache.get(text, self._config.model_name)
            if cached is not None:
                return cached
        
        # Load model if needed
        self._load_model()
        
        try:
            # Truncate if too long
            if len(text) > self._config.max_seq_length * 4:  # Rough estimate
                text = text[:self._config.max_seq_length * 4]
            
            # Generate embedding
            embedding = self._model.encode(
                text,
                normalize_embeddings=normalize,
                show_progress_bar=False
            )
            
            # Convert to list
            embedding_list = embedding.tolist()
            
            # Cache
            if use_cache:
                self._cache.set(text, self._config.model_name, embedding_list)
            
            return embedding_list
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise MCPError(
                code=MCPErrorCode.EMBEDDING_FAILED,
                message=f"Embedding generation failed: {e}"
            )
    
    def embed_batch(
        self,
        texts: List[str],
        use_cache: bool = True,
        normalize: bool = True,
        batch_size: Optional[int] = None
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed.
            use_cache: Whether to use caching.
            normalize: Whether to L2 normalize.
            batch_size: Batch size for processing.
            
        Returns:
            List of embedding vectors.
        """
        if not texts:
            return []
        
        batch_size = batch_size or self._config.batch_size
        
        # Check cache for all texts
        results = [None] * len(texts)
        texts_to_embed = []
        indices_to_embed = []
        
        if use_cache:
            for i, text in enumerate(texts):
                cached = self._cache.get(text, self._config.model_name)
                if cached is not None:
                    results[i] = cached
                else:
                    texts_to_embed.append(text)
                    indices_to_embed.append(i)
        else:
            texts_to_embed = texts
            indices_to_embed = list(range(len(texts)))
        
        # Generate embeddings for non-cached texts
        if texts_to_embed:
            self._load_model()
            
            try:
                # Process in batches
                embeddings = self._model.encode(
                    texts_to_embed,
                    normalize_embeddings=normalize,
                    batch_size=batch_size,
                    show_progress_bar=False
                )
                
                # Store results and cache
                for i, idx in enumerate(indices_to_embed):
                    embedding_list = embeddings[i].tolist()
                    results[idx] = embedding_list
                    
                    if use_cache:
                        self._cache.set(
                            texts_to_embed[i],
                            self._config.model_name,
                            embedding_list
                        )
                
            except Exception as e:
                logger.error(f"Batch embedding failed: {e}")
                raise MCPError(
                    code=MCPErrorCode.EMBEDDING_FAILED,
                    message=f"Batch embedding failed: {e}"
                )
        
        return results
    
    def similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector.
            embedding2: Second embedding vector.
            
        Returns:
            Cosine similarity score (0-1).
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        dot = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot / (norm1 * norm2))
    
    def text_similarity(
        self,
        text1: str,
        text2: str,
        use_cache: bool = True
    ) -> float:
        """
        Compute similarity between two texts.
        
        Args:
            text1: First text.
            text2: Second text.
            use_cache: Whether to cache embeddings.
            
        Returns:
            Similarity score (0-1).
        """
        emb1 = self.embed(text1, use_cache=use_cache)
        emb2 = self.embed(text2, use_cache=use_cache)
        return self.similarity(emb1, emb2)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self._cache._cache),
            "max_size": self._cache._max_size,
            "model": self._config.model_name,
            "dimension": self._config.dimension
        }
    
    def clear_cache(self):
        """Clear the embedding cache."""
        self._cache.clear()


# Global service instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the global embedding service."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
