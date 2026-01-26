#!/usr/bin/env python3
"""Test all FinFind APIs."""

import requests
import json

BASE = 'http://localhost:8000'

# Get actual IDs from Qdrant
def get_sample_ids():
    """Fetch actual IDs from Qdrant collections."""
    from app.agents.services.qdrant_service import get_qdrant_service
    qdrant = get_qdrant_service()
    
    products = qdrant.scroll('products', limit=1)
    users = qdrant.scroll('user_profiles', limit=1)
    
    product_id = products[0]['id'] if products else None
    user_id = users[0]['id'] if users else None
    
    return product_id, user_id

def test(name, method, url, data=None, params=None):
    """Test an API endpoint."""
    try:
        if method == 'GET':
            r = requests.get(url, params=params, timeout=15)
        else:
            r = requests.post(url, json=data, timeout=60)
        ok = r.status_code in [200, 201]
        symbol = "✓" if ok else "✗"
        print(f"{symbol} {name}: {r.status_code}")
        if ok:
            resp = r.json()
            if isinstance(resp, dict):
                print(f"   Keys: {list(resp.keys())[:6]}")
                # Show counts for data endpoints
                for key in ['products', 'results', 'recommendations', 'alternatives']:
                    if key in resp and isinstance(resp[key], list):
                        print(f"   {key.capitalize()}: {len(resp[key])} items")
            elif isinstance(resp, list):
                print(f"   Items: {len(resp)}")
        else:
            print(f"   Error: {r.text[:150]}")
        return ok, r
    except Exception as e:
        print(f"✗ {name}: {e}")
        return False, None


def main():
    results = {"passed": 0, "failed": 0}
    
    print("=" * 65)
    print("              FINFIND API TEST SUITE")
    print("=" * 65)
    
    # Get actual IDs
    print("\n📋 Getting sample IDs from Qdrant...")
    product_id, user_id = get_sample_ids()
    print(f"   Product ID: {product_id[:20]}..." if product_id else "   No products found")
    print(f"   User ID: {user_id[:20]}..." if user_id else "   No users found")
    
    # ============================================
    # HEALTH & ROOT
    # ============================================
    print("\n📍 HEALTH & ROOT")
    print("-" * 40)
    
    ok, _ = test("Health Check", "GET", f"{BASE}/health")
    results["passed" if ok else "failed"] += 1
    
    ok, _ = test("Root Endpoint", "GET", f"{BASE}/")
    results["passed" if ok else "failed"] += 1
    
    # ============================================
    # SEARCH APIs
    # ============================================
    print("\n🔍 SEARCH APIs")
    print("-" * 40)
    
    ok, _ = test("Search Products", "GET", f"{BASE}/api/v1/search/products", 
                 params={"q": "laptop", "limit": 5})
    results["passed" if ok else "failed"] += 1
    
    ok, _ = test("Search Suggestions", "GET", f"{BASE}/api/v1/search/suggest", 
                 params={"q": "head"})
    results["passed" if ok else "failed"] += 1
    
    ok, _ = test("Get Categories", "GET", f"{BASE}/api/v1/search/categories")
    results["passed" if ok else "failed"] += 1
    
    ok, _ = test("Get Brands", "GET", f"{BASE}/api/v1/search/brands")
    results["passed" if ok else "failed"] += 1
    
    # ============================================
    # AGENTS APIs
    # ============================================
    print("\n🤖 AGENTS APIs")
    print("-" * 40)
    
    ok, _ = test("List Agents", "GET", f"{BASE}/api/v1/agents/list")
    results["passed" if ok else "failed"] += 1
    
    ok, _ = test("Agents Health", "GET", f"{BASE}/api/v1/agents/health")
    results["passed" if ok else "failed"] += 1
    
    # Agent Query (orchestrator) - this works based on previous test
    ok, _ = test("Agent Query (Orchestrator)", "POST", f"{BASE}/api/v1/agents/query",
                 data={
                     "query": "I need a good laptop for programming under $800"
                 })
    results["passed" if ok else "failed"] += 1
    
    # ============================================
    # USERS APIs
    # ============================================
    print("\n👤 USERS APIs")
    print("-" * 40)
    
    if user_id:
        ok, _ = test("Get User Profile", "GET", f"{BASE}/api/v1/users/{user_id}/profile")
        results["passed" if ok else "failed"] += 1
    else:
        print("✗ Get User Profile: Skipped (no users)")
        results["failed"] += 1
    
    # ============================================
    # PRODUCTS APIs
    # ============================================
    print("\n📦 PRODUCTS APIs")
    print("-" * 40)
    
    if product_id:
        ok, _ = test("Get Product by ID", "GET", f"{BASE}/api/v1/products/{product_id}")
        results["passed" if ok else "failed"] += 1
    else:
        print("✗ Get Product by ID: Skipped (no products)")
        results["failed"] += 1
    
    # ============================================
    # RECOMMENDATIONS APIs
    # ============================================
    print("\n⭐ RECOMMENDATIONS APIs")
    print("-" * 40)
    
    if user_id:
        ok, _ = test("Get Recommendations", "GET", f"{BASE}/api/v1/recommendations/{user_id}",
                     params={"limit": 5})
        results["passed" if ok else "failed"] += 1
    else:
        print("✗ Get Recommendations: Skipped (no users)")
        results["failed"] += 1
    
    # ============================================
    # SUMMARY
    # ============================================
    print("\n" + "=" * 65)
    print("                    TEST SUMMARY")
    print("=" * 65)
    total = results["passed"] + results["failed"]
    print(f"\n   ✓ Passed: {results['passed']}/{total}")
    print(f"   ✗ Failed: {results['failed']}/{total}")
    pct = (results["passed"] / total * 100) if total > 0 else 0
    print(f"\n   Success Rate: {pct:.1f}%")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
