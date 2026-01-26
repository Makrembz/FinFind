#!/usr/bin/env python3
"""
Main script for generating FinFind synthetic data.

This script orchestrates the generation of products, reviews, users, and
interactions data for the FinFind e-commerce platform.

Usage:
    python run_generation.py [options]
    
Examples:
    # Generate all data with defaults
    python run_generation.py --all
    
    # Generate only products and reviews
    python run_generation.py --products 500 --reviews 1200
    
    # Generate with custom amounts
    python run_generation.py --all --products 1000 --users 200 --interactions 5000
    
    # Skip embeddings for faster testing
    python run_generation.py --all --no-embeddings
"""

import argparse
import logging
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_generation.config import GenerationConfig
from data_generation.generators.product_generator import ProductGenerator
from data_generation.generators.review_generator import ReviewGenerator
from data_generation.generators.user_generator import UserProfileGenerator
from data_generation.generators.interaction_generator import InteractionGenerator
from data_generation.services.consistency_service import ConsistencyService
from data_generation.uploaders.json_exporter import JSONExporter
from data_generation.models.product_models import Product
from data_generation.models.user_models import UserProfile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic data for FinFind"
    )
    
    # Mode selection
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='Generate all data types (products, reviews, users, interactions)'
    )
    
    parser.add_argument(
        '--products', '-p',
        type=int,
        default=500,
        help='Number of products to generate (default: 500)'
    )
    
    parser.add_argument(
        '--reviews', '-r',
        type=int,
        default=1200,
        help='Number of reviews to generate (default: 1200)'
    )
    
    parser.add_argument(
        '--users', '-u',
        type=int,
        default=100,
        help='Number of user profiles to generate (default: 100)'
    )
    
    parser.add_argument(
        '--interactions', '-i',
        type=int,
        default=2000,
        help='Number of interactions to generate (default: 2000)'
    )
    
    parser.add_argument(
        '--no-embeddings',
        action='store_true',
        help='Skip embedding generation (faster, for testing)'
    )
    
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        default='output',
        help='Output directory for generated data (default: output)'
    )
    
    # Skip flags for selective generation
    parser.add_argument(
        '--skip-products',
        action='store_true',
        help='Skip product generation (load from existing file)'
    )
    
    parser.add_argument(
        '--skip-users',
        action='store_true',
        help='Skip user profile generation (load from existing file)'
    )
    
    return parser.parse_args()


def load_existing_products(output_dir: Path) -> List[Product]:
    """Load products from existing JSON file."""
    products_file = output_dir / "products.json"
    if not products_file.exists():
        raise FileNotFoundError(f"Products file not found: {products_file}")
    
    logger.info(f"Loading existing products from {products_file}")
    with open(products_file, 'r') as f:
        data = json.load(f)
    
    # Handle both list and dict formats
    if isinstance(data, dict):
        items = data.get('items', [])
    else:
        items = data
    
    products = [Product(**p) for p in items]
    logger.info(f"Loaded {len(products)} existing products")
    return products


def load_existing_users(output_dir: Path) -> List[UserProfile]:
    """Load user profiles from existing JSON file."""
    users_file = output_dir / "user_profiles.json"
    if not users_file.exists():
        raise FileNotFoundError(f"Users file not found: {users_file}")
    
    logger.info(f"Loading existing users from {users_file}")
    with open(users_file, 'r') as f:
        data = json.load(f)
    
    # Handle both list and dict formats
    if isinstance(data, dict):
        items = data.get('items', [])
    else:
        items = data
    
    users = [UserProfile(**u) for u in items]
    logger.info(f"Loaded {len(users)} existing users")
    return users


