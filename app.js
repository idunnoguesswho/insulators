const state = {
  catalog: null,
  category: "All",
  query: "",
};

const els = {
  tabs: document.querySelector("#categoryTabs"),
  grid: document.querySelector("#cardGrid"),
  template: document.querySelector("#cardTemplate"),
  search: document.querySelector("#searchInput"),
  title: document.querySelector("#resultTitle"),
  meta: document.querySelector("#resultMeta"),
  theme: document.querySelector("#themeToggle"),
  chartCount: document.querySelector("#chartCount"),
  supplementCount: document.querySelector("#supplementCount"),
  layoutCount: document.querySelector("#layoutCount"),
};

function normalize(value) {
  return (value || "").toLowerCase();
}

function formatStatus(entry) {
  if (entry.assetStatus === "text-resource") return "Converted to a text-based tool resource";
  if (entry.extraction === "pdf-needs-ocr") return "Scanned PDF: OCR recommended";
  if (entry.assetStatus === "oversized") return "Too large to bundle for free static hosting";
  if (entry.assetStatus === "bundled") return "Bundled for offline-style access";
  return entry.extraction || "";
}

function filteredEntries() {
  const q = normalize(state.query);
  return state.catalog.entries.filter((entry) => {
    const categoryMatch = state.category === "All" || entry.category === state.category;
    const queryMatch = !q || normalize(entry.searchText).includes(q);
    return categoryMatch && queryMatch;
  });
}

function setCategory(category) {
  state.category = category;
  if (category !== "All") window.location.hash = encodeURIComponent(category);
  render();
}

function renderTabs() {
  els.tabs.innerHTML = "";
  ["All", ...state.catalog.categories].forEach((category) => {
    const tab = document.createElement("button");
    tab.className = "tab";
    tab.type = "button";
    tab.textContent = category;
    tab.setAttribute("aria-selected", String(category === state.category));
    tab.addEventListener("click", () => setCategory(category));
    els.tabs.appendChild(tab);
  });
}

function renderCards() {
  const entries = filteredEntries();
  els.grid.innerHTML = "";
  els.title.textContent = state.category === "All" ? "All references" : state.category;
  els.meta.textContent = `${entries.length} of ${state.catalog.entries.length} files`;

  for (const entry of entries) {
    const card = els.template.content.cloneNode(true);
    const article = card.querySelector(".resource-card");
    if (entry.thumbnailUrl) {
      const thumb = document.createElement("img");
      thumb.className = "card-thumb";
      thumb.src = entry.thumbnailUrl;
      thumb.alt = "";
      article.insertBefore(thumb, article.querySelector(".card-top"));
    }
    card.querySelector(".pill").textContent = entry.extension;
    card.querySelector(".file-size").textContent = `${entry.sizeMB} MB`;
    card.querySelector("h3").textContent = entry.title;
    card.querySelector(".summary").textContent = entry.summary;
    card.querySelector(".detail-link").href = entry.pageUrl;
    const asset = card.querySelector(".asset-link");
    if (entry.assetUrl && entry.downloadAllowed !== false) {
      asset.href = entry.assetUrl;
    } else {
      asset.remove();
    }
    card.querySelector(".status").textContent = formatStatus(entry);
    els.grid.appendChild(card);
  }
}

function renderCounts() {
  const count = (category) => state.catalog.entries.filter((entry) => entry.category === category).length;
  els.chartCount.textContent = count("Reference Charts");
  els.supplementCount.textContent = count("Book Supplements");
  els.layoutCount.textContent = count("Layouts & Patterns");
}

function render() {
  renderTabs();
  renderCards();
  renderCounts();
}

function loadTheme() {
  const saved = localStorage.getItem("insulator-theme");
  if (saved) document.documentElement.dataset.theme = saved;
}

function toggleTheme() {
  const current = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = current;
  localStorage.setItem("insulator-theme", current);
}

async function init() {
  loadTheme();
  els.theme.addEventListener("click", toggleTheme);
  els.search.addEventListener("input", (event) => {
    state.query = event.target.value;
    renderCards();
  });

  const response = await fetch("data/catalog.json");
  state.catalog = await response.json();
  const hash = decodeURIComponent(window.location.hash.replace("#", ""));
  if (hash && state.catalog.categories.includes(hash)) state.category = hash;
  render();
}

init().catch((error) => {
  els.meta.textContent = "Could not load catalog data.";
  console.error(error);
});
