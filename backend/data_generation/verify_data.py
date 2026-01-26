#!/usr/bin/env python3
"""
Verification script for generated data.

Validates the quality and consistency of generated synthetic data
before uploading to Qdrant.

Usage:
    python verify_data.py [--input-dir DIR]
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any
from collections import Counter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_json_file(filepath: Path) -> Dict:
    """Load and parse a JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def verify_products(products_data: Dict) -> Dict[str, Any]:
    """Verify product data quality."""
    items = products_data.get('items', [])
    
    results = {
        "count": len(items),
        "issues": [],
        "statistics": {}
    }
    
    if not items:
        results["issues"].append("No products found")
        return results
    
    # Check for required fields
    required_fields = ['id', 'title', 'description', 'category', 'price', 'brand']
    missing_fields = Counter()
    
    # Collect statistics
    categories = Counter()
    brands = Counter()
    prices = []
    title_lengths = []
    desc_lengths = []
    with_embeddings = 0
    
    for i, product in enumerate(items):
        # Check required fields
        for field in required_fields:
            if field not in product or not product[field]:
                missing_fields[field] += 1
        
        # Collect stats
        if product.get('category'):
            categories[product['category']] += 1
        if product.get('brand'):
            brands[product['brand']] += 1
        if product.get('price'):
            prices.append(product['price'])
        if product.get('title'):
            title_lengths.append(len(product['title']))
        if product.get('description'):
            desc_lengths.append(len(product['description']))
        if product.get('embedding') and len(product['embedding']) > 0:
            with_embeddings += 1
    
    # Report missing fields
    for field, count in missing_fields.items():
        if count > 0:
            results["issues"].append(f"Missing '{field}' in {count} products")
    
    # Calculate statistics
    results["statistics"] = {
        "total_products": len(items),
        "unique_categories": len(categories),
        "unique_brands": len(brands),
        "category_distribution": dict(categories.most_common(10)),
        "top_brands": dict(brands.most_common(10)),
        "price_range": {
            "min": min(prices) if prices else 0,
            "max": max(prices) if prices else 0,
            "avg": sum(prices) / len(prices) if prices else 0
        },
        "title_length": {
            "min": min(title_lengths) if title_lengths else 0,
            "max": max(title_lengths) if title_lengths else 0,
            "avg": sum(title_lengths) / len(title_lengths) if title_lengths else 0
        },
        "description_length": {
            "min": min(desc_lengths) if desc_lengths else 0,
            "max": max(desc_lengths) if desc_lengths else 0,
            "avg": sum(desc_lengths) / len(desc_lengths) if desc_lengths else 0
        },
        "with_embeddings": with_embeddings,
        "embedding_coverage": f"{with_embeddings / len(items) * 100:.1f}%" if items else "0%"
    }
    
    # Quality checks
    if len(categories) < 3:
        results["issues"].append(f"Low category diversity: only {len(categories)} categories")
    
    if prices and (max(prices) - min(prices)) < 100:
        results["issues"].append("Low price diversity: narrow price range")
    
    avg_desc_len = results["statistics"]["description_length"]["avg"]
    if avg_desc_len < 100:
        results["issues"].append(f"Short descriptions: avg {avg_desc_len:.0f} chars")
    
    return results


def verify_reviews(reviews_data: Dict, product_ids: set) -> Dict[str, Any]:
    """Verify review data quality."""
    items = reviews_data.get('items', [])
    
    results = {
        "count": len(items),
        "issues": [],
        "statistics": {}
    }
    
    if not items:
        results["issues"].append("No reviews found")
        return results
    
    # Check for required fields
    required_fields = ['review_id', 'product_id', 'rating', 'text']
    missing_fields = Counter()
    
    # Collect statistics
    ratings = Counter()
    sentiments = Counter()
    text_lengths = []
    verified_count = 0
    invalid_product_refs = 0
    with_embeddings = 0
    
    for review in items:
        # Check required fields
        for field in required_fields:
            if field not in review or review[field] is None:
                missing_fields[field] += 1
        
        # Check product reference
        if review.get('product_id') and review['product_id'] not in product_ids:
            invalid_product_refs += 1
        
        # Collect stats
        if review.get('rating'):
            ratings[review['rating']] += 1
        if review.get('sentiment'):
            sentiments[review['sentiment']] += 1
        if review.get('text'):
            text_lengths.append(len(review['text']))
        if review.get('verified_purchase'):
            verified_count += 1
        if review.get('embedding') and len(review['embedding']) > 0:
            with_embeddings += 1
    
    # Report missing fields
    for field, count in missing_fields.items():
        if count > 0:
            results["issues"].append(f"Missing '{field}' in {count} reviews")
    
    if invalid_product_refs > 0:
        results["issues"].append(f"{invalid_product_refs} reviews reference non-existent products")
    
    # Calculate statistics
    results["statistics"] = {
        "total_reviews": len(items),
        "rating_distribution": dict(sorted(ratings.items())),
        "sentiment_distribution": dict(sentiments),
        "average_rating": sum(r * c for r, c in ratings.items()) / len(items) if items else 0,
        "verified_purchases": verified_count,
        "verified_percentage": f"{verified_count / len(items) * 100:.1f}%" if items else "0%",
        "text_length": {
            "min": min(text_lengths) if text_lengths else 0,
            "max": max(text_lengths) if text_lengths else 0,
            "avg": sum(text_lengths) / len(text_lengths) if text_lengths else 0
        },
        "with_embeddings": with_embeddings,
        "embedding_coverage": f"{with_embeddings / len(items) * 100:.1f}%" if items else "0%",
        "unique_products_reviewed": len(set(r.get('product_id') for r in items if r.get('product_id')))
    }
    
    # Quality checks
    if ratings:
        # Check rating distribution is realistic
        five_star_pct = ratings.get(5, 0) / len(items) * 100
        one_star_pct = ratings.get(1, 0) / len(items) * 100
        
        if five_star_pct > 60:
            results["issues"].append(f"Unrealistic rating distribution: {five_star_pct:.1f}% 5-star reviews")
        if one_star_pct > 20:
            results["issues"].append(f"High negative reviews: {one_star_pct:.1f}% 1-star reviews")
    
    avg_text_len = results["statistics"]["text_length"]["avg"]
    if avg_text_len < 50:
        results["issues"].append(f"Short review texts: avg {avg_text_len:.0f} chars")
    
    return results


