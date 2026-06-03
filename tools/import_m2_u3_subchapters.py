import html
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image
from pypdf import PdfReader


SOURCE = Path(r"F:\Insulator Book\m2_u3.pdf")
OUT = Path(__file__).resolve().parents[1]
CATALOG = OUT / "data" / "catalog.json"
IMAGE_DIR = OUT / "assets" / "pdf-images" / "m2-u3"
PAGE_DIR = OUT / "pages"
SOURCE_ID = "m2-u3"
CATEGORY = "Module 2 Unit 3"


SECTIONS = [
    ("unit-objective", "Unit Objective", "Unit Objective"),
    ("introduction", "Introduction", "Introduction"),
    ("1-0-pattern-development", "1.0 Pattern Development", "1.0 Pattern Development"),
    ("1-1-parallel-line-development", "1.1 Parallel Line Development", "1.1 Parallel Line Development"),
    ("1-2-position-of-joint-lines", "1.2 Position of Joint lines", "1.2 Position of Joint lines"),
    (
        "1-3-construction-lines-lettering-numbering",
        "1.3 Use of Construction Lines, Lettering and Numbering",
        "1.3 Use of Construction Lines, Lettering and Numbering",
    ),
    ("2-0-development-of-cylindrical-fittings", "2.0 Development of Cylindrical Fittings", "2.0 Development of"),
    ("2-1-development-of-an-elbow-joint", "2.1 Development of an Elbow Joint", "2.1 Development of an Elbow Joint"),
    ("2-2-development-of-an-offset", "2.2 Development of an Offset", "2.2 Development of an Offset"),
    (
        "2-3-development-of-90-segmental-bend-1-full-2-half",
        "2.3 Development of a 90º Segmental bend -1 Full, 2 Half Segments",
        "2.3 Development of a 90º Segmental bend",
    ),
    (
        "2-4-development-of-90-segmental-bend-5-full-2-half",
        "2.4 Development of a 90º Segmental Bend -5 Full, 2 Half Segments",
        "2.4 Development of a 90º Segmental Bend",
    ),
    ("2-5-segmental-joints-simplified", "2.5 Segmental Joints (Simplified)", "2.5 Segmental Joints"),
    (
        "2-6-efficient-drawing-layout",
        "2.6 Efficient Drawing Layout and Sequencing of Layouts",
        "2.6 Efficient Drawing Layout and Sequencing",
    ),
    ("summary", "Summary", "Summary"),
]


IMAGE_ASSIGNMENTS = {
    "unit-objective": [4],
    "1-1-parallel-line-development": [6, 7],
    "2-1-development-of-an-elbow-joint": [9],
    "2-2-development-of-an-offset": [10, 11],
    "2-3-development-of-90-segmental-bend-1-full-2-half": [12],
    "2-4-development-of-90-segmental-bend-5-full-2-half": [13],
}


SECTION_PAGES = {
    "unit-objective": [4],
    "introduction": [5],
    "1-0-pattern-development": [6],
    "1-1-parallel-line-development": [6, 7, 8],
    "1-2-position-of-joint-lines": [8],
    "1-3-construction-lines-lettering-numbering": [8],
    "2-0-development-of-cylindrical-fittings": [9],
    "2-1-development-of-an-elbow-joint": [9, 10],
    "2-2-development-of-an-offset": [10, 11],
    "2-3-development-of-90-segmental-bend-1-full-2-half": [11, 12],
    "2-4-development-of-90-segmental-bend-5-full-2-half": [12, 13],
    "2-5-segmental-joints-simplified": [13, 14],
    "2-6-efficient-drawing-layout": [14],
    "summary": [15],
}


BOILERPLATE = {
    "Module 2– Unit 3",
    "Module 2- Unit 3",
    "Industrial Insulation Phase 2",
    "Parallel Line Development",
    "Revision 2.0, August 2014",
}


def clean_text(value):
    value = value.replace("\u00a0", " ")
    value = value.replace("\uf0b7", "-")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def normalize(value):
    return re.sub(r"\s+", " ", clean_text(value)).lower()


def summary(text):
    text = clean_text(text)
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return " ".join(sentences[:2])[:340].strip() or "Text section from Module 2 Unit 3."


