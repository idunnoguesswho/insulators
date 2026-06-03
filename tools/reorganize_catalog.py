import html
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import import_insulator_book as importer


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "catalog.json"
PAGES = ROOT / "pages"


TAB_GROUPS = [
    {
        "id": "lessons",
        "title": "Lessons",
        "description": "Wiki-style instruction pages and short lessons.",
        "categories": ["Insulator Tools", "Module 2 Unit 3", "Notebook"],
        "resourceModes": ["ocr-section", "pdf-subchapter", "local-ocr", "text-resource"],
    },
    {
        "id": "reference-data",
        "title": "Reference Data",
        "description": "Merged charts, workbook tabs, tables, formulas, and quick lookups.",
        "categories": ["Reference Charts", "Book Supplements"],
        "resourceModes": ["merged-reference", "xlsx-sheet"],
    },
    {
        "id": "standards-safety",
        "title": "Standards & Safety",
        "description": "Standards, specs, firestopping, asbestos, hazards, and working rules.",
        "categories": ["Standards & Handbooks", "Safety & Firestopping"],
    },
    {
        "id": "drawings-images",
        "title": "Drawings & Images",
        "description": "Layout drawings, page scans, sketches, and standalone image references.",
        "categories": ["Layouts & Patterns", "Sketches & Images"],
        "hasImages": True,
    },
    {
        "id": "source-archive",
        "title": "Source Archive",
        "description": "Every source file and secondary duplicate kept for traceability.",
        "includeHidden": True,
        "all": True,
    },
]


def slugify(value):
    value = value.lower().replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "reference"


def norm_title(value):
    value = re.sub(r"\([^)]*\)", "", value.lower())
    value = value.replace("_", " ")
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def source_label(entry):
    path = entry.get("relativePath") or entry.get("title") or "Source"
    return path.split("#", 1)[0]


def entry_text(entry):
    parts = [entry.get("title", ""), entry.get("summary", ""), entry.get("searchText", "")]
    for sheet in entry.get("sheets", []):
        for row in sheet.get("rows", []):
            parts.append(" ".join(cell for cell in row if cell))
    return importer.clean_text(" ".join(parts))


def dedupe_rows(entries):
    rows = []
    seen = set()
    for entry in entries:
        for sheet in entry.get("sheets", []):
            for row in sheet.get("rows", []):
                cleaned = [cell for cell in row if cell]
                if not cleaned:
                    continue
                key = tuple(cell.lower() for cell in cleaned)
                if key in seen:
                    continue
                seen.add(key)
                rows.append(cleaned)
    return rows


def write_merged_reference_page(title, entries, rows, page_url):
    sections = []
    if rows:
        table_rows = []
        for idx, row in enumerate(rows[:160]):
            tag = "th" if idx == 0 else "td"
            table_rows.append("<tr>" + "".join(f"<{tag}>{html.escape(cell)}</{tag}>" for cell in row[:12]) + "</tr>")
        sections.append(f'''<section class="wiki-block">
  <h2>Merged Table</h2>
  <div class="table-wrap"><table>{''.join(table_rows)}</table></div>
</section>''')

    source_items = []
    for entry in entries:
        link = entry.get("pageUrl", "")
        source_items.append(
            f'<li><a href="../{html.escape(link)}">{html.escape(source_label(entry))}</a></li>'
            if link
            else f"<li>{html.escape(source_label(entry))}</li>"
        )
    sections.append(f'''<section class="wiki-block">
  <h2>Sources Merged</h2>
  <ul>{''.join(source_items)}</ul>
</section>''')

    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <link rel="stylesheet" href="../styles.css">
</head>
<body class="detail-page">
  <main class="sheet detail merged-reference-detail">
    <a href="../index.html" class="back-link">Back to field notebook</a>
    <p class="eyebrow">Merged Reference Data</p>
    <h1>{html.escape(title)}</h1>
    <p class="meta">{len(rows)} unique rows from {len(entries)} workbook tabs</p>
    {''.join(sections)}
  </main>
