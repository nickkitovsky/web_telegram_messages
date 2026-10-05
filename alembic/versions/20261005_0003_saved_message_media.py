"""Store downloaded Telegram media metadata.

Revision ID: 20261005_0003
Revises: 20261005_0002
"""

import sqlalchemy as sa

from alembic import op

revision = "20261005_0003"
down_revision = "20261005_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("saved_messages", sa.Column("media_path", sa.String(length=500)))
    op.add_column("saved_messages", sa.Column("media_mime_type", sa.String(length=120)))
    op.add_column("saved_messages", sa.Column("media_file_name", sa.String(length=255)))
    op.add_column("saved_messages", sa.Column("media_kind", sa.String(length=32)))


def downgrade() -> None:
    op.drop_column("saved_messages", "media_kind")
    op.drop_column("saved_messages", "media_file_name")
    op.drop_column("saved_messages", "media_mime_type")
    op.drop_column("saved_messages", "media_path")
