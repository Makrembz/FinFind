"""
MCP Alternative Tools for FinFind AlternativeAgent.

Tools for finding product alternatives and substitutes.
"""

import logging
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

class SimilarInPriceRangeInput(BaseModel):
    """Input for finding similar products in price range."""
    product: Dict[str, Any] = Field(..., description="Reference product")
    min_price: Optional[float] = Field(default=None, description="Minimum price")
    max_price: Optional[float] = Field(default=None, description="Maximum price")
    limit: int = Field(default=5, ge=1, le=20, description="Max results")
    same_category: bool = Field(default=True, description="Require same category")


class CategoryAlternativesInput(BaseModel):
    """Input for finding category alternatives."""
    original_product: Dict[str, Any] = Field(..., description="Original product")
    user_budget: float = Field(..., description="User's budget")
    preferred_categories: Optional[List[str]] = Field(
        default=None,
        description="Categories to consider"
    )
    limit: int = Field(default=5, description="Max alternatives per category")


class DowngradeOptionsInput(BaseModel):
    """Input for finding downgrade options."""
    product: Dict[str, Any] = Field(..., description="Product to find downgrades for")
    max_price: float = Field(..., description="Maximum price for alternatives")
    preserve_features: Optional[List[str]] = Field(
        default=None,
        description="Features that must be preserved"
    )
    limit: int = Field(default=5, description="Max downgrade options")


class UpgradePathInput(BaseModel):
    """Input for showing upgrade paths."""
    product: Dict[str, Any] = Field(..., description="Current product")
    budget_increase: float = Field(..., description="How much more user could spend")
    show_benefits: bool = Field(default=True, description="Show what upgrades provide")
    limit: int = Field(default=5, description="Max upgrade options")


# ========================================
# Find Similar In Price Range Tool
# ========================================

class FindSimilarInPriceRangeTool(MCPTool):
    """
    MCP tool for finding similar products in a different price range.
    
    Features:
    - Semantic similarity to reference product
    - Price range filtering
    - Category matching
    """
    
    name: str = "find_similar_in_price_range"
    description: str = """
    Finds products similar to a reference product but in a different price tier.
    Useful for finding affordable alternatives or premium upgrades.
    Maintains semantic similarity while adjusting price.
    """
    args_schema: type = SimilarInPriceRangeInput
    
    mcp_metadata: MCPToolMetadata = MCPToolMetadata(
        name="find_similar_in_price_range",
        description="Find similar products in price range",
        category="alternative",
        tags=["alternative", "price", "similarity"],
        requires_qdrant=True,
        requires_embedding=True,
        cacheable=True,
        cache_ttl_seconds=300,
        avg_latency_ms=150
    )
    
    def _execute(
        self,
        product: Dict[str, Any],
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 5,
        same_category: bool = True
    ) -> MCPToolOutput:
        """Find similar products in price range."""
        
        qdrant = get_qdrant_service()
        embedding_service = get_embedding_service()
        config = get_config()
        
        # Build product embedding
        product_text = self._build_product_text(product)
        product_embedding = embedding_service.embed(product_text)
        
        original_price = product.get("price", 0)
        
        # Set default price range if not specified
        if min_price is None and max_price is None:
            # Default to 20% cheaper to 20% more expensive
            min_price = original_price * 0.5
            max_price = original_price * 0.8
        
        # Build filters
        filters = {}
        
        if min_price is not None or max_price is not None:
            price_range = {}
            if min_price is not None:
                price_range["gte"] = min_price
            if max_price is not None:
                price_range["lte"] = max_price
            filters["price"] = {"range": price_range}
        
        if same_category and product.get("category"):
            filters["category"] = product["category"]
        
        try:
            # Search for similar products
            results = qdrant.mmr_search(
                collection=config.qdrant.products_collection,
                query_vector=product_embedding,
                limit=limit + 5,  # Get extra to filter original
                diversity=0.3,
                filters=filters if filters else None
            )
            
            # Filter out the original product
            original_id = product.get("id")
            alternatives = []
            
            for result in results:
                if result["id"] != original_id:
                    alt_price = result.get("payload", {}).get("price", 0)
                    savings = original_price - alt_price
                    savings_pct = (savings / original_price * 100) if original_price > 0 else 0
                    
                    alternatives.append({
                        "id": result["id"],
                        "similarity_score": round(result["score"], 3),
                        "price": alt_price,
                        "savings": round(savings, 2),
                        "savings_percentage": round(savings_pct, 1),
                        **result.get("payload", {})
                    })
                
                if len(alternatives) >= limit:
                    break
            
            return MCPToolOutput.success_response(
                data={
                    "original_product": {
                        "id": original_id,
                        "name": product.get("name"),
                        "price": original_price
                    },
                    "alternatives": alternatives,
                    "price_range": {
                        "min": min_price,
                        "max": max_price
                    },
                    "found_count": len(alternatives)
                }
            )
            
        except Exception as e:
            logger.exception(f"Failed to find alternatives: {e}")
            raise MCPError(
                code=MCPErrorCode.VECTOR_SEARCH_FAILED,
                message=f"Failed to find alternatives: {str(e)}"
            )
    
    def _build_product_text(self, product: Dict) -> str:
        """Build searchable text from product."""
        parts = []
        for field in ["name", "description", "category", "brand"]:
            if product.get(field):
                parts.append(str(product[field]))
        if product.get("tags"):
            parts.extend(product["tags"])
        return " ".join(parts)


