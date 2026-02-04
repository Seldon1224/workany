"""Path utilities for WorkAny API."""
from pathlib import Path


def expand_path(path: str) -> str:
    """Expand ~ to home directory in path.
    
    Args:
        path: Path string that may contain ~
    
    Returns:
        Expanded absolute path
    """
    if path.startswith("~"):
        return str(Path(path).expanduser())
    return path


def ensure_dir(path: str) -> None:
    """Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path to ensure exists
    """
    Path(path).mkdir(parents=True, exist_ok=True)
