"""Check product categories in Qdrant."""
from qdrant_client import QdrantClient
from dotenv import load_dotenv
import os

load_dotenv()

client = QdrantClient(url=os.getenv('QDRANT_URL'), api_key=os.getenv('QDRANT_API_KEY'))

# Get all products
results = client.scroll('products', limit=200, with_payload=True)

categories = {}
laptops = []

for p in results[0]:
    cat = p.payload.get('category', 'Unknown')
    categories[cat] = categories.get(cat, 0) + 1
    title = p.payload.get('title', '')
    if 'laptop' in title.lower() or 'macbook' in title.lower() or 'notebook' in title.lower():
        laptops.append(f"{title[:50]}: ${p.payload.get('price')}")

print('Categories:', dict(sorted(categories.items())))
print(f'\nLaptops found ({len(laptops)}):')
for l in laptops[:10]:
    print(f'  - {l}')
