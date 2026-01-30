"""Debug collaborative filtering in recommendations."""
from app.agents.services.qdrant_service import QdrantService

qdrant = QdrantService()
user_id = '013c3cb2-482a-55b0-9559-6688c3b78313'

# Test the scroll with user_id filter
print("=== Testing scroll for user interactions ===")
results = qdrant.scroll(
    collection='user_interactions',
    limit=30,
    filters={'user_id': {'match': user_id}},
    with_payload=True
)
print(f'Found {len(results)} interactions')

positive_product_ids = []
for r in results[:10]:
    payload = r.get('payload', {})
    inner = payload.get('payload', payload)
    interaction_type = inner.get('interaction_type', '')
    product_id = inner.get('product_id')
    print(f"  - {interaction_type}: {product_id}")
    
    if interaction_type in ["purchase", "add_to_cart", "wishlist", "bookmark"]:
        if product_id and product_id not in positive_product_ids:
            positive_product_ids.append(product_id)

# Filter out invalid IDs (prod_xxx format)
valid_positive_ids = [pid for pid in positive_product_ids if not pid.startswith('prod_')]
print(f"\nPositive IDs: {positive_product_ids}")
print(f"Valid positive IDs (UUID format): {valid_positive_ids}")

# Test recommend with valid IDs only
if valid_positive_ids:
    print(f"\n=== Testing recommend with {len(valid_positive_ids)} valid IDs ===")
    collab_results = qdrant.recommend(
        collection='products',
        positive_ids=valid_positive_ids[:5],
        limit=5
    )
    print(f"Collaborative filtering returned {len(collab_results)} results:")
    for r in collab_results:
        payload = r.get('payload', {})
        inner = payload.get('payload', payload)
        name = inner.get('title', inner.get('name', 'Unknown'))
        print(f"  - {r.get('id')}: {name[:40]}... (score: {r.get('score', 0):.4f})")
else:
    print("\nNo valid positive IDs found!")
