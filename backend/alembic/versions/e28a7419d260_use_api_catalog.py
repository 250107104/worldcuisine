"""Allow full API recipe names."""
import sqlalchemy as sa
from alembic import op

revision = "e28a7419d260"
down_revision = "c98e0e31f248"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("dishes", "name", existing_type=sa.String(100), type_=sa.Text())
    op.alter_column("activity", "dish_name", existing_type=sa.String(100), type_=sa.Text())


def downgrade() -> None:
    # Reverting the schema leaves imported records in place. PostgreSQL rejects overlong names.
    op.alter_column("activity", "dish_name", existing_type=sa.Text(), type_=sa.String(100))
    op.alter_column("dishes", "name", existing_type=sa.Text(), type_=sa.String(100))
