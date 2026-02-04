"""Configuration loader for WorkAny API."""
import os
from pathlib import Path


async def load_config() -> None:
    """Load and initialize configuration.
    
    Creates necessary directories if they don't exist.
    """
    # Create .workany directory structure
    workany_dir = Path.home() / ".workany"
    (workany_dir / "logs").mkdir(parents=True, exist_ok=True)
    (workany_dir / "skills").mkdir(parents=True, exist_ok=True)
    
    # Create default sessions directory
    sessions_dir = Path.home() / "workany-sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"✅ Configuration loaded")
    print(f"   WorkAny dir: {workany_dir}")
    print(f"   Sessions dir: {sessions_dir}")
