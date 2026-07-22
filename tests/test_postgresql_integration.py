"""Optional PostgreSQL adapter and route integration test."""

import os

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.adapters.postgresql.database import get_session
from app.adapters.postgresql.models import TaskModel
from app.config import get_settings
from app.main import app

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not TEST_DATABASE_URL,
        reason="TEST_DATABASE_URL must point to an isolated PostgreSQL database",
    ),
]


@pytest.fixture(scope="module", autouse=True)
def migrated_database():
    original_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL or ""
    get_settings.cache_clear()
    command.upgrade(Config("alembic.ini"), "head")
    yield
    command.downgrade(Config("alembic.ini"), "base")
    if original_url is None:
        os.environ.pop("DATABASE_URL", None)
    else:
        os.environ["DATABASE_URL"] = original_url
    get_settings.cache_clear()


@pytest.mark.anyio
async def test_task_routes_persist_filter_update_and_paginate() -> None:
    engine = create_async_engine(TEST_DATABASE_URL or "")
    test_session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def test_session():
        async with test_session_factory() as session, session.begin():
            yield session

    app.dependency_overrides[get_session] = test_session
    try:
        async with test_session_factory() as session, session.begin():
            await session.execute(delete(TaskModel))

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            first = await client.post("/tasks", json={"name": "Database task"})
            second = await client.post(
                "/tasks", json={"name": "Another task", "status": "Done"}
            )
            assert first.status_code == second.status_code == 201

            page_one = await client.get(
                "/tasks", params={"sort_order": "asc", "limit": 1}
            )
            cursor = page_one.json()["next_cursor"]
            page_two = await client.get(
                "/tasks",
                params={"sort_order": "asc", "limit": 1, "cursor": cursor},
            )
            returned_ids = {
                page_one.json()["items"][0]["id"],
                page_two.json()["items"][0]["id"],
            }
            assert returned_ids == {first.json()["id"], second.json()["id"]}

            filtered = await client.get(
                "/tasks", params={"status": "Done", "name": "another"}
            )
            assert [item["id"] for item in filtered.json()["items"]] == [
                second.json()["id"]
            ]

            updated = await client.put(
                f"/tasks/{first.json()['id']}",
                json={"status": "In Progress", "description": "Stored in Postgres"},
            )
            fetched = await client.get(f"/tasks/{first.json()['id']}")
            assert updated.json() == fetched.json()
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()
