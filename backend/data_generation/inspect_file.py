#!/usr/bin/env python3
"""
Inspect the actual content of the JSON file.
"""

import json
import sys

def inspect_file(filepath):
    print(f"Inspecting: {filepath}")
    print("=" * 70)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"File size: {len(content)} bytes")
        print(f"First 500 characters:")
        print("-" * 70)
        print(content[:500])
        print("-" * 70)
        
        # Try to parse
        data = json.loads(content)
        
        if isinstance(data, list):
            print(f"\nData type: List with {len(data)} items")
            if len(data) > 0:
                print(f"\nFirst item structure:")
                print(json.dumps(data[0], indent=2)[:1000])
        elif isinstance(data, dict):
            print(f"\nData type: Dictionary with keys: {list(data.keys())}")
            print(f"\nFull content:")
            print(json.dumps(data, indent=2)[:2000])
        else:
            print(f"\nData type: {type(data)}")
            print(f"Content: {data}")
            
    except json.JSONDecodeError as e:
        print(f"\n❌ JSON Parse Error: {e}")
        print(f"Error at line {e.lineno}, column {e.colno}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        filepath = "output/user_interactions_qdrant.json"
    else:
        filepath = sys.argv[1]
    
    inspect_file(filepath)
