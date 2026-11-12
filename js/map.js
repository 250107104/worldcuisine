// Interactive SVG world map.
// Data: free GeoJSON (johan/world.geo.json). Fetched, then drawn as <path> elements.
import { getCountryByIso3 } from "./data.js";
import { errorBlock, loadingBlock } from "./utils.js";

// Local copy of free GeoJSON (johan/world.geo.json) — no internet needed for the map itself
const GEO_URL = "data/world.geo.json";
const WIDTH = 1000;
const HEIGHT = 392; // latitudes 83°N to 58°S (Antarctica left out)
const SCALE = WIDTH / 360;

// Longitude/latitude -> SVG x/y (simple equirectangular projection)
function project([lon, lat]) {
  return [((lon + 180) * SCALE).toFixed(1), ((83 - lat) * SCALE).toFixed(1)];
}

function ringToPath(ring) {
  return ring.map((point, i) => (i === 0 ? "M" : "L") + project(point).join(" ")).join("") + "Z";
}

function geometryToPath(geometry) {
  const polygons = geometry.type === "Polygon" ? [geometry.coordinates] : geometry.coordinates;
  return polygons.map((polygon) => polygon.map(ringToPath).join("")).join("");
}

function buildSvg(features) {
  const paths = features
    .filter((f) => f.id !== "ATA")
    .map((f) => {
      const hasData = Boolean(getCountryByIso3(f.id));
      const name = f.properties.name;
      const extra = hasData ? 'tabindex="0" role="button"' : "";
      return `<path class="country ${hasData ? "has-data" : ""}" data-iso3="${f.id}" data-name="${name}"
        aria-label="${name}" ${extra} d="${geometryToPath(f.geometry)}"><title>${name}</title></path>`;
    })
    .join("");
  return `<svg class="map-svg" viewBox="0 0 ${WIDTH} ${HEIGHT}" role="group" aria-label="World map">${paths}</svg>`;
}

/**
 * initMap(container, onSelect)
 * onSelect({ iso3, name }) is called when a country is clicked.
 */
export async function initMap(container, onSelect) {
  container.innerHTML = loadingBlock("Loading map");

  try {
    const response = await fetch(GEO_URL);
    if (!response.ok) throw new Error("HTTP " + response.status);
    const geo = await response.json();
    container.innerHTML = buildSvg(geo.features);
  } catch (error) {
    console.error("Map error:", error);
    const hint = window.location.protocol === "file:" ? "Open the site through a local server (Live Server), not by double-clicking the file." : "Check that data/world.geo.json exists.";
    errorBlock(container, "Could not load the map. " + hint, () => initMap(container, onSelect));
    return;
  }

  function select(path) {
    container.querySelectorAll(".selected").forEach((p) => p.classList.remove("selected"));
    path.classList.add("selected");
    onSelect({ iso3: path.dataset.iso3, name: path.dataset.name });
  }

  // One listener on the whole map (event delegation)
  container.addEventListener("click", (e) => {
    const path = e.target.closest(".country");
    if (path) select(path);
  });
  container.addEventListener("keydown", (e) => {
    const path = e.target.closest(".country");
    if (path && (e.key === "Enter" || e.key === " ")) {
      e.preventDefault();
      select(path);
    }
  });
}
