#!/usr/bin/env python3
"""
Diagnose the exact issue with the Qdrant JSON files.
"""

import json
import sys

def diagnose_file(filepath):
    print(f"Diagnosing: {filepath}")
    print("=" * 70)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Check top-level structure
    if isinstance(data, dict):
        print(f"✗ Format: Dictionary (expected: List)")
        print(f"  Keys: {list(data.keys())}")
        
        if 'points' in data:
            points = data['points']
            print(f"  → Found 'points' key with {len(points)} items")
        else:
            print(f"  ✗ No 'points' key found!")
            return
    elif isinstance(data, list):
        print(f"✓ Format: List")
        points = data
    else:
        print(f"✗ Unexpected format: {type(data)}")
        return
    
    print(f"\nTotal items: {len(points)}")
    
    if len(points) == 0:
        print("✗ Empty list!")
        return
    
    # Check first item structure
    first = points[0]
    print(f"\nFirst item structure:")
    print(f"  Keys: {list(first.keys())}")
    
    # Check for ID
    if 'id' in first:
        print(f"  ✓ Has 'id': {first['id'][:50]}")
    else:
        print(f"  ✗ Missing 'id'")
    
    # Check for vector/embedding
    has_vector = 'vector' in first
    has_embedding = 'embedding' in first
    
    if has_vector:
        vec_len = len(first['vector'])
        print(f"  ✓ Has 'vector': dimension {vec_len}")
        if vec_len == 0:
            print(f"    ✗ ERROR: Empty vector!")
    else:
        print(f"  ✗ Missing 'vector'")
    
    if has_embedding:
        emb_len = len(first['embedding'])
        print(f"  ✓ Has 'embedding': dimension {emb_len}")
        if emb_len == 0:
            print(f"    ✗ ERROR: Empty embedding!")
    else:
        print(f"  ✗ Missing 'embedding'")
    
    # Check payload
    if 'payload' in first:
        print(f"  ✓ Has 'payload'")
        payload_keys = list(first['payload'].keys())[:10]
        print(f"    Keys: {payload_keys}")
    else:
        print(f"  ✗ Missing 'payload'")
    
    # Summary
    print(f"\n" + "=" * 70)
    print("DIAGNOSIS:")
    
    issues = []
    fixes = []
    
    if isinstance(data, dict):
        issues.append("File is a dictionary, not a list")
        fixes.append("Extract the 'points' array")
    
    if has_vector and not has_embedding:
        issues.append("Uses 'vector' instead of 'embedding'")
        fixes.append("Rename 'vector' to 'embedding' in all items")
    
    if not has_vector and not has_embedding:
        issues.append("No vector/embedding field found!")
    
    if has_vector and len(first.get('vector', [])) == 0:
        issues.append("Vectors are empty (dimension 0)")
    
    if has_embedding and len(first.get('embedding', [])) == 0:
        issues.append("Embeddings are empty (dimension 0)")
    
    if issues:
        print("✗ ISSUES FOUND:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        
        if fixes:
            print("\n📋 FIXES NEEDED:")
            for i, fix in enumerate(fixes, 1):
                print(f"  {i}. {fix}")
    else:
        print("✓ No issues found - file looks good!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        files = [
            "output/products_qdrant.json",
            "output/reviews_qdrant.json",
            "output/user_profiles_qdrant.json",
            "output/user_interactions_qdrant.json"
        ]
        print("Checking all Qdrant files...\n")
        for f in files:
            try:
                diagnose_file(f)
                print("\n")
            except Exception as e:
                print(f"Error with {f}: {e}\n")
    else:
        filepath = sys.argv[1]
        diagnose_file(filepath)
