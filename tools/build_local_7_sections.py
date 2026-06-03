import html
import re
import subprocess
from pathlib import Path

from pypdf import PdfReader


PDF_PATH = Path(r"F:\Insulator Book\Processed\Local 7 Book.pdf")
OUT_ROOT = Path(__file__).resolve().parents[1]
PAGE_DIR = OUT_ROOT / "pages" / "local-7-book"
IMAGE_DIR = OUT_ROOT / "assets" / "local-7-book"
OCR_DIR = OUT_ROOT / "data" / "local-7-book-ocr"
OCR_SCRIPT = OUT_ROOT / "tools" / "ocr_image.ps1"


SECTIONS = [
    (1, "Table of Contents 1 & 2", [2, 3]),
    (2, "Dedication", [4]),
    (3, "Introduction and Acknowledgement", [4]),
    (4, "Basic Tool List & Decimal Equivalent Chart", [5]),
    (5, "Refrigeration Fittings", [5]),
    (6, "Long Radius Rubber 90 Degree Elbow", [6]),
    (7, "Short Radius Rubber 90 Degree Elbow", [7]),
    (8, "Equal Reducing Rubber 90 Degree Elbow", [8]),
    (9, "Lag Chart and Dimensions for Beveled Block Lags", [9]),
    (10, "Parts of a Circle", [10]),
    (11, "Geometric Construction 1", [11]),
    (12, "Geometric Construction 2", [12]),
    (13, "Ellipse Construction", [13]),
    (14, "Dividing a Circle into a Selected Number of Parts", [14]),
    (15, "Jacketing Chart", [15]),
    (16, "Pipe Sizes and Basic Math Formulas", [16]),
    (17, "One and Two-piece End-caps", [17]),
    (18, "Formula for a 45 Degree Conical", [18]),
    (19, "Another Method for a 45 Degree Conical", [19]),
    (20, "Formula for an Equal Tee", [20]),
    (21, "Formula for an Unequal Tee", [21]),
    (22, "Layouts for Equal and Unequal Tees (Stem Portions Only)", [22]),
    (23, "Another Method for an Unequal Tee (Stem Portion)", [23]),
    (24, "Formula for a 45 Degree Equal Lateral", [24]),
    (25, "Another Method for a 45 Degree Equal Lateral", [25]),
    (26, "Formula for an Unequal 45 Degree Lateral", [26]),
    (27, "Diagram for an Unequal 45 Degree Lateral", [27]),
    (28, "Concentric Reducer (Equal Cone) Reducer", [28]),
    (29, "Layout for a Cone or Taper", [29]),
    (30, "Eccentric Reducer (Hog Nose)", [30]),
    (31, "Conic Reducing Tee at 90 Degrees", [31]),
    (32, "Diagram for a Conic Reducing Tee at 90 Degrees", [32]),
    (33, "Square to Round", [33]),
    (34, "Square to Round (Where Round is Larger)", [34]),
    (35, "Round to Square", [35]),
    (36, "Rectangular to Round", [36]),
    (37, "Square to Square Transition", [37]),
    (38, "Oval to Round", [38]),
    (39, "Square to Round (Single Offset)", [39]),
    (40, "Square to Round (Double Offset)", [40]),
    (41, "Square to Round (Double Offset) Round is Outside the Square", [41]),
    (42, "Enlarging or Reducing a Pattern", [41]),
    (43, "Long Radius Miter Chart", [42]),
    (44, "Short Radius Miter Chart", [43]),
    (45, "Gore Chart", [44]),
    (46, "Heel and Throat Using Machinists Figures", [45]),
    (47, "Heat Traced Piping & Sweeps & Field Bends", [46]),
    (48, "Formula for a Gore Pattern (Regular Method)", [47]),
    (49, "Short-cut Method for Gore Layouts", [48]),
    (50, "Short-cut Method for Metal Gores", [49]),
    (51, "Rise Method for a 90 Degree Elbow", [50]),
    (52, "Gores for Long Radius 90 Degree Elbow", [51]),
    (53, "Three-piece 90 Degree Short Radius Elbow", [52]),
    (54, "Two-piece 45 Degree Elbow by Rise", [53]),
    (55, "Negative Throat Elbows", [54]),
    (56, "Diagram for Negative Throat Elbows", [55]),
    (57, "Four-piece Short Radius 90 Degree Elbow w/Negative Throat", [56]),
    (58, "Five-piece Long Radius Duct 90 Degree Elbow", [57]),
    (59, "Four-piece Short Radius Duct 90 Degree Elbow", [58]),
    (60, "Negative Throat Plug 90 Degree Metal Layout", [59]),
    (61, "Four or Six-piece Flat-end Tank with a Rise", [60]),
    (62, "Snap-line Gores", [61]),
    (63, "Orange-peel Gores", [62]),
    (64, "Diameter Method for Orange-peel Gores", [63]),
    (65, "Six Division Method for Orange-peel Gores", [64]),
    (66, "Another Method for Gores to a Domed Head", [65]),
    (67, "Cone with a Slanted Top", [66]),
    (68, "Round Three-piece Offset", [67]),
    (69, "Off-center Taper", [68]),
    (70, "Diagram for Off-center Taper", [69]),
    (71, "Three-piece 90 Degree Elbow with a Round Branch", [70]),
    (72, "Cone with a 90 Degree Square Run-out and a 45 Degree Round Run-out", [71]),
    (73, "Diagram for Cone with a 90 Degree Square Run-out and a 45 Degree Round Run-out", [72]),
    (74, "Taper with a 90 Degree Round Run-out", [73]),
    (75, "Diagram for a Taper with a 90 Degree Round Run-out", [74]),
    (76, "Combination Layout Text 1", [75]),
    (77, "Combination Layout Text 2", [76]),
    (78, "Diagram 1 for a Combination Layout", [77]),
    (79, "Diagram 2 for a Combination Layout", [78]),
    (80, "Two-way Y Branch", [79]),
    (81, "Diagram for Two-way Branch", [80]),
    (82, "Finding Dimensions for Cones and Transitions", [81]),
    (83, "Determining the Radius of a Curve", [82]),
]


