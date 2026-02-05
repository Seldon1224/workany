"""Type definitions for Agent module."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Literal, Optional


class AgentProvider(str, Enum):
    """Agent provider types."""
    CLAUDE = "claude"


@dataclass
class AgentSession:
    """Agent session information."""
    id: str
    created_at: datetime
    phase: Literal["idle", "planning", "executing", "completed", "error"]
    is_aborted: bool = False


from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):
    """Conversation message for context."""
    role: Literal["user", "assistant"]
    content: str


class ImageAttachment(BaseModel):
    """Image attachment for agent input."""
    data: str = Field(..., description="Base64 encoded image data")
    mime_type: str = Field(..., alias="mimeType", description="MIME type of the image")
    
    class Config:
        populate_by_name = True  # Allow both mime_type and mimeType


class SandboxConfig(BaseModel):
    """Sandbox configuration."""
    enabled: bool = False
    provider: Optional[str] = None
    api_endpoint: Optional[str] = Field(None, alias="apiEndpoint")
    
    class Config:
        populate_by_name = True


class SkillsConfig(BaseModel):
    """Skills configuration."""
    enabled: bool = True
    sources: list[Literal["user", "project"]] = Field(default_factory=lambda: ["user"])


class McpConfig(BaseModel):
    """MCP configuration."""
    enabled: bool = True
    servers: dict[str, Any] = Field(default_factory=dict)



@dataclass
class AgentConfig:
    """Agent configuration."""
    provider: AgentProvider = AgentProvider.CLAUDE
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None


@dataclass
class AgentOptions:
    """Options for agent execution."""
    session_id: Optional[str] = None
    conversation: Optional[list[ConversationMessage]] = None
    cwd: Optional[str] = None
    task_id: Optional[str] = None
    sandbox: Optional[SandboxConfig] = None
    images: Optional[list[ImageAttachment]] = None
    skills_config: Optional[SkillsConfig] = None
    mcp_config: Optional[McpConfig] = None
    allowed_tools: Optional[list[str]] = None


# Agent message types
class AgentMessage(dict):
    """Base class for agent messages (SSE events)."""
    pass
