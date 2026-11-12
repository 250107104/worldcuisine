// Explore page: search + filters + recipe grid.
import {
  searchMeals, getMealsByCountry, getMealsByCategory,
  getRandomMeals, getMealById, getAreas, getCategories,
} from "./api.js";
import { isInWatchlist, toggleWatchlist, isFavorite, toggleFavorite, getRating } from "./storage.js";
import { esc, recipeUrl, errorBlock, loadingBlock } from "./utils.js";

const PAGE_SIZE = 12;

const $ = (selector) => document.querySelector(selector);
const form = $("#filter-form");
const grid = $("#recipe-grid");
const status = $("#status");
const loadMoreBtn = $("#load-more");

let allResults = [];       // meals for the current search, in the order the API gave them
let results = [];          // same meals, sorted for display
let shown = 0;             // how many cards are on the screen
let searchId = 0;          // ignores old answers if the user searches again quickly
const mealsById = new Map(); // newest known data for every meal on screen

/* ---------- Filters ---------- */
function getFilters() {
  const data = new FormData(form);
  return {
    q: data.get("q").trim(),
    area: data.get("area"),
    category: data.get("category"),
    sort: data.get("sort"),
  };
}

async function loadFilterOptions() {
  const [areas, categories] = await Promise.allSettled([getAreas(), getCategories()]);
  const fill = (select, result) => {
    if (result.status !== "fulfilled") return;
    const current = select.value;
    const existing = [...select.options].map((o) => o.value);
    const newOptions = result.value.filter((v) => !existing.includes(v));
    select.insertAdjacentHTML("beforeend", newOptions.map((v) => `<option value="${esc(v)}">${esc(v)}</option>`).join(""));
    select.value = current;
  };
  fill($("#area-select"), areas);
  fill($("#category-select"), categories);

  if (areas.status === "rejected" || categories.status === "rejected") {
    const note = $("#filter-note");
    note.hidden = false;
    note.textContent = "Some filter options could not be loaded. Search still works.";
  }
}

// Reads ?q=...&area=Italian&category=Seafood from the address bar
function applyUrlParams() {
  const params = new URLSearchParams(window.location.search);
  ["q", "area", "category"].forEach((name) => {
    const value = params.get(name);
    if (!value) return;
    const field = form.elements[name];
    // a select needs the option to exist before we can choose it
    if (field.tagName === "SELECT" && ![...field.options].some((o) => o.value === value)) {
      field.insertAdjacentHTML("beforeend", `<option value="${esc(value)}">${esc(value)}</option>`);
    }
    field.value = value;
  });
}

/* ---------- Loading data ---------- */
// Keeps only meals that appear in every list (TheMealDB cannot combine filters itself)
function intersect(lists) {
  const [first, ...others] = lists;
  return first
    .filter((meal) => others.every((list) => list.some((m) => m.id === meal.id)))
    .map((meal) => {
      // prefer the version of the meal that has the most details
      const best = lists.map((l) => l.find((m) => m.id === meal.id)).find((m) => m.area || m.category);
      return best || meal;
    });
}

async function fetchResults(filters) {
  const requests = [];
  if (filters.q) requests.push(searchMeals(filters.q));
  if (filters.area) requests.push(getMealsByCountry(filters.area));
  if (filters.category) requests.push(getMealsByCategory(filters.category));

  if (requests.length === 0) return { meals: await getRandomMeals(PAGE_SIZE), isRandom: true };
  return { meals: intersect(await Promise.all(requests)), isRandom: false };
}

async function runSearch() {
  const myId = ++searchId;
  const filters = getFilters();

  grid.innerHTML = "";
  loadMoreBtn.hidden = true;
  $("#results-title").textContent = "";
  status.innerHTML = loadingBlock("Loading recipes");

  try {
    const { meals, isRandom } = await fetchResults(filters);
    if (myId !== searchId) return;

    allResults = meals;
    meals.forEach((m) => mealsById.set(m.id, m));
    sortResults(filters.sort);
    status.innerHTML = "";

    if (results.length === 0) {
      status.innerHTML = `<div class="state"><p>No recipes found. Try different words or fewer filters.</p>
        <button id="empty-clear" class="btn btn-outline" type="button">Clear filters</button></div>`;
      $("#empty-clear").addEventListener("click", clearFilters);
      return;
    }

    $("#results-title").textContent = isRandom ? "Random picks for you" : `${results.length} recipe${results.length === 1 ? "" : "s"} found`;
    shown = 0;
    renderMore();
  } catch (error) {
    if (myId !== searchId) return;
    console.error(error);
    errorBlock(status, "Could not load recipes. Check your internet connection.", runSearch);
  }
}

/* ---------- Sorting ---------- */
function sortResults(sort) {
  results = [...allResults]; // start again from the API order, so "Default" works
  if (sort === "name-asc") results.sort((a, b) => a.name.localeCompare(b.name));
  if (sort === "name-desc") results.sort((a, b) => b.name.localeCompare(a.name));
  if (sort === "rating") {
    results.sort((a, b) => (getRating(b.id) || 0) - (getRating(a.id) || 0) || a.name.localeCompare(b.name));
  }
}

