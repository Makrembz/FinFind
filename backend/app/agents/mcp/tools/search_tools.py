"""
MCP Search Tools for FinFind SearchAgent.

Tools for semantic search, query interpretation, and filtering.
"""

import logging
import re
from typing import Dict, Any, List, Optional

from pydantic import BaseModel, Field

from ..protocol import (
    MCPTool, MCPToolMetadata, MCPToolOutput,
    MCPError, MCPErrorCode
)
from ...services import get_qdrant_service, get_embedding_service, get_cache_service
from ...config import get_config

logger = logging.getLogger(__name__)


# ========================================
# Input Schemas
# ========================================

class SemanticSearchInput(BaseModel):
    """Input schema for semantic search."""
    query: str = Field(..., description="The search query text")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum results to return")
    category: Optional[str] = Field(default=None, description="Product category filter")
    min_price: Optional[float] = Field(default=None, ge=0, description="Minimum price filter")
    max_price: Optional[float] = Field(default=None, ge=0, description="Maximum price filter")
    brands: Optional[List[str]] = Field(default=None, description="Brand filter list")
    use_mmr: bool = Field(default=True, description="Use MMR for diversity")
    diversity: float = Field(default=0.3, ge=0, le=1, description="MMR diversity factor")


class FinancialFiltersInput(BaseModel):
    """Input schema for financial filters."""
    products: List[Dict[str, Any]] = Field(..., description="Products to filter")
    budget_max: Optional[float] = Field(default=None, description="Maximum budget")
    budget_min: Optional[float] = Field(default=None, description="Minimum budget")
    payment_methods: Optional[List[str]] = Field(default=None, description="Accepted payment methods")
    financing_required: bool = Field(default=False, description="Whether financing is needed")


class VagueQueryInput(BaseModel):
    """Input schema for vague query interpretation."""
    query: str = Field(..., description="The vague user query")
    user_context: Optional[Dict[str, Any]] = Field(default=None, description="User context for personalization")
    conversation_history: Optional[List[Dict]] = Field(default=None, description="Recent conversation messages")


class ImageSearchInput(BaseModel):
    """Input schema for image search."""
    image_url: Optional[str] = Field(default=None, description="URL of the image")
    image_base64: Optional[str] = Field(default=None, description="Base64 encoded image")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum results")
    category: Optional[str] = Field(default=None, description="Category filter")
    max_price: Optional[float] = Field(default=None, ge=0, description="Maximum price filter")
    min_price: Optional[float] = Field(default=None, ge=0, description="Minimum price filter")


class VoiceSearchInput(BaseModel):
    """Input schema for voice search."""
    audio_url: Optional[str] = Field(default=None, description="URL of audio file")
    audio_base64: Optional[str] = Field(default=None, description="Base64 encoded audio")
    language: str = Field(default="en", description="Audio language code (or 'auto' for detection)")
    audio_format: str = Field(default="wav", description="Audio format (wav, mp3, m4a, etc.)")
    auto_search: bool = Field(default=True, description="Automatically search after transcription")


# ========================================
# Qdrant Semantic Search Tool
# ========================================

