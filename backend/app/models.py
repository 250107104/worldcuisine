"""SQLAlchemy mappings for the WorldCuisine catalog and user workflows."""
from datetime import datetime

from sqlalchemy import (
    BigInteger, CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint,
    Identity, Index, Integer, Sequence, String, Text, func, text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.db import utcnow


class Base(DeclarativeBase):
    type_annotation_map = {datetime: DateTime(timezone=True)}


dish_ids = Sequence("dish_ids", start=1028, metadata=Base.metadata)


class Country(Base):
    __tablename__ = "countries"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    iso2: Mapped[str] = mapped_column(String(2), unique=True)
    iso3: Mapped[str] = mapped_column(String(3), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    cuisine: Mapped[str] = mapped_column(String(100))
    dishes: Mapped[list["Dish"]] = relationship(back_populates="country", passive_deletes="all")


class Dish(Base):
    __tablename__ = "dishes"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, server_default=dish_ids.next_value())
    country_id: Mapped[str] = mapped_column(ForeignKey("countries.id", ondelete="RESTRICT"), index=True)
    name: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(40))
    tags: Mapped[list[str]] = mapped_column(JSONB, default=list)
    ingredients: Mapped[list[dict]] = mapped_column(JSONB)
    image: Mapped[str | None] = mapped_column(Text)
    instructions: Mapped[str] = mapped_column(Text)
    youtube: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    country: Mapped[Country] = relationship(back_populates="dishes", lazy="joined")
    __table_args__ = (Index("uq_dishes_country_name", country_id, func.lower(name), unique=True),)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, server_default=text("concat('u', nextval('user_ids'::regclass))")
    )
    username: Mapped[str] = mapped_column(String(24))
    email: Mapped[str | None] = mapped_column(String(320))
    # Store only an encoded Argon2id hash, never a user's submitted password.
    password_hash: Mapped[str | None] = mapped_column(String(255))
    bio: Mapped[str] = mapped_column(String(160))
    avatar: Mapped[str] = mapped_column(String(8))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    __table_args__ = (
        Index("uq_users_username", func.lower(username), unique=True),
        Index("uq_users_email", func.lower(email), unique=True, postgresql_where=email.is_not(None)),
    )


class CollectionEntry(Base):
    __tablename__ = "collection_entries"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    kind: Mapped[str] = mapped_column(String(10), primary_key=True)
    dish_id: Mapped[str] = mapped_column(
        ForeignKey("dishes.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    added_at: Mapped[datetime] = mapped_column(default=utcnow)
    dish: Mapped[Dish] = relationship(lazy="joined")

    __table_args__ = (
        CheckConstraint("kind IN ('watchlist', 'favorites', 'tried')", name="ck_collection_kind"),
    )


class Rating(Base):
    __tablename__ = "ratings"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    dish_id: Mapped[str] = mapped_column(
        ForeignKey("dishes.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    stars: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    dish: Mapped[Dish] = relationship(lazy="joined")

    __table_args__ = (CheckConstraint("stars BETWEEN 1 AND 5", name="ck_rating_stars"),)


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, server_default=text("concat('r', nextval('review_ids'::regclass))")
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    dish_id: Mapped[str] = mapped_column(ForeignKey("dishes.id", ondelete="CASCADE"), index=True)
    text: Mapped[str] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow)
    user: Mapped[User] = relationship(lazy="joined")
    dish: Mapped[Dish] = relationship(lazy="joined")
    rating: Mapped[Rating] = relationship(lazy="joined", viewonly=True)

    __table_args__ = (
        Index("uq_review_user_dish", user_id, dish_id, unique=True),
        ForeignKeyConstraint(
            ["user_id", "dish_id"], ["ratings.user_id", "ratings.dish_id"],
            name="fk_review_rating", deferrable=True, initially="DEFERRED",
        ),
    )


class ExploredDish(Base):
    __tablename__ = "explored_dishes"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    dish_id: Mapped[str] = mapped_column(
        ForeignKey("dishes.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    explored_at: Mapped[datetime] = mapped_column(default=utcnow)


class PassportStamp(Base):
    __tablename__ = "passport_stamps"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    country_id: Mapped[str] = mapped_column(
        ForeignKey("countries.id", ondelete="RESTRICT"), primary_key=True, index=True
    )
    stamped_at: Mapped[datetime] = mapped_column(default=utcnow)


class Activity(Base):
    __tablename__ = "activity"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    dish_id: Mapped[str | None] = mapped_column(ForeignKey("dishes.id", ondelete="CASCADE"), index=True)
    dish_name: Mapped[str | None] = mapped_column(Text)
    type: Mapped[str] = mapped_column(String(12))
    detail: Mapped[int | None] = mapped_column(Integer)
    at: Mapped[datetime] = mapped_column(default=utcnow)

    __table_args__ = (
        CheckConstraint("type IN ('watchlist', 'favorite', 'tried', 'rating', 'review')", name="ck_activity_type"),
    )
