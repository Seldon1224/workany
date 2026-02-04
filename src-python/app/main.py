"""FastAPI application entry point."""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import agent, files, health, mcp, providers
from app.middleware import setup_cors
from config import load_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.
    
    Args:
        app: FastAPI application
    """
    # Startup
    print("🚀 WorkAny API (Python) starting...")
    await load_config()
    print("✅ Configuration loaded")
    
    # Initialize Provider Manager
    from shared.provider.manager import init_provider_manager
    await init_provider_manager()
    print("✅ Provider Manager initialized")
    
    yield
    
    # Shutdown
    print("👋 WorkAny API shutting down...")
    
    # Shutdown Provider Manager
    from shared.provider.manager import shutdown_provider_manager
    await shutdown_provider_manager()
    print("✅ Provider Manager shutdown")


# Create FastAPI app
app = FastAPI(
    title="WorkAny API",
    version="0.1.0",
    description="WorkAny API - Python/FastAPI implementation",
    lifespan=lifespan,
)

# Setup CORS
setup_cors(app)

# Register routes
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(agent.router, prefix="/agent", tags=["agent"])
app.include_router(files.router, prefix="/files", tags=["files"])
app.include_router(mcp.router, prefix="/mcp", tags=["mcp"])
app.include_router(providers.router, prefix="/providers", tags=["providers"])


@app.get("/")
async def root():
    """Root endpoint.
    
    Returns:
        API information
    """
    return {
        "name": "WorkAny API",
        "version": "0.1.0",
        "implementation": "Python/FastAPI",
        "endpoints": {
            "health": "/health",
            "agent": "/agent",
            "files": "/files",
            "mcp": "/mcp",
            "providers": "/providers",
        },
    }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "2026"))
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )
