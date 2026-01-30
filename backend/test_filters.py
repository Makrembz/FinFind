"""Quick filter test."""
from app.agents.services.qdrant_service import get_qdrant_service
from app.agents.services.embedding_service import get_embedding_service

qdrant = get_qdrant_service()
embedder = get_embedding_service()

query_vector = embedder.embed('laptop for programming')

print('\n=== FILTER TEST: Price <= 1000 ===')
results = qdrant.semantic_search(
    collection='products',
    query_vector=query_vector,
    limit=5,
    filters={'price': {'lte': 1000}}
)
print(f'Found {len(results)} results')
for r in results:
    p = r['payload']
    title = p.get('title', '?')[:45]
    price = p.get('price', 0)
    cat = p.get('category', '?')
    print(f'  {title} - ${price:.2f} - {cat}')

print('\n=== FILTER TEST: Category = Electronics ===')
results2 = qdrant.semantic_search(
    collection='products',
    query_vector=query_vector,
    limit=5,
    filters={'category': 'Electronics'}
)
print(f'Found {len(results2)} results')
for r in results2:
    p = r['payload']
    title = p.get('title', '?')[:45]
    price = p.get('price', 0)
    print(f'  {title} - ${price:.2f}')

print('\n=== COMBINED: Electronics + Price <= 2000 ===')
results3 = qdrant.semantic_search(
    collection='products',
    query_vector=query_vector,
    limit=5,
    filters={
        'category': 'Electronics',
        'price': {'lte': 2000}
    }
)
print(f'Found {len(results3)} results')
for r in results3:
    p = r['payload']
    title = p.get('title', '?')[:45]
    price = p.get('price', 0)
    print(f'  {title} - ${price:.2f}')
