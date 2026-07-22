"""Unit tests for persistence-independent task use cases."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from app.services.tasks import (
    InvalidCursorError,
    SortOrder,
    TaskNotFoundError,
    TaskQuery,
    TaskService,
    TaskSortBy,
    TaskStatus,
)
from tests.fakes import InMemoryTaskRepository

FIRST_ID = UUID("00000000-0000-0000-0000-000000000001")
SECOND_ID = UUID("00000000-0000-0000-0000-000000000002")


@pytest.mark.anyio
async def test_create_get_and_update_task() -> None:
    repository = InMemoryTaskRepository()
    times = iter(
        [
            datetime(2026, 7, 22, 10, tzinfo=UTC),
            datetime(2026, 7, 22, 11, tzinfo=UTC),
        ]
    )
    service = TaskService(
        repository, clock=lambda: next(times), id_factory=lambda: FIRST_ID
    )

    created = await service.create(
        name="Write tests", description=None, status=TaskStatus.TODO
    )
    updated = await service.update(
        created.id,
        {"description": "Cover use cases", "status": TaskStatus.IN_PROGRESS},
    )

    assert await service.get(created.id) == updated
    assert updated.status is TaskStatus.IN_PROGRESS
    assert updated.updated_at > updated.created_at


@pytest.mark.anyio
async def test_missing_task_raises_not_found() -> None:
    service = TaskService(InMemoryTaskRepository())

    with pytest.raises(TaskNotFoundError):
        await service.get(FIRST_ID)


@pytest.mark.anyio
async def test_cursor_pagination_and_query_binding() -> None:
    repository = InMemoryTaskRepository()
    now = datetime(2026, 7, 22, 10, tzinfo=UTC)
    ids = iter([FIRST_ID, SECOND_ID])
    times = iter([now, now + timedelta(minutes=1)])
    service = TaskService(
        repository,
        clock=lambda: next(times),
        id_factory=lambda: next(ids),
    )
    await service.create(name="First task", description=None, status=TaskStatus.TODO)
    await service.create(name="Second task", description=None, status=TaskStatus.DONE)
    query = TaskQuery(sort_order=SortOrder.ASC, limit=1)

    first_page = await service.list(query)
    second_page = await service.list(query, first_page.next_cursor)

    assert [task.name for task in first_page.items] == ["First task"]
    assert [task.name for task in second_page.items] == ["Second task"]
    assert second_page.next_cursor is None

    changed_query = TaskQuery(
        sort_by=TaskSortBy.UPDATED_AT,
        sort_order=SortOrder.ASC,
        limit=1,
    )
    with pytest.raises(InvalidCursorError):
        await service.list(changed_query, first_page.next_cursor)
