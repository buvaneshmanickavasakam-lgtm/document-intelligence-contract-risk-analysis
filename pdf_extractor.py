import sys
import os
import re
from pypdf import PdfReader

# ============================================================
# INPUT PDF
# ============================================================

if len(sys.argv) > 1:
    pdf_path = sys.argv[1]
else:
    pdf_path = "Service_agreement.pdf"

print("=" * 80)
print("              CONTRACT PDF VALIDATION")
print("=" * 80)

print(f"\nPDF: {pdf_path}")

# ============================================================
# 1. FILE EXISTENCE
# ============================================================

if not os.path.exists(pdf_path):
    print("\nERROR: PDF file not found.")
    print(f"File: {pdf_path}")
    sys.exit(1)

# ============================================================
# 2. FILE TYPE
# ============================================================

if not pdf_path.lower().endswith(".pdf"):
    print("\nERROR: Input file must be a PDF.")
    sys.exit(1)

# ============================================================
# 3. READ PDF
# ============================================================

try:
    reader = PdfReader(pdf_path)
except Exception as e:
    print("\nERROR: Unable to read PDF.")
    print(f"Details: {e}")
    sys.exit(1)

# ============================================================
# 4. PAGE CHECK
# ============================================================

page_count = len(reader.pages)

if page_count == 0:
    print("\nERROR: PDF contains no pages.")
    sys.exit(1)

print(f"Pages: {page_count}")

# ============================================================
# 5. TEXT EXTRACTION
# ============================================================

all_text = []

for page_number, page in enumerate(reader.pages, start=1):

    try:
        page_text = page.extract_text() or ""
    except Exception:
        page_text = ""

    all_text.append(page_text)

text = "\n".join(all_text)

character_count = len(text)

print(f"Extracted characters: {character_count:,}")

# ============================================================
# 6. MINIMUM TEXT CHECK
# ============================================================

MIN_TEXT_CHARACTERS = 1000

if character_count < MIN_TEXT_CHARACTERS:

    print("\n" + "=" * 80)
    print("              INSUFFICIENT TEXT")
    print("=" * 80)

    print(
        "\nThis PDF does not contain enough extractable text "
        "for the current analysis pipeline."
    )

    print(
        "\nPossible reason:"
    )

    print(
        "The PDF may be scanned/image-based or "
        "text extraction may have failed."
    )

    print(
        "\nOCR/LayoutLM processing will be required "
        "for this type of document."
    )

    sys.exit(1)

# ============================================================
# 7. TEXT QUALITY CHECK
# ============================================================

# Keep letters and numbers only for the quality calculation.
alphanumeric_text = re.sub(
    r"[^A-Za-z0-9]",
    "",
    text
)

if character_count > 0:
    text_quality_ratio = (
        len(alphanumeric_text) / character_count
    )
else:
    text_quality_ratio = 0

print(
    f"Text quality ratio: "
    f"{text_quality_ratio:.2%}"
)

# A normal contract should contain substantial
# alphanumeric/text content.

MIN_TEXT_QUALITY = 0.20

if text_quality_ratio < MIN_TEXT_QUALITY:

    print("\n" + "=" * 80)
    print("              LOW QUALITY TEXT EXTRACTION")
    print("=" * 80)

    print(
        "\nThe PDF contains text, but the extracted content "
        "does not appear suitable for contract analysis."
    )

    print(
        "\nPossible reason:"
    )

    print(
        "The PDF may be image-based, corrupted, "
        "or have an unusual text encoding."
    )

    print(
        "\nOCR/LayoutLM processing may be required."
    )

    sys.exit(1)

# ============================================================
# 8. SAVE EXTRACTED TEXT
# ============================================================

OUTPUT_FILE = "contract_text.txt"

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as f:

    f.write(text)

print(
    f"\nSaved extracted text: {OUTPUT_FILE}"
)

# ============================================================
# SUCCESS
# ============================================================

print("\n" + "=" * 80)
print("              PDF VALIDATION SUCCESSFUL")
print("=" * 80)

print(
    "\nThe PDF contains sufficient and usable "
    "extractable text for the next pipeline stage."
)

print("=" * 80)