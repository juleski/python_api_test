"""Response models shared by API routes."""

from typing import Literal

from pydantic import BaseModel


class WelcomeResponse(BaseModel):
    """Response returned by the root endpoint."""

    message: str


class HealthResponse(BaseModel):
    """Response returned by the health endpoint."""

    status: Literal["ok"]
