// Country page: country.html?c=italy
import { getCountryById } from "./data.js";
import { getMealsByCountry, getPopularIngredients, getCuisineSummary } from "./api.js";
import { markCountryExplored } from "./storage.js";
import { esc, exploreCountryUrl, flagImg, photoBox, dishCard, errorBlock, loadingBlock } from "./utils.js";

const box = document.querySelector("#country-content");

async function initCountry() {
  const id = new URLSearchParams(window.location.search).get("c");
  const country = getCountryById(id);

  if (!country) {
    box.innerHTML = `<div class="container state"><h1>Cuisine not found</h1>
      <p>We don't have that country yet.</p><a class="btn" href="index.html#map">Back to the map</a></div>`;
    return;
  }

  document.title = `${country.name} cuisine — WorldCuisine`;
  markCountryExplored(country.id); // Culinary Passport stamp (shown on the profile page)
  box.innerHTML = `<div class="container">${loadingBlock("Loading cuisine")}</div>`;

  const [summary, dishes, ingredients] = await Promise.allSettled([
    getCuisineSummary(country.wiki),
    getMealsByCountry(country.area),
    getPopularIngredients(country.area),
  ]);

  const dishList = dishes.status === "fulfilled" ? dishes.value : [];
  const ingredientList = ingredients.status === "fulfilled" ? ingredients.value : [];
  const intro = summary.status === "fulfilled" && summary.value ? summary.value : "Description is not available right now.";

  box.innerHTML = `
    <section class="country-hero">
      ${photoBox(dishList.length ? dishList[0].image : "", country.name + " food")}
      <div class="container">
        <p class="eyebrow">Cuisine</p>
        <h1>${flagImg(country)} ${esc(country.name)}</h1>
      </div>
    </section>
    <div class="container">
      <p class="country-intro">${esc(intro)}</p>
      <p class="source-note">Description: Wikipedia. Dishes and ingredients: TheMealDB.</p>

      <section class="country-section">
        <h2>Traditional dishes</h2>
        <div id="dishes-box"></div>
      </section>

      <section class="country-section">
        <h2>Popular ingredients</h2>
        <div id="ingredients-box"></div>
      </section>

      <div class="country-cta">
        <a class="btn" href="${exploreCountryUrl(country)}">Explore dishes</a><br>
        <a class="back-link" href="index.html#map">← Back to the map</a>
      </div>
    </div>`;

  // Dishes: error / empty / list
  const dishesBox = document.querySelector("#dishes-box");
  if (dishes.status === "rejected") errorBlock(dishesBox, "Could not load dishes. Check your internet connection.", initCountry);
  else if (dishList.length === 0) dishesBox.innerHTML = '<p class="state">No dishes found for this cuisine yet.</p>';
  else dishesBox.innerHTML = `<div class="card-grid">${dishList.slice(0, 12).map((d) => dishCard(d, country.name)).join("")}</div>`;

  // Ingredients: list / empty
  document.querySelector("#ingredients-box").innerHTML = ingredientList.length
    ? `<ul class="tag-list">${ingredientList.map((i) => `<li class="tag">${esc(i)}</li>`).join("")}</ul>`
    : '<p class="state">Ingredient data is not available.</p>';
}

initCountry();
