"""
Cache Service for FinFind.

Provides unified caching for all agent operations with:
- TTL-based expiration
- Multi-level caching
- Statistics tracking
"""

import logging
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta
from collections import OrderedDict
import hashlib
import json
import threading

logger = logging.getLogger(__name__)


class CacheEntry:
    """Single cache entry with metadata."""
    
    def __init__(
        self,
        value: Any,
        ttl_seconds: int,
        tags: Optional[List[str]] = None
    ):
        self.value = value
        self.created_at = datetime.utcnow()
        self.last_accessed = datetime.utcnow()
        self.ttl = timedelta(seconds=ttl_seconds)
        self.tags = tags or []
        self.hit_count = 0
    
    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.created_at + self.ttl
    
    def access(self) -> Any:
        """Record access and return value."""
        self.last_accessed = datetime.utcnow()
        self.hit_count += 1
        return self.value


class CacheService:
    """
    Centralized cache service for agents.
    
    Features:
    - LRU eviction
    - TTL expiration
    - Tag-based invalidation
    - Thread-safe operations
    """
    
    def __init__(
        self,
        max_size: int = 5000,
        default_ttl: int = 300
    ):
        """
        Initialize cache service.
        
        Args:
            max_size: Maximum cache entries.
            default_ttl: Default TTL in seconds.
        """
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = threading.RLock()
        
        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
    
    def _make_key(self, namespace: str, key: str) -> str:
        """Create namespaced cache key."""
        return f"{namespace}:{key}"
    
    def _hash_key(self, data: Any) -> str:
        """Hash complex data to create key."""
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(json_str.encode()).hexdigest()
    
    def get(
        self,
        namespace: str,
        key: str
    ) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            namespace: Cache namespace.
            key: Cache key.
            
        Returns:
            Cached value or None if not found/expired.
        """
        full_key = self._make_key(namespace, key)
        
        with self._lock:
            entry = self._cache.get(full_key)
            
            if entry is None:
                self._misses += 1
                return None
            
            if entry.is_expired:
                del self._cache[full_key]
                self._misses += 1
                return None
            
            # Move to end (LRU)
            self._cache.move_to_end(full_key)
            self._hits += 1
            
            return entry.access()
    
    def set(
        self,
        namespace: str,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        tags: Optional[List[str]] = None
    ):
        """
        Set value in cache.
        
        Args:
            namespace: Cache namespace.
            key: Cache key.
            value: Value to cache.
            ttl: Time to live in seconds.
            tags: Tags for grouping/invalidation.
        """
        full_key = self._make_key(namespace, key)
        ttl = ttl or self._default_ttl
        
        with self._lock:
            # Evict if at capacity
            while len(self._cache) >= self._max_size:
                self._evict_oldest()
            
            self._cache[full_key] = CacheEntry(value, ttl, tags)
            self._cache.move_to_end(full_key)
    
    def delete(self, namespace: str, key: str) -> bool:
        """Delete a specific key."""
        full_key = self._make_key(namespace, key)
        
        with self._lock:
            if full_key in self._cache:
                del self._cache[full_key]
                return True
            return False
    
    def invalidate_namespace(self, namespace: str):
        """Invalidate all keys in a namespace."""
        prefix = f"{namespace}:"
        
        with self._lock:
            keys_to_delete = [
                k for k in self._cache.keys()
                if k.startswith(prefix)
            ]
            
            for key in keys_to_delete:
                del self._cache[key]
            
            if keys_to_delete:
                logger.info(f"Invalidated {len(keys_to_delete)} keys in namespace '{namespace}'")
    
    def invalidate_by_tag(self, tag: str):
        """Invalidate all entries with a specific tag."""
        with self._lock:
            keys_to_delete = [
                k for k, v in self._cache.items()
                if tag in v.tags
            ]
            
            for key in keys_to_delete:
                del self._cache[key]
            
            if keys_to_delete:
                logger.info(f"Invalidated {len(keys_to_delete)} keys with tag '{tag}'")
    
    def _evict_oldest(self):
        """Evict the oldest entry (LRU)."""
        if self._cache:
            self._cache.popitem(last=False)
            self._evictions += 1
    
    def cleanup_expired(self):
        """Remove all expired entries."""
        with self._lock:
            expired = [
                k for k, v in self._cache.items()
                if v.is_expired
            ]
            
            for key in expired:
                del self._cache[key]
            
            if expired:
                logger.info(f"Cleaned up {len(expired)} expired cache entries")
    
    def clear(self):
        """Clear entire cache."""
        with self._lock:
            self._cache.clear()
            logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._hits + self._misses
        
        with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": self._hits / total_requests if total_requests > 0 else 0,
                "evictions": self._evictions,
                "default_ttl": self._default_ttl
            }
    
    def get_keys(self, namespace: Optional[str] = None) -> List[str]:
        """Get all cache keys, optionally filtered by namespace."""
        with self._lock:
            if namespace:
                prefix = f"{namespace}:"
                return [k for k in self._cache.keys() if k.startswith(prefix)]
            return list(self._cache.keys())
    
    # ========================================
    # Convenience Methods
    # ========================================
    
    def get_or_compute(
        self,
        namespace: str,
        key: str,
        compute_fn,
        ttl: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> Any:
        """
        Get from cache or compute and cache.
        
        Args:
            namespace: Cache namespace.
            key: Cache key.
            compute_fn: Function to compute value if not cached.
            ttl: Time to live.
            tags: Tags for invalidation.
            
        Returns:
            Cached or computed value.
        """
        cached = self.get(namespace, key)
        if cached is not None:
            return cached
        
        value = compute_fn()
        self.set(namespace, key, value, ttl, tags)
        return value
    
    async def get_or_compute_async(
        self,
        namespace: str,
        key: str,
        compute_fn,
        ttl: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> Any:
        """Async version of get_or_compute."""
        cached = self.get(namespace, key)
        if cached is not None:
            return cached
        
        value = await compute_fn()
        self.set(namespace, key, value, ttl, tags)
        return value


# Global cache service instance
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Get or create the global cache service."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service
