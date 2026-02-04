"""Agent core module."""
from .base import IAgent
from .claude import ClaudeAgent
from .types import (
    AgentConfig,
    AgentMessage,
    AgentOptions,
    AgentProvider,
    AgentSession,
    ConversationMessage,
    ImageAttachment,
    McpConfig,
    SandboxConfig,
    SkillsConfig,
)


def create_agent(config: AgentConfig) -> IAgent:
    """Create an agent instance based on configuration.
    
    Args:
        config: Agent configuration
    
    Returns:
        Agent instance
    
    Raises:
        ValueError: If provider is not supported
    """
    if config.provider == AgentProvider.CLAUDE:
        return ClaudeAgent(config)
    else:
        raise ValueError(f"Unsupported agent provider: {config.provider}")


def create_agent_from_env() -> IAgent:
    """Create an agent instance from environment variables.
    
    Returns:
        Agent instance configured from environment
    """
    config = AgentConfig(
        provider=AgentProvider.CLAUDE,
        api_key=None,  # Will use ANTHROPIC_API_KEY from env
        base_url=None,
        model=None,
    )
    return create_agent(config)


__all__ = [
    "IAgent",
    "ClaudeAgent",
    "create_agent",
    "create_agent_from_env",
    "AgentConfig",
    "AgentMessage",
    "AgentOptions",
    "AgentProvider",
    "AgentSession",
    "ConversationMessage",
    "ImageAttachment",
    "McpConfig",
    "SandboxConfig",
    "SkillsConfig",
]
