// Reviews page: write, edit, delete and view reviews (saved in LocalStorage)
import {
  getWatchlist, getFavorites, getTried, getReviews, getReview, saveReview, deleteReview, getRating, getAverageRating,
} from "./storage.js";
import { getMealById } from "./api.js";
import { esc, recipeUrl, formatDate, starsText, createStarRating } from "./utils.js";

const $ = (selector) => document.querySelector(selector);
const form = $("#review-form");
const dishSelect = $("#review-dish");
const textArea = $("#review-text");
const errorsBox = $("#form-errors");
const messageBox = $("#form-message");
const cancelBtn = $("#cancel-btn");

const meals = new Map(); // id -> { id, name, image, area, category } for the dropdown
const stars = createStarRating({ label: "Your rating" });
$("#review-stars").appendChild(stars.element);

/* ---------- Dropdown ---------- */
function collectMeals() {
  getWatchlist().concat(getFavorites(), getTried()).forEach((m) => meals.set(m.id, m));
  getReviews().forEach((r) =>
    meals.set(r.mealId, { id: r.mealId, name: r.mealName, image: r.mealImage, area: r.area, category: r.category })
  );
}

function fillDropdown(selectedId = "") {
  const options = [...meals.values()].sort((a, b) => a.name.localeCompare(b.name))
    .map((m) => `<option value="${esc(m.id)}">${esc(m.name)}</option>`).join("");
  dishSelect.innerHTML = '<option value="">Choose a dish…</option>' + options;
  dishSelect.value = selectedId;
}

/* ---------- Form ---------- */
function resetForm() {
  form.reset();
  stars.setValue(0);
  dishSelect.disabled = false;
  cancelBtn.hidden = true;
  $("#form-title").textContent = "Write a review";
  $("#save-btn").textContent = "Save review";
  errorsBox.innerHTML = "";
  [dishSelect, textArea].forEach((el) => el.removeAttribute("aria-invalid"));
}

// Fills the form with an existing review so the user can change it
function startEdit(mealId) {
  const review = getReview(mealId);
  if (!review) return;
  dishSelect.value = review.mealId;
  dishSelect.disabled = true; // one review per dish
  stars.setValue(review.rating);
  textArea.value = review.text;
  cancelBtn.hidden = false;
  $("#form-title").textContent = "Edit your review";
  $("#save-btn").textContent = "Update review";
  messageBox.textContent = "";
  form.scrollIntoView({ behavior: "smooth" });
  textArea.focus();
}

function validate() {
  const errors = [];
  const text = textArea.value.trim();
  if (!dishSelect.value) errors.push("Please choose a dish.");
  if (stars.getValue() === 0) errors.push("Please choose a star rating.");
  if (!text) errors.push("Please write your review.");
  else if (text.length < 10) errors.push("Your review must be at least 10 characters.");

  dishSelect.setAttribute("aria-invalid", !dishSelect.value);
  textArea.setAttribute("aria-invalid", text.length < 10);
  errorsBox.innerHTML = errors.map((e) => `<p>${e}</p>`).join("");
  return errors.length === 0;
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  messageBox.textContent = "";
  if (!validate()) return;

  const saved = saveReview({ meal: meals.get(dishSelect.value), rating: stars.getValue(), text: textArea.value });
  if (!saved) {
    errorsBox.innerHTML = "<p>Could not save the review. Please try again.</p>";
    return;
  }
  resetForm();
  fillDropdown();
  messageBox.textContent = "Review saved!";
  render();
});

cancelBtn.addEventListener("click", () => { resetForm(); fillDropdown(); });

// If the user picks a dish that already has a review, open it for editing
dishSelect.addEventListener("change", () => {
  messageBox.textContent = "";
  if (dishSelect.value && getReview(dishSelect.value)) startEdit(dishSelect.value);
});

/* ---------- Review list ---------- */
function render() {
  const reviews = [...getReviews()].sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  const { average, count } = getAverageRating();

  $("#review-count").textContent = `(${reviews.length})`;
  $("#reviews-summary").textContent = count
    ? `Your average rating: ${average} / 5 across ${count} rated dish${count === 1 ? "" : "es"}.`
    : "You have not rated any dishes yet.";

  if (reviews.length === 0) {
    $("#review-list").innerHTML = '<div class="state"><p>No reviews yet. Write your first one!</p></div>';
    return;
  }

  $("#review-list").innerHTML = reviews.map((r) => `
    <article class="review" data-meal="${esc(r.mealId)}" data-id="${esc(r.id)}">
      <div class="photo">${r.mealImage ? `<img src="${esc(r.mealImage)}" alt="" loading="lazy" onerror="this.classList.add('img-failed')">` : ""}</div>
      <div>
        <h3><a href="${recipeUrl(r.mealId)}">${esc(r.mealName)}</a></h3>
        <div class="review-stars" aria-label="Rating ${r.rating} out of 5">${starsText(r.rating)}</div>
        <p class="review-text">${esc(r.text)}</p>
        <p class="review-date">${formatDate(r.createdAt)}${r.updatedAt !== r.createdAt ? ` · edited ${formatDate(r.updatedAt)}` : ""}</p>
        <button class="btn btn-small btn-outline" type="button" data-action="edit">Edit</button>
        <button class="btn btn-small btn-outline" type="button" data-action="delete">Delete</button>
      </div>
    </article>`).join("");
}

$("#review-list").addEventListener("click", (e) => {
  const button = e.target.closest("button[data-action]");
  if (!button) return;
  const card = button.closest(".review");

  if (button.dataset.action === "edit") startEdit(card.dataset.meal);
  if (button.dataset.action === "delete" && window.confirm("Delete this review?")) {
    deleteReview(card.dataset.id);
    resetForm();
    fillDropdown();
    render();
  }
});

/* ---------- Start ---------- */
async function init() {
  collectMeals();

  // recipe.html links here with ?id=52772, so that dish must be in the list
  const id = new URLSearchParams(window.location.search).get("id");
  if (id && !meals.has(id)) {
    try {
      const meal = await getMealById(id);
      if (meal) meals.set(meal.id, meal);
    } catch (error) {
      errorsBox.innerHTML = "<p>Could not load that dish. Check your internet connection.</p>";
    }
  }

  fillDropdown(id && meals.has(id) ? id : "");
  if (id && getReview(id)) startEdit(id);
  render();
}

init();