# ========================================
# Find Category Alternatives Tool
# ========================================

class FindCategoryAlternativesTool(MCPTool):
    """
    MCP tool for finding alternatives in different categories.
    
    Suggests products from related categories that:
    - Serve similar purpose
    - Fit user's budget
    - Match user preferences
    """
    
    name: str = "find_category_alternatives"
    description: str = """
    Finds alternative products in different categories that fit the budget.
    Useful when the desired product is out of budget.
    Suggests similar-purpose items from related categories.
    """
    args_schema: type = CategoryAlternativesInput
    
    mcp_metadata: MCPToolMetadata = MCPToolMetadata(
        name="find_category_alternatives",
        description="Find alternatives in different categories",
        category="alternative",
        tags=["alternative", "category", "budget"],
        requires_qdrant=True,
        requires_embedding=True,
        cacheable=True,
        cache_ttl_seconds=300,
        avg_latency_ms=200
    )
    
    # Category relationships
    RELATED_CATEGORIES = {
        "laptops": ["tablets", "chromebooks", "desktops"],
        "smartphones": ["tablets", "feature_phones"],
        "headphones": ["earbuds", "speakers"],
        "cameras": ["smartphones", "action_cameras"],
        "tablets": ["laptops", "e-readers"],
        "smartwatches": ["fitness_trackers", "traditional_watches"],
        "gaming_consoles": ["gaming_laptops", "streaming_devices"],
        "tvs": ["monitors", "projectors"],
    }
    
    def _execute(
        self,
        original_product: Dict[str, Any],
        user_budget: float,
        preferred_categories: Optional[List[str]] = None,
        limit: int = 5
    ) -> MCPToolOutput:
        """Find category alternatives."""
        
        qdrant = get_qdrant_service()
        embedding_service = get_embedding_service()
        config = get_config()
        
        original_category = original_product.get("category", "").lower()
        original_price = original_product.get("price", 0)
        
        # Determine categories to search
        if preferred_categories:
            categories_to_search = preferred_categories
        else:
            categories_to_search = self.RELATED_CATEGORIES.get(
                original_category,
                []
            )
        
        if not categories_to_search:
            return MCPToolOutput.success_response(
                data={
                    "alternatives_by_category": {},
                    "message": "No related categories found",
                    "suggestion": "Try specifying preferred categories"
                }
            )
        
        # Build semantic query from original product
        product_text = f"{original_product.get('name', '')} {original_product.get('description', '')}"
        query_embedding = embedding_service.embed(product_text)
        
        alternatives_by_category = {}
        
        for category in categories_to_search:
            try:
                # Search in category with budget filter
                results = qdrant.semantic_search(
                    collection=config.qdrant.products_collection,
                    query_vector=query_embedding,
                    limit=limit,
                    filters={
                        "category": category,
                        "price": {"range": {"lte": user_budget}}
                    }
                )
                
                if results:
                    alternatives_by_category[category] = [
                        {
                            "id": r["id"],
                            "similarity": round(r["score"], 3),
                            "price": r.get("payload", {}).get("price", 0),
                            "budget_remaining": round(
                                user_budget - r.get("payload", {}).get("price", 0), 2
                            ),
                            **r.get("payload", {})
                        }
                        for r in results
                    ]
            except Exception as e:
                logger.warning(f"Failed to search category {category}: {e}")
                continue
        
        # Calculate savings summary
        all_alternatives = []
        for cat_alts in alternatives_by_category.values():
            all_alternatives.extend(cat_alts)
        
        avg_savings = 0
        if all_alternatives:
            avg_savings = sum(
                original_price - alt.get("price", 0)
                for alt in all_alternatives
            ) / len(all_alternatives)
        
        return MCPToolOutput.success_response(
            data={
                "original_product": {
                    "name": original_product.get("name"),
                    "category": original_category,
                    "price": original_price
                },
                "user_budget": user_budget,
                "alternatives_by_category": alternatives_by_category,
                "summary": {
                    "categories_searched": len(categories_to_search),
                    "total_alternatives": len(all_alternatives),
                    "average_savings": round(avg_savings, 2)
                }
            }
        )


