#!/usr/bin/env python3
"""Debug script to check actual nested payload structures in Qdrant."""

import json
from app.agents.services.qdrant_service import get_qdrant_service

qdrant = get_qdrant_service()

print("=" * 70)
print("PRODUCT NESTED PAYLOAD STRUCTURE")
print("=" * 70)
products = qdrant.scroll('products', limit=1)
if products:
    outer_payload = products[0]['payload']
    print(f"Outer ID: {products[0]['id']}")
    print(f"Outer keys: {list(outer_payload.keys())}")
    
    # The actual data is nested in payload['payload']
    if 'payload' in outer_payload:
        inner = outer_payload['payload']
        print(f"\nInner payload keys: {list(inner.keys())}")
        print(f"\nInner payload values:")
        for k, v in inner.items():
            if k not in ['vector', 'tags', 'payment_options', 'image_urls', 'attributes']:
                val_str = str(v)[:100] if v else 'None'
                print(f"  {k}: {val_str}")
        if 'attributes' in inner:
            print(f"\n  attributes: {inner['attributes']}")

print("\n" + "=" * 70)
print("USER PROFILE NESTED PAYLOAD STRUCTURE")
print("=" * 70)
users = qdrant.scroll('user_profiles', limit=1)
if users:
    outer_payload = users[0]['payload']
    print(f"Outer ID: {users[0]['id']}")
    
    if 'payload' in outer_payload:
        inner = outer_payload['payload']
        print(f"\nInner payload keys: {list(inner.keys())}")
        # Show key fields
        for k in ['persona_type', 'age_range', 'budget_min', 'budget_max', 'primary_payment_method']:
            if k in inner:
                print(f"  {k}: {inner[k]}")
        if 'preferences' in inner:
            prefs = inner['preferences']
            print(f"\n  preferences keys: {list(prefs.keys())}")
        if 'financial_context' in inner:
            fin = inner['financial_context']
            print(f"  financial_context keys: {list(fin.keys())}")

print("\n" + "=" * 70)
print("REVIEW NESTED PAYLOAD STRUCTURE")
print("=" * 70)
reviews = qdrant.scroll('reviews', limit=1)
if reviews:
    outer_payload = reviews[0]['payload']
    if 'payload' in outer_payload:
        inner = outer_payload['payload']
        print(f"Inner payload keys: {list(inner.keys())}")
        for k, v in inner.items():
            if k != 'vector':
                val_str = str(v)[:100] if v else 'None'
                print(f"  {k}: {val_str}")

print("\n" + "=" * 70)
print("INTERACTION NESTED PAYLOAD STRUCTURE")
print("=" * 70)
interactions = qdrant.scroll('user_interactions', limit=1)
if interactions:
    outer_payload = interactions[0]['payload']
    if 'payload' in outer_payload:
        inner = outer_payload['payload']
        print(f"Inner payload keys: {list(inner.keys())}")
        for k, v in inner.items():
            if k != 'vector':
                val_str = str(v)[:100] if v else 'None'
                print(f"  {k}: {val_str}")
