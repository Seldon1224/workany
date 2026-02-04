"""Health check API routes."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def health_check():
    """Health check endpoint.
    
    Returns:
        Health status
    """
    return {
        "status": "ok",
        "version": "0.1.0",
        "service": "WorkAny API (Python)",
    }