def generate_all_data(config: GenerationConfig, args) -> Dict[str, Any]:
    """
    Generate all data: products, reviews, users, interactions.
    
    Args:
        config: Generation configuration.
        args: Command line arguments.
        
    Returns:
        Dictionary with generated data and statistics.
    """
    results = {
        "products": [],
        "reviews": [],
        "users": [],
        "interactions": [],
        "statistics": {},
        "validation": {}
    }
    
    # Initialize services
    consistency_service = ConsistencyService()
    exporter = JSONExporter(str(config.output_dir))
    
    # ==========================================
    # PHASE 1: Generate or Load Products
    # ==========================================
    logger.info("=" * 60)
    logger.info("PHASE 1: Products")
    logger.info("=" * 60)
    
    if args.skip_products:
        products = load_existing_products(config.output_dir)
        results["validation"]["products"] = True
    else:
        product_generator = ProductGenerator(config)
        products = product_generator.generate()
        
        # Validate products
        products_valid = product_generator.validate(products)
        results["validation"]["products"] = products_valid
        
        if not products_valid:
            logger.error("Product validation failed!")
            return results
        
        # Export products
        exporter.export_products(products)
        if config.generate_embeddings:
            exporter.export_for_qdrant(products, "products")
        
        logger.info(f"Generated and exported {len(products)} products")
    
    # Register products for consistency tracking
    consistency_service.register_products(products)
    results["products"] = products
    
    # ==========================================
    # PHASE 2: Generate Reviews
    # ==========================================
    logger.info("=" * 60)
    logger.info("PHASE 2: Reviews")
    logger.info("=" * 60)
    
    review_generator = ReviewGenerator(config, products)
    reviews = review_generator.generate()
    
    # Validate reviews
    reviews_valid = review_generator.validate(reviews)
    results["validation"]["reviews"] = reviews_valid
    
    if not reviews_valid:
        logger.error("Review validation failed!")
        return results
    
    # Register reviews for consistency tracking
    consistency_service.register_reviews(reviews)
    results["reviews"] = reviews
    
    # Export reviews
    exporter.export_reviews(reviews)
    if config.generate_embeddings:
        exporter.export_for_qdrant(reviews, "reviews")
    
    # Get review statistics
    review_stats = review_generator.get_review_stats(reviews)
    results["statistics"]["reviews"] = review_stats
    
    # Update product stats with review data
    for product in products:
        product_reviews = [r for r in reviews if r.product_id == product.id]
        if product_reviews:
            product.review_count = len(product_reviews)
            product.rating_avg = round(
                sum(r.rating for r in product_reviews) / len(product_reviews), 2
            )
    
    # Re-export products with updated stats
    exporter.export_products(products, "products_with_reviews.json")
    
    logger.info(f"Generated and exported {len(reviews)} reviews")
    
    # ==========================================
    # PHASE 3: Generate or Load User Profiles
    # ==========================================
    logger.info("=" * 60)
    logger.info("PHASE 3: User Profiles")
    logger.info("=" * 60)
    
    if args.skip_users:
        users = load_existing_users(config.output_dir)
        results["validation"]["users"] = True
    else:
        user_generator = UserProfileGenerator(config, products)
        users = user_generator.generate()
        
        # Validate
        users_valid = user_generator.validate(users)
        results["validation"]["users"] = users_valid
        
        if not users_valid:
            logger.error("User profile validation failed!")
            return results
        
        # Export
        exporter.export_users(users)
        if config.generate_embeddings:
            exporter.export_for_qdrant(users, "user_profiles")
        
        # Get statistics
        results["statistics"]["users"] = user_generator.get_statistics(users)
        
        logger.info(f"Generated and exported {len(users)} user profiles")
    
    consistency_service.register_users(users)
    results["users"] = users
    
    # ==========================================
    # PHASE 4: Generate User Interactions
    # ==========================================
    if args.all:
        logger.info("=" * 60)
        logger.info("PHASE 4: User Interactions")
        logger.info("=" * 60)
        
        interaction_generator = InteractionGenerator(config, users, products)
        interactions = interaction_generator.generate()
        
        # Validate
        interactions_valid = interaction_generator.validate(interactions)
        results["validation"]["interactions"] = interactions_valid
        
        if not interactions_valid:
            logger.error("Interaction validation failed!")
            return results
        
        consistency_service.register_interactions(interactions)
        results["interactions"] = interactions
        
        # Export
        exporter.export_interactions(interactions)
        if config.generate_embeddings:
            exporter.export_for_qdrant(interactions, "user_interactions")
        
        # Get statistics
        results["statistics"]["interactions"] = interaction_generator.get_statistics(interactions)
        
        logger.info(f"Generated and exported {len(interactions)} interactions")
    else:
        results["validation"]["interactions"] = True
    
    # ==========================================
    # PHASE 5: Generate Metadata
    # ==========================================
    logger.info("=" * 60)
    logger.info("PHASE 5: Metadata and Summary")
    logger.info("=" * 60)
    
    # Collect category distribution
    category_distribution = {}
    for product in products:
        category_distribution[product.category] = category_distribution.get(product.category, 0) + 1
    
    price_stats = {
        "min": min(p.price for p in products),
        "max": max(p.price for p in products),
        "avg": round(sum(p.price for p in products) / len(products), 2)
    }
    
    metadata = {
        "generated_at": datetime.utcnow().isoformat(),
        "config": {
            "num_products": config.num_products,
            "num_reviews": config.num_reviews,
            "num_users": config.num_users,
            "num_interactions": config.num_interactions,
            "random_seed": config.random_seed,
            "generate_embeddings": config.generate_embeddings,
            "embedding_model": config.embedding_model if config.generate_embeddings else None
        },
        "products": {
            "count": len(products),
            "category_distribution": category_distribution,
            "price_stats": price_stats
        },
        "reviews": results["statistics"].get("reviews", {}),
        "users": results["statistics"].get("users", {}),
        "interactions": results["statistics"].get("interactions", {}),
        "consistency": consistency_service.get_statistics()
    }
    
    exporter.export_metadata(metadata)
    results["statistics"]["metadata"] = metadata
    
    return results


