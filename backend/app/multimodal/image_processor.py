"""
Image processor for visual product search.

Supports multiple backends:
- CLIP (OpenAI's via HuggingFace transformers)
- OpenCLIP (open-source with more model options)
- Groq Vision API (cloud-based)

Provides:
- Image embedding generation
- Image preprocessing and validation
- Caching of embeddings
"""

import io
import base64
import hashlib
import logging
from typing import Optional, List, Tuple, Union
from pathlib import Path
from functools import lru_cache
import numpy as np

from .config import ImageConfig, ImageBackend, get_multimodal_config
from .schemas import (
    ImageEmbeddingResult,
    ProcessedImage,
    MultimodalError,
    MultimodalErrorCode
)

logger = logging.getLogger(__name__)


class ImageProcessor:
    """
    Process images and generate embeddings for visual search.
    
    Supports multiple backends:
    - CLIP local: Uses HuggingFace transformers
    - OpenCLIP: Open-source CLIP with more models
    - Groq Vision: Cloud API for image understanding
    """
    
    def __init__(self, config: Optional[ImageConfig] = None):
        self.config = config or get_multimodal_config().image
        self._model = None
        self._processor = None
        self._tokenizer = None
        self._initialized = False
        self._embedding_cache: dict = {}
        
    def _initialize_clip_local(self) -> None:
        """Initialize local CLIP model."""
        try:
            from transformers import CLIPModel, CLIPProcessor
            import torch
            
            logger.info(f"Loading CLIP model: {self.config.clip_model_name}")
            
            self._model = CLIPModel.from_pretrained(
                self.config.clip_model_name
            )
            self._processor = CLIPProcessor.from_pretrained(
                self.config.clip_processor_name
            )
            
            # Move to device
            if self.config.device == "cuda" and torch.cuda.is_available():
                self._model = self._model.cuda()
            
            self._model.eval()
            self._initialized = True
            logger.info("CLIP model initialized successfully")
            
        except ImportError as e:
            logger.error(f"transformers not installed: {e}")
            raise RuntimeError(
                "transformers package required for local CLIP. "
                "Install with: pip install transformers torch"
            )
        except Exception as e:
            logger.error(f"Failed to initialize CLIP: {e}")
            raise
    
    def _initialize_openclip(self) -> None:
        """Initialize OpenCLIP model."""
        try:
            import open_clip
            import torch
            
            logger.info(
                f"Loading OpenCLIP model: {self.config.openclip_model_name} "
                f"({self.config.openclip_pretrained})"
            )
            
            self._model, _, self._processor = open_clip.create_model_and_transforms(
                self.config.openclip_model_name,
                pretrained=self.config.openclip_pretrained
            )
            self._tokenizer = open_clip.get_tokenizer(
                self.config.openclip_model_name
            )
            
            # Move to device
            if self.config.device == "cuda" and torch.cuda.is_available():
                self._model = self._model.cuda()
            
            self._model.eval()
            self._initialized = True
            logger.info("OpenCLIP model initialized successfully")
            
        except ImportError as e:
            logger.error(f"open_clip not installed: {e}")
            raise RuntimeError(
                "open_clip package required for OpenCLIP. "
                "Install with: pip install open-clip-torch"
            )
        except Exception as e:
            logger.error(f"Failed to initialize OpenCLIP: {e}")
            raise
    
    def _initialize(self) -> None:
        """Initialize the appropriate backend."""
        if self._initialized:
            return
            
        if self.config.backend == ImageBackend.CLIP_LOCAL:
            self._initialize_clip_local()
        elif self.config.backend == ImageBackend.OPENCLIP:
            self._initialize_openclip()
        elif self.config.backend in [ImageBackend.GROQ_VISION, ImageBackend.OPENAI_VISION]:
            # API-based backends don't need local initialization
            self._initialized = True
        else:
            raise ValueError(f"Unknown backend: {self.config.backend}")
    
    def _validate_image(
        self,
        image_data: bytes
    ) -> Tuple[bool, Optional[str], Optional[ProcessedImage]]:
        """Validate image data."""
        try:
            from PIL import Image
            
            # Check size
            if len(image_data) > self.config.max_image_size:
                return False, f"Image too large: {len(image_data)} bytes", None
            
            # Try to open image
            image = Image.open(io.BytesIO(image_data))
            
            # Check format
            format_lower = (image.format or "").lower()
            if format_lower not in self.config.allowed_formats:
                return False, f"Invalid format: {format_lower}", None
            
            processed = ProcessedImage(
                original_size=(image.width, image.height),
                processed_size=(image.width, image.height),
                format=format_lower,
                file_size_bytes=len(image_data),
                is_valid=True
            )
            
            return True, None, processed
            
        except Exception as e:
            return False, f"Invalid image: {str(e)}", None
    
    def _preprocess_image(self, image_data: bytes) -> "Image.Image":
        """Preprocess image for embedding generation."""
        from PIL import Image
        
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        # Resize if configured
        if self.config.resize_for_processing:
            image = image.resize(
                (self.config.processing_size, self.config.processing_size),
                Image.Resampling.LANCZOS
            )
        
        return image
    
    def _get_cache_key(self, image_data: bytes) -> str:
        """Generate cache key for image data."""
        return hashlib.sha256(image_data).hexdigest()
    
    def _embed_clip_local(self, image: "Image.Image") -> np.ndarray:
        """Generate embedding using local CLIP."""
        import torch
        
        # Process image
        inputs = self._processor(
            images=image,
            return_tensors="pt"
        )
        
        # Move to device
        if self.config.device == "cuda":
            inputs = {k: v.cuda() for k, v in inputs.items()}
        
        # Generate embedding
        with torch.no_grad():
            image_features = self._model.get_image_features(**inputs)
            
            # Handle BaseModelOutputWithPooling if needed
            if hasattr(image_features, 'pooler_output'):
                image_features = image_features.pooler_output
            elif not isinstance(image_features, torch.Tensor):
                # Try to extract tensor from dict-like output
                if hasattr(image_features, 'last_hidden_state'):
                    image_features = image_features.last_hidden_state[:, 0, :]
        
        # Normalize
        embedding = image_features.cpu().numpy().flatten()
        if self.config.normalize_embeddings:
            embedding = embedding / np.linalg.norm(embedding)
        
        return embedding
    
    def _embed_openclip(self, image: "Image.Image") -> np.ndarray:
        """Generate embedding using OpenCLIP."""
        import torch
        
        # Process image
        image_tensor = self._processor(image).unsqueeze(0)
        
        # Move to device
        if self.config.device == "cuda":
            image_tensor = image_tensor.cuda()
        
        # Generate embedding
        with torch.no_grad():
            image_features = self._model.encode_image(image_tensor)
        
        # Normalize
        embedding = image_features.cpu().numpy().flatten()
        if self.config.normalize_embeddings:
            embedding = embedding / np.linalg.norm(embedding)
        
        return embedding
    
    async def _embed_groq_vision(self, image_data: bytes) -> np.ndarray:
        """Generate embedding using Groq Vision API."""
        import httpx
        
        if not self.config.vision_api_key:
            raise RuntimeError("Groq API key not configured")
        
        # Encode image to base64
        image_b64 = base64.b64encode(image_data).decode()
        
        # Use Groq's vision model to generate description
        # Then embed the description (workaround since Groq doesn't have direct embeddings)
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.config.vision_api_base or 'https://api.groq.com/openai/v1'}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.config.vision_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llava-v1.5-7b-4096-preview",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{image_b64}"
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": "Describe this product image in detail for search purposes. Include color, style, type, and any visible features."
                                }
                            ]
                        }
                    ],
                    "max_tokens": 300
                },
                timeout=30.0
            )
            
            response.raise_for_status()
            result = response.json()
            description = result["choices"][0]["message"]["content"]
        
        # Generate text embedding from description
        # Use local embedding model for this
        from sentence_transformers import SentenceTransformer
        embed_model = SentenceTransformer("all-MiniLM-L6-v2")
        embedding = embed_model.encode(description, normalize_embeddings=True)
        
        return embedding
    
    async def generate_embedding(
        self,
        image_data: bytes,
        use_cache: bool = True
    ) -> ImageEmbeddingResult:
        """
        Generate embedding for an image.
        
        Args:
            image_data: Raw image bytes
            use_cache: Whether to use embedding cache
            
        Returns:
            ImageEmbeddingResult with embedding vector
        """
        import time
        start_time = time.time()
        
        # Check cache
        cache_key = self._get_cache_key(image_data)
        if use_cache and self.config.enable_cache:
            if cache_key in self._embedding_cache:
                cached = self._embedding_cache[cache_key]
                logger.debug(f"Image embedding cache hit: {cache_key[:16]}...")
                return cached
        
        # Validate image
        is_valid, error_msg, processed_info = self._validate_image(image_data)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Initialize backend
        self._initialize()
        
        # Preprocess
        image = self._preprocess_image(image_data)
        
        # Generate embedding based on backend
        if self.config.backend == ImageBackend.CLIP_LOCAL:
            embedding = self._embed_clip_local(image)
        elif self.config.backend == ImageBackend.OPENCLIP:
            embedding = self._embed_openclip(image)
        elif self.config.backend == ImageBackend.GROQ_VISION:
            embedding = await self._embed_groq_vision(image_data)
        else:
            raise ValueError(f"Unsupported backend: {self.config.backend}")
        
        processing_time = (time.time() - start_time) * 1000
        
        result = ImageEmbeddingResult(
            embedding=embedding.tolist(),
            dimension=len(embedding),
            model_used=self.config.clip_model_name if self.config.backend == ImageBackend.CLIP_LOCAL else self.config.openclip_model_name,
            processing_time_ms=processing_time,
            image_size=processed_info.original_size if processed_info else None
        )
        
        # Cache result
        if use_cache and self.config.enable_cache:
            self._embedding_cache[cache_key] = result
        
        return result
    
    async def generate_embedding_from_base64(
        self,
        image_base64: str,
        use_cache: bool = True
    ) -> ImageEmbeddingResult:
        """Generate embedding from base64-encoded image."""
        try:
            image_data = base64.b64decode(image_base64)
        except Exception as e:
            raise ValueError(f"Invalid base64 image data: {e}")
        
        return await self.generate_embedding(image_data, use_cache)
    
    async def generate_embedding_from_url(
        self,
        image_url: str,
        use_cache: bool = True
    ) -> ImageEmbeddingResult:
        """Generate embedding from image URL."""
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.get(image_url, timeout=30.0)
            response.raise_for_status()
            image_data = response.content
        
        return await self.generate_embedding(image_data, use_cache)
    
    async def generate_text_embedding(
        self,
        text: str
    ) -> List[float]:
        """
        Generate text embedding for text-to-image search.
        
        This allows searching for images using text descriptions.
        """
        self._initialize()
        
        import torch
        
        if self.config.backend == ImageBackend.CLIP_LOCAL:
            inputs = self._processor(
                text=[text],
                return_tensors="pt",
                padding=True,
                truncation=True
            )
            
            if self.config.device == "cuda":
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            with torch.no_grad():
                text_features = self._model.get_text_features(**inputs)
            
            embedding = text_features.cpu().numpy().flatten()
            
        elif self.config.backend == ImageBackend.OPENCLIP:
            text_tokens = self._tokenizer([text])
            
            if self.config.device == "cuda":
                text_tokens = text_tokens.cuda()
            
            with torch.no_grad():
                text_features = self._model.encode_text(text_tokens)
            
            embedding = text_features.cpu().numpy().flatten()
        else:
            # For API backends, use sentence transformer
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("all-MiniLM-L6-v2")
            embedding = model.encode(text, normalize_embeddings=True)
        
        if self.config.normalize_embeddings:
            embedding = embedding / np.linalg.norm(embedding)
        
        return embedding.tolist()
    
    def compute_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """Compute cosine similarity between two embeddings."""
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))
    
    def clear_cache(self) -> int:
        """Clear the embedding cache."""
        count = len(self._embedding_cache)
        self._embedding_cache.clear()
        return count


# Singleton instance
_image_processor: Optional[ImageProcessor] = None


def get_image_processor(config: Optional[ImageConfig] = None) -> ImageProcessor:
    """Get singleton image processor instance."""
    global _image_processor
    if _image_processor is None:
        _image_processor = ImageProcessor(config)
    return _image_processor