NON_INSTRUCTION_SECTIONS = {1, 2, 3, 4, 5}


def slugify(value):
    value = value.lower().replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "section"


def section_filename(number, title):
    return f"section-{number:02d}-{slugify(title)}.html"


def page_image_path(page_number):
    return IMAGE_DIR / f"local-7-book-p{page_number:03d}.jpg"


def normalize_text(value):
    replacements = {
        "\x00": "",
        "\uf0b7": "-",
        "\u2022": "-",
        "\u25a0": "",
        "\u00a0": " ",
        "\u00c2": "",
        "\u00b0": " degrees",
        "Ã¢â‚¬Â¢": "-",
        "â€¢": "-",
        "â– ": "",
        "â–": "",
        "Â«": "",
        "Ã‚Â°": " degrees",
        "Â°": " degrees",
        "Ã¢â‚¬â€œ": "-",
        "Ã¢â‚¬â€": "-",
        "â€“": "-",
        "â€”": "-",
        "Ã¢â‚¬â„¢": "'",
        "â€™": "'",
        "Ã¢â‚¬Å“": '"',
        "â€œ": '"',
        "â€\x9d": '"',
        "O.D.1": "O.D.I.",
        "0.D.1": "O.D.I.",
        "0.D.I": "O.D.I.",
        "Linel": "Line 1",
        "221/2": "22 1/2",
        "11/2": "1 1/2",
        "1 L.": "1 1/2.",
        "Add I\"": "Add 1\"",
        "rimp": "crimp",
        "-aPOINVOIP": "",
        "l/2": "1/2",
        " h.": " 1/2.",
    }
    for bad, good in replacements.items():
        value = value.replace(bad, good)
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"\b1\s+1/\s*(?:22|2)?(?=\s|$|\.)", "1 1/2", value)
    value = re.sub(r"\bb\s+the number\b", "by the number", value)
    value = re.sub(r"Example\s*:?\s*90\s+-:-\s+8\s+=\s+I\s+i", "Example: 90 / 8 = 11.25", value)
    value = re.sub(r"(?:-\s*){6,}", " ", value)
    value = re.sub(r"(?:â€¢\s*){3,}", " ", value)
    value = re.sub(r"\btep\b", "Step", value, flags=re.IGNORECASE)
    value = re.sub(r"\bstep\b", "Step", value)
    value = re.sub(r"\s+([,.;:])", r"\1", value)
    return value.strip()


