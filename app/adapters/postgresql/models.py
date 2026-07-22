"""SQLAlchemy persistence models."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Index, String, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base metadata used by the PostgreSQL adapter and Alembic."""


class TaskModel(Base):
    """Database representation of a task."""

    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint(
            "status IN ('To Do', 'In Progress', 'Done')",
            name="ck_tasks_status",
        ),
        Index("ix_tasks_status", "status"),
        Index("ix_tasks_created_at_id", "created_at", "id"),
        Index("ix_tasks_updated_at_id", "updated_at", "id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
