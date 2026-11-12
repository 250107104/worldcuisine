// Recipe page: recipe.html?id=52772
import { getMealById } from "./api.js";
import { isInWatchlist, toggleWatchlist, isFavorite, toggleFavorite, getRating, saveRating, markDishExplored, markCountryExplored } from "./storage.js";
import { countries } from "./data.js";
import { esc, safeUrl, createStarRating, errorBlock, loadingBlock } from "./utils.js";

const box = document.querySelector("#recipe-content");
const id = new URLSearchParams(window.location.search).get("id");

function showError() {
  errorBlock(box, "Could not load this recipe. Check your internet connection.", loadRecipe);
}

function showNotFound() {
  box.innerHTML = `<div class="state"><h1>Recipe not found</h1><p>We could not find this recipe.</p>
    <a class="btn" href="explore.html">Back to recipes</a></div>`;
}

function render(meal) {
  document.title = `${meal.name} — WorldCuisine`;

  // Instructions arrive as one text with line breaks -> one <p> per line
  const steps = meal.instructions ? meal.instructions.split(/\r?\n/).filter((line) => line.trim()) : [];

  const ingredientsHtml = meal.ingredients.length
    ? `<ul class="ingredient-list">${meal.ingredients
        .map((i) => `<li><span>${esc(i.name)}</span><span class="measure">${esc(i.measure)}</span></li>`).join("")}</ul>`
    : '<p class="state">No ingredient list available.</p>';

  const instructionsHtml = steps.length
    ? steps.map((s) => `<p>${esc(s)}</p>`).join("")
    : '<p class="state">No instructions available.</p>';

  const links = [
    safeUrl(meal.youtube) ? `<a href="${esc(meal.youtube)}" target="_blank" rel="noopener">▶ Watch tutorial on YouTube</a>` : "",
    safeUrl(meal.source) ? `<a href="${esc(meal.source)}" target="_blank" rel="noopener">Original recipe source</a>` : "",
    `<a href="reviews.html?id=${encodeURIComponent(meal.id)}">✎ Write a review</a>`,
  ].join("");

  box.innerHTML = `
    <a class="back-link" href="explore.html">← Back to recipes</a>
    <section class="recipe-top">
      <div class="photo recipe-photo">
        ${meal.image ? `<img src="${esc(meal.image)}" alt="${esc(meal.name)}" onerror="this.classList.add('img-failed')">` : ""}
      </div>
      <div class="recipe-info">
        <h1>${esc(meal.name)}</h1>
        <ul class="recipe-tags">
          ${meal.area ? `<li class="tag">Origin: ${esc(meal.area)}</li>` : ""}
          ${meal.category ? `<li class="tag">${esc(meal.category)}</li>` : ""}
        </ul>
        <div id="recipe-stars"></div>
        <div class="recipe-actions">
          <button id="watchlist-btn" class="btn" type="button" aria-pressed="false">+ Watchlist</button>
          <button id="favorite-btn" class="icon-btn" type="button" aria-pressed="false" aria-label="Add to favorites">♥</button>
        </div>
        <div class="recipe-links">${links}</div>
      </div>
    </section>
    <section class="recipe-body">
      <div><h2>Ingredients</h2>${ingredientsHtml}</div>
      <div class="instructions"><h2>Instructions</h2>${instructionsHtml}</div>
    </section>
    <p class="source-note">Recipe data: TheMealDB.</p>`;

  // Your rating (saved in LocalStorage)
  const stars = createStarRating({
    value: getRating(meal.id) || 0,
    label: "Your rating",
    onChange: (value) => saveRating(meal.id, value, meal),
  });
  document.querySelector("#recipe-stars").appendChild(stars.element);

  // Culinary Passport: opening a recipe counts as exploring the dish and its country
  markDishExplored(meal.id);
  const country = countries.find((c) => c.area === meal.area);
  if (country) markCountryExplored(country.id);

  const watchBtn = document.querySelector("#watchlist-btn");
  const favBtn = document.querySelector("#favorite-btn");

  function refreshButtons() {
    const inList = isInWatchlist(meal.id);
    watchBtn.setAttribute("aria-pressed", inList);
    watchBtn.textContent = inList ? "✓ In watchlist" : "+ Watchlist";
    const fav = isFavorite(meal.id);
    favBtn.setAttribute("aria-pressed", fav);
    favBtn.setAttribute("aria-label", fav ? "Remove from favorites" : "Add to favorites");
  }

  watchBtn.addEventListener("click", () => { toggleWatchlist(meal); refreshButtons(); });
  favBtn.addEventListener("click", () => { toggleFavorite(meal); refreshButtons(); });
  refreshButtons();
  window.addEventListener("pageshow", (e) => { if (e.persisted) refreshButtons(); });
}

async function loadRecipe() {
  if (!id) return showNotFound();
  box.innerHTML = loadingBlock("Loading recipe");
  try {
    const meal = await getMealById(id);
    if (meal) render(meal);
    else showNotFound();
  } catch (error) {
    console.error(error);
    showError();
  }
}

loadRecipe();