# ========================================
# Get Downgrade Options Tool
# ========================================

class GetDowngradeOptionsTool(MCPTool):
    """
    MCP tool for finding lower-spec versions of products.
    
    Finds products that:
    - Have similar core features
    - Are priced lower
    - Trade off advanced features for affordability
    """
    
    name: str = "get_downgrade_options"
    description: str = """
    Finds lower-spec versions of a product that fit the budget.
    Identifies what features are traded off for the lower price.
    Helps users understand value-for-money trade-offs.
    """
    args_schema: type = DowngradeOptionsInput
    
    mcp_metadata: MCPToolMetadata = MCPToolMetadata(
        name="get_downgrade_options",
        description="Find budget-friendly downgrade alternatives",
        category="alternative",
        tags=["alternative", "downgrade", "budget"],
        requires_qdrant=True,
        requires_embedding=True,
        cacheable=True,
        cache_ttl_seconds=300,
        avg_latency_ms=180
    )
    
    def _execute(
        self,
        product: Dict[str, Any],
        max_price: float,
        preserve_features: Optional[List[str]] = None,
        limit: int = 5
    ) -> MCPToolOutput:
        """Find downgrade options."""
        
        qdrant = get_qdrant_service()
        embedding_service = get_embedding_service()
        config = get_config()
        
        original_price = product.get("price", 0)
        category = product.get("category")
        brand = product.get("brand")
        
        if max_price >= original_price:
            return MCPToolOutput.success_response(
                data={
                    "message": "Max price is higher than original - consider find_similar_in_price_range instead",
                    "downgrades": [],
                    "original_price": original_price,
                    "max_price": max_price
                }
            )
        
        # Build query emphasizing core features
        query_parts = [product.get("name", "")]
        if category:
            query_parts.append(f"category: {category}")
        if preserve_features:
            query_parts.extend(preserve_features)
        
        query_embedding = embedding_service.embed(" ".join(query_parts))
        
        # Search with price filter
        filters = {
            "price": {"range": {"lte": max_price, "gt": 0}}
        }
        if category:
            filters["category"] = category
        
        try:
            results = qdrant.semantic_search(
                collection=config.qdrant.products_collection,
                query_vector=query_embedding,
                limit=limit * 2,
                filters=filters
            )
            
            downgrades = []
            original_features = set(product.get("features", []))
            
            for result in results:
                if result["id"] == product.get("id"):
                    continue
                
                payload = result.get("payload", {})
                alt_price = payload.get("price", 0)
                alt_features = set(payload.get("features", []))
                
                # Calculate what's preserved and lost
                preserved = original_features.intersection(alt_features)
                lost = original_features - alt_features
                gained = alt_features - original_features
                
                # Check if must-have features are preserved
                if preserve_features:
                    preserve_set = set(preserve_features)
                    if not preserve_set.issubset(alt_features):
                        continue
                
                savings = original_price - alt_price
                savings_pct = (savings / original_price * 100) if original_price > 0 else 0
                
                downgrades.append({
                    "id": result["id"],
                    "similarity_score": round(result["score"], 3),
                    "price": alt_price,
                    "savings": round(savings, 2),
                    "savings_percentage": round(savings_pct, 1),
                    "trade_offs": {
                        "features_preserved": list(preserved)[:5],
                        "features_lost": list(lost)[:5],
                        "features_gained": list(gained)[:3]
                    },
                    **payload
                })
                
                if len(downgrades) >= limit:
                    break
            
            # Sort by similarity (best match first)
            downgrades.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            return MCPToolOutput.success_response(
                data={
                    "original_product": {
                        "id": product.get("id"),
                        "name": product.get("name"),
                        "price": original_price,
                        "features": list(original_features)[:10]
                    },
                    "max_price": max_price,
                    "downgrades": downgrades,
                    "summary": {
                        "options_found": len(downgrades),
                        "best_savings": max(
                            (d["savings"] for d in downgrades),
                            default=0
                        )
                    }
                }
            )
            
        except Exception as e:
            logger.exception(f"Failed to find downgrades: {e}")
            raise MCPError(
                code=MCPErrorCode.VECTOR_SEARCH_FAILED,
                message=f"Failed to find downgrades: {str(e)}"
            )


# ========================================
# Get Upgrade Path Tool
# ========================================

