"""Shared constants (kept free of FastAPI/Pydantic imports)."""

AVATARS = ["🍜", "🍕", "🍣", "🌮", "🥐", "🍩", "🥑", "🍓"]
COLLECTION_KINDS = ("watchlist", "favorites", "tried")
MAX_ACTIVITY = 50

# (minimum stamps, rank title) - highest matching tier wins
PASSPORT_RANKS = [
    (20, "World Chef"),
    (10, "Globetrotter"),
    (5, "Traveler"),
    (1, "Tourist"),
    (0, "Newcomer"),
]
