"""Track whether Saved Message media was inspected.

Revision ID: 20261005_0004
Revises: 20261005_0003
"""

import sqlalchemy as sa

from alembic import op

revision = "20261005_0004"
down_revision = "20261005_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "saved_messages",
        sa.Column("media_checked", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.execute("UPDATE saved_messages SET media_checked = true WHERE media_path IS NOT NULL")


def downgrade() -> None:
    op.drop_column("saved_messages", "media_checked")
