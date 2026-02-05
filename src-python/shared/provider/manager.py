"""Provider Manager.

Manages provider lifecycle, switching, and configuration.
Provides a unified interface for accessing sandbox and agent providers.
"""

import os
from typing import Any, Dict, List, Optional, Set

from shared.provider.types import (
    IProvider,
    ProviderEvent,
    ProviderEventListener,
    ProviderMetadata,
    ProviderSelectionConfig,
    ProvidersConfig,
)
from shared.utils.logger import create_logger

logger = create_logger("ProviderManager")


# ============================================================================
# Provider Registry Protocol
# ============================================================================


class IProviderRegistry:
    """Interface for provider registries."""

    async def get_available(self) -> List[str]:
        """Get available provider types.

        Returns:
            List of available provider types
        """
        raise NotImplementedError

    def get_all_metadata(self) -> List[ProviderMetadata]:
        """Get metadata for all registered providers.

        Returns:
            List of provider metadata
        """
        raise NotImplementedError

    async def get_instance(
        self, type: str, config: Optional[Dict[str, Any]] = None
    ) -> IProvider:
        """Get a provider instance.

        Args:
            type: Provider type
            config: Optional configuration

        Returns:
            Provider instance
        """
        raise NotImplementedError

    async def stop_all(self) -> None:
        """Stop all provider instances."""
        raise NotImplementedError


# ============================================================================
# Provider Manager
# ============================================================================


