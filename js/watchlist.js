// Watchlist + Favorites page
import {
  getWatchlist, getFavorites, removeFromWatchlist, moveToFavorites, removeFavorite,
  isTried, toggleTried, getRating, saveRating,
} from "./storage.js";
import { esc, recipeUrl, createStarRating } from "./utils.js";

const $ = (selector) => document.querySelector(selector);
const watchGrid = $("#watchlist-grid");
const favGrid = $("#favorites-grid");
const sortSelect = $("#wl-sort");

function sortItems(items, sort) {
  const list = [...items];
  const byName = (a, b) => a.name.localeCompare(b.name);
  if (sort === "newest") list.sort((a, b) => (b.addedAt || "").localeCompare(a.addedAt || ""));
  if (sort === "oldest") list.sort((a, b) => (a.addedAt || "").localeCompare(b.addedAt || ""));
  if (sort === "name-asc") list.sort(byName);
  if (sort === "name-desc") list.sort((a, b) => byName(b, a));
  if (sort === "not-tried") list.sort((a, b) => isTried(a.id) - isTried(b.id) || byName(a, b));
  if (sort === "rating") list.sort((a, b) => (getRating(b.id) || 0) - (getRating(a.id) || 0) || byName(a, b));
  return list;
}

function cardHtml(item, kind) {
  const url = recipeUrl(item.id);
  const tried = isTried(item.id);

  const actions = kind === "watchlist"
    ? `<button class="btn btn-small" type="button" data-action="tried" aria-pressed="${tried}">${tried ? "✓ Tried" : "Mark as tried"}</button>
       <button class="btn btn-small btn-outline" type="button" data-action="to-favorites">♥ Move to Favorites</button>
       <button class="btn btn-small btn-outline" type="button" data-action="remove-watchlist">Remove</button>`
    : '<button class="btn btn-small btn-outline" type="button" data-action="remove-favorite">Remove from Favorites</button>';

  return `
    <article class="card user-card" data-id="${esc(item.id)}">
      <a class="photo" href="${url}" tabindex="-1" aria-hidden="true">
        ${item.image ? `<img src="${esc(item.image)}" alt="" loading="lazy" onerror="this.classList.add('img-failed')">` : ""}
      </a>
      <div class="card-body">
        <div class="card-meta">
          ${item.area ? `<span class="card-tag">${esc(item.area)}</span>` : ""}
          ${item.category ? `<span class="card-tag">${esc(item.category)}</span>` : ""}
        </div>
        <h3><a href="${url}">${esc(item.name)}</a></h3>
        <div class="card-stars"></div>
        <div class="card-actions">
          ${actions}
          <a class="btn btn-small btn-outline" href="${url}">View Recipe</a>
        </div>
      </div>
    </article>`;
}

function renderGrid(grid, items, kind, emptyText) {
  if (items.length === 0) {
    grid.innerHTML = `<div class="state"><p>${emptyText}</p><a class="btn btn-outline" href="explore.html">Explore recipes</a></div>`;
    return;
  }
  grid.innerHTML = items.map((item) => cardHtml(item, kind)).join("");

  // add the clickable stars to every card
  grid.querySelectorAll(".user-card").forEach((card) => {
    const item = items.find((m) => m.id === card.dataset.id);
    const stars = createStarRating({
      value: getRating(item.id) || 0,
      label: `Your rating for ${item.name}`,
      onChange: (value) => {
        saveRating(item.id, value, item);
        if (sortSelect.value === "rating") render();
      },
    });
    card.querySelector(".card-stars").appendChild(stars.element);
  });
}

function render() {
  try {
    draw();
  } catch (error) {
    console.error(error);
    const message = '<div class="state error"><p>Could not show your saved dishes. Open the browser console (F12) for details.</p></div>';
    watchGrid.innerHTML = message;
    favGrid.innerHTML = message;
  }
}

function draw() {
  const watchlist = sortItems(getWatchlist(), sortSelect.value);
  const favorites = getFavorites();
  $("#wl-count").textContent = `(${watchlist.length})`;
  $("#fav-count").textContent = `(${favorites.length})`;
  renderGrid(watchGrid, watchlist, "watchlist", "Your watchlist is empty. Find a dish you want to try!");
  renderGrid(favGrid, favorites, "favorites", "No favorites yet. Press ♥ on a recipe to save it here.");
}

// One listener per grid handles every button (event delegation)
watchGrid.addEventListener("click", (e) => {
  const button = e.target.closest("button[data-action]");
  if (!button) return;
  const id = button.closest(".user-card").dataset.id;
  const item = getWatchlist().find((m) => m.id === id);

  if (button.dataset.action === "tried") toggleTried(item);
  if (button.dataset.action === "to-favorites") moveToFavorites(id);
  if (button.dataset.action === "remove-watchlist") removeFromWatchlist(id);
  render();
});

favGrid.addEventListener("click", (e) => {
  const button = e.target.closest('button[data-action="remove-favorite"]');
  if (!button) return;
  removeFavorite(button.closest(".user-card").dataset.id);
  render();
});

sortSelect.addEventListener("change", render);
render();
