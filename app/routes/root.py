"""Root endpoint."""

from fastapi import APIRouter

from app.schemas.responses import WelcomeResponse

router = APIRouter(tags=["general"])


@router.get("/", response_model=WelcomeResponse)
async def read_root() -> WelcomeResponse:
    """Return a welcome message."""
    return WelcomeResponse(message="Welcome to the FastAPI API")
