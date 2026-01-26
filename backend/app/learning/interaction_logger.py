"""
Interaction Logger for FinFind Learning System.

Captures all user interactions with full context for learning
and improvement. Supports batch writing to Qdrant for efficiency.
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import deque
import uuid

from .models import (
    Interaction,
    InteractionType,
    InteractionContext,
    FeedbackSignal
)

logger = logging.getLogger(__name__)


class InteractionLogger:
    """
    Logs all user interactions for the learning system.
    
    Features:
    - Captures interactions with full context
    - Buffers writes for batch efficiency
    - Derives feedback signals from interaction types
    - Tracks constraint violations
    """
    
    def __init__(
        self,
        buffer_size: int = 100,
        flush_interval_seconds: float = 30.0,
        qdrant_collection: str = "user_interactions"
    ):
        """
        Initialize the interaction logger.
        
        Args:
            buffer_size: Number of interactions to buffer before flushing
            flush_interval_seconds: Max time between flushes
            qdrant_collection: Qdrant collection name for interactions
        """
        self._buffer: deque = deque(maxlen=buffer_size * 2)  # Extra capacity
        self._buffer_size = buffer_size
        self._flush_interval = flush_interval_seconds
        self._collection = qdrant_collection
        
        # Statistics
        self._total_logged = 0
        self._total_flushed = 0
        self._flush_errors = 0
        
        # Background flush task
        self._flush_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Qdrant client (lazy loaded)
        self._qdrant_client = None
    
    async def start(self):
        """Start the background flush task."""
        if self._running:
            return
        
        self._running = True
        self._flush_task = asyncio.create_task(self._periodic_flush())
        logger.info("Interaction logger started")
    
    async def stop(self):
        """Stop the logger and flush remaining interactions."""
        self._running = False
        
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        
        # Final flush
        await self._flush_buffer()
        logger.info(f"Interaction logger stopped. Total logged: {self._total_logged}")
    
    async def _periodic_flush(self):
        """Periodically flush the buffer."""
        while self._running:
            await asyncio.sleep(self._flush_interval)
            await self._flush_buffer()
    
    # ========================================
    # Logging Methods
    # ========================================
    
    async def log_interaction(
        self,
        interaction_type: InteractionType,
        context: InteractionContext,
        items_shown: Optional[List[str]] = None,
        item_interacted: Optional[str] = None,
        position: Optional[int] = None,
        duration_ms: Optional[int] = None,
        item_price: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log a single interaction.
        
        Args:
            interaction_type: Type of interaction
            context: Context at interaction time
            items_shown: Product IDs shown to user
            item_interacted: Product ID user interacted with
            position: Position in list (for CTR)
            duration_ms: Time spent
            item_price: Price of interacted item
            metadata: Additional metadata
            
        Returns:
            Interaction ID
        """
        # Check for budget constraint violation
        budget_exceeded = False
        constraint_violated = None
        
        if item_price and context.budget_max:
            if item_price > context.budget_max:
                budget_exceeded = True
                constraint_violated = "budget_exceeded"
        
        # Derive feedback signal
        feedback_signal = self._derive_feedback_signal(
            interaction_type, position, duration_ms
        )
        
        interaction = Interaction(
            interaction_type=interaction_type,
            context=context,
            items_shown=items_shown or [],
            item_interacted=item_interacted,
            position=position,
            duration_ms=duration_ms,
            item_price=item_price,
            budget_exceeded=budget_exceeded,
            constraint_violated=constraint_violated,
            feedback_signal=feedback_signal,
            metadata=metadata or {}
        )
        
        self._buffer.append(interaction)
        self._total_logged += 1
        
        # Flush if buffer is full
        if len(self._buffer) >= self._buffer_size:
            await self._flush_buffer()
        
        return interaction.id
    
    async def log_search(
        self,
        user_id: str,
        session_id: str,
        query: str,
        results: List[str],
        search_type: str = "text",
        agent_used: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        budget_max: Optional[float] = None,
        ab_variant: Optional[str] = None
    ) -> str:
        """Log a search interaction."""
        interaction_type = {
            "text": InteractionType.SEARCH,
            "voice": InteractionType.VOICE_SEARCH,
            "image": InteractionType.IMAGE_SEARCH
        }.get(search_type, InteractionType.SEARCH)
        
        context = InteractionContext(
            user_id=user_id,
            session_id=session_id,
            query=query,
            budget_max=budget_max,
            filters_applied=filters or {},
            agent_used=agent_used,
            ab_test_variant=ab_variant
        )
        
        return await self.log_interaction(
            interaction_type=interaction_type,
            context=context,
            items_shown=results,
            metadata={"search_type": search_type, "result_count": len(results)}
        )
    
    async def log_product_click(
        self,
        user_id: str,
        session_id: str,
        product_id: str,
        position: int,
        items_shown: List[str],
        query: Optional[str] = None,
        item_price: Optional[float] = None,
        budget_max: Optional[float] = None,
        source: str = "search"  # search, recommendation, alternative
    ) -> str:
        """Log a product click interaction."""
        context = InteractionContext(
            user_id=user_id,
            session_id=session_id,
            query=query,
            budget_max=budget_max
        )
        
        return await self.log_interaction(
            interaction_type=InteractionType.PRODUCT_CLICK,
            context=context,
            items_shown=items_shown,
            item_interacted=product_id,
            position=position,
            item_price=item_price,
            metadata={"source": source}
        )
    
    async def log_recommendation_interaction(
        self,
        user_id: str,
        session_id: str,
        recommendations_shown: List[str],
        clicked_product: Optional[str] = None,
        position: Optional[int] = None,
        item_price: Optional[float] = None,
        agent_used: str = "RecommendationAgent",
        dismissed: bool = False
    ) -> str:
        """Log a recommendation view/click/dismiss."""
        context = InteractionContext(
            user_id=user_id,
            session_id=session_id,
            agent_used=agent_used
        )
        
        if dismissed:
            interaction_type = InteractionType.RECOMMENDATION_DISMISS
        elif clicked_product:
            interaction_type = InteractionType.RECOMMENDATION_CLICK
        else:
            interaction_type = InteractionType.RECOMMENDATION_VIEW
        
        return await self.log_interaction(
            interaction_type=interaction_type,
            context=context,
            recommendations_shown=recommendations_shown,
            item_interacted=clicked_product,
            position=position,
            item_price=item_price
        )
    
    async def log_alternative_interaction(
        self,
        user_id: str,
        session_id: str,
        original_product_id: str,
        alternatives_shown: List[str],
        alternative_clicked: Optional[str] = None,
        alternative_accepted: bool = False,
        item_price: Optional[float] = None,
        budget_max: Optional[float] = None
    ) -> str:
        """Log an alternative product interaction."""
        context = InteractionContext(
            user_id=user_id,
            session_id=session_id,
            budget_max=budget_max,
            agent_used="AlternativeAgent"
        )
        
        if alternative_accepted:
            interaction_type = InteractionType.ALTERNATIVE_ACCEPT
        elif alternative_clicked:
            interaction_type = InteractionType.ALTERNATIVE_CLICK
        else:
            interaction_type = InteractionType.ALTERNATIVE_VIEW
        
        return await self.log_interaction(
            interaction_type=interaction_type,
            context=context,
            alternatives_shown=alternatives_shown,
            item_interacted=alternative_clicked,
            item_price=item_price,
            metadata={"original_product_id": original_product_id}
        )
    
    async def log_cart_action(
        self,
        user_id: str,
        session_id: str,
        product_id: str,
        action: str,  # "add" or "remove"
        item_price: Optional[float] = None,
        budget_max: Optional[float] = None,
        source: str = "search"
    ) -> str:
        """Log add/remove cart actions."""
        context = InteractionContext(
            user_id=user_id,
            session_id=session_id,
            budget_max=budget_max
        )
        
        interaction_type = (
            InteractionType.ADD_TO_CART if action == "add" 
            else InteractionType.REMOVE_FROM_CART
        )
        
        return await self.log_interaction(
            interaction_type=interaction_type,
            context=context,
            item_interacted=product_id,
            item_price=item_price,
            metadata={"source": source}
        )
    
    async def log_purchase(
        self,
        user_id: str,
        session_id: str,
        products: List[Dict[str, Any]],
        total_amount: float,
        budget_max: Optional[float] = None
    ) -> str:
        """Log a purchase completion."""
        context = InteractionContext(
            user_id=user_id,
            session_id=session_id,
            budget_max=budget_max
        )
        
        product_ids = [p.get("id") for p in products]
        
        return await self.log_interaction(
            interaction_type=InteractionType.PURCHASE_COMPLETE,
            context=context,
            items_shown=product_ids,
            item_price=total_amount,
            metadata={
                "products": products,
                "item_count": len(products),
                "total_amount": total_amount
            }
        )
    
    async def log_explanation_feedback(
        self,
        user_id: str,
        session_id: str,
        product_id: str,
        helpful: bool,
        explanation_text: Optional[str] = None
    ) -> str:
        """Log feedback on explanations."""
        context = InteractionContext(
            user_id=user_id,
            session_id=session_id,
            agent_used="ExplainabilityAgent"
        )
        
        interaction_type = (
            InteractionType.EXPLANATION_HELPFUL if helpful
            else InteractionType.EXPLANATION_UNHELPFUL
        )
        
        return await self.log_interaction(
            interaction_type=interaction_type,
            context=context,
            item_interacted=product_id,
            metadata={"explanation_text": explanation_text}
        )
    
    # ========================================
    # Helper Methods
    # ========================================
    
    def _derive_feedback_signal(
        self,
        interaction_type: InteractionType,
        position: Optional[int],
        duration_ms: Optional[int]
    ) -> FeedbackSignal:
        """Derive feedback signal from interaction type and context."""
        
        # Strong positive signals
        if interaction_type in [
            InteractionType.PURCHASE,
            InteractionType.PURCHASE_COMPLETE,
            InteractionType.ADD_TO_CART,
            InteractionType.ALTERNATIVE_ACCEPT,
            InteractionType.EXPLANATION_HELPFUL,
            InteractionType.RATING,
        ]:
            return FeedbackSignal.POSITIVE
        
        # Strong negative signals
        if interaction_type in [
            InteractionType.REMOVE_FROM_CART,
            InteractionType.RECOMMENDATION_DISMISS,
            InteractionType.ALTERNATIVE_REJECT,
            InteractionType.EXPLANATION_UNHELPFUL,
        ]:
            return FeedbackSignal.NEGATIVE
        
        # Click signals - positive if early position, implicit if late
        if interaction_type in [
            InteractionType.PRODUCT_CLICK,
            InteractionType.RECOMMENDATION_CLICK,
            InteractionType.ALTERNATIVE_CLICK,
        ]:
            if position is not None and position <= 3:
                return FeedbackSignal.POSITIVE
            return FeedbackSignal.IMPLICIT_POSITIVE
        
        # View signals - depends on duration
        if interaction_type in [
            InteractionType.PRODUCT_VIEW,
            InteractionType.RECOMMENDATION_VIEW,
            InteractionType.ALTERNATIVE_VIEW,
            InteractionType.EXPLANATION_VIEW,
        ]:
            if duration_ms and duration_ms > 5000:  # >5 seconds
                return FeedbackSignal.IMPLICIT_POSITIVE
            return FeedbackSignal.NEUTRAL
        
        return FeedbackSignal.NEUTRAL
    
    async def _flush_buffer(self):
        """Flush buffered interactions to storage."""
        if not self._buffer:
            return
        
        # Grab current buffer contents
        interactions = list(self._buffer)
        self._buffer.clear()
        
        if not interactions:
            return
        
        try:
            await self._write_to_storage(interactions)
            self._total_flushed += len(interactions)
            logger.debug(f"Flushed {len(interactions)} interactions to storage")
        except Exception as e:
            logger.error(f"Failed to flush interactions: {e}")
            self._flush_errors += 1
            # Re-add to buffer for retry (up to limit)
            for interaction in interactions[:self._buffer_size]:
                self._buffer.append(interaction)
    
    async def _write_to_storage(self, interactions: List[Interaction]):
        """Write interactions to Qdrant storage."""
        try:
            # Lazy load Qdrant client
            if self._qdrant_client is None:
                from ..agents.services.qdrant_service import get_qdrant_service
                self._qdrant_client = get_qdrant_service()
            
            # Prepare points for upsert
            points = []
            for interaction in interactions:
                # Create a simple embedding from interaction data
                # In production, use proper embedding model
                points.append({
                    "id": interaction.id,
                    "payload": interaction.to_dict()
                })
            
            # Batch upsert to Qdrant
            # Note: For production, ensure collection exists with proper schema
            await self._qdrant_client.upsert_points(
                collection_name=self._collection,
                points=points
            )
            
        except Exception as e:
            logger.warning(f"Qdrant write failed, falling back to memory: {e}")
            # Store in memory as fallback (for development/testing)
            if not hasattr(self, '_memory_store'):
                self._memory_store = []
            for interaction in interactions:
                self._memory_store.append(interaction.to_dict())
    
    # ========================================
    # Query Methods
    # ========================================
    
    async def get_user_interactions(
        self,
        user_id: str,
        interaction_types: Optional[List[InteractionType]] = None,
        limit: int = 100,
        since: Optional[datetime] = None
    ) -> List[Interaction]:
        """Get interactions for a user."""
        # Try Qdrant first
        try:
            if self._qdrant_client is None:
                from ..agents.services.qdrant_service import get_qdrant_service
                self._qdrant_client = get_qdrant_service()
            
            filters = {"must": [{"key": "context.user_id", "match": {"value": user_id}}]}
            
            if interaction_types:
                type_values = [it.value for it in interaction_types]
                filters["must"].append({
                    "key": "interaction_type",
                    "match": {"any": type_values}
                })
            
            results = await self._qdrant_client.scroll(
                collection_name=self._collection,
                scroll_filter=filters,
                limit=limit
            )
            
            return [Interaction.from_dict(r.payload) for r in results]
            
        except Exception as e:
            logger.warning(f"Qdrant read failed: {e}")
            # Fallback to memory store
            if hasattr(self, '_memory_store'):
                filtered = [
                    Interaction.from_dict(i) for i in self._memory_store
                    if i.get("context", {}).get("user_id") == user_id
                ]
                return filtered[:limit]
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get logger statistics."""
        return {
            "total_logged": self._total_logged,
            "total_flushed": self._total_flushed,
            "buffer_size": len(self._buffer),
            "flush_errors": self._flush_errors,
            "running": self._running
        }


# Singleton instance
_interaction_logger: Optional[InteractionLogger] = None


def get_interaction_logger() -> InteractionLogger:
    """Get the singleton interaction logger instance."""
    global _interaction_logger
    if _interaction_logger is None:
        _interaction_logger = InteractionLogger()
    return _interaction_logger
