"""recreate daily_updates

Revision ID: 846939560e3d
Revises: 638ec0b63936
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "846939560e3d"
down_revision: Union[str, Sequence[str], None] = "638ec0b63936"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "daily_updates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("employee_id", sa.Integer(),sa.ForeignKey("users.id"), nullable=False),
        sa.Column("work_done", sa.Text(), nullable=False),
        sa.Column("next_steps", sa.Text(), nullable=False),
        sa.Column("confidence_score", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["users.id"],
            ondelete="CASCADE",   # Optional but recommended
        ),
    )

    op.create_index(
        "ix_daily_updates_id",
        "daily_updates",
        ["id"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_daily_updates_id", table_name="daily_updates")
    op.drop_table("daily_updates")