"""SQLAlchemy implementation of the task repository port."""

from sqlalchemy import and_, asc, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.postgresql.models import TaskModel
from app.services.tasks import CursorPosition, SortOrder, Task, TaskQuery, TaskStatus


def _to_domain(model: TaskModel) -> Task:
    return Task(
        id=model.id,
        name=model.name,
        description=model.description,
        status=TaskStatus(model.status),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SQLAlchemyTaskRepository:
    """Persist tasks using an injected SQLAlchemy session."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, task: Task) -> Task:
        model = TaskModel(
            id=task.id,
            name=task.name,
            description=task.description,
            status=task.status.value,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )
        self.session.add(model)
        await self.session.flush()
        return _to_domain(model)

    async def get(self, task_id) -> Task | None:
        model = await self.session.get(TaskModel, task_id)
        return _to_domain(model) if model else None

    async def update(self, task: Task) -> Task:
        model = await self.session.get(TaskModel, task.id)
        if model is None:
            return task
        model.name = task.name
        model.description = task.description
        model.status = task.status.value
        model.updated_at = task.updated_at
        await self.session.flush()
        return _to_domain(model)

    async def list(
        self, query: TaskQuery, after: CursorPosition | None
    ) -> tuple[list[Task], bool]:
        timestamp_column = getattr(TaskModel, query.sort_by.value)
        statement = select(TaskModel)

        if query.status:
            statement = statement.where(TaskModel.status == query.status.value)
        if query.name:
            statement = statement.where(
                TaskModel.name.icontains(query.name, autoescape=True)
            )
        if after:
            comparison = (
                timestamp_column > after.timestamp
                if query.sort_order is SortOrder.ASC
                else timestamp_column < after.timestamp
            )
            id_comparison = (
                TaskModel.id > after.task_id
                if query.sort_order is SortOrder.ASC
                else TaskModel.id < after.task_id
            )
            statement = statement.where(
                or_(
                    comparison,
                    and_(timestamp_column == after.timestamp, id_comparison),
                )
            )

        order = asc if query.sort_order is SortOrder.ASC else desc
        statement = statement.order_by(order(timestamp_column), order(TaskModel.id))
        statement = statement.limit(query.limit + 1)
        models = list((await self.session.scalars(statement)).all())
        has_more = len(models) > query.limit
        return [_to_domain(model) for model in models[: query.limit]], has_more
