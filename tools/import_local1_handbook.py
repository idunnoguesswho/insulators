import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path


SOURCE_PDF = Path(r"F:\Insulator Book\Insulator Tools\Local 1 Handbook.pdf")
OCR_JSON = Path("data/local-1-handbook-ocr.json")
CATALOG_JSON = Path("data/catalog.json")
PAGES_DIR = Path("pages")
HANDBOOK_ID = "local-1-handbook"


TOC = {
    1: "Table of Contents 1 & 2",
    2: "Dedication",
    3: "Introduction and Acknowledgement",
    4: "Basic Tool List & Decimal Equivalent Chart",
    5: "Refrigeration Fittings",
    6: "Long Radius Rubber 90 Degree Elbow",
    7: "Short Radius Rubber 90 Degree Elbow",
    8: "Equal Reducing Rubber 90 Degree Elbow",
    9: "Lag Chart and Dimensions for Beveled Block Lags",
    10: "Parts of a Circle",
    11: "Geometric Construction 1",
    12: "Geometric Construction 2",
    13: "Ellipse Construction",
    14: "Dividing a Circle into a Selected Number of Parts",
    15: "Jacketing Chart",
    16: "Pipe Sizes and Basic Math Formulas",
    17: "One and Two-piece End-caps",
    18: "Formula for a 45 Degree Conical",
    19: "Another Method for a 45 Degree Conical",
    20: "Formula for an Equal Tee",
    21: "Formula for an Unequal Tee",
    22: "Layouts for Equal and Unequal Tees (Stem Portions Only)",
    23: "Another Method for an Unequal Tee (Stem Portion)",
    24: "Formula for a 45 Degree Equal Lateral",
    25: "Another Method for a 45 Degree Equal Lateral",
    26: "Formula for an Unequal 45 Degree Lateral",
    27: "Diagram for an Unequal 45 Degree Lateral",
    28: "Concentric Reducer (Equal Cone) Reducer",
    29: "Layout for a Cone or Taper",
    30: "Eccentric Reducer (Hog Nose)",
    31: "Conic Reducing Tee at 90 Degrees",
    32: "Diagram for a Conic Reducing Tee at 90 Degrees",
    33: "Square to Round",
    34: "Square to Round (Where Round is Larger)",
    35: "Round to Square",
    36: "Rectangular to Round",
    37: "Square to Square Transition",
    38: "Oval to Round",
    39: "Square to Round (Single Offset)",
    40: "Square to Round (Double Offset)",
    41: "Square to Round (Double Offset) Round is Outside the Square",
    42: "Enlarging or Reducing a Pattern",
    43: "Long Radius Miter Chart",
    44: "Short Radius Miter Chart",
    45: "Gore Chart",
    46: "Heel and Throat Using Machinists Figures",
    47: "Heat Traced Piping & Sweeps & Field Bends",
    48: "Formula for a Gore Pattern (Regular Method)",
    49: "Short-cut Method for Gore Layouts",
    50: "Short-cut Method for Metal Gores",
    51: "Rise Method for a 90 Degree Elbow",
    52: "Gores for Long Radius 90 Degree Elbow",
    53: "Three-piece 90 Degree Short Radius Elbow",
    54: "Two-piece 45 Degree Elbow by Rise",
    55: "Negative Throat Elbows",
    56: "Diagram for Negative Throat Elbows",
    57: "Four-piece Short Radius 90 Degree Elbow w/Negative Throat",
    58: "Five-piece Long Radius Duct 90 Degree Elbow",
    59: "Four-piece Short Radius Duct 90 Degree Elbow",
    60: "Negative Throat Plug 90 Degree Metal Layout",
    61: "Four or Six-piece Flat-end Tank with a Rise",
    62: "Snap-line Gores",
    63: "Orange-peel Gores",
    64: "Diameter Method for Orange-peel Gores",
    65: "Six Division Method for Orange-peel Gores",
    66: "Another Method for Gores to a Domed Head",
    67: "Cone with a Slanted Top",
    68: "Round Three-piece Offset",
    69: "Off-center Taper",
    70: "Diagram for Off-center Taper",
    71: "Three-piece 90 Degree Elbow with a Round Branch",
    72: "Cone with a 90 Degree Square Run-out and a 45 Degree Round Run-out",
    73: "Diagram for Cone with a 90 Degree Square Run-out and a 45 Degree Round Run-out",
    74: "Taper with a 90 Degree Round Run-out",
    75: "Diagram for a Taper with a 90 Degree Round Run-out",
    76: "Combination Layout Text 1",
    77: "Combination Layout Text 2",
    78: "Diagram 1 for a Combination Layout",
    79: "Diagram 2 for a Combination Layout",
    80: "Two-way Y Branch",
    81: "Diagram for Two-way Y Branch",
    82: "Finding Dimensions for Cones and Transitions",
    83: "Determining the Radius of a Curve (Geometric & Algebraic)",
}


