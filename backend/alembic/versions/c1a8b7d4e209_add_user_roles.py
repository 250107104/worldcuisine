"""Add explicit user/admin roles for authorization."""
import sqlalchemy as sa
from alembic import op

revision = "c1a8b7d4e209"
down_revision = "f4c18a6d2b91"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("role", sa.String(length=16), server_default="user", nullable=False))
    op.create_check_constraint("ck_users_role", "users", "role IN ('user', 'admin')")


def downgrade() -> None:
    op.drop_constraint("ck_users_role", "users", type_="check")
    op.drop_column("users", "role")
