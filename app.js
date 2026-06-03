const state = {
  catalog: null,
  tab: "all",
  query: "",
};

const els = {
  tabs: document.querySelector("#categoryTabs"),
  grid: document.querySelector("#cardGrid"),
  template: document.querySelector("#cardTemplate"),
  search: document.querySelector("#searchInput"),
  topicGrid: document.querySelector("#topicGrid"),
  title: document.querySelector("#resultTitle"),
  meta: document.querySelector("#resultMeta"),
  theme: document.querySelector("#themeToggle"),
  chartCount: document.querySelector("#chartCount"),
  supplementCount: document.querySelector("#supplementCount"),
  layoutCount: document.querySelector("#layoutCount"),
  referenceMeta: document.querySelector("#referenceMeta"),
  referenceList: document.querySelector("#referenceList"),
};

function normalize(value) {
  return (value || "").toLowerCase();
}

function formatStatus(entry) {
  if (entry.resourceMode === "merged-reference") return `${entry.mergedSourceCount || 0} reference tabs merged`;
  if (entry.duplicateSourceCount) return `${entry.duplicateSourceCount} matching source copies grouped`;
  if (entry.assetStatus === "text-resource") return "Converted to a text-based tool resource";
  if (entry.extraction === "pdf-needs-ocr") return "Scanned PDF: OCR recommended";
  if (entry.assetStatus === "oversized") return "Too large to bundle for free static hosting";
  if (entry.assetStatus === "bundled") return "Bundled for offline-style access";
  return entry.extraction || "";
}

function resourceKind(entry) {
  const haystack = normalize(`${entry.title} ${entry.category} ${entry.relativePath}`);
  if (entry.resourceMode === "merged-reference") return "Merged reference";
  if (entry.resourceMode === "xlsx-sheet" || /chart|table|card|size|flange|fraction|decimal|reference/.test(haystack)) {
    return "Quick reference";
  }
  if (/lesson|unit|development|tee|gore|layout|pattern|method|formula|section|handbook|notebook/.test(haystack)) {
    return "Short lesson";
  }
  if (entry.thumbnailUrl || entry.extension === "JPG" || entry.extension === "PNG") return "Image reference";
  return "Source record";
}

function visibleEntries() {
  return state.catalog.entries.filter((entry) => !entry.browseHidden);
}

function tabGroups() {
  return [
    {
      id: "all",
      title: "All",
      description: "Everything except secondary duplicate cards.",
    },
    ...(state.catalog.tabGroups || []),
  ];
}

function tabMatches(tab, entry) {
  if (tab.id === "all") return !entry.browseHidden;
  if (!tab.includeHidden && entry.browseHidden) return false;
  if (tab.all) return true;
  if ((tab.categories || []).includes(entry.category)) return true;
  if ((tab.resourceModes || []).includes(entry.resourceMode)) return true;
  if (tab.hasImages && (entry.images?.length || entry.thumbnailUrl)) return true;
  return false;
}

function activeTab() {
  return tabGroups().find((tab) => tab.id === state.tab) || tabGroups()[0];
}

function filteredEntries() {
  const q = normalize(state.query);
  const tab = activeTab();
  return state.catalog.entries.filter((entry) => {
    const categoryMatch = tabMatches(tab, entry);
    const queryMatch = !q || normalize(entry.searchText).includes(q);
    return categoryMatch && queryMatch;
  });
}

function setTab(tabId) {
  state.tab = tabId;
  if (tabId !== "all") window.location.hash = encodeURIComponent(tabId);
  else history.replaceState(null, "", window.location.pathname);
  render();
}

function renderTabs() {
  els.tabs.innerHTML = "";
  tabGroups().forEach((group) => {
    const button = document.createElement("button");
    button.className = "tab";
    button.type = "button";
    const count = group.id === "all" ? visibleEntries().length : group.count;
    button.textContent = `${group.title} ${count ?? ""}`.trim();
    button.title = group.description || group.title;
    button.setAttribute("aria-selected", String(group.id === state.tab));
    button.addEventListener("click", () => setTab(group.id));
    els.tabs.appendChild(button);
  });
}

function renderCards() {
  const entries = filteredEntries();
  els.grid.innerHTML = "";
  const tab = activeTab();
  els.title.textContent = tab.id === "all" ? "All lessons and references" : tab.title;
  const total = tab.includeHidden ? state.catalog.entries.length : visibleEntries().length;
  els.meta.textContent = `${entries.length} shown / ${total} browse cards`;

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
    card.querySelector(".pill").textContent = resourceKind(entry);
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
  const count = (category) => visibleEntries().filter((entry) => entry.category === category).length;
  els.chartCount.textContent = count("Reference Charts");
  els.supplementCount.textContent = count("Book Supplements");
  els.layoutCount.textContent = count("Layouts & Patterns");
}

function renderTopics() {
  if (!els.topicGrid) return;
  els.topicGrid.innerHTML = "";
  for (const topic of state.catalog.topics || []) {
    const link = document.createElement("a");
    link.className = "topic-card";
    link.href = topic.url;
    link.innerHTML = `<span>${topic.count} lessons / refs</span><strong>${topic.title}</strong><p>${topic.description}</p>`;
    els.topicGrid.appendChild(link);
  }
}

function renderReferences() {
  if (!els.referenceList) return;
  const references = new Map();
  for (const entry of state.catalog.entries) {
    if (entry.resourceMode === "merged-reference") continue;
    const key = (entry.relativePath || entry.title).split("#", 1)[0];
    if (!references.has(key)) {
      references.set(key, {
        title: key,
        sourcePath: entry.sourcePath || "",
        category: entry.category || "Reference",
      });
    }
  }

  const sorted = Array.from(references.values()).sort((a, b) => a.title.localeCompare(b.title));
  els.referenceMeta.textContent = `${sorted.length} source files processed from ${state.catalog.sourceRoot || "the source folder"}.`;
  els.referenceList.innerHTML = "";
  for (const reference of sorted) {
    const item = document.createElement("li");
    item.textContent = `${reference.title} (${reference.category})`;
    els.referenceList.appendChild(item);
  }
}

function render() {
  renderTabs();
  renderTopics();
  renderCards();
  renderCounts();
  renderReferences();
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
  if (hash && tabGroups().some((tab) => tab.id === hash)) state.tab = hash;
  render();
}

init().catch((error) => {
  els.meta.textContent = "Could not load catalog data.";
  console.error(error);
});
