"""Bridge the existing Assignment 5 service store to normalized SQLAlchemy tables.

Services retain their established business rules and dictionary-facing contract;
this module hydrates that unit-of-work from SQL at request start and writes it back
atomically at request end. A process lock prevents concurrent requests from
clobbering the shared legacy service state during this compatibility transition.
"""
from threading import RLock

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db import db
from app.models import (ActivityEntry, CollectionItem, Country, Dish, ExploredDish,
                        PassportStamp, Rating, Review, User)

STATE_LOCK = RLock()


def load_state(session: Session) -> None:
    db.reset()
    for row in session.scalars(select(Country)):
        db.countries[row.id] = {"id": row.id, "name": row.name, "cuisine": row.cuisine,
                                "iso2": row.iso2, "iso3": row.iso3}
    for row in session.scalars(select(Dish)):
        db.dishes[row.id] = {"id": row.id, "name": row.name, "country_id": row.country_id,
                             "category": row.category, "image": row.image, "tags": row.tags or [],
                             "ingredients": row.ingredients or [], "instructions": row.instructions,
                             "created_at": row.created_at}
    for row in session.scalars(select(User)):
        db.users[row.id] = {"id": row.id, "username": row.username, "bio": row.bio,
                            "avatar": row.avatar, "created_at": row.created_at}
        db.init_user_data(row.id)
    for row in session.scalars(select(CollectionItem)):
        db.collections[row.user_id][row.kind][row.dish_id] = row.added_at
    for row in session.scalars(select(Rating)):
        db.ratings[row.user_id][row.dish_id] = row.rating
    for row in session.scalars(select(Review)):
        db.reviews[row.id] = {"id": row.id, "user_id": row.user_id, "dish_id": row.dish_id,
                              "rating": row.rating, "text": row.text,
                              "created_at": row.created_at, "updated_at": row.updated_at}
    for row in session.scalars(select(PassportStamp)):
        db.stamps[row.user_id][row.country_id] = row.stamped_at
    for row in session.scalars(select(ExploredDish)):
        db.explored_dishes[row.user_id][row.dish_id] = row.first_opened_at
    activities = session.scalars(select(ActivityEntry).order_by(ActivityEntry.at.desc(), ActivityEntry.id.desc()))
    for row in activities:
        db.activity[row.user_id].append({"type": row.type, "dish_id": row.dish_id,
                                         "dish_name": row.dish_name, "detail": row.detail, "at": row.at})

    user_numbers = [int(uid[1:]) for uid in db.users if uid.startswith("u") and uid[1:].isdigit()]
    review_numbers = [int(rid[1:]) for rid in db.reviews if rid.startswith("r") and rid[1:].isdigit()]
    db._seq["user"] = max(user_numbers, default=0)
    db._seq["review"] = max(review_numbers, default=0)


def save_state(session: Session) -> None:
    # Delete in FK-safe order, then insert a complete consistent snapshot in one transaction.
    for model in (ActivityEntry, ExploredDish, PassportStamp, Review, Rating, CollectionItem,
                  Dish, User, Country):
        session.execute(delete(model))
    session.flush()

    session.add_all(Country(id=cid, name=c["name"], cuisine=c["cuisine"], iso2=c["iso2"], iso3=c["iso3"])
                    for cid, c in db.countries.items())
    session.flush()
    session.add_all(Dish(id=did, name=d["name"], country_id=d["country_id"], category=d.get("category"),
                         image=d.get("image"), tags=d.get("tags", []), ingredients=d.get("ingredients", []),
                         instructions=d.get("instructions"), created_at=d.get("created_at"))
                    for did, d in db.dishes.items())
    session.add_all(User(id=uid, username=u["username"], username_key=u["username"].casefold(),
                         bio=u.get("bio", ""), avatar=u.get("avatar", "🍜"), created_at=u["created_at"])
                    for uid, u in db.users.items())
    session.flush()

    for uid, collections in db.collections.items():
        for kind, dishes in collections.items():
            session.add_all(CollectionItem(user_id=uid, kind=kind, dish_id=did, added_at=added_at)
                            for did, added_at in dishes.items())
    for uid, ratings in db.ratings.items():
        session.add_all(Rating(user_id=uid, dish_id=did, rating=rating) for did, rating in ratings.items())
    session.add_all(Review(id=rid, user_id=r["user_id"], dish_id=r["dish_id"], rating=r["rating"],
                           text=r["text"], created_at=r["created_at"], updated_at=r["updated_at"])
                    for rid, r in db.reviews.items())
    for uid, stamps in db.stamps.items():
        session.add_all(PassportStamp(user_id=uid, country_id=cid, stamped_at=at) for cid, at in stamps.items())
    for uid, explored in db.explored_dishes.items():
        session.add_all(ExploredDish(user_id=uid, dish_id=did, first_opened_at=at) for did, at in explored.items())
    for uid, entries in db.activity.items():
        session.add_all(ActivityEntry(user_id=uid, type=e["type"], dish_id=e.get("dish_id"),
                                      dish_name=e.get("dish_name"), detail=e.get("detail"), at=e["at"])
                        for e in entries)
    session.flush()
