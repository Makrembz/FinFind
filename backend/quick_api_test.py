"""
Quick API data validation test - checks that APIs return real data, not 'Unknown' or null values.
Run from backend directory: python quick_api_test.py
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_api(name, url, check_func, params=None, method='GET', json_body=None):
    """Test an API endpoint and validate data."""
    try:
        if method == 'GET':
            resp = requests.get(url, params=params, timeout=30)
        else:
            resp = requests.post(url, json=json_body, timeout=30)
        
        data = resp.json()
        
        if data.get('error'):
            print(f"❌ {name}: Error - {data['error'].get('message', data['error'])}")
            return False
        
        result, details = check_func(data)
        if result:
            print(f"✅ {name}: {details}")
            return True
        else:
            print(f"❌ {name}: {details}")
            return False
            
    except Exception as e:
        print(f"❌ {name}: Exception - {str(e)}")
        return False

def main():
    print("\n" + "="*60)
    print("FinFind API Data Validation Test")
    print("="*60 + "\n")
    
    results = []
    
    # 1. Search Products
    def check_search(data):
        products = data.get('products', [])
        if not products:
            return False, "No products returned"
        p = products[0]
        name = p.get('name', 'Unknown')
        if name == 'Unknown' or not name:
            return False, "Product name is Unknown or empty"
        return True, f"Found {len(products)} products, first: '{name[:40]}...'"
    
    results.append(test_api(
        "Search Products",
        f"{BASE_URL}/search/products",
        check_search,
        params={"q": "laptop", "limit": 2}
    ))
    
    # 2. Categories
    def check_categories(data):
        cats = data.get('categories', [])
        if not cats:
            return False, "No categories"
        return True, f"Found {len(cats)} categories: {cats[:3]}"
    
    results.append(test_api(
        "Categories",
        f"{BASE_URL}/search/categories",
        check_categories
    ))
    
    # 3. Brands
    def check_brands(data):
        brands = data.get('brands', [])
        if not brands:
            return False, "No brands"
        return True, f"Found {len(brands)} brands: {brands[:3]}"
    
    results.append(test_api(
        "Brands",
        f"{BASE_URL}/search/brands",
        check_brands
    ))
    
    # 4. Product Details - need product ID first
    search_resp = requests.get(f"{BASE_URL}/search/products", params={"q": "test", "limit": 1}).json()
    if search_resp.get('products'):
        product_id = search_resp['products'][0]['id']
        
        def check_product(data):
            prod = data.get('product', {})
            name = prod.get('name', 'Unknown')
            price = prod.get('price', 0)
            if name == 'Unknown' or not name:
                return False, "Product name is Unknown"
            return True, f"'{name[:40]}...' - ${price}"
        
        results.append(test_api(
            "Product Details",
            f"{BASE_URL}/products/{product_id}",
            check_product
        ))
    
    # 5. User Profile - need user ID
    from app.agents.services.qdrant_service import get_qdrant_service
    qdrant = get_qdrant_service()
    users = qdrant.scroll(collection='user_profiles', limit=1)
    
    if users:
        user_id = users[0].get('id')
        
        def check_user(data):
            profile = data.get('profile', {})
            name = profile.get('name', 'Unknown')
            budget = profile.get('financial_profile', {}).get('monthly_budget', 0)
            if name == 'Unknown' or not name:
                return False, "User name is Unknown"
            return True, f"'{name}' - Budget: ${budget}"
        
        results.append(test_api(
            "User Profile",
            f"{BASE_URL}/users/{user_id}/profile",
            check_user
        ))
        
        # 6. Recommendations
        def check_recs(data):
            recs = data.get('recommendations', [])
            if not recs:
                return False, "No recommendations"
            r = recs[0]
            name = r.get('name', 'Unknown')
            if name == 'Unknown' or not name:
                return False, "Recommendation name is Unknown"
            return True, f"Found {len(recs)} recs, first: '{name[:40]}...'"
        
        results.append(test_api(
            "Recommendations",
            f"{BASE_URL}/recommendations/{user_id}",
            check_recs,
            params={"limit": 2}
        ))
    
    # Summary
    print("\n" + "="*60)
    passed = sum(results)
    total = len(results)
    print(f"SUMMARY: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print("="*60)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
