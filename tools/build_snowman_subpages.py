import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "data" / "catalog.json"
PDF_PATH = ROOT / "assets" / "files" / "snowmans-notes-half-size-e891d58d14.pdf"
PAGES_DIR = ROOT / "pages"
SUBPAGE_PREFIX = "snowmans-notes"


def clean_text(value):
    return re.sub(r"\s+", " ", value or "").strip()


def slugify(value):
    value = value.lower().replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "section"


def extract_page_texts():
    reader = PdfReader(str(PDF_PATH))
    pages = {}
    for index, page in enumerate(reader.pages, start=1):
        raw = page.extract_text() or ""
        lines = [clean_text(line) for line in raw.splitlines()]
        pages[index] = "\n".join(line for line in lines if line)
    return pages


def parse_contents(page_texts):
    content = "\n".join(page_texts.get(page, "") for page in (3, 4, 5))
    sections = []
    pending = []
    skip_titles = {"contents", "snowman's notes"}

    for raw_line in content.splitlines():
        line = clean_text(raw_line)
        if not line:
            continue
        if line.lower() in skip_titles:
            continue

        match = re.search(r"(.*?)(?:\s*\.+\s*|\s+)(\d{1,3})$", line)
        if match:
            title_part = clean_text(match.group(1).replace(".", " "))
            page = int(match.group(2))
            title = clean_text(" ".join(pending + [title_part]))
            pending = []
            if title and 1 <= page <= 200:
                sections.append({"title": title, "page": page})
        else:
            pending.append(line)

    deduped = []
    seen = set()
    for section in sections:
        key = (section["title"].lower(), section["page"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(section)
    return deduped


def page_body_for_range(page_texts, start, end):
    body = []
    for page in range(start, end + 1):
        text = page_texts.get(page, "")
        if not text:
            continue
        body.append(f"<section class=\"text-page\"><h2>Page {page}</h2>")
        for paragraph in text.split("\n"):
            paragraph = paragraph.strip()
            if paragraph:
                body.append(f"<p>{html.escape(paragraph)}</p>")
        body.append("</section>")
    return "\n".join(body)


def write_page(path, title, body, extra_head=""):
    page = f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{html.escape(title)}</title>
  <link rel=\"stylesheet\" href=\"../styles.css\">
  {extra_head}
</head>
<body class=\"detail-page\">
  <main class=\"sheet detail\">
    {body}
  </main>
</body>
</html>
"""
    path.write_text(page, encoding="utf-8")


def build_subpages(page_texts, sections):
    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    max_page = max(page_texts)
    section_links = []

    for index, section in enumerate(sections):
        next_page = sections[index + 1]["page"] if index + 1 < len(sections) else max_page + 1
        start = section["page"]
        end = max(start, next_page - 1)
        section_id = f"{SUBPAGE_PREFIX}-{start:03d}-{slugify(section['title'])}"
        page_url = f"pages/{section_id}.html"
        file_path = PAGES_DIR / f"{section_id}.html"

        prev_link = section_links[-1]["pageUrl"] if section_links else None
        next_title = sections[index + 1]["title"] if index + 1 < len(sections) else None
        next_id = None
        if next_title:
            next_id = f"pages/{SUBPAGE_PREFIX}-{next_page:03d}-{slugify(next_title)}.html"

        nav = ["<nav class=\"subsection-nav\">"]
        nav.append("<a href=\"snowmans-notes-subsections.html\" class=\"back-link\">Back to Snowman's subsections</a>")
        if prev_link:
            nav.append(f"<a href=\"../{html.escape(prev_link)}\">Previous</a>")
        if next_id:
            nav.append(f"<a href=\"../{html.escape(next_id)}\">Next</a>")
        nav.append("</nav>")

        source_link = "../assets/files/snowmans-notes-half-size-e891d58d14.pdf"
        body = [
            "".join(nav),
            f"<h1>{html.escape(section['title'])}</h1>",
            f"<p class=\"meta\">Snowman's Notes · pages {start}-{end} · PDF subsection</p>",
            f"<p><a class=\"button\" href=\"{source_link}#page={start}\">Open source PDF at page {start}</a></p>",
            page_body_for_range(page_texts, start, end),
        ]
        write_page(file_path, section["title"], "\n".join(body))

        summary = clean_text(page_texts.get(start, section["title"]))[:220]
        section_links.append(
            {
                "title": section["title"],
                "startPage": start,
                "endPage": end,
                "pageUrl": page_url,
                "summary": summary,
            }
        )

    return section_links


def write_subsection_index(section_links):
    cards = []
    for section in section_links:
        cards.append(
            "<a class=\"subsection-card\" href=\"../{url}\">"
            "<span>Pages {start}-{end}</span>"
            "<strong>{title}</strong>"
            "<p>{summary}</p>"
            "</a>".format(
                url=html.escape(section["pageUrl"]),
                start=section["startPage"],
                end=section["endPage"],
                title=html.escape(section["title"]),
                summary=html.escape(section["summary"]),
            )
        )

    body = "\n".join(
        [
            "<a href=\"../index.html\" class=\"back-link\">Back to field notebook</a>",
            "<h1>Snowman's Notes Subsections</h1>",
            f"<p class=\"meta\">{len(section_links)} linked subsections generated from the bundled Snowmans Notes Half Size PDF.</p>",
            "<div class=\"subsection-grid\">",
            "\n".join(cards),
            "</div>",
        ]
    )
    write_page(PAGES_DIR / "snowmans-notes-subsections.html", "Snowman's Notes Subsections", body)


def update_catalog(section_links):
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    catalog["snowmanSubsections"] = section_links
    catalog["snowmanSubsectionsGeneratedAt"] = datetime.now(timezone.utc).isoformat()
    CATALOG_PATH.write_text(json.dumps(catalog, indent=2), encoding="utf-8")


def main():
    page_texts = extract_page_texts()
    sections = parse_contents(page_texts)
    section_links = build_subpages(page_texts, sections)
    write_subsection_index(section_links)
    update_catalog(section_links)
    print(f"Built {len(section_links)} Snowman's Notes subsection pages.")


if __name__ == "__main__":
    main()
