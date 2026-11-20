"""Keep source and video links supplied by TheMealDB."""
import sqlalchemy as sa
from alembic import op

revision = "27b20981e8b1"
down_revision = "e28a7419d260"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("dishes", sa.Column("youtube", sa.Text(), nullable=True))
    op.add_column("dishes", sa.Column("source", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("dishes", "source")
    op.drop_column("dishes", "youtube")
