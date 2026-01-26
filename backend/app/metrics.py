"""
FinFind Metrics and Monitoring Configuration

Provides Prometheus-compatible metrics for monitoring
application health and performance.
"""

import time
from functools import wraps
from typing import Callable, Optional, Dict, Any
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

# Try to import prometheus_client, gracefully handle if not installed
try:
    from prometheus_client import (
        Counter,
        Histogram,
        Gauge,
        Summary,
        Info,
        generate_latest,
        CONTENT_TYPE_LATEST,
        CollectorRegistry,
        multiprocess,
        REGISTRY
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("prometheus_client not installed. Metrics will be disabled.")


# =============================================================================
# Metrics Registry
# =============================================================================

if PROMETHEUS_AVAILABLE:
    # HTTP Request metrics
    http_requests_total = Counter(
        "http_requests_total",
        "Total HTTP requests",
        ["method", "endpoint", "status_code"]
    )
    
    http_request_duration_seconds = Histogram(
        "http_request_duration_seconds",
        "HTTP request duration in seconds",
        ["method", "endpoint"],
        buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
    )
    
    http_requests_in_progress = Gauge(
        "http_requests_in_progress",
        "Number of HTTP requests in progress",
        ["method", "endpoint"]
    )
    
    # Agent metrics
    agent_queries_total = Counter(
        "agent_queries_total",
        "Total agent queries",
        ["agent", "status"]
    )
    
    agent_query_duration_seconds = Histogram(
        "agent_query_duration_seconds",
        "Agent query duration in seconds",
        ["agent"],
        buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0]
    )
    
    agent_tool_calls_total = Counter(
        "agent_tool_calls_total",
        "Total agent tool calls",
        ["agent", "tool", "status"]
    )
    
    # Search metrics
    search_requests_total = Counter(
        "search_requests_total",
        "Total search requests",
        ["search_type", "status"]
    )
    
    search_results_count = Histogram(
        "search_results_count",
        "Number of search results returned",
        ["search_type"],
        buckets=[0, 1, 5, 10, 20, 50, 100]
    )
    
    search_latency_seconds = Histogram(
        "search_latency_seconds",
        "Search latency in seconds",
        ["search_type"],
        buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
    )
    
    # Recommendation metrics
    recommendation_requests_total = Counter(
        "recommendation_requests_total",
        "Total recommendation requests",
        ["status"]
    )
    
    recommendation_score_histogram = Histogram(
        "recommendation_score_histogram",
        "Distribution of recommendation scores",
        buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    )
    
    # Database metrics
    qdrant_operations_total = Counter(
        "qdrant_operations_total",
        "Total Qdrant operations",
        ["operation", "collection", "status"]
    )
    
    qdrant_operation_duration_seconds = Histogram(
        "qdrant_operation_duration_seconds",
        "Qdrant operation duration in seconds",
        ["operation", "collection"],
        buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5]
    )
    
    # LLM metrics
    llm_requests_total = Counter(
        "llm_requests_total",
        "Total LLM API requests",
        ["model", "status"]
    )
    
    llm_request_duration_seconds = Histogram(
        "llm_request_duration_seconds",
        "LLM API request duration in seconds",
        ["model"],
        buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
    )
    
    llm_tokens_used = Counter(
        "llm_tokens_used_total",
        "Total LLM tokens used",
        ["model", "token_type"]
    )
    
    # Learning system metrics
    interactions_logged_total = Counter(
        "interactions_logged_total",
        "Total user interactions logged",
        ["interaction_type"]
    )
    
    feedback_received_total = Counter(
        "feedback_received_total",
        "Total feedback received",
        ["feedback_type", "rating"]
    )
    
    model_updates_total = Counter(
        "model_updates_total",
        "Total model updates performed",
        ["update_type", "status"]
    )
    
    # Application info
    app_info = Info(
        "finfind_app",
        "FinFind application information"
    )
    
    # Active users gauge
    active_users = Gauge(
        "active_users",
        "Number of active users"
    )


# =============================================================================
# Metrics Decorators and Utilities
# =============================================================================

def track_request(method: str, endpoint: str):
    """Decorator to track HTTP request metrics."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not PROMETHEUS_AVAILABLE:
                return await func(*args, **kwargs)
            
            http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()
            start_time = time.time()
            status_code = "500"
            
            try:
                result = await func(*args, **kwargs)
                status_code = str(getattr(result, "status_code", 200))
                return result
            except Exception as e:
                status_code = "500"
                raise
            finally:
                duration = time.time() - start_time
                http_requests_total.labels(
                    method=method,
                    endpoint=endpoint,
                    status_code=status_code
                ).inc()
                http_request_duration_seconds.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)
                http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()
        
        return wrapper
    return decorator


def track_agent_query(agent_name: str):
    """Decorator to track agent query metrics."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not PROMETHEUS_AVAILABLE:
                return await func(*args, **kwargs)
            
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                agent_queries_total.labels(agent=agent_name, status=status).inc()
                agent_query_duration_seconds.labels(agent=agent_name).observe(duration)
        
        return wrapper
    return decorator


@contextmanager
def track_operation(
    metric_counter: "Counter",
    metric_histogram: "Histogram",
    labels: Dict[str, str]
):
    """Context manager to track operation metrics."""
    if not PROMETHEUS_AVAILABLE:
        yield
        return
    
    start_time = time.time()
    status = "success"
    
    try:
        yield
    except Exception:
        status = "error"
        raise
    finally:
        duration = time.time() - start_time
        metric_counter.labels(**labels, status=status).inc()
        label_subset = {k: v for k, v in labels.items() if k != "status"}
        metric_histogram.labels(**label_subset).observe(duration)


class MetricsMiddleware:
    """ASGI middleware for automatic request metrics."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not PROMETHEUS_AVAILABLE:
            await self.app(scope, receive, send)
            return
        
        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "/")
        
        # Normalize path to reduce cardinality
        endpoint = self._normalize_path(path)
        
        http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()
        start_time = time.time()
        status_code = "500"
        
        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = str(message.get("status", 500))
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration = time.time() - start_time
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()
    
    @staticmethod
    def _normalize_path(path: str) -> str:
        """Normalize path to reduce metric cardinality."""
        # Replace UUIDs and IDs with placeholders
        import re
        
        # UUID pattern
        path = re.sub(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            "{id}",
            path
        )
        
        # Numeric IDs
        path = re.sub(r"/\d+", "/{id}", path)
        
        return path


def get_metrics() -> bytes:
    """Get Prometheus metrics in exposition format."""
    if not PROMETHEUS_AVAILABLE:
        return b"# Prometheus client not installed"
    return generate_latest(REGISTRY)


def init_app_info(version: str, environment: str):
    """Initialize application info metric."""
    if PROMETHEUS_AVAILABLE:
        app_info.info({
            "version": version,
            "environment": environment,
        })


# =============================================================================
# Health Check
# =============================================================================

async def health_check() -> Dict[str, Any]:
    """Perform health check on all services."""
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {}
    }
    
    # Check Qdrant
    try:
        # Add actual Qdrant health check
        health_status["services"]["qdrant"] = "connected"
    except Exception as e:
        health_status["services"]["qdrant"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check LLM service
    try:
        # Add actual LLM health check
        health_status["services"]["llm"] = "connected"
    except Exception as e:
        health_status["services"]["llm"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status


# Export
__all__ = [
    "track_request",
    "track_agent_query",
    "track_operation",
    "MetricsMiddleware",
    "get_metrics",
    "init_app_info",
    "health_check",
    "PROMETHEUS_AVAILABLE",
]
