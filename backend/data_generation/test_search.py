"""Quick test of search API."""
import requests

response = requests.post(
    'http://localhost:8000/api/v1/search/products',
    json={'query': 'laptop', 'limit': 5}
)
data = response.json()
print('Query:', data.get('query'))
print('Total results:', data.get('total_results'))
print()
for p in data.get('products', []):
    name = p.get('name', 'Unknown')[:50]
    score = p.get('relevance_score', 0)
    print(f'{name:50} - Score: {score:.3f}')
