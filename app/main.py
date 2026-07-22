"""Application entrypoint."""

from fastapi import FastAPI

from app.routes import health, root


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title="Python API Test",
        description="A FastAPI project for practicing API development.",
        version="0.1.0",
    )
    application.include_router(root.router)
    application.include_router(health.router)
    return application


app = create_app()
