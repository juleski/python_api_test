"""In-memory adapters used by application tests."""

from app.services.tasks import CursorPosition, SortOrder, Task, TaskQuery


class InMemoryTaskRepository:
    """Small persistence adapter with the same port semantics as PostgreSQL."""

    def __init__(self) -> None:
        self.tasks: dict[object, Task] = {}

    async def add(self, task: Task) -> Task:
        self.tasks[task.id] = task
        return task

    async def get(self, task_id) -> Task | None:
        return self.tasks.get(task_id)

    async def update(self, task: Task) -> Task:
        self.tasks[task.id] = task
        return task

    async def list(
        self, query: TaskQuery, after: CursorPosition | None
    ) -> tuple[list[Task], bool]:
        tasks = list(self.tasks.values())
        if query.status:
            tasks = [task for task in tasks if task.status is query.status]
        if query.name:
            needle = query.name.casefold()
            tasks = [task for task in tasks if needle in task.name.casefold()]

        reverse = query.sort_order is SortOrder.DESC
        tasks.sort(
            key=lambda task: (getattr(task, query.sort_by.value), task.id),
            reverse=reverse,
        )
        if after:
            after_key = (after.timestamp, after.task_id)
            tasks = [
                task
                for task in tasks
                if (
                    (getattr(task, query.sort_by.value), task.id) > after_key
                    if query.sort_order is SortOrder.ASC
                    else (getattr(task, query.sort_by.value), task.id) < after_key
                )
            ]
        has_more = len(tasks) > query.limit
        return tasks[: query.limit], has_more
