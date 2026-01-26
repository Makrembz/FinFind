"""
Qdrant Cloud Uploader for FinFind synthetic data.

Handles connection, collection creation, batch uploading,
and verification of all data collections.
"""

import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from dotenv import load_dotenv
from tqdm import tqdm

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class UploadConfig:
    """Configuration for Qdrant upload."""
    
    # Qdrant connection
    qdrant_url: str = field(default_factory=lambda: os.getenv("QDRANT_URL", ""))
    qdrant_api_key: str = field(default_factory=lambda: os.getenv("QDRANT_API_KEY", ""))
    
    # Collection names
    products_collection: str = field(
        default_factory=lambda: os.getenv("QDRANT_PRODUCTS_COLLECTION", "products")
    )
    user_profiles_collection: str = field(
        default_factory=lambda: os.getenv("QDRANT_USER_PROFILES_COLLECTION", "user_profiles")
    )
    reviews_collection: str = field(
        default_factory=lambda: os.getenv("QDRANT_REVIEWS_COLLECTION", "reviews")
    )
    interactions_collection: str = field(
        default_factory=lambda: os.getenv("QDRANT_INTERACTIONS_COLLECTION", "user_interactions")
    )
    
    # Vector dimensions
    text_embedding_dim: int = 384
    
    # Upload settings
    batch_size: int = 100
    max_retries: int = 3
    retry_delay: float = 2.0
    timeout: int = 60
    
    # Input directory
    input_dir: Path = field(default_factory=lambda: Path("output"))
    
    def validate(self) -> Tuple[bool, List[str]]:
        """Validate configuration."""
        errors = []
        
        if not self.qdrant_url:
            errors.append("QDRANT_URL not set")
        if not self.qdrant_api_key:
            errors.append("QDRANT_API_KEY not set")
        if not self.input_dir.exists():
            errors.append(f"Input directory not found: {self.input_dir}")
        
        return len(errors) == 0, errors


@dataclass
class CollectionSchema:
    """Schema definition for a Qdrant collection."""
    
    name: str
    vector_size: int
    distance: str = "Cosine"
    
    # Payload indexes for filtering
    payload_indexes: Dict[str, str] = field(default_factory=dict)
    
    # Optional named vectors
    named_vectors: Optional[Dict[str, Dict]] = None


