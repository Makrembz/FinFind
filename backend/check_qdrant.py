"""Check Qdrant data structure"""
from dotenv import load_dotenv
import os
load_dotenv()
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

client = QdrantClient(url=os.getenv('QDRANT_URL'), api_key=os.getenv('QDRANT_API_KEY'))

print("=" * 60)
print("QDRANT DATA INSPECTION")
print("=" * 60)

# Check products
print("\n1. PRODUCTS COLLECTION:")
result = client.scroll(collection_name='products', limit=2, with_payload=True, with_vectors=False)
if result[0]:
    for p in result[0]:
        print(f"  Point ID: {p.id}")
        print(f"  Payload 'id' field: {p.payload.get('id')}")
        print(f"  Payload 'name' field: {p.payload.get('name')}")
        print(f"  Payload keys: {list(p.payload.keys())[:8]}")
        print()

# Check user_profiles
print("\n2. USER_PROFILES COLLECTION:")
result = client.scroll(collection_name='user_profiles', limit=2, with_payload=True, with_vectors=False)
if result[0]:
    for p in result[0]:
        print(f"  Point ID: {p.id}")
        print(f"  Payload 'user_id' field: {p.payload.get('user_id')}")
        print(f"  Payload 'persona_type' field: {p.payload.get('persona_type')}")
        print(f"  Payload keys: {list(p.payload.keys())[:8]}")
        print()

# Check user_interactions
print("\n3. USER_INTERACTIONS COLLECTION:")
result = client.scroll(collection_name='user_interactions', limit=2, with_payload=True, with_vectors=False)
if result[0]:
    for p in result[0]:
        print(f"  Point ID: {p.id}")
        print(f"  Payload 'user_id' field: {p.payload.get('user_id')}")
        print(f"  Payload 'product_id' field: {p.payload.get('product_id')}")
        print(f"  Payload keys: {list(p.payload.keys())[:8]}")
        print()

# Check reviews
print("\n4. REVIEWS COLLECTION:")
result = client.scroll(collection_name='reviews', limit=2, with_payload=True, with_vectors=False)
if result[0]:
    for p in result[0]:
        print(f"  Point ID: {p.id}")
        print(f"  Payload 'review_id' field: {p.payload.get('review_id')}")
        print(f"  Payload 'product_id' field: {p.payload.get('product_id')}")
        print(f"  Payload keys: {list(p.payload.keys())[:8]}")
        print()

# Search for specific prod_ ID in payload
print("\n5. SEARCHING FOR prod_46d046b5c615:")
try:
    result = client.scroll(
        collection_name='products', 
        limit=5,
        with_payload=True,
        with_vectors=False,
        scroll_filter=Filter(must=[FieldCondition(key='id', match=MatchValue(value='prod_46d046b5c615'))])
    )
    print(f"  Found {len(result[0])} products with id='prod_46d046b5c615'")
except Exception as e:
    print(f"  Error: {e}")

print("\n" + "=" * 60)
