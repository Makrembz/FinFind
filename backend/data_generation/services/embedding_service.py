"""
Embedding service for generating text embeddings.

Handles batch embedding generation with progress tracking
and memory-efficient processing.
"""

from typing import List, Optional
import logging
from tqdm import tqdm

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings."""
    
    def __init__(self, 
                 model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
                 batch_size: int = 64):
        """
        Initialize the embedding service.
        
        Args:
            model_name: Name of the sentence-transformers model.
            batch_size: Batch size for embedding generation.
        """
        self.model_name = model_name
        self.batch_size = batch_size
        self._model = None
        self._dimension = None
    
    @property
    def model(self):
        """Lazy load the embedding model."""
        if self._model is None:
            self._load_model()
        return self._model
    
    @property
    def dimension(self) -> int:
        """Get the embedding dimension."""
        if self._dimension is None:
            _ = self.model  # Ensure model is loaded
        return self._dimension
    
    def _load_model(self) -> None:
        """Load the embedding model."""
        try:
            from sentence_transformers import SentenceTransformer
            
            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            self._dimension = self._model.get_sentence_embedding_dimension()
            logger.info(f"Model loaded. Embedding dimension: {self._dimension}")
            
        except ImportError:
            logger.error(
                "sentence-transformers not installed. "
                "Run: pip install sentence-transformers"
            )
            raise
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def encode(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed.
            
        Returns:
            Embedding vector as list of floats.
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def encode_batch(self, texts: List[str], 
                     show_progress: bool = True) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: List of texts to embed.
            show_progress: Whether to show progress bar.
            
        Returns:
            List of embedding vectors.
        """
        if not texts:
            return []
        
        logger.info(f"Generating embeddings for {len(texts)} texts...")
        embeddings = []
        
        iterator = range(0, len(texts), self.batch_size)
        if show_progress:
            iterator = tqdm(iterator, desc="Generating embeddings")
        
        for i in iterator:
            batch = texts[i:i + self.batch_size]
            batch_embeddings = self.model.encode(batch, convert_to_numpy=True)
            embeddings.extend(batch_embeddings.tolist())
        
        logger.info(f"Generated {len(embeddings)} embeddings")
        return embeddings
    
    def is_available(self) -> bool:
        """Check if the embedding service is available."""
        try:
            from sentence_transformers import SentenceTransformer
            return True
        except ImportError:
            return False


# Singleton instance for convenience
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service(model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
                          batch_size: int = 64) -> EmbeddingService:
    """
    Get or create the embedding service singleton.
    
    Args:
        model_name: Name of the sentence-transformers model.
        batch_size: Batch size for embedding generation.
        
    Returns:
        EmbeddingService instance.
    """
    global _embedding_service
    
    if _embedding_service is None:
        _embedding_service = EmbeddingService(model_name, batch_size)
    
    return _embedding_service
