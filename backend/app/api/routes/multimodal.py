"""
Multimodal API routes for image and voice search.

Provides endpoints for:
- Image upload and visual search
- Voice upload and transcription
- Combined multimodal search
"""

import logging
import uuid
import time
import base64
from typing import Optional, List

from fastapi import (
    APIRouter,
    Depends,
    File,
    UploadFile,
    Form,
    HTTPException,
    status,
    Request
)
from pydantic import BaseModel, Field

from ..dependencies import (
    get_image_processor,
    get_voice_processor,
    get_qdrant_service,
    get_current_user,
    check_rate_limit,
    UserContext
)
from ...multimodal.image_processor import ImageProcessor
from ...multimodal.voice_processor import VoiceProcessor
from ...multimodal.schemas import (
    ImageSearchRequest,
    ImageSearchResponse,
    ImageSearchResult,
    SimilarProduct,
    VoiceSearchRequest,
    VoiceSearchResponse,
    VoiceTranscriptionResult,
    MultimodalError,
    MultimodalErrorCode
)
from ...agents.services.qdrant_service import QdrantService
from ...agents.services.ranking_service import rank_search_results, RankingStrategy

logger = logging.getLogger(__name__)

router = APIRouter()


# ==============================================================================
# Request/Response Models
# ==============================================================================

class ImageSearchRequestBody(BaseModel):
    """Request body for image search (when using base64)."""
    image_base64: Optional[str] = Field(
        default=None,
        description="Base64-encoded image"
    )
    image_url: Optional[str] = Field(
        default=None,
        description="URL to fetch image from"
    )
    max_price: Optional[float] = Field(default=None, ge=0)
    min_price: Optional[float] = Field(default=None, ge=0)
    categories: Optional[List[str]] = None
    limit: int = Field(default=10, ge=1, le=50)
    score_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    use_mmr: bool = Field(default=True)
    diversity_factor: float = Field(default=0.3, ge=0.0, le=1.0)


class VoiceSearchRequestBody(BaseModel):
    """Request body for voice search (when using base64)."""
    audio_base64: str = Field(description="Base64-encoded audio")
    audio_format: str = Field(default="wav")
    language: Optional[str] = Field(default=None)
    translate_to_english: bool = Field(default=False)
    auto_search: bool = Field(default=True)
    search_limit: int = Field(default=10, ge=1, le=50)
    max_budget: Optional[float] = Field(default=None, ge=0)


class TranscriptionResponse(BaseModel):
    """Response for transcription-only endpoint."""
    success: bool
    text: Optional[str] = None
    detected_language: Optional[str] = None
    duration_seconds: Optional[float] = None
    processing_time_ms: Optional[float] = None
    error: Optional[str] = None
    request_id: str


# ==============================================================================
# Image Search Endpoints
# ==============================================================================

