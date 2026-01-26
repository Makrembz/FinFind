"""
Context Manager for FinFind Agents.

Manages context sharing between agents, context compression,
and context persistence for multi-turn conversations.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import asdict

from .agent_state import (
    AgentState, 
    ConversationContext, 
    UserContext,
    FinancialContext,
    SearchContext,
    ProductContext
)

logger = logging.getLogger(__name__)


class ContextManager:
    """
    Manages context for the agent system.
    
    Responsibilities:
    - Store and retrieve conversation contexts
    - Compress context for token efficiency
    - Share context between agents
    - Persist context for multi-turn conversations
    """
    
    def __init__(self, max_history: int = 100):
        """
        Initialize the context manager.
        
        Args:
            max_history: Maximum number of conversations to keep in memory.
        """
        self._contexts: Dict[str, ConversationContext] = {}
        self._max_history = max_history
        self._access_times: Dict[str, datetime] = {}
    
    # ========================================
    # Context CRUD Operations
    # ========================================
    
    def create_context(
        self,
        user_id: Optional[str] = None,
        user_context: Optional[UserContext] = None
    ) -> ConversationContext:
        """
        Create a new conversation context.
        
        Args:
            user_id: Optional user ID to associate.
            user_context: Optional pre-populated user context.
            
        Returns:
            New ConversationContext instance.
        """
        context = ConversationContext()
        
        if user_context:
            context.user = user_context
        elif user_id:
            context.user.user_id = user_id
        
        self._contexts[context.conversation_id] = context
        self._access_times[context.conversation_id] = datetime.utcnow()
        
        # Cleanup old contexts if needed
        self._cleanup_old_contexts()
        
        logger.debug(f"Created new context: {context.conversation_id}")
        return context
    
    def get_context(self, conversation_id: str) -> Optional[ConversationContext]:
        """
        Get a conversation context by ID.
        
        Args:
            conversation_id: The conversation ID to look up.
            
        Returns:
            The ConversationContext or None if not found.
        """
        context = self._contexts.get(conversation_id)
        if context:
            self._access_times[conversation_id] = datetime.utcnow()
        return context
    
    def update_context(
        self, 
        conversation_id: str, 
        updates: Dict[str, Any]
    ) -> Optional[ConversationContext]:
        """
        Update a conversation context.
        
        Args:
            conversation_id: The conversation ID to update.
            updates: Dictionary of updates to apply.
            
        Returns:
            Updated ConversationContext or None.
        """
        context = self.get_context(conversation_id)
        if not context:
            return None
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(context, key):
                setattr(context, key, value)
        
        context.updated_at = datetime.utcnow()
        return context
    
    def delete_context(self, conversation_id: str) -> bool:
        """
        Delete a conversation context.
        
        Args:
            conversation_id: The conversation ID to delete.
            
        Returns:
            True if deleted, False if not found.
        """
        if conversation_id in self._contexts:
            del self._contexts[conversation_id]
            del self._access_times[conversation_id]
            return True
        return False
    
    # ========================================
    # User Context Management
    # ========================================
    
    def load_user_context(
        self,
        user_id: str,
        user_data: Dict[str, Any]
    ) -> UserContext:
        """
        Load user context from user profile data.
        
        Args:
            user_id: The user ID.
            user_data: User profile data from Qdrant.
            
        Returns:
            Populated UserContext.
        """
        financial = FinancialContext(
            budget_min=user_data.get('budget_min'),
            budget_max=user_data.get('budget_max'),
            monthly_budget=user_data.get('monthly_budget'),
            disposable_income=user_data.get('disposable_income'),
            risk_tolerance=user_data.get('risk_tolerance', 'medium')
        )
        
        user_context = UserContext(
            user_id=user_id,
            persona_type=user_data.get('persona_type'),
            financial=financial,
            preferred_categories=user_data.get('preferred_categories', []),
            preferred_brands=user_data.get('preferred_brands', [])
        )
        
        return user_context
    
    def update_user_financial(
        self,
        conversation_id: str,
        budget_min: Optional[float] = None,
        budget_max: Optional[float] = None
    ):
        """Update user's financial context in a conversation."""
        context = self.get_context(conversation_id)
        if context:
            if budget_min is not None:
                context.user.financial.budget_min = budget_min
            if budget_max is not None:
                context.user.financial.budget_max = budget_max
    
    # ========================================
    # Search Context Management
    # ========================================
    
    def set_search_context(
        self,
        conversation_id: str,
        query: str,
        interpreted_query: Optional[str] = None,
        detected_intent: Optional[str] = None,
        filters: Optional[Dict] = None,
        results_count: int = 0
    ):
        """Set search context for a conversation."""
        context = self.get_context(conversation_id)
        if context:
            context.search = SearchContext(
                query=query,
                interpreted_query=interpreted_query,
                detected_intent=detected_intent,
                filters_applied=filters or {},
                results_count=results_count
            )
            
            # Add to recent searches
            if query not in context.user.recent_searches:
                context.user.recent_searches.append(query)
                # Keep only last 20 searches
                context.user.recent_searches = context.user.recent_searches[-20:]
    
    # ========================================
    # Product Context Management
    # ========================================
    
    def add_viewed_product(
        self,
        conversation_id: str,
        product_id: str,
        product_data: Optional[Dict] = None
    ):
        """Add a viewed product to the context."""
        context = self.get_context(conversation_id)
        if context:
            if product_id not in context.products.product_ids:
                context.products.product_ids.append(product_id)
            if product_data:
                context.products.product_details[product_id] = product_data
            
            # Also add to user's viewed products
            if product_id not in context.user.viewed_products:
                context.user.viewed_products.append(product_id)
    
    def add_recommended_products(
        self,
        conversation_id: str,
        product_ids: List[str]
    ):
        """Add recommended products to the context."""
        context = self.get_context(conversation_id)
        if context:
            for pid in product_ids:
                if pid not in context.products.recommended_products:
                    context.products.recommended_products.append(pid)
    
    def mark_product_rejected(
        self,
        conversation_id: str,
        product_id: str,
        reason: Optional[str] = None
    ):
        """Mark a product as rejected by the user."""
        context = self.get_context(conversation_id)
        if context:
            if product_id not in context.products.rejected_products:
                context.products.rejected_products.append(product_id)
    
    # ========================================
    # Context Compression
    # ========================================
    
    def compress_context(
        self,
        context: ConversationContext,
        max_messages: int = 10,
        include_products: bool = True
    ) -> Dict[str, Any]:
        """
        Compress context for efficient token usage.
        
        Args:
            context: The conversation context.
            max_messages: Maximum messages to include.
            include_products: Whether to include product details.
            
        Returns:
            Compressed context dictionary.
        """
        compressed = {
            "conversation_id": context.conversation_id,
            "stage": context.stage.value,
            "user": {
                "id": context.user.user_id,
                "persona": context.user.persona_type,
                "budget_max": context.user.financial.budget_max,
                "budget_min": context.user.financial.budget_min,
                "preferred_categories": context.user.preferred_categories[:3],
            },
            "recent_messages": [
                {"role": m["role"], "content": m["content"][:200]}
                for m in context.messages[-max_messages:]
            ],
        }
        
        if context.search:
            compressed["search"] = {
                "query": context.search.query,
                "intent": context.search.detected_intent,
                "results": context.search.results_count
            }
        
        if include_products and context.products.recommended_products:
            compressed["recommended_products"] = context.products.recommended_products[:5]
        
        return compressed
    
    def get_context_for_agent(
        self,
        conversation_id: str,
        agent_type: str
    ) -> Dict[str, Any]:
        """
        Get context optimized for a specific agent type.
        
        Different agents need different context details.
        """
        context = self.get_context(conversation_id)
        if not context:
            return {}
        
        base = self.compress_context(context)
        
        if agent_type == "search":
            # SearchAgent needs search history and preferences
            base["recent_searches"] = context.user.recent_searches[-5:]
            base["preferred_brands"] = context.user.preferred_brands
            
        elif agent_type == "recommendation":
            # RecommendationAgent needs full user profile
            base["full_financial"] = context.user.financial.to_dict()
            base["purchase_history"] = context.user.purchased_products[-10:]
            base["viewed_products"] = context.user.viewed_products[-10:]
            
        elif agent_type == "explainability":
            # ExplainabilityAgent needs product details
            base["product_details"] = {
                pid: context.products.product_details.get(pid, {})
                for pid in context.products.recommended_products[:3]
            }
            
        elif agent_type == "alternative":
            # AlternativeAgent needs rejected products and constraints
            base["rejected_products"] = context.products.rejected_products
            base["constraints_failed"] = True  # Indicates why alternative was called
        
        return base
    
    # ========================================
    # Context Serialization
    # ========================================
    
    def serialize_context(self, context: ConversationContext) -> str:
        """Serialize context to JSON string."""
        return json.dumps(context.to_dict(), default=str)
    
    def deserialize_context(self, data: str) -> ConversationContext:
        """Deserialize context from JSON string."""
        parsed = json.loads(data)
        # Reconstruct context from dictionary
        context = ConversationContext()
        context.conversation_id = parsed.get("conversation_id", context.conversation_id)
        # ... additional reconstruction logic
        return context
    
    # ========================================
    # Cleanup
    # ========================================
    
    def _cleanup_old_contexts(self):
        """Remove old contexts if over limit."""
        if len(self._contexts) <= self._max_history:
            return
        
        # Sort by access time and remove oldest
        sorted_ids = sorted(
            self._access_times.items(),
            key=lambda x: x[1]
        )
        
        # Remove oldest 20%
        to_remove = int(len(sorted_ids) * 0.2)
        for conv_id, _ in sorted_ids[:to_remove]:
            self.delete_context(conv_id)
        
        logger.info(f"Cleaned up {to_remove} old contexts")
    
    def cleanup_expired(self, max_age_hours: int = 24):
        """Remove contexts older than max_age_hours."""
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        to_remove = [
            conv_id for conv_id, access_time in self._access_times.items()
            if access_time < cutoff
        ]
        
        for conv_id in to_remove:
            self.delete_context(conv_id)
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} expired contexts")


# Global context manager instance
_context_manager: Optional[ContextManager] = None


def get_context_manager() -> ContextManager:
    """Get or create the global context manager."""
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager
