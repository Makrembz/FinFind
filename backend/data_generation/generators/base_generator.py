"""
Base generator class with common functionality.

Provides shared utilities for all data generators including
random seeding, progress tracking, and embedding generation.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Any
import random
import numpy as np
from tqdm import tqdm
import logging

from ..config import GenerationConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseGenerator(ABC):
    """Abstract base class for all data generators."""
    
    def __init__(self, config: Optional[GenerationConfig] = None):
        """
        Initialize the generator.
        
        Args:
            config: Generation configuration. Uses default if not provided.
        """
        self.config = config or GenerationConfig()
        self._setup_random_seed()
        self._embedding_model = None
        
    def _setup_random_seed(self) -> None:
        """Set random seeds for reproducibility."""
        random.seed(self.config.random_seed)
        np.random.seed(self.config.random_seed)
        logger.info(f"Random seed set to {self.config.random_seed}")
    
    def _get_embedding_model(self):
        """Lazy load the embedding model."""
        if self._embedding_model is None and self.config.generate_embeddings:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading embedding model: {self.config.embedding_model}")
                self._embedding_model = SentenceTransformer(self.config.embedding_model)
                logger.info("Embedding model loaded successfully")
            except ImportError:
                logger.warning(
                    "sentence-transformers not installed. "
                    "Run: pip install sentence-transformers"
                )
                self.config.generate_embeddings = False
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                self.config.generate_embeddings = False
        return self._embedding_model
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed.
            
        Returns:
            List of embedding vectors.
        """
        if not self.config.generate_embeddings:
            return [[] for _ in texts]
        
        model = self._get_embedding_model()
        if model is None:
            return [[] for _ in texts]
        
        logger.info(f"Generating embeddings for {len(texts)} texts...")
        embeddings = []
        
        # Process in batches
        for i in tqdm(range(0, len(texts), self.config.embedding_batch_size), 
                      desc="Generating embeddings"):
            batch = texts[i:i + self.config.embedding_batch_size]
            batch_embeddings = model.encode(batch, convert_to_numpy=True)
            embeddings.extend(batch_embeddings.tolist())
        
        return embeddings
    
    def generate_single_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text string to embed.
            
        Returns:
            Embedding vector.
        """
        if not self.config.generate_embeddings:
            return []
        
        model = self._get_embedding_model()
        if model is None:
            return []
        
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    @staticmethod
    def weighted_choice(choices: List[Any], weights: List[float]) -> Any:
        """
        Make a weighted random choice.
        
        Args:
            choices: List of items to choose from.
            weights: Corresponding weights (must sum to 1.0).
            
        Returns:
            Selected item.
        """
        return random.choices(choices, weights=weights, k=1)[0]
    
    @staticmethod
    def generate_log_normal_price(mean: float, std: float, 
                                   min_val: float, max_val: float) -> float:
        """
        Generate a price using log-normal distribution.
        
        This creates realistic price distributions with right-skew.
        
        Args:
            mean: Mean of the underlying normal distribution.
            std: Standard deviation.
            min_val: Minimum allowed price.
            max_val: Maximum allowed price.
            
        Returns:
            Generated price.
        """
        # Calculate log-normal parameters
        log_mean = np.log(mean**2 / np.sqrt(std**2 + mean**2))
        log_std = np.sqrt(np.log(1 + (std**2 / mean**2)))
        
        # Generate and clamp
        price = np.random.lognormal(log_mean, log_std)
        price = max(min_val, min(max_val, price))
        
        return price
    
    @staticmethod
    def adjust_to_psychological_price(base_price: float) -> float:
        """
        Adjust price to realistic e-commerce price points.
        
        Args:
            base_price: Raw calculated price.
            
        Returns:
            Psychologically adjusted price (e.g., $X.99).
        """
        if base_price < 10:
            # Round to .99 or .49
            rounded = round(base_price)
            return rounded - 0.01 if rounded > base_price else rounded + 0.99
        elif base_price < 100:
            # End in .99 or round to nearest $5
            if random.random() < 0.7:
                return int(base_price) + 0.99
            else:
                return round(base_price / 5) * 5
        elif base_price < 1000:
            # End in .99 or round to nearest $10/$25
            if random.random() < 0.5:
                return (int(base_price / 10) * 10) - 0.01
            else:
                return round(base_price / 25) * 25
        else:
            # Round to nearest $50 or $100
            if random.random() < 0.5:
                return round(base_price / 50) * 50
            else:
                return round(base_price / 100) * 100
    
    @abstractmethod
    def generate(self) -> List[Any]:
        """
        Generate data items.
        
        Returns:
            List of generated data items.
        """
        pass
    
    @abstractmethod
    def validate(self, items: List[Any]) -> bool:
        """
        Validate generated items.
        
        Args:
            items: List of items to validate.
            
        Returns:
            True if all items are valid.
        """
        pass