@router.post("/image/search", response_model=ImageSearchResponse)
async def search_by_image(
    request: Request,
    file: UploadFile = File(..., description="Image file to search with"),
    max_price: Optional[float] = Form(None),
    min_price: Optional[float] = Form(None),
    categories: Optional[str] = Form(None, description="Comma-separated categories"),
    limit: int = Form(10),
    score_threshold: float = Form(0.5),
    use_mmr: bool = Form(True),
    diversity_factor: float = Form(0.3),
    image_processor: ImageProcessor = Depends(get_image_processor),
    qdrant_service: QdrantService = Depends(get_qdrant_service),
    user: Optional[UserContext] = Depends(get_current_user),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    Search for products using an uploaded image.
    
    Upload a product image to find visually similar items in the catalog.
    Results can be filtered by price range and categories.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    start_time = time.time()
    
    try:
        # Validate file
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )
        
        # Read image data
        image_data = await file.read()
        
        logger.info(
            f"Image search request: {len(image_data)} bytes, "
            f"user={user.user_id if user else 'anonymous'}"
        )
        
        # Generate image embedding
        embedding_start = time.time()
        embedding_result = await image_processor.generate_embedding(image_data)
        embedding_time = (time.time() - embedding_start) * 1000
        
        # Search Qdrant
        search_start = time.time()
        
        # Build filters - use "range" wrapper for numeric conditions
        filters = {}
        if min_price is not None or max_price is not None:
            price_range = {}
            if min_price is not None:
                price_range["gte"] = min_price
            if max_price is not None:
                price_range["lte"] = max_price
            filters["price"] = {"range": price_range}
        
        if categories:
            category_list = [c.strip() for c in categories.split(",")]
            filters["category"] = {"any": category_list}
        
        # Perform search using "image" named vector
        # The embedding is generated from CLIP (512-dim) for image similarity search
        if use_mmr:
            search_results = qdrant_service.mmr_search(
                collection="products",
                query_vector=embedding_result.embedding,
                limit=limit,
                diversity=diversity_factor,
                filters=filters if filters else None,
                vector_name="image"  # Search against image embeddings
            )
        else:
            search_results = qdrant_service.semantic_search(
                collection="products",
                query_vector=embedding_result.embedding,
                limit=limit * 2,  # Fetch more for ranking
                score_threshold=score_threshold,
                filters=filters if filters else None,
                vector_name="image"  # Search against image embeddings
            )
        
        search_time = (time.time() - search_start) * 1000
        
        # Apply ranking for better results
        ranking_context = None
        if user:
            ranking_context = {
                "user_id": user.user_id,
                "budget_max": max_price,
                "budget_min": min_price,
                "preferred_categories": [c.strip() for c in categories.split(",")] if categories else [],
                "price_sensitivity": 0.5
            }
        
        ranked_results = rank_search_results(
            products=search_results,
            strategy=RankingStrategy.BALANCED,
            user_context=ranking_context,
            diversity_factor=diversity_factor if use_mmr else 0,
            query="image search"
        )
        
        # Limit to requested count after ranking
        ranked_results = ranked_results[:limit]
        
        # Format results
        products = []
        for idx, result in enumerate(ranked_results):
            outer_payload = result.get("payload", {})
            payload = outer_payload.get("payload", outer_payload)  # Handle nested payload
            products.append(SimilarProduct(
                product_id=result.get("id", ""),
                name=payload.get("title", payload.get("name", "Unknown Product")),
                description=payload.get("description"),
                price=payload.get("price", 0.0),
                category=payload.get("category", "Unknown"),
                similarity_score=result.get("score", 0.0),
                image_url=payload.get("image_url"),
                brand=payload.get("brand"),
                rating=payload.get("rating_avg", payload.get("rating")),
                visual_match_reasons=_generate_visual_match_reasons(
                    result.get("score", 0.0)
                ),
                ranking_score=result.get("ranking_score"),
                rank=idx + 1
            ))
        
        total_time = (time.time() - start_time) * 1000
        
        return ImageSearchResponse(
            success=True,
            result=ImageSearchResult(
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
                diversity_used=use_mmr,
                search_summary=_generate_search_summary(len(products), categories)
            ),
            request_id=request_id
        )
        
    except ValueError as e:
        logger.warning(f"Image search validation error: {e}")
        return ImageSearchResponse(
            success=False,
            error=MultimodalError(
                code=MultimodalErrorCode.INVALID_IMAGE_FORMAT,
                message=str(e)
            ),
            request_id=request_id
        )
    except Exception as e:
        logger.error(f"Image search error: {e}", exc_info=True)
        return ImageSearchResponse(
            success=False,
            error=MultimodalError(
                code=MultimodalErrorCode.IMAGE_PROCESSING_FAILED,
                message=f"Image search failed: {str(e)}"
            ),
            request_id=request_id
        )