class ProviderManager:
    """Centralized manager for all provider types."""

    def __init__(self):
        """Initialize provider manager."""
        self._config = ProvidersConfig()
        self._listeners: Set[ProviderEventListener] = set()
        self._registries: Dict[str, IProviderRegistry] = {}
        self._active_providers: Dict[str, IProvider] = {}

    # ========================================================================
    # Registry Management
    # ========================================================================

    def register_registry(self, category: str, registry: IProviderRegistry) -> None:
        """Register a provider registry for a category.

        Args:
            category: Provider category (e.g., 'sandbox', 'agent')
            registry: Provider registry instance
        """
        self._registries[category] = registry
        logger.info(f"Registered registry for category: {category}")

    # ========================================================================
    # Provider Access
    # ========================================================================

    async def get_sandbox_provider(self) -> Optional[IProvider]:
        """Get the current sandbox provider.

        Returns:
            Sandbox provider instance or None
        """
        registry = self._registries.get("sandbox")
        if not registry:
            logger.warning("No sandbox registry registered")
            return None

        selection = self._config.sandbox
        if not selection:
            # Use first available
            available = await registry.get_available()
            if not available:
                return None
            return await registry.get_instance(available[0])

        return await registry.get_instance(selection.type, selection.config)

    async def get_agent_provider(self) -> Optional[IProvider]:
        """Get the current agent provider.

        Returns:
            Agent provider instance or None
        """
        registry = self._registries.get("agent")
        if not registry:
            logger.warning("No agent registry registered")
            return None

        selection = self._config.agent
        if not selection:
            # Use first available
            available = await registry.get_available()
            if not available:
                return None
            return await registry.get_instance(available[0])

        return await registry.get_instance(selection.type, selection.config)

    async def get_provider(self, category: str) -> Optional[IProvider]:
        """Get provider by category.

        Args:
            category: Provider category

        Returns:
            Provider instance or None
        """
        registry = self._registries.get(category)
        if not registry:
            logger.warning(f"No registry for category: {category}")
            return None

        selection = getattr(self._config, category, None)
        if not selection:
            available = await registry.get_available()
            if not available:
                return None
            return await registry.get_instance(available[0])

        return await registry.get_instance(selection.type, selection.config)

    # ========================================================================
    # Provider Switching
    # ========================================================================

    async def switch_sandbox_provider(
        self, type: str, config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Switch sandbox provider.

        Args:
            type: Provider type
            config: Optional configuration
        """
        registry = self._registries.get("sandbox")
        
        # Update config first
        self._config.sandbox = ProviderSelectionConfig(
            category="sandbox", type=type, config=config
        )
        
        # If no registry, just update config and return
        if not registry:
            logger.warning("No sandbox registry registered, only updating configuration")
            self._emit(
                ProviderEvent(
                    type="provider:switched",
                    provider_type=type,
                    data={"category": "sandbox", "config_only": True},
                )
            )
            logger.info(f"Updated sandbox provider config to: {type}")
            return

        # Stop current instance if exists
        current = self._active_providers.get("sandbox")
        if current:
            await current.shutdown()
            del self._active_providers["sandbox"]

        # Create and activate new provider
        provider = await registry.get_instance(type, config)
        self._active_providers["sandbox"] = provider

        self._emit(
            ProviderEvent(
                type="provider:switched",
                provider_type=type,
                data={"category": "sandbox"},
            )
        )

        logger.info(f"Switched sandbox provider to: {type}")

    async def switch_agent_provider(
        self, type: str, config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Switch agent provider.

        Args:
            type: Provider type
            config: Optional configuration
        """
        registry = self._registries.get("agent")
        
        # Update config first
        self._config.agent = ProviderSelectionConfig(
            category="agent", type=type, config=config
        )
        
        # If no registry, just update config and return
        if not registry:
            logger.warning("No agent registry registered, only updating configuration")
            self._emit(
                ProviderEvent(
                    type="provider:switched",
                    provider_type=type,
                    data={"category": "agent", "config_only": True},
                )
            )
            logger.info(f"Updated agent provider config to: {type}")
            return

        # Stop current instance if exists
        current = self._active_providers.get("agent")
        if current:
            await current.shutdown()
            del self._active_providers["agent"]

        # Create and activate new provider
        provider = await registry.get_instance(type, config)
        self._active_providers["agent"] = provider

        self._emit(
            ProviderEvent(
                type="provider:switched",
                provider_type=type,
                data={"category": "agent"},
            )
        )

        logger.info(f"Switched agent provider to: {type}")

    # ========================================================================
    # Configuration
    # ========================================================================

    def get_config(self) -> ProvidersConfig:
        """Get current configuration.

        Returns:
            Providers configuration
        """
        return self._config

    def set_config(self, config: ProvidersConfig) -> None:
        """Set configuration.

        Args:
            config: Providers configuration
        """
        self._config = config
        logger.info("Configuration updated")

    def update_from_settings(self, settings: Dict[str, Any]) -> None:
        """Update configuration from settings.

        Args:
            settings: Settings dictionary
        """
        if "sandboxProvider" in settings:
            self._config.sandbox = ProviderSelectionConfig(
                category="sandbox",
                type=settings["sandboxProvider"],
                config=settings.get("sandboxConfig"),
            )

        if "agentProvider" in settings:
            self._config.agent = ProviderSelectionConfig(
                category="agent",
                type=settings["agentProvider"],
                config=settings.get("agentConfig"),
            )

    # ========================================================================
    # Metadata
    # ========================================================================

    def get_sandbox_providers_metadata(self) -> List[ProviderMetadata]:
        """Get all sandbox provider metadata.

        Returns:
            List of sandbox provider metadata
        """
        registry = self._registries.get("sandbox")
        return registry.get_all_metadata() if registry else []

    def get_agent_providers_metadata(self) -> List[ProviderMetadata]:
        """Get all agent provider metadata.

        Returns:
            List of agent provider metadata
        """
        registry = self._registries.get("agent")
        return registry.get_all_metadata() if registry else []

    async def get_available_sandbox_providers(self) -> List[str]:
        """Get available sandbox providers.

        Returns:
            List of available sandbox provider types
        """
        registry = self._registries.get("sandbox")
        return await registry.get_available() if registry else []

    async def get_available_agent_providers(self) -> List[str]:
        """Get available agent providers.

        Returns:
            List of available agent provider types
        """
        registry = self._registries.get("agent")
        return await registry.get_available() if registry else []

    # ========================================================================
    # Lifecycle
    # ========================================================================

    async def initialize(self) -> None:
        """Initialize all registries and load default providers."""
        logger.info("Initializing...")

        # Load default configuration from environment if not set
        if not self._config.sandbox:
            sandbox_type = os.getenv("SANDBOX_PROVIDER", "codex")
            self._config.sandbox = ProviderSelectionConfig(
                category="sandbox", type=sandbox_type
            )

        if not self._config.agent:
            agent_type = os.getenv("AGENT_PROVIDER", "claude")
            # Load agent configuration from environment variables
            agent_config = {}
            if agent_type == "claude":
                # Load Anthropic/Claude configuration
                api_key = os.getenv("ANTHROPIC_API_KEY")
                base_url = os.getenv("ANTHROPIC_BASE_URL")
                model = os.getenv("ANTHROPIC_MODEL")
                
                if api_key:
                    agent_config["apiKey"] = api_key
                if base_url:
                    agent_config["baseUrl"] = base_url
                if model:
                    agent_config["model"] = model
            
            self._config.agent = ProviderSelectionConfig(
                category="agent", 
                type=agent_type,
                config=agent_config if agent_config else None
            )

        logger.info(f"Initialized with config: {self._config.to_dict()}")

    async def shutdown(self) -> None:
        """Shutdown all active providers."""
        logger.info("Shutting down...")

        # Stop all active providers
        for category, provider in list(self._active_providers.items()):
            try:
                await provider.shutdown()
                logger.info(f"Stopped {category} provider")
            except Exception as e:
                logger.warning(f"Error stopping {category} provider: {e}")

        self._active_providers.clear()

        # Stop all registries
        for category, registry in self._registries.items():
            try:
                await registry.stop_all()
                logger.info(f"Stopped all {category} providers")
            except Exception as e:
                logger.warning(f"Error stopping {category} registry: {e}")

        logger.info("Shutdown complete")

    # ========================================================================
    # Events
    # ========================================================================

    def on(self, listener: ProviderEventListener) -> None:
        """Add an event listener.

        Args:
            listener: Event listener function
        """
        self._listeners.add(listener)

    def off(self, listener: ProviderEventListener) -> None:
        """Remove an event listener.

        Args:
            listener: Event listener function
        """
        self._listeners.discard(listener)

    def _emit(self, event: ProviderEvent) -> None:
        """Emit an event.

        Args:
            event: Provider event
        """
        for listener in self._listeners:
            try:
                listener(event)
            except Exception as e:
                logger.error(f"Error in event listener: {e}")


# ============================================================================
# Singleton Instance
# ============================================================================

_provider_manager: Optional[ProviderManager] = None


def get_provider_manager() -> ProviderManager:
    """Get the global provider manager instance.

    Returns:
        Provider manager instance
    """
    global _provider_manager
    if _provider_manager is None:
        _provider_manager = ProviderManager()
    return _provider_manager


async def init_provider_manager() -> ProviderManager:
    """Initialize the provider manager.

    Returns:
        Initialized provider manager
    """
    manager = get_provider_manager()
    await manager.initialize()
    return manager


async def shutdown_provider_manager() -> None:
    """Shutdown the provider manager."""
    global _provider_manager
    if _provider_manager:
        await _provider_manager.shutdown()
