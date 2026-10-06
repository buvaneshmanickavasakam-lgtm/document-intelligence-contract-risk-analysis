import re
import sys
import pandas as pd
from pypdf import PdfReader

# ============================================================
# INPUT PDF
# ============================================================

if len(sys.argv) > 1:
    PDF_PATH = sys.argv[1]
else:
    PDF_PATH = "Service_agreement.pdf"

OUTPUT_FILE = "contract_sections.csv"

# ============================================================
# EXTRACT PDF TEXT
# ============================================================

print("=" * 80)
print("              CONTRACT SECTION EXTRACTION")
print("=" * 80)

print(f"\nPDF: {PDF_PATH}")

reader = PdfReader(PDF_PATH)

pages = []

for page in reader.pages:
    page_text = page.extract_text() or ""
    pages.append(page_text)

raw_text = "\n".join(pages)

print(f"Pages: {len(reader.pages)}")
print(f"Raw text: {len(raw_text):,} characters")

# ============================================================
# BASIC CLEANING
# ============================================================

text = raw_text

# Normalize line endings
text = text.replace("\r\n", "\n").replace("\r", "\n")

# Remove common SEC webpage artifacts
text = re.sub(
    r"https?://www\.sec\.gov/[^\n]*",
    "",
    text,
    flags=re.IGNORECASE
)

# Remove common page markers
text = re.sub(
    r"\bPage\s+\d+\s+of\s+\d+\b",
    "",
    text,
    flags=re.IGNORECASE
)

# Remove repeated blank lines
text = re.sub(r"\n\s*\n+", "\n\n", text)

text = text.strip()

print(f"Cleaned text: {len(text):,} characters")

# ============================================================
# SECTION HEADER PATTERN
# ============================================================
#
# Supports:
#
# 1. GENERAL
# 2. DEFINITIONS
# 13. INSURANCE
# 1.1 Background and Purpose
# 2.9 Audits
# 17.10 Third Party Beneficiaries
#
# ============================================================

section_pattern = re.compile(
    r"(?m)^[ \t]*"
    r"(\d+(?:\.\d+)*)"
    r"\.?"
    r"[ \t]+"
    r"([A-Z][^\n]{2,150}?)"
    r"[ \t]*$"
)

matches = list(section_pattern.finditer(text))

print(f"\nRaw section detections: {len(matches)}")

# ============================================================
# CLEAN SECTION HEADINGS
# ============================================================

sections = []

for match in matches:

    section_number = match.group(1).strip()
    section_title = match.group(2).strip()

    # Remove headings ending with page numbers
    if re.search(r"\s+\d{1,4}$", section_title):
        continue

    # Ignore very short headings
    if len(section_title) < 3:
        continue

    # Ignore obvious non-section headings
    ignored_titles = {
        "TABLE OF CONTENTS",
        "CONTENTS",
        "EXHIBITS",
        "SCHEDULES"
    }

    if section_title.upper().strip() in ignored_titles:
        continue

    sections.append({
        "section_number": section_number,
        "section_title": section_title,
        "start": match.start(),
        "end": match.end()
    })

# ============================================================
# REMOVE DUPLICATES
# ============================================================

unique_sections = []
seen = set()

for section in sections:

    key = (
        section["section_number"],
        section["section_title"].upper()
    )

    if key in seen:
        continue

    seen.add(key)
    unique_sections.append(section)

sections = unique_sections

print(f"Clean section detections: {len(sections)}")

# ============================================================
# EXTRACT SECTION TEXT
# ============================================================

records = []

for i, section in enumerate(sections):

    start = section["end"]

    if i + 1 < len(sections):
        end = sections[i + 1]["start"]
    else:
        end = len(text)

    section_text = text[start:end].strip()

    if len(section_text) < 50:
        continue

    records.append({
        "section_number": section["section_number"],
        "section_title": section["section_title"],
        "text": section_text
    })

# ============================================================
# SAVE
# ============================================================

df = pd.DataFrame(records)

df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8"
)

# ============================================================
# DISPLAY
# ============================================================

print("\n" + "=" * 80)
print("              EXTRACTED CONTRACT SECTIONS")
print("=" * 80)

print(f"\nFinal sections: {len(df)}")

print("\nFirst 30 sections:\n")

for _, row in df.head(30).iterrows():
    print(
        f"{row['section_number']} - "
        f"{row['section_title']}"
    )

# ============================================================
# TOP-LEVEL SECTION CHECK
# ============================================================

print("\n" + "=" * 80)
print("              TOP-LEVEL SECTION CHECK")
print("=" * 80)

top_level = df[
    df["section_number"].astype(str).str.match(r"^\d+$")
]

print(
    f"\nTop-level sections detected: "
    f"{len(top_level)}"
)

for _, row in top_level.iterrows():
    print(
        f"{row['section_number']} - "
        f"{row['section_title']}"
    )

# ============================================================
# SPECIFIC INSURANCE CHECK
# ============================================================

insurance = df[
    df["section_title"]
    .astype(str)
    .str.contains("INSURANCE", case=False, na=False)
]

print("\n" + "=" * 80)
print("              INSURANCE SECTION CHECK")
print("=" * 80)

if len(insurance) > 0:

    for _, row in insurance.iterrows():

        print(
            f"\nFOUND: {row['section_number']} - "
            f"{row['section_title']}"
        )

else:

    print("\nWARNING: INSURANCE section was not detected.")

print("\n" + "=" * 80)
print(f"Saved: {OUTPUT_FILE}")
print("=" * 80)