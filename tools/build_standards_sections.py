import argparse
import html
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image
from pypdf import PdfReader


SOURCE_TITLE = "National Commercial & Industrial Insulatoin Standards"
SOURCE_ID = "national-commercial-and-industrial-insulatoin-standards"
SECTION_ROOT = f"{SOURCE_ID}-section"


def slugify(value):
    value = value.lower().replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "section"


def clean_text(value):
    return re.sub(r"\s+", " ", value or "").strip()


def optimize_image(source_bytes, out_path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    temp = out_path.with_suffix(".source")
    temp.write_bytes(source_bytes)
    try:
        with Image.open(temp) as image:
            image = image.convert("RGB")
            max_width = 1600
            if image.width > max_width:
                ratio = max_width / image.width
                size = (max_width, max(1, round(image.height * ratio)))
                image = image.resize(size, Image.Resampling.LANCZOS)
            image.save(out_path, "JPEG", quality=78, optimize=True)
    finally:
        temp.unlink(missing_ok=True)


def extract_page_images(pdf_path, image_dir, force=False):
    reader = PdfReader(str(pdf_path))
    pages = []
    for page_index, page in enumerate(reader.pages, start=1):
        out = image_dir / f"{SOURCE_ID}-p{page_index:03d}.jpg"
        if force or not out.exists():
            images = getattr(page, "images", [])
            if not images:
                continue
            optimize_image(images[0].data, out)
        pages.append({"page": page_index, "image": f"assets/pdf-images/{out.name}"})
    return pages


def ocr_image(powershell, helper, image_path):
    result = subprocess.run(
        [
            powershell,
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(helper),
            "-ImagePath",
            str(image_path),
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return clean_text(result.stdout)


def ocr_pages(pages, out_dir, helper, powershell="powershell.exe", force=False):
    ocr_path = out_dir / "data" / f"{SOURCE_ID}-ocr.json"
    existing = {}
    if ocr_path.exists() and not force:
        existing = {item["page"]: item for item in json.loads(ocr_path.read_text(encoding="utf-8"))}

    ocr = []
    for item in pages:
        page_number = item["page"]
        if page_number in existing:
            ocr.append(existing[page_number])
            continue
        image_path = out_dir / item["image"]
        text = ocr_image(powershell, helper, image_path)
        print(f"OCR page {page_number}: {len(text)} chars")
        ocr.append({"page": page_number, "image": item["image"], "text": text})

        if page_number % 10 == 0:
            ocr_path.write_text(json.dumps(ocr, indent=2), encoding="utf-8")

    ocr_path.write_text(json.dumps(ocr, indent=2), encoding="utf-8")
    return ocr


def infer_sections(ocr_pages):
    expected_headings = [
        (1, "Cover, Preface, Acknowledgment, Contents, and Plate Index"),
        (13, "Section I - Introduction"),
        (17, "Section II - Insulation Materials and Properties"),
        (37, "Section III - Insulation Systems Design"),
        (51, "Section IV - General Application Methods/Illustrations"),
        (151, "Section V - Specialized Applications Methods/Illustrations"),
        (207, "Section VI - Specification Writing"),
        (261, "Section VII - Project Coordination"),
        (265, "Section VIII - Maintenance"),
        (269, "Section IX - Insulation Thickness Programs"),
        (279, "Section X - Firestopping Systems"),
        (295, "Section XI - Glossary"),
        (317, "Section XII - Appendix Tables"),
    ]
    page_text = {page["page"]: page["text"].upper() for page in ocr_pages}
    known_scan = (
        len(ocr_pages) >= 358
        and "SECTION I" in page_text.get(13, "")
        and "SECTION X" in page_text.get(279, "")
        and "GLOSSARY" in page_text.get(295, "")
        and "APPENDIX TABLES" in page_text.get(317, "")
    )
    if known_scan:
        deduped = [{"start": start, "title": title} for start, title in expected_headings]
        for index, section in enumerate(deduped):
            next_start = deduped[index + 1]["start"] if index + 1 < len(deduped) else ocr_pages[-1]["page"] + 1
            section["end"] = next_start - 1
        return deduped

    contents_text = "\n".join(page["text"] for page in ocr_pages[:18])
    section_markers = []
    for match in re.finditer(r"SECTION\s+(\d{5})\s+([A-Z0-9 ,/&().:\-]+?)\s+(\d{1,3})\b", contents_text):
        number, title, page_number = match.groups()
        title = clean_text(title).title()
        section_markers.append((int(page_number), f"Section {number} - {title}"))

    deduped = []
    seen = set()
    for page_number, title in sorted(section_markers):
        key = (page_number, title)
        if key not in seen:
            deduped.append({"start": page_number, "title": title})
            seen.add(key)

    if not deduped:
        deduped = [
            {"start": 1, "title": "Cover and Front Matter"},
            {"start": 11, "title": "Index"},
        ]

    if deduped[0]["start"] > 1:
        deduped.insert(0, {"start": 1, "title": "Cover and Front Matter"})

    for index, section in enumerate(deduped):
        next_start = deduped[index + 1]["start"] if index + 1 < len(deduped) else ocr_pages[-1]["page"] + 1
        section["end"] = next_start - 1
    return deduped


def section_summary(pages):
    for page in pages:
        text = clean_text(page["text"])
        if len(text) > 80:
            return text[:360]
    return "OCR text and page images from the source PDF."


def write_section_page(out_dir, section, pages, prev_section, next_section):
    page_id = section["id"]
    page_path = out_dir / "pages" / section["pageFile"]

    nav = ['<nav class="section-nav">']
    if prev_section:
        nav.append(f'<a class="button ghost" href="{html.escape(prev_section["pageFile"])}">Previous</a>')
    nav.append('<a class="button ghost" href="../index.html#Standards%20%26%20Handbooks">Index</a>')
    nav.append(f'<a class="button ghost" href="{SOURCE_ID}-pdf-fd7d574065.html">Standards home</a>')
    if next_section:
        nav.append(f'<a class="button ghost" href="{html.escape(next_section["pageFile"])}">Next</a>')
    nav.append("</nav>")

    body = [
        '<!doctype html>',
        '<html lang="en">',
        "<head>",
        '  <meta charset="utf-8">',
        '  <meta name="viewport" content="width=device-width, initial-scale=1">',
        f"  <title>{html.escape(section['title'])}</title>",
        '  <link rel="stylesheet" href="../styles.css">',
        "</head>",
        '<body class="detail-page">',
        '  <main class="sheet detail standards-detail">',
        '    <a href="../index.html" class="back-link">Back to field notebook</a>',
        f"    <h1>{html.escape(section['title'])}</h1>",
        f'    <p class="meta">{html.escape(SOURCE_TITLE)} &middot; pages {section["start"]}-{section["end"]}</p>',
        "    " + "".join(nav),
    ]

    for pdf_page in pages:
        body.append(f'    <section class="text-page" id="page-{pdf_page["page"]}">')
        body.append(f'      <h2>Page {pdf_page["page"]}</h2>')
        body.append(f'      <figure class="page-scan"><a href="../{html.escape(pdf_page["image"])}"><img src="../{html.escape(pdf_page["image"])}" alt="Source scan page {pdf_page["page"]}"></a></figure>')
        text = pdf_page["text"].strip()
        if text:
            for paragraph in re.split(r"(?<=[.!?])\s+|\n+", text):
                paragraph = clean_text(paragraph)
                if paragraph:
                    body.append(f"      <p>{html.escape(paragraph)}</p>")
        else:
            body.append("      <p class=\"notice\">No OCR text was detected on this source page.</p>")
        body.append("    </section>")

    body.extend(["  </main>", "</body>", "</html>", ""])
    page_path.write_text("\n".join(body), encoding="utf-8")
    return page_id


def update_catalog(out_dir, sections, ocr_pages):
    catalog_path = out_dir / "data" / "catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    catalog["entries"] = [
        entry for entry in catalog["entries"]
        if not entry["id"].startswith(SECTION_ROOT)
    ]

    page_lookup = {page["page"]: page for page in ocr_pages}
    standards = next(
        (entry for entry in catalog["entries"] if entry["title"].lower() == SOURCE_TITLE.lower()),
        None,
    )
    if standards:
        standards["summary"] = "OCR section index for the National Commercial & Industrial Insulation Standards source PDF."
        standards["extraction"] = "pdf-ocr-sections"
        standards["assetStatus"] = "oversized-ocr"
        standards["downloadAllowed"] = False
        standards["sectionCount"] = len(sections)
        standards["thumbnailUrl"] = "assets/pdf-images/national-commercial-and-industrial-insulatoin-standards-p001.jpg"
        standards["searchText"] = clean_text(" ".join([standards["searchText"], " ".join(s["title"] for s in sections)]))[:60000]

    new_entries = []
    for section in sections:
        pages = [page_lookup[number] for number in range(section["start"], section["end"] + 1) if number in page_lookup]
        text = " ".join(page["text"] for page in pages)
        section_id = f"{SECTION_ROOT}-{section['start']:03d}-{slugify(section['title'])}"
        new_entries.append({
            "id": section_id,
            "title": section["title"],
            "category": "Standards & Handbooks",
            "extension": "OCR",
            "relativePath": f"{SOURCE_TITLE}.pdf#page={section['start']}",
            "sourcePath": str(out_dir / "pages" / section["pageFile"]),
            "sizeBytes": 0,
            "sizeMB": 0,
            "modified": datetime.now(timezone.utc).isoformat(),
            "summary": section_summary(pages),
            "assetUrl": None,
            "assetStatus": "text-resource",
            "downloadAllowed": False,
            "resourceMode": "ocr-section",
            "extraction": "windows-ocr",
            "pages": len(pages),
            "imageCount": len(pages),
            "images": [page["image"] for page in pages[:8]],
            "thumbnailUrl": pages[0]["image"] if pages else None,
            "pdfPages": [],
            "paragraphs": [],
            "tables": [],
            "sheets": [],
            "pageUrl": section["pageUrl"],
            "searchText": clean_text(" ".join([section["title"], text]))[:60000],
        })

    catalog["entries"].extend(new_entries)
    catalog["categories"] = sorted({entry["category"] for entry in catalog["entries"]})
    catalog["generatedAt"] = datetime.now(timezone.utc).isoformat()
    catalog_path.write_text(json.dumps(catalog, indent=2), encoding="utf-8")


def write_landing_page(out_dir, sections):
    page_path = out_dir / "pages" / f"{SOURCE_ID}-pdf-fd7d574065.html"
    links = "\n".join(
        f'<li><a href="{html.escape(section["pageFile"])}">{html.escape(section["title"])}</a><span>Pages {section["start"]}-{section["end"]}</span></li>'
        for section in sections
    )
    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(SOURCE_TITLE)}</title>
  <link rel="stylesheet" href="../styles.css">
</head>
<body class="detail-page">
  <main class="sheet detail standards-detail">
    <a href="../index.html" class="back-link">Back to field notebook</a>
    <h1>{html.escape(SOURCE_TITLE)}</h1>
    <p class="meta">Standards &amp; Handbooks &middot; PDF &middot; OCR section index</p>
    <p class="notice">This page contains OCR text and page images generated only from the supplied PDF. OCR can contain recognition errors, so each page includes the original scan image for verification.</p>
    <figure class="lead-image"><img src="../assets/pdf-images/{SOURCE_ID}-p001.jpg" alt="{html.escape(SOURCE_TITLE)} cover"></figure>
    <h2>Sections</h2>
    <ol class="section-list">
      {links}
    </ol>
  </main>
</body>
</html>
"""
    page_path.write_text(page, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--force-images", action="store_true")
    parser.add_argument("--force-ocr", action="store_true")
    parser.add_argument("--powershell", default="powershell.exe")
    args = parser.parse_args()

    pdf_path = Path(args.pdf).resolve()
    out_dir = Path(args.out).resolve()
    image_dir = out_dir / "assets" / "pdf-images"
    helper = out_dir / "tools" / "ocr_image.ps1"

    pages = extract_page_images(pdf_path, image_dir, force=args.force_images)
    ocr = ocr_pages(pages, out_dir, helper, args.powershell, force=args.force_ocr)
    sections = infer_sections(ocr)
    for section in sections:
        section["id"] = f"{SECTION_ROOT}-{section['start']:03d}-{slugify(section['title'])}"
        section["pageFile"] = f"{section['id']}.html"
        section["pageUrl"] = f"pages/{section['pageFile']}"

    for index, section in enumerate(sections):
        prev_section = sections[index - 1] if index > 0 else None
        next_section = sections[index + 1] if index + 1 < len(sections) else None
        section_pages = [page for page in ocr if section["start"] <= page["page"] <= section["end"]]
        write_section_page(out_dir, section, section_pages, prev_section, next_section)

    write_landing_page(out_dir, sections)
    update_catalog(out_dir, sections, ocr)
    print(f"Built {len(sections)} sections from {len(ocr)} OCR pages.")


if __name__ == "__main__":
    main()
