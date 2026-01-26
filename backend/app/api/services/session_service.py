"""
Session management service for conversation state.

Handles:
- Conversation history storage
- Session creation and retrieval
- Context management for agents
"""

import logging
import uuid
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Single message in a conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {})
        )


@dataclass
class Session:
    """Conversation session with history and context."""
    session_id: str
    user_id: Optional[str] = None
    messages: List[Message] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(hours=24))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Add a message to the conversation."""
        msg = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.messages.append(msg)
        self.updated_at = datetime.utcnow()
    
    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get conversation history as list of dicts."""
        messages = self.messages
        if limit:
            messages = messages[-limit:]
        return [m.to_dict() for m in messages]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "messages": [m.to_dict() for m in self.messages],
            "context": self.context,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        return cls(
            session_id=data["session_id"],
            user_id=data.get("user_id"),
            messages=[Message.from_dict(m) for m in data.get("messages", [])],
            context=data.get("context", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
            metadata=data.get("metadata", {})
        )
    
    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at


class InMemorySessionStore:
    """In-memory session storage for development."""
    
    def __init__(self, cleanup_interval: int = 300):
        self._sessions: Dict[str, Session] = {}
        self._lock = asyncio.Lock()
        self._cleanup_interval = cleanup_interval
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start background cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_expired())
    
    async def stop(self):
        """Stop background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
    
    async def _cleanup_expired(self):
        """Periodically remove expired sessions."""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                async with self._lock:
                    expired_ids = [
                        sid for sid, session in self._sessions.items()
                        if session.is_expired
                    ]
                    for sid in expired_ids:
                        del self._sessions[sid]
                    if expired_ids:
                        logger.info(f"Cleaned up {len(expired_ids)} expired sessions")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Session cleanup error: {e}")
    
    async def create(self, user_id: Optional[str] = None, ttl_hours: int = 24) -> Session:
        """Create a new session."""
        session_id = str(uuid.uuid4())
        session = Session(
            session_id=session_id,
            user_id=user_id,
            expires_at=datetime.utcnow() + timedelta(hours=ttl_hours)
        )
        async with self._lock:
            self._sessions[session_id] = session
        return session
    
    async def get(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        async with self._lock:
            session = self._sessions.get(session_id)
            if session and not session.is_expired:
                return session
            elif session and session.is_expired:
                del self._sessions[session_id]
            return None
    
    async def update(self, session: Session) -> bool:
        """Update an existing session."""
        async with self._lock:
            if session.session_id in self._sessions:
                session.updated_at = datetime.utcnow()
                self._sessions[session.session_id] = session
                return True
            return False
    
    async def delete(self, session_id: str) -> bool:
        """Delete a session."""
        async with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False
    
    async def get_by_user(self, user_id: str) -> List[Session]:
        """Get all sessions for a user."""
        async with self._lock:
            return [
                s for s in self._sessions.values()
                if s.user_id == user_id and not s.is_expired
            ]


class RedisSessionStore:
    """Redis-based session storage for production."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", key_prefix: str = "finfind:session:"):
        self._redis_url = redis_url
        self._key_prefix = key_prefix
        self._redis = None
    
    async def start(self):
        """Initialize Redis connection."""
        try:
            import redis.asyncio as redis
            self._redis = redis.from_url(self._redis_url)
            await self._redis.ping()
            logger.info("Redis session store connected")
        except ImportError:
            logger.warning("redis package not installed, falling back to in-memory")
            raise
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            raise
    
    async def stop(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
    
    def _key(self, session_id: str) -> str:
        return f"{self._key_prefix}{session_id}"
    
    async def create(self, user_id: Optional[str] = None, ttl_hours: int = 24) -> Session:
        """Create a new session in Redis."""
        session_id = str(uuid.uuid4())
        session = Session(
            session_id=session_id,
            user_id=user_id,
            expires_at=datetime.utcnow() + timedelta(hours=ttl_hours)
        )
        
        await self._redis.setex(
            self._key(session_id),
            timedelta(hours=ttl_hours),
            json.dumps(session.to_dict())
        )
        
        # Index by user_id
        if user_id:
            await self._redis.sadd(f"{self._key_prefix}user:{user_id}", session_id)
        
        return session
    
    async def get(self, session_id: str) -> Optional[Session]:
        """Get a session from Redis."""
        data = await self._redis.get(self._key(session_id))
        if data:
            return Session.from_dict(json.loads(data))
        return None
    
    async def update(self, session: Session) -> bool:
        """Update a session in Redis."""
        key = self._key(session.session_id)
        if await self._redis.exists(key):
            session.updated_at = datetime.utcnow()
            ttl = await self._redis.ttl(key)
            if ttl > 0:
                await self._redis.setex(key, ttl, json.dumps(session.to_dict()))
            else:
                await self._redis.set(key, json.dumps(session.to_dict()))
            return True
        return False
    
    async def delete(self, session_id: str) -> bool:
        """Delete a session from Redis."""
        session = await self.get(session_id)
        result = await self._redis.delete(self._key(session_id))
        
        # Remove from user index
        if session and session.user_id:
            await self._redis.srem(f"{self._key_prefix}user:{session.user_id}", session_id)
        
        return result > 0
    
    async def get_by_user(self, user_id: str) -> List[Session]:
        """Get all sessions for a user from Redis."""
        session_ids = await self._redis.smembers(f"{self._key_prefix}user:{user_id}")
        sessions = []
        for sid in session_ids:
            session = await self.get(sid.decode() if isinstance(sid, bytes) else sid)
            if session:
                sessions.append(session)
        return sessions


class SessionService:
    """
    Unified session service with configurable backend.
    
    Provides consistent interface for:
    - Session creation and management
    - Conversation history
    - Context persistence
    """
    
    def __init__(self, use_redis: bool = False, redis_url: Optional[str] = None):
        self._use_redis = use_redis
        self._redis_url = redis_url or "redis://localhost:6379"
        self._store = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the session store."""
        if self._initialized:
            return
        
        if self._use_redis:
            try:
                self._store = RedisSessionStore(self._redis_url)
                await self._store.start()
                logger.info("Using Redis session store")
            except Exception as e:
                logger.warning(f"Redis unavailable, using in-memory: {e}")
                self._store = InMemorySessionStore()
                await self._store.start()
        else:
            self._store = InMemorySessionStore()
            await self._store.start()
            logger.info("Using in-memory session store")
        
        self._initialized = True
    
    async def shutdown(self):
        """Shutdown the session store."""
        if self._store:
            await self._store.stop()
        self._initialized = False
    
    async def create_session(
        self,
        user_id: Optional[str] = None,
        ttl_hours: int = 24,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> Session:
        """Create a new conversation session."""
        await self.initialize()
        session = await self._store.create(user_id, ttl_hours)
        if initial_context:
            session.context = initial_context
            await self._store.update(session)
        return session
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get an existing session."""
        await self.initialize()
        return await self._store.get(session_id)
    
    async def add_user_message(
        self,
        session_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add a user message to the session."""
        await self.initialize()
        session = await self._store.get(session_id)
        if session:
            session.add_message("user", content, metadata)
            return await self._store.update(session)
        return False
    
    async def add_assistant_message(
        self,
        session_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add an assistant message to the session."""
        await self.initialize()
        session = await self._store.get(session_id)
        if session:
            session.add_message("assistant", content, metadata)
            return await self._store.update(session)
        return False
    
    async def get_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get conversation history for a session."""
        await self.initialize()
        session = await self._store.get(session_id)
        if session:
            return session.get_history(limit)
        return []
    
    async def update_context(
        self,
        session_id: str,
        context_updates: Dict[str, Any]
    ) -> bool:
        """Update session context."""
        await self.initialize()
        session = await self._store.get(session_id)
        if session:
            session.context.update(context_updates)
            return await self._store.update(session)
        return False
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        await self.initialize()
        return await self._store.delete(session_id)
    
    async def get_user_sessions(self, user_id: str) -> List[Session]:
        """Get all sessions for a user."""
        await self.initialize()
        return await self._store.get_by_user(user_id)


# Singleton instance
_session_service: Optional[SessionService] = None


def get_session_service(
    use_redis: bool = False,
    redis_url: Optional[str] = None
) -> SessionService:
    """Get or create the session service singleton."""
    global _session_service
    if _session_service is None:
        _session_service = SessionService(use_redis, redis_url)
    return _session_service
