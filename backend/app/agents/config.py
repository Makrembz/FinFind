"""
Agent System Configuration for FinFind.

Centralizes all configuration for the multi-agent system including
LLM settings, Qdrant connection, and agent-specific parameters.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum

from dotenv import load_dotenv

load_dotenv()


class AgentType(str, Enum):
    """Types of agents in the system."""
    SEARCH = "search"
    RECOMMENDATION = "recommendation"
    EXPLAINABILITY = "explainability"
    ALTERNATIVE = "alternative"


class SearchStrategy(str, Enum):
    """Vector search strategies."""
    SIMILARITY = "similarity"
    MMR = "mmr"  # Maximal Marginal Relevance
    HYBRID = "hybrid"


@dataclass
class LLMConfig:
    """Configuration for the LLM provider (Groq)."""
    
    provider: str = "groq"
    model: str = field(
        default_factory=lambda: os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    )
    api_key: str = field(
        default_factory=lambda: os.getenv("GROQ_API_KEY", "")
    )
    temperature: float = 0.1
    max_tokens: int = 4096
    timeout: int = 60
    max_retries: int = 3
    
    # Rate limiting
    requests_per_minute: int = 30
    tokens_per_minute: int = 14400


@dataclass
class QdrantConfig:
    """Configuration for Qdrant Cloud connection."""
    
    url: str = field(
        default_factory=lambda: os.getenv("QDRANT_URL", "")
    )
    api_key: str = field(
        default_factory=lambda: os.getenv("QDRANT_API_KEY", "")
    )
    
    # Collection names
    products_collection: str = field(
        default_factory=lambda: os.getenv("QDRANT_PRODUCTS_COLLECTION", "products")
    )
    user_profiles_collection: str = field(
        default_factory=lambda: os.getenv("QDRANT_USER_PROFILES_COLLECTION", "user_profiles")
    )
    reviews_collection: str = field(
        default_factory=lambda: os.getenv("QDRANT_REVIEWS_COLLECTION", "reviews")
    )
    interactions_collection: str = field(
        default_factory=lambda: os.getenv("QDRANT_INTERACTIONS_COLLECTION", "user_interactions")
    )
    
    # Search settings
    default_limit: int = 10
    mmr_diversity: float = 0.3
    score_threshold: float = 0.5


@dataclass
class EmbeddingConfig:
    """Configuration for embedding model."""
    
    model_name: str = field(
        default_factory=lambda: os.getenv(
            "EMBEDDING_MODEL", 
            "sentence-transformers/all-MiniLM-L6-v2"
        )
    )
    dimension: int = 384
    max_seq_length: int = 256
    batch_size: int = 32


@dataclass 
class SearchAgentConfig:
    """Configuration specific to SearchAgent."""
    
    # Search settings
    default_limit: int = 10
    max_limit: int = 50
    search_strategy: SearchStrategy = SearchStrategy.MMR
    mmr_lambda: float = 0.7  # Balance between relevance and diversity
    
    # Query interpretation
    expand_synonyms: bool = True
    detect_intent: bool = True
    
    # Financial filtering
    apply_budget_filter: bool = True
    budget_tolerance: float = 0.2  # 20% above budget allowed


@dataclass
class RecommendationAgentConfig:
    """Configuration specific to RecommendationAgent."""
    
    # Recommendation settings
    default_recommendations: int = 5
    max_recommendations: int = 20
    
    # Scoring weights
    relevance_weight: float = 0.4
    affordability_weight: float = 0.3
    rating_weight: float = 0.2
    popularity_weight: float = 0.1
    
    # User context
    use_purchase_history: bool = True
    use_browsing_history: bool = True
    history_window_days: int = 30


@dataclass
class ExplainabilityAgentConfig:
    """Configuration specific to ExplainabilityAgent."""
    
    # Explanation settings
    include_similarity_score: bool = True
    include_financial_analysis: bool = True
    include_feature_comparison: bool = True
    include_review_summary: bool = True
    
    # Detail level
    explanation_detail: str = "detailed"  # brief, detailed, comprehensive
    max_factors: int = 5


@dataclass
class AlternativeAgentConfig:
    """Configuration specific to AlternativeAgent."""
    
    # Alternative finding settings
    price_range_step: float = 0.1  # 10% step for price adjustments
    max_price_adjustments: int = 5
    min_similarity_score: float = 0.6
    
    # Alternative types
    include_downgrades: bool = True
    include_different_brands: bool = True
    include_different_categories: bool = False
    
    # Limits
    alternatives_per_type: int = 3


@dataclass
class A2AConfig:
    """Configuration for Agent-to-Agent communication."""
    
    # Communication settings
    max_delegation_depth: int = 3
    timeout_per_agent: int = 30
    
    # Context sharing
    share_full_context: bool = True
    context_compression: bool = False
    
    # Logging
    log_communications: bool = True


@dataclass
class AgentConfig:
    """Master configuration for the agent system."""
    
    # Core configurations
    llm: LLMConfig = field(default_factory=LLMConfig)
    qdrant: QdrantConfig = field(default_factory=QdrantConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    
    # Agent-specific configurations
    search: SearchAgentConfig = field(default_factory=SearchAgentConfig)
    recommendation: RecommendationAgentConfig = field(default_factory=RecommendationAgentConfig)
    explainability: ExplainabilityAgentConfig = field(default_factory=ExplainabilityAgentConfig)
    alternative: AlternativeAgentConfig = field(default_factory=AlternativeAgentConfig)
    
    # A2A configuration
    a2a: A2AConfig = field(default_factory=A2AConfig)
    
    # System settings
    debug: bool = field(
        default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true"
    )
    log_level: str = field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO")
    )
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        if not self.llm.api_key:
            errors.append("GROQ_API_KEY is not set")
        
        if not self.qdrant.url:
            errors.append("QDRANT_URL is not set")
        
        if not self.qdrant.api_key:
            errors.append("QDRANT_API_KEY is not set")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary (masks sensitive values)."""
        return {
            "llm": {
                "provider": self.llm.provider,
                "model": self.llm.model,
                "temperature": self.llm.temperature,
                "api_key": "***" if self.llm.api_key else "NOT SET"
            },
            "qdrant": {
                "url": self.qdrant.url,
                "api_key": "***" if self.qdrant.api_key else "NOT SET",
                "collections": {
                    "products": self.qdrant.products_collection,
                    "user_profiles": self.qdrant.user_profiles_collection,
                    "reviews": self.qdrant.reviews_collection,
                    "interactions": self.qdrant.interactions_collection
                }
            },
            "debug": self.debug
        }


# Global config instance
_config: Optional[AgentConfig] = None


def get_config() -> AgentConfig:
    """Get or create the global config instance."""
    global _config
    if _config is None:
        _config = AgentConfig()
    return _config


def set_config(config: AgentConfig):
    """Set the global config instance."""
    global _config
    _config = config
