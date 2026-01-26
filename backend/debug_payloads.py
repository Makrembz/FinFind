#!/usr/bin/env python3
"""Debug script to check actual payload structures in Qdrant."""

import json
from app.agents.services.qdrant_service import get_qdrant_service

qdrant = get_qdrant_service()

print("=" * 70)
print("PRODUCT PAYLOAD STRUCTURE")
print("=" * 70)
products = qdrant.scroll('products', limit=1)
if products:
    payload = products[0]['payload']
    print(f"ID: {products[0]['id']}")
    print(f"\nAll keys: {list(payload.keys())}")
    print(f"\nKey values:")
    for k, v in payload.items():
        if k not in ['vector', 'tags', 'payment_options', 'image_urls']:
            val_str = str(v)[:80] if v else 'None'
            print(f"  {k}: {val_str}")

print("\n" + "=" * 70)
print("USER PROFILE PAYLOAD STRUCTURE")
print("=" * 70)
users = qdrant.scroll('user_profiles', limit=1)
if users:
    payload = users[0]['payload']
    print(f"ID: {users[0]['id']}")
    print(f"\nAll keys: {list(payload.keys())}")
    # Show top-level non-nested
    for k, v in payload.items():
        if k not in ['vector', 'purchase_history', 'payload'] and not isinstance(v, dict):
            val_str = str(v)[:80] if v else 'None'
            print(f"  {k}: {val_str}")
    # Show nested preferences
    if 'preferences' in payload and isinstance(payload['preferences'], dict):
        print(f"\n  preferences keys: {list(payload['preferences'].keys())}")
    if 'financial_context' in payload and isinstance(payload['financial_context'], dict):
        print(f"  financial_context keys: {list(payload['financial_context'].keys())}")

print("\n" + "=" * 70)
print("REVIEW PAYLOAD STRUCTURE")
print("=" * 70)
reviews = qdrant.scroll('reviews', limit=1)
if reviews:
    payload = reviews[0]['payload']
    print(f"ID: {reviews[0]['id']}")
    print(f"\nAll keys: {list(payload.keys())}")
    for k, v in payload.items():
        if k not in ['vector']:
            val_str = str(v)[:80] if v else 'None'
            print(f"  {k}: {val_str}")

print("\n" + "=" * 70)
print("INTERACTION PAYLOAD STRUCTURE")
print("=" * 70)
interactions = qdrant.scroll('user_interactions', limit=1)
if interactions:
    payload = interactions[0]['payload']
    print(f"ID: {interactions[0]['id']}")
    print(f"\nAll keys: {list(payload.keys())}")
    for k, v in payload.items():
        if k not in ['vector']:
            val_str = str(v)[:80] if v else 'None'
            print(f"  {k}: {val_str}")
