# FinFind LLM Cost Optimization Guide

## Groq Model Pricing (per million tokens)

| Model | Input | Output | Speed | Best For |
|-------|-------|--------|-------|----------|
| `llama-3.1-8b-instant` | **$0.05** | **$0.08** | 560 tps | **Cheapest - Simple tasks, fallback** |
| `llama-3.3-70b-versatile` | $0.59 | $0.79 | 280 tps | Complex reasoning, orchestration |
| `meta-llama/llama-4-scout-17b-16e-instruct` | $0.11 | $0.34 | 750 tps | Good quality/cost balance |
| `openai/gpt-oss-20b` | $0.075 | $0.30 | 1000 tps | Fast and good |

## Free Tier Rate Limits

| Model | Tokens/Minute | Requests/Minute |
|-------|---------------|-----------------|
| `llama-3.1-8b-instant` | 250K | 1K |
| `llama-3.3-70b-versatile` | 300K | 1K |

## Current FinFind Configuration

### Primary Model: `llama-3.3-70b-versatile`
- Best for complex agent orchestration and tool calling
- High quality responses

### Fallback Model: `llama-3.1-8b-instant`
- Activated when primary hits rate limits
- 10x cheaper than primary
- Still good for simple tasks

## Caching System

FinFind implements LLM response caching to reduce API calls:

### Cache Location
- Memory: Up to 500 entries
- Disk: `backend/app/agents/services/.llm_cache/`

### Cached Operations
1. **Query Interpretation** (`InterpretQueryTool`)
   - Caches expanded queries for 24 hours
   - Same queries return instantly from cache

### Cache Usage

```python
from backend.app.agents.services.llm_cache import (
    get_cached_response,
    cache_response,
    get_cache_stats,
    clear_cache
)

# Check cache stats
stats = get_cache_stats()
print(f"Memory: {stats['memory_entries']}, Disk: {stats['disk_entries']}")

# Clear old cache entries
clear_cache(max_age_hours=48)

# Clear all cache
clear_cache()
```

## Recommendations for Different Use Cases

### Development/Testing (Minimum Cost)
```env
GROQ_MODEL=llama-3.1-8b-instant
GROQ_FALLBACK_MODEL=llama-3.1-8b-instant
```
- Same model for both (cheapest)
- Good for testing, not for production quality

### Production (Balanced)
```env
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_FALLBACK_MODEL=llama-3.1-8b-instant
```
- High quality for primary tasks
- Cheap fallback for rate limits

### High Traffic (Cost Optimized)
```env
GROQ_MODEL=llama-3.1-8b-instant
GROQ_FALLBACK_MODEL=llama-3.1-8b-instant
```
- All requests use cheapest model
- Use caching aggressively

## Cost Estimation

### Per 1000 User Queries (Typical)

With `llama-3.3-70b-versatile`:
- Input: ~1000 tokens/query × 1000 = 1M tokens → $0.59
- Output: ~500 tokens/query × 1000 = 500K tokens → $0.40
- **Total: ~$1.00 per 1000 queries**

With `llama-3.1-8b-instant`:
- Input: 1M tokens → $0.05
- Output: 500K tokens → $0.04
- **Total: ~$0.09 per 1000 queries (90% savings!)**

### With Caching (50% hit rate)
- Reduces costs by 50%
- `llama-3.3-70b-versatile`: ~$0.50 per 1000 queries
- `llama-3.1-8b-instant`: ~$0.045 per 1000 queries

## Best Practices

1. **Always use caching** - Query interpretation is highly cacheable
2. **Use fallback model** - Set `use_fallback_on_rate_limit: true`
3. **Monitor cache stats** - Check hit rates regularly
4. **Clear old cache** - Run `clear_cache(max_age_hours=72)` periodically
5. **Batch operations** - Group similar queries to maximize cache hits

## Monitoring

Check cache performance:
```python
from backend.app.agents.services.llm_cache import get_cache_stats
print(get_cache_stats())
```

Expected output:
```json
{
    "memory_entries": 125,
    "disk_entries": 250,
    "disk_size_kb": 45.2,
    "cache_dir": "/path/to/.llm_cache"
}
```