def clean_section_body(text):
    lines = []
    for raw_line in clean_text(text).splitlines():
        line = raw_line.strip()
        if not line or line in BOILERPLATE or re.fullmatch(r"\d+", line):
            continue
        lines.append(line)

    paragraphs = []
    current = []
    for line in lines:
        is_standalone = (
            line.startswith("-")
            or line.startswith("Figure ")
            or line.startswith("Note:")
            or line.startswith("Refer to")
            or re.match(r"^\d\.\d", line)
            or line in {"Key Learning Points", "Truncated Cylinder", "The Development of Figure 2"}
        )
        if is_standalone:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            paragraphs.append(line)
        else:
            current.append(line)
    if current:
        paragraphs.append(" ".join(current))
    return "\n\n".join(paragraphs)


def page_texts(reader):
    pages = []
    for page_number, page in enumerate(reader.pages, start=1):
        pages.append(
            {
                "page": page_number,
                "text": clean_text(page.extract_text() or ""),
            }
        )
    return pages


def section_ranges(pages):
    joined = "\n\n".join(f"[[PAGE:{page['page']}]]\n{page['text']}" for page in pages[3:15])
    compact = normalize(joined)
    starts = []
    for section_id, title, marker in SECTIONS:
        idx = compact.find(normalize(marker))
        if idx < 0:
            raise RuntimeError(f"Could not locate section marker: {title}")
        starts.append((idx, section_id, title))
    starts.sort()

    sections = []
    for pos, (start, section_id, title) in enumerate(starts):
        end = starts[pos + 1][0] if pos + 1 < len(starts) else len(compact)
        raw_start = map_compact_to_raw(joined, start)
        raw_end = map_compact_to_raw(joined, end)
        chunk = clean_text(joined[raw_start:raw_end])
        chunk = re.sub(r"^\[\[PAGE:\d+\]\]\s*", "", chunk)
        chunk = re.sub(r"\[\[PAGE:\d+\]\]\s*", "", chunk)
        sections.append(
            {
                "id": section_id,
                "title": title,
                "text": clean_section_body(chunk),
                "sourcePages": SECTION_PAGES[section_id],
            }
        )
    return sections


def map_compact_to_raw(raw, compact_index):
    raw_pos = compact_pos = 0
    in_space = False
    while raw_pos < len(raw) and compact_pos < compact_index:
        char = raw[raw_pos]
        replacement = " " if char.isspace() else char.lower()
        if replacement == " ":
            if not in_space:
                compact_pos += 1
            in_space = True
        else:
            compact_pos += 1
            in_space = False
        raw_pos += 1
    return raw_pos


def find_section_pages(pages, title):
    needle = normalize(title.split(" ", 1)[-1])
    return [page["page"] for page in pages if needle in normalize(page["text"])]


def extract_images(reader):
    if IMAGE_DIR.exists():
        for old_image in IMAGE_DIR.iterdir():
            if old_image.is_file():
                old_image.unlink()
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    extracted = {}
    for page_number, page in enumerate(reader.pages, start=1):
        page_images = []
        for image_index, image in enumerate(getattr(page, "images", []), start=1):
            ext = Path(image.name).suffix.lower()
            if ext not in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
                ext = ".jpg"
            filename = f"m2-u3-p{page_number:03d}-{image_index:02d}{ext}"
            target = IMAGE_DIR / filename
            target.write_bytes(image.data)
            with Image.open(target) as opened:
                width, height = opened.size
            if width < 200 or height < 200:
                target.unlink(missing_ok=True)
                continue
            page_images.append(
                {
                    "url": f"assets/pdf-images/m2-u3/{filename}",
                    "page": page_number,
                    "width": width,
                    "height": height,
                }
            )
        if page_images:
            extracted[page_number] = page_images
    return extracted


def render_text(text):
    parts = []
    for block in re.split(r"\n\s*\n", text):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        if len(lines) > 1 and all(line.startswith("-") for line in lines):
            parts.append("<ul>")
            for line in lines:
                parts.append(f"<li>{html.escape(line.lstrip('- '))}</li>")
            parts.append("</ul>")
        else:
            for line in lines:
                parts.append(f"<p>{html.escape(line)}</p>")
    return "\n".join(parts)


