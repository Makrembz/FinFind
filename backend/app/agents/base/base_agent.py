"""
Base Agent Class for FinFind.

Provides the foundation for all specialized agents with common
functionality for LLM interaction, tool execution, and state management.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable, Type
from datetime import datetime

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import BaseTool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_groq import ChatGroq

from .agent_state import AgentState, ConversationContext
from ..config import AgentConfig, get_config, AgentType

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all FinFind agents.
    
    Provides:
    - LLM initialization (Groq)
    - Tool management
    - Agent execution with LangChain
    - State management
    - A2A communication hooks
    """
    
    # Class attributes to be set by subclasses
    agent_type: AgentType
    agent_name: str
    agent_description: str
    
    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        tools: Optional[List[BaseTool]] = None
    ):
        """
        Initialize the base agent.
        
        Args:
            config: Agent configuration. Uses global config if not provided.
            tools: List of tools for this agent. If not provided, uses default tools.
        """
        self.config = config or get_config()
        self._llm: Optional[BaseChatModel] = None
        self._tools: List[BaseTool] = tools or []
        self._agent_executor: Optional[AgentExecutor] = None
        self._other_agents: Dict[str, 'BaseAgent'] = {}
        
        # Initialize tools if not provided
        if not self._tools:
            self._tools = self._create_default_tools()
    
    # ========================================
    # LLM Management
    # ========================================
    
    def _create_llm(self) -> BaseChatModel:
        """Create the LLM instance (Groq)."""
        return ChatGroq(
            model=self.config.llm.model,
            api_key=self.config.llm.api_key,
            temperature=self.config.llm.temperature,
            max_tokens=self.config.llm.max_tokens,
            timeout=self.config.llm.timeout,
            max_retries=self.config.llm.max_retries,
        )
    
    @property
    def llm(self) -> BaseChatModel:
        """Get or create the LLM instance."""
        if self._llm is None:
            self._llm = self._create_llm()
        return self._llm
    
    # ========================================
    # Tool Management
    # ========================================
    
    @abstractmethod
    def _create_default_tools(self) -> List[BaseTool]:
        """
        Create the default tools for this agent.
        
        Must be implemented by subclasses.
        
        Returns:
            List of BaseTool instances.
        """
        pass
    
    def add_tool(self, tool: BaseTool):
        """Add a tool to this agent."""
        self._tools.append(tool)
        # Reset executor to include new tool
        self._agent_executor = None
    
    def get_tools(self) -> List[BaseTool]:
        """Get all tools for this agent."""
        return self._tools
    
    def get_tool_names(self) -> List[str]:
        """Get names of all tools."""
        return [tool.name for tool in self._tools]
    
    # ========================================
    # Agent Executor
    # ========================================
    
    @abstractmethod
    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for this agent.
        
        Must be implemented by subclasses.
        
        Returns:
            System prompt string.
        """
        pass
    
    def _create_prompt_template(self) -> ChatPromptTemplate:
        """Create the prompt template for the agent."""
        return ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
    
    def _create_agent_executor(self) -> AgentExecutor:
        """Create the LangChain agent executor."""
        prompt = self._create_prompt_template()
        
        # Create the tool-calling agent
        agent = create_tool_calling_agent(
            llm=self.llm,
            tools=self._tools,
            prompt=prompt
        )
        
        # Create executor with error handling
        return AgentExecutor(
            agent=agent,
            tools=self._tools,
            verbose=self.config.debug,
            handle_parsing_errors=True,
            max_iterations=10,
            return_intermediate_steps=True
        )
    
    @property
    def executor(self) -> AgentExecutor:
        """Get or create the agent executor."""
        if self._agent_executor is None:
            self._agent_executor = self._create_agent_executor()
        return self._agent_executor
    
    # ========================================
    # Agent Execution
    # ========================================
    
    async def run(
        self,
        input_text: str,
        state: Optional[AgentState] = None,
        context: Optional[ConversationContext] = None
    ) -> AgentState:
        """
        Run the agent on the given input.
        
        Args:
            input_text: The user input or delegated task.
            state: Optional existing state to continue from.
            context: Optional conversation context.
            
        Returns:
            Updated AgentState with results.
        """
        # Create or update state
        if state is None:
            state = AgentState(input_text=input_text)
            if context:
                state.context = context
        
        state.current_agent = self.agent_name
        state.agent_chain.append(self.agent_name)
        
        logger.info(f"[{self.agent_name}] Running with input: {input_text[:100]}...")
        
        try:
            # Prepare input for executor
            executor_input = self._prepare_executor_input(input_text, state)
            
            # Run the agent
            result = await self.executor.ainvoke(executor_input)
            
            # Process result
            state = self._process_result(result, state)
            
            logger.info(f"[{self.agent_name}] Completed successfully")
            
        except Exception as e:
            logger.exception(f"[{self.agent_name}] Error: {e}")
            state.add_error(f"{self.agent_name}: {str(e)}")
        
        return state
    
    def run_sync(
        self,
        input_text: str,
        state: Optional[AgentState] = None,
        context: Optional[ConversationContext] = None
    ) -> AgentState:
        """Synchronous version of run()."""
        # Create or update state
        if state is None:
            state = AgentState(input_text=input_text)
            if context:
                state.context = context
        
        state.current_agent = self.agent_name
        state.agent_chain.append(self.agent_name)
        
        logger.info(f"[{self.agent_name}] Running with input: {input_text[:100]}...")
        
        try:
            # Prepare input for executor
            executor_input = self._prepare_executor_input(input_text, state)
            
            # Run the agent
            result = self.executor.invoke(executor_input)
            
            # Process result
            state = self._process_result(result, state)
            
            logger.info(f"[{self.agent_name}] Completed successfully")
            
        except Exception as e:
            logger.exception(f"[{self.agent_name}] Error: {e}")
            state.add_error(f"{self.agent_name}: {str(e)}")
        
        return state
    
    def _prepare_executor_input(
        self,
        input_text: str,
        state: AgentState
    ) -> Dict[str, Any]:
        """Prepare input dictionary for the executor."""
        # Build chat history from context
        chat_history = []
        if state.context and state.context.messages:
            for msg in state.context.get_recent_messages(10):
                if msg["role"] == "user":
                    chat_history.append(HumanMessage(content=msg["content"]))
                else:
                    chat_history.append(AIMessage(content=msg["content"]))
        
        return {
            "input": input_text,
            "chat_history": chat_history
        }
    
    def _process_result(
        self,
        result: Dict[str, Any],
        state: AgentState
    ) -> AgentState:
        """Process the executor result and update state."""
        # Extract output
        output = result.get("output", "")
        state.output_text = output
        
        # Store intermediate steps
        intermediate_steps = result.get("intermediate_steps", [])
        for action, observation in intermediate_steps:
            state.add_result(self.agent_name, {
                "tool": action.tool,
                "input": str(action.tool_input)[:200],
                "output": str(observation)[:500]
            })
        
        # Add message to context
        if state.context:
            state.context.add_message("assistant", output, self.agent_name)
        
        return state
    
    # ========================================
    # A2A Communication
    # ========================================
    
    def register_agent(self, agent: 'BaseAgent'):
        """Register another agent for A2A communication."""
        self._other_agents[agent.agent_name] = agent
    
    async def delegate_to(
        self,
        agent_name: str,
        task: str,
        state: AgentState
    ) -> AgentState:
        """
        Delegate a task to another agent.
        
        Args:
            agent_name: Name of the agent to delegate to.
            task: The task description.
            state: Current agent state.
            
        Returns:
            Updated state from the delegated agent.
        """
        if agent_name not in self._other_agents:
            state.add_error(f"Agent '{agent_name}' not registered")
            return state
        
        # Check delegation depth
        if state.delegation_depth >= self.config.a2a.max_delegation_depth:
            state.add_warning(f"Max delegation depth reached, cannot delegate to {agent_name}")
            return state
        
        logger.info(f"[{self.agent_name}] Delegating to {agent_name}: {task[:50]}...")
        
        # Increment delegation depth
        state.delegation_depth += 1
        
        # Run delegated agent
        other_agent = self._other_agents[agent_name]
        state = await other_agent.run(task, state)
        
        return state
    
    # ========================================
    # Utility Methods
    # ========================================
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about this agent."""
        return {
            "name": self.agent_name,
            "type": self.agent_type.value,
            "description": self.agent_description,
            "tools": self.get_tool_names(),
            "llm_model": self.config.llm.model
        }
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.agent_name}>"
