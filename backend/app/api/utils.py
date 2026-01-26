"""
Utility functions for the API.

Common helpers for:
- Response formatting
- Error handling
- Validation
- Pagination
"""

import logging
import math
from typing import Any, Dict, List, Optional, TypeVar
from datetime import datetime

from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


# ==============================================================================
# Pagination Helpers
# ==============================================================================

def paginate(
    items: List[Any],
    page: int,
    page_size: int
) -> Dict[str, Any]:
    """
    Paginate a list of items.
    
    Returns:
        Dict with items, total, page, page_size, total_pages, has_next, has_prev
    """
    total = len(items)
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    
    start = (page - 1) * page_size
    end = start + page_size
    
    return {
        "items": items[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }


def calculate_offset(page: int, page_size: int) -> int:
    """Calculate offset for pagination."""
    return (page - 1) * page_size


# ==============================================================================
# Response Helpers
# ==============================================================================

def success_response(
    data: Optional[Dict[str, Any]] = None,
    message: str = "Success",
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create a standardized success response."""
    response = {
        "success": True,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }
    if data:
        response.update(data)
    if request_id:
        response["request_id"] = request_id
    return response


def error_response(
    error: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create a standardized error response."""
    return {
        "success": False,
        "error": error,
        "message": message,
        "details": details,
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat()
    }


# ==============================================================================
# Validation Helpers
# ==============================================================================

def validate_price_range(
    min_price: Optional[float],
    max_price: Optional[float]
) -> bool:
    """Validate price range values."""
    if min_price is not None and min_price < 0:
        return False
    if max_price is not None and max_price < 0:
        return False
    if min_price is not None and max_price is not None:
        if min_price > max_price:
            return False
    return True


def validate_rating(rating: Optional[float]) -> bool:
    """Validate rating value."""
    if rating is None:
        return True
    return 0 <= rating <= 5


# ==============================================================================
# Filter Helpers
# ==============================================================================

def build_qdrant_filters(
    categories: Optional[List[str]] = None,
    brands: Optional[List[str]] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    in_stock: Optional[bool] = None,
    tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Build Qdrant filter conditions from common parameters.
    
    Returns:
        Dict with filter conditions for Qdrant search
    """
    filters = {}
    
    if categories:
        filters["category"] = {"any": categories}
    
    if brands:
        filters["brand"] = {"any": brands}
    
    if min_price is not None or max_price is not None:
        price_filter = {}
        if min_price is not None:
            price_filter["gte"] = min_price
        if max_price is not None:
            price_filter["lte"] = max_price
        filters["price"] = price_filter
    
    if min_rating is not None:
        filters["rating_avg"] = {"gte": min_rating}
    
    if in_stock is not None:
        if in_stock:
            filters["stock_status"] = {"match": "in_stock"}
        else:
            filters["stock_status"] = {"match": "out_of_stock"}
    
    if tags:
        filters["tags"] = {"any": tags}
    
    return filters if filters else None


# ==============================================================================
# Format Helpers
# ==============================================================================

def format_product_result(
    product_data: Dict[str, Any],
    score: float = 0.0
) -> Dict[str, Any]:
    """
    Format raw product data into a standardized result.
    
    Args:
        product_data: Raw product data from Qdrant
        score: Relevance score
    
    Returns:
        Formatted product dict
    """
    payload = product_data.get("payload", product_data)
    
    return {
        "id": product_data.get("id", payload.get("id", "")),
        "name": payload.get("title", payload.get("name", "Unknown")),
        "description": payload.get("description"),
        "price": payload.get("price", 0.0),
        "original_price": payload.get("original_price"),
        "category": payload.get("category", "Unknown"),
        "subcategory": payload.get("subcategory"),
        "brand": payload.get("brand"),
        "rating": payload.get("rating_avg"),
        "review_count": payload.get("review_count"),
        "image_url": payload.get("image_url"),
        "in_stock": payload.get("stock_status", "in_stock") == "in_stock",
        "relevance_score": score,
        "tags": payload.get("tags", [])
    }


def format_user_profile(
    user_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Format raw user data into a standardized profile."""
    payload = user_data.get("payload", user_data)
    
    return {
        "user_id": user_data.get("id", payload.get("user_id", "")),
        "name": payload.get("name"),
        "email": payload.get("email"),
        "financial_profile": {
            "monthly_income": payload.get("monthly_income"),
            "monthly_budget": payload.get("monthly_budget"),
            "credit_score_range": payload.get("credit_score_range"),
            "preferred_payment_methods": payload.get("preferred_payment_methods", []),
            "risk_tolerance": payload.get("risk_tolerance"),
            "savings_goal": payload.get("savings_goal")
        },
        "preferences": {
            "favorite_categories": payload.get("preferred_categories", []),
            "favorite_brands": payload.get("preferred_brands", "").split(", ") 
                if isinstance(payload.get("preferred_brands"), str) 
                else payload.get("preferred_brands", []),
            "price_sensitivity": payload.get("price_sensitivity"),
            "quality_preference": payload.get("quality_preference"),
            "eco_friendly": payload.get("eco_friendly", False),
            "local_preference": payload.get("local_preference", False)
        }
    }


# ==============================================================================
# Timing Helpers
# ==============================================================================

class Timer:
    """Simple timer context manager."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        import time
        self.start_time = time.time()
        return self
    
    def __exit__(self, *args):
        import time
        self.end_time = time.time()
    
    @property
    def elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0.0


# ==============================================================================
# Logging Helpers
# ==============================================================================

def log_request(
    endpoint: str,
    method: str,
    request_id: str,
    user_id: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None
):
    """Log an incoming request."""
    logger.info(
        f"Request: {method} {endpoint}",
        extra={
            "request_id": request_id,
            "user_id": user_id,
            "params": params
        }
    )


def log_response(
    endpoint: str,
    request_id: str,
    status_code: int,
    duration_ms: float
):
    """Log an outgoing response."""
    logger.info(
        f"Response: {endpoint} - {status_code} in {duration_ms:.2f}ms",
        extra={
            "request_id": request_id,
            "status_code": status_code,
            "duration_ms": duration_ms
        }
    )
