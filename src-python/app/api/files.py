"""Files API routes."""
import os
from pathlib import Path
from typing import Optional

import aiofiles
from fastapi import APIRouter
from pydantic import BaseModel

from config.constants import get_all_skills_dirs, get_home_dir

router = APIRouter()


class FileEntry(BaseModel):
    """File or directory entry."""
    name: str
    path: str
    isDir: bool
    children: Optional[list["FileEntry"]] = None


class ReadDirRequest(BaseModel):
    """Read directory request."""
    path: str
    maxDepth: int = 3


class ReadFileRequest(BaseModel):
    """Read file request."""
    path: str


class StatRequest(BaseModel):
    """File stat request."""
    path: str


# Ignored files/folders
IGNORED_NAMES = {
    "node_modules", "__pycache__", ".git", ".venv", "venv",
    "dist", "build", ".next", ".cache", "logs",
}


def should_ignore(name: str) -> bool:
    """Check if a file/folder should be ignored.
    
    Args:
        name: File or directory name
    
    Returns:
        True if should be ignored
    """
    if name.startswith("."):
        return True
    if name in IGNORED_NAMES:
        return True
    if name.endswith(".log"):
        return True
    return False


async def read_dir_recursive(
    dir_path: str,
    depth: int = 0,
    max_depth: int = 3
) -> list[FileEntry]:
    """Recursively read directory contents.
    
    Args:
        dir_path: Directory path
        depth: Current depth
        max_depth: Maximum recursion depth
    
    Returns:
        List of file entries
    """
    if depth > max_depth:
        return []
    
    try:
        entries = []
        path_obj = Path(dir_path)
        
        for item in path_obj.iterdir():
            if should_ignore(item.name):
                continue
            
            is_dir = item.is_dir()
            entry = FileEntry(
                name=item.name,
                path=str(item),
                isDir=is_dir,
            )
            
            if is_dir and depth < max_depth:
                try:
                    entry.children = await read_dir_recursive(
                        str(item),
                        depth + 1,
                        max_depth
                    )
                except:
                    entry.children = []
            
            entries.append(entry)
        
        # Sort: directories first, then by name
        entries.sort(key=lambda x: (not x.isDir, x.name))
        return entries
    
    except Exception as e:
        print(f"Error reading {dir_path}: {e}")
        return []


@router.post("/readdir")
async def read_directory(request: ReadDirRequest):
    """Read directory contents recursively.
    
    Args:
        request: Read directory request
    
    Returns:
        Directory contents
    """
    dir_path = request.path
    
    # Expand ~ to home directory
    if dir_path.startswith("~"):
        home_dir = get_home_dir()
        dir_path = dir_path.replace("~", home_dir, 1)
    
    # Security check: only allow reading from home directory
    home_dir = get_home_dir()
    if not dir_path.startswith(home_dir) and not dir_path.startswith("/tmp"):
        return {
            "success": False,
            "error": "Access denied: path must be within home directory",
            "files": [],
        }
    
    # Check if directory exists
    path_obj = Path(dir_path)
    if not path_obj.exists():
        return {
            "success": False,
            "error": "Directory does not exist",
            "files": [],
        }
    
    if not path_obj.is_dir():
        return {
            "success": False,
            "error": "Path is not a directory",
            "files": [],
        }
    
    files = await read_dir_recursive(dir_path, 0, request.maxDepth)
    
    return {
        "success": True,
        "path": dir_path,
        "files": files,
    }


@router.post("/stat")
async def stat_file(request: StatRequest):
    """Get file or directory stats.
    
    Args:
        request: Stat request
    
    Returns:
        File stats
    """
    try:
        path_obj = Path(request.path)
        if not path_obj.exists():
            return {"exists": False}
        
        stat = path_obj.stat()
        return {
            "exists": True,
            "isFile": path_obj.is_file(),
            "isDirectory": path_obj.is_dir(),
            "size": stat.st_size,
            "mtime": stat.st_mtime,
        }
    except Exception as e:
        return {"error": str(e)}


@router.post("/read")
async def read_file(request: ReadFileRequest):
    """Read file contents.
    
    Args:
        request: Read file request
    
    Returns:
        File contents
    """
    file_path = request.path
    
    # Security check
    home_dir = get_home_dir()
    if not file_path.startswith(home_dir) and not file_path.startswith("/tmp"):
        return {
            "success": False,
            "error": "Access denied",
        }
    
    try:
        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
            content = await f.read()
        
        return {
            "success": True,
            "content": content,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


@router.post("/read-binary")
async def read_binary_file(request: ReadFileRequest):
    """Read binary file contents and return as base64.
    
    Args:
        request: Read file request
    
    Returns:
        Base64 encoded file contents
    """
    import base64
    
    file_path = request.path
    
    # Security check
    home_dir = get_home_dir()
    if not file_path.startswith(home_dir) and not file_path.startswith("/tmp"):
        return {
            "success": False,
            "error": "Access denied",
        }
    
    try:
        async with aiofiles.open(file_path, "rb") as f:
            content = await f.read()
        
        # Encode to base64
        encoded = base64.b64encode(content).decode('utf-8')
        
        return {
            "success": True,
            "content": encoded,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


@router.get("/skills-dir")
async def get_skills_directory():
    """Get all skills directories.
    
    Returns:
        Skills directories information
    """
    skills_dirs = get_all_skills_dirs()
    results = []
    
    for dir_info in skills_dirs:
        path_obj = Path(dir_info["path"])
        exists = path_obj.exists() and path_obj.is_dir()
        
        # Try to create workany skills dir if it doesn't exist
        if not exists and dir_info["name"] == "workany":
            try:
                path_obj.mkdir(parents=True, exist_ok=True)
                exists = True
            except:
                pass
        
        results.append({
            "name": dir_info["name"],
            "path": dir_info["path"],
            "exists": exists,
        })
    
    # Return first existing directory for backward compatibility
    first_existing = next((r for r in results if r["exists"]), None)
    
    return {
        "path": first_existing["path"] if first_existing else "",
        "exists": bool(first_existing),
        "directories": results,
    }
