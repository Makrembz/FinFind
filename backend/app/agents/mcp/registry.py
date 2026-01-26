"""
MCP Tool Registry for FinFind.

Manages registration, discovery, and access to MCP tools.
Provides caching and performance optimization.
"""

import logging
from typing import Dict, Any, List, Optional, Type
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib
import json

from .protocol import MCPTool, MCPToolMetadata, MCPError, MCPErrorCode

logger = logging.getLogger(__name__)


class CacheEntry:
    """Cache entry with TTL support."""
    
    def __init__(self, data: Any, ttl_seconds: int):
        self.data = data
        self.created_at = datetime.utcnow()
        self.ttl = timedelta(seconds=ttl_seconds)
        self.hit_count = 0
    
    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.created_at + self.ttl
    
    def hit(self) -> Any:
        """Record a cache hit and return data."""
        self.hit_count += 1
        return self.data


class MCPToolCache:
    """
    In-memory cache for MCP tool results.
    
    Features:
    - TTL-based expiration
    - LRU eviction
    - Hit/miss statistics
    """
    
    def __init__(self, max_size: int = 1000):
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._hits = 0
        self._misses = 0
    
    def _make_key(self, tool_name: str, params: Dict) -> str:
        """Create cache key from tool name and parameters."""
        param_str = json.dumps(params, sort_keys=True, default=str)
        hash_str = hashlib.md5(f"{tool_name}:{param_str}".encode()).hexdigest()
        return f"{tool_name}:{hash_str}"
    
    def get(self, tool_name: str, params: Dict) -> Optional[Any]:
        """Get cached result if available and not expired."""
        key = self._make_key(tool_name, params)
        entry = self._cache.get(key)
        
        if entry is None:
            self._misses += 1
            return None
        
        if entry.is_expired:
            del self._cache[key]
            self._misses += 1
            return None
        
        self._hits += 1
        return entry.hit()
    
    def set(self, tool_name: str, params: Dict, data: Any, ttl_seconds: int):
        """Cache a result with TTL."""
        # Evict if at max size
        if len(self._cache) >= self._max_size:
            self._evict_oldest()
        
        key = self._make_key(tool_name, params)
        self._cache[key] = CacheEntry(data, ttl_seconds)
    
    def _evict_oldest(self):
        """Evict oldest entries (simple LRU approximation)."""
        if not self._cache:
            return
        
        # Remove 10% of oldest entries
        entries = sorted(
            self._cache.items(),
            key=lambda x: x[1].created_at
        )
        
        to_remove = max(1, len(entries) // 10)
        for key, _ in entries[:to_remove]:
            del self._cache[key]
    
    def invalidate(self, tool_name: Optional[str] = None):
        """Invalidate cache entries."""
        if tool_name is None:
            self._cache.clear()
        else:
            keys_to_remove = [
                k for k in self._cache.keys() 
                if k.startswith(f"{tool_name}:")
            ]
            for key in keys_to_remove:
                del self._cache[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self._hits + self._misses
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / total if total > 0 else 0
        }


class MCPToolRegistry:
    """
    Central registry for MCP tools.
    
    Features:
    - Tool registration and discovery
    - Category-based organization
    - Shared caching
    - Usage statistics
    """
    
    def __init__(self, cache_size: int = 1000):
        self._tools: Dict[str, MCPTool] = {}
        self._categories: Dict[str, List[str]] = defaultdict(list)
        self._cache = MCPToolCache(max_size=cache_size)
        self._initialized = False
    
    def register(self, tool: MCPTool):
        """Register a tool with the registry."""
        name = tool.name
        
        if name in self._tools:
            logger.warning(f"Tool '{name}' already registered, replacing")
        
        self._tools[name] = tool
        
        # Add to category
        category = tool.metadata.category
        if name not in self._categories[category]:
            self._categories[category].append(name)
        
        logger.info(f"Registered MCP tool: {name} (category: {category})")
    
    def unregister(self, name: str):
        """Remove a tool from the registry."""
        if name in self._tools:
            tool = self._tools.pop(name)
            category = tool.metadata.category
            if name in self._categories[category]:
                self._categories[category].remove(name)
            self._cache.invalidate(name)
            logger.info(f"Unregistered MCP tool: {name}")
    
    def get(self, name: str) -> Optional[MCPTool]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def get_by_category(self, category: str) -> List[MCPTool]:
        """Get all tools in a category."""
        tool_names = self._categories.get(category, [])
        return [self._tools[name] for name in tool_names if name in self._tools]
    
    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self._tools.keys())
    
    def list_categories(self) -> List[str]:
        """List all categories."""
        return list(self._categories.keys())
    
    def execute(
        self,
        tool_name: str,
        params: Dict[str, Any],
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a tool with optional caching.
        
        Args:
            tool_name: Name of the tool to execute.
            params: Parameters to pass to the tool.
            use_cache: Whether to use caching.
            
        Returns:
            Tool output dictionary.
        """
        tool = self.get(tool_name)
        if tool is None:
            return {
                "success": False,
                "error": {
                    "code": MCPErrorCode.RESOURCE_NOT_FOUND.value,
                    "message": f"Tool '{tool_name}' not found"
                }
            }
        
        # Check cache
        if use_cache and tool.metadata.cacheable:
            cached = self._cache.get(tool_name, params)
            if cached is not None:
                cached["metadata"]["cache_hit"] = True
                return cached
        
        # Execute tool
        result = tool._run(**params)
        
        # Cache result if successful and cacheable
        if (
            use_cache and 
            tool.metadata.cacheable and 
            result.get("success", False)
        ):
            self._cache.set(
                tool_name,
                params,
                result,
                tool.metadata.cache_ttl_seconds
            )
        
        return result
    
    async def execute_async(
        self,
        tool_name: str,
        params: Dict[str, Any],
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Async execution with caching."""
        tool = self.get(tool_name)
        if tool is None:
            return {
                "success": False,
                "error": {
                    "code": MCPErrorCode.RESOURCE_NOT_FOUND.value,
                    "message": f"Tool '{tool_name}' not found"
                }
            }
        
        # Check cache
        if use_cache and tool.metadata.cacheable:
            cached = self._cache.get(tool_name, params)
            if cached is not None:
                cached["metadata"]["cache_hit"] = True
                return cached
        
        # Execute tool
        result = await tool._arun(**params)
        
        # Cache result
        if (
            use_cache and 
            tool.metadata.cacheable and 
            result.get("success", False)
        ):
            self._cache.set(
                tool_name,
                params,
                result,
                tool.metadata.cache_ttl_seconds
            )
        
        return result
    
    def execute_batch(
        self,
        requests: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple tools in batch.
        
        Each request should have:
        - tool_name: str
        - params: Dict
        - use_cache: bool (optional)
        """
        results = []
        for request in requests:
            tool_name = request.get("tool_name")
            params = request.get("params", {})
            use_cache = request.get("use_cache", True)
            
            result = self.execute(tool_name, params, use_cache)
            results.append({
                "tool_name": tool_name,
                "result": result
            })
        
        return results
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all tools."""
        return {
            "tools": {
                name: tool.get_stats() 
                for name, tool in self._tools.items()
            },
            "cache": self._cache.get_stats(),
            "total_tools": len(self._tools),
            "categories": dict(self._categories)
        }
    
    def get_tool_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a tool."""
        tool = self.get(name)
        if tool is None:
            return None
        
        return {
            "name": tool.name,
            "description": tool.description,
            "metadata": tool.metadata.to_dict(),
            "stats": tool.get_stats(),
            "args_schema": tool.args_schema.schema() if tool.args_schema else None
        }


# Global registry instance
_registry: Optional[MCPToolRegistry] = None


def get_tool_registry() -> MCPToolRegistry:
    """Get or create the global tool registry."""
    global _registry
    if _registry is None:
        _registry = MCPToolRegistry()
    return _registry


def register_tool(tool: MCPTool):
    """Convenience function to register a tool."""
    get_tool_registry().register(tool)


def execute_tool(tool_name: str, **params) -> Dict[str, Any]:
    """Convenience function to execute a tool."""
    return get_tool_registry().execute(tool_name, params)
