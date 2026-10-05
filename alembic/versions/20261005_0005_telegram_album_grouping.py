"""Group Telegram album messages in the feed.

Revision ID: 20261005_0005
Revises: 20261005_0004
"""

import sqlalchemy as sa

from alembic import op

revision = "20261005_0005"
down_revision = "20261005_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("saved_messages", sa.Column("telegram_grouped_id", sa.BigInteger()))
    op.create_index(
        "ix_saved_messages_telegram_grouped_id",
        "saved_messages",
        ["telegram_grouped_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_saved_messages_telegram_grouped_id", table_name="saved_messages")
    op.drop_column("saved_messages", "telegram_grouped_id")
