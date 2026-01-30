"""
Fix user_interactions_qdrant.json by adding embeddings for items with empty vectors.

The file structure is a JSON array of points directly (not wrapped in an object).
"""
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

def main():
    output_dir = Path('output')
    
    # Load user_interactions_qdrant.json
    print("Loading user_interactions_qdrant.json...")
    with open(output_dir / 'user_interactions_qdrant.json', 'r') as f:
        data = json.load(f)
    
    # Handle both structures: direct array or wrapped in 'points'
    if isinstance(data, list):
        points = data
        is_array = True
    else:
        points = data.get('points', [])
        is_array = False
    print(f"Total interactions: {len(points)}")
    
    # Find items with empty vectors
    empty_indices = []
    for i, p in enumerate(points):
        vec = p.get('vector', [])
        if not vec or len(vec) == 0:
            empty_indices.append(i)
    
    print(f"Interactions with empty vectors: {len(empty_indices)}")
    
    if not empty_indices:
        print("All vectors are present. Nothing to fix.")
        return
    
    # Load embedding model
    print("Loading embedding model...")
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    
    # Generate embeddings for items with empty vectors
    print("Generating embeddings for interactions with empty vectors...")
    
    texts_to_embed = []
    for idx in empty_indices:
        payload = points[idx].get('payload', {})
        
        # Build text from interaction context
        parts = []
        
        # Interaction type
        interaction_type = payload.get('interaction_type', '')
        parts.append(f"interaction: {interaction_type}")
        
        # Search context
        search_ctx = payload.get('search_context') or {}
        if search_ctx.get('query'):
            parts.append(f"search: {search_ctx['query']}")
        if search_ctx.get('filters'):
            filters = search_ctx['filters']
            if filters.get('categories'):
                parts.append(f"category: {', '.join(filters['categories'])}")
            if filters.get('brands'):
                parts.append(f"brand: {', '.join(filters['brands'])}")
        
        # View context
        view_ctx = payload.get('view_context') or {}
        if view_ctx.get('product_title'):
            parts.append(f"viewed: {view_ctx['product_title']}")
        elif view_ctx.get('product_name'):
            parts.append(f"viewed: {view_ctx['product_name']}")
        if view_ctx.get('product_category'):
            parts.append(f"category: {view_ctx['product_category']}")
        elif view_ctx.get('category'):
            parts.append(f"category: {view_ctx['category']}")
        
        # Cart context
        cart_ctx = payload.get('cart_context') or {}
        if cart_ctx.get('product_title'):
            parts.append(f"cart: {cart_ctx['product_title']}")
        elif cart_ctx.get('product_name'):
            parts.append(f"cart: {cart_ctx['product_name']}")
        if cart_ctx.get('product_category'):
            parts.append(f"category: {cart_ctx['product_category']}")
        
        # Purchase context
        purchase_ctx = payload.get('purchase_context') or {}
        if purchase_ctx.get('products'):
            for prod in purchase_ctx['products']:
                if prod.get('title'):
                    parts.append(f"purchased: {prod['title']}")
                if prod.get('category'):
                    parts.append(f"category: {prod['category']}")
        elif purchase_ctx.get('product_name'):
            parts.append(f"purchased: {purchase_ctx['product_name']}")
        
        # Wishlist context
        wishlist_ctx = payload.get('wishlist_context') or {}
        if wishlist_ctx.get('product_title'):
            parts.append(f"wishlist: {wishlist_ctx['product_title']}")
        elif wishlist_ctx.get('product_name'):
            parts.append(f"wishlist: {wishlist_ctx['product_name']}")
        if wishlist_ctx.get('product_category'):
            parts.append(f"category: {wishlist_ctx['product_category']}")
        
        text = ' | '.join(parts) if parts else f"user interaction {interaction_type}"
        texts_to_embed.append(text)
    
    # Generate embeddings in batches
    print(f"Generating {len(texts_to_embed)} embeddings...")
    batch_size = 64
    embeddings = []
    
    for i in tqdm(range(0, len(texts_to_embed), batch_size), desc="Generating embeddings"):
        batch = texts_to_embed[i:i + batch_size]
        batch_embeddings = model.encode(batch, convert_to_numpy=True)
        embeddings.extend(batch_embeddings.tolist())
    
    # Update points with new embeddings
    print("Updating points with new embeddings...")
    for idx, emb in zip(empty_indices, embeddings):
        points[idx]['vector'] = emb
    
    # Verify
    empty_after = sum(1 for p in points if not p.get('vector') or len(p.get('vector', [])) == 0)
    print(f"Empty vectors after fix: {empty_after}")
    
    # Save updated file
    print("Saving updated user_interactions_qdrant.json...")
    with open(output_dir / 'user_interactions_qdrant.json', 'w') as f:
        # Save in the same format as loaded
        if is_array:
            json.dump(points, f)
        else:
            json.dump(data, f)
    
    print("Done!")

if __name__ == "__main__":
    main()
