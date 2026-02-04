"""Provider type definitions.

This module defines the base types and interfaces for the extensible provider system.
Used by both Sandbox and Agent providers.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Literal, Optional, Protocol

# ============================================================================
# Provider States
# ============================================================================


class ProviderState(str, Enum):
    """Provider state enumeration."""

    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    ERROR = "error"
    STOPPING = "stopping"
    STOPPED = "stopped"


# ============================================================================
# Provider Events
# ============================================================================


class ProviderEventType(str, Enum):
    """Provider event type enumeration."""

    REGISTERED = "registered"
    UNREGISTERED = "unregistered"
    INITIALIZED = "initialized"
    STARTED = "started"
    STOPPED = "stopped"
    ERROR = "error"
    STATE_CHANGED = "state_changed"
    PROVIDER_REGISTERED = "provider:registered"
    PROVIDER_UNREGISTERED = "provider:unregistered"
    PROVIDER_INITIALIZED = "provider:initialized"
    PROVIDER_STARTED = "provider:started"
    PROVIDER_STOPPED = "provider:stopped"
    PROVIDER_ERROR = "provider:error"
    PROVIDER_SWITCHED = "provider:switched"


class ProviderEvent:
    """Provider event."""

    def __init__(
        self,
        type: str,
        provider_type: str,
        timestamp: Optional[datetime] = None,
        data: Optional[Any] = None,
        error: Optional[Exception] = None,
    ):
        """Initialize provider event.

        Args:
            type: Event type
            provider_type: Provider type identifier
            timestamp: Event timestamp (defaults to now)
            data: Optional event data
            error: Optional error
        """
        self.type = type
        self.provider_type = provider_type
        self.timestamp = timestamp or datetime.now()
        self.data = data
        self.error = error


ProviderEventListener = Callable[[ProviderEvent], None]


# ============================================================================
# Provider Capabilities
# ============================================================================


class ProviderCapabilities(Dict[str, Any]):
    """Provider capabilities dictionary."""

    pass


# ============================================================================
# Provider Metadata
# ============================================================================


class ProviderMetadata:
    """Provider metadata."""

    def __init__(
        self,
        type: str,
        name: str,
        description: Optional[str] = None,
        version: Optional[str] = None,
        capabilities: Optional[ProviderCapabilities] = None,
        config_schema: Optional[Dict[str, Any]] = None,
    ):
        """Initialize provider metadata.

        Args:
            type: Unique type identifier
            name: Human-readable name
            description: Description of the provider
            version: Version string
            capabilities: Provider capabilities
            config_schema: Configuration schema for validation
        """
        self.type = type
        self.name = name
        self.description = description
        self.version = version
        self.capabilities = capabilities or {}
        self.config_schema = config_schema or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "type": self.type,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "capabilities": self.capabilities,
            "configSchema": self.config_schema,
        }


# ============================================================================
# Provider Configuration
# ============================================================================


class ProviderConfig:
    """Provider configuration."""

    def __init__(
        self,
        type: str,
        name: str,
        enabled: bool = True,
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize provider configuration.

        Args:
            type: Provider type identifier
            name: Human-readable name
            enabled: Whether this provider is enabled
            config: Provider-specific configuration
        """
        self.type = type
        self.name = name
        self.enabled = enabled
        self.config = config or {}


class ProviderSelectionConfig:
    """Provider selection configuration."""

    def __init__(
        self,
        category: Literal["sandbox", "agent"],
        type: str,
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize provider selection configuration.

        Args:
            category: Category of provider
            type: Provider type identifier
            config: Provider-specific configuration
        """
        self.category = category
        self.type = type
        self.config = config or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "category": self.category,
            "type": self.type,
            "config": self.config,
        }


class ProvidersConfig:
    """Providers configuration."""

    def __init__(
        self,
        sandbox: Optional[ProviderSelectionConfig] = None,
        agent: Optional[ProviderSelectionConfig] = None,
    ):
        """Initialize providers configuration.

        Args:
            sandbox: Current sandbox provider selection
            agent: Current agent provider selection
        """
        self.sandbox = sandbox
        self.agent = agent

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        result: Dict[str, Any] = {}
        if self.sandbox:
            result["sandbox"] = self.sandbox.to_dict()
        if self.agent:
            result["agent"] = self.agent.to_dict()
        return result


# ============================================================================
# Base Provider Interface
# ============================================================================


class IProvider(Protocol):
    """Base interface for all providers (Sandbox, Agent, etc.)."""

    @property
    def type(self) -> str:
        """Provider type identifier."""
        ...

    @property
    def name(self) -> str:
        """Human-readable provider name."""
        ...

    async def is_available(self) -> bool:
        """Check if this provider is available on the current platform.

        Returns:
            True if available, False otherwise
        """
        ...

    async def init(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the provider with optional configuration.

        Args:
            config: Optional configuration dictionary
        """
        ...

    async def stop(self) -> None:
        """Stop and cleanup the provider."""
        ...

    async def shutdown(self) -> None:
        """Shutdown the provider (alias for stop)."""
        ...

    def get_capabilities(self) -> ProviderCapabilities:
        """Get the capabilities of this provider.

        Returns:
            Provider capabilities
        """
        ...


# ============================================================================
# Provider Instance
# ============================================================================


class ProviderInstance:
    """Provider instance wrapper."""

    def __init__(
        self,
        provider: IProvider,
        state: ProviderState = ProviderState.UNINITIALIZED,
        config: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None,
    ):
        """Initialize provider instance.

        Args:
            provider: Provider instance
            state: Current state
            config: Configuration used to create this instance
            error: Error if state is 'error'
        """
        self.provider = provider
        self.state = state
        self.config = config
        self.error = error
        self.created_at = datetime.now()
        self.last_used_at = datetime.now()
