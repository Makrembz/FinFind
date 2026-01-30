"""Check user interactions in Qdrant."""
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from dotenv import load_dotenv
import os

load_dotenv()

client = QdrantClient(
    url=os.getenv('QDRANT_URL'),
    api_key=os.getenv('QDRANT_API_KEY')
)

# Get all interactions
print("=== All Recent Interactions ===")
result = client.scroll(
    collection_name='user_interactions',
    limit=20,
    with_payload=True
)

print(f"Total interactions found: {len(result[0])}")

# Group by interaction type
type_counts = {}
for point in result[0]:
    itype = point.payload.get('interaction_type', 'unknown')
    type_counts[itype] = type_counts.get(itype, 0) + 1

print("\nInteraction types:")
for itype, count in type_counts.items():
    print(f"  {itype}: {count}")

# Check for demo user
print("\n=== Demo User Interactions ===")
demo_result = client.scroll(
    collection_name='user_interactions',
    scroll_filter=Filter(
        must=[
            FieldCondition(
                key='user_id',
                match=MatchValue(value='013c3cb2-482a-55b0-9559-6688c3b78313')
            )
        ]
    ),
    limit=10,
    with_payload=True
)

print(f"Demo user interactions: {len(demo_result[0])}")
for point in demo_result[0]:
    print(f"  - {point.payload.get('interaction_type')}: {point.payload.get('product_id')} at {point.payload.get('timestamp')}")

# Get collection info
info = client.get_collection('user_interactions')
print(f"\n=== Collection Info ===")
print(f"Total points: {info.points_count}")
print(f"Vectors count: {info.vectors_count}")
