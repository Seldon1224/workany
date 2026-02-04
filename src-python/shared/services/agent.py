"""Agent service layer."""
from datetime import datetime
from typing import AsyncGenerator, Optional
from nanoid import generate

from core.agent import (
    create_agent,
    create_agent_from_env,
    IAgent,
    AgentConfig,
    AgentMessage,
    AgentOptions,
    AgentSession,
    ConversationMessage,
    ImageAttachment,
    McpConfig,
    SandboxConfig,
    SkillsConfig,
)
from shared.utils.logger import create_logger

logger = create_logger("AgentService")

# Global agent instance (lazy initialized)
_global_agent: Optional[IAgent] = None

# Active sessions
_active_sessions: dict[str, AgentSession] = {}


def get_agent(config: Optional[AgentConfig] = None) -> IAgent:
    """Get or create the global agent instance.
    
    Args:
        config: Optional agent configuration
    
    Returns:
        Agent instance
    """
    global _global_agent
    
    # If config with API credentials is provided, create a new agent instance
    if config and (config.api_key or config.base_url or config.model):
        logger.info("Creating new agent with custom config")
        return create_agent(config)
    
    # Use cached global agent for default configuration
    if not _global_agent:
        logger.info("Creating agent from environment variables")
        _global_agent = create_agent_from_env()
    
    return _global_agent


def create_session() -> AgentSession:
    """Create a new agent session.
    
    Returns:
        New agent session
    """
    session = AgentSession(
        id=generate(),
        created_at=datetime.now(),
        phase="executing",
        is_aborted=False,
    )
    _active_sessions[session.id] = session
    return session


def get_session(session_id: str) -> Optional[AgentSession]:
    """Get an existing session.
    
    Args:
        session_id: Session ID
    
    Returns:
        Session if found, None otherwise
    """
    return _active_sessions.get(session_id)


def delete_session(session_id: str) -> bool:
    """Delete a session.
    
    Args:
        session_id: Session ID
    
    Returns:
        True if session was deleted, False if not found
    """
    if session_id in _active_sessions:
        session = _active_sessions[session_id]
        session.is_aborted = True
        del _active_sessions[session_id]
        return True
    return False


async def run_agent(
    prompt: str,
    session: AgentSession,
    conversation: Optional[list[ConversationMessage]] = None,
    work_dir: Optional[str] = None,
    task_id: Optional[str] = None,
    model_config: Optional[dict] = None,
    sandbox_config: Optional[SandboxConfig] = None,
    images: Optional[list[ImageAttachment]] = None,
    skills_config: Optional[SkillsConfig] = None,
    mcp_config: Optional[McpConfig] = None,
) -> AsyncGenerator[AgentMessage, None]:
    """Run agent with the given prompt.
    
    Args:
        prompt: User prompt
        session: Agent session
        conversation: Optional conversation history
        work_dir: Optional working directory
        task_id: Optional task ID
        model_config: Optional model configuration
        sandbox_config: Optional sandbox configuration
        images: Optional image attachments
        skills_config: Optional skills configuration
        mcp_config: Optional MCP configuration
    
    Yields:
        Agent messages
    """
    # Build agent config from model_config
    agent_config = None
    if model_config:
        agent_config = AgentConfig(
            api_key=model_config.get("apiKey"),
            base_url=model_config.get("baseUrl"),
            model=model_config.get("model"),
        )
    
    agent = get_agent(agent_config)
    
    logger.info(f"Running agent with prompt: {prompt[:100]}...")
    logger.info(f"Sandbox config: {sandbox_config}")
    logger.info(f"Skills config: {skills_config}")
    logger.info(f"MCP config: {mcp_config}")
    
    # Build agent options
    options = AgentOptions(
        session_id=session.id,
        conversation=conversation,
        cwd=work_dir,
        task_id=task_id,
        sandbox=sandbox_config,
        images=images,
        skills_config=skills_config,
        mcp_config=mcp_config,
    )
    
    # Run agent and yield messages
    async for message in agent.run(prompt, options):
        yield message


def stop_agent(session_id: str) -> None:
    """Stop an agent execution.
    
    Args:
        session_id: Session ID to stop
    """
    session = _active_sessions.get(session_id)
    if session:
        session.is_aborted = True
