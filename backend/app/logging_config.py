"""
FinFind Production Logging Configuration

Provides structured JSON logging with contextual information
for production environments.
"""

import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict, Optional
from logging.handlers import RotatingFileHandler
import os


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def __init__(self, **kwargs):
        super().__init__()
        self.default_fields = kwargs
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add default fields
        log_entry.update(self.default_fields)
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields from record
        if hasattr(record, "extra"):
            log_entry.update(record.extra)
        
        # Add request context if available
        for attr in ["request_id", "user_id", "path", "method"]:
            if hasattr(record, attr):
                log_entry[attr] = getattr(record, attr)
        
        return json.dumps(log_entry)


class ContextFilter(logging.Filter):
    """Filter that adds contextual information to log records."""
    
    def __init__(self, context_provider=None):
        super().__init__()
        self.context_provider = context_provider
    
    def filter(self, record: logging.LogRecord) -> bool:
        if self.context_provider:
            context = self.context_provider()
            for key, value in context.items():
                setattr(record, key, value)
        return True


def setup_logging(
    app_name: str = "finfind",
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    json_format: bool = True,
    context_provider=None
) -> logging.Logger:
    """
    Set up production logging configuration.
    
    Args:
        app_name: Application name for logging
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path for file logging
        json_format: Use JSON format (True) or plain text (False)
        context_provider: Optional callable that returns context dict
    
    Returns:
        Configured root logger
    """
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers = []
    
    # Create formatter
    if json_format:
        formatter = JSONFormatter(
            app=app_name,
            environment=os.getenv("ENVIRONMENT", "development"),
            version=os.getenv("APP_VERSION", "1.0.0")
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)
    
    # Add context filter
    if context_provider:
        console_handler.addFilter(ContextFilter(context_provider))
    
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        if context_provider:
            file_handler.addFilter(ContextFilter(context_provider))
        logger.addHandler(file_handler)
    
    # Set third-party loggers to WARNING
    for third_party in ["uvicorn", "httpx", "httpcore", "urllib3"]:
        logging.getLogger(third_party).setLevel(logging.WARNING)
    
    return logger


class RequestLogger:
    """Middleware for logging HTTP requests."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    async def __call__(self, request, call_next):
        import time
        import uuid
        
        # Generate request ID
        request_id = str(uuid.uuid4())[:8]
        
        # Start timer
        start_time = time.time()
        
        # Log request
        self.logger.info(
            f"Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query": str(request.query_params),
                "user_agent": request.headers.get("user-agent", ""),
            }
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        self.logger.info(
            f"Request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
            }
        )
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response


class AgentLogger:
    """Logger for agent operations with structured output."""
    
    def __init__(self, agent_name: str):
        self.logger = logging.getLogger(f"agent.{agent_name}")
        self.agent_name = agent_name
    
    def log_query(self, query: str, context: Optional[Dict] = None):
        """Log incoming query to agent."""
        self.logger.info(
            f"Agent query received",
            extra={
                "agent": self.agent_name,
                "event": "query",
                "query": query[:200],  # Truncate long queries
                "context": context or {},
            }
        )
    
    def log_tool_call(self, tool_name: str, input_data: Dict, duration_ms: float):
        """Log tool invocation."""
        self.logger.debug(
            f"Tool called: {tool_name}",
            extra={
                "agent": self.agent_name,
                "event": "tool_call",
                "tool": tool_name,
                "input_keys": list(input_data.keys()),
                "duration_ms": duration_ms,
            }
        )
    
    def log_response(self, response: Dict, duration_ms: float):
        """Log agent response."""
        self.logger.info(
            f"Agent response generated",
            extra={
                "agent": self.agent_name,
                "event": "response",
                "response_keys": list(response.keys()),
                "duration_ms": duration_ms,
            }
        )
    
    def log_error(self, error: Exception, context: Optional[Dict] = None):
        """Log agent error."""
        self.logger.error(
            f"Agent error: {str(error)}",
            extra={
                "agent": self.agent_name,
                "event": "error",
                "error_type": type(error).__name__,
                "context": context or {},
            },
            exc_info=True
        )


# Export setup function
__all__ = [
    "setup_logging",
    "JSONFormatter",
    "RequestLogger",
    "AgentLogger",
]
