#!/usr/bin/env python3
"""
Script to fix products.json format issues for compatibility with Product model.
"""

import json
import sys
from pathlib import Path

def fix_products_json(input_file: str, output_file: str = None):
    """
    Fix common format issues in products.json:
    - Convert string connectivity to list
    - Ensure all list fields are actually lists
    """
    if output_file is None:
        output_file = input_file.replace('.json', '_fixed.json')
    
    print(f"Reading from: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both list and dict formats
    if isinstance(data, dict):
        items = data.get('items', [])
    else:
        items = data
    
    fixed_count = 0
    
    for product in items:
        if 'attributes' in product:
            attrs = product['attributes']
            
            # Fix connectivity - convert string to list
            if 'connectivity' in attrs and isinstance(attrs['connectivity'], str):
                attrs['connectivity'] = [attrs['connectivity']]
                fixed_count += 1
            
            # Ensure other list fields are lists (add more as needed)
            list_fields = ['features', 'colors', 'materials', 'compatible_devices']
            for field in list_fields:
                if field in attrs and isinstance(attrs[field], str):
                    attrs[field] = [attrs[field]]
                    fixed_count += 1
    
    # Save fixed data
    with open(output_file, 'w', encoding='utf-8') as f:
        if isinstance(data, dict):
            data['items'] = items
            json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            json.dump(items, f, indent=2, ensure_ascii=False)
    
    print(f"Fixed {fixed_count} field(s)")
    print(f"Saved to: {output_file}")
    print(f"\nProcessed {len(items)} products")
    
    if output_file != input_file:
        print(f"\nTo use the fixed file, either:")
        print(f"1. Replace original: mv {output_file} {input_file}")
        print(f"2. Or backup and replace: mv {input_file} {input_file}.backup && mv {output_file} {input_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_products.py <path_to_products.json> [output_file]")
        print("\nExample:")
        print("  python fix_products.py output/products.json")
        print("  python fix_products.py output/products.json output/products_fixed.json")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        fix_products_json(input_file, output_file)
        print("\n✅ Success!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
