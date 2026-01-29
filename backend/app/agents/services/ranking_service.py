"""
Product Ranking Service for FinFind.

Implements intelligent product ranking combining multiple signals:
- Semantic relevance (from vector similarity)
- Quality signals (rating, review count)
- Popularity indicators
- Personalization (user preferences)
- Financial fit (budget alignment)
- Freshness (recency boost for newer products)

Best Practices Applied:
1. Multi-factor scoring with configurable weights
2. Normalization of scores across different scales
3. User context-aware personalization
4. Diversity preservation (works with MMR)
5. Explainable ranking with score breakdown
"""

import logging
import math
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class RankingStrategy(str, Enum):
    """Available ranking strategies."""
    RELEVANCE = "relevance"           # Pure semantic relevance
    POPULARITY = "popularity"          # Rating + reviews weighted
    BALANCED = "balanced"              # Mix of relevance + quality
    PERSONALIZED = "personalized"      # User-preference weighted
    VALUE = "value"                    # Best bang for buck
    BUDGET_SMART = "budget_smart"      # Financial-first: prioritizes budget fit & affordability


@dataclass
class RankingWeights:
    """Configurable weights for ranking factors."""
    relevance: float = 0.35            # Semantic similarity score
    rating: float = 0.15               # Product rating (0-5)
    popularity: float = 0.10           # Review count / popularity
    price_fit: float = 0.20            # How well price fits budget
    category_match: float = 0.10       # User category preference
    brand_preference: float = 0.05     # User brand preference
    financial_health: float = 0.05     # Impact on user's financial health
    
    @classmethod
    def for_strategy(cls, strategy: RankingStrategy) -> "RankingWeights":
        """Get weights optimized for a specific strategy."""
        if strategy == RankingStrategy.RELEVANCE:
            return cls(relevance=0.70, rating=0.15, popularity=0.10, 
                      price_fit=0.05, category_match=0.0, brand_preference=0.0, financial_health=0.0)
        elif strategy == RankingStrategy.POPULARITY:
            return cls(relevance=0.25, rating=0.35, popularity=0.30,
                      price_fit=0.05, category_match=0.05, brand_preference=0.0, financial_health=0.0)
        elif strategy == RankingStrategy.PERSONALIZED:
            return cls(relevance=0.30, rating=0.15, popularity=0.10,
                      price_fit=0.15, category_match=0.15, brand_preference=0.10, financial_health=0.05)
        elif strategy == RankingStrategy.VALUE:
            return cls(relevance=0.25, rating=0.25, popularity=0.10,
                      price_fit=0.30, category_match=0.05, brand_preference=0.0, financial_health=0.05)
        elif strategy == RankingStrategy.BUDGET_SMART:
            # Financial-first ranking for FinCommerce
            # Heavily weights budget fit, affordability, and financial impact
            return cls(relevance=0.20, rating=0.10, popularity=0.05,
                      price_fit=0.35, category_match=0.10, brand_preference=0.0, financial_health=0.20)
        else:  # BALANCED
            return cls()


@dataclass
class UserContext:
    """User context for personalized ranking with financial profile."""
    user_id: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    monthly_income: Optional[float] = None
    monthly_budget: Optional[float] = None  # Total monthly shopping budget
    savings_goal: Optional[float] = None
    preferred_categories: List[str] = field(default_factory=list)
    preferred_brands: List[str] = field(default_factory=list)
    purchase_history_categories: List[str] = field(default_factory=list)
    price_sensitivity: float = 0.5  # 0 = not sensitive, 1 = very sensitive
    risk_tolerance: str = "moderate"  # conservative, moderate, aggressive
    preferred_payment_methods: List[str] = field(default_factory=list)


@dataclass
class RankingResult:
    """Result of ranking a product."""
    product: Dict[str, Any]
    final_score: float
    score_breakdown: Dict[str, float]
    rank: int = 0
    ranking_explanation: str = ""


