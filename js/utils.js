// Helpers shared by ALL pages. Import what you need: import { esc, errorBlock } from "./utils.js";

// API text is put into innerHTML, so we escape it first (safety habit)
export function esc(text) {
  const div = document.createElement("div");
  div.textContent = text ?? "";
  return div.innerHTML.replace(/"/g, "&quot;");
}

// Only allow normal web links coming from the API
export const safeUrl = (url) => (/^https?:\/\//i.test(url || "") ? url : "");

export function formatDate(iso) {
  return new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

export function formatDateTime(iso) {
  return new Date(iso).toLocaleString("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}

// Read-only stars as text, e.g. 4 -> ★★★★☆
export const starsText = (n) => "★".repeat(n) + "☆".repeat(5 - n);

// First 2 sentences of a long text
export const shortText = (text, sentences = 2) =>
  (text.match(/[^.!?]+[.!?]+/g) || [text]).slice(0, sentences).join(" ").trim();

/* ---------- Links between pages (one place, so every page links the same way) ---------- */
export const recipeUrl = (id) => `recipe.html?id=${encodeURIComponent(id)}`;
export const countryUrl = (country) => `country.html?c=${encodeURIComponent(country.id)}`;
export const exploreCountryUrl = (country) => `explore.html?area=${encodeURIComponent(country.area)}`;

/* ---------- Small pieces of HTML used on several pages ---------- */
export const flagImg = (country) =>
  `<img class="flag" src="https://flagcdn.com/w80/${country.iso2}.png" alt="Flag of ${esc(country.name)}">`;

// Photo box: shows a green/terracotta gradient if the image is missing or fails to load
export const photoBox = (src, alt) =>
  `<div class="photo">${src ? `<img src="${esc(src)}" alt="${esc(alt)}" loading="lazy" onerror="this.classList.add('img-failed')">` : ""}</div>`;

// Simple dish card (home + country pages). dish = { id, name, image }
export const dishCard = (dish, tag) => `
  <a class="card" href="${recipeUrl(dish.id)}">
    ${photoBox(dish.image, dish.name)}
    <div class="card-body">
      <span class="card-tag">${esc(tag)}</span>
      <h3>${esc(dish.name)}</h3>
    </div>
  </a>`;

/* ---------- API states ---------- */
// Error message with a "Try again" button. Used by every page that loads data.
export function errorBlock(container, message, onRetry) {
  container.innerHTML = `<div class="state error"><p>${esc(message)}</p><button class="btn btn-small" type="button">Try again</button></div>`;
  container.querySelector("button").addEventListener("click", onRetry);
}

export const loadingBlock = (label = "Loading") =>
  `<div class="spinner" role="status" aria-label="${esc(label)}"></div>`;

/* ---------- Star rating (clickable 1-5) ---------- */
// const stars = createStarRating({ value: 3, onChange: (n) => saveRating(id, n) });
// container.appendChild(stars.element);   stars.getValue();   stars.setValue(5);
export function createStarRating({ value = 0, onChange = null, label = "Your rating" } = {}) {
  const element = document.createElement("div");
  element.className = "stars";
  element.setAttribute("role", "radiogroup");
  element.setAttribute("aria-label", label);
  let current = value || 0;

  for (let i = 1; i <= 5; i++) {
    const star = document.createElement("button");
    star.type = "button";
    star.className = "star";
    star.textContent = "★";
    star.dataset.value = i;
    star.setAttribute("role", "radio");
    star.setAttribute("aria-label", `${i} star${i > 1 ? "s" : ""}`);
    element.appendChild(star);
  }

  function paint() {
    element.querySelectorAll(".star").forEach((star) => {
      const n = Number(star.dataset.value);
      star.classList.toggle("on", n <= current);
      star.setAttribute("aria-checked", n === current);
    });
  }

  element.addEventListener("click", (e) => {
    const star = e.target.closest(".star");
    if (!star) return;
    current = Number(star.dataset.value);
    paint();
    if (onChange) onChange(current);
  });

  paint();
  return { element, getValue: () => current, setValue: (v) => { current = v || 0; paint(); } };
}