SECTION_FOR_SEQ = {
    2: 1,
    3: 1,
    4: 5,
    5: 4,
    6: 6,
    7: 7,
    8: 8,
    9: 10,
    10: 11,
    11: 12,
    12: 13,
    13: 14,
    14: 15,
    15: 16,
    16: 17,
    17: 18,
    18: 19,
    19: 20,
    20: 21,
    21: 22,
    22: 23,
    23: 24,
    24: 25,
    25: 26,
    26: 27,
    27: 28,
    28: 29,
    29: 30,
    30: 31,
    31: 32,
    32: 33,
    33: 34,
    34: 35,
    35: 36,
    36: 37,
    37: 38,
    38: 39,
    39: 40,
    40: 41,
    41: 42,
    42: 43,
    43: 44,
    44: 45,
    45: 46,
    46: 47,
    47: 48,
    48: 49,
    49: 50,
    50: 51,
    51: 52,
    52: 53,
    53: 54,
    54: 55,
    55: 56,
    56: 57,
    57: 58,
    58: 59,
    59: 60,
    60: 61,
    61: 62,
    62: 63,
    63: 64,
    64: 65,
    65: 66,
    66: 67,
    67: 68,
    68: 69,
    69: 70,
    70: 71,
    71: 72,
    72: 73,
    73: 74,
    74: 75,
    75: 76,
    76: 77,
    77: 78,
    78: 79,
    79: 80,
    80: 81,
    81: 82,
    82: 83,
}


def slugify(value):
    value = value.lower().replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "section"


def clean_text(value):
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"\s+", " ", line).strip() for line in value.split("\n")]
    return "\n".join(line for line in lines if line)


def summary_for(records, fallback):
    text = clean_text("\n".join(record.get("text", "") for record in records))
    if not text:
        return fallback
    text = re.sub(r"\s+", " ", text)
    return text[:360].strip()


def page_shell(title, body):
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <link rel="stylesheet" href="../styles.css">
</head>
<body class="detail-page">
  <main class="sheet detail handbook-detail">
    <a href="../index.html" class="back-link">Back to field notebook</a>
    {body}
  </main>
