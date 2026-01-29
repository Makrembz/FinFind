#!/usr/bin/env python3
"""
Comprehensive API Test Script for FinFind Backend
Tests all endpoints with real data from Qdrant
"""
import requests
import json
from typing import Dict, Any, List, Tuple

BASE_URL = "http://localhost:8000/api/v1"

def test_endpoint(name: str, method: str, url: str, **kwargs) -> Tuple[bool, str, Any]:
    """Test a single endpoint and return success status, message, and response data."""
    try:
        response = requests.request(method, url, timeout=30, **kwargs)
        data = response.json() if response.text else {}
        if response.status_code in [200, 201]:
            return True, f"✓ {name}: OK ({response.status_code})", data
        else:
            error = data.get("error", {}).get("message", data.get("detail", str(response.text)[:100]))
            return False, f"✗ {name}: {response.status_code} - {error}", data
    except Exception as e:
        return False, f"✗ {name}: Error - {str(e)[:100]}", None

def run_tests():
    """Run all API tests."""
    results = []
    
    # Use real IDs from the Qdrant database (UUIDs)
    USER_ID = "013c3cb2-482a-55b0-9559-6688c3b78313"  # luxury_shopper
    PRODUCT_ID = "02308d23-3611-5cf3-81bf-169d137f9a2b"  # Vitamix blender
    
    print("=" * 70)
    print("FINFIND API COMPREHENSIVE TEST")
    print("=" * 70)
    print(f"Base URL: {BASE_URL}")
    print(f"Test User ID: {USER_ID}")
    print(f"Test Product ID: {PRODUCT_ID}")
    print("=" * 70)
    
    # 1. Health endpoints
    print("\n1. HEALTH ENDPOINTS")
    results.append(test_endpoint("Health Check", "GET", f"{BASE_URL.replace('/api/v1', '')}/health"))
    results.append(test_endpoint("Root Endpoint", "GET", BASE_URL.replace("/api/v1", "/")))
    
    # 2. Search endpoints
    print("\n2. SEARCH ENDPOINTS")
    results.append(test_endpoint("Search Products", "GET", f"{BASE_URL}/search/products?q=laptop"))
    results.append(test_endpoint("Search Suggestions", "GET", f"{BASE_URL}/search/suggest?q=app"))
    results.append(test_endpoint("Get Categories", "GET", f"{BASE_URL}/search/categories"))
    results.append(test_endpoint("Get Brands", "GET", f"{BASE_URL}/search/brands"))
    
    # 3. User endpoints
    print("\n3. USER ENDPOINTS")
    results.append(test_endpoint("Get User Profile", "GET", f"{BASE_URL}/users/{USER_ID}/profile"))
    results.append(test_endpoint("Update User Profile", "PUT", f"{BASE_URL}/users/{USER_ID}/profile", 
        json={"preferences": {"favorite_categories": ["Electronics", "Fashion"]}}))
    
    # 4. Product endpoints
    print("\n4. PRODUCT ENDPOINTS")
    results.append(test_endpoint("Get Product", "GET", f"{BASE_URL}/products/{PRODUCT_ID}"))
    results.append(test_endpoint("Get Product Reviews", "GET", f"{BASE_URL}/products/{PRODUCT_ID}/reviews"))
    results.append(test_endpoint("Get Similar Products", "GET", f"{BASE_URL}/products/{PRODUCT_ID}/similar"))
    
    # 5. Recommendations endpoints
    print("\n5. RECOMMENDATION ENDPOINTS")
    ok, msg, data = test_endpoint("Get Recommendations", "GET", f"{BASE_URL}/recommendations/{USER_ID}")
    results.append((ok, msg, data))
    
    # Get a recommended product ID for further testing
    rec_product_id = None
    if ok and data and data.get("recommendations"):
        rec_product_id = data["recommendations"][0]["id"]
        print(f"   Using recommended product: {rec_product_id}")
    
    if rec_product_id:
        results.append(test_endpoint("Explain Recommendation", "POST", f"{BASE_URL}/recommendations/explain",
            json={"user_id": USER_ID, "product_id": rec_product_id}))
        results.append(test_endpoint("Get Alternatives", "GET", f"{BASE_URL}/recommendations/alternatives/{rec_product_id}"))
    else:
        results.append((False, "✗ Explain Recommendation: Skipped (no product)", None))
        results.append((False, "✗ Get Alternatives: Skipped (no product)", None))
    
    # 6. Agent endpoints
    print("\n6. AGENT ENDPOINTS")
    results.append(test_endpoint("List Agents", "GET", f"{BASE_URL}/agents/list"))
    results.append(test_endpoint("Agent Health", "GET", f"{BASE_URL}/agents/health"))
    
    # Test agent query
    results.append(test_endpoint("Agent Query", "POST", f"{BASE_URL}/agents/query",
        json={"query": "Find affordable laptops", "user_id": USER_ID}))
    
    # Test session management
    ok, msg, session_data = test_endpoint("Create Session", "POST", f"{BASE_URL}/agents/session",
        json={"user_id": USER_ID})
    results.append((ok, msg, session_data))
    
    if ok and session_data and session_data.get("sessionId"):
        session_id = session_data["sessionId"]
        results.append(test_endpoint("Get Session", "GET", f"{BASE_URL}/agents/session/{session_id}"))
    else:
        results.append((False, "✗ Get Session: Skipped (no session)", None))
    
    # 7. Workflow endpoints
    print("\n7. WORKFLOW ENDPOINTS")
    results.append(test_endpoint("List Workflows", "GET", f"{BASE_URL}/workflows"))
    
    # 8. Learning endpoints
    print("\n8. LEARNING ENDPOINTS")
    results.append(test_endpoint("Track Click", "POST", f"{BASE_URL}/learning/track/click",
        json={"product_id": PRODUCT_ID, "position": 1, "items_shown": [PRODUCT_ID]}))
    results.append(test_endpoint("Learning Dashboard", "GET", f"{BASE_URL}/learning/dashboard"))
    results.append(test_endpoint("Learning Status", "GET", f"{BASE_URL}/learning/status"))
    
    # Print results
    print("\n" + "=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for success, _, _ in results if success)
    total = len(results)
    
    for success, message, _ in results:
        print(message)
    
    print(f"\n✓ Passed: {passed}/{total}")
    print(f"✗ Failed: {total - passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    print("=" * 70)
    
    return passed == total

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