class QdrantSemanticSearchTool(MCPTool):
    """
    MCP tool for semantic search on products with MMR.
    
    Features:
    - Vector similarity search via Qdrant
    - MMR for result diversity
    - Multi-field filtering
    - Score-based ranking
    """
    
    name: str = "qdrant_semantic_search"
    description: str = """
    Performs semantic vector search on the product catalog.
    Uses embeddings to find products matching the query meaning.
    Supports MMR (Maximal Marginal Relevance) for diverse results.
    Can filter by category, price range, and brands.
    """
    args_schema: type = SemanticSearchInput
    
    mcp_metadata: MCPToolMetadata = MCPToolMetadata(
        name="qdrant_semantic_search",
        description="Semantic search on products with MMR",
        category="search",
        tags=["search", "qdrant", "semantic", "mmr"],
        requires_qdrant=True,
        requires_embedding=True,
        cacheable=True,
        cache_ttl_seconds=300,
        avg_latency_ms=150
    )
    
    def _execute(
        self,
        query: str,
        limit: int = 10,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        brands: Optional[List[str]] = None,
        use_mmr: bool = True,
        diversity: float = 0.3
    ) -> MCPToolOutput:
        """Execute semantic search."""
        
        # Get services
        qdrant = get_qdrant_service()
        embedding_service = get_embedding_service()
        cache = get_cache_service()
        config = get_config()
        
        # Check cache
        cache_key = f"{query}:{limit}:{category}:{min_price}:{max_price}:{use_mmr}"
        cached = cache.get("semantic_search", cache_key)
        if cached:
            return MCPToolOutput.success_response(
                data=cached,
                cache_hit=True,
                query=query,
                result_count=len(cached.get("products", []))
            )
        
        try:
            # Generate query embedding
            query_vector = embedding_service.embed(query)
            
            # Build filters
            filters = {}
            if category:
                filters["category"] = category
            if min_price is not None or max_price is not None:
                price_range = {}
                if min_price is not None:
                    price_range["gte"] = min_price
                if max_price is not None:
                    price_range["lte"] = max_price
                filters["price"] = {"range": price_range}
            if brands:
                filters["brand"] = {"any": brands}
            
            # Perform search
            if use_mmr:
                results = qdrant.mmr_search(
                    collection=config.qdrant.products_collection,
                    query_vector=query_vector,
                    limit=limit,
                    diversity=diversity,
                    filters=filters if filters else None
                )
            else:
                results = qdrant.semantic_search(
                    collection=config.qdrant.products_collection,
                    query_vector=query_vector,
                    limit=limit,
                    filters=filters if filters else None
                )
            
            # Format results
            products = []
            for result in results:
                product = {
                    "id": result["id"],
                    "score": result["score"],
                    **result.get("payload", {})
                }
                products.append(product)
            
            response_data = {
                "query": query,
                "products": products,
                "total_results": len(products),
                "filters_applied": filters,
                "search_type": "mmr" if use_mmr else "similarity"
            }
            
            # Cache result
            cache.set("semantic_search", cache_key, response_data, ttl=300)
            
            return MCPToolOutput.success_response(
                data=response_data,
                query=query,
                result_count=len(products)
            )
            
        except MCPError:
            raise
        except Exception as e:
            logger.exception(f"Semantic search failed: {e}")
            raise MCPError(
                code=MCPErrorCode.VECTOR_SEARCH_FAILED,
                message=f"Search failed: {str(e)}",
                details={"query": query}
            )


# ========================================
# Apply Financial Filters Tool
# ========================================

class ApplyFinancialFiltersTool(MCPTool):
    """
    MCP tool for applying financial filters to products.
    
    Filters products based on:
    - Budget constraints
    - Payment method availability
    - Financing options
    """
    
    name: str = "apply_financial_filters"
    description: str = """
    Filters products based on user's financial constraints.
    Applies budget limits, checks payment methods, and financing options.
    Returns filtered products with affordability indicators.
    """
    args_schema: type = FinancialFiltersInput
    
    mcp_metadata: MCPToolMetadata = MCPToolMetadata(
        name="apply_financial_filters",
        description="Filter products by financial constraints",
        category="search",
        tags=["filter", "financial", "budget"],
        requires_qdrant=False,
        cacheable=False,
        avg_latency_ms=10
    )
    
    def _execute(
        self,
        products: List[Dict[str, Any]],
        budget_max: Optional[float] = None,
        budget_min: Optional[float] = None,
        payment_methods: Optional[List[str]] = None,
        financing_required: bool = False
    ) -> MCPToolOutput:
        """Apply financial filters to products."""
        
        if not products:
            return MCPToolOutput.success_response(
                data={"products": [], "filtered_count": 0, "original_count": 0}
            )
        
        filtered = []
        filter_stats = {
            "budget_filtered": 0,
            "payment_filtered": 0,
            "financing_filtered": 0
        }
        
        for product in products:
            price = product.get("price", 0)
            
            # Budget filter
            if budget_max and price > budget_max:
                filter_stats["budget_filtered"] += 1
                continue
            if budget_min and price < budget_min:
                filter_stats["budget_filtered"] += 1
                continue
            
            # Payment method filter
            if payment_methods:
                product_payments = product.get("payment_methods", [])
                if not any(pm in product_payments for pm in payment_methods):
                    filter_stats["payment_filtered"] += 1
                    continue
            
            # Financing filter
            if financing_required:
                has_financing = product.get("financing_available", False)
                if not has_financing:
                    filter_stats["financing_filtered"] += 1
                    continue
            
            # Calculate affordability score
            affordability = 1.0
            if budget_max and price > 0:
                affordability = 1 - (price / budget_max)
                affordability = max(0, min(1, affordability))
            
            product["affordability_score"] = round(affordability, 2)
            product["within_budget"] = True
            filtered.append(product)
        
        # Sort by affordability (most affordable first)
        filtered.sort(key=lambda x: x.get("affordability_score", 0), reverse=True)
        
        return MCPToolOutput.success_response(
            data={
                "products": filtered,
                "filtered_count": len(filtered),
                "original_count": len(products),
                "filter_stats": filter_stats,
                "filters_applied": {
                    "budget_max": budget_max,
                    "budget_min": budget_min,
                    "payment_methods": payment_methods,
                    "financing_required": financing_required
                }
            }
        )


