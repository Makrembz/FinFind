"""Test Qdrant connection and search."""
import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

load_dotenv()

# Connect to Qdrant
client = QdrantClient(
    url=os.getenv('QDRANT_URL'),
    api_key=os.getenv('QDRANT_API_KEY')
)

# Check collections
print("=== Collections ===")
collections = client.get_collections()
for c in collections.collections:
    print(f"  - {c.name}")

# Get product collection info
print("\n=== Products Collection ===")
info = client.get_collection('products')
print(f"Points count: {info.points_count}")
print(f"Vector size: {info.config.params.vectors.size}")

# Get a sample product
print("\n=== Sample Product ===")
sample = client.scroll(collection_name='products', limit=1, with_vectors=True)
if sample[0]:
    point = sample[0][0]
    print(f"ID: {point.id}")
    print(f"Payload keys: {list(point.payload.keys())}")
    if 'title' in point.payload:
        print(f"Title: {point.payload.get('title')}")
    if 'name' in point.payload:
        print(f"Name: {point.payload.get('name')}")
    print(f"Vector length: {len(point.vector) if point.vector else 'None'}")
    print(f"Vector sample (first 5): {point.vector[:5] if point.vector else 'None'}")

# Test search with embedding
print("\n=== Testing Search ===")
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
query = "laptop computer"
query_embedding = model.encode(query).tolist()
print(f"Query: {query}")
print(f"Embedding length: {len(query_embedding)}")

results = client.query_points(
    collection_name='products',
    query=query_embedding,
    limit=5,
    with_payload=True
)

print(f"\n=== Search Results ===")
for i, r in enumerate(results.points):
    payload = r.payload
    name = payload.get('title', payload.get('name', 'Unknown'))
    print(f"{i+1}. Score: {r.score:.4f} - {name}")
    print(f"   Category: {payload.get('category')}")
