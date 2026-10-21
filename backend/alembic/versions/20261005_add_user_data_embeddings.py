"""add user_data_embeddings table

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-10-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_data_embeddings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("source_type", sa.String(30), nullable=False),
        sa.Column("source_id", sa.UUID(), nullable=True),
        sa.Column("field_key", sa.String(255), nullable=False),
        sa.Column("text_content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(768), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_user_data_embeddings_user_id",
        "user_data_embeddings",
        ["user_id"],
    )

    op.create_index(
        "ix_user_data_embeddings_user_source",
        "user_data_embeddings",
        ["user_id", "source_type"],
    )


def downgrade() -> None:
    op.drop_index("ix_user_data_embeddings_user_source", table_name="user_data_embeddings")
    op.drop_index("ix_user_data_embeddings_user_id", table_name="user_data_embeddings")
    op.drop_table("user_data_embeddings")
