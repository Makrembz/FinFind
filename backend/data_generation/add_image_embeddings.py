"""
Add Image Embeddings to Products Collection.

This script:
1. Recreates the products collection with named vectors (text + image)
2. Generates image embeddings using CLIP for each product
3. Uploads products with both text and image embeddings

The image embedding is generated from the product's text description
(simulating what CLIP would generate from an actual product image).
For a production system, you would generate embeddings from actual images.
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def is_valid_uuid(val: str) -> bool:
    """Check if a string is a valid UUID."""
    import uuid
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False


def get_clip_model():
    """Load CLIP model for image embedding generation."""
    try:
        from transformers import CLIPModel, CLIPProcessor, CLIPTokenizer
        import torch
        
        model_name = "openai/clip-vit-base-patch32"
        logger.info(f"Loading CLIP model: {model_name}")
        
        model = CLIPModel.from_pretrained(model_name)
        processor = CLIPProcessor.from_pretrained(model_name)
        tokenizer = CLIPTokenizer.from_pretrained(model_name)
        
        model.eval()
        logger.info("CLIP model loaded successfully")
        
        return model, processor, tokenizer
    except ImportError:
        logger.error("transformers not installed. Run: pip install transformers torch")
        raise


def generate_clip_text_embedding(model, tokenizer, text: str) -> List[float]:
    """
    Generate CLIP embedding from text.
    
    This simulates what the CLIP embedding would be for a product image
    by using the text description. In production, you'd use actual images.
    """
    import torch
    
    # Truncate text to CLIP's max length
    max_length = 77
    
    with torch.no_grad():
        inputs = tokenizer(
            text, 
            return_tensors="pt", 
            padding=True, 
            truncation=True,
            max_length=max_length
        )
        # get_text_features may return BaseModelOutputWithPooling
        outputs = model.get_text_features(**inputs)
        
        # Handle both tensor and BaseModelOutputWithPooling
        if isinstance(outputs, torch.Tensor):
            text_features = outputs
        elif hasattr(outputs, 'pooler_output') and outputs.pooler_output is not None:
            text_features = outputs.pooler_output
        else:
            raise ValueError("Unexpected output type from CLIP model")
        
        # Normalize the embedding
        text_features = text_features / text_features.norm(p=2, dim=-1, keepdim=True)
        
    return text_features[0].tolist()


def recreate_products_collection_with_named_vectors():
    """Recreate products collection with named vectors for text and image."""
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        VectorParams, Distance, PayloadSchemaType
    )
    
    client = QdrantClient(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY"),
        timeout=60
    )
    
    collection_name = "products"
    
    # Delete existing collection
    try:
        client.delete_collection(collection_name)
        logger.info(f"Deleted existing collection: {collection_name}")
    except Exception:
        pass
    
    # Create collection with named vectors
    logger.info(f"Creating collection with named vectors: {collection_name}")
    
    client.create_collection(
        collection_name=collection_name,
        vectors_config={
            # Text embedding (384-dim from all-MiniLM-L6-v2)
            "text": VectorParams(
                size=384,
                distance=Distance.COSINE
            ),
            # Image embedding (512-dim from CLIP)
            "image": VectorParams(
                size=512,
                distance=Distance.COSINE
            )
        }
    )
    
    # Create payload indexes
    payload_indexes = {
        "category": PayloadSchemaType.KEYWORD,
        "subcategory": PayloadSchemaType.KEYWORD,
        "brand": PayloadSchemaType.KEYWORD,
        "price": PayloadSchemaType.FLOAT,
        "rating_avg": PayloadSchemaType.FLOAT,
        "stock_status": PayloadSchemaType.KEYWORD,
        "tags": PayloadSchemaType.KEYWORD
    }
    
    for field_name, field_schema in payload_indexes.items():
        try:
            client.create_payload_index(
                collection_name=collection_name,
                field_name=field_name,
                field_schema=field_schema
            )
        except Exception as e:
            logger.warning(f"Could not create index for {field_name}: {e}")
    
    logger.info("Collection created with named vectors (text: 384, image: 512)")
    return client


def load_products_from_json() -> List[Dict[str, Any]]:
    """Load products from generated JSON file."""
    output_dir = Path(__file__).parent / "output"
    products_file = output_dir / "products.json"
    
    if not products_file.exists():
        raise FileNotFoundError(f"Products file not found: {products_file}")
    
    with open(products_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    products = data.get("products", data) if isinstance(data, dict) else data
    logger.info(f"Loaded {len(products)} products from {products_file}")
    return products


def generate_text_embedding(text: str) -> List[float]:
    """Generate text embedding using sentence-transformers."""
    from sentence_transformers import SentenceTransformer
    
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def upload_products_with_dual_vectors(
    client,
    products: List[Dict[str, Any]],
    clip_model,
    clip_tokenizer,
    batch_size: int = 50
):
    """Upload products with both text and image embeddings."""
    from qdrant_client.models import PointStruct
    from sentence_transformers import SentenceTransformer
    
    # Load text embedding model
    text_model = SentenceTransformer("all-MiniLM-L6-v2")
    
    collection_name = "products"
    total_uploaded = 0
    
    # Process in batches
    for i in tqdm(range(0, len(products), batch_size), desc="Uploading products"):
        batch = products[i:i + batch_size]
        points = []
        
        for product in batch:
            # Create searchable text
            title = product.get("title", product.get("name", ""))
            description = product.get("description", "")
            category = product.get("category", "")
            brand = product.get("brand", "")
            tags = " ".join(product.get("tags", []))
            
            search_text = f"{title} {description} {category} {brand} {tags}"
            
            # Generate text embedding (384-dim)
            text_embedding = text_model.encode(
                search_text, 
                normalize_embeddings=True
            ).tolist()
            
            # Generate image embedding from description (512-dim)
            # This simulates CLIP embedding from product image
            image_text = f"{title}. {description[:200]}"
            image_embedding = generate_clip_text_embedding(
                clip_model, 
                clip_tokenizer, 
                image_text
            )
            
            # Prepare payload
            payload = {
                "title": title,
                "name": title,
                "description": description,
                "price": product.get("price", 0.0),
                "original_price": product.get("original_price"),
                "currency": product.get("currency", "USD"),
                "category": category,
                "subcategory": product.get("subcategory", ""),
                "brand": brand,
                "rating_avg": product.get("rating_avg", product.get("rating", 0.0)),
                "review_count": product.get("review_count", 0),
                "image_url": product.get("image_url", ""),
                "stock_status": product.get("stock_status", "in_stock"),
                "tags": product.get("tags", []),
                "attributes": product.get("attributes", {}),
                "payment_options": product.get("payment_options", [])
            }
            
            # Create point with named vectors
            # Generate a proper UUID from the product ID string
            product_id = product.get("id", str(i))
            # Convert non-UUID IDs to UUIDs using a consistent hash
            import hashlib
            if not is_valid_uuid(product_id):
                # Create a UUID from the product ID string
                id_hash = hashlib.md5(product_id.encode()).hexdigest()
                product_id = f"{id_hash[:8]}-{id_hash[8:12]}-{id_hash[12:16]}-{id_hash[16:20]}-{id_hash[20:32]}"
            
            point = PointStruct(
                id=product_id,
                vector={
                    "text": text_embedding,
                    "image": image_embedding
                },
                payload=payload
            )
            points.append(point)
        
        # Upload batch
        client.upsert(
            collection_name=collection_name,
            points=points
        )
        total_uploaded += len(points)
    
    logger.info(f"Uploaded {total_uploaded} products with dual vectors")
    return total_uploaded


def verify_collection(client):
    """Verify the collection was created correctly."""
    collection_name = "products"
    
    # Get collection info
    info = client.get_collection(collection_name)
    logger.info(f"Collection: {collection_name}")
    logger.info(f"  Points count: {info.points_count}")
    logger.info(f"  Vectors config: {info.config.params.vectors}")
    
    # Test search with text vector
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    query_embedding = model.encode("laptop computer", normalize_embeddings=True).tolist()
    
    results = client.query_points(
        collection_name=collection_name,
        query=query_embedding,
        using="text",  # Use named vector
        limit=3
    )
    
    logger.info(f"\nText search test ('laptop computer'):")
    for r in results.points:
        logger.info(f"  - {r.payload.get('title', 'N/A')} (score: {r.score:.3f})")
    
    return info.points_count


def main():
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("Adding Image Embeddings to Products Collection")
    logger.info("=" * 60)
    
    # Step 1: Load CLIP model
    logger.info("\nStep 1: Loading CLIP model...")
    clip_model, clip_processor, clip_tokenizer = get_clip_model()
    
    # Step 2: Recreate collection with named vectors
    logger.info("\nStep 2: Recreating collection with named vectors...")
    client = recreate_products_collection_with_named_vectors()
    
    # Step 3: Load products
    logger.info("\nStep 3: Loading products...")
    products = load_products_from_json()
    
    # Step 4: Upload with dual vectors
    logger.info("\nStep 4: Uploading products with text + image vectors...")
    uploaded = upload_products_with_dual_vectors(
        client, 
        products, 
        clip_model, 
        clip_tokenizer
    )
    
    # Step 5: Verify
    logger.info("\nStep 5: Verifying upload...")
    count = verify_collection(client)
    
    logger.info("\n" + "=" * 60)
    logger.info(f"SUCCESS: {count} products uploaded with dual vectors")
    logger.info("  - Text vector: 384 dimensions (all-MiniLM-L6-v2)")
    logger.info("  - Image vector: 512 dimensions (CLIP)")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