</body>
</html>
"""
    (ROOT / page_url).write_text(page, encoding="utf-8")


def make_merged_reference_entries(entries):
    groups = defaultdict(list)
    for entry in entries:
        if entry.get("resourceMode") == "xlsx-sheet":
            groups[norm_title(entry["title"])].append(entry)

    merged = []
    for key, grouped in sorted(groups.items()):
        if len(grouped) < 2 or key == "sheet2":
            continue
        title = grouped[0]["title"].strip()
        rows = dedupe_rows(grouped)
        merged_id = f"merged-reference-{slugify(title)}"
        page_url = f"pages/{merged_id}.html"
        write_merged_reference_page(title, grouped, rows, page_url)

        for entry in grouped:
            entry["browseHidden"] = True
            entry["mergedInto"] = merged_id

        text = importer.clean_text(" ".join(entry_text(entry) for entry in grouped))
        merged.append(
            {
                "id": merged_id,
                "title": title,
                "category": "Reference Charts",
                "topics": ["reference-charts", "book-supplements", "source-inventory"],
                "extension": "MERGED",
                "relativePath": " + ".join(entry["relativePath"] for entry in grouped),
                "sourcePath": " + ".join(entry.get("sourcePath", "") for entry in grouped),
                "sizeBytes": 0,
                "sizeMB": 0,
                "modified": datetime.now(timezone.utc).isoformat(),
                "summary": f"Merged quick reference table from {len(grouped)} matching workbook tabs with {len(rows)} unique rows.",
                "assetUrl": None,
                "assetStatus": "text-resource",
                "downloadAllowed": False,
                "resourceMode": "merged-reference",
                "extraction": "merged-reference",
                "pages": None,
                "imageCount": 0,
                "images": [],
                "thumbnailUrl": None,
                "pdfPages": [],
                "paragraphs": [],
                "tables": [rows[:80]],
                "sheets": [],
                "pageUrl": page_url,
                "searchText": text[:60000],
                "mergedSourceCount": len(grouped),
                "mergedSources": [entry["id"] for entry in grouped],
            }
        )
    return merged


def choose_primary(entries):
    def score(entry):
        score_value = 0
        if entry.get("local1Handbook") or entry.get("sectionCount"):
            score_value += 80
        if entry.get("resourceMode") in {"ocr-section", "local-ocr", "pdf-subchapter", "merged-reference"}:
            score_value += 40
        if entry.get("pdfPages") or entry.get("paragraphs") or entry.get("sheets"):
            score_value += 20
        if "processed/" in (entry.get("relativePath", "").lower()):
            score_value += 8
        if entry.get("assetStatus") == "bundled":
            score_value += 5
        return score_value

    return sorted(entries, key=score, reverse=True)[0]


def mark_duplicate_sources(entries):
    groups = defaultdict(list)
    for entry in entries:
        if entry.get("browseHidden") or entry.get("resourceMode") in {"xlsx-sheet", "merged-reference", "ocr-section", "local-ocr", "pdf-subchapter"}:
            continue
        groups[norm_title(entry["title"])].append(entry)

    for key, grouped in groups.items():
        if len(grouped) < 2:
            continue
        primary = choose_primary(grouped)
        primary["alternateSources"] = [
            {
                "title": entry["title"],
                "relativePath": entry.get("relativePath"),
                "pageUrl": entry.get("pageUrl"),
            }
            for entry in grouped
            if entry["id"] != primary["id"]
        ]
        primary["duplicateSourceCount"] = len(grouped)
        for entry in grouped:
            if entry["id"] == primary["id"]:
                continue
            entry["browseHidden"] = True
            entry["duplicateOf"] = primary["id"]


def group_matches(tab, entry):
    if tab.get("all"):
        return True
    if entry.get("category") in tab.get("categories", []):
        return True
    if entry.get("resourceMode") in tab.get("resourceModes", []):
        return True
    if tab.get("hasImages") and (entry.get("images") or entry.get("thumbnailUrl")):
        return True
    return False


def visible_for_topic(topic, entries):
    topic_entries = entries if topic.get("include_all") else [entry for entry in entries if topic["id"] in entry.get("topics", [])]
    if topic.get("include_all"):
        return topic_entries
    return [entry for entry in topic_entries if not entry.get("browseHidden")]


def refresh_topic_pages(catalog):
    topics = []
    visible_entries = [entry for entry in catalog["entries"] if not entry.get("browseHidden")]
    for topic in importer.TOPIC_DEFINITIONS:
        topic_entries = visible_for_topic(topic, catalog["entries"])
        page_topic = dict(topic)
        page_topic["description"] = topic["description"]
        importer.render_topic_page(page_topic, catalog["entries"] if topic.get("include_all") else visible_entries, ROOT)
        topics.append(
            {
                "id": topic["id"],
                "title": topic["title"],
                "description": topic["description"],
                "url": f"topics/{topic['id']}.html",
                "count": len(topic_entries),
            }
        )
    catalog["topics"] = topics


def main():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    catalog["entries"] = [entry for entry in catalog["entries"] if not entry["id"].startswith("merged-reference-")]

    merged = make_merged_reference_entries(catalog["entries"])
    catalog["entries"].extend(merged)
    mark_duplicate_sources(catalog["entries"])

    for tab in TAB_GROUPS:
        tab["count"] = sum(
            1
            for entry in catalog["entries"]
            if group_matches(tab, entry) and (tab.get("includeHidden") or not entry.get("browseHidden"))
        )

    catalog["tabGroups"] = TAB_GROUPS
    catalog["resourceCount"] = len(catalog["entries"])
    catalog["visibleResourceCount"] = sum(1 for entry in catalog["entries"] if not entry.get("browseHidden"))
    catalog["duplicateHiddenCount"] = sum(1 for entry in catalog["entries"] if entry.get("browseHidden"))
    catalog["categories"] = sorted({entry["category"] for entry in catalog["entries"] if not entry.get("browseHidden")})
    catalog["generatedAt"] = datetime.now(timezone.utc).isoformat()
    refresh_topic_pages(catalog)
    CATALOG.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    print(
        f"Reorganized {catalog['resourceCount']} resources into {catalog['visibleResourceCount']} visible cards; "
        f"merged {len(merged)} reference groups."
    )


if __name__ == "__main__":
    main()
