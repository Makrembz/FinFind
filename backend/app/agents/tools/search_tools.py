"""
Search Tools for FinFind SearchAgent.

Provides tools for query interpretation, budget filtering,
and image-based search.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Type
from pydantic import BaseModel, Field

from langchain_core.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_groq import ChatGroq

from ..config import get_config

logger = logging.getLogger(__name__)


# ========================================
# Input Schemas
# ========================================

class InterpretQueryInput(BaseModel):
    """Input schema for query interpretation."""
    
    query: str = Field(description="The user's raw search query")
    user_context: Optional[Dict] = Field(
        default=None,
        description="Optional user context for personalization"
    )


class ApplyBudgetFilterInput(BaseModel):
    """Input schema for budget filtering."""
    
    products: List[Dict] = Field(description="List of products to filter")
    budget_min: Optional[float] = Field(
        default=None,
        description="Minimum budget"
    )
    budget_max: Optional[float] = Field(
        default=None,
        description="Maximum budget"
    )
    tolerance: float = Field(
        default=0.2,
        description="Budget tolerance (0.2 = 20% above max allowed)"
    )
    prefer_affordable: bool = Field(
        default=True,
        description="Sort results by affordability"
    )


class ImageSearchInput(BaseModel):
    """Input schema for image search."""
    
    image_url: Optional[str] = Field(
        default=None,
        description="URL of the image to search"
    )
    image_base64: Optional[str] = Field(
        default=None,
        description="Base64 encoded image"
    )
    limit: int = Field(default=10, description="Maximum results")


# ========================================
# Query Intent Detection
# ========================================

INTENT_PATTERNS = {
    "product_search": [
        r"find|search|looking for|show me|i want|i need",
        r"best|top|popular|recommended"
    ],
    "price_inquiry": [
        r"how much|price|cost|cheap|affordable|budget",
        r"under \$?\d+|less than \$?\d+"
    ],
    "comparison": [
        r"compare|vs|versus|difference|better",
        r"which one|what's the best"
    ],
    "recommendation": [
        r"recommend|suggest|what should|help me choose",
        r"good for|suitable for"
    ],
    "alternative": [
        r"alternative|similar to|like|instead of",
        r"cheaper|different"
    ],
    "category_browse": [
        r"all|list|browse|category|categories",
        r"what (do you have|products)"
    ]
}

CATEGORY_KEYWORDS = {
    "Electronics": [
        "laptop", "laptops", "notebook", "computer", "pc", "desktop",
        "phone", "smartphone", "iphone", "android", "mobile",
        "tablet", "ipad", "headphones", "earbuds", "airpods",
        "speaker", "bluetooth speaker", "soundbar",
        "camera", "dslr", "mirrorless", "webcam",
        "tv", "television", "monitor", "display", "screen",
        "keyboard", "mouse", "gaming", "console", "playstation", "xbox", "nintendo",
        "smartwatch", "wearable", "fitness tracker",
        "charger", "power bank", "cable", "adapter"
    ],
    "Laptops": [  # Sub-category for more specific matching
        "laptop", "laptops", "notebook", "macbook", "chromebook",
        "ultrabook", "gaming laptop", "workstation"
    ],
    "Smartphones": [
        "phone", "smartphone", "iphone", "android", "mobile phone",
        "pixel", "galaxy", "oneplus"
    ],
    "Headphones & Audio": [
        "headphones", "earbuds", "earphones", "airpods", "headset",
        "speaker", "bluetooth speaker", "soundbar", "audio"
    ],
    "Clothing": [
        "shirt", "t-shirt", "tshirt", "pants", "trousers", "dress", 
        "jacket", "coat", "shoes", "sneakers", "boots", "sandals",
        "jeans", "sweater", "hoodie", "shorts", "skirt", "blouse"
    ],
    "Home & Kitchen": [
        "furniture", "sofa", "couch", "table", "chair", "bed", "mattress",
        "kitchen", "cookware", "pot", "pan", "knife", "utensil",
        "bedding", "pillow", "blanket", "sheet",
        "decor", "lamp", "rug", "curtain",
        "appliance", "vacuum", "blender", "coffee maker", "toaster"
    ],
    "Sports & Outdoors": [
        "fitness", "gym", "workout", "exercise", "yoga", "mat",
        "sports", "ball", "racket", "bat",
        "outdoor", "camping", "tent", "hiking", "backpack",
        "bike", "bicycle", "cycling", "running", "shoes"
    ],
    "Books": ["book", "novel", "reading", "textbook", "ebook", "kindle"],
    "Beauty": [
        "makeup", "cosmetics", "lipstick", "mascara", "foundation",
        "skincare", "moisturizer", "serum", "sunscreen",
        "beauty", "perfume", "cologne", "fragrance",
        "hair", "shampoo", "conditioner", "styling"
    ],
    "Toys & Games": [
        "toy", "toys", "game", "games", "puzzle", "lego", "board game",
        "action figure", "doll", "plush"
    ],
    "Automotive": [
        "car", "automotive", "vehicle", "parts", "accessories",
        "tire", "wheel", "seat cover", "dash cam"
    ]
}


def detect_intent(query: str) -> str:
    """Detect the intent of a search query."""
    query_lower = query.lower()
    
    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, query_lower):
                return intent
    
    return "product_search"  # Default intent


def extract_price_range(query: str) -> tuple:
    """Extract price range from query."""
    query_lower = query.lower()
    min_price = None
    max_price = None
    
    # Patterns for price extraction
    under_pattern = r"under\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)"
    over_pattern = r"over\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)"
    between_pattern = r"between\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:and|to|-)\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)"
    budget_pattern = r"budget\s*(?:of|is)?\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)"
    
    # Check for "between X and Y"
    between_match = re.search(between_pattern, query_lower)
    if between_match:
        min_price = float(between_match.group(1).replace(",", ""))
        max_price = float(between_match.group(2).replace(",", ""))
        return min_price, max_price
    
    # Check for "under X"
    under_match = re.search(under_pattern, query_lower)
    if under_match:
        max_price = float(under_match.group(1).replace(",", ""))
    
    # Check for "over X"
    over_match = re.search(over_pattern, query_lower)
    if over_match:
        min_price = float(over_match.group(1).replace(",", ""))
    
    # Check for "budget of X"
    budget_match = re.search(budget_pattern, query_lower)
    if budget_match:
        max_price = float(budget_match.group(1).replace(",", ""))
    
    return min_price, max_price


def detect_category(query: str) -> Optional[str]:
    """Detect product category from query with improved matching."""
    query_lower = query.lower()
    
    # Priority order - more specific categories first
    priority_categories = [
        "Laptops", "Smartphones", "Headphones & Audio",  # Specific first
        "Electronics", "Clothing", "Home & Kitchen", 
        "Sports & Outdoors", "Books", "Beauty", 
        "Toys & Games", "Automotive"
    ]
    
    # Score each category based on keyword matches
    category_scores = {}
    for category in priority_categories:
        if category not in CATEGORY_KEYWORDS:
            continue
        keywords = CATEGORY_KEYWORDS[category]
        score = 0
        for keyword in keywords:
            # Exact word match (with word boundaries)
            if re.search(r'\b' + re.escape(keyword) + r'\b', query_lower):
                # Longer keywords get higher scores
                score += len(keyword)
        if score > 0:
            category_scores[category] = score
    
    if not category_scores:
        return None
    
    # Return the highest scoring category
    best_category = max(category_scores, key=category_scores.get)
    
    # Map sub-categories to main categories for Qdrant filtering
    category_mapping = {
        "Laptops": "Electronics",
        "Smartphones": "Electronics", 
        "Headphones & Audio": "Electronics"
    }
    
    return category_mapping.get(best_category, best_category)


# ========================================
# Interpret Query Tool
# ========================================

class InterpretQueryTool(BaseTool):
    """
    Tool for interpreting user search queries.
    
    Expands vague queries into structured search parameters,
    detects intent, extracts price ranges, and identifies categories.
    """
    
    name: str = "interpret_query"
    description: str = """Interpret and expand a user's search query.
