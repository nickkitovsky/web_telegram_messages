"""Store whether Saved Messages were forwarded.

Revision ID: 20261005_0007
Revises: 20261005_0006
"""

import sqlalchemy as sa

from alembic import op

revision = "20261005_0007"
down_revision = "20261005_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "saved_messages",
        sa.Column("is_forwarded", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.execute("UPDATE saved_messages SET is_forwarded = true WHERE channel IS NOT NULL")


def downgrade() -> None:
    op.drop_column("saved_messages", "is_forwarded")
