"""
Redis Search Cache for FinFind.

Provides caching for search queries to reduce latency and vector database load.
"""

import os
import json
import hashlib
import logging
from typing import Optional, Dict, Any, List
from datetime import timedelta

logger = logging.getLogger(__name__)

# In-memory fallback cache when Redis is not available
_memory_cache: Dict[str, Dict[str, Any]] = {}
MAX_MEMORY_CACHE = 200


def _create_cache_key(query: str, filters: Optional[Dict] = None, strategy: str = "balanced") -> str:
    """Create a unique cache key from search parameters."""
    key_data = {
        "query": query.lower().strip(),
        "filters": filters or {},
        "strategy": strategy
    }
    key_str = json.dumps(key_data, sort_keys=True)
    return f"search:{hashlib.md5(key_str.encode()).hexdigest()}"


class SearchCacheService:
    """
    Redis-based search cache with in-memory fallback.
    
    Caches search results to:
    - Reduce latency for frequent searches
    - Lower vector database query load
    - Save embedding computation costs
    """
    
    def __init__(
        self,
        redis_url: Optional[str] = None,
        default_ttl_seconds: int = 300,  # 5 minutes
        enabled: bool = True
    ):
        self._redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self._redis = None
        self._enabled = enabled
        self._default_ttl = default_ttl_seconds
        self._use_memory_fallback = True
        
    async def connect(self) -> bool:
        """Connect to Redis. Returns True if connected."""
        if not self._enabled:
            logger.info("Search cache disabled")
            return False
            
        try:
            import redis.asyncio as aioredis
            self._redis = aioredis.from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Ping returns True for async redis
            pong = await self._redis.ping()  # type: ignore
            if pong:
                self._use_memory_fallback = False
                logger.info("Search cache connected to Redis")
                return True
            return False
        except ImportError:
            logger.warning("redis package not installed, using memory cache")
            self._use_memory_fallback = True
            return False
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}, using memory cache")
            self._use_memory_fallback = True
            return False
    
    async def disconnect(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None
    
    async def get(
        self,
        query: str,
        filters: Optional[Dict] = None,
        strategy: str = "balanced"
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached search results.
        
        Returns:
            Cached response dict or None if not cached
        """
        if not self._enabled:
            return None
            
        cache_key = _create_cache_key(query, filters, strategy)
        
        try:
            if self._use_memory_fallback:
                entry = _memory_cache.get(cache_key)
                if entry:
                    logger.debug(f"Memory cache hit: {cache_key[:20]}...")
                    return entry.get("data")
                return None
            
            if self._redis:
                cached = await self._redis.get(cache_key)
                if cached:
                    logger.debug(f"Redis cache hit: {cache_key[:20]}...")
                    return json.loads(cached)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        
        return None
    
    async def set(
        self,
        query: str,
        filters: Optional[Dict],
        strategy: str,
        response: Dict[str, Any],
        ttl_seconds: Optional[int] = None
    ):
        """
        Cache search results.
        
        Args:
            query: Search query
            filters: Applied filters
            strategy: Ranking strategy used
            response: Full response to cache
            ttl_seconds: Cache TTL (default: 5 minutes)
        """
        if not self._enabled:
            return
            
        cache_key = _create_cache_key(query, filters, strategy)
        ttl = ttl_seconds or self._default_ttl
        
        try:
            if self._use_memory_fallback:
                # Memory cache with size limit
                global _memory_cache
                if len(_memory_cache) >= MAX_MEMORY_CACHE:
                    # Remove oldest entry
                    if _memory_cache:
                        oldest = next(iter(_memory_cache))
                        del _memory_cache[oldest]
                _memory_cache[cache_key] = {"data": response}
                logger.debug(f"Memory cached: {cache_key[:20]}...")
                return
            
            if self._redis:
                await self._redis.setex(
                    cache_key,
                    timedelta(seconds=ttl),
                    json.dumps(response)
                )
                logger.debug(f"Redis cached: {cache_key[:20]}...")
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    async def invalidate(self, query: str, filters: Optional[Dict] = None, strategy: str = "balanced"):
        """Remove a specific cache entry."""
        cache_key = _create_cache_key(query, filters, strategy)
        
        try:
            if self._use_memory_fallback:
                _memory_cache.pop(cache_key, None)
            elif self._redis:
                await self._redis.delete(cache_key)
        except Exception as e:
            logger.error(f"Cache invalidate error: {e}")
    
    async def clear_all(self):
        """Clear all search cache entries."""
        try:
            if self._use_memory_fallback:
                global _memory_cache
                _memory_cache = {}
            elif self._redis:
                async for key in self._redis.scan_iter("search:*"):
                    await self._redis.delete(key)
                logger.info("Search cache cleared")
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {
            "enabled": self._enabled,
            "backend": "redis" if not self._use_memory_fallback else "memory",
            "connected": self._redis is not None and not self._use_memory_fallback,
        }
        
        try:
            if self._use_memory_fallback:
                stats["entries"] = len(_memory_cache)
                stats["max_entries"] = MAX_MEMORY_CACHE
            elif self._redis:
                count = 0
                async for _ in self._redis.scan_iter("search:*"):
                    count += 1
                stats["entries"] = count
                
                info = await self._redis.info("memory")
                stats["memory_used"] = info.get("used_memory_human", "unknown")
        except Exception as e:
            stats["error"] = str(e)
        
        return stats


# Singleton instance
_cache_instance: Optional[SearchCacheService] = None


async def get_search_cache() -> SearchCacheService:
    """Get or create the search cache singleton."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = SearchCacheService(
            enabled=os.getenv("SEARCH_CACHE_ENABLED", "true").lower() == "true",
            default_ttl_seconds=int(os.getenv("SEARCH_CACHE_TTL", "300"))
        )
        await _cache_instance.connect()
    return _cache_instance
