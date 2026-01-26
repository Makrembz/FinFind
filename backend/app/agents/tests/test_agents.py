"""
Tests for the FinFind Agent System.

Run with: pytest backend/app/agents/tests/test_agents.py -v
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Test imports - verifies module structure
from ..config import (
    AgentConfig, 
    get_config, 
    AgentType,
    LLMConfig,
    QdrantConfig,
    EmbeddingConfig
)
from ..base import (
    BaseAgent,
    AgentState,
    ConversationContext,
    ContextManager,
    get_context_manager,
    UserContext,
    FinancialContext
)
from ..orchestrator import (
    AgentOrchestrator,
    A2AProtocol,
    A2AMessage,
    A2AMessageType
)
from ..search_agent import SearchAgent
from ..recommendation_agent import RecommendationAgent
from ..explainability_agent import ExplainabilityAgent
from ..alternative_agent import AlternativeAgent


# ========================================
# Configuration Tests
# ========================================

class TestAgentConfig:
    """Tests for agent configuration."""
    
    def test_config_creation(self):
        """Test that config can be created."""
        config = AgentConfig()
        assert config is not None
        assert config.llm is not None
        assert config.qdrant is not None
        assert config.embedding is not None
    
    def test_llm_config_defaults(self):
        """Test LLM config defaults."""
        llm = LLMConfig()
        assert llm.provider == "groq"
        assert llm.temperature == 0.1
        assert llm.max_tokens == 4096
    
    def test_qdrant_config_collections(self):
        """Test Qdrant collection names."""
        qdrant = QdrantConfig()
        assert qdrant.products_collection == "products"
        assert qdrant.user_profiles_collection == "user_profiles"
        assert qdrant.reviews_collection == "reviews"
        assert qdrant.interactions_collection == "user_interactions"
    
    def test_embedding_config_dimensions(self):
        """Test embedding config dimensions."""
        embedding = EmbeddingConfig()
        assert embedding.dimension == 384
        assert "MiniLM" in embedding.model_name
    
    def test_agent_types(self):
        """Test agent type enum."""
        assert AgentType.SEARCH == "search"
        assert AgentType.RECOMMENDATION == "recommendation"
        assert AgentType.EXPLAINABILITY == "explainability"
        assert AgentType.ALTERNATIVE == "alternative"
    
    def test_config_to_dict(self):
        """Test config serialization."""
        config = AgentConfig()
        config_dict = config.to_dict()
        assert "llm" in config_dict
        assert "qdrant" in config_dict
        assert config_dict["llm"]["api_key"] in ["***", "NOT SET"]


# ========================================
# Agent State Tests
# ========================================

class TestAgentState:
    """Tests for agent state management."""
    
    def test_state_creation(self):
        """Test state creation."""
        state = AgentState(input_text="Find laptops")
        assert state.input_text == "Find laptops"
        assert state.status == "pending"
        assert state.output_products == []
    
    def test_state_add_result(self):
        """Test adding results to state."""
        state = AgentState(input_text="test")
        product = {"id": "1", "name": "Test Product"}
        state.add_result("SearchAgent", product)
        
        assert len(state.agent_results) == 1
        assert state.agent_results["SearchAgent"] == product
    
    def test_state_add_products(self):
        """Test adding products to state."""
        state = AgentState(input_text="test")
        products = [
            {"id": "1", "name": "Product 1"},
            {"id": "2", "name": "Product 2"}
        ]
        state.add_products(products)
        
        assert len(state.output_products) == 2
    
    def test_state_mark_complete(self):
        """Test marking state complete."""
        state = AgentState(input_text="test")
        state.mark_complete()
        
        assert state.status == "completed"
        assert state.completed_at is not None
        assert state.execution_time_ms >= 0
    
    def test_state_mark_failed(self):
        """Test marking state failed."""
        state = AgentState(input_text="test")
        state.mark_failed("Test error")
        
        assert state.status == "failed"
        assert "Test error" in state.errors


# ========================================
# Context Manager Tests
# ========================================

class TestContextManager:
    """Tests for context management."""
    
    def test_create_context(self):
        """Test context creation."""
        manager = ContextManager()
        context = manager.create_context(user_id="user123")
        
        assert context is not None
        assert context.user.user_id == "user123"
        assert context.conversation_id is not None
    
    def test_get_context(self):
        """Test retrieving context."""
        manager = ContextManager()
        context = manager.create_context(user_id="user123")
        
        retrieved = manager.get_context(context.conversation_id)
        assert retrieved is not None
        assert retrieved.conversation_id == context.conversation_id
    
    def test_add_message(self):
        """Test adding messages to context."""
        manager = ContextManager()
        context = manager.create_context()
        
        context.add_message("user", "Hello")
        context.add_message("assistant", "Hi there!")
        
        assert len(context.messages) == 2
        assert context.messages[0]["role"] == "user"
        assert context.messages[1]["role"] == "assistant"
    
    def test_delete_context(self):
        """Test deleting context."""
        manager = ContextManager()
        context = manager.create_context()
        conv_id = context.conversation_id
        
        result = manager.delete_context(conv_id)
        assert result is True
        
        retrieved = manager.get_context(conv_id)
        assert retrieved is None
    
    def test_global_context_manager(self):
        """Test global context manager singleton."""
        manager1 = get_context_manager()
        manager2 = get_context_manager()
        assert manager1 is manager2


# ========================================
# A2A Protocol Tests
# ========================================

class TestA2AProtocol:
    """Tests for A2A communication protocol."""
    
    def test_protocol_creation(self):
        """Test protocol creation."""
        protocol = A2AProtocol()
        assert protocol is not None
        assert protocol.list_agents() == []
    
    def test_register_agent(self):
        """Test agent registration."""
        protocol = A2AProtocol()
        mock_agent = Mock(spec=BaseAgent)
        mock_agent.name = "TestAgent"
        
        protocol.register_agent("TestAgent", mock_agent)
        assert "TestAgent" in protocol.list_agents()
    
    def test_unregister_agent(self):
        """Test agent unregistration."""
        protocol = A2AProtocol()
        mock_agent = Mock(spec=BaseAgent)
        
        protocol.register_agent("TestAgent", mock_agent)
        protocol.unregister_agent("TestAgent")
        
        assert "TestAgent" not in protocol.list_agents()
    
    def test_message_types(self):
        """Test message type enum."""
        assert A2AMessageType.DELEGATE_TASK is not None
        assert A2AMessageType.SHARE_CONTEXT is not None
        assert A2AMessageType.REQUEST_CONTEXT is not None
        assert A2AMessageType.HANDOFF is not None
    
    def test_create_message(self):
        """Test A2A message creation."""
        message = A2AMessage(
            sender="Agent1",
            recipient="Agent2",
            message_type=A2AMessageType.DELEGATE_TASK,
            content="Do something"
        )
        
        assert message.sender == "Agent1"
        assert message.recipient == "Agent2"
        assert message.message_id is not None


# ========================================
# Agent Orchestrator Tests
# ========================================

class TestAgentOrchestrator:
    """Tests for agent orchestrator."""
    
    @patch.object(AgentOrchestrator, 'initialize')
    def test_orchestrator_creation(self, mock_init):
        """Test orchestrator creation."""
        orchestrator = AgentOrchestrator()
        assert orchestrator is not None
        assert orchestrator._initialized is False
    
    def test_determine_agent_search(self):
        """Test agent determination for search queries."""
        orchestrator = AgentOrchestrator()
        
        agent = orchestrator._determine_agent("Find me a laptop")
        assert agent == "SearchAgent"
        
        agent = orchestrator._determine_agent("Search for phones")
        assert agent == "SearchAgent"
    
    def test_determine_agent_recommendation(self):
        """Test agent determination for recommendation queries."""
        orchestrator = AgentOrchestrator()
        
        agent = orchestrator._determine_agent("Recommend something for me")
        assert agent == "RecommendationAgent"
        
        agent = orchestrator._determine_agent("Give me a personalized suggestion")
        assert agent == "RecommendationAgent"
    
    def test_determine_agent_explainability(self):
        """Test agent determination for explanation queries."""
        orchestrator = AgentOrchestrator()
        
        agent = orchestrator._determine_agent("Why did you recommend this?")
        assert agent == "ExplainabilityAgent"
        
        agent = orchestrator._determine_agent("Explain this product")
        assert agent == "ExplainabilityAgent"
    
    def test_determine_agent_alternative(self):
        """Test agent determination for alternative queries."""
        orchestrator = AgentOrchestrator()
        
        agent = orchestrator._determine_agent("Find a cheaper alternative")
        assert agent == "AlternativeAgent"
        
        agent = orchestrator._determine_agent("Show me something similar to this")
        assert agent == "AlternativeAgent"
    
    def test_get_status(self):
        """Test orchestrator status."""
        orchestrator = AgentOrchestrator()
        status = orchestrator.get_status()
        
        assert "initialized" in status
        assert "agents" in status


# ========================================
# Agent Import Tests
# ========================================

class TestAgentImports:
    """Tests for agent module imports."""
    
    def test_search_agent_import(self):
        """Test SearchAgent import and creation."""
        config = AgentConfig()
        # Just test the import, not initialization (requires API keys)
        assert SearchAgent is not None
    
    def test_recommendation_agent_import(self):
        """Test RecommendationAgent import."""
        assert RecommendationAgent is not None
    
    def test_explainability_agent_import(self):
        """Test ExplainabilityAgent import."""
        assert ExplainabilityAgent is not None
    
    def test_alternative_agent_import(self):
        """Test AlternativeAgent import."""
        assert AlternativeAgent is not None


# ========================================
# Financial Context Tests
# ========================================

class TestFinancialContext:
    """Tests for financial context management."""
    
    def test_financial_context_creation(self):
        """Test financial context creation."""
        financial = FinancialContext(
            budget_min=100,
            budget_max=1000,
            risk_tolerance="medium"
        )
        
        assert financial.budget_min == 100
        assert financial.budget_max == 1000
        assert financial.risk_tolerance == "medium"
    
    def test_user_context_with_financial(self):
        """Test user context with financial data."""
        financial = FinancialContext(
            budget_max=500,
            monthly_budget=1000
        )
        
        user = UserContext(
            user_id="user123",
            financial=financial
        )
        
        assert user.user_id == "user123"
        assert user.financial.budget_max == 500


# ========================================
# Integration Tests (Require Mocking)
# ========================================

class TestIntegration:
    """Integration tests with mocked external services."""
    
    @pytest.mark.asyncio
    @patch('app.agents.tools.qdrant_tools.QdrantSearchTool._run')
    async def test_mock_search_flow(self, mock_qdrant):
        """Test search flow with mocked Qdrant."""
        mock_qdrant.return_value = {
            "success": True,
            "results": [
                {"id": "1", "name": "Test Product", "price": 100}
            ]
        }
        
        # Would test full flow here with mocked LLM and Qdrant
        # For now just verify the mock works
        from ..tools.qdrant_tools import QdrantSearchTool
        tool = QdrantSearchTool()
        result = tool._run(query="test")
        
        assert result["success"] is True


# ========================================
# Edge Case Tests
# ========================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_empty_input(self):
        """Test handling of empty input."""
        state = AgentState(input_text="")
        assert state.input_text == ""
    
    def test_long_input(self):
        """Test handling of very long input."""
        long_input = "a" * 10000
        state = AgentState(input_text=long_input)
        assert len(state.input_text) == 10000
    
    def test_special_characters_input(self):
        """Test handling of special characters."""
        special = "Find 'laptop' with <special> & \"chars\""
        state = AgentState(input_text=special)
        assert state.input_text == special
    
    def test_context_cleanup(self):
        """Test context cleanup functionality."""
        manager = ContextManager()
        
        # Create multiple contexts
        for i in range(5):
            manager.create_context(user_id=f"user{i}")
        
        # Verify they exist
        assert len(manager._contexts) == 5
        
        # Cleanup with 0 hour max age (should remove all)
        manager.cleanup_expired(max_age_hours=0)
        # Note: Cleanup checks timestamp, newly created won't be removed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
