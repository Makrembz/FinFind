"""
Alternative Tools for FinFind AlternativeAgent.

Provides tools for finding substitute products when
budget or other constraints aren't met.
"""

import logging
from typing import Dict, Any, List, Optional, Type
from pydantic import BaseModel, Field

from langchain_core.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_groq import ChatGroq
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range

from .qdrant_tools import get_qdrant_client, embed_text
from ..config import get_config

logger = logging.getLogger(__name__)


# ========================================
# Input Schemas
# ========================================

class FindSimilarProductsInput(BaseModel):
    """Input schema for finding similar products."""
    
    product_id: str = Field(description="Source product ID")
    max_price: Optional[float] = Field(
        default=None,
        description="Maximum price for alternatives"
    )
    same_category: bool = Field(
        default=True,
        description="Limit to same category"
    )
    limit: int = Field(default=5, description="Number of alternatives")
    exclude_ids: List[str] = Field(
        default_factory=list,
        description="Product IDs to exclude"
    )


class AdjustPriceRangeInput(BaseModel):
    """Input schema for price range adjustment."""
    
    original_price: float = Field(description="Original product price")
    user_budget: float = Field(description="User's budget")
    adjustment_step: float = Field(
        default=0.1,
        description="Step size for price range (e.g., 0.1 = 10%)"
    )
    max_steps: int = Field(
        default=5,
        description="Maximum adjustment steps"
    )


class SuggestAlternativesInput(BaseModel):
    """Input schema for alternative suggestions."""
    
    original_product: Dict = Field(description="Original product data")
    user_profile: Optional[Dict] = Field(
        default=None,
        description="User profile for personalization"
    )
    reason: str = Field(
        default="over_budget",
        description="Reason for seeking alternatives: over_budget, out_of_stock, low_rating, etc."
    )
    num_suggestions: int = Field(
        default=3,
        description="Number of alternatives to suggest"
    )


# ========================================
# Find Similar Products Tool
# ========================================