def extract_page_images(reader):
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    for page_number, page in enumerate(reader.pages, start=1):
        out = page_image_path(page_number)
        if out.exists():
            continue
        images = list(getattr(page, "images", []))
        if images:
            out.write_bytes(images[0].data)


def ocr_page(page_number):
    OCR_DIR.mkdir(parents=True, exist_ok=True)
    cache = OCR_DIR / f"page-{page_number:03d}.txt"
    if cache.exists():
        return normalize_text(cache.read_text(encoding="utf-8"))
    image = page_image_path(page_number)
    if not image.exists():
        return ""
    result = subprocess.run(
        [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(OCR_SCRIPT),
            str(image),
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    text = normalize_text(result.stdout)
    cache.write_text(text, encoding="utf-8")
    return text


def remove_repeated_step_labels(text):
    matches = list(re.finditer(r"\bStep\s+\d+\.?", text))
    if len(matches) < 3:
        return text
    first_chunk = text[: matches[-1].end()]
    if len(first_chunk) <= 90:
        return text[matches[-1].end() :].strip()
    return text


def page_text(page_numbers):
    return normalize_text(" ".join(ocr_page(page_number) for page_number in page_numbers))


def pdf_page_text(reader, page_numbers):
    parts = []
    for page_number in page_numbers:
        if 1 <= page_number <= len(reader.pages):
            parts.append(reader.pages[page_number - 1].extract_text() or "")
    text = normalize_text(" ".join(parts))
    text = re.sub(r"(?:-\s*){8,}", " ", text)
    text = re.sub(r"(?:\.\s*){8,}", " ", text)
    return text


def strip_title(text, title):
    title_words = [re.escape(word) for word in re.findall(r"[A-Za-z0-9]+", title) if len(word) > 1]
    if not title_words:
        return text
    flexible = r"\s+".join(title_words[:8])
    return re.sub(rf"^{flexible}\b", "", text, flags=re.IGNORECASE).strip()


def split_sentences(text):
    pieces = re.split(r"(?<=[.!?])\s+(?=(?:[A-Z0-9]|\(|\"))", text)
    return [piece.strip(" -") for piece in pieces if piece.strip(" -")]


def parse_steps(text):
    matches = list(re.finditer(r"\bStep\s+(\d+)\.?", text))
    if not matches:
        return []
    first_step_one = next((idx for idx, match in enumerate(matches) if int(match.group(1)) == 1), 0)
    matches = matches[first_step_one:]
    steps = []
    last_number = 0
    for index, match in enumerate(matches):
        step_number = int(match.group(1))
        if step_number <= last_number:
            continue
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[start:end].strip(" .:-")
        body = remove_repeated_step_labels(body)
        if body:
            body = re.sub(r"\s+\d{1,3}\s*$", "", body).strip()
            steps.append((step_number, body))
            last_number = step_number
    return steps


def clean_step_bodies(steps, title):
    cleaned = []
    title_pattern = re.escape(title)
    for number, body in steps:
        body = normalize_text(body)
        repeat = re.search(title_pattern, body, flags=re.IGNORECASE)
        if repeat and repeat.start() > 30:
            body = body[: repeat.start()].strip(" .:-")
        body = re.sub(r"\s+(Point|Line|Figure)\s*$", "", body).strip()
        body = re.sub(r"(?:\s+-){4,}.*$", "", body).strip()
        cleaned.append((number, body))
    return [(number, body) for number, body in cleaned if body]


def usable_step_count(text):
    steps = parse_steps(text)
    return sum(1 for _, body in steps if len(body) > 25)


def parse_required(text):
    match = re.search(r"Information required:?", text, flags=re.IGNORECASE)
    if not match:
        return []
    next_step = re.search(r"\bStep\s+1\.?", text[match.end() :], flags=re.IGNORECASE)
    end = match.end() + next_step.start() if next_step else len(text)
    chunk = remove_repeated_step_labels(text[match.end() : end]).strip(" .:-")
    if not chunk:
        # Windows OCR often reads the step labels before the requirement list.
        first_step = re.search(r"\bStep\s+1\.?", text, flags=re.IGNORECASE)
        if first_step:
            chunk = text[match.end() : first_step.start()].strip(" .:-")
    if not chunk:
        return []
    known_markers = [
        "Pipe Call-out Size",
        "Thickness of Insulation",
        "Insulation thickness",
        "Pipe size",
        "O.D.I.",
        "Outside Diameter of Insulation",
        "Number of degrees",
        "Number of pieces",
        "Center Line Radius",
        "Total circumference",
        "Rise",
        "Radius",
        "Height",
        "Large diameter",
        "Small diameter",
        "True height",
        "Diameter of the tank",
        "Length of a gore",
    ]
    found = []
    for marker in known_markers:
        if re.search(re.escape(marker), chunk, flags=re.IGNORECASE):
            found.append(marker)
    if found:
        return list(dict.fromkeys(found))
    return split_sentences(chunk)[:8]


def parse_formulas(text):
    formulas = []
    for sentence in split_sentences(text):
        has_formula_word = any(word in sentence.lower() for word in ["formula", "multiply", "divide", "tangent", "square root", "times pi", "equals", " = "])
        if has_formula_word:
            formulas.append(sentence)
    return list(dict.fromkeys(formulas))[:10]


def parse_notes(text, steps, formulas):
    used = " ".join(body for _, body in steps) + " " + " ".join(formulas)
    notes = []
    for sentence in split_sentences(text):
        low = sentence.lower()
        if sentence in used:
            continue
        if low.startswith(("note:", "*note")) or "review:" in low or "be sure" in low or "when " in low:
            notes.append(sentence)
    return list(dict.fromkeys(notes))[:8]


def wiki_content(number, title, pdf_text, ocr_text):
    text = pdf_text
    if usable_step_count(ocr_text) > usable_step_count(pdf_text):
        text = ocr_text
    body = normalize_text(strip_title(text, title))
    required = parse_required(body)
    steps = clean_step_bodies(parse_steps(body), title)
    formula_source = " ".join(step_body for _, step_body in steps) if steps else body
    formulas = parse_formulas(formula_source)
    notes = parse_notes(body, steps, formulas)
    if number in NON_INSTRUCTION_SECTIONS:
        overview = split_sentences(body)[:12]
    else:
        overview = []
    return {
        "required": required,
        "steps": steps,
        "formulas": formulas,
        "notes": notes,
        "overview": overview,
        "raw": body,
    }


def render_list(title, items):
    if not items:
        return ""
    out = [f"<section class=\"wiki-block\"><h2>{html.escape(title)}</h2><ul>"]
    for item in items:
        out.append(f"<li>{html.escape(item)}</li>")
    out.append("</ul></section>")
    return "\n".join(out)


def render_steps(steps):
    if not steps:
        return ""
    out = ["<section class=\"wiki-block\"><h2>Procedure</h2><ol class=\"procedure-list\">"]
    for number, body in steps:
        out.append(f"<li><span>Step {number}</span><p>{html.escape(body)}</p></li>")
    out.append("</ol></section>")
    return "\n".join(out)


def render_overview(items):
    if not items:
        return ""
    out = ["<section class=\"wiki-block\"><h2>Extracted Text</h2>"]
    for item in items:
        out.append(f"<p>{html.escape(item)}</p>")
    out.append("</section>")
    return "\n".join(out)


def render_raw(content):
    if content["steps"] or content["overview"]:
        return ""
    sentences = split_sentences(content["raw"])[:20]
    return render_overview(sentences)


def render_source_drawings(number, title, pages):
    figures = []
    for page_number in pages:
        image = page_image_path(page_number)
        if image.exists():
            figures.append(
                f'''<figure class="pdf-page-image">
  <a href="../../assets/local-7-book/{image.name}"><img src="../../assets/local-7-book/{image.name}" alt="Section {number} source drawing page {page_number}"></a>
  <figcaption>Source drawing page {page_number}</figcaption>
</figure>'''
            )
    if not figures:
        return ""
    return f'''<aside class="local-7-images">
  <h2>Source Drawing</h2>
  <p class="meta">Use the scan to verify layout geometry and figure references.</p>
  {''.join(figures)}
</aside>'''


def build_section_page(index, section, content):
    number, title, pages = section
    prev_link = ""
    next_link = ""
    if index > 0:
        prev_number, prev_title, _ = SECTIONS[index - 1]
        prev_link = f'<a class="button ghost" href="{section_filename(prev_number, prev_title)}">Previous</a>'
    if index < len(SECTIONS) - 1:
        next_number, next_title, _ = SECTIONS[index + 1]
        next_link = f'<a class="button" href="{section_filename(next_number, next_title)}">Next</a>'

    article = "\n".join(
        part
        for part in [
            render_overview(content["overview"]),
            render_list("Required Information", content["required"]),
            render_list("Formulas and Measurements", content["formulas"]),
            render_steps(content["steps"]),
            render_list("Notes", content["notes"]),
            render_raw(content),
        ]
        if part
    )
    if not article:
        article = '<section class="wiki-block"><h2>Extracted Text</h2><p>No usable text was extracted for this section.</p></section>'

    drawings = render_source_drawings(number, title, pages)
    lesson_class = "wiki-article local-7-split" if drawings else "wiki-article"

    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Section {number}: {html.escape(title)}</title>
  <link rel="stylesheet" href="../../styles.css">
</head>
<body class="detail-page local-7-page">
  <main class="local-7-detail wiki-detail">
    <nav class="section-nav top">
      <a href="../../index.html" class="back-link">Back to field notebook</a>
      <a href="index.html" class="back-link">Local 7 wiki index</a>
    </nav>
    <header class="sheet local-7-section-hero">
      <p class="eyebrow">Local 7 Wiki</p>
      <h1>Section {number}: {html.escape(title)}</h1>
      <div class="card-actions section-pager">{prev_link}{next_link}</div>
    </header>
    <article class="{lesson_class}">
      <div class="wiki-main">
        {article}
      </div>
      {drawings}
    </article>
  </main>
</body>
</html>
"""
    (PAGE_DIR / section_filename(number, title)).write_text(page, encoding="utf-8")


def build_index(contents):
    cards = []
    for number, title, _ in SECTIONS:
        content = contents[number]
        bits = []
        if content["required"]:
            bits.append(f"{len(content['required'])} inputs")
        if content["steps"]:
            bits.append(f"{len(content['steps'])} steps")
        if content["formulas"]:
            bits.append(f"{len(content['formulas'])} formulas")
        meta = " - ".join(bits) or "text entry"
        cards.append(
            f'''<a class="local-7-section-card" href="{section_filename(number, title)}">
  <span>Section {number}</span>
  <strong>{html.escape(title)}</strong>
  <small>{html.escape(meta)}</small>
</a>'''
        )

    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Local 7 Wiki</title>
  <link rel="stylesheet" href="../../styles.css">
</head>
<body class="detail-page local-7-page">
  <main class="local-7-detail">
    <section class="sheet local-7-section-hero">
      <a href="../../index.html" class="back-link">Back to field notebook</a>
      <p class="eyebrow">Searchable Instruction Set</p>
      <h1>Local 7 Wiki</h1>
      <p class="meta">Instruction pages generated from the provided Local 7 Book text only.</p>
      <label class="wiki-search">
        <span>Search sections</span>
        <input id="local7Search" type="search" placeholder="Search tee, gore, elbow, cone, square to round...">
      </label>
    </section>
    <section class="local-7-section-grid" id="local7Sections">
      {''.join(cards)}
    </section>
  </main>
  <script>
    const search = document.querySelector("#local7Search");
    const cards = Array.from(document.querySelectorAll(".local-7-section-card"));
    search.addEventListener("input", () => {{
      const query = search.value.trim().toLowerCase();
      for (const card of cards) {{
        card.hidden = query && !card.textContent.toLowerCase().includes(query);
      }}
    }});
  </script>
</body>
</html>
"""
    (PAGE_DIR / "index.html").write_text(page, encoding="utf-8")


def main():
    if not PDF_PATH.exists():
        raise FileNotFoundError(PDF_PATH)
    PAGE_DIR.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(str(PDF_PATH))
    extract_page_images(reader)
    contents = {}
    for index, section in enumerate(SECTIONS):
        number, title, pages = section
        ocr_text = page_text(pages)
        content = wiki_content(number, title, pdf_page_text(reader, pages), ocr_text)
        contents[number] = content
        build_section_page(index, section, content)
    build_index(contents)
    print(f"Built {len(SECTIONS)} Local 7 wiki pages in {PAGE_DIR}")


if __name__ == "__main__":
    main()
