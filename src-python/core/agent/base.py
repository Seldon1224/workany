"""Base Agent implementation."""
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional

from shared.types.agent import AgentConfig, AgentMessage, AgentOptions, AgentProvider


class IAgent(ABC):
    """Abstract base class for agent implementations."""
    
    def __init__(self, config: AgentConfig):
        """Initialize agent with configuration.
        
        Args:
            config: Agent configuration
        """
        self.config = config
    
    @property
    @abstractmethod
    def provider(self) -> AgentProvider:
        """Get the provider type."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the human-readable name."""
        pass
    
    @abstractmethod
    async def run(
        self,
        prompt: str,
        options: Optional[AgentOptions] = None
    ) -> AsyncGenerator[AgentMessage, None]:
        """Run the agent with the given prompt.
        
        Args:
            prompt: User prompt
            options: Optional execution options
        
        Yields:
            Agent messages (SSE events)
        """
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the agent is available.
        
        Returns:
            True if agent is available, False otherwise
        """
        pass