@router.post("/image/search-json", response_model=ImageSearchResponse)
async def search_by_image_json(
    request: Request,
    body: ImageSearchRequestBody,
    image_processor: ImageProcessor = Depends(get_image_processor),
    qdrant_service: QdrantService = Depends(get_qdrant_service),
    user: Optional[UserContext] = Depends(get_current_user),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    Search for products using a base64-encoded image or image URL.
    
    Alternative to file upload for programmatic access.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    start_time = time.time()
    
    try:
        # Generate embedding
        embedding_start = time.time()
        
        if body.image_base64:
            embedding_result = await image_processor.generate_embedding_from_base64(
                body.image_base64
            )
        elif body.image_url:
            embedding_result = await image_processor.generate_embedding_from_url(
                body.image_url
            )
        else:
            raise ValueError("Either image_base64 or image_url must be provided")
        
        embedding_time = (time.time() - embedding_start) * 1000
        
        # Build filters
        filters = {}
        if body.max_price is not None:
            filters["price"] = {"lte": body.max_price}
        if body.min_price is not None:
            if "price" in filters:
                filters["price"]["gte"] = body.min_price
            else:
                filters["price"] = {"gte": body.min_price}
        
        if body.categories:
            filters["category"] = {"any": body.categories}
        
        # Search using "image" named vector
        search_start = time.time()
        
        if body.use_mmr:
            search_results = qdrant_service.mmr_search(
                collection="products",
                query_vector=embedding_result.embedding,
                limit=body.limit,
                diversity=body.diversity_factor,
                filters=filters if filters else None,
                vector_name="image"  # Search against image embeddings
            )
        else:
            search_results = qdrant_service.semantic_search(
                collection="products",
                query_vector=embedding_result.embedding,
                limit=body.limit,
                score_threshold=body.score_threshold,
                filters=filters if filters else None,
                vector_name="image"  # Search against image embeddings
            )
        
        search_time = (time.time() - search_start) * 1000
        total_time = (time.time() - start_time) * 1000
        
        # Format results
        products = []
        for r in search_results:
            outer_payload = r.get("payload", {})
            payload = outer_payload.get("payload", outer_payload)  # Handle nested payload
            products.append(SimilarProduct(
                product_id=r.get("id", ""),
                name=payload.get("title", payload.get("name", "Unknown")),
                description=payload.get("description"),
                price=payload.get("price", 0.0),
                category=payload.get("category", "Unknown"),
                similarity_score=r.get("score", 0.0),
                image_url=payload.get("image_url"),
                brand=payload.get("brand"),
                rating=payload.get("rating_avg", payload.get("rating"))
            ))
        
        return ImageSearchResponse(
            success=True,
            result=ImageSearchResult(
                products=products,
                total_found=len(products),
                embedding_time_ms=embedding_time,
                search_time_ms=search_time,
                total_time_ms=total_time,
                filters_applied={
                    "max_price": body.max_price,
                    "min_price": body.min_price,
                    "categories": body.categories
                },
                diversity_used=body.use_mmr
            ),
            request_id=request_id
        )
        
    except Exception as e:
        logger.error(f"Image search JSON error: {e}", exc_info=True)
        return ImageSearchResponse(
            success=False,
            error=MultimodalError(
                code=MultimodalErrorCode.IMAGE_PROCESSING_FAILED,
                message=str(e)
            ),
            request_id=request_id
        )


@router.post("/image/embedding")
async def generate_image_embedding(
    request: Request,
    file: UploadFile = File(...),
    image_processor: ImageProcessor = Depends(get_image_processor),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    Generate embedding for an image without searching.
    
    Useful for batch processing or custom search logic.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    try:
        image_data = await file.read()
        result = await image_processor.generate_embedding(image_data)
        
        return {
            "success": True,
            "embedding": result.embedding,
            "dimension": result.dimension,
            "model": result.model_used,
            "processing_time_ms": result.processing_time_ms,
            "request_id": request_id
        }
    except Exception as e:
        logger.error(f"Embedding generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==============================================================================
# Voice Search Endpoints
# ==============================================================================

@router.post("/voice/search", response_model=VoiceSearchResponse)
async def search_by_voice(
    request: Request,
    file: UploadFile = File(..., description="Audio file with voice query"),
    language: Optional[str] = Form(None),
    translate_to_english: bool = Form(False),
    auto_search: bool = Form(True),
    search_limit: int = Form(10),
    max_budget: Optional[float] = Form(None),
    voice_processor: VoiceProcessor = Depends(get_voice_processor),
    qdrant_service: QdrantService = Depends(get_qdrant_service),
    user: Optional[UserContext] = Depends(get_current_user),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    Search for products using voice input.
    
    Upload an audio file with a spoken search query. The audio is
    transcribed and used to search for products.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    try:
        # Validate file
        content_type = file.content_type or ""
        if not content_type.startswith("audio/"):
            # Accept common audio MIME types
            allowed_types = [
                "audio/wav", "audio/mp3", "audio/mpeg", "audio/m4a",
                "audio/webm", "audio/ogg", "audio/flac",
                "application/octet-stream"  # Sometimes audio is sent as this
            ]
            if content_type not in allowed_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File must be audio. Got: {content_type}"
                )
        
        # Read audio data
        audio_data = await file.read()
        
        # Determine format from filename
        filename = file.filename or "audio.wav"
        audio_format = filename.rsplit(".", 1)[-1].lower()
        if audio_format not in ["wav", "mp3", "m4a", "webm", "ogg", "flac"]:
            audio_format = "wav"
        
        logger.info(
            f"Voice search request: {len(audio_data)} bytes, format={audio_format}, "
            f"user={user.user_id if user else 'anonymous'}"
        )
        
        # Transcribe
        transcription = await voice_processor.transcribe(
            audio_data,
            audio_format=audio_format,
            language=language,
            translate=translate_to_english
        )
        
        # Search if requested
        search_results = None
        if auto_search and transcription.text:
            # Generate text embedding
            from ...agents.services.embedding_service import get_embedding_service
            embedding_service = get_embedding_service()
            
            query_embedding = await embedding_service.embed(transcription.text)
            
            # Build filters
            filters = {}
            if max_budget is not None:
                filters["price"] = {"lte": max_budget}
            
            # Search
            results = await qdrant_service.semantic_search(
                collection="products",
                query_vector=query_embedding,
                limit=search_limit,
                filters=filters if filters else None
            )
            
            search_results = {
                "query": transcription.text,
                "products": [
                    {
                        "id": r.get("id"),
                        "name": (r.get("payload", {}).get("payload", r.get("payload", {})).get("title") or
                                 r.get("payload", {}).get("payload", r.get("payload", {})).get("name")),
                        "price": r.get("payload", {}).get("payload", r.get("payload", {})).get("price"),
                        "category": r.get("payload", {}).get("payload", r.get("payload", {})).get("category"),
                        "score": r.get("score")
                    }
                    for r in results
                ]
            }
        
        return VoiceSearchResponse(
            success=True,
            transcription=transcription,
            search_results=search_results,
            request_id=request_id,
            summary=_generate_voice_summary(transcription, search_results)
        )
        
    except ValueError as e:
        logger.warning(f"Voice search validation error: {e}")
        return VoiceSearchResponse(
            success=False,
            error=MultimodalError(
                code=MultimodalErrorCode.INVALID_AUDIO_FORMAT,
                message=str(e)
            ),
            request_id=request_id
        )
    except Exception as e:
        logger.error(f"Voice search error: {e}", exc_info=True)
        return VoiceSearchResponse(
            success=False,
            error=MultimodalError(
                code=MultimodalErrorCode.TRANSCRIPTION_FAILED,
                message=f"Voice search failed: {str(e)}"
            ),
            request_id=request_id
        )


@router.post("/voice/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    request: Request,
    file: UploadFile = File(...),
    language: Optional[str] = Form(None),
    translate_to_english: bool = Form(False),
    voice_processor: VoiceProcessor = Depends(get_voice_processor),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    Transcribe audio without searching.
    
    Use this endpoint to convert speech to text without performing a search.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    try:
        audio_data = await file.read()
        filename = file.filename or "audio.wav"
        audio_format = filename.rsplit(".", 1)[-1].lower()
        
        transcription = await voice_processor.transcribe(
            audio_data,
            audio_format=audio_format,
            language=language,
            translate=translate_to_english
        )
        
        return TranscriptionResponse(
            success=True,
            text=transcription.text,
            detected_language=transcription.detected_language,
            duration_seconds=transcription.audio_duration_seconds,
            processing_time_ms=transcription.processing_time_ms,
            request_id=request_id
        )
        
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return TranscriptionResponse(
            success=False,
            error=str(e),
            request_id=request_id
        )


@router.post("/voice/search-json", response_model=VoiceSearchResponse)
async def search_by_voice_json(
    request: Request,
    body: VoiceSearchRequestBody,
    voice_processor: VoiceProcessor = Depends(get_voice_processor),
    qdrant_service: QdrantService = Depends(get_qdrant_service),
    user: Optional[UserContext] = Depends(get_current_user),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    Search for products using base64-encoded audio.
    
    Alternative to file upload for programmatic access.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    try:
        # Transcribe
        transcription = await voice_processor.transcribe_from_base64(
            body.audio_base64,
            audio_format=body.audio_format,
            language=body.language,
            translate=body.translate_to_english
        )
        
        # Search if requested
        search_results = None
        if body.auto_search and transcription.text:
            from ...agents.services.embedding_service import get_embedding_service
            embedding_service = get_embedding_service()
            
            query_embedding = await embedding_service.embed(transcription.text)
            
            filters = {}
            if body.max_budget is not None:
                filters["price"] = {"lte": body.max_budget}
            
            results = await qdrant_service.semantic_search(
                collection="products",
                query_vector=query_embedding,
                limit=body.search_limit,
                filters=filters if filters else None
            )
            
            search_results = {
                "query": transcription.text,
                "products": [
                    {
                        "id": r.get("id"),
                        "name": (r.get("payload", {}).get("payload", r.get("payload", {})).get("title") or
                                 r.get("payload", {}).get("payload", r.get("payload", {})).get("name")),
                        "price": r.get("payload", {}).get("payload", r.get("payload", {})).get("price"),
                        "score": r.get("score")
                    }
                    for r in results
                ]
            }
        
        return VoiceSearchResponse(
            success=True,
            transcription=transcription,
            search_results=search_results,
            request_id=request_id,
            summary=_generate_voice_summary(transcription, search_results)
        )
        
    except Exception as e:
        logger.error(f"Voice search JSON error: {e}")
        return VoiceSearchResponse(
            success=False,
            error=MultimodalError(
                code=MultimodalErrorCode.TRANSCRIPTION_FAILED,
                message=str(e)
            ),
            request_id=request_id
        )


# ==============================================================================
# Helper Functions
# ==============================================================================

def _generate_visual_match_reasons(score: float) -> List[str]:
    """Generate reasons for visual similarity."""
    reasons = []
    
    if score > 0.9:
        reasons.append("Very similar visual appearance")
        reasons.append("Matching color scheme")
        reasons.append("Similar shape and design")
    elif score > 0.7:
        reasons.append("Similar visual style")
        reasons.append("Related design elements")
    elif score > 0.5:
        reasons.append("Some visual similarities")
        reasons.append("Related product category")
    else:
        reasons.append("Loosely related appearance")
    
    return reasons


def _generate_search_summary(count: int, categories: Optional[str]) -> str:
    """Generate natural language search summary."""
    if count == 0:
        return "No visually similar products found matching your criteria."
    
    summary = f"Found {count} visually similar product"
    if count > 1:
        summary += "s"
    
    if categories:
        summary += f" in {categories}"
    
    return summary + "."


def _generate_voice_summary(
    transcription: VoiceTranscriptionResult,
    search_results: Optional[dict]
) -> str:
    """Generate summary for voice search."""
    parts = []
    
    # Transcription part
    if transcription.was_translated:
        parts.append(f'Understood: "{transcription.text}" (translated from {transcription.detected_language})')
    else:
        parts.append(f'Understood: "{transcription.text}"')
    
    # Search part
    if search_results:
        count = len(search_results.get("products", []))
        if count > 0:
            parts.append(f"Found {count} matching products.")
        else:
            parts.append("No matching products found.")
    
    return " ".join(parts)
