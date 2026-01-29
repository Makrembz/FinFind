"""
Regenerate products_qdrant.json from products.json with embeddings.
"""
import json
from sentence_transformers import SentenceTransformer
from pathlib import Path

def main():
    output_dir = Path(__file__).parent / "output"
    
    print('Loading products.json...')
    with open(output_dir / 'products.json', 'r', encoding='utf-8') as f:
        products = json.load(f)

    print(f'Loaded {len(products)} products')

    print('Loading embedding model...')
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    print('Generating embeddings...')
    # Create text for embedding
    texts = []
    for p in products:
        tags = ' '.join(p.get('tags', []))
        text = f"{p['title']} {p['description']} {p['category']} {p['subcategory']} {tags}"
        texts.append(text)

    embeddings = model.encode(texts, show_progress_bar=True)

    print('Creating Qdrant points...')
    points = []
    for product, embedding in zip(products, embeddings):
        point = {
            'id': product['id'],
            'vector': embedding.tolist(),
            'payload': product
        }
        points.append(point)

    # Save to products_qdrant.json
    output_file = output_dir / 'products_qdrant.json'
    output_data = {'points': points}
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f'Saved {len(points)} products to {output_file}')

if __name__ == "__main__":
    main()
