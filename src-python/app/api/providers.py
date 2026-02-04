"""Provider Management API Routes.

Provides REST endpoints for managing sandbox and agent providers.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from shared.provider.manager import get_provider_manager
from shared.utils.logger import create_logger

logger = create_logger("ProvidersAPI")

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================


class SwitchProviderRequest(BaseModel):
    """Switch provider request."""

    type: str
    config: Optional[Dict[str, Any]] = None


class SwitchProviderResponse(BaseModel):
    """Switch provider response."""

    success: bool
    current: str
    message: str


class ProviderMetadataResponse(BaseModel):
    """Provider metadata response."""

    type: str
    name: str
    description: Optional[str] = None
    version: Optional[str] = None
    configSchema: Optional[Dict[str, Any]] = None
    available: bool = False
    current: bool = False


class ProvidersListResponse(BaseModel):
    """Providers list response."""

    providers: List[ProviderMetadataResponse]
    current: Optional[str] = None


class AvailableProvidersResponse(BaseModel):
    """Available providers response."""

    available: List[str]


class SettingsSyncRequest(BaseModel):
    """Settings sync request."""

    sandboxProvider: Optional[str] = None
    sandboxConfig: Optional[Dict[str, Any]] = None
    agentProvider: Optional[str] = None
    agentConfig: Optional[Dict[str, Any]] = None
    defaultProvider: Optional[str] = None
    defaultModel: Optional[str] = None


class ProvidersConfigResponse(BaseModel):
    """Providers config response."""

    sandbox: Optional[Dict[str, Any]] = None
    agent: Optional[Dict[str, Any]] = None


# ============================================================================
# Sandbox Provider Routes
# ============================================================================


@router.get("/sandbox", response_model=ProvidersListResponse)
async def list_sandbox_providers():
    """List all sandbox providers with their metadata."""
    try:
        manager = get_provider_manager()
        metadata = manager.get_sandbox_providers_metadata()
        available = await manager.get_available_sandbox_providers()
        current = manager.get_config().sandbox

        providers = [
            ProviderMetadataResponse(
                **m.to_dict(),
                available=m.type in available,
                current=current.type == m.type if current else False,
            )
            for m in metadata
        ]

        return ProvidersListResponse(
            providers=providers, current=current.type if current else None
        )
    except Exception as e:
        logger.error(f"Error listing sandbox providers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list sandbox providers")


@router.get("/sandbox/available", response_model=AvailableProvidersResponse)
async def get_available_sandbox_providers():
    """List available sandbox providers (those that can actually run on this system)."""
    try:
        manager = get_provider_manager()
        available = await manager.get_available_sandbox_providers()
        return AvailableProvidersResponse(available=available)
    except Exception as e:
        logger.error(f"Error getting available sandbox providers: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to get available sandbox providers"
        )


@router.post("/sandbox/switch", response_model=SwitchProviderResponse)
async def switch_sandbox_provider(request: SwitchProviderRequest):
    """Switch to a different sandbox provider."""
    try:
        if not request.type:
            raise HTTPException(status_code=400, detail="Provider type is required")

        manager = get_provider_manager()
        await manager.switch_sandbox_provider(request.type, request.config)

        return SwitchProviderResponse(
            success=True,
            current=request.type,
            message=f"Switched to sandbox provider: {request.type}",
        )
    except ValueError as e:
        logger.error(f"Error switching sandbox provider: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error switching sandbox provider: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to switch sandbox provider: {str(e)}"
        )


# ============================================================================
# Agent Provider Routes
# ============================================================================


@router.get("/agents", response_model=ProvidersListResponse)
async def list_agent_providers():
    """List all agent providers with their metadata."""
    try:
        manager = get_provider_manager()
        metadata = manager.get_agent_providers_metadata()
        available = await manager.get_available_agent_providers()
        current = manager.get_config().agent

        providers = [
            ProviderMetadataResponse(
                **m.to_dict(),
                available=m.type in available,
                current=current.type == m.type if current else False,
            )
            for m in metadata
        ]

        return ProvidersListResponse(
            providers=providers, current=current.type if current else None
        )
    except Exception as e:
        logger.error(f"Error listing agent providers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list agent providers")


@router.get("/agents/available", response_model=AvailableProvidersResponse)
async def get_available_agent_providers():
    """List available agent providers."""
    try:
        manager = get_provider_manager()
        available = await manager.get_available_agent_providers()
        return AvailableProvidersResponse(available=available)
    except Exception as e:
        logger.error(f"Error getting available agent providers: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to get available agent providers"
        )


@router.post("/agents/switch", response_model=SwitchProviderResponse)
async def switch_agent_provider(request: SwitchProviderRequest):
    """Switch to a different agent provider."""
    try:
        if not request.type:
            raise HTTPException(status_code=400, detail="Provider type is required")

        manager = get_provider_manager()
        await manager.switch_agent_provider(request.type, request.config)

        return SwitchProviderResponse(
            success=True,
            current=request.type,
            message=f"Switched to agent provider: {request.type}",
        )
    except ValueError as e:
        logger.error(f"Error switching agent provider: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error switching agent provider: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to switch agent provider: {str(e)}"
        )


# ============================================================================
# Settings Sync Route
# ============================================================================


@router.post("/settings/sync")
async def sync_settings(request: SettingsSyncRequest):
    """Sync frontend settings with the backend."""
    try:
        manager = get_provider_manager()

        # Update sandbox provider if specified
        if request.sandboxProvider:
            await manager.switch_sandbox_provider(
                request.sandboxProvider, request.sandboxConfig
            )

        # Update agent provider if specified
        # The agentConfig now includes apiKey, baseUrl, and model from the selected AI provider
        if request.agentProvider:
            await manager.switch_agent_provider(
                request.agentProvider, request.agentConfig
            )

        logger.info(
            f"Settings synced: agentProvider={request.agentProvider}, "
            f"defaultProvider={request.defaultProvider}, "
            f"defaultModel={request.defaultModel}, "
            f"hasApiKey={bool(request.agentConfig and request.agentConfig.get('apiKey'))}, "
            f"hasBaseUrl={bool(request.agentConfig and request.agentConfig.get('baseUrl'))}"
        )

        config = manager.get_config()
        return {"success": True, "config": config.to_dict()}
    except Exception as e:
        logger.error(f"Error syncing settings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to sync settings: {str(e)}")


# ============================================================================
# Config Route
# ============================================================================


@router.get("/config", response_model=ProvidersConfigResponse)
async def get_providers_config():
    """Get current provider configuration."""
    try:
        manager = get_provider_manager()
        config = manager.get_config()
        return ProvidersConfigResponse(**config.to_dict())
    except Exception as e:
        logger.error(f"Error getting config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get configuration")