# ========================================
# Interpret Vague Query Tool
# ========================================

class InterpretVagueQueryTool(MCPTool):
    """
    MCP tool for interpreting vague user queries.
    
    Enhances ambiguous queries with:
    - Intent detection
    - Category inference
    - Budget extraction
    - Query expansion
    """
    
    name: str = "interpret_vague_query"
    description: str = """
    Interprets and enhances vague or ambiguous user queries.
    Detects user intent, infers categories, extracts budget hints.
    Returns an enriched query with additional context.
    """
    args_schema: type = VagueQueryInput
    
    mcp_metadata: MCPToolMetadata = MCPToolMetadata(
        name="interpret_vague_query",
        description="Enhance vague queries with context",
        category="search",
        tags=["nlp", "query", "interpretation"],
        requires_llm=True,
        cacheable=True,
        cache_ttl_seconds=600,
        avg_latency_ms=200
    )
    
    # Intent patterns
    INTENT_PATTERNS = {
        "browse": r"\b(looking|browsing|show|what|see)\b",
        "compare": r"\b(compare|versus|vs|difference|better)\b",
        "recommend": r"\b(recommend|suggest|best|top|good)\b",
        "specific": r"\b(need|want|looking for|find|get)\b",
        "budget": r"\b(cheap|affordable|budget|under|less than)\b",
        "quality": r"\b(premium|quality|best|high-end|luxury)\b"
    }
    
    # Category keywords
    CATEGORY_KEYWORDS = {
        "electronics": ["laptop", "phone", "computer", "tablet", "tv", "camera", "headphones"],
        "clothing": ["shirt", "pants", "dress", "shoes", "jacket", "clothes", "wear"],
        "home": ["furniture", "kitchen", "decor", "bed", "sofa", "table", "chair"],
        "sports": ["fitness", "gym", "running", "sports", "outdoor", "exercise"],
        "beauty": ["makeup", "skincare", "beauty", "cosmetics", "perfume"]
    }
    
    # Budget extraction patterns
    BUDGET_PATTERNS = [
        (r"\$(\d+(?:,\d{3})*(?:\.\d{2})?)", lambda m: float(m.group(1).replace(",", ""))),
        (r"under\s+\$?(\d+)", lambda m: float(m.group(1))),
        (r"less than\s+\$?(\d+)", lambda m: float(m.group(1))),
        (r"(\d+)\s+(?:dollars|bucks)", lambda m: float(m.group(1))),
        (r"budget\s+(?:of\s+)?\$?(\d+)", lambda m: float(m.group(1)))
    ]
    
    def _execute(
        self,
        query: str,
        user_context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> MCPToolOutput:
        """Interpret vague query."""
        
        query_lower = query.lower()
        
        # Detect intents
        intents = []
        for intent, pattern in self.INTENT_PATTERNS.items():
            if re.search(pattern, query_lower):
                intents.append(intent)
        
        if not intents:
            intents = ["browse"]  # Default intent
        
        # Infer categories
        inferred_categories = []
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if any(kw in query_lower for kw in keywords):
                inferred_categories.append(category)
        
        # Extract budget
        extracted_budget = None
        for pattern, extractor in self.BUDGET_PATTERNS:
            match = re.search(pattern, query_lower)
            if match:
                try:
                    extracted_budget = extractor(match)
                    break
                except:
                    pass
        
        # Check user context for budget hints
        if extracted_budget is None and user_context:
            extracted_budget = user_context.get("budget_max")
        
        # Extract key terms
        stopwords = {"a", "an", "the", "is", "are", "for", "me", "i", "want", "need", "looking"}
        words = query_lower.split()
        key_terms = [w for w in words if w not in stopwords and len(w) > 2]
        
        # Build expanded query
        expanded_parts = [query]
        if inferred_categories:
            expanded_parts.append(f"category: {inferred_categories[0]}")
        
        # Quality indicators
        quality_level = "standard"
        if "budget" in intents or any(w in query_lower for w in ["cheap", "affordable"]):
            quality_level = "budget"
        elif "quality" in intents or any(w in query_lower for w in ["premium", "best", "luxury"]):
            quality_level = "premium"
        
        # Use conversation history for context
        previous_products = []
        if conversation_history:
            for msg in conversation_history[-3:]:
                if msg.get("products"):
                    previous_products.extend(msg["products"][:2])
        
        return MCPToolOutput.success_response(
            data={
                "original_query": query,
                "interpreted": {
                    "intents": intents,
                    "primary_intent": intents[0] if intents else "browse",
                    "categories": inferred_categories,
                    "budget": extracted_budget,
                    "quality_level": quality_level,
                    "key_terms": key_terms
                },
                "expanded_query": " ".join(expanded_parts),
                "search_hints": {
                    "category_filter": inferred_categories[0] if inferred_categories else None,
                    "max_price": extracted_budget,
                    "sort_by": "price" if "budget" in intents else "relevance"
                },
                "context_products": previous_products[:3] if previous_products else []
            }
        )


# ========================================
# Image Similarity Search Tool
# ========================================

class ImageSimilaritySearchTool(MCPTool):
    """
    MCP tool for image-based product search.
    
    Finds products similar to an uploaded image using CLIP embeddings.
    """
    
    name: str = "image_similarity_search"
    description: str = """
    Searches for products similar to an uploaded image.
    Uses CLIP image embeddings to find visually similar products.
    Supports image URL or base64 encoded image data.
    Can filter by category and price range.
    """
    args_schema: type = ImageSearchInput
    
    mcp_metadata: MCPToolMetadata = MCPToolMetadata(
        name="image_similarity_search",
        description="Search products by image similarity using CLIP",
        category="search",
        tags=["image", "visual", "similarity", "clip"],
        requires_qdrant=True,
        requires_embedding=True,
        cacheable=True,
        cache_ttl_seconds=600,
        avg_latency_ms=500
    )
    
    async def _execute_async(
        self,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        limit: int = 10,
        category: Optional[str] = None,
        max_price: Optional[float] = None,
        min_price: Optional[float] = None
    ) -> MCPToolOutput:
        """Execute image similarity search using CLIP."""
        import asyncio
        
        if not image_url and not image_base64:
            raise MCPError(
                code=MCPErrorCode.MISSING_PARAMETER,
                message="Either image_url or image_base64 must be provided"
            )
        
        try:
            # Import multimodal processor
            from ....multimodal.image_processor import get_image_processor
            from ....multimodal.config import get_multimodal_config
            
            config = get_multimodal_config()
            if not config.enable_image_search:
                return MCPToolOutput.success_response(
                    data={
                        "products": [],
                        "message": "Image search is disabled in configuration",
                        "supported": False
                    }
                )
            
            image_processor = get_image_processor()
            qdrant = get_qdrant_service()
            
            # Generate image embedding
            if image_base64:
                embedding_result = await image_processor.generate_embedding_from_base64(
                    image_base64
                )
            else:
                embedding_result = await image_processor.generate_embedding_from_url(
                    image_url
                )
            
            # Build filters
            filters = {}
            if category:
                filters["category"] = {"match": category}
            if max_price is not None:
                filters["price"] = {"lte": max_price}
            if min_price is not None:
                if "price" in filters:
                    filters["price"]["gte"] = min_price
                else:
                    filters["price"] = {"gte": min_price}
            
            # Search against image_vector field
            results = await qdrant.mmr_search(
                collection="products",
                query_vector=embedding_result.embedding,
                limit=limit,
                score_threshold=0.4,
                diversity=0.3,
                filters=filters if filters else None,
                vector_name="image_vector"
            )
            
            # Format results
            products = []
            for r in results:
                payload = r.get("payload", {})
                products.append({
                    "id": r.get("id"),
                    "name": payload.get("name"),
                    "description": payload.get("description"),
                    "price": payload.get("price"),
                    "category": payload.get("category"),
                    "image_url": payload.get("image_url"),
                    "similarity_score": r.get("score", 0.0)
                })
            
            return MCPToolOutput.success_response(
                data={
                    "products": products,
                    "total_found": len(products),
                    "embedding_model": embedding_result.model_used,
                    "embedding_time_ms": embedding_result.processing_time_ms,
                    "supported": True
                }
            )
            
        except ImportError as e:
            logger.warning(f"Image processor not available: {e}")
            return MCPToolOutput.success_response(
                data={
                    "products": [],
                    "message": "Image search requires multimodal module. Install with: pip install transformers torch pillow",
                    "supported": False,
                    "suggestion": "Please describe what you see in the image, and I'll search for similar products"
                }
            )
        except Exception as e:
            logger.error(f"Image search error: {e}", exc_info=True)
            raise MCPError(
                code=MCPErrorCode.INTERNAL_ERROR,
                message=f"Image search failed: {str(e)}"
            )
    
    def _execute(
        self,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        limit: int = 10,
        category: Optional[str] = None,
        max_price: Optional[float] = None,
        min_price: Optional[float] = None
    ) -> MCPToolOutput:
        """Sync wrapper for async execution."""
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self._execute_async(
                image_url=image_url,
                image_base64=image_base64,
                limit=limit,
                category=category,
                max_price=max_price,
                min_price=min_price
            )
        )


