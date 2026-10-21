"""enable pgvector and add canonical_embeddings

Revision ID: a1b2c3d4e5f6
Revises: 10971a104aca
Create Date: 2026-10-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "10971a104aca"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "canonical_embeddings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("canonical_key", sa.String(100), nullable=False),
        sa.Column("label_text", sa.String(500), nullable=False),
        sa.Column("embedding", Vector(768), nullable=True),
        sa.Column(
            "source",
            sa.String(20),
            nullable=False,
            server_default="seed",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_canonical_embeddings_key",
        "canonical_embeddings",
        ["canonical_key"],
    )


def downgrade() -> None:
    op.drop_index("ix_canonical_embeddings_key", table_name="canonical_embeddings")
    op.drop_table("canonical_embeddings")
    op.execute("DROP EXTENSION IF EXISTS vector")
