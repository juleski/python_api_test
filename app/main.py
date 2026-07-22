"""Application entrypoint."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.adapters.postgresql.database import dispose_engine
from app.metrics import ApiLatencyMiddleware
from app.metrics import router as metrics_router
from app.routes import health, root, tasks


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Manage application-level resources."""
    yield
    await dispose_engine()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title="Python API Test",
        description="A FastAPI project for practicing API development.",
        version="0.1.0",
        lifespan=lifespan,
    )
    application.include_router(root.router)
    application.include_router(health.router)
    application.include_router(tasks.router)
    application.include_router(metrics_router)
    application.add_middleware(ApiLatencyMiddleware)
    return application


app = create_app()
