"""
User Profile Generator for FinFind.

Generates realistic user profiles with diverse financial contexts,
payment preferences, and shopping behaviors.
"""

import random
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import numpy as np
from tqdm import tqdm
import logging

from .base_generator import BaseGenerator
from ..config import GenerationConfig, USER_PERSONAS, BRANDS_BY_CATEGORY
from ..models.user_models import (
    UserProfile, FinancialContext, UserPreferences, PurchaseHistoryItem
)
from ..models.product_models import Product

logger = logging.getLogger(__name__)


class UserProfileGenerator(BaseGenerator):
    """Generator for creating realistic user profiles."""
    
    def __init__(
        self, 
        config: Optional[GenerationConfig] = None,
        products: Optional[List[Product]] = None
    ):
        """
        Initialize the user profile generator.
        
        Args:
            config: Generation configuration.
            products: Previously generated products for purchase history.
        """
        super().__init__(config)
        self.products = products or []
        
        # Index products by category for purchase history generation
        self._products_by_category: Dict[str, List[Product]] = {}
        self._products_by_price_range: Dict[str, List[Product]] = {}
        self._build_product_indexes()
        
        # Calculate persona weights for random selection
        self._persona_weights = self._calculate_persona_weights()
    
    def _build_product_indexes(self) -> None:
        """Build indexes for efficient product lookup."""
        for product in self.products:
            # By category
            if product.category not in self._products_by_category:
                self._products_by_category[product.category] = []
            self._products_by_category[product.category].append(product)
            
            # By price range
            price_range = self._get_price_range_key(product.price)
            if price_range not in self._products_by_price_range:
                self._products_by_price_range[price_range] = []
            self._products_by_price_range[price_range].append(product)
        
        logger.info(f"Indexed {len(self.products)} products across {len(self._products_by_category)} categories")
    
    def _get_price_range_key(self, price: float) -> str:
        """Categorize price into a range key."""
        if price < 50:
            return "budget"
        elif price < 200:
            return "moderate_low"
        elif price < 500:
            return "moderate_high"
        elif price < 1000:
            return "premium"
        else:
            return "luxury"
    
    def _calculate_persona_weights(self) -> Dict[str, float]:
        """Calculate normalized weights for persona selection."""
        weights = {
            persona: data["weight"] 
            for persona, data in USER_PERSONAS.items()
        }
        total = sum(weights.values())
        return {k: v / total for k, v in weights.items()}
    
    def generate(self) -> List[UserProfile]:
        """
        Generate user profiles.
        
        Returns:
            List of UserProfile objects.
        """
        logger.info(f"Generating {self.config.num_users} user profiles...")
        users = []
        
        # Determine persona distribution
        persona_counts = self._distribute_personas()
        
        for persona_type, count in tqdm(persona_counts.items(), desc="Generating personas"):
            for _ in range(count):
                user = self._generate_user(persona_type)
                users.append(user)
        
        # Shuffle to mix personas
        random.shuffle(users)
        
        # Generate embeddings
        if self.config.generate_embeddings:
            self._add_embeddings(users)
        
        logger.info(f"Generated {len(users)} user profiles")
        return users
    
    def _distribute_personas(self) -> Dict[str, int]:
        """Distribute total users across personas based on weights."""
        counts = {}
        remaining = self.config.num_users
        
        personas = list(USER_PERSONAS.keys())
        for i, persona in enumerate(personas):
            if i == len(personas) - 1:
                # Last persona gets remaining
                counts[persona] = remaining
            else:
                count = int(self.config.num_users * self._persona_weights[persona])
                counts[persona] = count
                remaining -= count
        
        return counts
    
    def _generate_user(self, persona_type: str) -> UserProfile:
        """
        Generate a single user profile based on persona type.
        
        Args:
            persona_type: Type of persona to generate.
            
        Returns:
            UserProfile object.
        """
        persona = USER_PERSONAS[persona_type]
        
        # Generate age
        age_range = self._select_weighted(
            persona["age_ranges"],
            persona["age_weights"]
        )
        
        # Generate financial context
        financial_context = self._generate_financial_context(persona)
        
        # Generate payment methods
        payment_methods, primary_method = self._generate_payment_methods(persona)
        
        # Generate preferences
        preferences = self._generate_preferences(persona, financial_context)
        
        # Generate financial goals
        num_goals = random.randint(2, 4)
        financial_goals = random.sample(persona["financial_goals"], min(num_goals, len(persona["financial_goals"])))
        
        # Generate purchase history (if products available)
        purchase_history = self._generate_purchase_history(
            persona_type, 
            preferences, 
            financial_context,
            payment_methods
        )
        
        # Calculate derived metrics
        total_ltv = sum(p.price_paid for p in purchase_history)
        purchase_count = len(purchase_history)
        avg_order_value = total_ltv / purchase_count if purchase_count > 0 else 0
        
        # Days since registration (random, older for seniors/families)
        base_days = {"student": 180, "young_professional": 365, "family": 730, 
                     "affluent": 540, "senior": 900, "budget_conscious": 400, "luxury_shopper": 450}
        days_registered = int(np.random.exponential(base_days.get(persona_type, 365)))
        days_registered = min(days_registered, 1800)  # Cap at 5 years
        
        # Days since last purchase
        days_since_purchase = None
        if purchase_history:
            # Most recent purchase was most recent in our history
            days_since_purchase = random.randint(1, 90)
        
        # Session count based on engagement
        session_multiplier = {
            "student": 1.2, "young_professional": 1.0, "family": 0.9,
            "affluent": 0.8, "senior": 0.7, "budget_conscious": 1.3, "luxury_shopper": 0.6
        }
        avg_sessions = days_registered / 7 * session_multiplier.get(persona_type, 1.0)
        session_count = int(np.random.poisson(avg_sessions))
        
        return UserProfile(
            persona_type=persona_type,
            age_range=age_range,
            financial_context=financial_context,
            payment_methods=payment_methods,
            primary_payment_method=primary_method,
            preferences=preferences,
            financial_goals=financial_goals,
            purchase_history=purchase_history,
            total_lifetime_value=round(total_ltv, 2),
            purchase_count=purchase_count,
            avg_order_value=round(avg_order_value, 2),
            days_since_last_purchase=days_since_purchase,
            days_since_registration=days_registered,
            session_count=max(1, session_count)
        )
    
    def _generate_financial_context(self, persona: Dict) -> FinancialContext:
        """Generate financial context for a user."""
        # Budget range (use gamma distribution for realistic spread)
        budget_min, budget_max = persona["budget_range"]
        budget_low = random.uniform(budget_min * 0.8, budget_min * 1.2)
        budget_high = random.uniform(budget_max * 0.8, budget_max * 1.2)
        budget_low = max(budget_low, 20)  # Minimum $20
        
        # Monthly discretionary
        monthly_min, monthly_max = persona["monthly_discretionary"]
        monthly = random.uniform(monthly_min, monthly_max)
        
        # Affordability score
        aff_min, aff_max = persona["affordability_score_range"]
        affordability = random.uniform(aff_min, aff_max)
        
        # Risk tolerance
        risk_tolerance = self._select_weighted(
            list(persona["risk_tolerance_weights"].keys()),
            list(persona["risk_tolerance_weights"].values())
        )
        
        # Spending style
        spending_style = self._select_weighted(
            list(persona["spending_style_weights"].keys()),
            list(persona["spending_style_weights"].values())
        )
        
        # Credit card ownership (higher income = higher chance)
        has_credit = random.random() < (0.5 + affordability * 0.4)
        
        # Credit utilization (if has credit card)
        credit_util = None
        if has_credit:
            # Lower income tends to higher utilization
            base_util = 1 - affordability  # Inverse relationship
            credit_util = np.clip(np.random.normal(base_util * 0.5, 0.15), 0, 0.95)
        
        # Prefers installments (lower income more likely)
        prefers_installments = random.random() < (0.6 - affordability * 0.5)
        
        return FinancialContext(
            budget_min=round(budget_low, 2),
            budget_max=round(budget_high, 2),
            monthly_discretionary=round(monthly, 2),
            affordability_score=round(affordability, 3),
            risk_tolerance=risk_tolerance,
            spending_style=spending_style,
            has_credit_card=has_credit,
            credit_utilization=round(credit_util, 3) if credit_util else None,
            prefers_installments=prefers_installments
        )
    
    def _generate_payment_methods(self, persona: Dict) -> tuple:
        """Generate payment methods and primary method."""
        primary_methods = persona["payment_methods"]["primary"]
        secondary_methods = persona["payment_methods"]["secondary"]
        
        # Always include at least one primary method
        methods = [random.choice(primary_methods)]
        
        # 60% chance to add another primary
        if random.random() < 0.6 and len(primary_methods) > 1:
            other_primary = [m for m in primary_methods if m != methods[0]]
            if other_primary:
                methods.append(random.choice(other_primary))
        
        # 40% chance to add a secondary
        if random.random() < 0.4:
            methods.append(random.choice(secondary_methods))
        
        # Primary is usually the first one
        primary = methods[0]
        
        return list(set(methods)), primary
    
    def _generate_preferences(
        self, 
        persona: Dict, 
        financial_context: FinancialContext
    ) -> UserPreferences:
        """Generate shopping preferences."""
        # Category affinity (add some noise to base values)
        category_affinity = {}
        for category, base_affinity in persona["category_affinities"].items():
            noise = np.random.normal(0, 0.1)
            affinity = np.clip(base_affinity + noise, 0, 1)
            category_affinity[category] = round(affinity, 3)
        
        # Brand preferences based on affordability
        preferred_brands = []
        avoided_brands = []
        
        for category, affinity in category_affinity.items():
            if affinity > 0.6 and category in BRANDS_BY_CATEGORY:
                brands = BRANDS_BY_CATEGORY[category]
                
                # High affordability prefers premium
                if financial_context.affordability_score > 0.7:
                    if random.random() < 0.7:
                        preferred_brands.extend(random.sample(brands["premium"], min(2, len(brands["premium"]))))
                    if random.random() < 0.3:
                        avoided_brands.extend(random.sample(brands["budget"], min(1, len(brands["budget"]))))
                
                # Low affordability prefers budget
                elif financial_context.affordability_score < 0.4:
                    if random.random() < 0.6:
                        preferred_brands.extend(random.sample(brands["budget"], min(2, len(brands["budget"]))))
                    if random.random() < 0.2:
                        avoided_brands.extend(random.sample(brands["premium"], min(1, len(brands["premium"]))))
                
                # Middle prefers mid-tier
                else:
                    if random.random() < 0.5:
                        preferred_brands.extend(random.sample(brands["mid_tier"], min(2, len(brands["mid_tier"]))))
        
        # Deduplicate
        preferred_brands = list(set(preferred_brands))[:10]
        avoided_brands = list(set(avoided_brands))[:5]
        
        # Price sensitivity (inverse of affordability + persona factor)
        base_sensitivity = 1 - financial_context.affordability_score
        if persona.get("deal_seeker_prob", 0.5) > 0.7:
            base_sensitivity += 0.1
        price_sensitivity = np.clip(base_sensitivity + np.random.normal(0, 0.1), 0.1, 0.95)
        
        # Quality preference (correlated with affordability)
        quality_pref = financial_context.affordability_score * 0.8 + np.random.normal(0, 0.1)
        quality_pref = np.clip(quality_pref, 0.2, 0.95)
        
        # Reviews importance
        rev_min, rev_max = persona["reviews_importance_range"]
        reviews_importance = random.uniform(rev_min, rev_max)
        
        # Brand loyalty
        loy_min, loy_max = persona["brand_loyalty_range"]
        brand_loyalty = random.uniform(loy_min, loy_max)
        
        # Deal seeking
        deal_seeker = random.random() < persona["deal_seeker_prob"]
        waits_for_sales = deal_seeker and random.random() < 0.6
        uses_coupons = deal_seeker and random.random() < 0.7
        
        return UserPreferences(
            category_affinity=category_affinity,
            preferred_brands=preferred_brands,
            avoided_brands=avoided_brands,
            brand_loyalty_score=round(brand_loyalty, 3),
            price_sensitivity=round(price_sensitivity, 3),
            quality_preference=round(quality_pref, 3),
            reviews_importance=round(reviews_importance, 3),
            deal_seeker=deal_seeker,
            waits_for_sales=waits_for_sales,
            uses_coupons=uses_coupons
        )
    
    def _generate_purchase_history(
        self,
        persona_type: str,
        preferences: UserPreferences,
        financial_context: FinancialContext,
        payment_methods: List[str]
    ) -> List[PurchaseHistoryItem]:
        """Generate realistic purchase history."""
        if not self.products:
            return []
        
        # Number of past purchases based on persona
        purchase_counts = {
            "student": (2, 8),
            "young_professional": (5, 15),
            "family": (8, 25),
            "affluent": (10, 30),
            "senior": (5, 15),
            "budget_conscious": (3, 10),
            "luxury_shopper": (5, 20)
        }
        min_p, max_p = purchase_counts.get(persona_type, (3, 12))
        num_purchases = random.randint(min_p, max_p)
        
        history = []
        
        # Get products user can afford and is interested in
        affordable_products = self._get_affordable_products(financial_context)
        interested_products = self._get_interested_products(preferences, affordable_products)
        
        if not interested_products:
            interested_products = affordable_products
        
        if not interested_products:
            # Fall back to all products, but prefer cheaper ones
            interested_products = sorted(self.products, key=lambda p: p.price)[:100]
        
        # Generate purchases over past year
        now = datetime.utcnow()
        
        for _ in range(min(num_purchases, len(interested_products))):
            product = random.choice(interested_products)
            
            # Remove to avoid duplicates (but allow some repeats for consumables)
            if product.category not in ["Beauty & Personal Care", "Books & Media"]:
                interested_products = [p for p in interested_products if p.id != product.id]
            
            # Days ago (more recent for more active shoppers)
            days_ago = random.randint(7, 365)
            purchased_at = now - timedelta(days=days_ago)
            
            # Payment method
            payment = random.choice(payment_methods)
            
            # Was on sale (budget conscious more likely to buy on sale)
            on_sale = random.random() < (0.3 + preferences.price_sensitivity * 0.4)
            
            # Price paid (discount if on sale)
            price_paid = product.price
            if on_sale:
                discount = random.uniform(0.10, 0.35)
                price_paid = product.price * (1 - discount)
            
            # Satisfaction (affected by quality preference match)
            base_satisfaction = 3.5 + random.uniform(-0.5, 1.0)
            if product.rating_avg > 4.0 and preferences.quality_preference > 0.6:
                base_satisfaction += 0.5
            satisfaction = np.clip(base_satisfaction, 1, 5)
            
            history.append(PurchaseHistoryItem(
                product_id=product.id,
                category=product.category,
                subcategory=product.subcategory,
                brand=product.brand,
                price_paid=round(price_paid, 2),
                payment_method=payment,
                purchased_at=purchased_at,
                was_on_sale=on_sale,
                satisfaction_score=round(satisfaction, 1)
            ))
        
        # Sort by date (most recent first)
        history.sort(key=lambda x: x.purchased_at, reverse=True)
        
        return history
    
    def _get_affordable_products(self, financial_context: FinancialContext) -> List[Product]:
        """Get products within user's budget."""
        max_price = financial_context.budget_max * 1.2  # Allow slight overspend
        return [p for p in self.products if p.price <= max_price]
    
    def _get_interested_products(
        self, 
        preferences: UserPreferences,
        product_pool: List[Product]
    ) -> List[Product]:
        """Filter products by user's category interests."""
        interested = []
        
        for product in product_pool:
            category_interest = preferences.category_affinity.get(product.category, 0.3)
            
            # Higher interest = higher chance of considering
            if random.random() < category_interest:
                # Brand preference bonus
                if product.brand in preferences.preferred_brands:
                    interested.append(product)
                    interested.append(product)  # Add twice for higher weight
                elif product.brand not in preferences.avoided_brands:
                    interested.append(product)
        
        return interested
    
    def _add_embeddings(self, users: List[UserProfile]) -> None:
        """Add embeddings to user profiles."""
        texts = [user.get_embedding_text() for user in users]
        embeddings = self.generate_embeddings(texts)
        
        for user, embedding in zip(users, embeddings):
            user.embedding = embedding
    
    def _select_weighted(self, options: List, weights: List[float]) -> Any:
        """Select from options based on weights."""
        total = sum(weights)
        normalized = [w / total for w in weights]
        return np.random.choice(options, p=normalized)
    
    def validate(self, users: List[UserProfile]) -> bool:
        """
        Validate generated user profiles.
        
        Args:
            users: List of UserProfile objects to validate.
            
        Returns:
            True if all validations pass.
        """
        logger.info("Validating generated user profiles...")
        
        errors = []
        warnings = []
        
        # Check total count
        if len(users) < self.config.num_users:
            errors.append(f"Expected {self.config.num_users} users, got {len(users)}")
        
        # Check for unique IDs
        ids = [u.id for u in users]
        if len(ids) != len(set(ids)):
            errors.append("Duplicate user IDs found")
        
        # Check persona distribution
        persona_counts = {}
        for user in users:
            persona_counts[user.persona_type] = persona_counts.get(user.persona_type, 0) + 1
        
        logger.info(f"Persona distribution: {persona_counts}")
        
        # Validate each user
        for user in users:
            # Budget validation
            if user.financial_context.budget_min >= user.financial_context.budget_max:
                errors.append(f"User {user.id}: budget_min >= budget_max")
            
            # Payment methods validation
            if user.primary_payment_method not in user.payment_methods:
                errors.append(f"User {user.id}: primary payment method not in payment methods")
            
            # Embedding validation
            if self.config.generate_embeddings and not user.embedding:
                warnings.append(f"User {user.id}: missing embedding")
            
            # Purchase history validation
            for purchase in user.purchase_history:
                if purchase.price_paid <= 0:
                    errors.append(f"User {user.id}: invalid purchase price")
        
        # Report
        for warning in warnings[:5]:
            logger.warning(warning)
        for error in errors[:5]:
            logger.error(error)
        
        if errors:
            logger.error(f"Validation failed with {len(errors)} errors")
            return False
        
        if warnings:
            logger.warning(f"Validation passed with {len(warnings)} warnings")
        else:
            logger.info("Validation passed successfully")
        
        return True
    
    def get_statistics(self, users: List[UserProfile]) -> Dict[str, Any]:
        """
        Generate statistics about the user profiles.
        
        Args:
            users: List of UserProfile objects.
            
        Returns:
            Dictionary of statistics.
        """
        stats = {
            "total_users": len(users),
            "personas": {},
            "age_ranges": {},
            "payment_methods": {},
            "financial_metrics": {
                "avg_budget_min": 0,
                "avg_budget_max": 0,
                "avg_affordability": 0
            },
            "purchase_history": {
                "total_purchases": 0,
                "avg_purchases_per_user": 0,
                "total_ltv": 0
            }
        }
        
        budgets_min = []
        budgets_max = []
        affordabilities = []
        total_purchases = 0
        total_ltv = 0
        
        for user in users:
            # Persona counts
            stats["personas"][user.persona_type] = stats["personas"].get(user.persona_type, 0) + 1
            
            # Age ranges
            stats["age_ranges"][user.age_range] = stats["age_ranges"].get(user.age_range, 0) + 1
            
            # Payment methods
            for method in user.payment_methods:
                stats["payment_methods"][method] = stats["payment_methods"].get(method, 0) + 1
            
            # Financial metrics
            budgets_min.append(user.financial_context.budget_min)
            budgets_max.append(user.financial_context.budget_max)
            affordabilities.append(user.financial_context.affordability_score)
            
            # Purchase history
            total_purchases += len(user.purchase_history)
            total_ltv += user.total_lifetime_value
        
        stats["financial_metrics"]["avg_budget_min"] = round(np.mean(budgets_min), 2)
        stats["financial_metrics"]["avg_budget_max"] = round(np.mean(budgets_max), 2)
        stats["financial_metrics"]["avg_affordability"] = round(np.mean(affordabilities), 3)
        
        stats["purchase_history"]["total_purchases"] = total_purchases
        stats["purchase_history"]["avg_purchases_per_user"] = round(total_purchases / len(users), 2)
        stats["purchase_history"]["total_ltv"] = round(total_ltv, 2)
        
        return stats