/* ---------- Cards ---------- */
function metaHtml(meal) {
  const rating = getRating(meal.id);
  return `${meal.area ? `<span class="card-tag">${esc(meal.area)}</span>` : ""}
          ${meal.category ? `<span class="card-tag">${esc(meal.category)}</span>` : ""}
          ${rating ? `<span class="rating" aria-label="Rating ${rating} out of 5">★ ${rating}</span>` : ""}`;
}

function cardHtml(meal) {
  const url = recipeUrl(meal.id);
  return `
    <article class="card recipe-card" data-id="${esc(meal.id)}">
      <a class="photo" href="${url}" tabindex="-1" aria-hidden="true">
        <img src="${esc(meal.image)}" alt="" loading="lazy" onerror="this.classList.add('img-failed')">
      </a>
      <div class="card-body">
        <div class="card-meta">${metaHtml(meal)}</div>
        <h3><a href="${url}">${esc(meal.name)}</a></h3>
        <div class="card-actions">
          <button class="btn btn-small" type="button" data-action="watchlist" aria-pressed="false">+ Watchlist</button>
          <button class="icon-btn" type="button" data-action="favorite" aria-pressed="false" aria-label="Add to favorites">♥</button>
          <a class="btn btn-small btn-outline" href="${url}">View Recipe</a>
        </div>
      </div>
    </article>`;
}

function refreshButtons(card) {
  const id = card.dataset.id;
  const inList = isInWatchlist(id);
  const watchBtn = card.querySelector('[data-action="watchlist"]');
  watchBtn.setAttribute("aria-pressed", inList);
  watchBtn.textContent = inList ? "✓ In watchlist" : "+ Watchlist";

  const fav = isFavorite(id);
  const favBtn = card.querySelector('[data-action="favorite"]');
  favBtn.setAttribute("aria-pressed", fav);
  favBtn.setAttribute("aria-label", fav ? "Remove from favorites" : "Add to favorites");
}

function renderMore() {
  const batch = results.slice(shown, shown + PAGE_SIZE);
  grid.insertAdjacentHTML("beforeend", batch.map(cardHtml).join(""));
  shown += batch.length;
  loadMoreBtn.hidden = shown >= results.length;

  batch.forEach((meal) => {
    refreshButtons(grid.querySelector(`[data-id="${CSS.escape(meal.id)}"]`));
    enrichMeal(meal);
  });
}

// Filter lists only contain name + image. We load the rest (country, category) in the background.
async function enrichMeal(meal) {
  if (meal.area && meal.category) return;
  try {
    const full = await getMealById(meal.id);
    if (!full) return;
    mealsById.set(full.id, full);
    const card = grid.querySelector(`[data-id="${CSS.escape(full.id)}"]`);
    if (card) card.querySelector(".card-meta").innerHTML = metaHtml(full);
  } catch (error) {
    // not important: the card simply stays without extra info
  }
}

/* ---------- Events ---------- */
function clearFilters() {
  form.reset();
  history.replaceState(null, "", "explore.html");
  runSearch();
}

form.addEventListener("submit", (e) => { e.preventDefault(); runSearch(); });
$("#clear-btn").addEventListener("click", clearFilters);
$("#area-select").addEventListener("change", runSearch);
$("#category-select").addEventListener("change", runSearch);

// Sorting does not need new data, so we only re-draw the cards
$("#sort-select").addEventListener("change", () => {
  sortResults(getFilters().sort);
  grid.innerHTML = "";
  shown = 0;
  renderMore();
});

loadMoreBtn.addEventListener("click", renderMore);

// One listener for all buttons inside the grid (event delegation)
grid.addEventListener("click", async (e) => {
  const button = e.target.closest("button[data-action]");
  if (!button) return;
  const card = button.closest(".recipe-card");
  let meal = mealsById.get(card.dataset.id);
  if (!meal) return;

  // Filter lists only have name + image. Load the details first, so the saved dish
  // also has its country and category (needed by the Watchlist and Passport pages).
  if (!meal.area || !meal.category) {
    try {
      const full = await getMealById(meal.id);
      if (full) { meal = full; mealsById.set(full.id, full); }
    } catch (error) {
      // offline: we still save what we have
    }
  }

  if (button.dataset.action === "watchlist") toggleWatchlist(meal);
  if (button.dataset.action === "favorite") toggleFavorite(meal);
  refreshButtons(card);
});

// Coming back with the browser's Back button can show an old page: re-read LocalStorage
window.addEventListener("pageshow", (e) => {
  if (e.persisted) grid.querySelectorAll(".recipe-card").forEach(refreshButtons);
});

/* ---------- Start ---------- */
applyUrlParams();
loadFilterOptions();
runSearch();
