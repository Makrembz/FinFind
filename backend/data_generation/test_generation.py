#!/usr/bin/env python3
"""
Quick test script for data generation.

Generates a small sample to verify everything works before
running full generation.
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test that all imports work."""
    print("Testing imports...")
    
    try:
        from data_generation.config import (
            GenerationConfig, CATEGORY_HIERARCHY, BRANDS_BY_CATEGORY,
            USER_PERSONAS, SEARCH_QUERY_TEMPLATES, FUNNEL_PROBABILITIES
        )
        print("  ✓ Config imports OK")
    except ImportError as e:
        print(f"  ✗ Config import failed: {e}")
        return False
    
    try:
        from data_generation.models.product_models import Product, ProductAttributes
        print("  ✓ Product models OK")
    except ImportError as e:
        print(f"  ✗ Product models failed: {e}")
        return False
    
    try:
        from data_generation.models.review_models import Review, ReviewAspects
        print("  ✓ Review models OK")
    except ImportError as e:
        print(f"  ✗ Review models failed: {e}")
        return False
    
    try:
        from data_generation.models.user_models import UserProfile, FinancialContext, UserPreferences
        print("  ✓ User models OK")
    except ImportError as e:
        print(f"  ✗ User models failed: {e}")
        return False
    
    try:
        from data_generation.models.interaction_models import UserInteraction, SearchContext, ViewContext
        print("  ✓ Interaction models OK")
    except ImportError as e:
        print(f"  ✗ Interaction models failed: {e}")
        return False
    
    try:
        from data_generation.generators.product_generator import ProductGenerator
        print("  ✓ Product generator OK")
    except ImportError as e:
        print(f"  ✗ Product generator failed: {e}")
        return False
    
    try:
        from data_generation.generators.review_generator import ReviewGenerator
        print("  ✓ Review generator OK")
    except ImportError as e:
        print(f"  ✗ Review generator failed: {e}")
        return False
    
    try:
        from data_generation.generators.user_generator import UserProfileGenerator
        print("  ✓ User generator OK")
    except ImportError as e:
        print(f"  ✗ User generator failed: {e}")
        return False
    
    try:
        from data_generation.generators.interaction_generator import InteractionGenerator
        print("  ✓ Interaction generator OK")
    except ImportError as e:
        print(f"  ✗ Interaction generator failed: {e}")
        return False
    
    return True


def test_product_generation():
    """Test generating a small number of products."""
    print("\nTesting product generation (5 products, no embeddings)...")
    
    from data_generation.config import GenerationConfig
    from data_generation.generators.product_generator import ProductGenerator
    
    config = GenerationConfig(
        num_products=5,
        generate_embeddings=False,
        random_seed=42
    )
    
    generator = ProductGenerator(config)
    products = generator.generate()
    
    if len(products) != 5:
        print(f"  ✗ Expected 5 products, got {len(products)}")
        return False
    
    # Check each product
    for i, product in enumerate(products):
        if not product.id:
            print(f"  ✗ Product {i} missing ID")
            return False
        if not product.title or len(product.title) < 10:
            print(f"  ✗ Product {i} has invalid title")
            return False
        if not product.description or len(product.description) < 50:
            print(f"  ✗ Product {i} has invalid description")
            return False
        if product.price <= 0:
            print(f"  ✗ Product {i} has invalid price: {product.price}")
            return False
    
    print(f"  ✓ Generated {len(products)} valid products")
    
    # Show sample
    sample = products[0]
    print(f"\n  Sample Product:")
    print(f"    Title: {sample.title[:60]}...")
    print(f"    Category: {sample.category} > {sample.subcategory}")
    print(f"    Brand: {sample.brand}")
    print(f"    Price: ${sample.price:.2f}")
    
    return True


