// ===== WorldCuisine API module (TheMealDB + Wikipedia) =====
// Other modules: import { searchMeals, getMealById } from "./api.js";
//
// A "meal" object always looks like this (missing values are null, never invented):
// { id, name, image, area, category, tags, instructions, youtube, source, ingredients: [{ name, measure }] }
// Note: lists from filter endpoints (country / category) only contain
// id, name and image. Use getMealById(id) to get the rest.

const MEALDB = "https://www.themealdb.com/api/json/v1/1";
const WIKI = "https://en.wikipedia.org/api/rest_v1/page/summary";

const cache = new Map(); // remembers answers so the same URL is not requested twice

async function request(url, useCache = true) {
  if (useCache && cache.has(url)) return cache.get(url);
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Request failed (${response.status})`);
  const data = await response.json();
  if (useCache) cache.set(url, data);
  return data;
}

const clean = (text) => (typeof text === "string" && text.trim() ? text.trim() : null);

// Converts the raw API object into the meal object described above
function normalizeMeal(raw) {
  const ingredients = [];
  for (let i = 1; i <= 20; i++) {
    const name = clean(raw["strIngredient" + i]);
    if (name) ingredients.push({ name, measure: clean(raw["strMeasure" + i]) || "" });
  }
  return {
    id: raw.idMeal,
    name: raw.strMeal,
    image: clean(raw.strMealThumb),
    area: clean(raw.strArea),
    category: clean(raw.strCategory),
    tags: clean(raw.strTags) ? raw.strTags.split(",").map((t) => t.trim()) : [],
    instructions: clean(raw.strInstructions),
    youtube: clean(raw.strYoutube),
    source: clean(raw.strSource),
    ingredients,
  };
}

// The API answers { meals: null } when nothing is found -> we return []
const toMeals = (data) => (data.meals || []).map(normalizeMeal);

/* ---------- Main functions ---------- */

// Search meals by name, e.g. searchMeals("pasta") -> full meal objects
export async function searchMeals(query) {
  const text = query.trim();
  if (!text) return [];
  return toMeals(await request(`${MEALDB}/search.php?s=${encodeURIComponent(text)}`));
}

// Meals of one country/cuisine. TheMealDB uses demonyms: "Italian", "Japanese", "Mexican"...
export async function getMealsByCountry(area) {
  return toMeals(await request(`${MEALDB}/filter.php?a=${encodeURIComponent(area)}`));
}

// Meals of one category: "Seafood", "Dessert", "Vegetarian"...
export async function getMealsByCategory(category) {
  return toMeals(await request(`${MEALDB}/filter.php?c=${encodeURIComponent(category)}`));
}

// Full details of one meal. Returns null if the ID does not exist.
export async function getMealById(id) {
  const meals = toMeals(await request(`${MEALDB}/lookup.php?i=${encodeURIComponent(id)}`));
  return meals[0] || null;
}

// One random meal (full details). Never cached, so each call is different.
export async function getRandomMeal() {
  const meals = toMeals(await request(`${MEALDB}/random.php`, false));
  return meals[0] || null;
}

// Several different random meals (the free API gives one per request, so we ask in parallel)
export async function getRandomMeals(count = 8) {
  const results = await Promise.allSettled(Array.from({ length: count }, () => getRandomMeal()));
  const unique = new Map();
  results.forEach((r) => {
    if (r.status === "fulfilled" && r.value) unique.set(r.value.id, r.value);
  });
  if (unique.size === 0) throw new Error("Could not load random meals");
  return [...unique.values()];
}

// Lists for the filter dropdowns -> arrays of strings
export async function getAreas() {
  const data = await request(`${MEALDB}/list.php?a=list`);
  return (data.meals || []).map((m) => m.strArea).sort();
}

export async function getCategories() {
  const data = await request(`${MEALDB}/list.php?c=list`);
  return (data.meals || []).map((m) => m.strCategory).sort();
}

/* ---------- Extra helpers used by the homepage / country page ---------- */

// Most common ingredients in the first few meals of a country
export async function getPopularIngredients(area, limit = 8) {
  const meals = (await getMealsByCountry(area)).slice(0, 4);
  const details = await Promise.all(meals.map((m) => getMealById(m.id)));

  const counts = {};
  details.filter(Boolean).forEach((meal) =>
    meal.ingredients.forEach(({ name }) => {
      const key = name.toLowerCase();
      counts[key] = (counts[key] || 0) + 1;
    })
  );
  return Object.keys(counts).sort((a, b) => counts[b] - counts[a]).slice(0, limit);
}

// Cuisine description from Wikipedia (plain text)
export async function getCuisineSummary(wikiTitle) {
  const data = await request(`${WIKI}/${encodeURIComponent(wikiTitle.replace(/ /g, "_"))}`);
  return data.extract || "";
}
