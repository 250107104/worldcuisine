// Shared layout for EVERY page: navigation bar + footer.
// Each page needs:  <body data-page="...">  <header id="site-header">  <footer id="site-footer">
// The link with the same name as data-page is highlighted.

const NAV_LINKS = [
  { label: "Home", href: "index.html", page: "home" },
  { label: "Explore", href: "explore.html", page: "explore" },
  { label: "Watchlist", href: "watchlist.html", page: "watchlist" },
  { label: "Reviews", href: "reviews.html", page: "reviews" },
  { label: "Profile", href: "profile.html", page: "profile" },
];

// country.html and recipe.html belong to "Explore", so Explore stays highlighted there
const PAGE_GROUPS = { country: "explore", recipe: "explore" };

function renderHeader() {
  const page = document.body.dataset.page;
  const current = PAGE_GROUPS[page] || page;
  const links = NAV_LINKS.map(
    (l) => `<li><a href="${l.href}" ${l.page === current ? 'aria-current="page"' : ""}>${l.label}</a></li>`
  ).join("");

  document.querySelector("#site-header").innerHTML = `
    <nav class="nav container" aria-label="Main">
      <a class="logo" href="index.html">WorldCuisine</a>
      <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="nav-menu" aria-label="Toggle menu">
        <span></span><span></span><span></span>
      </button>
      <ul id="nav-menu" class="nav-menu">${links}</ul>
    </nav>`;

  const toggle = document.querySelector(".nav-toggle");
  toggle.addEventListener("click", () => {
    const open = document.querySelector("#nav-menu").classList.toggle("open");
    toggle.setAttribute("aria-expanded", open);
  });
}

function renderFooter() {
  document.querySelector("#site-footer").innerHTML = `
    <div class="container footer-inner">
      <div><a class="logo" href="index.html">WorldCuisine</a><p>The world is served.</p></div>
      <ul>${NAV_LINKS.map((l) => `<li><a href="${l.href}">${l.label}</a></li>`).join("")}</ul>
      <p class="copyright">© ${new Date().getFullYear()} WorldCuisine. A student project. Data: TheMealDB, Wikipedia, flagcdn.</p>
    </div>`;
}

renderHeader();
renderFooter();
