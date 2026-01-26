"""
Review data generator for FinFind.

Generates realistic product reviews with varied sentiment,
ratings, and realistic text that references actual products.
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from faker import Faker
from tqdm import tqdm
import logging
import numpy as np

from .base_generator import BaseGenerator
from ..config import GenerationConfig, REVIEW_TEMPLATES
from ..models.product_models import Product
from ..models.review_models import Review, ReviewAspects

logger = logging.getLogger(__name__)
fake = Faker()
Faker.seed(42)


class ReviewGenerator(BaseGenerator):
    """Generator for product review data."""
    
    def __init__(self, config: Optional[GenerationConfig] = None, 
                 products: Optional[List[Product]] = None):
        """
        Initialize the review generator.
        
        Args:
            config: Generation configuration.
            products: List of products to generate reviews for.
        """
        super().__init__(config)
        self.products = products or []
        self.product_popularity = {}
        self._init_review_data()
    
    def _init_review_data(self) -> None:
        """Initialize review-specific data."""
        # Review duration phrases
        self.durations = [
            "a few days", "a week", "two weeks", "a month", 
            "a few months", "six months", "a year"
        ]
        
        # Feature categories by product category
        self.feature_words = {
            "Electronics": {
                "positive": ["performance", "battery life", "build quality", "display", "sound", "speed", "design", "features"],
                "negative": ["battery", "lag", "heat", "weight", "price", "software", "connectivity"]
            },
            "Fashion": {
                "positive": ["fit", "quality", "color", "comfort", "style", "material", "value"],
                "negative": ["sizing", "color", "stitching", "shrinkage", "fit"]
            },
            "Home & Kitchen": {
                "positive": ["quality", "durability", "design", "functionality", "ease of use", "value"],
                "negative": ["assembly", "durability", "instructions", "quality", "size"]
            },
            "Books & Media": {
                "positive": ["writing", "story", "characters", "pacing", "content", "value"],
                "negative": ["ending", "pacing", "characters", "length", "price"]
            },
            "Sports & Fitness": {
                "positive": ["durability", "comfort", "quality", "grip", "value", "performance"],
                "negative": ["durability", "comfort", "smell", "quality", "instructions"]
            },
            "Beauty & Personal Care": {
                "positive": ["results", "scent", "texture", "packaging", "value", "effectiveness"],
                "negative": ["scent", "irritation", "results", "packaging", "price"]
            }
        }
        
        # Generate fake user IDs for reviews
        self.user_ids = [f"user_{uuid.uuid4()}" for _ in range(self.config.num_users)]
    
    def set_products(self, products: List[Product]) -> None:
        """
        Set the products to generate reviews for.
        
        Args:
            products: List of Product objects.
        """
        self.products = products
        self._calculate_product_popularity()
    
    def _calculate_product_popularity(self) -> None:
        """
        Calculate product popularity weights using Pareto distribution.
        
        This ensures some products get more reviews than others (realistic).
        """
        if not self.products:
            return
        
        n = len(self.products)
        
        # Generate Pareto-distributed weights
        # Top 20% get 60% of reviews
        pareto_alpha = 1.5
        weights = np.random.pareto(pareto_alpha, n)
        weights = weights / weights.sum()  # Normalize
        
        # Assign weights to products
        self.product_popularity = {
            product.id: weight for product, weight in zip(self.products, weights)
        }
    
    def _select_product(self) -> Product:
        """Select a product weighted by popularity."""
        if not self.product_popularity:
            return random.choice(self.products)
        
        product_ids = list(self.product_popularity.keys())
        weights = list(self.product_popularity.values())
        
        selected_id = self.weighted_choice(product_ids, weights)
        
        for product in self.products:
            if product.id == selected_id:
                return product
        
        return random.choice(self.products)
    
    def _select_rating(self) -> int:
        """Select a rating based on configured distribution."""
        return self.weighted_choice([1, 2, 3, 4, 5], self.config.rating_distribution)
    
    def _calculate_sentiment(self, rating: int, text: str) -> Tuple[str, float]:
        """
        Calculate sentiment label and score based on rating and text.
        
        Args:
            rating: Star rating (1-5).
            text: Review text.
            
        Returns:
            Tuple of (sentiment_label, sentiment_score).
        """
        # Get base sentiment range from rating
        sentiment_range = self.config.sentiment_ranges[rating]
        
        # Generate score within range
        base_score = random.uniform(sentiment_range[0], sentiment_range[1])
        
        # Adjust based on text keywords (simple heuristic)
        positive_words = ["love", "amazing", "excellent", "perfect", "great", "best", "fantastic", "wonderful"]
        negative_words = ["terrible", "awful", "horrible", "worst", "hate", "broken", "useless", "waste"]
        
        text_lower = text.lower()
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        # Adjust score slightly based on text
        adjustment = (pos_count - neg_count) * 0.05
        score = max(-1.0, min(1.0, base_score + adjustment))
        
        # Determine label
        if score > 0.2:
            label = "positive"
        elif score < -0.2:
            label = "negative"
        else:
            label = "neutral"
        
        return (label, round(score, 3))
    
    def _generate_review_title(self, rating: int, product: Product) -> str:
        """Generate a review title based on rating."""
        product_type = product.subcategory.lower()
        
        titles_by_rating = {
            5: [
                f"Best {product_type} ever!",
                "Absolutely love it!",
                "Exceeded my expectations",
                "Highly recommend!",
                "Perfect purchase",
                "Five stars - no hesitation",
                "Amazing quality",
                f"The {product_type} I've been looking for"
            ],
            4: [
                "Great product overall",
                "Very satisfied",
                "Good value for money",
                "Solid purchase",
                "Would recommend",
                "Happy with my purchase",
                "Minor issues but still great",
                f"Good {product_type}"
            ],
            3: [
                "It's okay",
                "Average product",
                "Mixed feelings",
                "Gets the job done",
                "Not bad, not great",
                "Room for improvement",
                "Decent for the price",
                "Meets basic expectations"
            ],
            2: [
                "Disappointed",
                "Expected more",
                "Not worth the price",
                "Quality issues",
                "Below expectations",
                "Would not buy again",
                "Several problems",
                "Needs improvement"
            ],
            1: [
                "Terrible product",
                "Complete waste of money",
                "Do not buy",
                "Horrible quality",
                "Major disappointment",
                "Worst purchase ever",
                "Save your money",
                "Defective product"
            ]
        }
        
        return random.choice(titles_by_rating[rating])
    
    def _generate_review_text(self, rating: int, product: Product) -> str:
        """
        Generate realistic review text based on rating and product.
        
        Args:
            rating: Star rating (1-5).
            product: Product being reviewed.
            
        Returns:
            Generated review text.
        """
        templates = REVIEW_TEMPLATES[rating]
        product_type = product.subcategory.lower()
        category = product.category
        
        # Get feature words for this category
        features = self.feature_words.get(category, self.feature_words["Electronics"])
        positive_features = features["positive"]
        negative_features = features["negative"]
        
        # Select features to mention
        feature1 = random.choice(positive_features if rating >= 3 else negative_features)
        feature2 = random.choice(positive_features if rating >= 4 else negative_features)
        
        # Build review from templates
        opener = random.choice(templates["openers"]).format(product_type=product_type)
        body = random.choice(templates["body"]).format(
            feature1=feature1,
            feature2=feature2,
            duration=random.choice(self.durations)
        )
        closer = random.choice(templates["closers"])
        
        # Sometimes add extra details
        extras = []
        if random.random() < 0.4:
            if rating >= 4:
                extras.append(f"The {random.choice(positive_features)} is exactly what I expected.")
            else:
                extras.append(f"I had issues with the {random.choice(negative_features)}.")
        
        if random.random() < 0.3:
            if rating >= 4:
                extras.append(f"Shipping was fast and packaging was secure.")
            elif rating <= 2:
                extras.append(f"Customer service was not helpful when I reported the issue.")
        
        if random.random() < 0.3:
            price_comment = self._generate_price_comment(rating, product.price)
            if price_comment:
                extras.append(price_comment)
        
        # Combine parts
        parts = [opener, body]
        parts.extend(extras)
        parts.append(closer)
        
        text = " ".join(parts)
        
        # Sometimes make reviews longer with more detail
        if random.random() < 0.2:
            text = self._expand_review(text, rating, product)
        
        return text
    
    def _generate_price_comment(self, rating: int, price: float) -> Optional[str]:
        """Generate a comment about the price."""
        if rating >= 4:
            comments = [
                f"Worth every penny of the ${price:.2f}.",
                "Great value for the price.",
                "Excellent quality for what you pay.",
                "Would gladly pay more for this quality."
            ]
        elif rating == 3:
            comments = [
                "Price is fair for what you get.",
                f"At ${price:.2f}, it's okay but not amazing.",
                "You get what you pay for."
            ]
        else:
            comments = [
                f"Not worth ${price:.2f} at all.",
                "Way overpriced for the quality.",
                "Save your money for something better.",
                "Should be half the price."
            ]
        
        return random.choice(comments)
    
    def _expand_review(self, base_text: str, rating: int, product: Product) -> str:
        """Expand a review with more detail."""
        expansions = []
        
        if rating >= 4:
            expansions = [
                f"I've been using the {product.brand} {product.subcategory.lower()} for {random.choice(self.durations)} now and it still performs like new.",
                f"I compared this to other {product.subcategory.lower()}s in this price range and this one clearly stands out.",
                f"My family members were so impressed they ordered one for themselves.",
                f"This is my second purchase from {product.brand} and they never disappoint."
            ]
        elif rating == 3:
            expansions = [
                f"I've used other {product.subcategory.lower()}s before and this one is about average.",
                f"It has some good features but also some drawbacks to consider.",
                "I'm keeping it for now but might look for alternatives later."
            ]
        else:
            expansions = [
                f"I really wanted to like this {product.subcategory.lower()} but it let me down.",
                "I've contacted customer support multiple times with no resolution.",
                f"My previous {product.subcategory.lower()} from a different brand was much better.",
                "Considering returning this if the issues persist."
            ]
        
        return base_text + " " + random.choice(expansions)
    
    def _generate_aspect_ratings(self, rating: int) -> ReviewAspects:
        """Generate aspect-based ratings."""
        def aspect_score(base_rating: int) -> float:
            # Add some variance around the base rating
            variance = random.uniform(-0.5, 0.5)
            score = base_rating + variance
            return round(max(1, min(5, score)), 1)
        
        return ReviewAspects(
            quality=aspect_score(rating),
            value=aspect_score(rating + random.choice([-1, 0, 0, 1])),  # Value can vary more
            shipping=aspect_score(min(5, rating + 1)),  # Shipping usually rated higher
            ease_of_use=aspect_score(rating),
            durability=aspect_score(rating) if random.random() < 0.7 else None
        )
    
    def _generate_helpful_votes(self, text_length: int, rating: int) -> Tuple[int, int]:
        """
        Generate helpful vote counts.
        
        Longer, more extreme reviews tend to get more votes.
        """
        # Base vote count influenced by text length and rating extremity
        extremity = abs(rating - 3)  # 0-2 scale
        length_factor = min(text_length / 200, 2)  # Cap at 2x
        
        base_votes = int(random.expovariate(0.1) * (1 + extremity) * length_factor)
        total_votes = min(base_votes, 500)  # Cap at 500
        
        # Helpful ratio varies (usually positive reviews marked more helpful)
        if rating >= 4:
            helpful_ratio = random.uniform(0.7, 0.95)
        elif rating == 3:
            helpful_ratio = random.uniform(0.4, 0.7)
        else:
            helpful_ratio = random.uniform(0.5, 0.85)  # Negative reviews also helpful as warnings
        
        helpful_votes = int(total_votes * helpful_ratio)
        
        return (helpful_votes, total_votes)
    
    def _generate_timestamp(self) -> datetime:
        """Generate a timestamp within the past 12 months."""
        days_ago = random.randint(1, 365)
        hours_ago = random.randint(0, 23)
        minutes_ago = random.randint(0, 59)
        
        return datetime.utcnow() - timedelta(
            days=days_ago, 
            hours=hours_ago, 
            minutes=minutes_ago
        )
    
    def _generate_review(self, product: Product) -> Review:
        """Generate a complete review for a product."""
        rating = self._select_rating()
        title = self._generate_review_title(rating, product)
        text = self._generate_review_text(rating, product)
        sentiment, sentiment_score = self._calculate_sentiment(rating, text)
        aspects = self._generate_aspect_ratings(rating)
        helpful, total = self._generate_helpful_votes(len(text), rating)
        verified = random.random() < self.config.verified_purchase_prob
        
        review = Review(
            review_id=f"rev_{uuid.uuid4()}",
            product_id=product.id,
            user_id=random.choice(self.user_ids),
            title=title,
            text=text,
            rating=rating,
            sentiment=sentiment,
            sentiment_score=sentiment_score,
            aspects=aspects,
            helpful_votes=helpful,
            total_votes=total,
            verified_purchase=verified,
            created_at=self._generate_timestamp()
        )
        
        return review
    
    def generate(self) -> List[Review]:
        """
        Generate the configured number of reviews.
        
        Returns:
            List of generated Review objects.
        """
        if not self.products:
            raise ValueError("No products set. Call set_products() first or pass products to constructor.")
        
        self._calculate_product_popularity()
        reviews = []
        
        logger.info(f"Generating {self.config.num_reviews} reviews for {len(self.products)} products...")
        
        for _ in tqdm(range(self.config.num_reviews), desc="Generating reviews"):
            product = self._select_product()
            review = self._generate_review(product)
            reviews.append(review)
        
        # Generate embeddings in batch
        if self.config.generate_embeddings:
            texts = [r.get_embedding_text() for r in reviews]
            embeddings = self.generate_embeddings(texts)
            
            for review, embedding in zip(reviews, embeddings):
                review.embedding = embedding
        
        logger.info(f"Generated {len(reviews)} reviews successfully")
        return reviews
    
    def validate(self, reviews: List[Review]) -> bool:
        """
        Validate generated reviews.
        
        Args:
            reviews: List of reviews to validate.
            
        Returns:
            True if all reviews are valid.
        """
        logger.info(f"Validating {len(reviews)} reviews...")
        
        issues = []
        seen_ids = set()
        product_ids = {p.id for p in self.products}
        
        for i, review in enumerate(reviews):
            # Check for duplicate IDs
            if review.review_id in seen_ids:
                issues.append(f"Review {i}: Duplicate ID {review.review_id}")
            seen_ids.add(review.review_id)
            
            # Check product reference
            if review.product_id not in product_ids:
                issues.append(f"Review {i}: Invalid product_id {review.product_id}")
            
            # Check required fields
            if len(review.title) < 5:
                issues.append(f"Review {i}: Title too short")
            if len(review.text) < 20:
                issues.append(f"Review {i}: Text too short")
            if review.rating < 1 or review.rating > 5:
                issues.append(f"Review {i}: Invalid rating {review.rating}")
            
            # Check embedding if expected
            if self.config.generate_embeddings and not review.embedding:
                issues.append(f"Review {i}: Missing embedding")
        
        if issues:
            for issue in issues[:10]:
                logger.warning(issue)
            if len(issues) > 10:
                logger.warning(f"...and {len(issues) - 10} more issues")
            return False
        
        logger.info("All reviews validated successfully")
        return True
    
    def get_review_stats(self, reviews: List[Review]) -> Dict:
        """
        Get statistics about generated reviews.
        
        Args:
            reviews: List of reviews.
            
        Returns:
            Dictionary of statistics.
        """
        if not reviews:
            return {}
        
        ratings = [r.rating for r in reviews]
        sentiments = [r.sentiment for r in reviews]
        verified = [r for r in reviews if r.verified_purchase]
        
        return {
            "total_reviews": len(reviews),
            "average_rating": round(sum(ratings) / len(ratings), 2),
            "rating_distribution": {
                i: ratings.count(i) for i in range(1, 6)
            },
            "sentiment_distribution": {
                s: sentiments.count(s) for s in ["positive", "neutral", "negative"]
            },
            "verified_purchase_count": len(verified),
            "verified_purchase_pct": round(len(verified) / len(reviews) * 100, 1),
            "unique_products": len(set(r.product_id for r in reviews)),
            "unique_users": len(set(r.user_id for r in reviews))
        }


def generate_reviews(products: List[Product],
                     num_reviews: int = 1200,
                     generate_embeddings: bool = True,
                     random_seed: int = 42) -> List[Review]:
    """
    Convenience function to generate reviews.
    
    Args:
        products: List of products to generate reviews for.
        num_reviews: Number of reviews to generate.
        generate_embeddings: Whether to generate embeddings.
        random_seed: Random seed for reproducibility.
        
    Returns:
        List of generated Review objects.
    """
    config = GenerationConfig(
        num_reviews=num_reviews,
        generate_embeddings=generate_embeddings,
        random_seed=random_seed
    )
    
    generator = ReviewGenerator(config, products)
    reviews = generator.generate()
    generator.validate(reviews)
    
    return reviews
