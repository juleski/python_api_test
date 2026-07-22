"""Task application services."""

from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.application.cursors import decode_cursor, encode_cursor
from app.domain.tasks import Task, TaskPage, TaskQuery, TaskRepository, TaskStatus


class TaskNotFoundError(LookupError):
    """Raised when a requested task does not exist."""


class EmptyTaskUpdateError(ValueError):
    """Raised when an update contains no editable fields."""


class TaskService:
    """Persistence-independent task use cases."""

    def __inipt__(
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
        if not changes:
            raise EmptyTaskUpdateError
        task = await self.get(task_id)
        updated = replace(task, **changes, updated_at=self.clock())
        return await self.repository.update(updated)

    async def list(self, query: TaskQuery, cursor: str | None = None) -> TaskPage:
        position = decode_cursor(cursor, query) if cursor else None
        tasks, has_more = await self.repository.list(query, position)
        next_cursor = encode_cursor(tasks[-1], query) if has_more and tasks else None
        return TaskPage(items=tasks, next_cursor=next_cursor)
