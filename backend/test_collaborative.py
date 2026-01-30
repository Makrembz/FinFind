"""Test collaborative filtering recommendations."""
import requests
import json
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from dotenv import load_dotenv
import os

load_dotenv()
client = QdrantClient(url=os.getenv('QDRANT_URL'), api_key=os.getenv('QDRANT_API_KEY'))

# Demo user ID
user_id = '013c3cb2-482a-55b0-9559-6688c3b78313'

# First, get some REAL product IDs from the database
print("=== Getting real product IDs from database ===")
products = client.scroll(
    collection_name='products',
    limit=10,
    with_payload=True
)

real_product_ids = []
for p in products[0]:
    real_product_ids.append(p.id)
    name = p.payload.get('payload', p.payload).get('title', p.payload.get('name', 'Unknown'))
    print(f"  - {p.id}: {name[:50]}")

if len(real_product_ids) < 3:
    print("ERROR: Not enough products in database")
    exit(1)

# Add some positive interactions with REAL product IDs
print("\n=== Adding test interactions with REAL product IDs ===")

# Add wishlist interaction
r1 = requests.post(
    f'http://localhost:8000/api/v1/products/{real_product_ids[0]}/interact',
    json={'interaction_type': 'wishlist', 'metadata': {'user_id': user_id}}
)
print(f"Wishlist interaction for {real_product_ids[0]}: {r1.status_code}")

# Add add_to_cart interaction  
r2 = requests.post(
    f'http://localhost:8000/api/v1/products/{real_product_ids[1]}/interact',
    json={'interaction_type': 'add_to_cart', 'metadata': {'user_id': user_id}}
)
print(f"Add to cart interaction for {real_product_ids[1]}: {r2.status_code}")

# Add purchase interaction
r3 = requests.post(
    f'http://localhost:8000/api/v1/products/{real_product_ids[2]}/interact',
    json={'interaction_type': 'purchase', 'metadata': {'user_id': user_id}}
)
print(f"Purchase interaction for {real_product_ids[2]}: {r3.status_code}")

# Now test recommendations
print("\n=== Testing Recommendations ===")
r4 = requests.get(f'http://localhost:8000/api/v1/recommendations/{user_id}?limit=5&include_reasons=true')
print(f"Recommendations status: {r4.status_code}")

if r4.status_code == 200:
    data = r4.json()
    print(f"Success: {data.get('success')}")
    print(f"Total recommendations: {data.get('total', 0)}")
    print(f"\nRecommendation Reasons:")
    for i, rec in enumerate(data.get('recommendations', [])[:5]):
        reasons = data.get('reasons', {}).get(rec.get('id'), [])
        print(f"\n{i+1}. {rec.get('name', 'Unknown')[:50]}...")
        print(f"   Price: ${rec.get('price', 0)}")
        print(f"   Category: {rec.get('category')}")
        print(f"   Reasons: {reasons}")
        
    # Check if any have collaborative filtering reason
    collab_count = 0
    for rec in data.get('recommendations', []):
        reasons = data.get('reasons', {}).get(rec.get('id'), [])
        if any('shopping behavior' in str(r) for r in reasons):
            collab_count += 1
    print(f"\n✅ Products from collaborative filtering: {collab_count}/{len(data.get('recommendations', []))}")
else:
    print(f"Error: {r4.text}")

# Check the interaction count
print("\n=== User Interactions Analysis ===")

result = client.scroll(
    collection_name='user_interactions',
    scroll_filter=Filter(must=[FieldCondition(key='user_id', match=MatchValue(value=user_id))]),
    limit=50,
    with_payload=True
)

# Count by type
type_counts = {}
positive_ids = []
for point in result[0]:
    payload = point.payload.get('payload', point.payload)
    itype = payload.get('interaction_type', 'unknown')
    product_id = payload.get('product_id')
    type_counts[itype] = type_counts.get(itype, 0) + 1
    if itype in ['purchase', 'add_to_cart', 'wishlist', 'bookmark'] and product_id:
        positive_ids.append(product_id)

print(f"Total interactions for user: {len(result[0])}")
print("By type:")
for itype, count in type_counts.items():
    print(f"  {itype}: {count}")

print(f"\nPositive signal product IDs: {positive_ids[:10]}")

# Test the recommend API using our QdrantService
print("\n=== Testing QdrantService Recommend Method Directly ===")
try:
    from app.agents.services.qdrant_service import QdrantService
    
    qdrant_service = QdrantService()
    
    if positive_ids:
        # Only use unique IDs that exist in the products collection
        # Filter out IDs that don't exist (like prod_new_001, prod_new_002, prod_187bbfc14c30)
        valid_positive_ids = [pid for pid in list(set(positive_ids)) if not pid.startswith('prod_')][:5]
        print(f"Using valid positive IDs: {valid_positive_ids}")
        
        if valid_positive_ids:
            recommend_result = qdrant_service.recommend(
                collection='products',
                positive_ids=valid_positive_ids,
                limit=5
            )
            
            print(f"QdrantService recommend returned {len(recommend_result)} results:")
            for r in recommend_result[:5]:
                payload = r.get('payload', {})
                inner_payload = payload.get('payload', payload)
                name = inner_payload.get('title', inner_payload.get('name', 'Unknown'))
                print(f"  - {r.get('id')}: {name[:40]}... (score: {r.get('score', 0):.4f})")
        else:
            print("No valid positive IDs found for testing!")
    else:
        print("No positive IDs found for testing!")
except Exception as e:
    import traceback
    print(f"QdrantService recommend error: {e}")
    traceback.print_exc()