def test_review_generation():
    """Test generating reviews linked to products."""
    print("\nTesting review generation (10 reviews for 5 products)...")
    
    from data_generation.config import GenerationConfig
    from data_generation.generators.product_generator import ProductGenerator
    from data_generation.generators.review_generator import ReviewGenerator
    
    config = GenerationConfig(
        num_products=5,
        num_reviews=10,
        generate_embeddings=False,
        random_seed=42
    )
    
    # Generate products first
    product_generator = ProductGenerator(config)
    products = product_generator.generate()
    
    # Generate reviews
    review_generator = ReviewGenerator(config, products)
    reviews = review_generator.generate()
    
    if len(reviews) != 10:
        print(f"  ✗ Expected 10 reviews, got {len(reviews)}")
        return False
    
    # Check that reviews reference valid products
    product_ids = {p.id for p in products}
    for review in reviews:
        if review.product_id not in product_ids:
            print(f"  ✗ Review references invalid product: {review.product_id}")
            return False
    
    print(f"  ✓ Generated {len(reviews)} valid reviews")
    
    # Show sample
    sample = reviews[0]
    print(f"\n  Sample Review:")
    print(f"    Rating: {'⭐' * sample.rating}")
    print(f"    Title: {sample.title}")
    print(f"    Text: {sample.text[:80]}...")
    print(f"    Sentiment: {sample.sentiment} ({sample.sentiment_score:.2f})")
    print(f"    Verified: {sample.verified_purchase}")
    
    # Show stats
    stats = review_generator.get_review_stats(reviews)
    print(f"\n  Review Stats:")
    print(f"    Average Rating: {stats['average_rating']:.2f}")
    print(f"    Rating Distribution: {stats['rating_distribution']}")
    print(f"    Sentiment Distribution: {stats['sentiment_distribution']}")
    
    return True


def test_json_export():
    """Test exporting data to JSON."""
    print("\nTesting JSON export...")
    
    from data_generation.config import GenerationConfig
    from data_generation.generators.product_generator import ProductGenerator
    from data_generation.generators.review_generator import ReviewGenerator
    from data_generation.uploaders.json_exporter import JSONExporter
    import tempfile
    import json
    
    config = GenerationConfig(
        num_products=3,
        num_reviews=5,
        generate_embeddings=False
    )
    
    # Generate data
    product_gen = ProductGenerator(config)
    products = product_gen.generate()
    
    review_gen = ReviewGenerator(config, products)
    reviews = review_gen.generate()
    
    # Export to temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        exporter = JSONExporter(tmpdir)
        
        products_path = exporter.export_products(products)
        reviews_path = exporter.export_reviews(reviews)
        
        # Verify files exist and are valid JSON
        if not products_path.exists():
            print("  ✗ Products file not created")
            return False
        
        if not reviews_path.exists():
            print("  ✗ Reviews file not created")
            return False
        
        # Load and verify structure
        with open(products_path) as f:
            products_data = json.load(f)
        
        if products_data.get('count') != 3:
            print(f"  ✗ Products count mismatch: {products_data.get('count')}")
            return False
        
        with open(reviews_path) as f:
            reviews_data = json.load(f)
        
        if reviews_data.get('count') != 5:
            print(f"  ✗ Reviews count mismatch: {reviews_data.get('count')}")
            return False
    
    print("  ✓ JSON export working correctly")
    return True


def test_embedding_availability():
    """Check if sentence-transformers is available."""
    print("\nChecking embedding model availability...")
    
    try:
        from sentence_transformers import SentenceTransformer
        print("  ✓ sentence-transformers is installed")
        
        # Try loading the model (this may take a moment first time)
        print("  Loading model (may take a moment on first run)...")
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        dim = model.get_sentence_embedding_dimension()
        print(f"  ✓ Model loaded successfully (dimension: {dim})")
        
        # Test encoding
        test_text = "This is a test product description"
        embedding = model.encode(test_text)
        print(f"  ✓ Test embedding generated (length: {len(embedding)})")
        
        return True
    except ImportError:
        print("  ⚠ sentence-transformers not installed")
        print("    Run: pip install sentence-transformers")
        return False
    except Exception as e:
        print(f"  ✗ Error loading model: {e}")
        return False


