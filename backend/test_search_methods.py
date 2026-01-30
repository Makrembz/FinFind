"""
Test script to demonstrate Qdrant search methods in FinFind.

This script shows:
1. Semantic Search (simple similarity)
2. MMR Search (diverse results)
3. Filter building
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agents.services.qdrant_service import QdrantService, get_qdrant_service
from app.agents.services.embedding_service import EmbeddingService, get_embedding_service


def print_results(title: str, results: list, show_vectors: bool = False):
    """Pretty print search results."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    print(f"  Found {len(results)} results\n")
    
    for i, r in enumerate(results, 1):
        payload = r.get("payload", {})
        # Handle nested payload
        if "payload" in payload:
            payload = payload["payload"]
        
        name = payload.get("title", payload.get("name", "Unknown"))
        price = payload.get("price", 0)
        category = payload.get("category", "N/A")
        score = r.get("score", 0)
        mmr_score = r.get("mmr_score")
        
        print(f"  {i}. {name[:50]}")
        print(f"     Category: {category} | Price: ${price:.2f}")
        print(f"     Similarity Score: {score:.4f}", end="")
        if mmr_score:
            print(f" | MMR Score: {mmr_score:.4f}", end="")
        print("\n")


def main():
    print("\n" + "="*60)
    print("  FinFind Qdrant Search Methods Demo")
    print("="*60)
    
    # Initialize services
    print("\n[1] Initializing services...")
    qdrant = get_qdrant_service()
    embedder = get_embedding_service()
    
    # Test query
    query = "laptop for programming"
    print(f"\n[2] Query: \"{query}\"")
    
    # Generate embedding
    print("[3] Generating embedding...")
    query_vector = embedder.embed(query)
    print(f"    Vector dimension: {len(query_vector)}")
    
    # ============================================
    # TEST 1: Simple Semantic Search (no filters)
    # ============================================
    print("\n[4] Running SEMANTIC SEARCH (no filters)...")
    semantic_results = qdrant.semantic_search(
        collection="products",
        query_vector=query_vector,
        limit=5,
        score_threshold=0.3
    )
    print_results("SEMANTIC SEARCH - Top 5 by Similarity", semantic_results)
    
    # ============================================
    # TEST 2: MMR Search (diverse results)
    # ============================================
    print("\n[5] Running MMR SEARCH (diversity=0.3)...")
    mmr_results = qdrant.mmr_search(
        collection="products",
        query_vector=query_vector,
        limit=5,
        diversity=0.3  # 0.3 = balance relevance & diversity
    )
    print_results("MMR SEARCH - Top 5 with Diversity", mmr_results)
    
    # ============================================
    # TEST 3: Semantic Search with Price Filter
    # ============================================
    print("\n[6] Running SEMANTIC SEARCH with PRICE FILTER (< $500)...")
    filtered_results = qdrant.semantic_search(
        collection="products",
        query_vector=query_vector,
        limit=5,
        filters={
            "price": {"lte": 500}  # Price <= $500
        }
    )
    print_results("FILTERED SEARCH - Price under $500", filtered_results)
    
    # ============================================
    # TEST 4: Semantic Search with Category Filter
    # ============================================
    print("\n[7] Running SEMANTIC SEARCH with CATEGORY FILTER...")
    category_results = qdrant.semantic_search(
        collection="products",
        query_vector=query_vector,
        limit=5,
        filters={
            "category": {"match": "Electronics"}
        }
    )
    print_results("FILTERED SEARCH - Electronics Only", category_results)
    
    # ============================================
    # TEST 5: Combined Filters
    # ============================================
    print("\n[8] Running SEMANTIC SEARCH with COMBINED FILTERS...")
    combined_results = qdrant.semantic_search(
        collection="products",
        query_vector=query_vector,
        limit=5,
        filters={
            "category": {"match": "Electronics"},
            "rating_avg": {"gte": 4.0}  # Rating >= 4.0
        }
    )
    print_results("COMBINED FILTERS - Electronics with Rating >= 4.0", combined_results)
    
    # ============================================
    # Comparison: Semantic vs MMR
    # ============================================
    print("\n" + "="*60)
    print("  COMPARISON: Semantic vs MMR")
    print("="*60)
    print("""
    SEMANTIC SEARCH:
    - Uses: client.query_points()
    - Returns: Most similar results by cosine distance
    - Pros: Fast, straightforward
    - Cons: May return very similar items (redundant)
    
    MMR SEARCH (Maximal Marginal Relevance):
    - Uses: client.query_points() + MMR algorithm
    - Formula: MMR = λ * sim(doc, query) - (1-λ) * max(sim(doc, selected))
    - λ (lambda) = 1 - diversity
    - diversity=0.3 → λ=0.7 (favor relevance)
    - diversity=0.7 → λ=0.3 (favor diversity)
    - Pros: Diverse results, avoids redundancy
    - Cons: Slightly slower (needs vectors for comparison)
    """)
    
    # ============================================
    # Filter Building Examples
    # ============================================
    print("\n" + "="*60)
    print("  FILTER BUILDING EXAMPLES")
    print("="*60)
    print("""
    Filter Types Supported:
    
    1. EXACT MATCH:
       {"category": {"match": "Electronics"}}
       → category == "Electronics"
    
    2. RANGE (numeric):
       {"price": {"gte": 100, "lte": 500}}
       → 100 <= price <= 500
    
    3. ANY OF (multiple values):
       {"category": {"any": ["Electronics", "Computers"]}}
       → category IN ("Electronics", "Computers")
    
    4. NONE OF (exclude):
       {"brand": {"none": ["BrandX", "BrandY"]}}
       → brand NOT IN ("BrandX", "BrandY")
    
    5. COMBINED:
       {
           "category": {"match": "Electronics"},
           "price": {"lte": 1000},
           "rating_avg": {"gte": 4.0}
       }
       → Electronics AND price <= 1000 AND rating >= 4.0
    """)
    
    print("\n✅ Demo complete!")


if __name__ == "__main__":
    main()
