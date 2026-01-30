"""
LLM Response Caching for FinFind Agents.

Implements caching to reduce API calls and costs.
"""

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

# Cache directory
CACHE_DIR = Path(__file__).parent / ".llm_cache"
CACHE_DIR.mkdir(exist_ok=True)

# In-memory LRU cache for session
_memory_cache: Dict[str, Dict[str, Any]] = {}
MAX_MEMORY_CACHE = 500


def _hash_key(prompt: str, model: str) -> str:
    """Create a hash key for caching."""
    content = f"{model}::{prompt}"
    return hashlib.sha256(content.encode()).hexdigest()[:32]


def get_cached_response(prompt: str, model: str, max_age_hours: int = 24) -> Optional[str]:
    """
    Get a cached LLM response if available.
    
    Args:
        prompt: The prompt text
        model: The model name
        max_age_hours: Maximum cache age in hours
        
    Returns:
        Cached response or None
    """
    cache_key = _hash_key(prompt, model)
    
    # Check memory cache first
    if cache_key in _memory_cache:
        entry = _memory_cache[cache_key]
        age_hours = (time.time() - entry['timestamp']) / 3600
        if age_hours < max_age_hours:
            logger.debug(f"Cache hit (memory): {cache_key[:8]}...")
            return entry['response']
    
    # Check disk cache
    cache_file = CACHE_DIR / f"{cache_key}.json"
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                entry = json.load(f)
            age_hours = (time.time() - entry['timestamp']) / 3600
            if age_hours < max_age_hours:
                # Also store in memory for faster access
                _memory_cache[cache_key] = entry
                logger.debug(f"Cache hit (disk): {cache_key[:8]}...")
                return entry['response']
        except (json.JSONDecodeError, KeyError):
            pass
    
    return None


def cache_response(prompt: str, model: str, response: str):
    """
    Cache an LLM response.
    
    Args:
        prompt: The prompt text
        model: The model name
        response: The response to cache
    """
    cache_key = _hash_key(prompt, model)
    entry = {
        'prompt_hash': cache_key,
        'model': model,
        'response': response,
        'timestamp': time.time()
    }
    
    # Store in memory
    if len(_memory_cache) >= MAX_MEMORY_CACHE:
        # Remove oldest entry
        oldest_key = min(_memory_cache, key=lambda k: _memory_cache[k]['timestamp'])
        del _memory_cache[oldest_key]
    _memory_cache[cache_key] = entry
    
    # Store on disk
    cache_file = CACHE_DIR / f"{cache_key}.json"
    try:
        with open(cache_file, 'w') as f:
            json.dump(entry, f)
        logger.debug(f"Cached response: {cache_key[:8]}...")
    except Exception as e:
        logger.warning(f"Failed to cache response: {e}")


def clear_cache(max_age_hours: Optional[int] = None):
    """
    Clear the cache.
    
    Args:
        max_age_hours: If provided, only clear entries older than this.
                      If None, clear all.
    """
    global _memory_cache
    
    if max_age_hours is None:
        _memory_cache = {}
        for cache_file in CACHE_DIR.glob("*.json"):
            cache_file.unlink()
        logger.info("Cache cleared completely")
    else:
        # Clear old entries only
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        # Memory cache
        old_keys = [
            k for k, v in _memory_cache.items()
            if current_time - v['timestamp'] > max_age_seconds
        ]
        for k in old_keys:
            del _memory_cache[k]
        
        # Disk cache
        for cache_file in CACHE_DIR.glob("*.json"):
            try:
                with open(cache_file, 'r') as f:
                    entry = json.load(f)
                if current_time - entry['timestamp'] > max_age_seconds:
                    cache_file.unlink()
            except:
                pass
        
        logger.info(f"Cleared cache entries older than {max_age_hours} hours")


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    memory_count = len(_memory_cache)
    disk_count = len(list(CACHE_DIR.glob("*.json")))
    
    total_size = sum(f.stat().st_size for f in CACHE_DIR.glob("*.json"))
    
    return {
        'memory_entries': memory_count,
        'disk_entries': disk_count,
        'disk_size_kb': total_size / 1024,
        'cache_dir': str(CACHE_DIR)
    }
