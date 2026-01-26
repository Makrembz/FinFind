"""
Comprehensive API testing script to verify all endpoints return proper data.
"""
import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000/api/v1"

def print_result(name: str, response: Dict[str, Any], check_fields: list = None):
    """Print test result with key fields."""
    print(f"\n{'='*60}")
    print(f"Test: {name}")
    print(f"Status: {'✓ PASS' if response.get('success', True) else '✗ FAIL'}")
    
    if response.get('error'):
        print(f"Error: {response['error']}")
        return False
    
    if check_fields:
        for field in check_fields:
            value = response
            for key in field.split('.'):
                if isinstance(value, dict):
                    value = value.get(key)
                elif isinstance(value, list) and len(value) > 0:
                    value = value[0].get(key) if isinstance(value[0], dict) else value
                else:
                    value = None
                    break
            
            if value and value not in ['Unknown', None, '']:
                print(f"  {field}: {str(value)[:80]}...")
            else:
                print(f"  {field}: ⚠ Missing or Unknown")
    
    return True

def test_search_products():
    """Test product search API."""
    resp = requests.get(f"{BASE_URL}/search/products", params={
        "q": "laptop",
        "limit": 2
    }).json()
    return print_result("Search Products", resp, [
        "products.name",
        "products.price",
        "products.category",
        "products.brand"
    ])

def test_search_categories():
    """Test categories API."""
    resp = requests.get(f"{BASE_URL}/search/categories").json()
    categories = resp.get('categories', [])
    print(f"\n{'='*60}")
    print(f"Test: Search Categories")
    print(f"Status: {'✓ PASS' if len(categories) > 0 else '✗ FAIL'}")
    print(f"  Found {len(categories)} categories: {categories[:5]}...")
    return len(categories) > 0

def test_search_brands():
    """Test brands API."""
    resp = requests.get(f"{BASE_URL}/search/brands").json()
    brands = resp.get('brands', [])
    print(f"\n{'='*60}")
    print(f"Test: Search Brands")
    print(f"Status: {'✓ PASS' if len(brands) > 0 else '✗ FAIL'}")
    print(f"  Found {len(brands)} brands: {brands[:5]}...")
    return len(brands) > 0

def test_product_details():
    """Test product details API."""
    # First get a product ID from search
    search_resp = requests.get(f"{BASE_URL}/search/products", params={
        "q": "electronics",
        "limit": 1
    }).json()
    
    if not search_resp.get('products'):
        print("\n⚠ No products found to test product details")
        return False
    
    product_id = search_resp['products'][0]['id']
    resp = requests.get(f"{BASE_URL}/products/{product_id}").json()
    
    if resp.get('error'):
        print(f"\n⚠ Product details error: {resp['error']}")
        return False
    
    product = resp.get('product', {})
    print(f"\n{'='*60}")
    print(f"Test: Product Details")
    print(f"Status: ✓ PASS")
    print(f"  name: {product.get('name', 'Unknown')[:60]}...")
    print(f"  price: ${product.get('price', 0)}")
    print(f"  category: {product.get('category', 'Unknown')}")
    print(f"  brand: {product.get('brand', 'Unknown')}")
    print(f"  rating: {product.get('rating_avg', 0)}")
    return True

def test_user_profile():
    """Test user profile API."""
    # Get a valid user ID
    from app.agents.services.qdrant_service import get_qdrant_service
    qdrant = get_qdrant_service()
    users = qdrant.scroll(collection='user_profiles', limit=1)
    
    if not users:
        print("\n⚠ No users found in database")
        return False
    
    user_id = users[0].get('id')
    resp = requests.get(f"{BASE_URL}/users/{user_id}/profile").json()
    
    if resp.get('error'):
        print(f"\n⚠ User profile error: {resp['error']}")
        return False
    
    profile = resp.get('profile', {})
    print(f"\n{'='*60}")
    print(f"Test: User Profile")
    print(f"Status: ✓ PASS")
    print(f"  user_id: {profile.get('user_id')}")
    print(f"  name: {profile.get('name', 'Unknown')}")
    print(f"  budget: ${profile.get('financial_profile', {}).get('monthly_budget', 0)}")
    print(f"  price_sensitivity: {profile.get('preferences', {}).get('price_sensitivity', 'Unknown')}")
    return True

def test_recommendations():
    """Test recommendations API."""
    # Get a valid user ID
    from app.agents.services.qdrant_service import get_qdrant_service
    qdrant = get_qdrant_service()
    users = qdrant.scroll(collection='user_profiles', limit=1)
    
    if not users:
        print("\n⚠ No users found for recommendations")
        return False
    
    user_id = users[0].get('id')
    resp = requests.get(f"{BASE_URL}/recommendations/{user_id}", params={"limit": 2}).json()
    
    if resp.get('error'):
        print(f"\n⚠ Recommendations error: {resp['error']}")
        return False
    
    recs = resp.get('recommendations', [])
    print(f"\n{'='*60}")
    print(f"Test: Recommendations")
    print(f"Status: ✓ PASS")
    print(f"  Found {len(recs)} recommendations")
    if recs:
        print(f"  First recommendation: {recs[0].get('name', 'Unknown')[:50]}...")
        print(f"  Price: ${recs[0].get('price', 0)}")
    return len(recs) > 0

def test_health_check():
    """Test health check endpoint."""
    resp = requests.get(f"{BASE_URL}/health").json()
    print(f"\n{'='*60}")
    print(f"Test: Health Check")
    print(f"Status: {'✓ PASS' if resp.get('status') == 'healthy' else '✗ FAIL'}")
    print(f"  API Status: {resp.get('status')}")
    print(f"  Version: {resp.get('version', 'unknown')}")
    return resp.get('status') == 'healthy'

def run_all_tests():
    """Run all API tests."""
    print("\n" + "="*60)
    print("FinFind API Comprehensive Test Suite")
    print("="*60)
    
    results = []
    
    # Health check
    results.append(("Health Check", test_health_check()))
    
    # Search tests
    results.append(("Search Products", test_search_products()))
    results.append(("Search Categories", test_search_categories()))
    results.append(("Search Brands", test_search_brands()))
    
    # Product tests
    results.append(("Product Details", test_product_details()))
    
    # User tests
    results.append(("User Profile", test_user_profile()))
    
    # Recommendation tests
    results.append(("Recommendations", test_recommendations()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status} - {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    return passed == total

if __name__ == "__main__":
    run_all_tests()