# ========================================
# Voice to Text Search Tool
# ========================================

class VoiceToTextSearchTool(MCPTool):
    """
    MCP tool for voice-based search.
    
    Converts voice input to text using Whisper and performs search.
    """
    
    name: str = "voice_to_text_search"
    description: str = """
    Converts voice input to text for searching.
    Uses Whisper for speech-to-text transcription.
    Supports multiple languages with auto-detection.
    Returns transcribed text and optionally search results.
    """
    args_schema: type = VoiceSearchInput
    
    mcp_metadata: MCPToolMetadata = MCPToolMetadata(
        name="voice_to_text_search",
        description="Convert voice to text using Whisper for search",
        category="search",
        tags=["voice", "speech", "transcription", "whisper"],
        requires_llm=False,
        cacheable=False,
        avg_latency_ms=1000
    )
    
    async def _execute_async(
        self,
        audio_url: Optional[str] = None,
        audio_base64: Optional[str] = None,
        language: str = "en",
        audio_format: str = "wav",
        auto_search: bool = True
    ) -> MCPToolOutput:
        """Execute voice to text conversion using Whisper."""
        import asyncio
        
        if not audio_url and not audio_base64:
            raise MCPError(
                code=MCPErrorCode.MISSING_PARAMETER,
                message="Either audio_url or audio_base64 must be provided"
            )
        
        try:
            # Import multimodal processor
            from ....multimodal.voice_processor import get_voice_processor
            from ....multimodal.config import get_multimodal_config
            
            config = get_multimodal_config()
            if not config.enable_voice_input:
                return MCPToolOutput.success_response(
                    data={
                        "transcribed_text": "",
                        "message": "Voice input is disabled in configuration",
                        "supported": False
                    }
                )
            
            voice_processor = get_voice_processor()
            
            # Get audio data
            if audio_base64:
                import base64
                audio_data = base64.b64decode(audio_base64)
            else:
                # Fetch from URL
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.get(audio_url, timeout=30.0)
                    response.raise_for_status()
                    audio_data = response.content
            
            # Transcribe audio
            transcription = await voice_processor.transcribe(
                audio_data,
                audio_format=audio_format,
                language=language if language != "auto" else None,
                translate=False
            )
            
            result_data = {
                "transcribed_text": transcription.text,
                "detected_language": transcription.detected_language,
                "audio_duration": transcription.audio_duration_seconds,
                "processing_time_ms": transcription.processing_time_ms,
                "model_used": transcription.model_used,
                "supported": True
            }
            
            # Optionally perform search with transcribed text
            if auto_search and transcription.text:
                qdrant = get_qdrant_service()
                embedding_service = get_embedding_service()
                
                # Generate embedding for transcribed text
                query_vector = await embedding_service.embed(transcription.text)
                
                # Search products
                search_results = await qdrant.semantic_search(
                    collection="products",
                    query_vector=query_vector,
                    limit=10,
                    score_threshold=0.3
                )
                
                products = []
                for r in search_results:
                    payload = r.get("payload", {})
                    products.append({
                        "id": r.get("id"),
                        "name": payload.get("name"),
                        "price": payload.get("price"),
                        "category": payload.get("category"),
                        "score": r.get("score", 0.0)
                    })
                
                result_data["search_results"] = {
                    "query": transcription.text,
                    "products": products,
                    "total_found": len(products)
                }
            
            return MCPToolOutput.success_response(data=result_data)
            
        except ImportError as e:
            logger.warning(f"Voice processor not available: {e}")
            return MCPToolOutput.success_response(
                data={
                    "transcribed_text": "",
                    "message": "Voice search requires multimodal module. Install with: pip install openai-whisper soundfile",
                    "supported": False,
                    "suggestion": "Please type your search query instead"
                }
            )
        except Exception as e:
            logger.error(f"Voice search error: {e}", exc_info=True)
            raise MCPError(
                code=MCPErrorCode.INTERNAL_ERROR,
                message=f"Voice transcription failed: {str(e)}"
            )
    
    def _execute(
        self,
        audio_url: Optional[str] = None,
        audio_base64: Optional[str] = None,
        language: str = "en",
        audio_format: str = "wav",
        auto_search: bool = True
    ) -> MCPToolOutput:
        """Sync wrapper for async execution."""
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self._execute_async(
                audio_url=audio_url,
                audio_base64=audio_base64,
                language=language,
                audio_format=audio_format,
                auto_search=auto_search
            )
        )