def test_user_generation():
    """Test generating user profiles."""
    print("\nTesting user profile generation (10 users, no embeddings)...")
    
    from data_generation.config import GenerationConfig
    from data_generation.generators.product_generator import ProductGenerator
    from data_generation.generators.user_generator import UserProfileGenerator
    
    config = GenerationConfig(
        num_products=20,
        num_users=10,
        generate_embeddings=False,
        random_seed=42
    )
    
    # Generate products first (needed for purchase history)
    product_generator = ProductGenerator(config)
    products = product_generator.generate()
    
    # Generate users
    user_generator = UserProfileGenerator(config, products)
    users = user_generator.generate()
    
    if len(users) != 10:
        print(f"  ✗ Expected 10 users, got {len(users)}")
        return False
    
    # Check user profiles
    personas_found = set()
    for user in users:
        if not user.id:
            print(f"  ✗ User missing ID")
            return False
        if user.financial_context.budget_min >= user.financial_context.budget_max:
            print(f"  ✗ Invalid budget range for user {user.id}")
            return False
        if user.primary_payment_method not in user.payment_methods:
            print(f"  ✗ Primary payment method not in methods for user {user.id}")
            return False
        personas_found.add(user.persona_type)
    
    print(f"  ✓ Generated {len(users)} valid user profiles")
    print(f"  ✓ Personas found: {personas_found}")
    
    # Show sample
    sample = users[0]
    print(f"\n  Sample User Profile:")
    print(f"    ID: {sample.id}")
    print(f"    Persona: {sample.persona_type}")
    print(f"    Age Range: {sample.age_range}")
    print(f"    Budget: ${sample.financial_context.budget_min:.0f} - ${sample.financial_context.budget_max:.0f}")
    print(f"    Affordability: {sample.financial_context.affordability_score:.2f}")
    print(f"    Payment Methods: {sample.payment_methods}")
    print(f"    Purchase History: {len(sample.purchase_history)} items")
    
    # Get stats
    stats = user_generator.get_statistics(users)
    print(f"\n  User Stats:")
    print(f"    Personas: {stats['personas']}")
    print(f"    Avg Budget: ${stats['financial_metrics']['avg_budget_min']:.0f} - ${stats['financial_metrics']['avg_budget_max']:.0f}")
    
    return True


def test_interaction_generation():
    """Test generating user interactions."""
    print("\nTesting interaction generation (100 interactions, no embeddings)...")
    
    from data_generation.config import GenerationConfig
    from data_generation.generators.product_generator import ProductGenerator
    from data_generation.generators.user_generator import UserProfileGenerator
    from data_generation.generators.interaction_generator import InteractionGenerator
    
    config = GenerationConfig(
        num_products=20,
        num_users=5,
        num_interactions=100,
        generate_embeddings=False,
        random_seed=42
    )
    
    # Generate products and users first
    product_generator = ProductGenerator(config)
    products = product_generator.generate()
    
    user_generator = UserProfileGenerator(config, products)
    users = user_generator.generate()
    
    # Generate interactions
    interaction_generator = InteractionGenerator(config, users, products)
    interactions = interaction_generator.generate()
    
    if len(interactions) < 90:  # Allow some variance
        print(f"  ✗ Expected ~100 interactions, got {len(interactions)}")
        return False
    
    # Check interactions
    user_ids = {u.id for u in users}
    product_ids = {p.id for p in products}
    interaction_types = set()
    
    for interaction in interactions:
        if not interaction.id:
            print(f"  ✗ Interaction missing ID")
            return False
        if interaction.user_id not in user_ids:
            print(f"  ✗ Invalid user reference: {interaction.user_id}")
            return False
        interaction_types.add(interaction.interaction_type)
    
    print(f"  ✓ Generated {len(interactions)} valid interactions")
    print(f"  ✓ Interaction types: {interaction_types}")
    
    # Show sample
    searches = [i for i in interactions if i.search_context]
    if searches:
        sample = searches[0]
        print(f"\n  Sample Search Interaction:")
        print(f"    Query: \"{sample.search_context.query}\"")
        print(f"    Type: {sample.search_context.query_type}")
        print(f"    Device: {sample.device_type}")
        print(f"    Session: {sample.session_id}")
    
    # Get stats
    stats = interaction_generator.get_statistics(interactions)
    print(f"\n  Interaction Stats:")
    print(f"    Types: {stats['interaction_types']}")
    print(f"    Unique Sessions: {stats['unique_sessions']}")
    print(f"    Conversions: {stats['conversions']}")
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("FinFind Data Generation - Quick Test")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Product Generation", test_product_generation()))
    results.append(("Review Generation", test_review_generation()))
    results.append(("User Generation", test_user_generation()))
    results.append(("Interaction Generation", test_interaction_generation()))
    results.append(("JSON Export", test_json_export()))
    results.append(("Embeddings", test_embedding_availability()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n✅ All tests passed! You can now run full generation:")
        print("   cd backend/data_generation")
        print("   python run_generation.py --all")
        print("")
        print("   Or generate with custom amounts:")
        print("   python run_generation.py --all --products 500 --users 100 --interactions 2000")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
