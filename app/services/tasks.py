"""Task types, business logic, pagination, and dependency wiring."""

import base64
import binascii
import json
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Protocol
from uuid import UUID, uuid4

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.postgresql.database import get_session


class TaskStatus(StrEnum):
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    DONE = "Done"


class TaskSortBy(StrEnum):
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class SortOrder(StrEnum):
    ASC = "asc"
    DESC = "desc"


@dataclass(frozen=True)
class Task:
    id: UUID
    name: str
    description: str | None
    status: TaskStatus
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class TaskQuery:
    status: TaskStatus | None = None
    name: str | None = None
    sort_by: TaskSortBy = TaskSortBy.CREATED_AT
    sort_order: SortOrder = SortOrder.DESC
    limit: int = 20


@dataclass(frozen=True)
class CursorPosition:
    timestamp: datetime
    task_id: UUID


@dataclass(frozen=True)
class TaskPage:
    items: list[Task]
    next_cursor: str | None


class TaskRepository(Protocol):
    """Small boundary between task logic and database adapters."""

    async def add(self, task: Task) -> Task: ...

    async def get(self, task_id: UUID) -> Task | None: ...

    async def update(self, task: Task) -> Task: ...

    async def list(
        self, query: TaskQuery, after: CursorPosition | None
    ) -> tuple[list[Task], bool]: ...


class TaskNotFoundError(LookupError):
    pass


class InvalidCursorError(ValueError):
    pass


def _query_context(query: TaskQuery) -> dict[str, str | None]:
    return {
        "status": query.status.value if query.status else None,
        "name": query.name,
        "sort_by": query.sort_by.value,
        "sort_order": query.sort_order.value,
    }


def _encode_cursor(task: Task, query: TaskQuery) -> str:
    timestamp = getattr(task, query.sort_by.value)
    payload = {
        "version": 1,
        **_query_context(query),
        "timestamp": timestamp.isoformat(),
        "task_id": str(task.id),
    }
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _decode_cursor(cursor: str, query: TaskQuery) -> CursorPosition:
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        payload = json.loads(base64.b64decode(padded, altchars=b"-_", validate=True))
        if not isinstance(payload, dict) or payload.get("version") != 1:
            raise InvalidCursorError
        if any(
            payload.get(key) != value for key, value in _query_context(query).items()
        ):
            raise InvalidCursorError
        timestamp = datetime.fromisoformat(payload["timestamp"])
        if timestamp.tzinfo is None:
            raise InvalidCursorError
        return CursorPosition(timestamp=timestamp, task_id=UUID(payload["task_id"]))
    except (
        InvalidCursorError,
        binascii.Error,
        UnicodeDecodeError,
        json.JSONDecodeError,
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        raise InvalidCursorError("Invalid cursor") from error


class TaskService:
    """Task business operations used directly by the route layer."""

    def __init__(
        self,
        repository: TaskRepository,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self.repository = repository
        self.clock = clock
        self.id_factory = id_factory

    async def create(
        self,
        *,
        name: str,
        description: str | None,
        status: TaskStatus,
    ) -> Task:
        now = self.clock()
        task = Task(
            id=self.id_factory(),
            name=name,
            description=description,
            status=status,
            created_at=now,
            updated_at=now,
        )
        return await self.repository.add(task)

    async def get(self, task_id: UUID) -> Task:
        task = await self.repository.get(task_id)
        if task is None:
            raise TaskNotFoundError
        return task

    async def update(self, task_id: UUID, changes: dict[str, object]) -> Task:
        task = await self.get(task_id)
        updated = replace(task, **changes, updated_at=self.clock())
        return await self.repository.update(updated)

    async def list(self, query: TaskQuery, cursor: str | None = None) -> TaskPage:
        position = _decode_cursor(cursor, query) if cursor else None
        tasks, has_more = await self.repository.list(query, position)
        next_cursor = _encode_cursor(tasks[-1], query) if has_more and tasks else None
        return TaskPage(items=tasks, next_cursor=next_cursor)


def get_task_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TaskService:
    """Build a task service with the configured database adapter."""
    from app.adapters.postgresql.repositories import SQLAlchemyTaskRepository

    return TaskService(SQLAlchemyTaskRepository(session))
