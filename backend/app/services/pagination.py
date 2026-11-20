"""One paging helper so every list endpoint returns the same {items, total, limit, offset} shape."""


def paginate(items: list, limit: int = 20, offset: int = 0) -> dict:
    return {"items": items[offset:offset + limit], "total": len(items), "limit": limit, "offset": offset}
