"""Track whether older Telegram message batches remain.

Revision ID: 20261005_0002
Revises: 20261005_0001
"""

import sqlalchemy as sa

from alembic import op

revision = "20261005_0002"
down_revision = "20261005_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "telegram_auth",
        sa.Column("sync_has_more", sa.Boolean(), server_default=sa.true(), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("telegram_auth", "sync_has_more")
