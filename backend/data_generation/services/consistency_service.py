"""
Consistency service for ensuring data integrity across collections.

Validates cross-references between products, users, reviews, and interactions
to ensure all generated data is properly connected.
"""

from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConsistencyReport:
    """Report of consistency validation results."""
    
    is_valid: bool = True
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    def add_error(self, message: str) -> None:
        """Add an error to the report."""
        self.errors.append(message)
        self.is_valid = False
        self.failed_checks += 1
    
    def add_warning(self, message: str) -> None:
        """Add a warning to the report."""
        self.warnings.append(message)
    
    def add_passed(self) -> None:
        """Record a passed check."""
        self.passed_checks += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_valid": self.is_valid,
            "total_checks": self.total_checks,
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
            "warnings": self.warnings[:50],  # Limit to first 50
            "errors": self.errors[:50]
        }


class ConsistencyService:
    """
    Service for ensuring data consistency across collections.
    
    Tracks IDs and metadata from generated data to validate
    cross-references and relationships.
    """
    
    def __init__(self):
        """Initialize the consistency service."""
        self.reset()
    
    def reset(self) -> None:
        """Reset all tracked data."""
        self._product_ids: Set[str] = set()
        self._product_prices: Dict[str, float] = {}
        self._product_categories: Dict[str, str] = {}
        self._product_brands: Dict[str, str] = {}
        
        self._user_ids: Set[str] = set()
        self._user_budgets: Dict[str, Tuple[float, float]] = {}
        self._user_categories: Dict[str, List[str]] = {}
        
        self._review_ids: Set[str] = set()
        self._reviews_by_product: Dict[str, List[str]] = {}
        
        self._interaction_ids: Set[str] = set()
    
    # === Product Registration ===
    
    def register_product(self, product_id: str, price: float, 
                        category: str, brand: str) -> None:
        """
        Register a product for consistency tracking.
        
        Args:
            product_id: Unique product identifier.
            price: Product price.
            category: Product category.
            brand: Product brand.
        """
        self._product_ids.add(product_id)
        self._product_prices[product_id] = price
        self._product_categories[product_id] = category
        self._product_brands[product_id] = brand
    
    def register_products(self, products: List[Any]) -> None:
        """
        Register multiple products.
        
        Args:
            products: List of Product objects.
        """
        for product in products:
            self.register_product(
                product_id=product.id,
                price=product.price,
                category=product.category,
                brand=product.brand
            )
        logger.info(f"Registered {len(products)} products for consistency tracking")
    
    # === User Registration ===
    
    def register_user(self, user_id: str, budget_min: float, 
                     budget_max: float, categories: List[str]) -> None:
        """
        Register a user for consistency tracking.
        
        Args:
            user_id: Unique user identifier.
            budget_min: Minimum budget.
            budget_max: Maximum budget.
            categories: Preferred categories.
        """
        self._user_ids.add(user_id)
        self._user_budgets[user_id] = (budget_min, budget_max)
        self._user_categories[user_id] = categories
    
    def register_users(self, users: List[Any]) -> None:
        """
        Register multiple users.
        
        Args:
            users: List of User objects.
        """
        for user in users:
            financial = getattr(user, 'financial_context', {})
            if isinstance(financial, dict):
                budget_min = financial.get('budget_min', 0)
                budget_max = financial.get('budget_max', 10000)
            else:
                budget_min = getattr(financial, 'budget_min', 0)
                budget_max = getattr(financial, 'budget_max', 10000)
            
            categories = getattr(user, 'preferred_categories', [])
            
            self.register_user(
                user_id=user.id,
                budget_min=budget_min,
                budget_max=budget_max,
                categories=categories
            )
        logger.info(f"Registered {len(users)} users for consistency tracking")
    
    # === Review Registration ===
    
    def register_review(self, review_id: str, product_id: str) -> None:
        """
        Register a review for consistency tracking.
        
        Args:
            review_id: Unique review identifier.
            product_id: Referenced product ID.
        """
        self._review_ids.add(review_id)
        
        if product_id not in self._reviews_by_product:
            self._reviews_by_product[product_id] = []
        self._reviews_by_product[product_id].append(review_id)
    
    def register_reviews(self, reviews: List[Any]) -> None:
        """
        Register multiple reviews.
        
        Args:
            reviews: List of Review objects.
        """
        for review in reviews:
            self.register_review(
                review_id=review.review_id,
                product_id=review.product_id
            )
        logger.info(f"Registered {len(reviews)} reviews for consistency tracking")
    
    # === Interaction Registration ===
    
    def register_interaction(self, interaction_id: str) -> None:
        """
        Register an interaction for consistency tracking.
        
        Args:
            interaction_id: Unique interaction identifier.
        """
        self._interaction_ids.add(interaction_id)
    
    def register_interactions(self, interactions: List[Any]) -> None:
        """
        Register multiple interactions.
        
        Args:
            interactions: List of Interaction objects.
        """
        for interaction in interactions:
            self.register_interaction(interaction.id)
        logger.info(f"Registered {len(interactions)} interactions for consistency tracking")
    
    # === Validation Methods ===
    
    def validate_product_id(self, product_id: str) -> bool:
        """Check if a product ID exists."""
        return product_id in self._product_ids
    
    def validate_user_id(self, user_id: str) -> bool:
        """Check if a user ID exists."""
        return user_id in self._user_ids
    
    def validate_review_id(self, review_id: str) -> bool:
        """Check if a review ID exists."""
        return review_id in self._review_ids
    
    def validate_reviews(self, reviews: List[Any]) -> ConsistencyReport:
        """
        Validate all reviews for consistency.
        
        Args:
            reviews: List of Review objects.
            
        Returns:
            ConsistencyReport with validation results.
        """
        report = ConsistencyReport()
        
        for review in reviews:
            report.total_checks += 1
            
            # Check product reference
            if not self.validate_product_id(review.product_id):
                report.add_error(
                    f"Review {review.review_id} references non-existent product {review.product_id}"
                )
            else:
                report.add_passed()
        
        if report.is_valid:
            logger.info(f"All {len(reviews)} reviews passed consistency checks")
        else:
            logger.warning(f"Review validation found {report.failed_checks} errors")
        
        return report
    
    def validate_interactions(self, interactions: List[Any]) -> ConsistencyReport:
        """
        Validate all interactions for consistency.
        
        Args:
            interactions: List of Interaction objects.
            
        Returns:
            ConsistencyReport with validation results.
        """
        report = ConsistencyReport()
        
        budget_violations = 0
        
        for interaction in interactions:
            report.total_checks += 2  # User check + product check
            
            # Check user reference
            if not self.validate_user_id(interaction.user_id):
                report.add_error(
                    f"Interaction {interaction.interaction_id} references non-existent user {interaction.user_id}"
                )
            else:
                report.add_passed()
            
            # Check product reference (if applicable)
            if interaction.product_id:
                if not self.validate_product_id(interaction.product_id):
                    report.add_error(
                        f"Interaction {interaction.interaction_id} references non-existent product {interaction.product_id}"
                    )
                else:
                    report.add_passed()
                    
                    # Check budget alignment for purchases
                    if interaction.interaction_type == "purchase":
                        user_budget = self._user_budgets.get(interaction.user_id)
                        product_price = self._product_prices.get(interaction.product_id)
                        
                        if user_budget and product_price:
                            if product_price > user_budget[1] * 1.2:  # 20% tolerance
                                budget_violations += 1
            else:
                report.add_passed()  # No product to check
        
        if budget_violations > 0:
            violation_pct = budget_violations / len([i for i in interactions if i.interaction_type == "purchase"]) * 100
            if violation_pct > 15:
                report.add_warning(
                    f"{budget_violations} purchase interactions exceed user budget (may indicate unrealistic data)"
                )
        
        if report.is_valid:
            logger.info(f"All {len(interactions)} interactions passed consistency checks")
        else:
            logger.warning(f"Interaction validation found {report.failed_checks} errors")
        
        return report
    
    # === Query Methods ===
    
    def get_product_ids(self) -> List[str]:
        """Get all registered product IDs."""
        return list(self._product_ids)
    
    def get_user_ids(self) -> List[str]:
        """Get all registered user IDs."""
        return list(self._user_ids)
    
    def get_products_for_user(self, user_id: str, 
                              max_count: int = 10,
                              within_budget: bool = True) -> List[str]:
        """
        Get products that match a user's budget and interests.
        
        Args:
            user_id: User identifier.
            max_count: Maximum products to return.
            within_budget: Only return products within user's budget.
            
        Returns:
            List of product IDs.
        """
        user_budget = self._user_budgets.get(user_id, (0, 10000))
        user_cats = self._user_categories.get(user_id, [])
        
        matching_products = []
        
        for product_id in self._product_ids:
            price = self._product_prices.get(product_id, 0)
            category = self._product_categories.get(product_id, "")
            
            # Check budget
            if within_budget and price > user_budget[1]:
                continue
            
            # Prefer matching categories
            if user_cats and category in user_cats:
                matching_products.insert(0, product_id)  # Priority
            else:
                matching_products.append(product_id)
            
            if len(matching_products) >= max_count * 2:
                break
        
        return matching_products[:max_count]
    
    def get_reviews_for_product(self, product_id: str) -> List[str]:
        """Get all review IDs for a product."""
        return self._reviews_by_product.get(product_id, [])
    
    def get_product_review_counts(self) -> Dict[str, int]:
        """Get review counts for all products."""
        return {
            product_id: len(reviews) 
            for product_id, reviews in self._reviews_by_product.items()
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about registered data."""
        return {
            "products": {
                "count": len(self._product_ids),
                "categories": len(set(self._product_categories.values())),
                "brands": len(set(self._product_brands.values())),
                "price_range": {
                    "min": min(self._product_prices.values()) if self._product_prices else 0,
                    "max": max(self._product_prices.values()) if self._product_prices else 0
                }
            },
            "users": {
                "count": len(self._user_ids),
                "budget_range": {
                    "min": min(b[0] for b in self._user_budgets.values()) if self._user_budgets else 0,
                    "max": max(b[1] for b in self._user_budgets.values()) if self._user_budgets else 0
                }
            },
            "reviews": {
                "count": len(self._review_ids),
                "products_with_reviews": len(self._reviews_by_product)
            },
            "interactions": {
                "count": len(self._interaction_ids)
            }
        }


# Singleton instance
_consistency_service: Optional[ConsistencyService] = None


def get_consistency_service() -> ConsistencyService:
    """Get or create the consistency service singleton."""
    global _consistency_service
    
    if _consistency_service is None:
        _consistency_service = ConsistencyService()
    
    return _consistency_service
