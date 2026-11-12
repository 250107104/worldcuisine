"""In-memory data store. One module-level instance (`db`) is shared by all services.

Layout (all keyed by string ids):
  countries[country_id]        -> country dict
  dishes[dish_id]              -> dish dict
  users[user_id]               -> user dict
  collections[user_id][kind]   -> {dish_id: added_at}      kind: watchlist | favorites | tried
  ratings[user_id]             -> {dish_id: 1..5}
  reviews[review_id]           -> review dict (one per user+dish)
  explored_dishes[user_id]     -> {dish_id: first_opened_at}
  stamps[user_id]              -> {country_id: stamped_at}   (the Culinary Passport)
  activity[user_id]            -> [entry, ...] newest first
"""
from datetime import datetime, timezone


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.countries: dict = {}
        self.dishes: dict = {}
        self.users: dict = {}
        self.collections: dict = {}
        self.ratings: dict = {}
        self.reviews: dict = {}
        self.explored_dishes: dict = {}
        self.stamps: dict = {}
        self.activity: dict = {}
        self._seq = {"dish": 1000, "user": 0, "review": 0}

    def next_id(self, kind: str) -> str:
        self._seq[kind] += 1
        n = self._seq[kind]
        return {"dish": str(n), "user": f"u{n}", "review": f"r{n}"}[kind]

    def init_user_data(self, user_id: str) -> None:
        self.collections[user_id] = {"watchlist": {}, "favorites": {}, "tried": {}}
        self.ratings[user_id] = {}
        self.explored_dishes[user_id] = {}
        self.stamps[user_id] = {}
        self.activity[user_id] = []

    def drop_user_data(self, user_id: str) -> None:
        for table in (self.collections, self.ratings, self.explored_dishes, self.stamps, self.activity):
            table.pop(user_id, None)
        for rid in [r for r, v in self.reviews.items() if v["user_id"] == user_id]:
            del self.reviews[rid]


db = Store()
