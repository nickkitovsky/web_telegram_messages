"""Create users, Telegram auth, messages and tags.

Revision ID: 20261005_0001
Revises:
"""

import sqlalchemy as sa

from alembic import op

revision = "20261005_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"])
    op.create_index("ix_user_sessions_token_hash", "user_sessions", ["token_hash"], unique=True)
    op.create_index("ix_user_sessions_expires_at", "user_sessions", ["expires_at"])

    op.create_table(
        "telegram_auth",
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("encrypted_session", sa.Text()),
        sa.Column("pending_phone", sa.String(length=32)),
        sa.Column("phone_code_hash", sa.Text()),
        sa.Column("password_required", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("connected_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.UniqueConstraint("user_id", "name", name="uq_tags_user_name"),
    )
    op.create_index("ix_tags_user_id", "tags", ["user_id"])

    op.create_table(
        "saved_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("telegram_message_id", sa.BigInteger(), nullable=False),
        sa.Column("text", sa.Text(), server_default="", nullable=False),
        sa.Column("title", sa.String(length=240)),
        sa.Column("message_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("channel", sa.String(length=255)),
        sa.Column("archived", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("classification_confidence", sa.Float()),
        sa.Column("classification_candidates", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("classification_pending", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.UniqueConstraint(
            "user_id",
            "telegram_message_id",
            name="uq_saved_messages_user_telegram_id",
        ),
    )
    op.create_index("ix_saved_messages_user_id", "saved_messages", ["user_id"])
    op.create_index(
        "ix_saved_messages_user_date",
        "saved_messages",
        ["user_id", "message_date"],
    )

    op.create_table(
        "saved_message_tags",
        sa.Column(
            "message_id",
            sa.Integer(),
            sa.ForeignKey("saved_messages.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "tag_id",
            sa.Integer(),
            sa.ForeignKey("tags.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )


def downgrade() -> None:
    op.drop_table("saved_message_tags")
    op.drop_index("ix_saved_messages_user_date", table_name="saved_messages")
    op.drop_index("ix_saved_messages_user_id", table_name="saved_messages")
    op.drop_table("saved_messages")
    op.drop_index("ix_tags_user_id", table_name="tags")
    op.drop_table("tags")
    op.drop_table("telegram_auth")
    op.drop_index("ix_user_sessions_expires_at", table_name="user_sessions")
    op.drop_index("ix_user_sessions_token_hash", table_name="user_sessions")
    op.drop_index("ix_user_sessions_user_id", table_name="user_sessions")
    op.drop_table("user_sessions")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