class QdrantUploader:
    """Uploader for Qdrant Cloud."""
    
    # Collection schemas
    COLLECTION_SCHEMAS = {
        "products": CollectionSchema(
            name="products",
            vector_size=384,
            payload_indexes={
                "category": "keyword",
                "subcategory": "keyword",
                "brand": "keyword",
                "price": "float",
                "rating_avg": "float",
                "stock_status": "keyword",
                "tags": "keyword"
            }
        ),
        "user_profiles": CollectionSchema(
            name="user_profiles",
            vector_size=384,
            payload_indexes={
                "persona_type": "keyword",
                "age_range": "keyword",
                "budget_min": "float",
                "budget_max": "float",
                "affordability_score": "float",
                "primary_payment_method": "keyword"
            }
        ),
        "reviews": CollectionSchema(
            name="reviews",
            vector_size=384,
            payload_indexes={
                "product_id": "keyword",
                "rating": "integer",
                "sentiment": "keyword",
                "sentiment_score": "float",
                "verified_purchase": "bool"
            }
        ),
        "user_interactions": CollectionSchema(
            name="user_interactions",
            vector_size=384,
            payload_indexes={
                "user_id": "keyword",
                "session_id": "keyword",
                "interaction_type": "keyword",
                "product_id": "keyword",
                "device_type": "keyword",
                "led_to_conversion": "bool"
            }
        )
    }
    
    def __init__(self, config: Optional[UploadConfig] = None):
        """
        Initialize the uploader.
        
        Args:
            config: Upload configuration.
        """
        self.config = config or UploadConfig()
        self._client = None
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate configuration and raise if invalid."""
        is_valid, errors = self.config.validate()
        if not is_valid:
            raise ValueError(f"Invalid configuration: {', '.join(errors)}")
    
    def _get_client(self):
        """Get or create Qdrant client."""
        if self._client is None:
            try:
                from qdrant_client import QdrantClient
                
                logger.info(f"Connecting to Qdrant Cloud: {self.config.qdrant_url}")
                self._client = QdrantClient(
                    url=self.config.qdrant_url,
                    api_key=self.config.qdrant_api_key,
                    timeout=self.config.timeout
                )
                
                # Test connection
                self._client.get_collections()
                logger.info("Successfully connected to Qdrant Cloud")
                
            except ImportError:
                raise ImportError(
                    "qdrant-client not installed. "
                    "Run: pip install qdrant-client"
                )
            except Exception as e:
                raise ConnectionError(f"Failed to connect to Qdrant: {e}")
        
        return self._client
    
    def create_collection(self, schema: CollectionSchema, recreate: bool = False) -> bool:
        """
        Create a collection with the specified schema.
        
        Args:
            schema: Collection schema definition.
            recreate: If True, delete and recreate existing collection.
            
        Returns:
            True if collection was created or already exists.
        """
        from qdrant_client.models import (
            VectorParams, Distance, PayloadSchemaType
        )
        
        client = self._get_client()
        
        # Check if collection exists
        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if schema.name in collection_names:
            if recreate:
                logger.info(f"Deleting existing collection: {schema.name}")
                client.delete_collection(schema.name)
            else:
                logger.info(f"Collection already exists: {schema.name}")
                return True
        
        # Create collection
        logger.info(f"Creating collection: {schema.name}")
        
        # Map distance string to Distance enum
        distance_map = {
            "Cosine": Distance.COSINE,
            "Euclid": Distance.EUCLID,
            "Dot": Distance.DOT
        }
        
        client.create_collection(
            collection_name=schema.name,
            vectors_config=VectorParams(
                size=schema.vector_size,
                distance=distance_map.get(schema.distance, Distance.COSINE)
            )
        )
        
        # Create payload indexes
        schema_type_map = {
            "keyword": PayloadSchemaType.KEYWORD,
            "integer": PayloadSchemaType.INTEGER,
            "float": PayloadSchemaType.FLOAT,
            "bool": PayloadSchemaType.BOOL,
            "text": PayloadSchemaType.TEXT
        }
        
        for field_name, field_type in schema.payload_indexes.items():
            try:
                client.create_payload_index(
                    collection_name=schema.name,
                    field_name=field_name,
                    field_schema=schema_type_map.get(field_type, PayloadSchemaType.KEYWORD)
                )
                logger.debug(f"Created index: {schema.name}.{field_name}")
            except Exception as e:
                logger.warning(f"Failed to create index {field_name}: {e}")
        
        logger.info(f"Collection created: {schema.name}")
        return True
    
    def create_all_collections(self, recreate: bool = False) -> Dict[str, bool]:
        """
        Create all collections.
        
        Args:
            recreate: If True, delete and recreate existing collections.
            
        Returns:
            Dict mapping collection name to creation success.
        """
        results = {}
        
        for name, schema in self.COLLECTION_SCHEMAS.items():
            # Map generic name to config-specific name
            collection_name = getattr(self.config, f"{name}_collection", name)
            schema.name = collection_name
            
            try:
                results[collection_name] = self.create_collection(schema, recreate)
            except Exception as e:
                logger.error(f"Failed to create collection {collection_name}: {e}")
                results[collection_name] = False
        
        return results
    
    def load_json_file(self, filename: str) -> Dict:
        """
        Load data from a JSON file.
        
        Args:
            filename: Name of the JSON file.
            
        Returns:
            Loaded JSON data.
        """
        filepath = self.config.input_dir / filename
        
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        logger.info(f"Loading data from: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data
    
    def _prepare_point(self, item: Dict, collection_type: str) -> Dict:
        """
        Prepare a point for upload.
        
        Args:
            item: Raw item data.
            collection_type: Type of collection (products, reviews, etc.).
            
        Returns:
            Prepared point dict with id, vector, payload.
        """
        from qdrant_client.models import PointStruct
        
        # Extract or generate ID
        point_id = item.get('id') or item.get('review_id') or item.get('user_id')
        if not point_id:
            point_id = str(uuid.uuid4())
        
        # Handle string IDs (Qdrant prefers int or UUID)
        if isinstance(point_id, str):
            # Keep string ID but ensure it's UUID-compatible for Qdrant
            if point_id.startswith(('prod_', 'user_', 'rev_', 'int_', 'sess_')):
                # Create deterministic UUID from string ID
                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, point_id))
        
        # Extract vector
        vector = item.get('embedding') or item.get('query_embedding') or []
        
        # If no vector, create a zero vector (will be updated later)
        if not vector or len(vector) == 0:
            vector = [0.0] * self.config.text_embedding_dim
        
        # Prepare payload (everything except embedding)
        payload = {k: v for k, v in item.items() if k not in ['embedding', 'query_embedding']}
        
        # Store original ID in payload for reference
        original_id = item.get('id') or item.get('review_id') or item.get('user_id')
        if original_id:
            payload['original_id'] = original_id
        
        return PointStruct(
            id=point_id,
            vector=vector,
            payload=payload
        )
    
    def upload_batch(
        self, 
        collection_name: str, 
        points: List, 
        retry_count: int = 0
    ) -> bool:
        """
        Upload a batch of points with retry logic.
        
        Args:
            collection_name: Target collection name.
            points: List of PointStruct objects.
            retry_count: Current retry attempt.
            
        Returns:
            True if upload succeeded.
        """
        client = self._get_client()
        
        try:
            client.upsert(
                collection_name=collection_name,
                points=points,
                wait=True
            )
            return True
            
        except Exception as e:
            if retry_count < self.config.max_retries:
                logger.warning(
                    f"Upload failed, retrying ({retry_count + 1}/{self.config.max_retries}): {e}"
                )
                time.sleep(self.config.retry_delay * (retry_count + 1))
                return self.upload_batch(collection_name, points, retry_count + 1)
            else:
                logger.error(f"Upload failed after {self.config.max_retries} retries: {e}")
                raise
    
    def upload_collection(
        self, 
        collection_name: str, 
        items: List[Dict],
        collection_type: str
    ) -> Tuple[int, int]:
        """
        Upload all items to a collection.
        
        Args:
            collection_name: Target collection name.
            items: List of items to upload.
            collection_type: Type of collection for point preparation.
            
        Returns:
            Tuple of (successful_count, failed_count).
        """
        logger.info(f"Uploading {len(items)} items to {collection_name}...")
        
        successful = 0
        failed = 0
        
        # Process in batches
        for i in tqdm(range(0, len(items), self.config.batch_size), 
                      desc=f"Uploading {collection_name}"):
            batch = items[i:i + self.config.batch_size]
            
            # Prepare points
            points = []
            for item in batch:
                try:
                    point = self._prepare_point(item, collection_type)
                    points.append(point)
                except Exception as e:
                    logger.warning(f"Failed to prepare point: {e}")
                    failed += 1
                    continue
            
            # Upload batch
            try:
                self.upload_batch(collection_name, points)
                successful += len(points)
            except Exception as e:
                logger.error(f"Batch upload failed: {e}")
                failed += len(points)
        
        logger.info(f"Upload complete: {successful} successful, {failed} failed")
        return successful, failed
    
    def upload_all(self, recreate_collections: bool = False) -> Dict[str, Dict]:
        """
        Upload all data to Qdrant Cloud.
        
        Args:
            recreate_collections: If True, recreate collections.
            
        Returns:
            Dict with upload results for each collection.
        """
        results = {}
        
        # Create collections
        logger.info("=" * 60)
        logger.info("Creating collections...")
        logger.info("=" * 60)
        
        collection_results = self.create_all_collections(recreate=recreate_collections)
        
        # Define file mappings
        file_mappings = [
            ("products_qdrant.json", self.config.products_collection, "products"),
            ("user_profiles_qdrant.json", self.config.user_profiles_collection, "user_profiles"),
            ("reviews_qdrant.json", self.config.reviews_collection, "reviews"),
            ("user_interactions_qdrant.json", self.config.interactions_collection, "user_interactions")
        ]
        
        # Fallback to regular JSON if Qdrant-specific files don't exist
        fallback_mappings = [
            ("products.json", self.config.products_collection, "products"),
            ("user_profiles.json", self.config.user_profiles_collection, "user_profiles"),
            ("reviews.json", self.config.reviews_collection, "reviews"),
            ("user_interactions.json", self.config.interactions_collection, "user_interactions")
        ]
        
        # Upload each collection
        for (qdrant_file, collection_name, collection_type), (fallback_file, _, _) in zip(
            file_mappings, fallback_mappings
        ):
            logger.info("=" * 60)
            logger.info(f"Uploading {collection_name}...")
            logger.info("=" * 60)
            
            # Try Qdrant-specific file first
            try:
                filepath = self.config.input_dir / qdrant_file
                if filepath.exists():
                    data = self.load_json_file(qdrant_file)
                    items = data.get('points', data.get('items', []))
                else:
                    # Fall back to regular JSON
                    data = self.load_json_file(fallback_file)
                    items = data.get('items', [])
                
                successful, failed = self.upload_collection(
                    collection_name, items, collection_type
                )
                
                results[collection_name] = {
                    "status": "success" if failed == 0 else "partial",
                    "total": len(items),
                    "successful": successful,
                    "failed": failed
                }
                
            except FileNotFoundError as e:
                logger.warning(f"File not found: {e}")
                results[collection_name] = {
                    "status": "skipped",
                    "error": str(e)
                }
            except Exception as e:
                logger.error(f"Upload failed for {collection_name}: {e}")
                results[collection_name] = {
                    "status": "failed",
                    "error": str(e)
                }
        
        return results
    
    def get_collection_info(self, collection_name: str) -> Dict:
        """Get information about a collection."""
        client = self._get_client()
        
        try:
            info = client.get_collection(collection_name)
            return {
                "name": collection_name,
                "points_count": info.points_count,
                "vectors_count": info.vectors_count,
                "status": info.status.value if info.status else "unknown"
            }
        except Exception as e:
            return {
                "name": collection_name,
                "error": str(e)
            }
    
    def get_all_collections_info(self) -> Dict[str, Dict]:
        """Get information about all collections."""
        collections = [
            self.config.products_collection,
            self.config.user_profiles_collection,
            self.config.reviews_collection,
            self.config.interactions_collection
        ]
        
        return {name: self.get_collection_info(name) for name in collections}


def main():
    """Main entry point for uploading data."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Upload data to Qdrant Cloud")
    parser.add_argument(
        '--recreate', '-r',
        action='store_true',
        help='Recreate collections (delete existing data)'
    )
    parser.add_argument(
        '--input-dir', '-i',
        type=str,
        default='output',
        help='Input directory with JSON files'
    )
    parser.add_argument(
        '--batch-size', '-b',
        type=int,
        default=100,
        help='Batch size for uploads'
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create config
    config = UploadConfig(
        input_dir=Path(args.input_dir),
        batch_size=args.batch_size
    )
    
    # Create uploader and run
    try:
        uploader = QdrantUploader(config)
        results = uploader.upload_all(recreate_collections=args.recreate)
        
        # Print summary
        print("\n" + "=" * 60)
        print("UPLOAD SUMMARY")
        print("=" * 60)
        
        for collection, result in results.items():
            status = result.get('status', 'unknown')
            if status == 'success':
                print(f"✓ {collection}: {result['successful']} points uploaded")
            elif status == 'partial':
                print(f"⚠ {collection}: {result['successful']}/{result['total']} points uploaded")
            elif status == 'skipped':
                print(f"⊘ {collection}: skipped - {result.get('error', 'unknown')}")
            else:
                print(f"✗ {collection}: failed - {result.get('error', 'unknown')}")
        
        print("=" * 60)
        
        # Get final collection info
        print("\nCollection Info:")
        info = uploader.get_all_collections_info()
        for name, details in info.items():
            if 'error' not in details:
                print(f"  {name}: {details['points_count']} points, status: {details['status']}")
            else:
                print(f"  {name}: error - {details['error']}")
        
    except Exception as e:
        logger.exception(f"Upload failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
