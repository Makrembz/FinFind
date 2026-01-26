"""
Multimodal service for centralized access to image and voice processing.

Provides a unified interface for:
- Image embedding generation and search
- Voice transcription and search
- Multimodal query handling
"""

import logging
from typing import Optional, List, Dict, Any
from functools import lru_cache

from ..multimodal.image_processor import ImageProcessor, get_image_processor
from ..multimodal.voice_processor import VoiceProcessor, get_voice_processor
from ..multimodal.config import MultimodalConfig, get_multimodal_config
from ..multimodal.schemas import (
    ImageSearchResult,
    SimilarProduct,
    VoiceTranscriptionResult,
    MultimodalError,
    MultimodalErrorCode
)
from .qdrant_service import QdrantService, get_qdrant_service
from .embedding_service import EmbeddingService, get_embedding_service

logger = logging.getLogger(__name__)


class MultimodalService:
    """
    Unified service for multimodal operations.
    
    Combines image processing, voice processing, and search
    into a single interface for agents and API endpoints.
    """
    
    def __init__(
        self,
        config: Optional[MultimodalConfig] = None,
        qdrant_service: Optional[QdrantService] = None,
        embedding_service: Optional[EmbeddingService] = None
    ):
        self.config = config or get_multimodal_config()
        self._qdrant = qdrant_service
        self._embedding = embedding_service
        self._image_processor: Optional[ImageProcessor] = None
        self._voice_processor: Optional[VoiceProcessor] = None
    
    @property
    def qdrant(self) -> QdrantService:
        if self._qdrant is None:
            self._qdrant = get_qdrant_service()
        return self._qdrant
    
    @property
    def embedding(self) -> EmbeddingService:
        if self._embedding is None:
            self._embedding = get_embedding_service()
        return self._embedding
    
    @property
    def image_processor(self) -> ImageProcessor:
        if self._image_processor is None:
            self._image_processor = get_image_processor(self.config.image)
        return self._image_processor
    
    @property
    def voice_processor(self) -> VoiceProcessor:
        if self._voice_processor is None:
            self._voice_processor = get_voice_processor(self.config.voice)
        return self._voice_processor
    
    # ==========================================================================
    # Image Operations
    # ==========================================================================
    
    def is_image_search_enabled(self) -> bool:
        """Check if image search is enabled."""
        return self.config.enable_image_search
    
    async def search_by_image(
        self,
        image_data: Optional[bytes] = None,
        image_base64: Optional[str] = None,
        image_url: Optional[str] = None,
        limit: int = 10,
        max_price: Optional[float] = None,
        min_price: Optional[float] = None,
        categories: Optional[List[str]] = None,
        use_mmr: bool = True,
        diversity: float = 0.3,
        score_threshold: float = 0.4
    ) -> ImageSearchResult:
        """
        Search for products using an image.
        
        Args:
            image_data: Raw image bytes
            image_base64: Base64-encoded image
            image_url: URL to fetch image from
            limit: Maximum results
            max_price: Price ceiling
            min_price: Price floor
            categories: Category filters
            use_mmr: Use MMR for diversity
            diversity: MMR diversity factor
            score_threshold: Minimum similarity score
            
        Returns:
            ImageSearchResult with similar products
        """
        import time
        start_time = time.time()
        
        if not self.config.enable_image_search:
            raise ValueError("Image search is disabled")
        
        # Generate embedding
        embedding_start = time.time()
        
        if image_data:
            embedding_result = await self.image_processor.generate_embedding(image_data)
        elif image_base64:
            embedding_result = await self.image_processor.generate_embedding_from_base64(
                image_base64
            )
        elif image_url:
            embedding_result = await self.image_processor.generate_embedding_from_url(
                image_url
            )
        else:
            raise ValueError("One of image_data, image_base64, or image_url must be provided")
        
        embedding_time = (time.time() - embedding_start) * 1000
        
        # Build filters
        filters = {}
        if max_price is not None:
            filters["price"] = {"lte": max_price}
        if min_price is not None:
            if "price" in filters:
                filters["price"]["gte"] = min_price
            else:
                filters["price"] = {"gte": min_price}
        if categories:
            filters["category"] = {"any": categories}
        
        # Search
        search_start = time.time()
        
        if use_mmr:
            results = await self.qdrant.mmr_search(
                collection="products",
                query_vector=embedding_result.embedding,
                limit=limit,
                score_threshold=score_threshold,
                diversity=diversity,
                filters=filters if filters else None,
                vector_name="image_vector"
            )
        else:
            results = await self.qdrant.semantic_search(
                collection="products",
                query_vector=embedding_result.embedding,
                limit=limit,
                score_threshold=score_threshold,
                filters=filters if filters else None,
                vector_name="image_vector"
            )
        
        search_time = (time.time() - search_start) * 1000
        total_time = (time.time() - start_time) * 1000
        
        # Format products
        products = []
        for r in results:
            payload = r.get("payload", {})
            products.append(SimilarProduct(
                product_id=str(r.get("id", "")),
                name=payload.get("name", "Unknown"),
                description=payload.get("description"),
                price=payload.get("price", 0.0),
                category=payload.get("category", "Unknown"),
                similarity_score=r.get("score", 0.0),
                image_url=payload.get("image_url"),
                brand=payload.get("brand"),
                rating=payload.get("rating")
            ))
        
        return ImageSearchResult(
            products=products,
            total_found=len(products),
            embedding_time_ms=embedding_time,
            search_time_ms=search_time,
            total_time_ms=total_time,
            filters_applied={
                "max_price": max_price,
                "min_price": min_price,
                "categories": categories
            },
            diversity_used=use_mmr
        )
    
    async def get_image_embedding(
        self,
        image_data: Optional[bytes] = None,
        image_base64: Optional[str] = None,
        image_url: Optional[str] = None
    ) -> List[float]:
        """Get image embedding without searching."""
        if not self.config.enable_image_search:
            raise ValueError("Image search is disabled")
        
        if image_data:
            result = await self.image_processor.generate_embedding(image_data)
        elif image_base64:
            result = await self.image_processor.generate_embedding_from_base64(image_base64)
        elif image_url:
            result = await self.image_processor.generate_embedding_from_url(image_url)
        else:
            raise ValueError("One of image_data, image_base64, or image_url must be provided")
        
        return result.embedding
    
    # ==========================================================================
    # Voice Operations
    # ==========================================================================
    
    def is_voice_input_enabled(self) -> bool:
        """Check if voice input is enabled."""
        return self.config.enable_voice_input
    
    async def transcribe_voice(
        self,
        audio_data: Optional[bytes] = None,
        audio_base64: Optional[str] = None,
        audio_format: str = "wav",
        language: Optional[str] = None,
        translate: bool = False
    ) -> VoiceTranscriptionResult:
        """
        Transcribe voice input to text.
        
        Args:
            audio_data: Raw audio bytes
            audio_base64: Base64-encoded audio
            audio_format: Audio format (wav, mp3, etc.)
            language: Language code or None for auto-detect
            translate: Translate to English
            
        Returns:
            VoiceTranscriptionResult with transcribed text
        """
        if not self.config.enable_voice_input:
            raise ValueError("Voice input is disabled")
        
        if audio_base64:
            return await self.voice_processor.transcribe_from_base64(
                audio_base64,
                audio_format=audio_format,
                language=language,
                translate=translate
            )
        elif audio_data:
            return await self.voice_processor.transcribe(
                audio_data,
                audio_format=audio_format,
                language=language,
                translate=translate
            )
        else:
            raise ValueError("Either audio_data or audio_base64 must be provided")
    
    async def search_by_voice(
        self,
        audio_data: Optional[bytes] = None,
        audio_base64: Optional[str] = None,
        audio_format: str = "wav",
        language: Optional[str] = None,
        limit: int = 10,
        max_price: Optional[float] = None,
        categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Search for products using voice input.
        
        Transcribes audio and performs semantic search.
        
        Returns:
            Dict with transcription and search results
        """
        if not self.config.enable_voice_input:
            raise ValueError("Voice input is disabled")
        
        # Transcribe
        transcription = await self.transcribe_voice(
            audio_data=audio_data,
            audio_base64=audio_base64,
            audio_format=audio_format,
            language=language
        )
        
        if not transcription.text:
            return {
                "transcription": transcription,
                "products": [],
                "message": "No speech detected in audio"
            }
        
        # Generate embedding for transcribed text
        query_embedding = await self.embedding.embed(transcription.text)
        
        # Build filters
        filters = {}
        if max_price is not None:
            filters["price"] = {"lte": max_price}
        if categories:
            filters["category"] = {"any": categories}
        
        # Search
        results = await self.qdrant.semantic_search(
            collection="products",
            query_vector=query_embedding,
            limit=limit,
            filters=filters if filters else None
        )
        
        # Format products
        products = []
        for r in results:
            payload = r.get("payload", {})
            products.append({
                "id": r.get("id"),
                "name": payload.get("name"),
                "price": payload.get("price"),
                "category": payload.get("category"),
                "score": r.get("score", 0.0)
            })
        
        return {
            "transcription": transcription,
            "query": transcription.text,
            "products": products,
            "total_found": len(products)
        }
    
    # ==========================================================================
    # Combined Operations
    # ==========================================================================
    
    async def multimodal_search(
        self,
        text_query: Optional[str] = None,
        image_data: Optional[bytes] = None,
        image_base64: Optional[str] = None,
        audio_data: Optional[bytes] = None,
        audio_base64: Optional[str] = None,
        limit: int = 10,
        max_price: Optional[float] = None,
        combine_results: bool = True
    ) -> Dict[str, Any]:
        """
        Perform multimodal search combining text, image, and voice inputs.
        
        Can combine results from multiple modalities or return separately.
        """
        results = {}
        all_products = []
        
        # Text search
        if text_query:
            query_embedding = await self.embedding.embed(text_query)
            
            filters = {}
            if max_price:
                filters["price"] = {"lte": max_price}
            
            text_results = await self.qdrant.semantic_search(
                collection="products",
                query_vector=query_embedding,
                limit=limit,
                filters=filters if filters else None
            )
            
            results["text_search"] = {
                "query": text_query,
                "products": text_results
            }
            all_products.extend(text_results)
        
        # Image search
        if (image_data or image_base64) and self.config.enable_image_search:
            image_result = await self.search_by_image(
                image_data=image_data,
                image_base64=image_base64,
                limit=limit,
                max_price=max_price
            )
            results["image_search"] = image_result
            all_products.extend([
                {"id": p.product_id, "payload": {"name": p.name, "price": p.price}, "score": p.similarity_score}
                for p in image_result.products
            ])
        
        # Voice search
        if (audio_data or audio_base64) and self.config.enable_voice_input:
            voice_result = await self.search_by_voice(
                audio_data=audio_data,
                audio_base64=audio_base64,
                limit=limit,
                max_price=max_price
            )
            results["voice_search"] = voice_result
            all_products.extend([
                {"id": p["id"], "payload": {"name": p["name"], "price": p["price"]}, "score": p["score"]}
                for p in voice_result.get("products", [])
            ])
        
        # Combine and deduplicate
        if combine_results and len(all_products) > 0:
            # Deduplicate by ID, keeping highest score
            seen = {}
            for product in all_products:
                pid = product.get("id")
                if pid:
                    if pid not in seen or product.get("score", 0) > seen[pid].get("score", 0):
                        seen[pid] = product
            
            # Sort by score and limit
            combined = sorted(seen.values(), key=lambda x: x.get("score", 0), reverse=True)
            results["combined_products"] = combined[:limit]
        
        return results
    
    # ==========================================================================
    # Utility Methods
    # ==========================================================================
    
    def get_supported_languages(self) -> List[str]:
        """Get supported languages for voice input."""
        return self.voice_processor.get_supported_languages()
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of multimodal services."""
        return {
            "image_search_enabled": self.config.enable_image_search,
            "voice_input_enabled": self.config.enable_voice_input,
            "image_backend": self.config.image.backend,
            "voice_backend": self.config.voice.backend,
            "image_embedding_dim": self.config.image.embedding_dimension,
            "supported_languages": self.config.voice.supported_languages
        }
    
    def clear_caches(self) -> Dict[str, int]:
        """Clear all caches."""
        cleared = {}
        
        if self._image_processor:
            cleared["image_embeddings"] = self._image_processor.clear_cache()
        
        if self._voice_processor:
            cleared["transcriptions"] = self._voice_processor.clear_cache()
        
        return cleared


# Singleton instance
_multimodal_service: Optional[MultimodalService] = None


def get_multimodal_service(
    config: Optional[MultimodalConfig] = None
) -> MultimodalService:
    """Get singleton multimodal service instance."""
    global _multimodal_service
    if _multimodal_service is None:
        _multimodal_service = MultimodalService(config)
    return _multimodal_service
