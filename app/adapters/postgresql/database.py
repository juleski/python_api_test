"""Async SQLAlchemy engine and session lifecycle."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

engine = create_async_engine(get_settings().database_url, pool_pre_ping=True)
session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Provide one transactional session per request."""
    async with session_factory() as session, session.begin():
        yield session


async def dispose_engine() -> None:
    """Release database connections during application shutdown."""
    await engine.dispose()
