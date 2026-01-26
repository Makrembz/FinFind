"""
MCP Protocol Implementation for FinFind.

Defines the Model Context Protocol standards for tool communication,
including input/output schemas, error handling, and metadata.
"""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Type, Union
from functools import wraps

from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)


# ========================================
# MCP Error Handling
# ========================================

class MCPErrorCode(str, Enum):
    """Standard MCP error codes."""
    
    # Client errors (4xx equivalent)
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_PARAMETER = "MISSING_PARAMETER"
    INVALID_PARAMETER_TYPE = "INVALID_PARAMETER_TYPE"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    RATE_LIMITED = "RATE_LIMITED"
    
    # Server errors (5xx equivalent)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    TIMEOUT = "TIMEOUT"
    DEPENDENCY_FAILED = "DEPENDENCY_FAILED"
    
    # Tool-specific errors
    VECTOR_SEARCH_FAILED = "VECTOR_SEARCH_FAILED"
    EMBEDDING_FAILED = "EMBEDDING_FAILED"
    LLM_FAILED = "LLM_FAILED"
    QDRANT_ERROR = "QDRANT_ERROR"


@dataclass
class MCPError(Exception):
    """Standard MCP error with structured information."""
    
    code: MCPErrorCode
    message: str
    details: Optional[Dict[str, Any]] = None
    recoverable: bool = True
    retry_after: Optional[int] = None  # seconds
    
    def __str__(self):
        return f"[{self.code.value}] {self.message}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "error": True,
            "code": self.code.value,
            "message": self.message,
            "details": self.details,
            "recoverable": self.recoverable,
            "retry_after": self.retry_after
        }


# ========================================
# MCP Tool Input/Output Models
# ========================================

class MCPToolInput(BaseModel):
    """
    Base class for MCP tool inputs.
    
    All tool inputs should inherit from this to ensure
    consistent validation and serialization.
    """
    
    class Config:
        extra = "forbid"  # Strict validation
        
    def validate_constraints(self) -> List[str]:
        """
        Validate business constraints beyond type checking.
        Override in subclasses for custom validation.
        
        Returns:
            List of validation error messages (empty if valid).
        """
        return []


@dataclass
class MCPToolOutput:
    """
    Standard MCP tool output format.
    
    All tools return this structure for consistency.
    """
    
    success: bool
    data: Optional[Any] = None
    error: Optional[MCPError] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Execution metrics
    execution_time_ms: float = 0.0
    tokens_used: int = 0
    cache_hit: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "success": self.success,
            "metadata": {
                **self.metadata,
                "execution_time_ms": self.execution_time_ms,
                "tokens_used": self.tokens_used,
                "cache_hit": self.cache_hit
            }
        }
        
        if self.success:
            result["data"] = self.data
        else:
            result["error"] = self.error.to_dict() if self.error else None
        
        return result
    
    @classmethod
    def success_response(
        cls,
        data: Any,
        execution_time_ms: float = 0.0,
        cache_hit: bool = False,
        **metadata
    ) -> "MCPToolOutput":
        """Create a success response."""
        return cls(
            success=True,
            data=data,
            execution_time_ms=execution_time_ms,
            cache_hit=cache_hit,
            metadata=metadata
        )
    
    @classmethod
    def error_response(
        cls,
        error: MCPError,
        execution_time_ms: float = 0.0
    ) -> "MCPToolOutput":
        """Create an error response."""
        return cls(
            success=False,
            error=error,
            execution_time_ms=execution_time_ms
        )


# ========================================
# MCP Tool Metadata
# ========================================

@dataclass
class MCPToolMetadata:
    """Metadata describing an MCP tool."""
    
    name: str
    description: str
    version: str = "1.0.0"
    
    # Categorization
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    
    # Performance characteristics
    avg_latency_ms: float = 100.0
    timeout_ms: int = 30000
    cacheable: bool = True
    cache_ttl_seconds: int = 300
    
    # Dependencies
    requires_qdrant: bool = False
    requires_llm: bool = False
    requires_embedding: bool = False
    
    # Rate limiting
    requests_per_minute: int = 60
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "category": self.category,
            "tags": self.tags,
            "performance": {
                "avg_latency_ms": self.avg_latency_ms,
                "timeout_ms": self.timeout_ms,
                "cacheable": self.cacheable,
                "cache_ttl_seconds": self.cache_ttl_seconds
            },
            "dependencies": {
                "requires_qdrant": self.requires_qdrant,
                "requires_llm": self.requires_llm,
                "requires_embedding": self.requires_embedding
            },
            "rate_limit": {
                "requests_per_minute": self.requests_per_minute
            }
        }


# ========================================
# MCP Tool Base Class
# ========================================

