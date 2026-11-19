"""SQLAlchemy tables for persistent WorldCuisine user and catalog data."""
from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON


class Base(DeclarativeBase):
    pass


class Country(Base):
    __tablename__ = "countries"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    cuisine: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    iso2: Mapped[str] = mapped_column(String(2), nullable=False)
    iso3: Mapped[str] = mapped_column(String(3), nullable=False)
    dishes: Mapped[list["Dish"]] = relationship(back_populates="country")


class Dish(Base):
    __tablename__ = "dishes"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)  # TheMealDB idMeal
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    country_id: Mapped[str] = mapped_column(ForeignKey("countries.id", ondelete="RESTRICT"), index=True)
    category: Mapped[str | None] = mapped_column(String(100))
    image: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    ingredients: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    instructions: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str | None] = mapped_column(String(40))
    country: Mapped[Country] = relationship(back_populates="dishes")
    collection_items: Mapped[list["CollectionItem"]] = relationship(back_populates="dish", cascade="all, delete-orphan")
    ratings: Mapped[list["Rating"]] = relationship(back_populates="dish", cascade="all, delete-orphan")
    reviews: Mapped[list["Review"]] = relationship(back_populates="dish", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    username: Mapped[str] = mapped_column(String(80), nullable=False)
    username_key: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    bio: Mapped[str] = mapped_column(Text, nullable=False, default="")
    avatar: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)
    collections: Mapped[list["CollectionItem"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    ratings: Mapped[list["Rating"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    reviews: Mapped[list["Review"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    stamps: Mapped[list["PassportStamp"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    explored_dishes: Mapped[list["ExploredDish"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    activity: Mapped[list["ActivityEntry"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class CollectionItem(Base):
    __tablename__ = "collection_items"
    __table_args__ = (CheckConstraint("kind IN ('watchlist','favorites','tried')", name="ck_collection_kind"),)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    kind: Mapped[str] = mapped_column(String(20), primary_key=True)
    dish_id: Mapped[str] = mapped_column(ForeignKey("dishes.id", ondelete="CASCADE"), primary_key=True)
    added_at: Mapped[str] = mapped_column(String(40), nullable=False)
    user: Mapped[User] = relationship(back_populates="collections")
    dish: Mapped[Dish] = relationship(back_populates="collection_items")


class Rating(Base):
    __tablename__ = "ratings"
    __table_args__ = (CheckConstraint("rating BETWEEN 1 AND 5", name="ck_rating_range"),)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    dish_id: Mapped[str] = mapped_column(ForeignKey("dishes.id", ondelete="CASCADE"), primary_key=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    user: Mapped[User] = relationship(back_populates="ratings")
    dish: Mapped[Dish] = relationship(back_populates="ratings")


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (UniqueConstraint("user_id", "dish_id", name="uq_review_user_dish"),
                      CheckConstraint("rating BETWEEN 1 AND 5", name="ck_review_rating_range"))
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    dish_id: Mapped[str] = mapped_column(ForeignKey("dishes.id", ondelete="CASCADE"), index=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(40), nullable=False)
    user: Mapped[User] = relationship(back_populates="reviews")
    dish: Mapped[Dish] = relationship(back_populates="reviews")


class PassportStamp(Base):
    __tablename__ = "passport_stamps"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    country_id: Mapped[str] = mapped_column(ForeignKey("countries.id", ondelete="CASCADE"), primary_key=True)
    stamped_at: Mapped[str] = mapped_column(String(40), nullable=False)
    user: Mapped[User] = relationship(back_populates="stamps")


class ExploredDish(Base):
    __tablename__ = "explored_dishes"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    dish_id: Mapped[str] = mapped_column(ForeignKey("dishes.id", ondelete="CASCADE"), primary_key=True)
    first_opened_at: Mapped[str] = mapped_column(String(40), nullable=False)
    user: Mapped[User] = relationship(back_populates="explored_dishes")


class ActivityEntry(Base):
    __tablename__ = "activity_entries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    dish_id: Mapped[str | None] = mapped_column(ForeignKey("dishes.id", ondelete="SET NULL"))
    dish_name: Mapped[str | None] = mapped_column(String(200))
    detail: Mapped[int | str | None] = mapped_column(JSON)
    at: Mapped[str] = mapped_column(String(40), nullable=False)
    user: Mapped[User] = relationship(back_populates="activity")
