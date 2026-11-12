// ===== WorldCuisine LocalStorage module =====
// Every user-specific feature uses these functions and keys. No backend, no database.
// Import example: import { addToWatchlist, saveRating, saveReview } from "./storage.js";
//
// A "meal" passed into these functions is: { id, name, image, area, category } (area/category may be null)
//
// KEY                       VALUE
// worldcuisine:watchlist -> [ { id, name, image, area, category, addedAt } ]
// worldcuisine:favorites -> [ { id, name, image, area, category, addedAt } ]
// worldcuisine:tried     -> [ { id, name, image, area, category, triedAt } ]
// worldcuisine:ratings   -> { "52772": 4 }                 (meal id -> whole number 1-5)
// worldcuisine:reviews   -> [ { id, mealId, mealName, mealImage, area, category, rating, text, createdAt, updatedAt } ]
// worldcuisine:profile   -> { username, bio, avatar }
// worldcuisine:explored  -> [ "52772", ... ]               (ids of dishes whose recipe page was opened)
// worldcuisine:countries -> [ { id: "italy", exploredAt } ]  (country ids from data.js)
// worldcuisine:activity  -> [ { type, mealId, mealName, detail, at } ]   newest first, max 50
// All dates are ISO strings: new Date().toISOString()

export const KEYS = {
  watchlist: "worldcuisine:watchlist",
  favorites: "worldcuisine:favorites",
  tried: "worldcuisine:tried",
  ratings: "worldcuisine:ratings",
  reviews: "worldcuisine:reviews",
  profile: "worldcuisine:profile",
  explored: "worldcuisine:explored",
  countries: "worldcuisine:countries",
  activity: "worldcuisine:activity",
};

const MAX_ACTIVITY = 50;
const now = () => new Date().toISOString();

/* ---------- Basic storage functions ---------- */

// Reads and parses JSON. Returns `fallback` if nothing is saved or the JSON is broken.
export function getData(key, fallback = null) {
  try {
    const raw = localStorage.getItem(key);
    return raw === null ? fallback : JSON.parse(raw);
  } catch (error) {
    return fallback;
  }
}

// Converts to JSON and saves. Returns true if it worked.
export function saveData(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch (error) {
    console.error("LocalStorage error:", error);
    return false;
  }
}

// Keeps only the fields we need from a meal
const toSaved = (meal) => ({
  id: String(meal.id),
  name: meal.name || meal.mealName || "Unknown dish",
  image: meal.image || meal.mealImage || null,
  area: meal.area || null,
  category: meal.category || null,
});

/* ---------- Activity feed ---------- */
// type: "watchlist" | "rating" | "review" | "tried" | "favorite"

export const getActivity = () => getData(KEYS.activity, []);

function logActivity(type, meal, detail = null) {
  const entry = { type, mealId: String(meal.id), mealName: meal.name || meal.mealName || null, detail, at: now() };
  saveData(KEYS.activity, [entry, ...getActivity()].slice(0, MAX_ACTIVITY));
}

// Looks for a dish in saved lists (used when we only know the id)
function findKnownMeal(id) {
  const lists = [getWatchlist(), getFavorites(), getTried()];
  for (const list of lists) {
    const found = list.find((m) => m.id === String(id));
    if (found) return found;
  }
  const review = getReviews().find((r) => r.mealId === String(id));
  return review ? { id: review.mealId, name: review.mealName } : null;
}

// Reads a saved list of dishes and repairs old or damaged records (e.g. saved before a field existed)
function getDishList(key, dateField) {
  const list = getData(key, []);
  if (!Array.isArray(list)) return [];
  return list
    .filter((m) => m && m.id !== undefined && m.id !== null)
    .map((m) => ({
      ...m,
      id: String(m.id),
      name: m.name || "Unknown dish",
      image: m.image || null,
      area: m.area || null,
      category: m.category || null,
      [dateField]: m[dateField] || "",
    }));
}

/* ---------- Watchlist ---------- */

export const getWatchlist = () => getDishList(KEYS.watchlist, "addedAt");
export const isInWatchlist = (id) => getWatchlist().some((m) => m.id === String(id));

// Returns false (and does nothing) if the dish is already saved -> no duplicates
export function addToWatchlist(meal) {
  if (isInWatchlist(meal.id)) return false;
  saveData(KEYS.watchlist, [...getWatchlist(), { ...toSaved(meal), addedAt: now() }]);
  logActivity("watchlist", meal);
  return true;
}

export function removeFromWatchlist(id) {
  saveData(KEYS.watchlist, getWatchlist().filter((m) => m.id !== String(id)));
}

// Adds if missing, removes if present. Returns true when the dish is now in the watchlist.
export function toggleWatchlist(meal) {
  if (isInWatchlist(meal.id)) {
    removeFromWatchlist(meal.id);
    return false;
  }
  return addToWatchlist(meal);
}

/* ---------- Favorites ---------- */

export const getFavorites = () => getDishList(KEYS.favorites, "addedAt");
export const isFavorite = (id) => getFavorites().some((m) => m.id === String(id));

export function addFavorite(meal) {
  if (isFavorite(meal.id)) return false;
  saveData(KEYS.favorites, [...getFavorites(), { ...toSaved(meal), addedAt: now() }]);
  logActivity("favorite", meal);
  return true;
}

export function removeFavorite(id) {
  saveData(KEYS.favorites, getFavorites().filter((m) => m.id !== String(id)));
}

export function toggleFavorite(meal) {
  if (isFavorite(meal.id)) {
    removeFavorite(meal.id);
    return false;
  }
  return addFavorite(meal);
}

