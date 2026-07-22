"""Request and response schemas for task endpoints."""

from datetime import datetime
from typing import Annotated, Self
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from app.services.tasks import TaskStatus

TaskName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]
TaskDescription = Annotated[
    str, StringConstraints(strip_whitespace=True, max_length=2000)
]


class TaskCreate(BaseModel):
    """Data accepted when creating a task."""

    name: TaskName
    description: TaskDescription | None = None
    status: TaskStatus = TaskStatus.TODO

    @field_validator("description")
    @classmethod
    def blank_description_is_none(cls, value: str | None) -> str | None:
        return value or None


class TaskUpdate(BaseModel):
    """Editable task fields; at least one must be supplied."""

    name: TaskName | None = None
    description: TaskDescription | None = None
    status: TaskStatus | None = None

    @field_validator("description")
    @classmethod
    def blank_description_is_none(cls, value: str | None) -> str | None:
        return value or None

    @model_validator(mode="after")
    def validate_changes(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("At least one editable field must be provided")
        if "name" in self.model_fields_set and self.name is None:
            raise ValueError("name cannot be null")
        if "status" in self.model_fields_set and self.status is None:
            raise ValueError("status cannot be null")
        return self

    def changes(self) -> dict[str, object]:
        return {
            field: getattr(self, field)
            for field in self.model_fields_set
            if field in {"name", "description", "status"}
        }


class TaskResponse(BaseModel):
    """Public task representation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    status: TaskStatus
    created_at: datetime
    updated_at: datetime


class TaskListResponse(BaseModel):
    """Cursor-paginated task response."""

    items: list[TaskResponse]
    next_cursor: str | None = Field(default=None)