class MCPTool(BaseTool, ABC):
    """
    Base class for MCP-compliant tools.
    
    Extends LangChain's BaseTool with MCP protocol features:
    - Standardized input validation
    - Structured output format
    - Error handling
    - Logging and metrics
    - Caching support
    """
    
    # Tool metadata
    mcp_metadata: MCPToolMetadata = None
    
    # Internal state
    _call_count: int = 0
    _total_latency_ms: float = 0.0
    _error_count: int = 0
    _last_called: Optional[datetime] = None
    
    class Config:
        arbitrary_types_allowed = True
    
    @property
    def metadata(self) -> MCPToolMetadata:
        """Get tool metadata."""
        if self.mcp_metadata is None:
            return MCPToolMetadata(
                name=self.name,
                description=self.description
            )
        return self.mcp_metadata
    
    def _run(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool with MCP protocol handling.
        
        This wraps the actual implementation with:
        - Input validation
        - Error handling
        - Metrics collection
        - Logging
        """
        start_time = time.time()
        self._call_count += 1
        self._last_called = datetime.utcnow()
        
        try:
            # Log tool invocation
            logger.info(f"MCP Tool '{self.name}' invoked with: {list(kwargs.keys())}")
            
            # Execute the actual tool logic
            result = self._execute(**kwargs)
            
            # Wrap in MCPToolOutput if not already
            if not isinstance(result, MCPToolOutput):
                result = MCPToolOutput.success_response(data=result)
            
            # Calculate execution time
            execution_time_ms = (time.time() - start_time) * 1000
            result.execution_time_ms = execution_time_ms
            self._total_latency_ms += execution_time_ms
            
            logger.info(f"MCP Tool '{self.name}' completed in {execution_time_ms:.2f}ms")
            
            return result.to_dict()
            
        except MCPError as e:
            self._error_count += 1
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(f"MCP Tool '{self.name}' error: {e}")
            return MCPToolOutput.error_response(e, execution_time_ms).to_dict()
            
        except Exception as e:
            self._error_count += 1
            execution_time_ms = (time.time() - start_time) * 1000
            logger.exception(f"MCP Tool '{self.name}' unexpected error: {e}")
            
            error = MCPError(
                code=MCPErrorCode.INTERNAL_ERROR,
                message=str(e),
                recoverable=False
            )
            return MCPToolOutput.error_response(error, execution_time_ms).to_dict()
    
    async def _arun(self, **kwargs) -> Dict[str, Any]:
        """Async execution with MCP protocol handling."""
        start_time = time.time()
        self._call_count += 1
        self._last_called = datetime.utcnow()
        
        try:
            logger.info(f"MCP Tool '{self.name}' async invoked")
            
            result = await self._aexecute(**kwargs)
            
            if not isinstance(result, MCPToolOutput):
                result = MCPToolOutput.success_response(data=result)
            
            execution_time_ms = (time.time() - start_time) * 1000
            result.execution_time_ms = execution_time_ms
            self._total_latency_ms += execution_time_ms
            
            return result.to_dict()
            
        except MCPError as e:
            self._error_count += 1
            execution_time_ms = (time.time() - start_time) * 1000
            return MCPToolOutput.error_response(e, execution_time_ms).to_dict()
            
        except Exception as e:
            self._error_count += 1
            execution_time_ms = (time.time() - start_time) * 1000
            error = MCPError(
                code=MCPErrorCode.INTERNAL_ERROR,
                message=str(e),
                recoverable=False
            )
            return MCPToolOutput.error_response(error, execution_time_ms).to_dict()
    
    @abstractmethod
    def _execute(self, **kwargs) -> Union[MCPToolOutput, Any]:
        """
        Actual tool implementation.
        
        Override this method in subclasses.
        Can return MCPToolOutput or raw data (will be wrapped).
        """
        pass
    
    async def _aexecute(self, **kwargs) -> Union[MCPToolOutput, Any]:
        """
        Async tool implementation.
        
        Default implementation calls sync version.
        Override for true async behavior.
        """
        return self._execute(**kwargs)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get tool usage statistics."""
        avg_latency = (
            self._total_latency_ms / self._call_count 
            if self._call_count > 0 else 0
        )
        
        return {
            "name": self.name,
            "call_count": self._call_count,
            "error_count": self._error_count,
            "error_rate": self._error_count / max(self._call_count, 1),
            "avg_latency_ms": avg_latency,
            "total_latency_ms": self._total_latency_ms,
            "last_called": self._last_called.isoformat() if self._last_called else None
        }
    
    def reset_stats(self):
        """Reset tool statistics."""
        self._call_count = 0
        self._total_latency_ms = 0.0
        self._error_count = 0
        self._last_called = None


# ========================================
# MCP Decorators
# ========================================

def mcp_tool(
    name: str,
    description: str,
    category: str = "general",
    requires_qdrant: bool = False,
    requires_llm: bool = False,
    requires_embedding: bool = False,
    cacheable: bool = True,
    cache_ttl: int = 300,
    timeout_ms: int = 30000
):
    """
    Decorator to create MCP-compliant tools from functions.
    
    Usage:
        @mcp_tool(
            name="my_tool",
            description="Does something useful",
            requires_qdrant=True
        )
        def my_tool_func(query: str, limit: int = 10) -> Dict:
            # Implementation
            return {"results": [...]}
    """
    def decorator(func):
        metadata = MCPToolMetadata(
            name=name,
            description=description,
            category=category,
            requires_qdrant=requires_qdrant,
            requires_llm=requires_llm,
            requires_embedding=requires_embedding,
            cacheable=cacheable,
            cache_ttl_seconds=cache_ttl,
            timeout_ms=timeout_ms
        )
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                logger.info(f"MCP Tool '{name}' invoked")
                result = func(*args, **kwargs)
                
                if not isinstance(result, MCPToolOutput):
                    result = MCPToolOutput.success_response(data=result)
                
                result.execution_time_ms = (time.time() - start_time) * 1000
                return result.to_dict()
                
            except MCPError as e:
                execution_time_ms = (time.time() - start_time) * 1000
                return MCPToolOutput.error_response(e, execution_time_ms).to_dict()
                
            except Exception as e:
                execution_time_ms = (time.time() - start_time) * 1000
                error = MCPError(
                    code=MCPErrorCode.INTERNAL_ERROR,
                    message=str(e)
                )
                return MCPToolOutput.error_response(error, execution_time_ms).to_dict()
        
        wrapper.mcp_metadata = metadata
        wrapper.is_mcp_tool = True
        return wrapper
    
    return decorator
