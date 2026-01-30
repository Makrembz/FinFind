"""Debug filter building."""
from app.agents.services.qdrant_service import get_qdrant_service
from app.agents.services.embedding_service import get_embedding_service

qdrant = get_qdrant_service()
embedder = get_embedding_service()

query_vector = embedder.embed('laptop')

print("\n=== Test 1: Filter with default threshold (0.5) ===")
results = qdrant.semantic_search(
    collection='products',
    query_vector=query_vector,
    limit=5,
    filters={'category': 'Electronics'}
)
print(f'Results: {len(results)}')

print("\n=== Test 2: Filter with LOW threshold (0.2) ===")
results2 = qdrant.semantic_search(
    collection='products',
    query_vector=query_vector,
    limit=5,
    filters={'category': 'Electronics'},
    score_threshold=0.2
)
print(f'Results: {len(results2)}')
for r in results2:
    p = r['payload']
    score = r['score']
    title = p.get("title", "?")[:40]
    print(f'  Score: {score:.3f} - {title}')

print("\n=== Test 3: Price filter with LOW threshold ===")
results3 = qdrant.semantic_search(
    collection='products',
    query_vector=query_vector,
    limit=5,
    filters={'price': {'lte': 1000}},
    score_threshold=0.2
)
print(f'Results: {len(results3)}')
for r in results3:
    p = r['payload']
    score = r['score']
    title = p.get("title", "?")[:35]
    price = p.get("price", 0)
    print(f'  Score: {score:.3f} - ${price:.0f} - {title}')
