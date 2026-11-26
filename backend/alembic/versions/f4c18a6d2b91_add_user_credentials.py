"""Add optional account credentials to existing user profiles.

Credentials remain nullable so existing demo/profile-only users and clients keep
working. New email/password credentials are stored in normalized/hash form.
"""
import sqlalchemy as sa
from alembic import op

revision = "f4c18a6d2b91"
down_revision = "27b20981e8b1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email", sa.String(length=320), nullable=True))
    op.add_column("users", sa.Column("password_hash", sa.String(length=255), nullable=True))
    op.create_index(
        "uq_users_email",
        "users",
        [sa.literal_column("lower(email)")],
        unique=True,
        postgresql_where=sa.text("email IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_users_email", table_name="users")
    op.drop_column("users", "password_hash")
    op.drop_column("users", "email")
