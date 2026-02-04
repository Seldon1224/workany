"""MCP API routes."""
import json
from pathlib import Path
from typing import Any

import aiofiles
from fastapi import APIRouter
from pydantic import BaseModel

from config.constants import get_all_mcp_config_paths, get_home_dir

router = APIRouter()


class MCPServerConfig(BaseModel):
    """MCP server configuration."""
    command: str | None = None
    args: list[str] | None = None
    env: dict[str, str] | None = None
    url: str | None = None
    headers: dict[str, str] | None = None


class MCPConfig(BaseModel):
    """MCP configuration."""
    mcpServers: dict[str, Any]


def get_mcp_config_path() -> str:
    """Get MCP config file path.
    
    Returns:
        Path to ~/.workany/mcp.json
    """
    return str(Path.home() / ".workany" / "mcp.json")


@router.get("/config")
async def get_mcp_config():
    """Read MCP configuration.
    
    Returns:
        MCP configuration
    """
    config_path = get_mcp_config_path()
    path_obj = Path(config_path)
    
    if not path_obj.exists():
        return {
            "success": True,
            "data": {"mcpServers": {}},
            "path": config_path,
        }
    
    try:
        async with aiofiles.open(config_path, "r") as f:
            content = await f.read()
        config = json.loads(content)
        
        return {
            "success": True,
            "data": config,
            "path": config_path,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "path": config_path,
        }


@router.post("/config")
async def save_mcp_config(config: MCPConfig):
    """Save MCP configuration.
    
    Args:
        config: MCP configuration to save
    
    Returns:
        Success status
    """
    config_path = get_mcp_config_path()
    path_obj = Path(config_path)
    
    # Ensure directory exists
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        config_json = json.dumps(config.model_dump(), indent=2)
        async with aiofiles.open(config_path, "w") as f:
            await f.write(config_json)
        
        return {
            "success": True,
            "message": "MCP config saved",
            "path": config_path,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


@router.get("/path")
async def get_mcp_path():
    """Get MCP config file path.
    
    Returns:
        MCP config path
    """
    return {
        "success": True,
        "path": get_mcp_config_path(),
    }


@router.get("/all-configs")
async def get_all_mcp_configs():
    """Read MCP configs from all sources.
    
    Returns:
        All MCP configurations
    """
    config_paths = get_all_mcp_config_paths()
    results = []
    
    for config_info in config_paths:
        path_obj = Path(config_info["path"])
        
        if not path_obj.exists():
            results.append({
                "name": config_info["name"],
                "path": config_info["path"],
                "exists": False,
                "servers": {},
            })
            continue
        
        try:
            async with aiofiles.open(config_info["path"], "r") as f:
                content = await f.read()
            config = json.loads(content)
            
            results.append({
                "name": config_info["name"],
                "path": config_info["path"],
                "exists": True,
                "servers": config.get("mcpServers", {}),
            })
        except:
            results.append({
                "name": config_info["name"],
                "path": config_info["path"],
                "exists": False,
                "servers": {},
            })
    
    return {
        "success": True,
        "configs": results,
    }
