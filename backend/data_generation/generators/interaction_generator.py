"""
User Interaction Generator for FinFind.

Generates realistic user interaction sequences including searches, clicks,
cart actions, and purchases with proper session tracking and behavioral patterns.
"""

import random
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from tqdm import tqdm
import logging

from .base_generator import BaseGenerator
from ..config import (
    GenerationConfig, USER_PERSONAS, BRANDS_BY_CATEGORY,
    CATEGORY_HIERARCHY, SEARCH_QUERY_TEMPLATES, SEARCH_FILL_INS,
    FUNNEL_PROBABILITIES, HOURLY_ACTIVITY_WEIGHTS, DAILY_ACTIVITY_WEIGHTS,
    DEVICE_PREFERENCES, SESSION_CONFIG
)
from ..models.user_models import UserProfile
from ..models.product_models import Product
from ..models.interaction_models import (
    UserInteraction, SearchContext, ViewContext, CartContext,
    PurchaseContext, WishlistContext, FinancialSnapshot
)

logger = logging.getLogger(__name__)


class InteractionGenerator(BaseGenerator):
    """Generator for creating realistic user interaction sequences."""
    
    def __init__(
        self,
        config: Optional[GenerationConfig] = None,
        users: Optional[List[UserProfile]] = None,
        products: Optional[List[Product]] = None
    ):
        """
        Initialize the interaction generator.
        
        Args:
            config: Generation configuration.
            users: Previously generated user profiles.
            products: Previously generated products.
        """
        super().__init__(config)
        self.users = users or []
        self.products = products or []
        
        # Build indexes for efficient lookup
        self._user_map: Dict[str, UserProfile] = {u.id: u for u in self.users}
        self._product_map: Dict[str, Product] = {p.id: p for p in self.products}
        self._products_by_category: Dict[str, List[Product]] = {}
        self._products_by_subcategory: Dict[str, List[Product]] = {}
        self._build_product_indexes()
        
        # Pre-compute normalized hour and day weights
        self._hour_weights = self._normalize_weights(HOURLY_ACTIVITY_WEIGHTS)
        self._day_weights = self._normalize_weights(DAILY_ACTIVITY_WEIGHTS)
        
        # Session tracking
        self._sessions: Dict[str, List[UserInteraction]] = {}
        
    def _build_product_indexes(self) -> None:
        """Build indexes for product lookup."""
        for product in self.products:
            # By category
            if product.category not in self._products_by_category:
                self._products_by_category[product.category] = []
            self._products_by_category[product.category].append(product)
            
            # By subcategory
            if product.subcategory not in self._products_by_subcategory:
                self._products_by_subcategory[product.subcategory] = []
            self._products_by_subcategory[product.subcategory].append(product)
    
    def _normalize_weights(self, weights: Dict) -> Dict:
        """Normalize weights to sum to 1."""
        total = sum(weights.values())
        return {k: v / total for k, v in weights.items()}
    
    def generate(self) -> List[UserInteraction]:
        """
        Generate user interactions.
        
        Returns:
            List of UserInteraction objects.
        """
        logger.info(f"Generating {self.config.num_interactions} user interactions...")
        
        if not self.users:
            logger.error("No users provided for interaction generation")
            return []
        
        if not self.products:
            logger.error("No products provided for interaction generation")
            return []
        
        interactions = []
        
        # Calculate sessions needed
        avg_interactions_per_session = SESSION_CONFIG["avg_interactions_per_session"]
        estimated_sessions = int(self.config.num_interactions / avg_interactions_per_session * 1.2)
        
        # Distribute sessions across users (some users more active than others)
        user_session_counts = self._distribute_sessions_to_users(estimated_sessions)
        
        # Generate sessions for each user
        for user_id, session_count in tqdm(user_session_counts.items(), desc="Generating sessions"):
            user = self._user_map[user_id]
            
            for _ in range(session_count):
                session_interactions = self._generate_session(user)
                interactions.extend(session_interactions)
                
                # Check if we have enough
                if len(interactions) >= self.config.num_interactions:
                    break
            
            if len(interactions) >= self.config.num_interactions:
                break
        
        # Trim to exact count
        interactions = interactions[:self.config.num_interactions]
        
        # Sort by timestamp
        interactions.sort(key=lambda x: x.timestamp)
        
        # Generate query embeddings for searches
        if self.config.generate_embeddings:
            self._add_query_embeddings(interactions)
        
        logger.info(f"Generated {len(interactions)} interactions")
        return interactions
    
    def _distribute_sessions_to_users(self, total_sessions: int) -> Dict[str, int]:
        """
        Distribute sessions across users based on activity levels.
        
        More engaged users (higher session_count in profile) get more sessions.
        """
        # Weight users by their session count
        weights = {u.id: max(1, u.session_count) for u in self.users}
        total_weight = sum(weights.values())
        
        distribution = {}
        remaining = total_sessions
        
        users = list(self.users)
        random.shuffle(users)
        
        for i, user in enumerate(users):
            if i == len(users) - 1:
                distribution[user.id] = remaining
            else:
                share = int(total_sessions * weights[user.id] / total_weight)
                share = max(1, share)  # At least 1 session
                distribution[user.id] = share
                remaining -= share
        
        return distribution
    
    def _generate_session(self, user: UserProfile) -> List[UserInteraction]:
        """
        Generate a complete user session with realistic behavior patterns.
        
        Args:
            user: The user profile for this session.
            
        Returns:
            List of interactions for this session.
        """
        session_id = f"sess_{uuid.uuid4().hex[:16]}"
        interactions = []
        
        # Determine session timing
        session_start = self._generate_session_start()
        current_time = session_start
        
        # Determine device based on time
        device = self._select_device_for_time(session_start.hour)
        
        # Determine session length
        duration = max(
            SESSION_CONFIG["min_session_duration"],
            min(
                np.random.normal(
                    SESSION_CONFIG["avg_session_duration_seconds"],
                    SESSION_CONFIG["session_duration_std"]
                ),
                SESSION_CONFIG["max_session_duration"]
            )
        )
        session_end = session_start + timedelta(seconds=duration)
        
        # Track session state
        cart = []  # Products in cart
        viewed_products = []  # Products viewed
        interaction_number = 0
        current_state = "search"  # Start with a search
        
        # Generate financial snapshot
        financial_snapshot = self._create_financial_snapshot(user, cart)
        
        # Session loop
        while current_time < session_end:
            interaction_number += 1
            time_in_session = (current_time - session_start).seconds
            
            if current_state == "search":
                # Generate a search interaction
                search_interaction = self._generate_search_interaction(
                    user, session_id, current_time, device,
                    interaction_number, time_in_session, financial_snapshot
                )
                interactions.append(search_interaction)
                
                # Decide next action
                current_state = self._get_next_state("search", user)
            
            elif current_state == "view":
                # Select a product to view
                product = self._select_product_to_view(user, viewed_products)
                
                if product:
                    viewed_products.append(product.id)
                    
                    view_interaction = self._generate_view_interaction(
                        user, product, session_id, current_time, device,
                        interaction_number, time_in_session, financial_snapshot
                    )
                    interactions.append(view_interaction)
                
                # Decide next action
                current_state = self._get_next_state("view", user)
            
            elif current_state == "add_to_cart":
                # Add last viewed product to cart
                if viewed_products:
                    product_id = viewed_products[-1]
                    product = self._product_map.get(product_id)
                    
                    if product and product_id not in cart:
                        cart.append(product_id)
                        
                        cart_interaction = self._generate_cart_interaction(
                            user, product, session_id, current_time, device,
                            interaction_number, time_in_session, financial_snapshot,
                            action="add", cart=cart
                        )
                        interactions.append(cart_interaction)
                        
                        # Update financial snapshot
                        financial_snapshot = self._create_financial_snapshot(user, cart)
                
                current_state = self._get_next_state("add_to_cart", user)
            
            elif current_state == "remove_from_cart":
                # Remove a product from cart
                if cart:
                    product_id = random.choice(cart)
                    product = self._product_map.get(product_id)
                    cart.remove(product_id)
                    
                    if product:
                        cart_interaction = self._generate_cart_interaction(
                            user, product, session_id, current_time, device,
                            interaction_number, time_in_session, financial_snapshot,
                            action="remove", cart=cart
                        )
                        interactions.append(cart_interaction)
                        financial_snapshot = self._create_financial_snapshot(user, cart)
                
                current_state = "view"  # Continue browsing
            
            elif current_state == "wishlist":
                # Add to wishlist
                if viewed_products:
                    product_id = viewed_products[-1]
                    product = self._product_map.get(product_id)
                    
                    if product:
                        wishlist_interaction = self._generate_wishlist_interaction(
                            user, product, session_id, current_time, device,
                            interaction_number, time_in_session, financial_snapshot
                        )
                        interactions.append(wishlist_interaction)
                
                current_state = self._get_next_state("wishlist", user)
            
            elif current_state == "purchase":
                # Make a purchase
                if cart:
                    purchase_interaction = self._generate_purchase_interaction(
                        user, cart, session_id, current_time, device,
                        interaction_number, time_in_session, financial_snapshot
                    )
                    interactions.append(purchase_interaction)
                    
                    # Mark interactions as converted
                    for interaction in interactions:
                        interaction.led_to_conversion = True
                    
                    cart = []  # Clear cart
                    financial_snapshot = self._create_financial_snapshot(user, cart)
                
                current_state = "abandon"  # End session after purchase
            
            elif current_state == "abandon":
                break  # End session
            
            # Advance time
            time_delta = max(10, np.random.normal(
                SESSION_CONFIG["time_between_interactions_mean"],
                SESSION_CONFIG["time_between_interactions_std"]
            ))
            current_time += timedelta(seconds=time_delta)
            
            # Safety check: max interactions per session
            if interaction_number >= SESSION_CONFIG["max_interactions_per_session"]:
                break
        
        return interactions
    
    def _generate_session_start(self) -> datetime:
        """Generate a realistic session start time."""
        # Random date in the past 90 days
        days_ago = random.randint(0, 90)
        base_date = datetime.utcnow() - timedelta(days=days_ago)
        
        # Select day of week based on weights
        target_weekday = self._select_from_weights(self._day_weights)
        current_weekday = base_date.weekday()
        days_diff = (target_weekday - current_weekday) % 7
        session_date = base_date + timedelta(days=days_diff)
        
        # Select hour based on weights
        hour = self._select_from_weights(self._hour_weights)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        
        return session_date.replace(hour=hour, minute=minute, second=second, microsecond=0)
    
    def _select_from_weights(self, weights: Dict[int, float]) -> int:
        """Select a key based on normalized weights."""
        keys = list(weights.keys())
        probs = [weights[k] for k in keys]
        return int(np.random.choice(keys, p=probs))
    
    def _select_device_for_time(self, hour: int) -> str:
        """Select device type based on time of day."""
        if 6 <= hour < 12:
            period = "morning"
        elif 12 <= hour < 18:
            period = "afternoon"
        elif 18 <= hour < 24:
            period = "evening"
        else:
            period = "night"
        
        devices = list(DEVICE_PREFERENCES[period].keys())
        probs = list(DEVICE_PREFERENCES[period].values())
        return np.random.choice(devices, p=probs)
    
    def _get_next_state(self, current_state: str, user: UserProfile) -> str:
        """
        Determine next state in the funnel based on probabilities.
        
        Adjusts probabilities based on user's spending style and price sensitivity.
        """
        if current_state not in FUNNEL_PROBABILITIES:
            return "abandon"
        
        probs = FUNNEL_PROBABILITIES[current_state].copy()
        
        # Adjust based on user characteristics
        if user.financial_context.spending_style == "impulsive":
            # More likely to purchase, less likely to abandon
            if "purchase" in probs:
                probs["purchase"] *= 1.5
            if "add_to_cart" in probs:
                probs["add_to_cart"] *= 1.3
            probs["abandon"] *= 0.7
        
        elif user.financial_context.spending_style == "frugal":
            # More likely to abandon, more research
            if "purchase" in probs:
                probs["purchase"] *= 0.7
            probs["abandon"] *= 1.3
            if "view" in probs:
                probs["view"] *= 1.2
        
        # Price sensitive users more likely to wishlist
        if user.preferences.price_sensitivity > 0.7:
            if "wishlist" in probs:
                probs["wishlist"] *= 1.5
        
        # Normalize
        total = sum(probs.values())
        probs = {k: v / total for k, v in probs.items()}
        
        states = list(probs.keys())
        probabilities = [probs[s] for s in states]
        
        return np.random.choice(states, p=probabilities)
    
    def _create_financial_snapshot(
        self, 
        user: UserProfile, 
        cart: List[str]
    ) -> FinancialSnapshot:
        """Create a financial snapshot at current point in session."""
        cart_total = sum(
            self._product_map[pid].price 
            for pid in cart 
            if pid in self._product_map
        )
        
        budget_remaining = max(0, user.financial_context.budget_max - cart_total)
        
        return FinancialSnapshot(
            budget_remaining=round(budget_remaining, 2),
            monthly_spent=round(random.uniform(0, user.financial_context.monthly_discretionary * 0.8), 2),
            affordability_for_item=None,  # Set per-item
            payment_method_available=user.payment_methods,
            installment_eligible=user.financial_context.prefers_installments
        )
    
    def _generate_search_interaction(
        self,
        user: UserProfile,
        session_id: str,
        timestamp: datetime,
        device: str,
        interaction_number: int,
        time_in_session: int,
        financial_snapshot: FinancialSnapshot
    ) -> UserInteraction:
        """Generate a search interaction."""
        query, query_type = self._generate_search_query(user)
        
        # Detect category from query (simplified)
        detected_category = None
        for category in CATEGORY_HIERARCHY.keys():
            if category.lower() in query.lower():
                detected_category = category
                break
        
        # Results count
        total_results = random.randint(5, 500)
        results_returned = min(20, total_results)
        
        search_context = SearchContext(
            query=query,
            query_type=query_type,
            detected_category=detected_category,
            total_results=total_results,
            results_returned=results_returned
        )
        
        return UserInteraction(
            user_id=user.id,
            session_id=session_id,
            interaction_type="search",
            timestamp=timestamp,
            search_context=search_context,
            financial_snapshot=financial_snapshot,
            device_type=device,
            session_interaction_number=interaction_number,
            time_since_session_start_seconds=time_in_session
        )
    
    def _generate_search_query(self, user: UserProfile) -> Tuple[str, str]:
        """Generate a realistic search query based on user profile."""
        # Choose query type based on user characteristics
        if user.preferences.deal_seeker and random.random() < 0.3:
            query_type = "product_search"  # budget_focused maps to product_search
        elif user.preferences.quality_preference > 0.7 and random.random() < 0.3:
            query_type = "product_search"  # quality_focused maps to product_search
        elif random.random() < 0.25:
            query_type = "vague_intent"
        elif random.random() < 0.15:
            query_type = "category_browse"
        else:
            query_type = "product_search"  # specific_product maps to product_search
        
        # Get template - map to config template keys
        template_key = query_type
        if user.preferences.deal_seeker and random.random() < 0.3:
            template_key = "budget_focused"
        elif user.preferences.quality_preference > 0.7 and random.random() < 0.3:
            template_key = "quality_focused"
        elif query_type == "product_search":
            template_key = "specific_product"
        templates = SEARCH_QUERY_TEMPLATES.get(template_key, SEARCH_QUERY_TEMPLATES["specific_product"])
        template = random.choice(templates)
        
        # Choose category based on user preferences
        categories = list(user.preferences.category_affinity.items())
        categories.sort(key=lambda x: x[1], reverse=True)
        
        # Weighted random selection favoring higher affinity
        weights = [c[1] for c in categories]
        total = sum(weights)
        weights = [w / total for w in weights]
        category = np.random.choice([c[0] for c in categories], p=weights)
        
        subcategory = random.choice(CATEGORY_HIERARCHY[category]["subcategories"])
        
        # Get brand from category
        if category in BRANDS_BY_CATEGORY:
            all_brands = (
                BRANDS_BY_CATEGORY[category]["premium"] +
                BRANDS_BY_CATEGORY[category]["mid_tier"] +
                BRANDS_BY_CATEGORY[category]["budget"]
            )
            brand = random.choice(all_brands)
            brand2 = random.choice([b for b in all_brands if b != brand])
        else:
            brand = "Generic"
            brand2 = "Store Brand"
        
        # Generate product type from subcategory
        product_type = subcategory.lower().rstrip('s')  # Simple singularize
        
        # Price based on user budget
        price = int(random.uniform(
            user.financial_context.budget_min,
            user.financial_context.budget_max
        ))
        
        # Fill template
        fill_data = {
            "brand": brand,
            "brand1": brand,
            "brand2": brand2,
            "product_type": product_type,
            "category": category,
            "subcategory": subcategory,
            "price": price,
            "color": random.choice(["black", "white", "blue", "red", "silver", "gray"]),
            "size": random.choice(["small", "medium", "large"]),
            "model": f"{brand[0]}{random.randint(100, 999)}",
            "feature": random.choice(SEARCH_FILL_INS["feature"]),
            "recipient": random.choice(SEARCH_FILL_INS["recipient"]),
            "occasion": random.choice(SEARCH_FILL_INS["occasion"]),
            "generic_item": random.choice(SEARCH_FILL_INS["generic_item"]),
            "adjective": random.choice(SEARCH_FILL_INS["adjective"]),
            "purpose": random.choice(SEARCH_FILL_INS["purpose"]),
            "material": random.choice(["leather", "cotton", "metal", "plastic", "wood"])
        }
        
        try:
            query = template.format(**fill_data)
        except KeyError:
            query = f"{product_type} {brand}"
        
        return query, query_type
    
    def _select_product_to_view(
        self, 
        user: UserProfile, 
        already_viewed: List[str]
    ) -> Optional[Product]:
        """Select a product for the user to view."""
        # Get candidates based on user preferences
        candidates = []
        
        for category, affinity in user.preferences.category_affinity.items():
            if category in self._products_by_category and affinity > 0.3:
                category_products = self._products_by_category[category]
                
                # Filter by price (user is more likely to view affordable products)
                affordable = [
                    p for p in category_products 
                    if p.price <= user.financial_context.budget_max * 1.5
                ]
                
                # Weight by affinity
                for product in affordable:
                    if product.id not in already_viewed:
                        # Add multiple times based on affinity
                        times = int(affinity * 5) + 1
                        candidates.extend([product] * times)
        
        if not candidates:
            # Fall back to any affordable product
            affordable = [
                p for p in self.products 
                if p.price <= user.financial_context.budget_max * 2
                and p.id not in already_viewed
            ]
            candidates = affordable
        
        if candidates:
            return random.choice(candidates)
        
        return None
    
    def _generate_view_interaction(
        self,
        user: UserProfile,
        product: Product,
        session_id: str,
        timestamp: datetime,
        device: str,
        interaction_number: int,
        time_in_session: int,
        financial_snapshot: FinancialSnapshot
    ) -> UserInteraction:
        """Generate a product view interaction."""
        # Time spent viewing (interested users spend more time)
        category_interest = user.preferences.category_affinity.get(product.category, 0.5)
        base_time = 30 + int(category_interest * 60)
        time_spent = max(5, int(np.random.normal(base_time, 20)))
        
        # Scroll depth
        scroll_depth = min(1.0, np.random.beta(2, 1.5))
        
        # Review viewing based on user preference
        viewed_reviews = random.random() < user.preferences.reviews_importance
        
        view_context = ViewContext(
            product_id=product.id,
            product_title=product.title,
            product_price=product.price,
            product_category=product.category,
            time_spent_seconds=time_spent,
            scroll_depth=round(scroll_depth, 2),
            viewed_reviews=viewed_reviews,
            viewed_similar_products=random.random() < 0.3,
            source="search"
        )
        
        # Update financial snapshot with affordability for this item
        affordability = min(1.0, financial_snapshot.budget_remaining / product.price) if product.price > 0 else 1.0
        financial_snapshot.affordability_for_item = round(affordability, 3)
        
        return UserInteraction(
            user_id=user.id,
            session_id=session_id,
            interaction_type="view",
            timestamp=timestamp,
            view_context=view_context,
            financial_snapshot=financial_snapshot,
            device_type=device,
            session_interaction_number=interaction_number,
            time_since_session_start_seconds=time_in_session
        )
    
    def _generate_cart_interaction(
        self,
        user: UserProfile,
        product: Product,
        session_id: str,
        timestamp: datetime,
        device: str,
        interaction_number: int,
        time_in_session: int,
        financial_snapshot: FinancialSnapshot,
        action: str,
        cart: List[str]
    ) -> UserInteraction:
        """Generate an add/remove from cart interaction."""
        cart_total = sum(
            self._product_map[pid].price 
            for pid in cart 
            if pid in self._product_map
        )
        
        cart_context = CartContext(
            product_id=product.id,
            product_title=product.title,
            product_price=product.price,
            product_category=product.category,
            quantity=1,
            cart_total_before=cart_total - product.price if action == "add" else cart_total + product.price,
            cart_total_after=cart_total,
            cart_item_count=len(cart),
            removal_reason="changed_mind" if action == "remove" else None
        )
        
        interaction_type = "add_to_cart" if action == "add" else "remove_from_cart"
        
        return UserInteraction(
            user_id=user.id,
            session_id=session_id,
            interaction_type=interaction_type,
            timestamp=timestamp,
            cart_context=cart_context,
            financial_snapshot=financial_snapshot,
            device_type=device,
            session_interaction_number=interaction_number,
            time_since_session_start_seconds=time_in_session
        )
    
    def _generate_wishlist_interaction(
        self,
        user: UserProfile,
        product: Product,
        session_id: str,
        timestamp: datetime,
        device: str,
        interaction_number: int,
        time_in_session: int,
        financial_snapshot: FinancialSnapshot
    ) -> UserInteraction:
        """Generate a wishlist interaction."""
        # Price alert more likely for price-sensitive users
        price_alert = random.random() < user.preferences.price_sensitivity
        target_price = None
        if price_alert:
            # Target price is usually 10-30% below current price
            discount = random.uniform(0.10, 0.30)
            target_price = round(product.price * (1 - discount), 2)
        
        wishlist_context = WishlistContext(
            product_id=product.id,
            product_title=product.title,
            product_price=product.price,
            product_category=product.category,
            action="add",
            wishlist_size_after=random.randint(1, 20),
            price_alert_set=price_alert,
            target_price=target_price
        )
        
        return UserInteraction(
            user_id=user.id,
            session_id=session_id,
            interaction_type="wishlist",
            timestamp=timestamp,
            wishlist_context=wishlist_context,
            financial_snapshot=financial_snapshot,
            device_type=device,
            session_interaction_number=interaction_number,
            time_since_session_start_seconds=time_in_session
        )
    
    def _generate_purchase_interaction(
        self,
        user: UserProfile,
        cart: List[str],
        session_id: str,
        timestamp: datetime,
        device: str,
        interaction_number: int,
        time_in_session: int,
        financial_snapshot: FinancialSnapshot
    ) -> UserInteraction:
        """Generate a purchase interaction."""
        products_data = []
        subtotal = 0
        
        for product_id in cart:
            product = self._product_map.get(product_id)
            if product:
                products_data.append({
                    "product_id": product.id,
                    "title": product.title,
                    "price": product.price,
                    "category": product.category
                })
                subtotal += product.price
        
        # Calculate totals
        discount = 0
        if user.preferences.uses_coupons and random.random() < 0.3:
            discount = subtotal * random.uniform(0.05, 0.15)
        
        tax = (subtotal - discount) * 0.08  # 8% tax
        shipping = 0 if subtotal > 50 else 5.99
        total = subtotal - discount + tax + shipping
        
        # Payment method
        payment_method = user.primary_payment_method
        
        # Installments for larger purchases by eligible users
        use_installments = False
        installment_plan = None
        if user.financial_context.prefers_installments and total > 200:
            use_installments = random.random() < 0.7
            if use_installments:
                if total < 500:
                    installment_plan = "3_months"
                elif total < 1000:
                    installment_plan = random.choice(["3_months", "6_months"])
                else:
                    installment_plan = random.choice(["6_months", "12_months"])
        
        purchase_context = PurchaseContext(
            products=products_data,
            subtotal=round(subtotal, 2),
            discount_amount=round(discount, 2),
            tax_amount=round(tax, 2),
            shipping_amount=round(shipping, 2),
            total_amount=round(total, 2),
            payment_method=payment_method,
            used_installments=use_installments,
            installment_plan=installment_plan,
            coupon_code="SAVE10" if discount > 0 else None
        )
        
        return UserInteraction(
            user_id=user.id,
            session_id=session_id,
            interaction_type="purchase",
            timestamp=timestamp,
            purchase_context=purchase_context,
            financial_snapshot=financial_snapshot,
            device_type=device,
            session_interaction_number=interaction_number,
            time_since_session_start_seconds=time_in_session,
            led_to_conversion=True
        )
    
    def _add_query_embeddings(self, interactions: List[UserInteraction]) -> None:
        """Add embeddings to search interactions."""
        # Collect all search queries
        search_interactions = [i for i in interactions if i.search_context]
        
        if not search_interactions:
            return
        
        texts = [i.search_context.query for i in search_interactions]
        embeddings = self.generate_embeddings(texts)
        
        for interaction, embedding in zip(search_interactions, embeddings):
            interaction.query_embedding = embedding
    
    def validate(self, interactions: List[UserInteraction]) -> bool:
        """
        Validate generated interactions.
        
        Args:
            interactions: List of UserInteraction objects.
            
        Returns:
            True if all validations pass.
        """
        logger.info("Validating generated interactions...")
        
        errors = []
        warnings = []
        
        # Check count - warn if significantly below target, but don't fail
        if len(interactions) < self.config.num_interactions * 0.5:
            errors.append(
                f"Expected ~{self.config.num_interactions} interactions, got {len(interactions)}"
            )
        elif len(interactions) < self.config.num_interactions * 0.9:
            warnings.append(
                f"Generated {len(interactions)} interactions (target: {self.config.num_interactions})"
            )
        
        # Check for unique IDs
        ids = [i.id for i in interactions]
        if len(ids) != len(set(ids)):
            errors.append("Duplicate interaction IDs found")
        
        # Validate references
        invalid_users = 0
        invalid_products = 0
        
        for interaction in interactions:
            # User reference
            if interaction.user_id not in self._user_map:
                invalid_users += 1
            
            # Product reference
            product_id = interaction.get_product_id()
            if product_id and product_id not in self._product_map:
                invalid_products += 1
        
        if invalid_users > 0:
            errors.append(f"Found {invalid_users} interactions with invalid user references")
        
        if invalid_products > 0:
            errors.append(f"Found {invalid_products} interactions with invalid product references")
        
        # Check interaction type distribution
        type_counts = {}
        for i in interactions:
            type_counts[i.interaction_type] = type_counts.get(i.interaction_type, 0) + 1
        
        logger.info(f"Interaction type distribution: {type_counts}")
        
        # Check for search embeddings
        if self.config.generate_embeddings:
            searches_without_embedding = sum(
                1 for i in interactions 
                if i.search_context and not i.query_embedding
            )
            if searches_without_embedding > 0:
                warnings.append(f"{searches_without_embedding} searches missing embeddings")
        
        # Report
        for warning in warnings[:5]:
            logger.warning(warning)
        for error in errors[:5]:
            logger.error(error)
        
        if errors:
            logger.error(f"Validation failed with {len(errors)} errors")
            return False
        
        logger.info("Validation passed successfully")
        return True
    
    def get_statistics(self, interactions: List[UserInteraction]) -> Dict[str, Any]:
        """
        Generate statistics about the interactions.
        
        Args:
            interactions: List of UserInteraction objects.
            
        Returns:
            Dictionary of statistics.
        """
        stats = {
            "total_interactions": len(interactions),
            "interaction_types": {},
            "device_types": {},
            "unique_users": len(set(i.user_id for i in interactions)),
            "unique_sessions": len(set(i.session_id for i in interactions)),
            "conversions": sum(1 for i in interactions if i.led_to_conversion),
            "search_queries": []
        }
        
        for i in interactions:
            stats["interaction_types"][i.interaction_type] = \
                stats["interaction_types"].get(i.interaction_type, 0) + 1
            stats["device_types"][i.device_type] = \
                stats["device_types"].get(i.device_type, 0) + 1
        
        # Sample search queries
        searches = [i for i in interactions if i.search_context][:20]
        stats["search_queries"] = [s.search_context.query for s in searches]
        
        # Calculate averages
        stats["avg_interactions_per_session"] = round(
            stats["total_interactions"] / max(1, stats["unique_sessions"]), 2
        )
        
        return stats
