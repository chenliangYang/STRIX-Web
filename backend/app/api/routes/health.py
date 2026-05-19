"""Health check route."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "code": 0,
        "message": "ok",
        "data": {
            "status": "healthy",
            "service": "strix-web-backend",
        },
    }
