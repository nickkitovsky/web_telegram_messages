"""Store Telegram message formatting entities.

Revision ID: 20261005_0006
Revises: 20261005_0005
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20261005_0006"
down_revision = "20261005_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "saved_messages",
        sa.Column(
            "text_entities",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("saved_messages", "text_entities")
