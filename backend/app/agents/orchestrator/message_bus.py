"""
A2A Message Bus for Inter-Agent Communication.

Provides advanced messaging patterns:
- Request/Response
- Publish/Subscribe
- Event broadcasting
- Context sharing with compression
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid
import json
import gzip
import base64

logger = logging.getLogger(__name__)


class MessagePriority(int, Enum):
    """Message priority levels."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class A2AEvent:
    """
    Event for publish/subscribe pattern.
    
    Attributes:
        event_type: Type of event (e.g., "search_complete", "budget_exceeded")
        source_agent: Agent that published the event
        data: Event data payload
        timestamp: When the event occurred
    """
    event_type: str
    source_agent: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "event_type": self.event_type,
            "source_agent": self.source_agent,
            "data": self.data,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class CompressedContext:
    """
    Compressed context for efficient sharing between agents.
    
    Reduces context size for faster A2A communication.
    """
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    query: Optional[str] = None
    intent: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    categories: List[str] = field(default_factory=list)
    product_ids: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_full_context(cls, context: Dict[str, Any]) -> 'CompressedContext':
        """Create compressed context from full context."""
        return cls(
            user_id=context.get("user_id"),
            conversation_id=context.get("conversation_id"),
            query=context.get("query", context.get("input_text")),
            intent=context.get("intent"),
            budget_min=context.get("budget_min"),
            budget_max=context.get("budget_max", context.get("max_price")),
            categories=context.get("categories", [])[:5],  # Limit
            product_ids=[p.get("id") for p in context.get("products", [])[:10]],
            constraints=context.get("constraints", {}),
            metadata={
                k: v for k, v in context.get("metadata", {}).items()
                if k in ["source", "priority", "session_id"]
            }
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in {
            "user_id": self.user_id,
            "conversation_id": self.conversation_id,
            "query": self.query,
            "intent": self.intent,
            "budget_min": self.budget_min,
            "budget_max": self.budget_max,
            "categories": self.categories if self.categories else None,
            "product_ids": self.product_ids if self.product_ids else None,
            "constraints": self.constraints if self.constraints else None,
            "metadata": self.metadata if self.metadata else None,
        }.items() if v is not None}
    
    def compress(self) -> str:
        """Compress context to base64 string."""
        json_data = json.dumps(self.to_dict())
        compressed = gzip.compress(json_data.encode())
        return base64.b64encode(compressed).decode()
    
    @classmethod
    def decompress(cls, data: str) -> 'CompressedContext':
        """Decompress context from base64 string."""
        compressed = base64.b64decode(data)
        json_data = gzip.decompress(compressed).decode()
        return cls(**json.loads(json_data))


