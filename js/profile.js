// Profile page: profile, stats, Culinary Passport, activity feed
import { getProfile, saveProfile, AVATARS, getStats, getExploredCountries, getActivity } from "./storage.js";
import { countries } from "./data.js";
import { esc, recipeUrl, formatDate, formatDateTime } from "./utils.js";

const $ = (selector) => document.querySelector(selector);

/* ---------- Profile ---------- */
function renderProfile() {
  const p = getProfile();
  $("#profile-card").innerHTML = `
    <div class="avatar" aria-hidden="true">${p.avatar}</div>
    <div class="profile-info">
      <h2>${esc(p.username)}</h2>
      <p>${p.bio ? esc(p.bio) : "No bio yet."}</p>
      <button id="edit-profile" class="btn btn-small" type="button">Edit profile</button>
    </div>`;
  $("#edit-profile").addEventListener("click", renderProfileForm);
}

function renderProfileForm() {
  const p = getProfile();
  $("#profile-card").innerHTML = `
    <form id="profile-form" class="profile-form" novalidate>
      <div class="form-field">
        <label for="username">Username</label>
        <input id="username" type="text" maxlength="24" value="${esc(p.username)}" required>
      </div>
      <div class="form-field">
        <label for="bio">Bio</label>
        <textarea id="bio" rows="3" maxlength="160" placeholder="Tell us about your food taste">${esc(p.bio)}</textarea>
      </div>
      <fieldset class="avatar-picker">
        <legend class="label">Avatar</legend>
        ${AVATARS.map((a) => `
          <label class="avatar-option">
            <input type="radio" name="avatar" value="${a}" ${a === p.avatar ? "checked" : ""}>
            <span>${a}</span>
          </label>`).join("")}
      </fieldset>
      <div id="profile-error" class="form-errors" role="alert"></div>
      <div class="form-buttons">
        <button class="btn" type="submit">Save</button>
        <button id="cancel-profile" class="btn btn-outline" type="button">Cancel</button>
      </div>
    </form>`;

  $("#cancel-profile").addEventListener("click", renderProfile);
  $("#profile-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const username = $("#username").value.trim();
    if (username.length < 2) {
      $("#username").setAttribute("aria-invalid", "true");
      $("#profile-error").textContent = "Username must be at least 2 characters.";
      return;
    }
    saveProfile({
      username,
      bio: $("#bio").value,
      avatar: document.querySelector('input[name="avatar"]:checked').value,
    });
    renderProfile();
  });
}

/* ---------- Stats ---------- */
function renderStats() {
  const s = getStats();
  const items = [
    [s.explored, "Dishes explored"],
    [s.tried, "Dishes tried"],
    [s.reviews, "Reviews"],
    [s.favorites, "Favorites"],
    [s.watchlist, "In watchlist"],
    [s.averageRating === null ? "–" : s.averageRating, "Average rating"],
  ];
  $("#stats-grid").innerHTML = items.map(([value, label]) => `<div class="stat"><strong>${value}</strong><span>${label}</span></div>`).join("");
}

/* ---------- Culinary Passport ---------- */
function renderPassport() {
  const explored = getExploredCountries().filter((e) => countries.some((c) => c.id === e.id));
  const total = countries.length;
  const percent = Math.round((explored.length / total) * 100);

  const stamps = countries.map((c) => {
    const entry = explored.find((e) => e.id === c.id);
    return `
      <div class="stamp ${entry ? "explored" : ""}">
        <img src="https://flagcdn.com/w80/${c.iso2}.png" alt="Flag of ${esc(c.name)}">
        <strong>${esc(c.name)}</strong>
        <small>${entry ? "Explored " + formatDate(entry.exploredAt) : "Not visited yet"}</small>
      </div>`;
  }).join("");

  $("#passport").innerHTML = `
    <p><strong>${explored.length}</strong> of ${total} countries explored (${percent}%)</p>
    <div class="progress" role="progressbar" aria-label="Countries explored" aria-valuemin="0" aria-valuemax="${total}" aria-valuenow="${explored.length}">
      <div class="progress-bar" style="width:${percent}%"></div>
    </div>
    <div class="passport-grid">${stamps}</div>
    ${explored.length === 0 ? '<p class="state">Open a country page on the <a href="index.html#map">map</a> to get your first stamp.</p>' : ""}`;
}

/* ---------- Activity feed ---------- */
function activityText(a) {
  const name = a.mealName ? `<a href="${recipeUrl(a.mealId)}">${esc(a.mealName)}</a>` : "a dish";
  if (a.type === "watchlist") return `Added ${name} to your watchlist`;
  if (a.type === "rating") return `Rated ${name} ${a.detail} / 5`;
  if (a.type === "review") return `Wrote a review of ${name}`;
  if (a.type === "tried") return `Marked ${name} as tried`;
  if (a.type === "favorite") return `Added ${name} to favorites`;
  return "";
}

function renderFeed() {
  const items = getActivity().slice(0, 15);
  $("#activity-feed").innerHTML = items.length
    ? items.map((a) => `<li><span>${activityText(a)}</span><time datetime="${a.at}">${formatDateTime(a.at)}</time></li>`).join("")
    : '<li><span class="state">No activity yet. Add a dish to your watchlist to get started.</span></li>';
}

renderProfile();
renderStats();
renderPassport();
renderFeed();