</body>
</html>
"""


def record_image(record, alt):
    return (
        '<figure class="source-page">'
        f'<img src="../{html.escape(record["image"])}" alt="{html.escape(alt)}">'
        f'<figcaption>Source scan page {record["seq"]}</figcaption>'
        "</figure>"
    )


def text_block(text):
    body = ['<section class="ocr-text" aria-label="OCR text">']
    for paragraph in clean_text(text).split("\n"):
        body.append(f"<p>{html.escape(paragraph)}</p>")
    body.append("</section>")
    return "".join(body)


def build_pages(records_by_section):
    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    section_entries = []

    for section_no in sorted(records_by_section):
        title = TOC[section_no]
        records = records_by_section[section_no]
        page_id = f"{HANDBOOK_ID}-section-{section_no:02d}-{slugify(title)}"
        parts = [
            f"<h1>{section_no}. {html.escape(title)}</h1>",
            '<p class="meta">Local 1 Handbook OCR &middot; source PDF scan</p>',
        ]
        for record in records:
            parts.append(record_image(record, f"{section_no}. {title}"))
            parts.append(text_block(record.get("text", "")))
        html_page = page_shell(f"{section_no}. {title}", "".join(parts))
        (PAGES_DIR / f"{page_id}.html").write_text(html_page, encoding="utf-8")
        section_entries.append(
            {
                "id": page_id,
                "title": f"Local 1 Handbook: {section_no}. {title}",
                "category": "Insulator Tools",
                "topics": ["insulator-tools", "standards-specs", "source-inventory"],
                "extension": "OCR",
                "relativePath": f"Insulator Tools/Local 1 Handbook.pdf#section-{section_no}",
                "sourcePath": str(SOURCE_PDF),
                "sizeBytes": SOURCE_PDF.stat().st_size if SOURCE_PDF.exists() else 0,
                "sizeMB": round((SOURCE_PDF.stat().st_size if SOURCE_PDF.exists() else 0) / (1024 * 1024), 2),
                "modified": datetime.fromtimestamp(SOURCE_PDF.stat().st_mtime, tz=timezone.utc).isoformat()
                if SOURCE_PDF.exists()
                else None,
                "summary": summary_for(records, title),
                "assetUrl": None,
                "assetStatus": "text-resource",
                "downloadAllowed": False,
                "resourceMode": "text-resource",
                "extraction": "local-ocr",
                "pages": len(records),
                "imageCount": len(records),
                "images": [record["image"] for record in records],
                "thumbnailUrl": records[0]["image"],
                "pdfPages": [],
                "paragraphs": [],
                "tables": [],
                "sheets": [],
                "searchText": clean_text(" ".join([title, *(record.get("text", "") for record in records)]))[:60000],
                "pageUrl": f"pages/{page_id}.html",
                "local1Handbook": True,
                "sectionNumber": section_no,
            }
        )

    return section_entries


def build_handbook_page(section_entries, cover_record, missing_sections):
    title = "Local 1 Handbook"
    links = []
    for entry in section_entries:
        section_no = entry["sectionNumber"]
        links.append(
            f'<li><a href="{html.escape(Path(entry["pageUrl"]).name)}">'
            f'{section_no}. {html.escape(TOC[section_no])}</a></li>'
        )
    missing = "".join(f"<li>{no}. {html.escape(TOC[no])}</li>" for no in missing_sections)
    missing_block = (
        f'<section class="notice"><p>These table-of-contents items did not have a standalone scanned page in this PDF extract.</p>'
        f"<ul>{missing}</ul></section>"
        if missing
        else ""
    )
    body = [
        "<h1>Local 1 Handbook</h1>",
        '<p class="meta">Heat &amp; Frost Insulators &amp; Asbestos Workers Information and Layout Handbook &middot; OCR section index</p>',
        record_image(cover_record, "Local 1 Handbook cover/title page"),
        text_block(cover_record.get("text", "")),
        "<h2>OCR Sections</h2>",
        f'<ol class="section-index">{"".join(links)}</ol>',
        missing_block,
    ]
    (PAGES_DIR / f"{HANDBOOK_ID}.html").write_text(page_shell(title, "".join(body)), encoding="utf-8")
    return {
        "id": HANDBOOK_ID,
        "title": "Local 1 Handbook",
        "category": "Insulator Tools",
        "topics": ["insulator-tools", "standards-specs", "source-inventory"],
        "extension": "OCR",
        "relativePath": "Insulator Tools/Local 1 Handbook.pdf",
        "sourcePath": str(SOURCE_PDF),
        "sizeBytes": SOURCE_PDF.stat().st_size if SOURCE_PDF.exists() else 0,
        "sizeMB": round((SOURCE_PDF.stat().st_size if SOURCE_PDF.exists() else 0) / (1024 * 1024), 2),
        "modified": datetime.fromtimestamp(SOURCE_PDF.stat().st_mtime, tz=timezone.utc).isoformat()
        if SOURCE_PDF.exists()
        else None,
        "summary": "OCR section index created from the scanned Local 1 Handbook PDF.",
        "assetUrl": None,
        "assetStatus": "text-resource",
        "downloadAllowed": False,
        "resourceMode": "text-resource",
        "extraction": "local-ocr",
        "pages": len(section_entries),
        "imageCount": 1,
        "images": [cover_record["image"]],
        "thumbnailUrl": cover_record["image"],
        "pdfPages": [],
        "paragraphs": [],
        "tables": [],
        "sheets": [],
        "searchText": clean_text(" ".join(["Local 1 Handbook", *TOC.values()])),
        "pageUrl": f"pages/{HANDBOOK_ID}.html",
        "local1Handbook": True,
    }


def main():
    records = json.loads(OCR_JSON.read_text(encoding="utf-8"))
    records_by_section = {}
    for record in records:
        section_no = SECTION_FOR_SEQ.get(record["seq"])
        if section_no:
            records_by_section.setdefault(section_no, []).append(record)

    section_entries = build_pages(records_by_section)
    missing_sections = [no for no in sorted(TOC) if no not in records_by_section]
    handbook_entry = build_handbook_page(section_entries, records[0], missing_sections)

    catalog = json.loads(CATALOG_JSON.read_text(encoding="utf-8"))
    catalog["entries"] = [entry for entry in catalog["entries"] if not entry.get("local1Handbook")]
    catalog["entries"].append(handbook_entry)
    catalog["entries"].extend(section_entries)
    catalog["categories"] = sorted({entry["category"] for entry in catalog["entries"]})
    catalog["generatedAt"] = datetime.now(timezone.utc).isoformat()
    CATALOG_JSON.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    print(f"Created {len(section_entries)} section pages and updated {CATALOG_JSON}")
    if missing_sections:
        print("Missing standalone scans:", ", ".join(str(no) for no in missing_sections))


if __name__ == "__main__":
    main()