Use this to understand vague queries like "laptop for dev" and extract:
- Intent (search, compare, recommend, etc.)
- Category (Electronics, Clothing, etc.)
- Price range (if mentioned)
- Key features to search for

Returns structured interpretation for better search."""
    
    args_schema: Type[BaseModel] = InterpretQueryInput
    
    def _run(
        self,
        query: str,
        user_context: Optional[Dict] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """Interpret the query."""
        try:
            # Detect intent
            intent = detect_intent(query)
            
            # Extract price range
            min_price, max_price = extract_price_range(query)
            
            # Detect category
            category = detect_category(query)
            
            # Use LLM for advanced interpretation
            config = get_config()
            llm = ChatGroq(
                model=config.llm.model,
                api_key=config.llm.api_key,
                temperature=0.1
            )
            
            interpretation_prompt = f"""Interpret this product search query and extract key information.

Query: "{query}"

Respond in this exact format:
EXPANDED_QUERY: [a clearer, more detailed version of what the user is looking for]
KEY_FEATURES: [comma-separated list of important features/attributes to search for]
USE_CASES: [what the product will be used for]
BRAND_PREFERENCE: [any brand mentioned or "none"]

Be concise and specific."""

            response = llm.invoke(interpretation_prompt)
            response_text = response.content
            
            # Parse LLM response
            expanded_query = query
            key_features = []
            use_cases = ""
            brand_preference = None
            
            for line in response_text.split("\n"):
                if line.startswith("EXPANDED_QUERY:"):
                    expanded_query = line.replace("EXPANDED_QUERY:", "").strip()
                elif line.startswith("KEY_FEATURES:"):
                    features_str = line.replace("KEY_FEATURES:", "").strip()
                    key_features = [f.strip() for f in features_str.split(",")]
                elif line.startswith("USE_CASES:"):
                    use_cases = line.replace("USE_CASES:", "").strip()
                elif line.startswith("BRAND_PREFERENCE:"):
                    brand = line.replace("BRAND_PREFERENCE:", "").strip().lower()
                    if brand != "none":
                        brand_preference = brand
            
            # Consider user context
            if user_context:
                if not max_price and user_context.get('budget_max'):
                    max_price = user_context['budget_max']
                if not category and user_context.get('preferred_categories'):
                    category = user_context['preferred_categories'][0]
            
            return {
                "success": True,
                "original_query": query,
                "interpreted": {
                    "expanded_query": expanded_query,
                    "intent": intent,
                    "category": category,
                    "min_price": min_price,
                    "max_price": max_price,
                    "key_features": key_features,
                    "use_cases": use_cases,
                    "brand_preference": brand_preference
                }
            }
            
        except Exception as e:
            logger.exception(f"Query interpretation error: {e}")
            # Return basic interpretation on error
            return {
                "success": False,
                "error": str(e),
                "original_query": query,
                "interpreted": {
                    "expanded_query": query,
                    "intent": detect_intent(query),
                    "category": detect_category(query),
                    "min_price": None,
                    "max_price": None,
                    "key_features": [],
                    "use_cases": "",
                    "brand_preference": None
                }
            }
    
    async def _arun(self, *args, **kwargs) -> Dict[str, Any]:
        """Async version."""
        return self._run(*args, **kwargs)


# ========================================
# Apply Budget Filter Tool
# ========================================

class ApplyBudgetFilterTool(BaseTool):
    """
    Tool for filtering products by budget constraints.
    
    Filters and optionally sorts products based on
    user's financial constraints.
    """
    
    name: str = "apply_budget_filter"
    description: str = """Filter products by budget constraints.
