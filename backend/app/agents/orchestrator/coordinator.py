"""
Agent Orchestrator for FinFind.

Coordinates the multi-agent system, handling request routing,
agent lifecycle, and cross-agent communication.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from ..base import BaseAgent, AgentState, ConversationContext, ContextManager, get_context_manager
from ..config import AgentConfig, AgentType, get_config
from ..search_agent import SearchAgent
from ..recommendation_agent import RecommendationAgent
from ..explainability_agent import ExplainabilityAgent
from ..alternative_agent import AlternativeAgent
from .a2a_protocol import A2AProtocol, A2AMessage, A2AMessageType
from .workflow_executor import WorkflowExecutor, WorkflowResult
from .workflows import WorkflowType, get_workflow, list_workflows
from .message_bus import A2AMessageBus, A2AEventTypes, CompressedContext

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Central orchestrator for the FinFind agent system.
    
    Responsibilities:
    - Initialize and manage all agents
    - Route requests to appropriate agents
    - Coordinate multi-agent interactions
    - Manage conversation state
    - Handle A2A communication
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize the orchestrator.
        
        Args:
            config: Agent configuration. Uses global config if not provided.
        """
        self.config = config or get_config()
        self._agents: Dict[str, BaseAgent] = {}
        self._a2a = A2AProtocol(log_communications=self.config.a2a.log_communications)
        self._context_manager = get_context_manager()
        self._workflow_executor: Optional[WorkflowExecutor] = None
        self._message_bus: Optional[A2AMessageBus] = None
        self._initialized = False
    
    # ========================================
    # Initialization
    # ========================================
    
    def initialize(self):
        """Initialize all agents and register them for A2A communication."""
        if self._initialized:
            logger.warning("Orchestrator already initialized")
            return
        
        logger.info("Initializing FinFind Agent Orchestrator...")
        
        # Validate configuration
        errors = self.config.validate()
        if errors:
            for error in errors:
                logger.error(f"Config error: {error}")
            raise ValueError(f"Configuration errors: {errors}")
        
        # Create agents
        self._agents = {
            "SearchAgent": SearchAgent(self.config),
            "RecommendationAgent": RecommendationAgent(self.config),
            "ExplainabilityAgent": ExplainabilityAgent(self.config),
            "AlternativeAgent": AlternativeAgent(self.config)
        }
        
        # Register agents with A2A protocol
        for name, agent in self._agents.items():
            self._a2a.register_agent(name, agent)
        
        # Cross-register agents for direct delegation
        for name, agent in self._agents.items():
            for other_name, other_agent in self._agents.items():
                if name != other_name:
                    agent.register_agent(other_agent)
        
        # Initialize workflow executor
        self._workflow_executor = WorkflowExecutor(self._a2a, self._agents)
        
        # Initialize message bus
        self._message_bus = A2AMessageBus()
        for name, agent in self._agents.items():
            self._message_bus.register_agent(name, agent)
        
        self._initialized = True
        logger.info(f"Orchestrator initialized with {len(self._agents)} agents")
    
    def get_agent(self, agent_type: Union[str, AgentType]) -> Optional[BaseAgent]:
        """Get an agent by type or name."""
        if isinstance(agent_type, AgentType):
            name_map = {
                AgentType.SEARCH: "SearchAgent",
                AgentType.RECOMMENDATION: "RecommendationAgent",
                AgentType.EXPLAINABILITY: "ExplainabilityAgent",
                AgentType.ALTERNATIVE: "AlternativeAgent"
            }
            agent_name = name_map.get(agent_type)
        else:
            agent_name = agent_type
        
        return self._agents.get(agent_name)
    
    # ========================================
    # Request Routing
    # ========================================
    
    def _determine_agent(self, input_text: str, context: Optional[ConversationContext] = None) -> str:
        """
        Determine which agent should handle a request.
        
        Args:
            input_text: User input.
            context: Conversation context.
            
        Returns:
            Name of the agent to handle the request.
        """
        input_lower = input_text.lower()
        
        # Check for explicit agent hints
        if any(word in input_lower for word in ["recommend", "suggestion", "for me", "personalized"]):
            return "RecommendationAgent"
        
        if any(word in input_lower for word in ["why", "explain", "reason", "how come"]):
            return "ExplainabilityAgent"
        
        if any(word in input_lower for word in ["alternative", "instead", "cheaper", "similar to", "like"]):
            return "AlternativeAgent"
        
        if any(word in input_lower for word in ["search", "find", "looking for", "show me", "where"]):
            return "SearchAgent"
        
        # Check conversation stage
        if context:
            if context.stage.value in ["compare", "decide"]:
                return "ExplainabilityAgent"
            if context.products.recommended_products:
                return "RecommendationAgent"
        
        # Default to search
        return "SearchAgent"
    
    # ========================================
    # Main Interface
    # ========================================
    
    async def process_request(
        self,
        input_text: str,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Process a user request through the agent system.
        
        This is the main entry point for all requests.
        
        Args:
            input_text: User's input text.
            user_id: Optional user ID for personalization.
            conversation_id: Optional conversation ID for continuity.
            context: Optional additional context.
            
        Returns:
            Response dictionary with results.
        """
        if not self._initialized:
            self.initialize()
        
        start_time = datetime.utcnow()
        
        # Get or create conversation context
        conv_context = None
        if conversation_id:
            conv_context = self._context_manager.get_context(conversation_id)
        
        # If conversation doesn't exist or no ID provided, create a new one
        if conv_context is None:
            conv_context = self._context_manager.create_context(user_id=user_id)
        
        # Add user message
        conv_context.add_message("user", input_text)
        
        # Create agent state
        state = AgentState(
            input_text=input_text,
            context=conv_context
        )
        
        try:
            # Determine which agent should handle this
            agent_name = self._determine_agent(input_text, conv_context)
            agent = self._agents.get(agent_name)
            
            logger.info(f"Routing request to {agent_name}")
            
            # Run the primary agent
            state = await agent.run(input_text, state, conv_context)
            
            # Check if we need follow-up actions
            state = await self._handle_follow_up(state, conv_context)
            
            # Mark complete
            state.mark_complete()
            
            # Build response
            response = {
                "success": True,
                "conversation_id": conv_context.conversation_id,
                "output": state.output_text,
                "products": state.output_products,
                "explanations": state.output_explanations,
                "agents_used": state.agent_chain,
                "execution_time_ms": state.execution_time_ms,
                "errors": state.errors,
                "warnings": state.warnings
            }
            
        except Exception as e:
            logger.exception(f"Error processing request: {e}")
            response = {
                "success": False,
                "conversation_id": conv_context.conversation_id,
                "error": str(e),
                "output": "I'm sorry, something went wrong. Please try again.",
                "products": [],
                "agents_used": state.agent_chain if state else []
            }
        
        return response
    
    def process_request_sync(
        self,
        input_text: str,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Synchronous version of process_request()."""
        if not self._initialized:
            self.initialize()
        
        # Get or create conversation context
        if conversation_id:
            conv_context = self._context_manager.get_context(conversation_id)
        else:
            conv_context = self._context_manager.create_context(user_id=user_id)
        
        conv_context.add_message("user", input_text)
        
        state = AgentState(
            input_text=input_text,
            context=conv_context
        )
        
        try:
            agent_name = self._determine_agent(input_text, conv_context)
            agent = self._agents.get(agent_name)
            
            state = agent.run_sync(input_text, state, conv_context)
            state.mark_complete()
            
            return {
                "success": True,
                "conversation_id": conv_context.conversation_id,
                "output": state.output_text,
                "products": state.output_products,
                "agents_used": state.agent_chain,
                "errors": state.errors
            }
            
        except Exception as e:
            logger.exception(f"Error: {e}")
            return {
                "success": False,
                "error": str(e),
                "output": "Something went wrong."
            }
    
    async def _handle_follow_up(
        self,
        state: AgentState,
        context: ConversationContext
    ) -> AgentState:
        """
        Handle follow-up actions after primary agent completes.
        
        May delegate to other agents based on results.
        """
        # Check if we need alternatives (budget exceeded)
        if state.output_products:
            budget_max = context.user.financial.budget_max
            if budget_max:
                over_budget = [
                    p for p in state.output_products
                    if p.get('price', 0) > budget_max
                ]
                if len(over_budget) == len(state.output_products):
                    # All results over budget - get alternatives
                    logger.info("All results over budget, delegating to AlternativeAgent")
                    alt_agent = self._agents.get("AlternativeAgent")
                    if alt_agent:
                        response = await self._a2a.delegate_task(
                            sender=state.current_agent or "Orchestrator",
                            recipient="AlternativeAgent",
                            task=f"Find budget-friendly alternatives under ${budget_max}",
                            context={"products": state.output_products[:3]}
                        )
                        if response.success and response.result:
                            state.add_warning("Original results exceeded budget. Showing alternatives.")
        
        return state
    
    # ========================================
    # Workflow Execution
    # ========================================
    
    async def execute_workflow(
        self,
        workflow_id: str,
        query: str,
        user_id: Optional[str] = None,
        budget_max: Optional[float] = None,
        additional_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Execute a predefined workflow.
        
        Args:
            workflow_id: ID of the workflow (search_recommend, recommend_explain, etc.)
            query: User query
            user_id: Optional user ID
            budget_max: Optional budget constraint
            additional_context: Any additional context
            
        Returns:
            Workflow result as dictionary
        """
        if not self._initialized:
            self.initialize()
        
        # Build context
        context = {
            "query": query,
            "input_text": query,
            "user_id": user_id or "anonymous",
            "budget_max": budget_max,
            "max_price": budget_max,
        }
        if additional_context:
            context.update(additional_context)
        
        # Get conversation context
        conv_context = self._context_manager.create_context(user_id=user_id)
        if budget_max:
            conv_context.user.financial.budget_max = budget_max
        
        # Execute workflow
        result = await self._workflow_executor.execute_workflow(
            workflow_id,
            context,
            conv_context
        )
        
        return {
            "success": result.success,
            "conversation_id": conv_context.conversation_id,
            "output": result.output,
            "products": result.products,
            "explanations": result.explanations,
            "alternatives": result.alternatives,
            "agents_used": result.agents_used,
            "execution_time_ms": result.execution_time_ms,
            "workflow_id": workflow_id,
            "execution_id": result.execution_id,
            "errors": result.errors,
            "warnings": result.warnings
        }
    
    async def search_and_personalize(
        self,
        query: str,
        user_id: Optional[str] = None,
        budget_max: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Execute Search → Recommendation workflow.
        
        1. SearchAgent finds matching products
        2. RecommendationAgent personalizes based on user profile
        """
        return await self.execute_workflow(
            "search_recommend",
            query,
            user_id=user_id,
            budget_max=budget_max
        )
    
    async def recommend_with_explanation(
        self,
        user_id: str,
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute Recommendation → Explainability workflow.
        
        1. RecommendationAgent gets personalized recommendations
        2. ExplainabilityAgent explains why each was recommended
        """
        return await self.execute_workflow(
            "recommend_explain",
            query or "Get my personalized recommendations",
            user_id=user_id
        )
    
    async def search_with_budget_fallback(
        self,
        query: str,
        budget_max: float,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute Search → Alternative workflow.
        
        1. SearchAgent searches for products
        2. If all results exceed budget, AlternativeAgent finds alternatives
        """
        return await self.execute_workflow(
            "search_alternative",
            query,
            user_id=user_id,
            budget_max=budget_max
        )
    
    async def full_discovery_pipeline(
        self,
        query: str,
        user_id: str,
        budget_max: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Execute full multi-agent pipeline.
        
        1. SearchAgent searches
        2. RecommendationAgent personalizes
        3. ExplainabilityAgent adds explanations
        4. AlternativeAgent prepares fallbacks (if needed)
        """
        return await self.execute_workflow(
            "full_pipeline",
            query,
            user_id=user_id,
            budget_max=budget_max
        )
    
    def list_available_workflows(self) -> List[Dict[str, Any]]:
        """List all available workflows."""
        return list_workflows()
    
    # ========================================
    # Specialized Workflows
    # ========================================
    
    async def search(
        self,
        query: str,
        user_id: Optional[str] = None,
        category: Optional[str] = None,
        max_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Direct search workflow.
        
        Bypasses routing and goes directly to SearchAgent.
        """
        if not self._initialized:
            self.initialize()
        
        search_agent: SearchAgent = self._agents.get("SearchAgent")
        
        context = self._context_manager.create_context(user_id=user_id)
        if max_price:
            context.user.financial.budget_max = max_price
        
        state = await search_agent.search(
            query=query,
            context=context,
            category=category,
            max_price=max_price
        )
        
        return {
            "success": True,
            "query": query,
            "products": state.output_products,
            "output": state.output_text,
            "conversation_id": context.conversation_id
        }
    
    async def recommend(
        self,
        user_id: str,
        category: Optional[str] = None,
        num_recommendations: int = 5
    ) -> Dict[str, Any]:
        """
        Direct recommendation workflow.
        
        Bypasses routing and goes directly to RecommendationAgent.
        """
        if not self._initialized:
            self.initialize()
        
        rec_agent: RecommendationAgent = self._agents.get("RecommendationAgent")
        
        result = rec_agent.get_recommendations(
            user_id=user_id,
            category=category,
            num_recommendations=num_recommendations
        )
        
        return result
    
    async def explain(
        self,
        product: Dict,
        user_id: Optional[str] = None,
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Direct explanation workflow.
        """
        if not self._initialized:
            self.initialize()
        
        exp_agent: ExplainabilityAgent = self._agents.get("ExplainabilityAgent")
        
        # Get user profile if user_id provided
        user_profile = None
        if user_id:
            from ..tools import GetUserProfileTool
            profile_tool = GetUserProfileTool()
            profile_result = profile_tool._run(user_id=user_id)
            if profile_result.get('success'):
                user_profile = profile_result['profile']
        
        result = exp_agent.get_explanation(
            product=product,
            user_profile=user_profile,
            query=query
        )
        
        return result
    
    async def find_alternatives(
        self,
        product: Dict,
        user_budget: float,
        num_alternatives: int = 3
    ) -> Dict[str, Any]:
        """
        Direct alternative finding workflow.
        """
        if not self._initialized:
            self.initialize()
        
        alt_agent: AlternativeAgent = self._agents.get("AlternativeAgent")
        
        result = alt_agent.get_budget_alternatives(
            product=product,
            user_budget=user_budget,
            num_alternatives=num_alternatives
        )
        
        return result
    
    # ========================================
    # A2A Interface
    # ========================================
    
    @property
    def a2a(self) -> A2AProtocol:
        """Access the A2A protocol handler."""
        return self._a2a
    
    async def delegate(
        self,
        from_agent: str,
        to_agent: str,
        task: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Delegate a task between agents.
        
        Args:
            from_agent: Sending agent name.
            to_agent: Receiving agent name.
            task: Task description.
            context: Optional context to share.
            
        Returns:
            Delegation result.
        """
        response = await self._a2a.delegate_task(
            sender=from_agent,
            recipient=to_agent,
            task=task,
            context=context
        )
        
        return response.to_dict()
    
    # ========================================
    # Status and Debugging
    # ========================================
    
    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status."""
        return {
            "initialized": self._initialized,
            "agents": {
                name: agent.get_agent_info()
                for name, agent in self._agents.items()
            },
            "config": self.config.to_dict(),
            "a2a_agents": self._a2a.list_agents(),
            "pending_tasks": len(self._a2a.get_pending_tasks()),
            "available_workflows": self.list_available_workflows(),
            "active_workflow_executions": (
                self._workflow_executor.get_active_executions()
                if self._workflow_executor else []
            )
        }
    
    def get_conversation_history(
        self,
        conversation_id: str
    ) -> Optional[Dict]:
        """Get conversation history."""
        context = self._context_manager.get_context(conversation_id)
        if context:
            return context.to_dict()
        return None


# Global orchestrator instance
_orchestrator: Optional[AgentOrchestrator] = None


def get_orchestrator() -> AgentOrchestrator:
    """Get or create the global orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
        _orchestrator.initialize()
    return _orchestrator
