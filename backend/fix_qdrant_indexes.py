"""
Fix Qdrant Collections - Add Required Indexes

This script adds the missing indexes for:
- 'rating' (float) on products collection
- 'original_id' (keyword) on all collections
"""

import os
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from qdrant_client import QdrantClient
from qdrant_client.models import PayloadSchemaType


def main():
    print("="*60)
    print("Qdrant Collection Index Fixer")
    print("="*60)
    
    # Connect to Qdrant
    url = os.getenv("QDRANT_URL")
    api_key = os.getenv("QDRANT_API_KEY")
    
    if not url or not api_key:
        print("❌ QDRANT_URL or QDRANT_API_KEY not set!")
        return
    
    print(f"\n1. Connecting to Qdrant...")
    client = QdrantClient(url=url, api_key=api_key)
    print(f"   ✅ Connected")
    
    # Collections and their required indexes
    collections_indexes = {
        "products": [
            ("rating", PayloadSchemaType.FLOAT),
            ("original_id", PayloadSchemaType.KEYWORD),
            ("price", PayloadSchemaType.FLOAT),
            ("category", PayloadSchemaType.KEYWORD),
        ],
        "user_profiles": [
            ("original_id", PayloadSchemaType.KEYWORD),
            ("user_id", PayloadSchemaType.KEYWORD),
        ],
        "reviews": [
            ("original_id", PayloadSchemaType.KEYWORD),
            ("product_id", PayloadSchemaType.KEYWORD),
            ("rating", PayloadSchemaType.FLOAT),
        ],
        "user_interactions": [
            ("original_id", PayloadSchemaType.KEYWORD),
            ("user_id", PayloadSchemaType.KEYWORD),
            ("product_id", PayloadSchemaType.KEYWORD),
            ("interaction_type", PayloadSchemaType.KEYWORD),
        ]
    }
    
    print(f"\n2. Creating indexes...")
    
    for collection, indexes in collections_indexes.items():
        print(f"\n   📦 Collection: {collection}")
        
        # Check if collection exists
        try:
            info = client.get_collection(collection)
            print(f"      Points: {info.points_count}")
        except Exception as e:
            print(f"      ⚠️ Collection not found, skipping")
            continue
        
        for field_name, field_type in indexes:
            try:
                client.create_payload_index(
                    collection_name=collection,
                    field_name=field_name,
                    field_schema=field_type,
                )
                print(f"      ✅ Created index: {field_name} ({field_type.value})")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"      ⏭️ Index exists: {field_name}")
                else:
                    print(f"      ❌ Error creating {field_name}: {e}")
    
    print("\n" + "="*60)
    print("✅ Index creation complete!")
    print("="*60)
    

if __name__ == "__main__":
    main()
