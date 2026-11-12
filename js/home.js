// Homepage: map + country panel, popular dishes, trending cuisines, discover, random dish.
import { countries, getCountryByIso3 } from "./data.js";
import { getMealsByCountry, getRandomMeal, getCuisineSummary } from "./api.js";
import { initMap } from "./map.js";
import {
  esc, shortText, countryUrl, recipeUrl, flagImg, photoBox, dishCard, errorBlock, loadingBlock,
} from "./utils.js";

const $ = (selector) => document.querySelector(selector);
const pick = (list) => list[Math.floor(Math.random() * list.length)];

/* ---------- Map panel ---------- */
let lastClick = 0; // protects the panel if the user clicks several countries quickly

async function showCountryPanel(selected) {
  const { iso3, name } = selected;
  const country = getCountryByIso3(iso3);
  const panel = $("#country-panel");

  if (!country) {
    panel.innerHTML = `<h3>${esc(name)}</h3><p>Cuisine guide coming soon. Try one of the highlighted countries.</p>`;
    return;
  }

  const clickId = ++lastClick;
  const head = `<div class="panel-head">${flagImg(country)}<h3>${esc(country.name)}</h3></div>`;
  panel.innerHTML = `${head}<p class="state">Loading cuisine…</p>`;

  const [summary, dishes] = await Promise.allSettled([getCuisineSummary(country.wiki), getMealsByCountry(country.area)]);
  if (clickId !== lastClick) return; // a newer click replaced this one

  const intro = summary.status === "fulfilled" && summary.value ? shortText(summary.value) : "Description is not available right now.";
  let dishHtml;
  if (dishes.status === "rejected") dishHtml = '<div id="panel-dishes"></div>';
  else if (dishes.value.length === 0) dishHtml = "<p>No dishes found yet.</p>";
  else dishHtml = `<ul class="dish-list">${dishes.value.slice(0, 5).map((d) => `<li><a href="${recipeUrl(d.id)}">${esc(d.name)}</a></li>`).join("")}</ul>`;

  panel.innerHTML = `
    ${head}
    <p>${esc(intro)}</p>
    <h4>Popular dishes</h4>
    ${dishHtml}
    <a class="btn" href="${countryUrl(country)}">Explore Cuisine</a>`;

  if (dishes.status === "rejected") {
    errorBlock($("#panel-dishes"), "Could not load dishes.", () => showCountryPanel(selected));
  }
}

/* ---------- Sections ---------- */
async function loadPopularDishes() {
  const box = $("#popular-dishes");
  box.innerHTML = loadingBlock("Loading dishes");

  // one random dish from each of 6 cuisines, requested in parallel
  const chosen = countries.slice(0, 6);
  const results = await Promise.allSettled(chosen.map((c) => getMealsByCountry(c.area)));
  const cards = [];
  results.forEach((result, i) => {
    if (result.status === "fulfilled" && result.value.length > 0) cards.push(dishCard(pick(result.value), chosen[i].name));
  });

  if (cards.length) box.innerHTML = cards.join("");
  else errorBlock(box, "Could not load dishes. Check your internet connection.", loadPopularDishes);
}

async function loadDiscover() {
  const box = $("#discover");
  const country = pick(countries);
  box.innerHTML = loadingBlock("Loading");

  const [summary, dishes] = await Promise.allSettled([getCuisineSummary(country.wiki), getMealsByCountry(country.area)]);
  if (summary.status === "rejected" && dishes.status === "rejected") {
    errorBlock(box, "Could not load a cuisine to discover.", loadDiscover);
    return;
  }

  const intro = summary.status === "fulfilled" ? shortText(summary.value) : "";
  const image = dishes.status === "fulfilled" && dishes.value.length ? pick(dishes.value).image : "";
  box.innerHTML = `
    <a class="card" href="${countryUrl(country)}">
      ${photoBox(image, country.name + " cuisine")}
      <div class="card-body">
        <span class="card-tag">Today's pick</span>
        <h3>${esc(country.name)}</h3>
        <p>${esc(intro)}</p>
      </div>
    </a>`;
}

async function showRandomDish() {
  const result = $("#random-dish-result");
  result.innerHTML = loadingBlock("Finding a dish");
  try {
    const dish = await getRandomMeal();
    if (!dish) throw new Error("No dish");
    result.innerHTML = `<strong>${esc(dish.name)}</strong>${esc([dish.category, dish.area].filter(Boolean).join(" · "))}
      <a href="${recipeUrl(dish.id)}">See the recipe →</a>`;
  } catch (error) {
    errorBlock(result, "Could not load a dish.", showRandomDish);
  }
}

/* ---------- Start ---------- */
initMap($("#map-container"), showCountryPanel);
$("#country-panel").innerHTML = '<p class="state">Select a country on the map to see its cuisine.</p>';

$("#trending-cuisines").innerHTML = countries.slice(0, 8)
  .map((c) => `<a class="chip" href="${countryUrl(c)}">${flagImg(c)}${esc(c.name)}</a>`).join("");

loadPopularDishes();
loadDiscover();
$("#random-dish-btn").addEventListener("click", showRandomDish);