class A2AMessageBus:
    """
    Message bus for A2A communication.
    
    Provides:
    - Async message queuing
    - Event pub/sub
    - Priority-based delivery
    - Message routing
    """
    
    def __init__(self, max_queue_size: int = 1000):
        self._agents: Dict[str, Any] = {}
        self._message_queue: asyncio.PriorityQueue = asyncio.PriorityQueue(maxsize=max_queue_size)
        self._event_subscribers: Dict[str, List[Callable]] = {}
        self._response_futures: Dict[str, asyncio.Future] = {}
        self._running = False
        self._processor_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the message bus."""
        if self._running:
            return
        
        self._running = True
        self._processor_task = asyncio.create_task(self._process_messages())
        logger.info("A2A Message Bus started")
    
    async def stop(self):
        """Stop the message bus."""
        self._running = False
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        logger.info("A2A Message Bus stopped")
    
    def register_agent(self, name: str, agent: Any):
        """Register an agent with the bus."""
        self._agents[name] = agent
        logger.debug(f"Registered agent '{name}' with message bus")
    
    def unregister_agent(self, name: str):
        """Unregister an agent."""
        self._agents.pop(name, None)
    
    # ========================================
    # Request/Response Pattern
    # ========================================
    
    async def request(
        self,
        sender: str,
        recipient: str,
        action: str,
        payload: Dict[str, Any],
        context: Optional[CompressedContext] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        """
        Send a request and wait for response.
        
        Args:
            sender: Sending agent name
            recipient: Target agent name
            action: Action to perform
            payload: Request data
            context: Compressed context
            priority: Message priority
            timeout: Response timeout
            
        Returns:
            Response from recipient
        """
        request_id = str(uuid.uuid4())
        
        # Create future for response
        future: asyncio.Future = asyncio.Future()
        self._response_futures[request_id] = future
        
        # Queue message
        message = {
            "id": request_id,
            "type": "request",
            "sender": sender,
            "recipient": recipient,
            "action": action,
            "payload": payload,
            "context": context.to_dict() if context else None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self._message_queue.put((
            -priority.value,  # Negative for priority queue (higher = first)
            datetime.utcnow().timestamp(),
            message
        ))
        
        try:
            # Wait for response
            response = await asyncio.wait_for(future, timeout=timeout)
            return response
        except asyncio.TimeoutError:
            logger.warning(f"Request {request_id} timed out")
            return {
                "success": False,
                "error": f"Request timed out after {timeout}s",
                "request_id": request_id
            }
        finally:
            self._response_futures.pop(request_id, None)
    
    async def respond(
        self,
        request_id: str,
        response: Dict[str, Any]
    ):
        """Send a response to a request."""
        future = self._response_futures.get(request_id)
        if future and not future.done():
            future.set_result(response)
    
    # ========================================
    # Publish/Subscribe Pattern
    # ========================================
    
    def subscribe(
        self,
        event_type: str,
        callback: Callable[[A2AEvent], Awaitable[None]]
    ):
        """Subscribe to an event type."""
        if event_type not in self._event_subscribers:
            self._event_subscribers[event_type] = []
        self._event_subscribers[event_type].append(callback)
        logger.debug(f"Subscribed to event '{event_type}'")
    
    def unsubscribe(
        self,
        event_type: str,
        callback: Callable[[A2AEvent], Awaitable[None]]
    ):
        """Unsubscribe from an event type."""
        if event_type in self._event_subscribers:
            try:
                self._event_subscribers[event_type].remove(callback)
            except ValueError:
                pass
    
    async def publish(
        self,
        event_type: str,
        source_agent: str,
        data: Dict[str, Any]
    ):
        """Publish an event to all subscribers."""
        event = A2AEvent(
            event_type=event_type,
            source_agent=source_agent,
            data=data
        )
        
        subscribers = self._event_subscribers.get(event_type, [])
        if not subscribers:
            logger.debug(f"No subscribers for event '{event_type}'")
            return
        
        # Notify all subscribers
        tasks = [
            asyncio.create_task(self._safe_callback(callback, event))
            for callback in subscribers
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.debug(f"Published event '{event_type}' to {len(subscribers)} subscribers")
    
    async def _safe_callback(
        self,
        callback: Callable[[A2AEvent], Awaitable[None]],
        event: A2AEvent
    ):
        """Safely execute a callback."""
        try:
            await callback(event)
        except Exception as e:
            logger.error(f"Event callback error: {e}")
    
    # ========================================
    # Message Processing
    # ========================================
    
    async def _process_messages(self):
        """Process messages from the queue."""
        while self._running:
            try:
                # Get message with timeout
                try:
                    priority, timestamp, message = await asyncio.wait_for(
                        self._message_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Process based on type
                if message["type"] == "request":
                    await self._handle_request(message)
                
                self._message_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Message processing error: {e}")
    
    async def _handle_request(self, message: Dict[str, Any]):
        """Handle an incoming request message."""
        recipient_name = message["recipient"]
        agent = self._agents.get(recipient_name)
        
        if not agent:
            await self.respond(message["id"], {
                "success": False,
                "error": f"Agent '{recipient_name}' not found"
            })
            return
        
        try:
            # Execute action on agent
            action = message["action"]
            payload = message["payload"]
            
            # Check if agent has the action method
            if hasattr(agent, action):
                method = getattr(agent, action)
                if asyncio.iscoroutinefunction(method):
                    result = await method(**payload)
                else:
                    result = method(**payload)
            elif hasattr(agent, "handle_action"):
                result = await agent.handle_action(action, payload)
            else:
                result = {"error": f"Agent does not support action '{action}'"}
            
            await self.respond(message["id"], {
                "success": True,
                "result": result,
                "agent": recipient_name
            })
            
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            await self.respond(message["id"], {
                "success": False,
                "error": str(e),
                "agent": recipient_name
            })


# Event type constants
class A2AEventTypes:
    """Standard A2A event types."""
    SEARCH_STARTED = "search_started"
    SEARCH_COMPLETED = "search_completed"
    PRODUCTS_FOUND = "products_found"
    NO_PRODUCTS_FOUND = "no_products_found"
    BUDGET_EXCEEDED = "budget_exceeded"
    RECOMMENDATION_READY = "recommendation_ready"
    EXPLANATION_READY = "explanation_ready"
    ALTERNATIVES_FOUND = "alternatives_found"
    AGENT_ERROR = "agent_error"
    CONTEXT_UPDATED = "context_updated"
    HANDOFF_REQUESTED = "handoff_requested"
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