def print_verification_report(products_result: Dict, reviews_result: Dict) -> bool:
    """Print verification report and return success status."""
    print("\n" + "=" * 70)
    print("DATA VERIFICATION REPORT")
    print("=" * 70)
    
    all_passed = True
    
    # Products section
    print("\n📦 PRODUCTS")
    print("-" * 50)
    print(f"   Total: {products_result['count']}")
    
    stats = products_result.get('statistics', {})
    if stats:
        print(f"   Categories: {stats.get('unique_categories', 0)}")
        print(f"   Brands: {stats.get('unique_brands', 0)}")
        print(f"   Price Range: ${stats.get('price_range', {}).get('min', 0):.2f} - ${stats.get('price_range', {}).get('max', 0):.2f}")
        print(f"   Avg Description: {stats.get('description_length', {}).get('avg', 0):.0f} chars")
        print(f"   Embeddings: {stats.get('embedding_coverage', '0%')}")
        print("\n   Category Distribution:")
        for cat, count in stats.get('category_distribution', {}).items():
            pct = count / products_result['count'] * 100 if products_result['count'] else 0
            print(f"      - {cat}: {count} ({pct:.1f}%)")
    
    if products_result['issues']:
        print("\n   ⚠️  Issues:")
        for issue in products_result['issues']:
            print(f"      - {issue}")
        all_passed = False
    else:
        print("\n   ✅ All checks passed")
    
    # Reviews section
    print("\n⭐ REVIEWS")
    print("-" * 50)
    print(f"   Total: {reviews_result['count']}")
    
    stats = reviews_result.get('statistics', {})
    if stats:
        print(f"   Average Rating: {stats.get('average_rating', 0):.2f}")
        print(f"   Verified: {stats.get('verified_percentage', '0%')}")
        print(f"   Products Reviewed: {stats.get('unique_products_reviewed', 0)}")
        print(f"   Avg Text Length: {stats.get('text_length', {}).get('avg', 0):.0f} chars")
        print(f"   Embeddings: {stats.get('embedding_coverage', '0%')}")
        print("\n   Rating Distribution:")
        for rating, count in sorted(stats.get('rating_distribution', {}).items()):
            pct = count / reviews_result['count'] * 100 if reviews_result['count'] else 0
            stars = "⭐" * int(rating)
            print(f"      {stars}: {count} ({pct:.1f}%)")
        print("\n   Sentiment Distribution:")
        for sentiment, count in stats.get('sentiment_distribution', {}).items():
            pct = count / reviews_result['count'] * 100 if reviews_result['count'] else 0
            emoji = {"positive": "😊", "neutral": "😐", "negative": "😞"}.get(sentiment, "")
            print(f"      {emoji} {sentiment}: {count} ({pct:.1f}%)")
    
    if reviews_result['issues']:
        print("\n   ⚠️  Issues:")
        for issue in reviews_result['issues']:
            print(f"      - {issue}")
        all_passed = False
    else:
        print("\n   ✅ All checks passed")
    
    # Summary
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ VERIFICATION PASSED - Data is ready for upload")
    else:
        print("⚠️  VERIFICATION COMPLETED WITH WARNINGS - Review issues above")
    print("=" * 70 + "\n")
    
    return all_passed


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Verify generated data")
    parser.add_argument(
        '--input-dir', '-i',
        type=str,
        default='output',
        help='Directory containing generated data (default: output)'
    )
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir)
    
    if not input_dir.exists():
        logger.error(f"Input directory not found: {input_dir}")
        sys.exit(1)
    
    # Load data
    products_file = input_dir / 'products.json'
    reviews_file = input_dir / 'reviews.json'
    
    if not products_file.exists():
        logger.error(f"Products file not found: {products_file}")
        sys.exit(1)
    
    logger.info("Loading products data...")
    products_data = load_json_file(products_file)
    
    # Get product IDs for review validation
    product_ids = set()
    for item in products_data.get('items', []):
        if item.get('id'):
            product_ids.add(item['id'])
    
    logger.info(f"Loaded {len(product_ids)} products")
    
    # Verify products
    logger.info("Verifying products...")
    products_result = verify_products(products_data)
    
    # Verify reviews if file exists
    reviews_result = {"count": 0, "issues": ["Reviews file not found"], "statistics": {}}
    if reviews_file.exists():
        logger.info("Loading reviews data...")
        reviews_data = load_json_file(reviews_file)
        logger.info(f"Loaded {len(reviews_data.get('items', []))} reviews")
        
        logger.info("Verifying reviews...")
        reviews_result = verify_reviews(reviews_data, product_ids)
    
    # Print report
    success = print_verification_report(products_result, reviews_result)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
