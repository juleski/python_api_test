"""Health-check endpoint."""

from fastapi import APIRouter

from app.schemas.responses import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def read_health() -> HealthResponse:
    """Report whether the API is healthy."""
    return HealthResponse(status="ok")