class ProductRankingService:
    """
    Service for ranking products based on multiple signals.
    
    Combines semantic relevance with quality signals and user preferences
    to produce optimally ranked product lists.
    """
    
    def __init__(
        self,
        strategy: RankingStrategy = RankingStrategy.BALANCED,
        weights: Optional[RankingWeights] = None
    ):
        """
        Initialize the ranking service.
        
        Args:
            strategy: Ranking strategy to use
            weights: Custom weights (overrides strategy defaults)
        """
        self.strategy = strategy
        self.weights = weights or RankingWeights.for_strategy(strategy)
        
        # Statistics for normalization (can be updated with actual data)
        self._max_review_count = 1000  # Approximate max reviews for normalization
        self._max_price = 5000         # Approximate max price for normalization
    
    def rank_products(
        self,
        products: List[Dict[str, Any]],
        user_context: Optional[UserContext] = None,
        query: Optional[str] = None
    ) -> List[RankingResult]:
        """
        Rank a list of products based on multiple signals.
        
        Args:
            products: List of products with payload data
            user_context: Optional user context for personalization
            query: Original search query (for explanation)
            
        Returns:
            List of RankingResult sorted by final_score descending
        """
        if not products:
            return []
        
        user_context = user_context or UserContext()
        ranked_results = []
        
        for product in products:
            result = self._score_product(product, user_context)
            ranked_results.append(result)
        
        # Sort by final score descending
        ranked_results.sort(key=lambda x: x.final_score, reverse=True)
        
        # Assign ranks
        for i, result in enumerate(ranked_results):
            result.rank = i + 1
            result.ranking_explanation = self._generate_explanation(result, query)
        
        return ranked_results
    
    def _score_product(
        self,
        product: Dict[str, Any],
        user_context: UserContext
    ) -> RankingResult:
        """Calculate the final score for a product with financial awareness."""
        # Extract data - handle nested payload structure
        payload = product.get("payload", product)
        if isinstance(payload, dict) and "payload" in payload:
            payload = payload["payload"]
        
        # 1. Relevance Score (from vector similarity, already 0-1)
        relevance_score = product.get("score", product.get("relevance_score", 0.5))
        
        # 2. Rating Score (normalize 0-5 to 0-1)
        rating = payload.get("rating_avg", payload.get("rating", 3.5))
        rating_score = min(1.0, rating / 5.0) if rating else 0.5
        
        # 3. Popularity Score (based on review count, log-normalized)
        review_count = payload.get("review_count", payload.get("reviews_count", 10))
        popularity_score = self._normalize_review_count(review_count)
        
        # 4. Price Fit Score (how well price aligns with user budget)
        price = payload.get("price", 0)
        price_fit_score = self._calculate_price_fit(price, user_context)
        
        # 5. Category Match Score
        category = payload.get("category", "")
        category_score = self._calculate_category_match(category, user_context)
        
        # 6. Brand Preference Score
        brand = payload.get("brand", "")
        brand_score = self._calculate_brand_match(brand, user_context)
        
        # 7. Financial Health Score (impact on user's financial goals)
        financial_health_score = self._calculate_financial_health(price, user_context)
        
        # Calculate weighted final score
        score_breakdown = {
            "relevance": relevance_score * self.weights.relevance,
            "rating": rating_score * self.weights.rating,
            "popularity": popularity_score * self.weights.popularity,
            "price_fit": price_fit_score * self.weights.price_fit,
            "category_match": category_score * self.weights.category_match,
            "brand_preference": brand_score * self.weights.brand_preference,
            "financial_health": financial_health_score * self.weights.financial_health
        }
        
        final_score = sum(score_breakdown.values())
        
        # Add affordability indicators for transparency
        affordability_info = self._get_affordability_info(price, user_context)
        
        # Add the scores to product for transparency
        product_with_scores = {
            **product,
            "ranking_score": round(final_score, 4),
            "score_breakdown": {k: round(v, 4) for k, v in score_breakdown.items()},
            "affordability": affordability_info
        }
        
        return RankingResult(
            product=product_with_scores,
            final_score=final_score,
            score_breakdown=score_breakdown
        )
    
    def _normalize_review_count(self, count: int) -> float:
        """Normalize review count using logarithmic scaling."""
        if count <= 0:
            return 0.1  # Small base score for products without reviews
        
        # Log normalization: log(count+1) / log(max+1)
        normalized = math.log(count + 1) / math.log(self._max_review_count + 1)
        return min(1.0, normalized)
    
    def _calculate_price_fit(
        self,
        price: float,
        user_context: UserContext
    ) -> float:
        """
        Calculate how well the price fits user's budget.
        
        Returns higher score for prices:
        - Within budget range: 1.0
        - Below budget: 0.8-1.0 (not too cheap is good)
        - Above budget: decays based on how much over
        """
        if not price:
            return 0.5
        
        budget_max = user_context.budget_max or self._max_price
        budget_min = user_context.budget_min or 0
        
        if budget_min <= price <= budget_max:
            # Within budget - score based on value position
            # Prefer items that use more of the budget (better quality assumption)
            range_size = budget_max - budget_min
            if range_size > 0:
                position = (price - budget_min) / range_size
                # Sweet spot is around 60-80% of budget
                return 0.8 + 0.2 * (1 - abs(position - 0.7) / 0.7)
            return 1.0
        
        elif price < budget_min:
            # Below budget - might be too cheap
            return 0.6 + 0.4 * (price / budget_min)
        
        else:
            # Above budget - decay based on overage
            overage_ratio = (price - budget_max) / budget_max
            # Exponential decay
            return max(0.1, 1.0 - overage_ratio * user_context.price_sensitivity * 2)
    
    def _calculate_category_match(
        self,
        category: str,
        user_context: UserContext
    ) -> float:
        """Calculate category preference match score."""
        if not category:
            return 0.5
        
        category_lower = category.lower()
        
        # Check direct preference match
        for pref in user_context.preferred_categories:
            if pref.lower() in category_lower or category_lower in pref.lower():
                return 1.0
        
        # Check purchase history match
        for hist_cat in user_context.purchase_history_categories:
            if hist_cat.lower() in category_lower or category_lower in hist_cat.lower():
                return 0.8
        
        return 0.5  # Neutral for non-matched categories
    
    def _calculate_brand_match(
        self,
        brand: str,
        user_context: UserContext
    ) -> float:
        """Calculate brand preference match score."""
        if not brand:
            return 0.5
        
        brand_lower = brand.lower()
        
        for pref in user_context.preferred_brands:
            if pref.lower() == brand_lower:
                return 1.0
        
        return 0.5  # Neutral for non-matched brands
    
    def _calculate_financial_health(
        self,
        price: float,
        user_context: UserContext
    ) -> float:
        """
        Calculate how this purchase impacts user's financial health.
        
        Considers:
        - Monthly budget impact
        - Savings goal impact
        - Risk tolerance alignment
        - Price as % of monthly income
        """
        if not price:
            return 0.5
        
        scores = []
        
        # 1. Monthly budget impact (if available)
        if user_context.monthly_budget:
            budget_percentage = (price / user_context.monthly_budget) * 100
            if budget_percentage <= 10:
                scores.append(1.0)  # Excellent - minimal budget impact
            elif budget_percentage <= 20:
                scores.append(0.9)  # Great - comfortable purchase
            elif budget_percentage <= 35:
                scores.append(0.7)  # Good - reasonable purchase
            elif budget_percentage <= 50:
                scores.append(0.5)  # Moderate - significant but manageable
            elif budget_percentage <= 75:
                scores.append(0.3)  # Caution - major purchase
            else:
                scores.append(0.1)  # Warning - exceeds budget significantly
        
        # 2. Monthly income impact (if available)
        if user_context.monthly_income:
            income_percentage = (price / user_context.monthly_income) * 100
            if income_percentage <= 5:
                scores.append(1.0)  # Negligible impact
            elif income_percentage <= 15:
                scores.append(0.8)  # Minor impact
            elif income_percentage <= 30:
                scores.append(0.5)  # Moderate impact
            elif income_percentage <= 50:
                scores.append(0.3)  # Major impact
            else:
                scores.append(0.1)  # Severe impact
        
        # 3. Savings goal alignment (if available)
        if user_context.savings_goal:
            # Lower price = better for savings
            savings_friendly = max(0, 1 - (price / user_context.savings_goal))
            scores.append(savings_friendly * 0.8 + 0.2)  # Minimum 0.2
        
        # 4. Risk tolerance adjustment
        risk_multipliers = {
            "conservative": 1.2,  # Prefer more affordable options
            "moderate": 1.0,
            "aggressive": 0.8    # More comfortable with larger purchases
        }
        multiplier = risk_multipliers.get(user_context.risk_tolerance, 1.0)
        
        if scores:
            base_score = sum(scores) / len(scores)
            return min(1.0, base_score * multiplier)
        
        # Default: use budget_max as reference
        if user_context.budget_max:
            ratio = price / user_context.budget_max
            if ratio <= 0.5:
                return 0.9
            elif ratio <= 1.0:
                return 0.7
            else:
                return max(0.1, 1.0 - ratio * 0.5)
        
        return 0.5
    
    def _get_affordability_info(
        self,
        price: float,
        user_context: UserContext
    ) -> Dict[str, Any]:
        """Generate affordability information for the product."""
        info = {
            "is_affordable": True,
            "budget_percentage": None,
            "monthly_income_percentage": None,
            "recommendation": "Within your budget"
        }
        
        if not price:
            return info
        
        # Calculate budget percentage
        if user_context.monthly_budget:
            budget_pct = (price / user_context.monthly_budget) * 100
            info["budget_percentage"] = round(budget_pct, 1)
            
            if budget_pct <= 20:
                info["recommendation"] = "Fits comfortably within your budget"
            elif budget_pct <= 40:
                info["recommendation"] = "Affordable - consider your priorities"
            elif budget_pct <= 60:
                info["is_affordable"] = False
                info["recommendation"] = "Significant purchase - plan carefully"
            else:
                info["is_affordable"] = False
                info["recommendation"] = "May strain your budget - consider alternatives"
        
        # Calculate income percentage
        if user_context.monthly_income:
            income_pct = (price / user_context.monthly_income) * 100
            info["monthly_income_percentage"] = round(income_pct, 1)
        
        # Check against savings goal
        if user_context.savings_goal and price > user_context.savings_goal * 0.5:
            info["savings_warning"] = True
            info["recommendation"] += " - may impact your savings goal"
        
        return info
    
    def _generate_explanation(
        self,
        result: RankingResult,
        query: Optional[str] = None
    ) -> str:
        """Generate human-readable ranking explanation."""
        breakdown = result.score_breakdown
        explanations = []
        
        # Identify top contributing factors
        sorted_factors = sorted(
            breakdown.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        factor_descriptions = {
            "relevance": "highly relevant to your search",
            "rating": "excellent customer ratings",
            "popularity": "popular with other shoppers",
            "price_fit": "fits your budget well",
            "financial_health": "good for your financial health",
            "category_match": "matches your preferred categories",
            "brand_preference": "from a brand you like"
        }
        
        # Add top 2-3 factors
        for factor, score in sorted_factors[:3]:
            if score > 0.05:  # Only mention significant factors
                explanations.append(factor_descriptions.get(factor, factor))
        
        if explanations:
            return "Ranked highly because: " + ", ".join(explanations)
        return "Matched your search criteria"
    
    def rerank_with_diversity(
        self,
        products: List[Dict[str, Any]],
        user_context: Optional[UserContext] = None,
        diversity_factor: float = 0.3,
        query: Optional[str] = None
    ) -> List[RankingResult]:
        """
        Rank products while maintaining diversity.
        
        Uses a greedy selection approach that balances ranking score
        with diversity from already selected items.
        
        Args:
            products: Products to rank
            user_context: User context for personalization
            diversity_factor: 0-1, higher = more diverse results
            query: Original search query
            
        Returns:
            Ranked and diversified product list
        """
        if not products:
            return []
        
        if diversity_factor <= 0:
            # No diversity, just rank
            return self.rank_products(products, user_context, query)
        
        # First, score all products
        user_context = user_context or UserContext()
        scored_products = [
            self._score_product(p, user_context) 
            for p in products
        ]
        
        # Greedy selection with diversity
        selected: List[RankingResult] = []
        remaining = scored_products.copy()
        
        while remaining and len(selected) < len(products):
            best_idx = 0
            best_combined_score = -1
            
            for i, candidate in enumerate(remaining):
                # Base score
                base_score = candidate.final_score
                
                # Diversity penalty
                diversity_penalty = 0
                if selected:
                    # Calculate similarity to already selected items
                    max_similarity = max(
                        self._product_similarity(candidate.product, s.product)
                        for s in selected
                    )
                    diversity_penalty = max_similarity * diversity_factor
                
                combined_score = base_score - diversity_penalty
                
                if combined_score > best_combined_score:
                    best_combined_score = combined_score
                    best_idx = i
            
            selected.append(remaining.pop(best_idx))
        
        # Assign final ranks
        for i, result in enumerate(selected):
            result.rank = i + 1
            result.ranking_explanation = self._generate_explanation(result, query)
        
        return selected
    
    def _product_similarity(
        self,
        product1: Dict[str, Any],
        product2: Dict[str, Any]
    ) -> float:
        """Calculate similarity between two products for diversity calculation."""
        payload1 = product1.get("payload", product1)
        payload2 = product2.get("payload", product2)
        
        if isinstance(payload1, dict) and "payload" in payload1:
            payload1 = payload1["payload"]
        if isinstance(payload2, dict) and "payload" in payload2:
            payload2 = payload2["payload"]
        
        similarity = 0.0
        factors = 0
        
        # Category similarity
        cat1 = payload1.get("category", "").lower()
        cat2 = payload2.get("category", "").lower()
        if cat1 and cat2:
            similarity += 1.0 if cat1 == cat2 else 0.0
            factors += 1
        
        # Brand similarity
        brand1 = payload1.get("brand", "").lower()
        brand2 = payload2.get("brand", "").lower()
        if brand1 and brand2:
            similarity += 1.0 if brand1 == brand2 else 0.0
            factors += 1
        
        # Price similarity (within 20% = similar)
        price1 = payload1.get("price", 0)
        price2 = payload2.get("price", 0)
        if price1 > 0 and price2 > 0:
            price_ratio = min(price1, price2) / max(price1, price2)
            similarity += price_ratio
            factors += 1
        
        return similarity / max(factors, 1)


# Convenience function for quick ranking
def rank_search_results(
    products: List[Dict[str, Any]],
    strategy: RankingStrategy = RankingStrategy.BALANCED,
    user_context: Optional[Dict[str, Any]] = None,
    diversity_factor: float = 0.3,
    query: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Convenience function to rank search results.
    
    Args:
        products: List of products from search
        strategy: Ranking strategy
        user_context: User context dict with budget, preferences etc.
        diversity_factor: Diversity factor for MMR-like behavior
        query: Original search query
        
    Returns:
        List of products sorted by ranking score with score information added
    """
    service = ProductRankingService(strategy=strategy)
    
    # Convert dict to UserContext if provided
    ctx = None
    if user_context:
        ctx = UserContext(
            user_id=user_context.get("user_id"),
            budget_min=user_context.get("budget_min"),
            budget_max=user_context.get("budget_max"),
            preferred_categories=user_context.get("preferred_categories", []),
            preferred_brands=user_context.get("preferred_brands", []),
            price_sensitivity=user_context.get("price_sensitivity", 0.5)
        )
    
    if diversity_factor > 0:
        results = service.rerank_with_diversity(
            products, ctx, diversity_factor, query
        )
    else:
        results = service.rank_products(products, ctx, query)
    
    # Return just the products with ranking info added
    return [r.product for r in results]
