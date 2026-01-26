"""
Agent State Management for FinFind.

Defines state structures for tracking agent context,
user information, and conversation history.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
import uuid


class ConversationStage(str, Enum):
    """Stages of a shopping conversation."""
    INITIAL = "initial"
    SEARCH = "search"
    BROWSE = "browse"
    COMPARE = "compare"
    DECIDE = "decide"
    PURCHASE = "purchase"


@dataclass
class FinancialContext:
    """User's financial context for filtering and recommendations."""
    
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    monthly_budget: Optional[float] = None
    disposable_income: Optional[float] = None
    credit_available: Optional[float] = None
    preferred_payment_method: Optional[str] = None
    risk_tolerance: str = "medium"  # low, medium, high
    
    def get_effective_budget(self) -> Optional[float]:
        """Get the effective maximum budget."""
        if self.budget_max:
            return self.budget_max
        if self.monthly_budget:
            return self.monthly_budget
        return self.disposable_income
    
    def can_afford(self, price: float, tolerance: float = 0.0) -> bool:
        """Check if a price is within budget."""
        max_budget = self.get_effective_budget()
        if max_budget is None:
            return True  # No budget constraint
        return price <= max_budget * (1 + tolerance)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "budget_min": self.budget_min,
            "budget_max": self.budget_max,
            "monthly_budget": self.monthly_budget,
            "disposable_income": self.disposable_income,
            "risk_tolerance": self.risk_tolerance
        }


@dataclass
class UserContext:
    """Context about the current user."""
    
    user_id: Optional[str] = None
    persona_type: Optional[str] = None
    financial: FinancialContext = field(default_factory=FinancialContext)
    
    # Preferences
    preferred_categories: List[str] = field(default_factory=list)
    preferred_brands: List[str] = field(default_factory=list)
    disliked_brands: List[str] = field(default_factory=list)
    
    # History
    recent_searches: List[str] = field(default_factory=list)
    viewed_products: List[str] = field(default_factory=list)
    purchased_products: List[str] = field(default_factory=list)
    
    # Session info
    device_type: str = "desktop"
    session_start: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "persona_type": self.persona_type,
            "financial": self.financial.to_dict(),
            "preferred_categories": self.preferred_categories,
            "preferred_brands": self.preferred_brands,
            "recent_searches": self.recent_searches[-5:],  # Last 5
            "viewed_products": self.viewed_products[-10:],  # Last 10
        }


@dataclass
class SearchContext:
    """Context from a search operation."""
    
    query: str
    interpreted_query: Optional[str] = None
    detected_intent: Optional[str] = None
    filters_applied: Dict[str, Any] = field(default_factory=dict)
    results_count: int = 0
    top_categories: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ProductContext:
    """Context about products being discussed."""
    
    product_ids: List[str] = field(default_factory=list)
    product_details: Dict[str, Dict] = field(default_factory=dict)
    compared_products: List[str] = field(default_factory=list)
    recommended_products: List[str] = field(default_factory=list)
    rejected_products: List[str] = field(default_factory=list)


@dataclass
class ConversationContext:
    """Full conversation context."""
    
    conversation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    stage: ConversationStage = ConversationStage.INITIAL
    
    # Message history
    messages: List[Dict[str, Any]] = field(default_factory=list)
    
    # Contexts
    user: UserContext = field(default_factory=UserContext)
    search: Optional[SearchContext] = None
    products: ProductContext = field(default_factory=ProductContext)
    
    # Agent tracking
    agents_involved: List[str] = field(default_factory=list)
    current_agent: Optional[str] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def add_message(self, role: str, content: str, agent: Optional[str] = None):
        """Add a message to the conversation."""
        self.messages.append({
            "role": role,
            "content": content,
            "agent": agent,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.updated_at = datetime.utcnow()
    
    def get_recent_messages(self, n: int = 10) -> List[Dict]:
        """Get the n most recent messages."""
        return self.messages[-n:]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "stage": self.stage.value,
            "user": self.user.to_dict(),
            "search": {
                "query": self.search.query,
                "intent": self.search.detected_intent
            } if self.search else None,
            "products": {
                "viewed": self.products.product_ids[-5:],
                "recommended": self.products.recommended_products[-5:]
            },
            "message_count": len(self.messages)
        }


@dataclass
class AgentState:
    """
    Complete state for an agent execution.
    
    This is the main state object passed between agents
    and through the agent execution pipeline.
    """
    
    # Request info
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    input_text: str = ""
    
    # Context
    context: ConversationContext = field(default_factory=ConversationContext)
    
    # Agent execution
    current_agent: Optional[str] = None
    agent_chain: List[str] = field(default_factory=list)
    delegation_depth: int = 0
    
    # Results
    results: Dict[str, Any] = field(default_factory=dict)
    intermediate_results: List[Dict] = field(default_factory=list)
    
    # Output
    output_text: Optional[str] = None
    output_products: List[Dict] = field(default_factory=list)
    output_explanations: List[Dict] = field(default_factory=list)
    
    # Error tracking
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Metadata
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    
    def add_result(self, agent: str, result: Dict[str, Any]):
        """Add intermediate result from an agent."""
        self.intermediate_results.append({
            "agent": agent,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def add_error(self, error: str):
        """Add an error message."""
        self.errors.append(error)
    
    def add_warning(self, warning: str):
        """Add a warning message."""
        self.warnings.append(warning)
    
    def mark_complete(self):
        """Mark the state as complete."""
        self.end_time = datetime.utcnow()
    
    @property
    def execution_time_ms(self) -> Optional[float]:
        """Get execution time in milliseconds."""
        if self.end_time:
            delta = self.end_time - self.start_time
            return delta.total_seconds() * 1000
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        return {
            "request_id": self.request_id,
            "input": self.input_text,
            "output": self.output_text,
            "products": len(self.output_products),
            "agents": self.agent_chain,
            "errors": self.errors,
            "execution_time_ms": self.execution_time_ms
        }