Use this to ensure search results match user's financial situation.
Can set min/max budget and tolerance (e.g., 20% above max).
Optionally sorts by affordability (price vs budget ratio)."""
    
    args_schema: Type[BaseModel] = ApplyBudgetFilterInput
    
    def _run(
        self,
        products: List[Dict],
        budget_min: Optional[float] = None,
        budget_max: Optional[float] = None,
        tolerance: float = 0.2,
        prefer_affordable: bool = True,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """Apply budget filtering."""
        try:
            filtered_products = []
            effective_max = budget_max * (1 + tolerance) if budget_max else None
            
            for product in products:
                price = product.get('price')
                if price is None:
                    continue
                
                # Check minimum
                if budget_min and price < budget_min:
                    continue
                
                # Check maximum with tolerance
                if effective_max and price > effective_max:
                    continue
                
                # Calculate affordability score
                affordability_score = 1.0
                if budget_max:
                    if price <= budget_max:
                        # Within budget - higher score for lower prices
                        affordability_score = 1.0 - (price / budget_max) * 0.3
                    else:
                        # Over budget but within tolerance - lower score
                        overage = (price - budget_max) / budget_max
                        affordability_score = 0.7 - overage
                
                product_with_score = {
                    **product,
                    "affordability_score": round(affordability_score, 3),
                    "within_budget": price <= budget_max if budget_max else True,
                    "budget_percentage": round(price / budget_max * 100, 1) if budget_max else None
                }
                filtered_products.append(product_with_score)
            
            # Sort by affordability if requested
            if prefer_affordable:
                filtered_products.sort(
                    key=lambda x: (-x.get('affordability_score', 0), x.get('price', 0))
                )
            
            return {
                "success": True,
                "original_count": len(products),
                "filtered_count": len(filtered_products),
                "budget_min": budget_min,
                "budget_max": budget_max,
                "effective_max": effective_max,
                "products": filtered_products
            }
            
        except Exception as e:
            logger.exception(f"Budget filter error: {e}")
            return {
                "success": False,
                "error": str(e),
                "products": products
            }
    
    async def _arun(self, *args, **kwargs) -> Dict[str, Any]:
        """Async version."""
        return self._run(*args, **kwargs)


# ========================================
# Image Search Tool
# ========================================

class ImageSearchTool(BaseTool):
    """
    Tool for image-based product search.
    
    Finds products similar to an uploaded image.
    (Placeholder - requires image embedding model)
    """
    
    name: str = "image_search"
    description: str = """Search for products using an image.
Use this when a user uploads an image to find similar products.
Provide either image_url or image_base64."""
    
    args_schema: Type[BaseModel] = ImageSearchInput
    
    def _run(
        self,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        limit: int = 10,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """Search by image."""
        try:
            if not image_url and not image_base64:
                return {
                    "success": False,
                    "error": "Either image_url or image_base64 must be provided",
                    "results": []
                }
            
            # TODO: Implement actual image search
            # This would require:
            # 1. Image embedding model (CLIP, etc.)
            # 2. Image vectors in Qdrant collection
            # 3. Image preprocessing pipeline
            
            return {
                "success": False,
                "error": "Image search not yet implemented",
                "message": "Image search requires CLIP or similar image embedding model",
                "results": []
            }
            
        except Exception as e:
            logger.exception(f"Image search error: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": []
            }
    
    async def _arun(self, *args, **kwargs) -> Dict[str, Any]:
        """Async version."""
        return self._run(*args, **kwargs)
