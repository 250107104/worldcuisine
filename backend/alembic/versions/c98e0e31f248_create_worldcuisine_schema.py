"""Create WorldCuisine schema

Revision ID: c98e0e31f248
Revises: 
Create Date: 2026-11-19 20:44:08.624241

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c98e0e31f248'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the relational schema and import the original Assignment 5 catalog."""
    op.execute("CREATE SEQUENCE dish_ids START WITH 1028")
    op.execute("CREATE SEQUENCE user_ids START WITH 2")
    op.execute("CREATE SEQUENCE review_ids START WITH 1")

    op.create_table('countries',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('iso2', sa.String(length=2), nullable=False),
        sa.Column('iso3', sa.String(length=3), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('cuisine', sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('iso2'),
        sa.UniqueConstraint('iso3'),
    )
    op.create_table('users',
        sa.Column('id', sa.String(length=32), server_default=sa.text("concat('u', nextval('user_ids'))"), nullable=False),
        sa.Column('username', sa.String(length=24), nullable=False),
        sa.Column('bio', sa.String(length=160), nullable=False),
        sa.Column('avatar', sa.String(length=8), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('uq_users_username', 'users', [sa.literal_column('lower(username)')], unique=True)
    op.create_table('dishes',
        sa.Column('id', sa.String(length=32), server_default=sa.text("nextval('dish_ids')"), nullable=False),
        sa.Column('country_id', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=40), nullable=False),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('ingredients', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('image', sa.Text(), nullable=True),
        sa.Column('instructions', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['country_id'], ['countries.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_dishes_country_id'), 'dishes', ['country_id'], unique=False)
    op.create_index('uq_dishes_country_name', 'dishes', ['country_id', sa.literal_column('lower(name)')], unique=True)
    op.create_table('passport_stamps',
        sa.Column('user_id', sa.String(length=32), nullable=False),
        sa.Column('country_id', sa.String(length=32), nullable=False),
        sa.Column('stamped_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['country_id'], ['countries.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'country_id'),
    )
    op.create_index(op.f('ix_passport_stamps_country_id'), 'passport_stamps', ['country_id'], unique=False)
    op.create_table('activity',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column('user_id', sa.String(length=32), nullable=False),
        sa.Column('dish_id', sa.String(length=32), nullable=True),
        sa.Column('dish_name', sa.String(length=100), nullable=True),
        sa.Column('type', sa.String(length=12), nullable=False),
        sa.Column('detail', sa.Integer(), nullable=True),
        sa.Column('at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("type IN ('watchlist', 'favorite', 'tried', 'rating', 'review')", name='ck_activity_type'),
        sa.ForeignKeyConstraint(['dish_id'], ['dishes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_activity_dish_id'), 'activity', ['dish_id'], unique=False)
    op.create_index(op.f('ix_activity_user_id'), 'activity', ['user_id'], unique=False)
    op.create_table('collection_entries',
        sa.Column('user_id', sa.String(length=32), nullable=False),
        sa.Column('kind', sa.String(length=10), nullable=False),
        sa.Column('dish_id', sa.String(length=32), nullable=False),
        sa.Column('added_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("kind IN ('watchlist', 'favorites', 'tried')", name='ck_collection_kind'),
        sa.ForeignKeyConstraint(['dish_id'], ['dishes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'kind', 'dish_id'),
    )
    op.create_index(op.f('ix_collection_entries_dish_id'), 'collection_entries', ['dish_id'], unique=False)
    op.create_table('explored_dishes',
        sa.Column('user_id', sa.String(length=32), nullable=False),
        sa.Column('dish_id', sa.String(length=32), nullable=False),
        sa.Column('explored_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['dish_id'], ['dishes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'dish_id'),
    )
    op.create_index(op.f('ix_explored_dishes_dish_id'), 'explored_dishes', ['dish_id'], unique=False)
    op.create_table('ratings',
        sa.Column('user_id', sa.String(length=32), nullable=False),
        sa.Column('dish_id', sa.String(length=32), nullable=False),
        sa.Column('stars', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('stars BETWEEN 1 AND 5', name='ck_rating_stars'),
        sa.ForeignKeyConstraint(['dish_id'], ['dishes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'dish_id'),
    )
    op.create_index(op.f('ix_ratings_dish_id'), 'ratings', ['dish_id'], unique=False)
    op.create_table('reviews',
        sa.Column('id', sa.String(length=32), server_default=sa.text("concat('r', nextval('review_ids'))"), nullable=False),
        sa.Column('user_id', sa.String(length=32), nullable=False),
        sa.Column('dish_id', sa.String(length=32), nullable=False),
        sa.Column('text', sa.String(length=1000), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['dish_id'], ['dishes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id', 'dish_id'], ['ratings.user_id', 'ratings.dish_id'], name='fk_review_rating', initially='DEFERRED', deferrable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_reviews_dish_id'), 'reviews', ['dish_id'], unique=False)
    op.create_index(op.f('ix_reviews_user_id'), 'reviews', ['user_id'], unique=False)
    op.create_index('uq_review_user_dish', 'reviews', ['user_id', 'dish_id'], unique=True)
    op.execute("ALTER SEQUENCE dish_ids OWNED BY dishes.id")
    op.execute("ALTER SEQUENCE user_ids OWNED BY users.id")
    op.execute("ALTER SEQUENCE review_ids OWNED BY reviews.id")

    users = sa.table(
        "users", sa.column("id"), sa.column("username"), sa.column("bio"),
        sa.column("avatar"), sa.column("created_at"),
    )
    op.execute(users.insert().values(
        id="u1", username="Food Explorer", bio="", avatar="🍜",
        created_at=sa.func.current_timestamp(),
    ))


def downgrade() -> None:
    """Downgrade schema."""
    for table in ("reviews", "ratings", "explored_dishes", "collection_entries", "activity",
                  "passport_stamps", "dishes", "users", "countries"):
        op.drop_table(table)