class FindSimilarProductsTool(BaseTool):
    """
    Tool for finding similar products with constraints.
    
    Finds products similar to a given product but within
    specified price or other constraints.
    """
    
    name: str = "find_similar_products"
    description: str = """Find products similar to a given product, optionally with price constraints.
Use this when a product is over budget or unavailable.
Searches for alternatives in the same or similar categories.
Can exclude specific products from results."""
    
    args_schema: Type[BaseModel] = FindSimilarProductsInput
    
    def _run(
        self,
        product_id: str,
        max_price: Optional[float] = None,
        same_category: bool = True,
        limit: int = 5,
        exclude_ids: List[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """Find similar products."""
        try:
            client = get_qdrant_client()
            config = get_config().qdrant
            exclude_ids = exclude_ids or []
            
            # Get source product
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
                    "error": f"Source product {product_id} not found",
                    "alternatives": []
                }
            
            source_point = source_results[0][0]
            source_product = source_point.payload
            source_vector = source_point.vector
            original_price = source_product.get('price', 0)
            
            # Build filter
            filter_conditions = []
            
            if same_category:
                filter_conditions.append(
                    FieldCondition(
                        key="category",
                        match=MatchValue(value=source_product.get('category'))
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
            
            # Search for similar products using query_points (new API)
            search_result = client.query_points(
                collection_name=config.products_collection,
                query=source_vector,
                query_filter=search_filter,
                limit=limit + len(exclude_ids) + 1  # Extra to account for exclusions
            )
            results = search_result.points
            
            # Filter and format results
            alternatives = []
            exclude_set = set(exclude_ids + [product_id])
            
            for result in results:
                result_id = result.payload.get('original_id', str(result.id))
                if result_id in exclude_set:
                    continue
                
                price = result.payload.get('price', 0)
                savings = original_price - price if original_price > 0 else 0
                
                alternatives.append({
                    "id": str(result.id),
                    "product_id": result_id,
                    "similarity_score": round(result.score, 4),
                    "title": result.payload.get('title'),
                    "category": result.payload.get('category'),
                    "price": price,
                    "rating": result.payload.get('rating'),
                    "savings": round(savings, 2) if savings > 0 else 0,
                    "savings_percent": round(savings / original_price * 100, 1) if original_price > 0 and savings > 0 else 0
                })
                
                if len(alternatives) >= limit:
                    break
            
            return {
                "success": True,
                "source_product": {
                    "id": product_id,
                    "title": source_product.get('title'),
                    "price": original_price,
                    "category": source_product.get('category')
                },
                "constraints": {
                    "max_price": max_price,
                    "same_category": same_category
                },
                "count": len(alternatives),
                "alternatives": alternatives
            }
            
        except Exception as e:
            logger.exception(f"Find similar products error: {e}")
            return {
                "success": False,
                "error": str(e),
                "alternatives": []
            }
    
    async def _arun(self, *args, **kwargs) -> Dict[str, Any]:
        """Async version."""
        return self._run(*args, **kwargs)


# ========================================
# Adjust Price Range Tool
# ========================================

class AdjustPriceRangeTool(BaseTool):
    """
    Tool for calculating adjusted price ranges.
    
    Helps find price ranges that might contain
    suitable alternatives when budget is exceeded.
    """
    
    name: str = "adjust_price_range"
    description: str = """Calculate adjusted price ranges for finding alternatives.
Use when a product exceeds budget to determine:
- How much of a downgrade is needed
- Price ranges to search in
- Savings needed to meet budget"""
    
    args_schema: Type[BaseModel] = AdjustPriceRangeInput
    
    def _run(
        self,
        original_price: float,
        user_budget: float,
        adjustment_step: float = 0.1,
        max_steps: int = 5,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """Calculate adjusted price ranges."""
        try:
            if original_price <= user_budget:
                return {
                    "success": True,
                    "message": "Original price is within budget",
                    "original_price": original_price,
                    "user_budget": user_budget,
                    "adjustment_needed": False,
                    "price_ranges": [{
                        "min": 0,
                        "max": user_budget,
                        "label": "within_budget"
                    }]
                }
            
            # Calculate overage
            overage = original_price - user_budget
            overage_percent = (overage / user_budget) * 100
            
            # Generate price ranges
            price_ranges = []
            
            for step in range(1, max_steps + 1):
                # Calculate range
                discount = step * adjustment_step
                range_max = original_price * (1 - discount)
                range_min = original_price * (1 - discount - adjustment_step)
                
                if range_max < 0:
                    break
                
                # Determine if this range is within budget
                within_budget = range_max <= user_budget
                
                price_ranges.append({
                    "step": step,
                    "discount_percent": round(discount * 100, 1),
                    "min": round(max(0, range_min), 2),
                    "max": round(range_max, 2),
                    "within_budget": within_budget,
                    "label": f"{int(discount * 100)}%_less"
                })
                
                # Stop if we've reached budget range
                if within_budget and range_min <= user_budget:
                    break
            
            # Find the minimum discount needed
            min_discount_needed = None
            for pr in price_ranges:
                if pr['within_budget']:
                    min_discount_needed = pr['discount_percent']
                    break
            
            return {
                "success": True,
                "original_price": original_price,
                "user_budget": user_budget,
                "adjustment_needed": True,
                "overage": round(overage, 2),
                "overage_percent": round(overage_percent, 1),
                "min_discount_needed": min_discount_needed,
                "price_ranges": price_ranges,
                "recommendation": f"Look for products {min_discount_needed}% cheaper to stay within budget" if min_discount_needed else "Consider significantly cheaper alternatives"
            }
            
        except Exception as e:
            logger.exception(f"Price range adjustment error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _arun(self, *args, **kwargs) -> Dict[str, Any]:
        """Async version."""
        return self._run(*args, **kwargs)


# ========================================
# Suggest Alternatives Tool
# ========================================

class SuggestAlternativesTool(BaseTool):
    """
    Tool for generating intelligent alternative suggestions.
    
    Uses LLM to explain why alternatives are suggested
    and how they compare to the original.
    """
    
    name: str = "suggest_alternatives"
    description: str = """Generate intelligent alternative product suggestions.
Use when a product doesn't meet constraints to:
- Find suitable alternatives
- Explain trade-offs
- Compare alternatives to original

Reasons for alternatives: over_budget, out_of_stock, low_rating, not_available"""
    
    args_schema: Type[BaseModel] = SuggestAlternativesInput
    
    def _run(
        self,
        original_product: Dict,
        user_profile: Optional[Dict] = None,
        reason: str = "over_budget",
        num_suggestions: int = 3,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """Generate alternative suggestions."""
        try:
            client = get_qdrant_client()
            config = get_config()
            
            original_price = original_product.get('price', 0)
            original_category = original_product.get('category', '')
            
            # Determine search constraints based on reason
            max_price = None
            filter_conditions = []
            
            if reason == "over_budget" and user_profile:
                budget = user_profile.get('financial_context', {}).get('budget_max')
                if budget:
                    max_price = budget
                    filter_conditions.append(
                        FieldCondition(key="price", range=Range(lte=budget))
                    )
            
            if reason == "low_rating":
                filter_conditions.append(
                    FieldCondition(key="rating", range=Range(gte=4.0))
                )
            
            # Same category by default
            if original_category:
                filter_conditions.append(
                    FieldCondition(
                        key="category",
                        match=MatchValue(value=original_category)
                    )
                )
            
            # Build search text from original product
            search_text = f"{original_product.get('title', '')} {original_product.get('description', '')}"
            search_vector = embed_text(search_text[:500])
            
            search_filter = Filter(must=filter_conditions) if filter_conditions else None
            
            # Search for alternatives using query_points (new API)
            search_result = client.query_points(
                collection_name=config.qdrant.products_collection,
                query=search_vector,
                query_filter=search_filter,
                limit=num_suggestions + 1  # +1 to exclude original if present
            )
            results = search_result.points
            
            # Filter and format alternatives
            original_id = original_product.get('id') or original_product.get('original_id')
            alternatives = []
            
            for result in results:
                result_id = result.payload.get('original_id', str(result.id))
                if result_id == original_id:
                    continue
                
                alt_price = result.payload.get('price', 0)
                price_diff = original_price - alt_price
                
                # Determine comparison
                comparison = []
                if price_diff > 0:
                    comparison.append(f"${price_diff:.2f} cheaper")
                elif price_diff < 0:
                    comparison.append(f"${abs(price_diff):.2f} more expensive")
                
                alt_rating = result.payload.get('rating', 0)
                orig_rating = original_product.get('rating', 0)
                if alt_rating > orig_rating:
                    comparison.append(f"Higher rated ({alt_rating} vs {orig_rating})")
                elif alt_rating < orig_rating:
                    comparison.append(f"Lower rated ({alt_rating} vs {orig_rating})")
                
                alternatives.append({
                    "product_id": result_id,
                    "title": result.payload.get('title'),
                    "category": result.payload.get('category'),
                    "price": alt_price,
                    "rating": alt_rating,
                    "similarity_score": round(result.score, 4),
                    "comparison_to_original": comparison,
                    "savings": round(price_diff, 2) if price_diff > 0 else 0
                })
                
                if len(alternatives) >= num_suggestions:
                    break
            
            # Generate explanation using LLM
            if alternatives:
                llm = ChatGroq(
                    model=config.llm.model,
                    api_key=config.llm.api_key,
                    temperature=0.3
                )
                
                alt_summaries = "\n".join([
                    f"- {a['title']}: ${a['price']}, {a['rating']}/5 rating"
                    for a in alternatives[:3]
                ])
                
                reason_text = {
                    "over_budget": "exceeds your budget",
                    "out_of_stock": "is currently out of stock",
                    "low_rating": "has lower ratings than you might prefer",
                    "not_available": "is not available in your region"
                }.get(reason, "may not be the best fit")
                
                prompt = f"""The user was looking at "{original_product.get('title')}" (${original_price}) but it {reason_text}.

Here are alternatives found:
{alt_summaries}

Write a brief, helpful 2-3 sentence explanation introducing these alternatives and their key trade-offs."""

                response = llm.invoke(prompt)
                explanation = response.content.strip()
            else:
                explanation = f"Unable to find alternatives that match your constraints. Consider adjusting your budget or exploring different categories."
            
            return {
                "success": True,
                "original_product": {
                    "id": original_id,
                    "title": original_product.get('title'),
                    "price": original_price
                },
                "reason": reason,
                "count": len(alternatives),
                "alternatives": alternatives,
                "explanation": explanation
            }
            
        except Exception as e:
            logger.exception(f"Suggest alternatives error: {e}")
            return {
                "success": False,
                "error": str(e),
                "alternatives": []
            }
    
    async def _arun(self, *args, **kwargs) -> Dict[str, Any]:
        """Async version."""
        return self._run(*args, **kwargs)