class GetUpgradePathTool(MCPTool):
    """
    MCP tool for showing upgrade options with additional budget.
    
    Shows what users could get if they:
    - Increase their budget slightly
    - Save a bit more
    - Consider financing
    """
    
    name: str = "get_upgrade_path"
    description: str = """
    Shows what better products become available with budget increase.
    Helps users understand the value of additional spending.
    Compares features and benefits of upgrades.
    """
    args_schema: type = UpgradePathInput
    
    mcp_metadata: MCPToolMetadata = MCPToolMetadata(
        name="get_upgrade_path",
        description="Show upgrade options with more budget",
        category="alternative",
        tags=["alternative", "upgrade", "budget"],
        requires_qdrant=True,
        requires_embedding=True,
        cacheable=True,
        cache_ttl_seconds=300,
        avg_latency_ms=180
    )
    
    def _execute(
        self,
        product: Dict[str, Any],
        budget_increase: float,
        show_benefits: bool = True,
        limit: int = 5
    ) -> MCPToolOutput:
        """Find upgrade options."""
        
        qdrant = get_qdrant_service()
        embedding_service = get_embedding_service()
        config = get_config()
        
        current_price = product.get("price", 0)
        new_budget = current_price + budget_increase
        category = product.get("category")
        
        # Build query for better versions
        query_parts = [
            product.get("name", ""),
            "premium", "better", "upgraded", "pro"
        ]
        if category:
            query_parts.append(category)
        
        query_embedding = embedding_service.embed(" ".join(query_parts))
        
        # Search in higher price range
        filters = {
            "price": {"range": {"gt": current_price, "lte": new_budget}}
        }
        if category:
            filters["category"] = category
        
        try:
            results = qdrant.semantic_search(
                collection=config.qdrant.products_collection,
                query_vector=query_embedding,
                limit=limit * 2,
                filters=filters
            )
            
            upgrades = []
            current_features = set(product.get("features", []))
            current_rating = product.get("rating", 0)
            
            for result in results:
                if result["id"] == product.get("id"):
                    continue
                
                payload = result.get("payload", {})
                upgrade_price = payload.get("price", 0)
                upgrade_features = set(payload.get("features", []))
                upgrade_rating = payload.get("rating", 0)
                
                # Calculate benefits
                additional_cost = upgrade_price - current_price
                new_features = upgrade_features - current_features
                rating_improvement = upgrade_rating - current_rating
                
                benefits = []
                if new_features:
                    benefits.append(f"+{len(new_features)} new features")
                if rating_improvement > 0:
                    benefits.append(f"+{rating_improvement:.1f} rating")
                if payload.get("brand") != product.get("brand"):
                    benefits.append(f"Premium brand: {payload.get('brand')}")
                
                # Value score: features gained per dollar spent
                value_score = len(new_features) / max(additional_cost, 1)
                
                upgrade_info = {
                    "id": result["id"],
                    "similarity_score": round(result["score"], 3),
                    "price": upgrade_price,
                    "additional_cost": round(additional_cost, 2),
                    "cost_increase_percentage": round(
                        (additional_cost / current_price * 100) if current_price > 0 else 0, 1
                    ),
                    **payload
                }
                
                if show_benefits:
                    upgrade_info["benefits"] = {
                        "new_features": list(new_features)[:5],
                        "rating_improvement": round(rating_improvement, 1),
                        "benefit_summary": benefits,
                        "value_score": round(value_score, 3)
                    }
                
                upgrades.append(upgrade_info)
                
                if len(upgrades) >= limit:
                    break
            
            # Sort by value score (best value upgrade first)
            if show_benefits:
                upgrades.sort(
                    key=lambda x: x.get("benefits", {}).get("value_score", 0),
                    reverse=True
                )
            
            # Create upgrade tiers
            tiers = {
                "budget_friendly": [u for u in upgrades if u["additional_cost"] <= budget_increase * 0.3],
                "mid_range": [u for u in upgrades if budget_increase * 0.3 < u["additional_cost"] <= budget_increase * 0.7],
                "premium": [u for u in upgrades if u["additional_cost"] > budget_increase * 0.7]
            }
            
            return MCPToolOutput.success_response(
                data={
                    "current_product": {
                        "id": product.get("id"),
                        "name": product.get("name"),
                        "price": current_price,
                        "rating": current_rating
                    },
                    "budget_increase": budget_increase,
                    "new_budget": new_budget,
                    "upgrades": upgrades,
                    "upgrade_tiers": tiers,
                    "summary": {
                        "options_found": len(upgrades),
                        "best_value": upgrades[0]["id"] if upgrades else None,
                        "average_cost_increase": sum(
                            u["additional_cost"] for u in upgrades
                        ) / len(upgrades) if upgrades else 0
                    }
                }
            )
            
        except Exception as e:
            logger.exception(f"Failed to find upgrades: {e}")
            raise MCPError(
                code=MCPErrorCode.VECTOR_SEARCH_FAILED,
                message=f"Failed to find upgrades: {str(e)}"
            )
