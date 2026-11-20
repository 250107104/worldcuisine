"""Serve only the site's public pages and assets alongside FastAPI."""
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[2]
PAGES = {"index", "country", "explore", "recipe", "watchlist", "reviews", "profile"}

router = APIRouter()


@router.get("/{page}.html", include_in_schema=False)
def website_page(page: str):
    if page not in PAGES:
        raise HTTPException(status_code=404, detail="Page not found")
    return FileResponse(ROOT / f"{page}.html")


def attach_website(app) -> None:
    app.include_router(router)
    for directory in ("css", "js", "data"):
        app.mount(f"/{directory}", StaticFiles(directory=ROOT / directory), name=directory)
