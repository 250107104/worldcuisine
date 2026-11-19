"""Initial normalized schema for catalog and user data."""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("countries", sa.Column("id", sa.String(40), primary_key=True),
                    sa.Column("name", sa.String(100), nullable=False),
                    sa.Column("cuisine", sa.String(100), nullable=False, unique=True),
                    sa.Column("iso2", sa.String(2), nullable=False),
                    sa.Column("iso3", sa.String(3), nullable=False))
    op.create_table("dishes", sa.Column("id", sa.String(40), primary_key=True),
                    sa.Column("name", sa.String(200), nullable=False),
                    sa.Column("country_id", sa.String(40), sa.ForeignKey("countries.id", ondelete="RESTRICT"), nullable=False),
                    sa.Column("category", sa.String(100)), sa.Column("image", sa.Text()),
                    sa.Column("tags", sa.JSON(), nullable=False), sa.Column("ingredients", sa.JSON(), nullable=False),
                    sa.Column("instructions", sa.Text()), sa.Column("created_at", sa.String(40)))
    op.create_index("ix_dishes_country_id", "dishes", ["country_id"])
    op.create_table("users", sa.Column("id", sa.String(40), primary_key=True),
                    sa.Column("username", sa.String(80), nullable=False),
                    sa.Column("username_key", sa.String(80), nullable=False, unique=True),
                    sa.Column("bio", sa.Text(), nullable=False), sa.Column("avatar", sa.String(20), nullable=False),
                    sa.Column("created_at", sa.String(40), nullable=False))
    op.create_table("collection_items", sa.Column("user_id", sa.String(40), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
                    sa.Column("kind", sa.String(20), primary_key=True),
                    sa.Column("dish_id", sa.String(40), sa.ForeignKey("dishes.id", ondelete="CASCADE"), primary_key=True),
                    sa.Column("added_at", sa.String(40), nullable=False),
                    sa.CheckConstraint("kind IN ('watchlist','favorites','tried')", name="ck_collection_kind"))
    op.create_table("ratings", sa.Column("user_id", sa.String(40), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
                    sa.Column("dish_id", sa.String(40), sa.ForeignKey("dishes.id", ondelete="CASCADE"), primary_key=True),
                    sa.Column("rating", sa.Integer(), nullable=False),
                    sa.CheckConstraint("rating BETWEEN 1 AND 5", name="ck_rating_range"))
    op.create_table("reviews", sa.Column("id", sa.String(40), primary_key=True),
                    sa.Column("user_id", sa.String(40), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
                    sa.Column("dish_id", sa.String(40), sa.ForeignKey("dishes.id", ondelete="CASCADE"), nullable=False),
                    sa.Column("rating", sa.Integer(), nullable=False), sa.Column("text", sa.Text(), nullable=False),
                    sa.Column("created_at", sa.String(40), nullable=False), sa.Column("updated_at", sa.String(40), nullable=False),
                    sa.UniqueConstraint("user_id", "dish_id", name="uq_review_user_dish"),
                    sa.CheckConstraint("rating BETWEEN 1 AND 5", name="ck_review_rating_range"))
    op.create_index("ix_reviews_user_id", "reviews", ["user_id"])
    op.create_index("ix_reviews_dish_id", "reviews", ["dish_id"])
    op.create_table("passport_stamps", sa.Column("user_id", sa.String(40), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
                    sa.Column("country_id", sa.String(40), sa.ForeignKey("countries.id", ondelete="CASCADE"), primary_key=True),
                    sa.Column("stamped_at", sa.String(40), nullable=False))
    op.create_table("explored_dishes", sa.Column("user_id", sa.String(40), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
                    sa.Column("dish_id", sa.String(40), sa.ForeignKey("dishes.id", ondelete="CASCADE"), primary_key=True),
                    sa.Column("first_opened_at", sa.String(40), nullable=False))
    op.create_table("activity_entries", sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
                    sa.Column("user_id", sa.String(40), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
                    sa.Column("type", sa.String(30), nullable=False), sa.Column("dish_id", sa.String(40), sa.ForeignKey("dishes.id", ondelete="SET NULL")),
                    sa.Column("dish_name", sa.String(200)), sa.Column("detail", sa.JSON()), sa.Column("at", sa.String(40), nullable=False))
    op.create_index("ix_activity_entries_user_id", "activity_entries", ["user_id"])


def downgrade():
    op.drop_table("activity_entries")
    op.drop_table("explored_dishes")
    op.drop_table("passport_stamps")
    op.drop_table("reviews")
    op.drop_table("ratings")
    op.drop_table("collection_items")
    op.drop_table("users")
    op.drop_table("dishes")
    op.drop_table("countries")
