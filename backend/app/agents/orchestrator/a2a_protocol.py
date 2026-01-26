"""
Agent-to-Agent (A2A) Communication Protocol for FinFind.

Defines the protocol for agents to communicate with each other,
share context, and delegate tasks.
"""

import logging
import uuid
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class A2AMessageType(str, Enum):
    """Types of A2A messages."""
    
    # Task delegation
    DELEGATE_TASK = "delegate_task"
    TASK_RESULT = "task_result"
    TASK_FAILED = "task_failed"
    
    # Context sharing
    SHARE_CONTEXT = "share_context"
    REQUEST_CONTEXT = "request_context"
    CONTEXT_RESPONSE = "context_response"
    
    # Coordination
    HANDOFF = "handoff"
    COLLABORATE = "collaborate"
    
    # Status
    PING = "ping"
    PONG = "pong"
    STATUS_UPDATE = "status_update"


@dataclass
class A2AMessage:
    """
    Message structure for A2A communication.
    
    Attributes:
        id: Unique message ID.
        type: Type of message.
        sender: Name of the sending agent.
        recipient: Name of the receiving agent (or "broadcast").
        payload: Message data.
        context: Shared context (compressed).
        correlation_id: ID linking related messages.
        timestamp: Message creation time.
    """
    
    type: A2AMessageType
    sender: str
    recipient: str
    payload: Dict[str, Any] = field(default_factory=dict)
    context: Optional[Dict[str, Any]] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "sender": self.sender,
            "recipient": self.recipient,
            "payload": self.payload,
            "context": self.context,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'A2AMessage':
        """Create message from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            type=A2AMessageType(data["type"]),
            sender=data["sender"],
            recipient=data["recipient"],
            payload=data.get("payload", {}),
            context=data.get("context"),
            correlation_id=data.get("correlation_id"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.utcnow()
        )


@dataclass
class A2AResponse:
    """Response to an A2A message."""
    
    success: bool
    message_id: str
    correlation_id: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "message_id": self.message_id,
            "correlation_id": self.correlation_id,
            "result": self.result,
            "error": self.error
        }


class A2AProtocol:
    """
    Protocol handler for Agent-to-Agent communication.
    
    Manages message routing, context sharing, and task delegation
    between agents.
    """
    
    def __init__(self, log_communications: bool = True):
        """
        Initialize the A2A protocol handler.
        
        Args:
            log_communications: Whether to log all A2A messages.
        """
        self._agents: Dict[str, Any] = {}
        self._message_handlers: Dict[A2AMessageType, List[Callable]] = {}
        self._message_history: List[A2AMessage] = []
        self._pending_tasks: Dict[str, A2AMessage] = {}
        self._log_communications = log_communications
        self._max_history = 1000
    
    # ========================================
    # Agent Registration
    # ========================================
    
    def register_agent(self, agent_name: str, agent: Any):
        """
        Register an agent with the protocol.
        
        Args:
            agent_name: Name of the agent.
            agent: The agent instance.
        """
        self._agents[agent_name] = agent
        logger.info(f"A2A: Registered agent '{agent_name}'")
    
    def unregister_agent(self, agent_name: str):
        """Unregister an agent."""
        if agent_name in self._agents:
            del self._agents[agent_name]
            logger.info(f"A2A: Unregistered agent '{agent_name}'")
    
    def get_agent(self, agent_name: str) -> Optional[Any]:
        """Get a registered agent by name."""
        return self._agents.get(agent_name)
    
    def list_agents(self) -> List[str]:
        """List all registered agents."""
        return list(self._agents.keys())
    
    # ========================================
    # Message Handling
    # ========================================
    
    def register_handler(
        self,
        message_type: A2AMessageType,
        handler: Callable[[A2AMessage], A2AResponse]
    ):
        """Register a handler for a message type."""
        if message_type not in self._message_handlers:
            self._message_handlers[message_type] = []
        self._message_handlers[message_type].append(handler)
    
    async def send_message(self, message: A2AMessage) -> A2AResponse:
        """
        Send a message to another agent.
        
        Args:
            message: The message to send.
            
        Returns:
            Response from the recipient.
        """
        # Log the message
        if self._log_communications:
            logger.info(
                f"A2A: {message.sender} -> {message.recipient} "
                f"[{message.type.value}] id={message.id[:8]}"
            )
        
        # Store in history
        self._message_history.append(message)
        self._cleanup_history()
        
        # Handle broadcast messages
        if message.recipient == "broadcast":
            return await self._broadcast(message)
        
        # Get recipient agent
        recipient = self._agents.get(message.recipient)
        if not recipient:
            return A2AResponse(
                success=False,
                message_id=message.id,
                correlation_id=message.correlation_id or message.id,
                error=f"Agent '{message.recipient}' not found"
            )
        
        # Process message based on type
        return await self._process_message(message, recipient)
    
    async def _process_message(
        self,
        message: A2AMessage,
        recipient: Any
    ) -> A2AResponse:
        """Process a message for a specific recipient."""
        try:
            if message.type == A2AMessageType.DELEGATE_TASK:
                return await self._handle_delegate_task(message, recipient)
            
            elif message.type == A2AMessageType.SHARE_CONTEXT:
                return self._handle_share_context(message, recipient)
            
            elif message.type == A2AMessageType.REQUEST_CONTEXT:
                return self._handle_request_context(message, recipient)
            
            elif message.type == A2AMessageType.HANDOFF:
                return await self._handle_handoff(message, recipient)
            
            elif message.type == A2AMessageType.PING:
                return A2AResponse(
                    success=True,
                    message_id=message.id,
                    correlation_id=message.id,
                    result={"status": "alive", "agent": message.recipient}
                )
            
            else:
                # Call registered handlers
                handlers = self._message_handlers.get(message.type, [])
                for handler in handlers:
                    result = await handler(message)
                    if result:
                        return result
                
                return A2AResponse(
                    success=False,
                    message_id=message.id,
                    correlation_id=message.correlation_id or message.id,
                    error=f"No handler for message type: {message.type.value}"
                )
                
        except Exception as e:
            logger.exception(f"A2A: Error processing message {message.id}")
            return A2AResponse(
                success=False,
                message_id=message.id,
                correlation_id=message.correlation_id or message.id,
                error=str(e)
            )
    
    async def _handle_delegate_task(
        self,
        message: A2AMessage,
        recipient: Any
    ) -> A2AResponse:
        """Handle task delegation to another agent."""
        task = message.payload.get("task", "")
        state = message.payload.get("state")
        context = message.context
        
        # Store pending task
        self._pending_tasks[message.id] = message
        
        try:
            # Run the recipient agent with the task
            if hasattr(recipient, 'run'):
                from ..base import AgentState, ConversationContext
                
                # Reconstruct state if provided
                agent_state = None
                if state:
                    agent_state = AgentState(**state) if isinstance(state, dict) else state
                
                # Run the agent
                result_state = await recipient.run(
                    input_text=task,
                    state=agent_state
                )
                
                # Return result
                return A2AResponse(
                    success=True,
                    message_id=message.id,
                    correlation_id=message.correlation_id or message.id,
                    result={
                        "output": result_state.output_text,
                        "products": result_state.output_products,
                        "agent_chain": result_state.agent_chain,
                        "errors": result_state.errors
                    }
                )
            else:
                return A2AResponse(
                    success=False,
                    message_id=message.id,
                    correlation_id=message.correlation_id or message.id,
                    error="Recipient agent does not support task execution"
                )
                
        finally:
            # Remove from pending
            self._pending_tasks.pop(message.id, None)
    
    def _handle_share_context(
        self,
        message: A2AMessage,
        recipient: Any
    ) -> A2AResponse:
        """Handle context sharing."""
        # Context is in message.context
        shared_context = message.context
        
        # If recipient has a method to receive context, call it
        if hasattr(recipient, 'receive_context'):
            recipient.receive_context(shared_context)
        
        return A2AResponse(
            success=True,
            message_id=message.id,
            correlation_id=message.correlation_id or message.id,
            result={"context_received": True}
        )
    
    def _handle_request_context(
        self,
        message: A2AMessage,
        recipient: Any
    ) -> A2AResponse:
        """Handle context request."""
        # Get context from recipient if it has a method
        context = None
        if hasattr(recipient, 'get_context'):
            context = recipient.get_context()
        
        return A2AResponse(
            success=True,
            message_id=message.id,
            correlation_id=message.correlation_id or message.id,
            result={"context": context}
        )
    
    async def _handle_handoff(
        self,
        message: A2AMessage,
        recipient: Any
    ) -> A2AResponse:
        """Handle complete handoff to another agent."""
        # Handoff transfers full control to recipient
        return await self._handle_delegate_task(message, recipient)
    
    async def _broadcast(self, message: A2AMessage) -> A2AResponse:
        """Broadcast a message to all agents."""
        results = {}
        
        for agent_name, agent in self._agents.items():
            if agent_name != message.sender:
                msg_copy = A2AMessage(
                    type=message.type,
                    sender=message.sender,
                    recipient=agent_name,
                    payload=message.payload,
                    context=message.context,
                    correlation_id=message.id
                )
                response = await self._process_message(msg_copy, agent)
                results[agent_name] = response.to_dict()
        
        return A2AResponse(
            success=True,
            message_id=message.id,
            correlation_id=message.id,
            result={"broadcast_results": results}
        )
    
    # ========================================
    # Convenience Methods
    # ========================================
    
    async def delegate_task(
        self,
        sender: str,
        recipient: str,
        task: str,
        state: Optional[Dict] = None,
        context: Optional[Dict] = None
    ) -> A2AResponse:
        """
        Convenience method to delegate a task.
        
        Args:
            sender: Sending agent name.
            recipient: Receiving agent name.
            task: Task description.
            state: Optional state to pass.
            context: Optional context to share.
            
        Returns:
            Response from recipient.
        """
        message = A2AMessage(
            type=A2AMessageType.DELEGATE_TASK,
            sender=sender,
            recipient=recipient,
            payload={"task": task, "state": state},
            context=context
        )
        return await self.send_message(message)
    
    async def request_collaboration(
        self,
        sender: str,
        recipient: str,
        task: str,
        shared_data: Dict[str, Any]
    ) -> A2AResponse:
        """Request collaboration from another agent."""
        message = A2AMessage(
            type=A2AMessageType.COLLABORATE,
            sender=sender,
            recipient=recipient,
            payload={"task": task, "shared_data": shared_data}
        )
        return await self.send_message(message)
    
    def share_context(
        self,
        sender: str,
        recipient: str,
        context: Dict[str, Any]
    ):
        """Share context with another agent (sync)."""
        message = A2AMessage(
            type=A2AMessageType.SHARE_CONTEXT,
            sender=sender,
            recipient=recipient,
            context=context
        )
        # For sync context sharing, directly update if possible
        agent = self._agents.get(recipient)
        if agent and hasattr(agent, 'receive_context'):
            agent.receive_context(context)
    
    # ========================================
    # History and Debugging
    # ========================================
    
    def get_message_history(
        self,
        agent: Optional[str] = None,
        message_type: Optional[A2AMessageType] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get message history with optional filters."""
        messages = self._message_history
        
        if agent:
            messages = [
                m for m in messages 
                if m.sender == agent or m.recipient == agent
            ]
        
        if message_type:
            messages = [m for m in messages if m.type == message_type]
        
        return [m.to_dict() for m in messages[-limit:]]
    
    def get_pending_tasks(self) -> Dict[str, Dict]:
        """Get currently pending tasks."""
        return {
            task_id: msg.to_dict()
            for task_id, msg in self._pending_tasks.items()
        }
    
    def _cleanup_history(self):
        """Clean up old messages from history."""
        if len(self._message_history) > self._max_history:
            self._message_history = self._message_history[-self._max_history:]
