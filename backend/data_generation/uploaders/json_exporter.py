"""
JSON Exporter for saving generated data to files.

Handles serialization and file output for all collection types
with proper formatting and metadata.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for handling datetime and other types."""
    
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, 'model_dump'):
            return obj.model_dump()
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)


class JSONExporter:
    """Exporter for saving generated data to JSON files."""
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize the JSON exporter.
        
        Args:
            output_dir: Directory for output files.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _serialize_item(self, item: Any) -> Dict:
        """Serialize a single item to a dictionary."""
        if hasattr(item, 'model_dump'):
            data = item.model_dump()
        elif hasattr(item, '__dict__'):
            data = item.__dict__.copy()
        else:
            data = item
        
        # Convert datetime objects
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
            elif hasattr(value, 'model_dump'):
                data[key] = value.model_dump()
        
        return data
    
    def export_products(self, products: List[Any], 
                        filename: str = "products.json") -> Path:
        """
        Export products to JSON file.
        
        Args:
            products: List of Product objects.
            filename: Output filename.
            
        Returns:
            Path to the output file.
        """
        output_path = self.output_dir / filename
        
        data = {
            "collection": "products",
            "generated_at": datetime.utcnow().isoformat(),
            "count": len(products),
            "items": [self._serialize_item(p) for p in products]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, cls=CustomJSONEncoder, indent=2)
        
        logger.info(f"Exported {len(products)} products to {output_path}")
        return output_path
    
    def export_reviews(self, reviews: List[Any],
                       filename: str = "reviews.json") -> Path:
        """
        Export reviews to JSON file.
        
        Args:
            reviews: List of Review objects.
            filename: Output filename.
            
        Returns:
            Path to the output file.
        """
        output_path = self.output_dir / filename
        
        data = {
            "collection": "reviews",
            "generated_at": datetime.utcnow().isoformat(),
            "count": len(reviews),
            "items": [self._serialize_item(r) for r in reviews]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, cls=CustomJSONEncoder, indent=2)
        
        logger.info(f"Exported {len(reviews)} reviews to {output_path}")
        return output_path
    
    def export_users(self, users: List[Any],
                     filename: str = "user_profiles.json") -> Path:
        """
        Export user profiles to JSON file.
        
        Args:
            users: List of User objects.
            filename: Output filename.
            
        Returns:
            Path to the output file.
        """
        output_path = self.output_dir / filename
        
        data = {
            "collection": "user_profiles",
            "generated_at": datetime.utcnow().isoformat(),
            "count": len(users),
            "items": [self._serialize_item(u) for u in users]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, cls=CustomJSONEncoder, indent=2)
        
        logger.info(f"Exported {len(users)} users to {output_path}")
        return output_path
    
    def export_interactions(self, interactions: List[Any],
                            filename: str = "user_interactions.json") -> Path:
        """
        Export interactions to JSON file.
        
        Args:
            interactions: List of Interaction objects.
            filename: Output filename.
            
        Returns:
            Path to the output file.
        """
        output_path = self.output_dir / filename
        
        data = {
            "collection": "user_interactions",
            "generated_at": datetime.utcnow().isoformat(),
            "count": len(interactions),
            "items": [self._serialize_item(i) for i in interactions]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, cls=CustomJSONEncoder, indent=2)
        
        logger.info(f"Exported {len(interactions)} interactions to {output_path}")
        return output_path
    
    def export_metadata(self, metadata: Dict[str, Any],
                        filename: str = "metadata.json") -> Path:
        """
        Export generation metadata.
        
        Args:
            metadata: Metadata dictionary.
            filename: Output filename.
            
        Returns:
            Path to the output file.
        """
        output_path = self.output_dir / filename
        
        data = {
            "generated_at": datetime.utcnow().isoformat(),
            **metadata
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, cls=CustomJSONEncoder, indent=2)
        
        logger.info(f"Exported metadata to {output_path}")
        return output_path
    
    def export_for_qdrant(self, items: List[Any], 
                          collection_name: str) -> Path:
        """
        Export data in Qdrant-ready format (points with vectors and payloads).
        
        Args:
            items: List of items with embedding and payload.
            collection_name: Name of the Qdrant collection.
            
        Returns:
            Path to the output file.
        """
        output_path = self.output_dir / f"{collection_name}_qdrant.json"
        
        points = []
        for item in items:
            if hasattr(item, 'to_qdrant_point'):
                point = item.to_qdrant_point()
            else:
                # Fallback for items without the method
                data = self._serialize_item(item)
                embedding = data.pop('embedding', [])
                point = {
                    "id": data.get('id') or data.get('review_id') or data.get('user_id'),
                    "vector": embedding,
                    "payload": data
                }
            points.append(point)
        
        data = {
            "collection": collection_name,
            "generated_at": datetime.utcnow().isoformat(),
            "count": len(points),
            "points": points
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, cls=CustomJSONEncoder)  # No indent for smaller files
        
        logger.info(f"Exported {len(points)} points for {collection_name} to {output_path}")
        return output_path
    
    def load_products(self, filename: str = "products.json") -> List[Dict]:
        """
        Load products from JSON file.
        
        Args:
            filename: Input filename.
            
        Returns:
            List of product dictionaries.
        """
        input_path = self.output_dir / filename
        
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data.get('items', [])
    
    def load_reviews(self, filename: str = "reviews.json") -> List[Dict]:
        """
        Load reviews from JSON file.
        
        Args:
            filename: Input filename.
            
        Returns:
            List of review dictionaries.
        """
        input_path = self.output_dir / filename
        
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data.get('items', [])