// Watchlist -> Favorites
export function moveToFavorites(id) {
  const meal = getWatchlist().find((m) => m.id === String(id));
  if (!meal) return false;
  addFavorite(meal);
  removeFromWatchlist(id);
  return true;
}

/* ---------- Tried ---------- */

export const getTried = () => getDishList(KEYS.tried, "triedAt");
export const isTried = (id) => getTried().some((m) => m.id === String(id));

export function markTried(meal) {
  if (isTried(meal.id)) return false;
  saveData(KEYS.tried, [...getTried(), { ...toSaved(meal), triedAt: now() }]);
  logActivity("tried", meal);
  return true;
}

export function unmarkTried(id) {
  saveData(KEYS.tried, getTried().filter((m) => m.id !== String(id)));
}

export function toggleTried(meal) {
  if (isTried(meal.id)) {
    unmarkTried(meal.id);
    return false;
  }
  return markTried(meal);
}

/* ---------- Ratings (1-5) ---------- */

export const getRatings = () => getData(KEYS.ratings, {});

// Returns a number 1-5, or null if the dish has no rating
export function getRating(id) {
  const value = Number(getRatings()[String(id)]);
  return value >= 1 ? value : null;
}

// Saves or updates the rating of a dish. `meal` is optional and only used for the activity feed.
// Returns false if the value is not a whole number from 1 to 5.
export function saveRating(mealId, value, meal = null) {
  const rating = Number(value);
  if (!Number.isInteger(rating) || rating < 1 || rating > 5) return false;

  const id = String(mealId);
  const ratings = getRatings();
  if (ratings[id] === rating) return true; // nothing changed
  ratings[id] = rating;
  saveData(KEYS.ratings, ratings);
  logActivity("rating", meal || findKnownMeal(id) || { id }, rating);
  return true;
}
export const setRating = saveRating; // old name, still works

// Average of all ratings the user has saved -> { average: 4.2, count: 5 } (average is null when empty)
export function getAverageRating() {
  const values = Object.values(getRatings()).map(Number).filter((v) => v >= 1);
  if (values.length === 0) return { average: null, count: 0 };
  const sum = values.reduce((total, v) => total + v, 0);
  return { average: Math.round((sum / values.length) * 10) / 10, count: values.length };
}

/* ---------- Reviews ---------- */

export const getReviews = () => getData(KEYS.reviews, []);
export const getReview = (mealId) => getReviews().find((r) => r.mealId === String(mealId)) || null;

// One review per dish: saving again for the same dish UPDATES the review (edit).
// Also saves the rating. Returns the saved review, or null if the data is not valid.
export function saveReview({ meal, rating, text }) {
  const cleanText = String(text || "").trim();
  const stars = Number(rating);
  if (!meal || !meal.id || !cleanText || !Number.isInteger(stars) || stars < 1 || stars > 5) return null;

  const mealId = String(meal.id);
  const reviews = getReviews();
  const old = reviews.find((r) => r.mealId === mealId);
  const saved = {
    id: old ? old.id : "r" + Date.now(),
    mealId,
    mealName: meal.name || meal.mealName || "Unknown dish",
    mealImage: meal.image || meal.mealImage || null,
    area: meal.area || null,
    category: meal.category || null,
    rating: stars,
    text: cleanText,
    createdAt: old ? old.createdAt : now(),
    updatedAt: now(),
  };

  saveData(KEYS.reviews, old ? reviews.map((r) => (r.id === old.id ? saved : r)) : [saved, ...reviews]);
  const ratings = getRatings();
  ratings[mealId] = stars;
  saveData(KEYS.ratings, ratings);
  logActivity("review", { id: mealId, name: saved.mealName }, stars);
  return saved;
}

export function deleteReview(reviewId) {
  saveData(KEYS.reviews, getReviews().filter((r) => r.id !== reviewId));
}

/* ---------- Profile ---------- */

export const AVATARS = ["🍜", "🍕", "🍣", "🌮", "🥐", "🍩", "🥑", "🍓"];
const DEFAULT_PROFILE = { username: "Food Explorer", bio: "", avatar: AVATARS[0] };

export const getProfile = () => ({ ...DEFAULT_PROFILE, ...getData(KEYS.profile, {}) });

// Returns the saved profile, or null if the username is empty
export function saveProfile({ username, bio, avatar }) {
  const name = String(username || "").trim();
  if (!name) return null;
  const profile = { username: name, bio: String(bio || "").trim(), avatar: AVATARS.includes(avatar) ? avatar : AVATARS[0] };
  saveData(KEYS.profile, profile);
  return profile;
}

/* ---------- Explored dishes and countries (Culinary Passport) ---------- */

export const getExploredDishes = () => getData(KEYS.explored, []);

export function markDishExplored(id) {
  const list = getExploredDishes();
  if (!list.includes(String(id))) saveData(KEYS.explored, [...list, String(id)]);
}

export const getExploredCountries = () => getData(KEYS.countries, []);
export const isCountryExplored = (id) => getExploredCountries().some((c) => c.id === id);

// countryId is the id from data.js, e.g. "italy"
export function markCountryExplored(countryId) {
  if (isCountryExplored(countryId)) return false;
  saveData(KEYS.countries, [...getExploredCountries(), { id: countryId, exploredAt: now() }]);
  return true;
}

/* ---------- Numbers for the profile page ---------- */

export function getStats() {
  const { average, count } = getAverageRating();
  return {
    explored: getExploredDishes().length,
    tried: getTried().length,
    reviews: getReviews().length,
    favorites: getFavorites().length,
    watchlist: getWatchlist().length,
    countries: getExploredCountries().length,
    averageRating: average,
    ratedCount: count,
  };
}