def print_summary(results: Dict[str, Any]) -> None:
    """Print a summary of the generation results."""
    print("\n" + "=" * 70)
    print("                    FINFIND DATA GENERATION SUMMARY")
    print("=" * 70)
    
    products = results.get("products", [])
    reviews = results.get("reviews", [])
    users = results.get("users", [])
    interactions = results.get("interactions", [])
    stats = results.get("statistics", {})
    validation = results.get("validation", {})
    
    # Products
    print(f"\n📦 PRODUCTS: {len(products)}")
    if products:
        categories = {}
        for p in products:
            categories[p.category] = categories.get(p.category, 0) + 1
        print("   Category Distribution:")
        for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
            print(f"   - {cat}: {count} ({count/len(products)*100:.1f}%)")
    
    # Reviews
    print(f"\n⭐ REVIEWS: {len(reviews)}")
    if stats.get("reviews"):
        rs = stats["reviews"]
        print(f"   Average Rating: {rs.get('average_rating', 'N/A')}")
        print(f"   Verified Purchases: {rs.get('verified_purchase_pct', 0)}%")
    
    # Users
    print(f"\n👤 USER PROFILES: {len(users)}")
    if stats.get("users"):
        us = stats["users"]
        print(f"   Personas: {us.get('personas', {})}")
        fm = us.get("financial_metrics", {})
        print(f"   Avg Budget: ${fm.get('avg_budget_min', 0):.0f} - ${fm.get('avg_budget_max', 0):.0f}")
        print(f"   Avg Affordability Score: {fm.get('avg_affordability', 0):.2f}")
    
    # Interactions
    print(f"\n🔄 INTERACTIONS: {len(interactions)}")
    if stats.get("interactions"):
        ist = stats["interactions"]
        print(f"   Unique Sessions: {ist.get('unique_sessions', 0)}")
        print(f"   Conversions: {ist.get('conversions', 0)}")
        print(f"   Types: {ist.get('interaction_types', {})}")
        queries = ist.get("search_queries", [])[:5]
        if queries:
            print("   Sample Queries:")
            for q in queries:
                print(f"     • \"{q}\"")
    
    # Validation
    print(f"\n✅ VALIDATION:")
    for key, passed in validation.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"   {key.capitalize()}: {status}")
    
    # Output files
    print("\n📁 OUTPUT FILES:")
    print("   output/")
    print("   ├── products.json")
    print("   ├── products_with_reviews.json")
    print("   ├── reviews.json")
    print("   ├── user_profiles.json")
    print("   ├── user_interactions.json")
    print("   ├── metadata.json")
    if results.get("statistics", {}).get("metadata", {}).get("config", {}).get("generate_embeddings"):
        print("   ├── *_qdrant.json (for Qdrant upload)")
    
    print("\n" + "=" * 70 + "\n")


def main():
    """Main entry point."""
    args = parse_args()
    
    logger.info("Starting FinFind Data Generation")
    logger.info(f"Products: {args.products}, Reviews: {args.reviews}, "
                f"Users: {args.users}, Interactions: {args.interactions}")
    logger.info(f"Output directory: {args.output_dir}")
    logger.info(f"Embeddings: {'Disabled' if args.no_embeddings else 'Enabled'}")
    
    start_time = datetime.now()
    
    # Create configuration
    config = GenerationConfig(
        num_products=args.products,
        num_reviews=args.reviews,
        num_users=args.users,
        num_interactions=args.interactions,
        random_seed=args.seed,
        generate_embeddings=not args.no_embeddings,
        output_dir=Path(args.output_dir)
    )
    
    try:
        # Generate data
        results = generate_all_data(config, args)
        
        # Print summary
        print_summary(results)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"Generation completed in {duration:.2f} seconds")
        
        # Check validation
        if not all(results.get("validation", {}).values()):
            logger.error("Some validations failed!")
            sys.exit(1)
        
    except Exception as e:
        logger.exception(f"Generation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
