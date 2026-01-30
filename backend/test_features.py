"""Test all FinFind features."""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_endpoint(name, method, url, data=None):
    """Test an endpoint and print results."""
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    try:
        if method == "GET":
            r = requests.get(url, timeout=30)
        else:
            r = requests.post(url, json=data, timeout=30)
        
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            result = r.json()
            print(f"  Response: {json.dumps(result, indent=2, default=str)[:800]}")
        else:
            print(f"  Error: {r.text[:500]}")
        return r.status_code == 200
    except Exception as e:
        print(f"  Error: {e}")
        return False


print("\n" + "="*60)
print("  FINFIND FEATURE TESTING")
print("="*60)

results = {}

# 1. Health check
results["Health"] = test_endpoint(
    "1. Health Check",
    "GET",
    f"{BASE_URL.replace('/api/v1', '')}/health"
)

# 2. Search products first to get a product ID
print("\n" + "="*60)
print("  2. Search Products (to get product ID)")
print("="*60)
search_resp = requests.post(f"{BASE_URL}/search/products", json={"query": "laptop", "limit": 3})
product_id = None
if search_resp.status_code == 200:
    products = search_resp.json().get("products", [])
    if products:
        product_id = products[0]["id"]
        print(f"  Found product: {products[0]['name'][:50]}")
        print(f"  Product ID: {product_id}")
        results["Search"] = True
    else:
        results["Search"] = False
else:
    results["Search"] = False

# 3. Alternative products (uses the product ID)
if product_id:
    results["Alternatives"] = test_endpoint(
        "3. Alternative Products",
        "GET",
        f"{BASE_URL}/recommendations/alternatives/{product_id}?limit=3&criteria=cheaper"
    )
else:
    results["Alternatives"] = False

# 4. Similar products
if product_id:
    results["Similar"] = test_endpoint(
        "4. Similar Products",
        "GET",
        f"{BASE_URL}/products/{product_id}/similar?limit=3"
    )
else:
    results["Similar"] = False

# 5. Search Suggestions
results["Suggestions"] = test_endpoint(
    "5. Search Suggestions",
    "GET",
    f"{BASE_URL}/search/suggest?q=laptop"
)

# 6. Agent query (uses LLM)
results["Agent"] = test_endpoint(
    "6. Agent Query (LLM)",
    "POST",
    f"{BASE_URL}/agents/query",
    {"query": "find me a laptop for programming under $2000", "include_explanations": True}
)

# 7. List agents
results["Agents List"] = test_endpoint(
    "7. List Available Agents",
    "GET",
    f"{BASE_URL}/agents/list"
)

# 8. Explain recommendation (needs product_id and user_id)
if product_id:
    results["Explain"] = test_endpoint(
        "8. Explain Recommendation",
        "POST",
        f"{BASE_URL}/recommendations/explain",
        {"product_id": product_id, "user_id": "test-user"}
    )
else:
    results["Explain"] = False

# Summary
print("\n" + "="*60)
print("  TEST SUMMARY")
print("="*60)
for name, passed in results.items():
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {name}: {status}")

passed = sum(1 for v in results.values() if v)
total = len(results)
print(f"\n  Total: {passed}/{total} passed")
