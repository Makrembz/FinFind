#!/usr/bin/env python3
"""
Check which interactions in the Qdrant file have missing embeddings.
"""

import json
import sys

def check_embeddings(filepath):
    print(f"Checking: {filepath}")
    print("=" * 70)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Total interactions: {len(data)}")
    
    missing_embeddings = []
    empty_embeddings = []
    valid_embeddings = []
    
    for i, item in enumerate(data):
        if 'embedding' not in item:
            missing_embeddings.append(i)
        elif not item['embedding'] or len(item['embedding']) == 0:
            empty_embeddings.append(i)
        else:
            valid_embeddings.append(i)
    
    print(f"\nResults:")
    print(f"  ✓ Valid embeddings: {len(valid_embeddings)}")
    print(f"  ✗ Missing 'embedding' key: {len(missing_embeddings)}")
    print(f"  ✗ Empty embeddings (dim=0): {len(empty_embeddings)}")
    
    if missing_embeddings or empty_embeddings:
        print(f"\n❌ PROBLEM: {len(missing_embeddings) + len(empty_embeddings)} interactions have no embeddings")
        
        # Show sample problematic items
        problematic = missing_embeddings[:5] + empty_embeddings[:5]
        print(f"\nSample problematic items (first 5):")
        for idx in problematic[:5]:
            item = data[idx]
            print(f"\n  Index {idx}:")
            print(f"    ID: {item.get('id', 'N/A')}")
            print(f"    Type: {item.get('payload', {}).get('interaction_type', 'N/A')}")
            has_embedding = 'embedding' in item
            embedding_len = len(item.get('embedding', [])) if has_embedding else 0
            print(f"    Has embedding: {has_embedding}")
            print(f"    Embedding length: {embedding_len}")
    else:
        print(f"\n✅ All interactions have valid embeddings!")
    
    # Show breakdown by interaction type
    print(f"\nBreakdown by interaction type:")
    type_counts = {}
    type_with_embeddings = {}
    
    for item in data:
        itype = item.get('payload', {}).get('interaction_type', 'unknown')
        type_counts[itype] = type_counts.get(itype, 0) + 1
        
        has_valid_embedding = 'embedding' in item and len(item.get('embedding', [])) > 0
        if has_valid_embedding:
            type_with_embeddings[itype] = type_with_embeddings.get(itype, 0) + 1
    
    for itype in sorted(type_counts.keys()):
        total = type_counts[itype]
        with_emb = type_with_embeddings.get(itype, 0)
        missing = total - with_emb
        status = "✓" if missing == 0 else "✗"
        print(f"  {status} {itype}: {with_emb}/{total} have embeddings ({missing} missing)")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        filepath = "output/user_interactions_qdrant.json"
        print(f"No file specified, using default: {filepath}\n")
    else:
        filepath = sys.argv[1]
    
    try:
        check_embeddings(filepath)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
