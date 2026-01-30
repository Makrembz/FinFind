"""
Qdrant Data Verification for FinFind.

Verifies that all data was uploaded correctly and runs
test searches to validate the collections are working.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class VerificationConfig:
    """Configuration for verification."""
    
    # Qdrant connection
    qdrant_url: str = field(default_factory=lambda: os.getenv("QDRANT_URL", ""))
    qdrant_api_key: str = field(default_factory=lambda: os.getenv("QDRANT_API_KEY", ""))
    
    # Collection names
    products_collection: str = field(
        default_factory=lambda: os.getenv("QDRANT_PRODUCTS_COLLECTION", "products")
    )
    user_profiles_collection: str = field(
        default_factory=lambda: os.getenv("QDRANT_USER_PROFILES_COLLECTION", "user_profiles")
    )
    reviews_collection: str = field(
        default_factory=lambda: os.getenv("QDRANT_REVIEWS_COLLECTION", "reviews")
    )
    interactions_collection: str = field(
        default_factory=lambda: os.getenv("QDRANT_INTERACTIONS_COLLECTION", "user_interactions")
    )
    
    # Vector dimension
    text_embedding_dim: int = 384
    
    # Expected counts (from generation)
    expected_products: int = 500
    expected_users: int = 100
    expected_reviews: int = 1200
    expected_interactions: int = 2000
    
    # Input directory for comparison
    input_dir: Path = field(default_factory=lambda: Path("output"))


@dataclass
class VerificationResult:
    """Result of a verification check."""
    
    name: str
    passed: bool
    message: str
    details: Optional[Dict] = None
    
    def __str__(self):
        status = "✓ PASS" if self.passed else "✗ FAIL"
        return f"{status}: {self.name} - {self.message}"


class QdrantVerifier:
    """Verifier for Qdrant collections."""
    
    def __init__(self, config: Optional[VerificationConfig] = None):
        """
        Initialize the verifier.
        
        Args:
            config: Verification configuration.
        """
        self.config = config or VerificationConfig()
        self._client = None
        self._embedding_model = None
        self.results: List[VerificationResult] = []
    
    def _get_client(self):
        """Get or create Qdrant client."""
        if self._client is None:
            from qdrant_client import QdrantClient
            
            self._client = QdrantClient(
                url=self.config.qdrant_url,
                api_key=self.config.qdrant_api_key,
                timeout=30
            )
        return self._client
    
    def _get_embedding_model(self):
        """Get or create embedding model for test queries."""
        if self._embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedding_model = SentenceTransformer(
                    'sentence-transformers/all-MiniLM-L6-v2'
                )
            except ImportError:
                logger.warning("sentence-transformers not installed, using random vectors")
                return None
        return self._embedding_model
    
    def _generate_test_vector(self, text: str) -> List[float]:
        """Generate a test vector for search."""
        model = self._get_embedding_model()
        if model:
            return model.encode(text).tolist()
        else:
            # Return random vector if no model
            import random
            return [random.random() for _ in range(self.config.text_embedding_dim)]
    
    def add_result(self, name: str, passed: bool, message: str, details: Dict = None):
        """Add a verification result."""
        result = VerificationResult(name, passed, message, details)
        self.results.append(result)
        logger.info(str(result))
        return result
    
    # ========================================
    # Collection Existence Checks
    # ========================================
    
    def verify_collections_exist(self) -> bool:
        """Verify all collections exist."""
        client = self._get_client()
        
        collections = client.get_collections().collections
        existing = {c.name for c in collections}
        
        expected = {
            self.config.products_collection,
            self.config.user_profiles_collection,
            self.config.reviews_collection,
            self.config.interactions_collection
        }
        
        missing = expected - existing
        
        if missing:
            self.add_result(
                "Collections Exist",
                False,
                f"Missing collections: {missing}",
                {"existing": list(existing), "missing": list(missing)}
            )
            return False
        
        self.add_result(
            "Collections Exist",
            True,
            f"All {len(expected)} collections found",
            {"collections": list(expected)}
        )
        return True
    
    # ========================================
    # Point Count Checks
    # ========================================
    
    def verify_point_counts(self) -> Dict[str, bool]:
        """Verify point counts in each collection."""
        client = self._get_client()
        results = {}
        
        checks = [
            (self.config.products_collection, self.config.expected_products, "Products"),
            (self.config.user_profiles_collection, self.config.expected_users, "User Profiles"),
            (self.config.reviews_collection, self.config.expected_reviews, "Reviews"),
            (self.config.interactions_collection, self.config.expected_interactions, "Interactions")
        ]
        
        for collection_name, expected_count, display_name in checks:
            try:
                info = client.get_collection(collection_name)
                actual_count = info.points_count
                
                # Allow 10% variance
                variance = 0.1
                min_expected = int(expected_count * (1 - variance))
                max_expected = int(expected_count * (1 + variance))
                
                passed = min_expected <= actual_count <= max_expected
                
                self.add_result(
                    f"{display_name} Count",
                    passed,
                    f"Expected ~{expected_count}, got {actual_count}",
                    {"expected": expected_count, "actual": actual_count}
                )
                results[collection_name] = passed
                
            except Exception as e:
                self.add_result(
                    f"{display_name} Count",
                    False,
                    f"Error: {e}"
                )
                results[collection_name] = False
        
        return results
    
    # ========================================
    # Vector Search Tests
    # ========================================
    
    def test_product_search(self) -> bool:
        """Test vector search on products collection."""
        client = self._get_client()
        
        # Generate test query vector
        query_text = "wireless bluetooth headphones with noise cancellation"
        query_vector = self._generate_test_vector(query_text)
        
        try:
            search_result = client.query_points(
                collection_name=self.config.products_collection,
                query=query_vector,
                limit=5
            )
            results = search_result.points
            
            if len(results) > 0:
                # Check that results have expected fields
                first_result = results[0]
                has_payload = first_result.payload is not None
                has_score = first_result.score is not None
                
                self.add_result(
                    "Product Vector Search",
                    True,
                    f"Found {len(results)} results for '{query_text[:30]}...'",
                    {
                        "query": query_text,
                        "results_count": len(results),
                        "top_score": results[0].score,
                        "top_product": results[0].payload.get('title', 'Unknown')[:50]
                    }
                )
                return True
            else:
                self.add_result(
                    "Product Vector Search",
                    False,
                    "No results returned"
                )
                return False
                
        except Exception as e:
            self.add_result(
                "Product Vector Search",
                False,
                f"Search failed: {e}"
            )
            return False
    
    def test_user_search(self) -> bool:
        """Test vector search on user profiles collection."""
        client = self._get_client()
        
        query_text = "budget conscious student looking for affordable electronics"
        query_vector = self._generate_test_vector(query_text)
        
        try:
            search_result = client.query_points(
                collection_name=self.config.user_profiles_collection,
                query=query_vector,
                limit=5
            )
            results = search_result.points
            
            if len(results) > 0:
                self.add_result(
                    "User Profile Vector Search",
                    True,
                    f"Found {len(results)} similar user profiles",
                    {
                        "query": query_text,
                        "results_count": len(results),
                        "top_persona": results[0].payload.get('persona_type', 'Unknown')
                    }
                )
                return True
            else:
                self.add_result(
                    "User Profile Vector Search",
                    False,
                    "No results returned"
                )
                return False
                
        except Exception as e:
            self.add_result(
                "User Profile Vector Search",
                False,
                f"Search failed: {e}"
            )
            return False
    
    def test_review_search(self) -> bool:
        """Test vector search on reviews collection."""
        client = self._get_client()
        
        query_text = "excellent product great quality highly recommend"
        query_vector = self._generate_test_vector(query_text)
        
        try:
            search_result = client.query_points(
                collection_name=self.config.reviews_collection,
                query=query_vector,
                limit=5
            )
            results = search_result.points
            
            if len(results) > 0:
                self.add_result(
                    "Review Vector Search",
                    True,
                    f"Found {len(results)} similar reviews",
                    {
                        "query": query_text,
                        "results_count": len(results),
                        "top_rating": results[0].payload.get('rating', 'Unknown'),
                        "top_sentiment": results[0].payload.get('sentiment', 'Unknown')
                    }
                )
                return True
            else:
                self.add_result(
                    "Review Vector Search",
                    False,
                    "No results returned"
                )
                return False
                
        except Exception as e:
            self.add_result(
                "Review Vector Search",
                False,
                f"Search failed: {e}"
            )
            return False
    
    def test_interaction_search(self) -> bool:
        """Test vector search on interactions collection."""
        client = self._get_client()
        
        query_text = "laptop for programming and coding"
        query_vector = self._generate_test_vector(query_text)
        
        try:
            search_result = client.query_points(
                collection_name=self.config.interactions_collection,
                query=query_vector,
                limit=5
            )
            results = search_result.points
            
            if len(results) > 0:
                self.add_result(
                    "Interaction Vector Search",
                    True,
                    f"Found {len(results)} similar interactions",
                    {
                        "query": query_text,
                        "results_count": len(results),
                        "top_type": results[0].payload.get('interaction_type', 'Unknown')
                    }
                )
                return True
            else:
                self.add_result(
                    "Interaction Vector Search",
                    False,
                    "No results returned"
                )
                return False
                
        except Exception as e:
            self.add_result(
                "Interaction Vector Search",
                False,
                f"Search failed: {e}"
            )
            return False
    
    # ========================================
    # Payload Filter Tests
    # ========================================
    
    def test_product_filters(self) -> bool:
        """Test payload filtering on products."""
        from qdrant_client.models import Filter, FieldCondition, MatchValue, Range
        
        client = self._get_client()
        
        try:
            # Test category filter
            results = client.scroll(
                collection_name=self.config.products_collection,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="category",
                            match=MatchValue(value="Electronics")
                        )
                    ]
                ),
                limit=10
            )
            
            electronics_count = len(results[0])
            
            # Test price range filter
            results = client.scroll(
                collection_name=self.config.products_collection,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="price",
                            range=Range(gte=100, lte=500)
                        )
                    ]
                ),
                limit=10
            )
            
            price_range_count = len(results[0])
            
            passed = electronics_count > 0 and price_range_count > 0
            
            self.add_result(
                "Product Payload Filters",
                passed,
                f"Category filter: {electronics_count} results, Price filter: {price_range_count} results",
                {
                    "electronics_count": electronics_count,
                    "price_range_count": price_range_count
                }
            )
            return passed
            
        except Exception as e:
            self.add_result(
                "Product Payload Filters",
                False,
                f"Filter test failed: {e}"
            )
            return False
    
    def test_user_filters(self) -> bool:
        """Test payload filtering on user profiles."""
        from qdrant_client.models import Filter, FieldCondition, MatchValue, Range
        
        client = self._get_client()
        
        try:
            # Test persona filter
            results = client.scroll(
                collection_name=self.config.user_profiles_collection,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="persona_type",
                            match=MatchValue(value="student")
                        )
                    ]
                ),
                limit=10
            )
            
            student_count = len(results[0])
            
            # Test budget filter
            results = client.scroll(
                collection_name=self.config.user_profiles_collection,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="budget_max",
                            range=Range(gte=1000)
                        )
                    ]
                ),
                limit=10
            )
            
            high_budget_count = len(results[0])
            
            passed = student_count > 0 or high_budget_count > 0
            
            self.add_result(
                "User Payload Filters",
                passed,
                f"Student filter: {student_count}, High budget filter: {high_budget_count}",
                {
                    "student_count": student_count,
                    "high_budget_count": high_budget_count
                }
            )
            return passed
            
        except Exception as e:
            self.add_result(
                "User Payload Filters",
                False,
                f"Filter test failed: {e}"
            )
            return False
    
    def test_review_filters(self) -> bool:
        """Test payload filtering on reviews."""
        from qdrant_client.models import Filter, FieldCondition, MatchValue, Range
        
        client = self._get_client()
        
        try:
            # Test rating filter
            results = client.scroll(
                collection_name=self.config.reviews_collection,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="rating",
                            range=Range(gte=4)
                        )
                    ]
                ),
                limit=10
            )
            
            high_rating_count = len(results[0])
            
            # Test sentiment filter
            results = client.scroll(
                collection_name=self.config.reviews_collection,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="sentiment",
                            match=MatchValue(value="positive")
                        )
                    ]
                ),
                limit=10
            )
            
            positive_count = len(results[0])
            
            passed = high_rating_count > 0 or positive_count > 0
            
            self.add_result(
                "Review Payload Filters",
                passed,
                f"High rating (≥4): {high_rating_count}, Positive sentiment: {positive_count}",
                {
                    "high_rating_count": high_rating_count,
                    "positive_count": positive_count
                }
            )
            return passed
            
        except Exception as e:
            self.add_result(
                "Review Payload Filters",
                False,
                f"Filter test failed: {e}"
            )
            return False
    
    def test_interaction_filters(self) -> bool:
        """Test payload filtering on interactions."""
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        client = self._get_client()
        
        try:
            # Test interaction type filter
            results = client.scroll(
                collection_name=self.config.interactions_collection,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="interaction_type",
                            match=MatchValue(value="search")
                        )
                    ]
                ),
                limit=10
            )
            
            search_count = len(results[0])
            
            # Test conversion filter
            results = client.scroll(
                collection_name=self.config.interactions_collection,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="interaction_type",
                            match=MatchValue(value="purchase")
                        )
                    ]
                ),
                limit=10
            )
            
            purchase_count = len(results[0])
            
            passed = search_count > 0 or purchase_count > 0
            
            self.add_result(
                "Interaction Payload Filters",
                passed,
                f"Search interactions: {search_count}, Purchase interactions: {purchase_count}",
                {
                    "search_count": search_count,
                    "purchase_count": purchase_count
                }
            )
            return passed
            
        except Exception as e:
            self.add_result(
                "Interaction Payload Filters",
                False,
                f"Filter test failed: {e}"
            )
            return False
    
    # ========================================
    # Cross-Collection Tests
    # ========================================
    
    def test_cross_collection_query(self) -> bool:
        """Test cross-collection queries (e.g., reviews for a product)."""
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        client = self._get_client()
        
        try:
            # Get a sample product
            products = client.scroll(
                collection_name=self.config.products_collection,
                limit=1
            )
            
            if not products[0]:
                self.add_result(
                    "Cross-Collection Query",
                    False,
                    "No products found to test"
                )
                return False
            
            product = products[0][0]
            product_id = product.payload.get('original_id') or product.payload.get('id')
            
            # Find reviews for this product
            reviews = client.scroll(
                collection_name=self.config.reviews_collection,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="product_id",
                            match=MatchValue(value=product_id)
                        )
                    ]
                ),
                limit=10
            )
            
            review_count = len(reviews[0])
            
            self.add_result(
                "Cross-Collection Query",
                True,
                f"Found {review_count} reviews for product '{product_id[:20]}...'",
                {
                    "product_id": product_id,
                    "product_title": product.payload.get('title', 'Unknown')[:50],
                    "review_count": review_count
                }
            )
            return True
            
        except Exception as e:
            self.add_result(
                "Cross-Collection Query",
                False,
                f"Cross-collection test failed: {e}"
            )
            return False
    
    def test_user_interactions_query(self) -> bool:
        """Test finding interactions for a user."""
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        client = self._get_client()

        try:
            # Get a sample user
            users = client.scroll(
                collection_name=self.config.user_profiles_collection,
                limit=1
            )

            if not users[0]:
                self.add_result(
                    "User Interactions Query",
                    False,
                    "No users found to test"
                )
                return False

            user = users[0][0]
            # User ID is stored in the point's id field, not in payload
            user_id = user.payload.get('original_id') or user.payload.get('id') or user.payload.get('user_id') or str(user.id)
            
            if not user_id:
                self.add_result(
                    "User Interactions Query",
                    False,
                    "User has no valid ID field"
                )
                return False

            # Find interactions for this user
            interactions = client.scroll(
                collection_name=self.config.interactions_collection,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="user_id",
                            match=MatchValue(value=str(user_id))
                        )
                    ]
                ),
                limit=20
            )

            interaction_count = len(interactions[0])

            self.add_result(
                "User Interactions Query",
                True,
                f"Found {interaction_count} interactions for user '{str(user_id)[:20]}...'",
                {
                    "user_id": str(user_id),
                    "persona": user.payload.get('persona_type', 'Unknown'),
                    "interaction_count": interaction_count
                }
            )
            return True
            
        except Exception as e:
            self.add_result(
                "User Interactions Query",
                False,
                f"User interactions test failed: {e}"
            )
            return False
    
    # ========================================
    # Combined Search Test
    # ========================================
    
    def test_combined_search(self) -> bool:
        """Test combined vector search with filters."""
        from qdrant_client.models import Filter, FieldCondition, MatchValue, Range

        client = self._get_client()

        query_text = "premium laptop for work"
        query_vector = self._generate_test_vector(query_text)

        try:
            # Search with category and price filter
            search_result = client.query_points(
                collection_name=self.config.products_collection,
                query=query_vector,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="category",
                            match=MatchValue(value="Electronics")
                        ),
                        FieldCondition(
                            key="price",
                            range=Range(gte=500, lte=2000)
                        )
                    ]
                ),
                limit=5
            )
            results = search_result.points

            if len(results) > 0:
                self.add_result(
                    "Combined Vector + Filter Search",
                    True,
                    f"Found {len(results)} electronics products $500-$2000",
                    {
                        "query": query_text,
                        "filters": "Electronics, $500-$2000",
                        "results_count": len(results),
                        "top_product": results[0].payload.get('title', 'Unknown')[:50],
                        "top_price": results[0].payload.get('price', 'Unknown')
                    }
                )
                return True
            else:
                self.add_result(
                    "Combined Vector + Filter Search",
                    False,
                    "No results returned"
                )
                return False
                
        except Exception as e:
            self.add_result(
                "Combined Vector + Filter Search",
                False,
                f"Combined search failed: {e}"
            )
            return False
    
    # ========================================
    # Run All Verifications
    # ========================================
    
    def run_all_verifications(self) -> Tuple[int, int]:
        """
        Run all verification checks.
        
        Returns:
            Tuple of (passed_count, failed_count).
        """
        logger.info("=" * 60)
        logger.info("Starting Qdrant Data Verification")
        logger.info("=" * 60)
        
        # Collection existence
        logger.info("\n--- Collection Existence ---")
        if not self.verify_collections_exist():
            logger.error("Collection existence check failed, aborting further tests")
            return 0, 1
        
        # Point counts
        logger.info("\n--- Point Counts ---")
        self.verify_point_counts()
        
        # Vector searches
        logger.info("\n--- Vector Search Tests ---")
        self.test_product_search()
        self.test_user_search()
        self.test_review_search()
        self.test_interaction_search()
        
        # Payload filters
        logger.info("\n--- Payload Filter Tests ---")
        self.test_product_filters()
        self.test_user_filters()
        self.test_review_filters()
        self.test_interaction_filters()
        
        # Cross-collection
        logger.info("\n--- Cross-Collection Tests ---")
        self.test_cross_collection_query()
        self.test_user_interactions_query()
        
        # Combined search
        logger.info("\n--- Combined Search Test ---")
        self.test_combined_search()
        
        # Calculate totals
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        
        return passed, failed
    
    def print_report(self):
        """Print a summary report of all verifications."""
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total = len(self.results)
        
        print("\n" + "=" * 70)
        print("               QDRANT VERIFICATION REPORT")
        print("=" * 70)
        print(f"\nGenerated at: {datetime.now().isoformat()}")
        print(f"Qdrant URL: {self.config.qdrant_url}")
        
        print("\n" + "-" * 70)
        print("RESULTS:")
        print("-" * 70)
        
        for result in self.results:
            print(f"  {result}")
        
        print("\n" + "-" * 70)
        print("SUMMARY:")
        print("-" * 70)
        print(f"  Total Checks: {total}")
        print(f"  Passed: {passed} ({passed/total*100:.1f}%)")
        print(f"  Failed: {failed} ({failed/total*100:.1f}%)")
        
        if failed == 0:
            print("\n✅ All verification checks passed!")
        else:
            print(f"\n⚠️  {failed} verification check(s) failed")
        
        print("=" * 70 + "\n")
        
        return failed == 0


def main():
    """Main entry point for verification."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Verify Qdrant data upload")
    parser.add_argument(
        '--expected-products',
        type=int,
        default=500,
        help='Expected number of products'
    )
    parser.add_argument(
        '--expected-users',
        type=int,
        default=100,
        help='Expected number of users'
    )
    parser.add_argument(
        '--expected-reviews',
        type=int,
        default=1200,
        help='Expected number of reviews'
    )
    parser.add_argument(
        '--expected-interactions',
        type=int,
        default=2000,
        help='Expected number of interactions'
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Create config
    config = VerificationConfig(
        expected_products=args.expected_products,
        expected_users=args.expected_users,
        expected_reviews=args.expected_reviews,
        expected_interactions=args.expected_interactions
    )
    
    # Run verification
    try:
        verifier = QdrantVerifier(config)
        passed, failed = verifier.run_all_verifications()
        all_passed = verifier.print_report()
        
        return 0 if all_passed else 1
        
    except Exception as e:
        logger.exception(f"Verification failed: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
