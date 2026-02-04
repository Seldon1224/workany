"""Configuration constants for WorkAny API."""
import os
from pathlib import Path


def get_home_dir() -> str:
    """Get user's home directory."""
    return str(Path.home())


def get_workany_dir() -> str:
    """Get WorkAny configuration directory (~/.workany)."""
    return str(Path.home() / ".workany")


def get_claude_dir() -> str:
    """Get Claude configuration directory (~/.claude)."""
    return str(Path.home() / ".claude")


# API Configuration
DEFAULT_API_HOST = "127.0.0.1"
DEFAULT_API_PORT = 2620  # Production port
DEFAULT_DEV_PORT = 2026  # Development port

# Skills directories
def get_all_skills_dirs() -> list[dict[str, str]]:
    """Get all skills directories (workany and claude)."""
    return [
        {"name": "workany", "path": str(Path.home() / ".workany" / "skills")},
        {"name": "claude", "path": str(Path.home() / ".claude" / "skills")},
    ]


# MCP configuration paths
def get_all_mcp_config_paths() -> list[dict[str, str]]:
    """Get all MCP configuration file paths."""
    return [
        {"name": "workany", "path": str(Path.home() / ".workany" / "mcp.json")},
        {"name": "claude", "path": str(Path.home() / ".claude" / "settings.json")},
    ]


# Default working directory
DEFAULT_WORK_DIR = str(Path.home() / "workany-sessions")

# Log file path
LOG_FILE_PATH = str(Path.home() / ".workany" / "logs" / "workany.log")
