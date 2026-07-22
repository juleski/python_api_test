"""Create tasks table.

Revision ID: 20260722_01
Revises:
Create Date: 2026-07-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260722_01"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(length=2000), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('To Do', 'In Progress', 'Done')",
            name="ck_tasks_status",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tasks_created_at_id", "tasks", ["created_at", "id"])
    op.create_index("ix_tasks_status", "tasks", ["status"])
    op.create_index("ix_tasks_updated_at_id", "tasks", ["updated_at", "id"])


def downgrade() -> None:
    op.drop_index("ix_tasks_updated_at_id", table_name="tasks")
    op.drop_index("ix_tasks_status", table_name="tasks")
    op.drop_index("ix_tasks_created_at_id", table_name="tasks")
    op.drop_table("tasks")
