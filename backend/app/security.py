"""
FinFind Security Configuration

Provides security middleware, rate limiting, and input validation
for production environments.
"""

import hashlib
import hmac
import secrets
import time
import re
from typing import Dict, List, Optional, Callable, Any
from functools import wraps
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# Rate Limiting
# =============================================================================

class RateLimiter:
    """
    In-memory rate limiter using token bucket algorithm.
    
    For production, consider using Redis-based rate limiting.
    """
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_size: int = 10
    ):
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.tokens: Dict[str, float] = defaultdict(lambda: burst_size)
        self.last_update: Dict[str, float] = defaultdict(time.time)
        self._lock = None  # Use asyncio.Lock() in async context
    
    def _refill_tokens(self, key: str) -> None:
        """Refill tokens based on time elapsed."""
        now = time.time()
        time_passed = now - self.last_update[key]
        tokens_to_add = time_passed * (self.requests_per_minute / 60)
        self.tokens[key] = min(
            self.burst_size,
            self.tokens[key] + tokens_to_add
        )
        self.last_update[key] = now
    
    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed for given key."""
        self._refill_tokens(key)
        
        if self.tokens[key] >= 1:
            self.tokens[key] -= 1
            return True
        return False
    
    def get_retry_after(self, key: str) -> float:
        """Get seconds until next token is available."""
        if self.tokens[key] >= 1:
            return 0
        return (1 - self.tokens[key]) * (60 / self.requests_per_minute)


class RateLimitMiddleware:
    """ASGI middleware for rate limiting."""
    
    def __init__(
        self,
        app,
        limiter: RateLimiter,
        key_func: Optional[Callable] = None
    ):
        self.app = app
        self.limiter = limiter
        self.key_func = key_func or self._default_key_func
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Get rate limit key
        key = self.key_func(scope)
        
        if not self.limiter.is_allowed(key):
            retry_after = self.limiter.get_retry_after(key)
            await self._send_rate_limit_response(send, retry_after)
            return
        
        await self.app(scope, receive, send)
    
    @staticmethod
    def _default_key_func(scope) -> str:
        """Default key function using client IP."""
        headers = dict(scope.get("headers", []))
        
        # Check for forwarded IP
        forwarded = headers.get(b"x-forwarded-for", b"").decode()
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        # Fall back to direct client IP
        client = scope.get("client", ("unknown", 0))
        return client[0] if client else "unknown"
    
    @staticmethod
    async def _send_rate_limit_response(send, retry_after: float):
        """Send 429 Too Many Requests response."""
        await send({
            "type": "http.response.start",
            "status": 429,
            "headers": [
                (b"content-type", b"application/json"),
                (b"retry-after", str(int(retry_after + 1)).encode()),
            ],
        })
        await send({
            "type": "http.response.body",
            "body": b'{"error": "Rate limit exceeded", "retry_after": ' + 
                    str(int(retry_after + 1)).encode() + b'}',
        })


# =============================================================================
# Input Validation & Sanitization
# =============================================================================

class InputValidator:
    """Input validation and sanitization utilities."""
    
    # Patterns for validation
    UUID_PATTERN = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        re.IGNORECASE
    )
    EMAIL_PATTERN = re.compile(
        r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )
    SAFE_STRING_PATTERN = re.compile(r"^[\w\s\-.,!?'\"()]+$")
    
    # Dangerous patterns to filter
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC)\b)",
        r"(--|\;|\/*|\*/)",
        r"(\bOR\b.*=.*|\bAND\b.*=.*)",
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
    ]
    
    @classmethod
    def validate_uuid(cls, value: str) -> bool:
        """Validate UUID format."""
        return bool(cls.UUID_PATTERN.match(value))
    
    @classmethod
    def validate_email(cls, value: str) -> bool:
        """Validate email format."""
        return bool(cls.EMAIL_PATTERN.match(value))
    
    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 1000) -> str:
        """Sanitize string input."""
        if not value:
            return ""
        
        # Truncate to max length
        value = value[:max_length]
        
        # Remove null bytes
        value = value.replace("\x00", "")
        
        # Basic HTML escaping
        value = (
            value
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;")
        )
        
        return value
    
    @classmethod
    def check_sql_injection(cls, value: str) -> bool:
        """Check for potential SQL injection patterns."""
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def check_xss(cls, value: str) -> bool:
        """Check for potential XSS patterns."""
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def validate_search_query(cls, query: str) -> tuple[bool, str]:
        """Validate search query input."""
        if not query or not query.strip():
            return False, "Query cannot be empty"
        
        if len(query) > 500:
            return False, "Query too long (max 500 characters)"
        
        if cls.check_sql_injection(query):
            logger.warning(f"Potential SQL injection attempt: {query[:100]}")
            return False, "Invalid characters in query"
        
        if cls.check_xss(query):
            logger.warning(f"Potential XSS attempt: {query[:100]}")
            return False, "Invalid characters in query"
        
        return True, ""


# =============================================================================
# Security Headers
# =============================================================================

class SecurityHeadersMiddleware:
    """ASGI middleware to add security headers."""
    
    DEFAULT_HEADERS = [
        (b"x-content-type-options", b"nosniff"),
        (b"x-frame-options", b"DENY"),
        (b"x-xss-protection", b"1; mode=block"),
        (b"referrer-policy", b"strict-origin-when-cross-origin"),
        (b"permissions-policy", b"geolocation=(), microphone=(), camera=()"),
    ]
    
    def __init__(
        self,
        app,
        content_security_policy: Optional[str] = None,
        custom_headers: Optional[List[tuple]] = None
    ):
        self.app = app
        self.headers = list(self.DEFAULT_HEADERS)
        
        if content_security_policy:
            self.headers.append(
                (b"content-security-policy", content_security_policy.encode())
            )
        
        if custom_headers:
            self.headers.extend(custom_headers)
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend(self.headers)
                message = {**message, "headers": headers}
            await send(message)
        
        await self.app(scope, receive, send_with_headers)


# =============================================================================
# API Key Authentication
# =============================================================================

class APIKeyAuth:
    """API key authentication handler."""
    
    def __init__(self, valid_keys: List[str], header_name: str = "X-API-Key"):
        self.valid_keys = set(valid_keys)
        self.header_name = header_name.lower()
    
    def validate(self, request_headers: Dict[bytes, bytes]) -> bool:
        """Validate API key from request headers."""
        api_key = request_headers.get(
            self.header_name.encode(),
            b""
        ).decode()
        
        if not api_key:
            return False
        
        # Use constant-time comparison to prevent timing attacks
        return any(
            hmac.compare_digest(api_key, valid_key)
            for valid_key in self.valid_keys
        )
    
    @staticmethod
    def generate_api_key(length: int = 32) -> str:
        """Generate a secure API key."""
        return secrets.token_urlsafe(length)


class APIKeyMiddleware:
    """ASGI middleware for API key authentication."""
    
    def __init__(
        self,
        app,
        auth: APIKeyAuth,
        exclude_paths: Optional[List[str]] = None
    ):
        self.app = app
        self.auth = auth
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/openapi.json"]
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        path = scope.get("path", "")
        
        # Check if path is excluded
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            await self.app(scope, receive, send)
            return
        
        # Validate API key
        headers = dict(scope.get("headers", []))
        
        if not self.auth.validate(headers):
            await self._send_unauthorized(send)
            return
        
        await self.app(scope, receive, send)
    
    @staticmethod
    async def _send_unauthorized(send):
        """Send 401 Unauthorized response."""
        await send({
            "type": "http.response.start",
            "status": 401,
            "headers": [(b"content-type", b"application/json")],
        })
        await send({
            "type": "http.response.body",
            "body": b'{"error": "Unauthorized", "message": "Invalid or missing API key"}',
        })


# =============================================================================
# CORS Configuration
# =============================================================================

class CORSConfig:
    """CORS configuration for the application."""
    
    def __init__(
        self,
        allow_origins: List[str] = None,
        allow_methods: List[str] = None,
        allow_headers: List[str] = None,
        allow_credentials: bool = False,
        max_age: int = 600
    ):
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allow_headers = allow_headers or ["*"]
        self.allow_credentials = allow_credentials
        self.max_age = max_age
    
    def is_origin_allowed(self, origin: str) -> bool:
        """Check if origin is allowed."""
        if "*" in self.allow_origins:
            return True
        return origin in self.allow_origins
    
    def get_cors_headers(self, origin: str) -> List[tuple]:
        """Get CORS headers for response."""
        if not self.is_origin_allowed(origin):
            return []
        
        headers = [
            (b"access-control-allow-origin", origin.encode()),
            (b"access-control-allow-methods", ", ".join(self.allow_methods).encode()),
            (b"access-control-allow-headers", ", ".join(self.allow_headers).encode()),
            (b"access-control-max-age", str(self.max_age).encode()),
        ]
        
        if self.allow_credentials:
            headers.append((b"access-control-allow-credentials", b"true"))
        
        return headers


# =============================================================================
# Request Signing
# =============================================================================

class RequestSigner:
    """Sign and verify requests using HMAC."""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode()
    
    def sign(self, data: str, timestamp: Optional[int] = None) -> str:
        """Sign data with timestamp."""
        timestamp = timestamp or int(time.time())
        message = f"{timestamp}.{data}"
        signature = hmac.new(
            self.secret_key,
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"{timestamp}.{signature}"
    
    def verify(
        self,
        data: str,
        signature: str,
        max_age: int = 300
    ) -> bool:
        """Verify signed data within time window."""
        try:
            parts = signature.split(".")
            if len(parts) != 2:
                return False
            
            timestamp = int(parts[0])
            
            # Check timestamp is within acceptable range
            if abs(time.time() - timestamp) > max_age:
                return False
            
            # Verify signature
            expected = self.sign(data, timestamp)
            return hmac.compare_digest(signature, expected)
            
        except (ValueError, TypeError):
            return False


# Export
__all__ = [
    "RateLimiter",
    "RateLimitMiddleware",
    "InputValidator",
    "SecurityHeadersMiddleware",
    "APIKeyAuth",
    "APIKeyMiddleware",
    "CORSConfig",
    "RequestSigner",
]
