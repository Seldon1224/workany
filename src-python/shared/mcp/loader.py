"""MCP server loader for Claude Agent SDK."""
import json
from pathlib import Path
from typing import Any, Optional

import aiofiles

from config.constants import get_workany_dir
from shared.utils.logger import create_logger

logger = create_logger("MCPLoader")


# MCP Server Config Types
class McpStdioServerConfig(dict):
    """Stdio-based MCP server configuration."""
    def __init__(self, command: str, args: Optional[list[str]] = None, env: Optional[dict[str, str]] = None):
        super().__init__()
        self["type"] = "stdio"
        self["command"] = command
        if args:
            self["args"] = args
        if env:
            self["env"] = env


class McpHttpServerConfig(dict):
    """HTTP-based MCP server configuration."""
    def __init__(self, url: str, headers: Optional[dict[str, str]] = None):
        super().__init__()
        self["type"] = "http"
        self["url"] = url
        if headers:
            self["headers"] = headers


class McpSSEServerConfig(dict):
    """SSE-based MCP server configuration."""
    def __init__(self, url: str, headers: Optional[dict[str, str]] = None):
        super().__init__()
        self["type"] = "sse"
        self["url"] = url
        if headers:
            self["headers"] = headers


McpServerConfig = McpStdioServerConfig | McpHttpServerConfig | McpSSEServerConfig


def get_mcp_config_path() -> str:
    """Get the MCP config file path.
    
    Returns:
        Path to ~/.workany/mcp.json
    """
    return str(Path(get_workany_dir()) / "mcp.json")


async def load_mcp_servers_from_file(
    config_path: str,
    source_name: str
) -> dict[str, McpServerConfig]:
    """Load MCP servers from a single config file.
    
    Args:
        config_path: Path to config file
        source_name: Name of the source (for logging)
    
    Returns:
        Dictionary of server name to config
    """
    try:
        path_obj = Path(config_path)
        if not path_obj.exists():
            return {}
        
        async with aiofiles.open(config_path, "r") as f:
            content = await f.read()
        config = json.loads(content)
        
        # Support both formats: { mcpServers: {...} } and direct { serverName: {...} }
        mcp_servers = config.get("mcpServers", config)
        
        if not mcp_servers or not isinstance(mcp_servers, dict):
            return {}
        
        servers: dict[str, McpServerConfig] = {}
        
        for name, server_config in mcp_servers.items():
            if not isinstance(server_config, dict):
                continue
            
            # URL-based server (HTTP or SSE)
            if "url" in server_config:
                url = server_config["url"]
                headers = server_config.get("headers")
                server_type = server_config.get("type", "http")
                
                if server_type == "sse":
                    servers[name] = McpSSEServerConfig(url, headers)
                    logger.info(f"[MCP] Loaded SSE server from {source_name}: {name}")
                else:
                    servers[name] = McpHttpServerConfig(url, headers)
                    logger.info(f"[MCP] Loaded HTTP server from {source_name}: {name}")
            
            # Stdio-based server
            elif "command" in server_config:
                command = server_config["command"]
                args = server_config.get("args")
                env = server_config.get("env")
                servers[name] = McpStdioServerConfig(command, args, env)
                logger.info(f"[MCP] Loaded stdio server from {source_name}: {name}")
        
        return servers
    
    except Exception as e:
        logger.error(f"[MCP] Error loading from {config_path}: {e}")
        return {}


async def load_mcp_servers(
    mcp_config: Optional[dict[str, Any]] = None
) -> dict[str, McpServerConfig]:
    """Load MCP servers configuration from ~/.workany/mcp.json.
    
    Args:
        mcp_config: Optional config to control loading
    
    Returns:
        Dictionary of server name to config
    """
    # If MCP is globally disabled, return empty
    if mcp_config and not mcp_config.get("enabled", True):
        logger.info("[MCP] MCP disabled, skipping server load")
        return {}
    
    config_path = get_mcp_config_path()
    servers = await load_mcp_servers_from_file(config_path, "workany")
    
    server_count = len(servers)
    if server_count > 0:
        logger.info(f"[MCP] Loaded {server_count} MCP server(s)")
    else:
        logger.info("[MCP] No MCP servers found")
    
    return servers