def build_page(section, images):
    image_html = ""
    if images:
        image_html = "<h2>Images from the Document</h2><div class=\"image-grid\">\n"
        for image in images:
            image_html += (
                f"<a href=\"../{html.escape(image['url'])}\">"
                f"<img src=\"../{html.escape(image['url'])}\" "
                f"alt=\"{html.escape(section['title'])} diagram from page {image['page']}\"></a>\n"
            )
        image_html += "</div>"

    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(section['title'])}</title>
  <link rel="stylesheet" href="../styles.css">
</head>
<body class="detail-page">
  <main class="sheet detail">
    <a href="../index.html" class="back-link">Back to field notebook</a>
    <p class="eyebrow">Module 2 Unit 3</p>
    <h1>{html.escape(section['title'])}</h1>
    <p class="meta">Parallel Line Development · PDF text section · Source pages {", ".join(str(page) for page in section["sourcePages"])}</p>
    <section class="text-page">
      {render_text(section["text"])}
    </section>
    {image_html}
  </main>
</body>
</html>
"""
    PAGE_DIR.mkdir(parents=True, exist_ok=True)
    (PAGE_DIR / f"{SOURCE_ID}-{section['id']}.html").write_text(page, encoding="utf-8")


def catalog_entry(section, images, pdf_size_mb):
    title = f"M2 U3: {section['title']}"
    search_text = " ".join(
        [
            title,
            CATEGORY,
            "Parallel Line Development Geometry Pattern Development Industrial Insulation",
            section["text"],
        ]
    )
    return {
        "id": f"{SOURCE_ID}-{section['id']}",
        "title": title,
        "category": CATEGORY,
        "extension": "PDF",
        "relativePath": f"m2_u3.pdf#{section['id']}",
        "sourcePath": str(SOURCE),
        "sizeBytes": SOURCE.stat().st_size,
        "sizeMB": pdf_size_mb,
        "modified": datetime.fromtimestamp(SOURCE.stat().st_mtime, tz=timezone.utc).isoformat(),
        "summary": summary(section["text"]),
        "assetUrl": None,
        "assetStatus": "text-resource",
        "downloadAllowed": False,
        "resourceMode": "text-resource",
        "extraction": "pdf-subchapter-text",
        "pages": section["sourcePages"],
        "imageCount": len(images),
        "images": [image["url"] for image in images],
        "thumbnailUrl": images[0]["url"] if images else None,
        "pdfPages": [{"page": page, "text": section["text"]} for page in section["sourcePages"][:1]],
        "paragraphs": [],
        "tables": [],
        "sheets": [],
        "searchText": clean_text(search_text)[:60000],
        "pageUrl": f"pages/{SOURCE_ID}-{section['id']}.html",
    }


def main():
    reader = PdfReader(str(SOURCE))
    pages = page_texts(reader)
    sections = section_ranges(pages)
    images_by_page = extract_images(reader)
    pdf_size_mb = round(SOURCE.stat().st_size / (1024 * 1024), 2)

    entries = []
    for old_page in PAGE_DIR.glob(f"{SOURCE_ID}-*.html"):
        old_page.unlink()
    for section in sections:
        assigned_pages = IMAGE_ASSIGNMENTS.get(section["id"], section["sourcePages"])
        images = [image for page in assigned_pages for image in images_by_page.get(page, [])]
        build_page(section, images)
        entries.append(catalog_entry(section, images, pdf_size_mb))

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    catalog["entries"] = [
        entry
        for entry in catalog["entries"]
        if not entry.get("id", "").startswith(f"{SOURCE_ID}-")
    ]
    catalog["entries"].extend(entries)
    catalog["entries"].sort(key=lambda entry: (entry["category"], entry["title"]))
    catalog["categories"] = sorted({entry["category"] for entry in catalog["entries"]})
    catalog["generatedAt"] = datetime.now(timezone.utc).isoformat()
    CATALOG.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    print(f"Imported {len(entries)} subchapters from {SOURCE.name}")


if __name__ == "__main__":
    main()
