# WorldCuisine

Run with a local server (ES modules do not work from file://): VS Code "Live Server" or `python -m http.server`.

## Final structure
```
index.html  country.html  explore.html  recipe.html  watchlist.html  reviews.html  profile.html
css/  style.css (design system + shared components) · home · country · explore · recipe · user
js/   main.js     nav + footer (every page)
      utils.js    shared helpers: esc, links, flagImg, photoBox, dishCard, errorBlock, createStarRating
      api.js      TheMealDB + Wikipedia
      storage.js  all LocalStorage keys and functions
      data.js     list of countries (id, iso3, iso2, name, area, wiki)
      map.js      SVG world map           home.js     homepage
      country.js  country page            explore.js  recipe discovery
      recipe.js   recipe details          watchlist.js · reviews.js · profile.js
data/world.geo.json   free GeoJSON used by the map
```

## Page flow and URLs
Home map -> `country.html?c=italy` -> `explore.html?area=Italian` -> `recipe.html?id=52772` -> `reviews.html?id=52772`
explore.html also accepts `?q=pasta&area=Italian&category=Dessert`.
Build links with the helpers in utils.js: `recipeUrl(id)`, `countryUrl(country)`, `exploreCountryUrl(country)`.

## Shared page skeleton
Every page has `<body data-page="...">`, `<header id="site-header">`, `<footer id="site-footer">` and
`<script type="module" src="js/main.js">` (draws nav + footer; country and recipe pages keep "Explore" highlighted).

## js/api.js (TheMealDB + Wikipedia)
```js
import { searchMeals, getMealsByCountry, getMealsByCategory,
         getMealById, getRandomMeal, getRandomMeals, getAreas, getCategories } from "./api.js";
```
| Function | Returns |
|---|---|
| `searchMeals("pasta")` | array of full meals |
| `getMealsByCountry("Italian")` | array of short meals (id, name, image) |
| `getMealsByCategory("Dessert")` | array of short meals |
| `getMealById("52772")` | full meal or `null` |
| `getRandomMeal()` / `getRandomMeals(8)` | full meal / array |
| `getAreas()` / `getCategories()` | array of strings |

Meal object: `{ id, name, image, area, category, tags, instructions, youtube, source, ingredients: [{name, measure}] }`.
Missing values are `null` (never invented). Short meals have `area`, `category` etc. = `null` — call `getMealById(id)` for details.
All functions throw on network errors: use `try/catch`. TheMealDB uses "Italian", not "Italy".

## js/storage.js (LocalStorage, no backend)
```js
import { getData, saveData, addToWatchlist, removeFromWatchlist, addFavorite, removeFavorite,
         saveReview, deleteReview, saveRating, getRating, getStats } from "./storage.js";
```
A **meal** passed to these functions: `{ id, name, image, area, category }` (area/category can be null).

| Key | Value |
|---|---|
| `worldcuisine:watchlist` | `[{ id, name, image, area, category, addedAt }]` |
| `worldcuisine:favorites` | `[{ id, name, image, area, category, addedAt }]` |
| `worldcuisine:tried` | `[{ id, name, image, area, category, triedAt }]` |
| `worldcuisine:ratings` | `{ "52772": 4 }` (meal id -> whole number 1-5) |
| `worldcuisine:reviews` | `[{ id, mealId, mealName, mealImage, area, category, rating, text, createdAt, updatedAt }]` |
| `worldcuisine:profile` | `{ username, bio, avatar }` |
| `worldcuisine:explored` | `["52772", ...]` ids of opened recipes |
| `worldcuisine:countries` | `[{ id: "italy", exploredAt }]` (ids from data.js) |
| `worldcuisine:activity` | `[{ type, mealId, mealName, detail, at }]` newest first, max 50 |

Dates are ISO strings. Meal ids are always strings.

| Function | What it does |
|---|---|
| `getData(key, fallback)` / `saveData(key, value)` | JSON.parse / JSON.stringify wrappers, safe if storage is broken |
| `addToWatchlist(meal)` / `removeFromWatchlist(id)` / `isInWatchlist(id)` / `getWatchlist()` | `add` returns false for duplicates |
| `addFavorite(meal)` / `removeFavorite(id)` / `isFavorite(id)` / `getFavorites()` | same rules |
| `moveToFavorites(id)` | watchlist -> favorites |
| `toggleWatchlist(meal)`, `toggleFavorite(meal)`, `toggleTried(meal)` | add or remove, returns true if now saved |
| `markTried(meal)` / `unmarkTried(id)` / `isTried(id)` / `getTried()` | tried dishes |
| `saveRating(id, 1-5, meal?)` / `getRating(id)` | rating or null; `saveRating` returns false for invalid values |
| `getAverageRating()` | `{ average, count }` of all saved ratings |
| `saveReview({ meal, rating, text })` | one review per dish: saving again edits it; also saves the rating; returns null if invalid |
| `deleteReview(reviewId)` / `getReviews()` / `getReview(mealId)` | reviews |
| `getProfile()` / `saveProfile({ username, bio, avatar })` | profile (has defaults) |
| `markDishExplored(id)` / `markCountryExplored(countryId)` / `getExploredCountries()` | Culinary Passport |
| `getActivity()` | feed; written automatically by the functions above |
| `getStats()` | all counts for the profile page |

## js/utils.js
`esc`, `safeUrl`, `formatDate`, `starsText`, `shortText`, `recipeUrl`, `countryUrl`, `exploreCountryUrl`, `flagImg`, `photoBox`, `dishCard`,
`errorBlock(container, message, retryFn)`, `loadingBlock()`, `createStarRating({ value, onChange })`.
Always use `esc()` before putting API text into innerHTML.

Data: TheMealDB (free key "1"), Wikipedia REST API, flagcdn.com.
