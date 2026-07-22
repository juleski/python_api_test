"""Task API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.tasks import TaskCreate, TaskListResponse, TaskResponse, TaskUpdate
from app.services.tasks import (
    InvalidCursorError,
    SortOrder,
    TaskNotFoundError,
    TaskQuery,
    TaskService,
    TaskSortBy,
    TaskStatus,
    get_task_service,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])
TaskServiceDependency = Annotated[TaskService, Depends(get_task_service)]


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate, service: TaskServiceDependency
) -> TaskResponse:
    task = await service.create(
        name=payload.name,
        description=payload.description,
        status=payload.status,
    )
    return TaskResponse.model_validate(task)


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    service: TaskServiceDependency,
    task_status: Annotated[TaskStatus | None, Query(alias="status")] = None,
    name: Annotated[str | None, Query(min_length=1, max_length=200)] = None,
    sort_by: TaskSortBy = TaskSortBy.CREATED_AT,
    sort_order: SortOrder = SortOrder.DESC,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: str | None = None,
) -> TaskListResponse:
    query = TaskQuery(
        status=task_status,
        name=name.strip() if name else None,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
    )
    try:
        page = await service.list(query, cursor)
    except InvalidCursorError as error:
        raise HTTPException(status_code=422, detail="Invalid cursor") from error
    return TaskListResponse(
        items=[TaskResponse.model_validate(task) for task in page.items],
        next_cursor=page.next_cursor,
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: UUID, service: TaskServiceDependency) -> TaskResponse:
    try:
        task = await service.get(task_id)
    except TaskNotFoundError as error:
        raise HTTPException(status_code=404, detail="Task not found") from error
    return TaskResponse.model_validate(task)


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID, payload: TaskUpdate, service: TaskServiceDependency
) -> TaskResponse:
    try:
        task = await service.update(task_id, payload.changes())
    except TaskNotFoundError as error:
        raise HTTPException(status_code=404, detail="Task not found") from error
    return TaskResponse.model_validate(task)
