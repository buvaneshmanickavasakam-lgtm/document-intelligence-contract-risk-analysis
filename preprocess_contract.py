import re
import sys
from pypdf import PdfReader
from transformers import AutoTokenizer

if len(sys.argv) > 1:
    PDF_PATH = sys.argv[1]
else:
    PDF_PATH = "Service_agreement.pdf"

MODEL_PATH = "./contract_roberta_model"

# ========================================
# 1. LOAD PDF
# ========================================

reader = PdfReader(PDF_PATH)

print("\n========================================")
print("      CONTRACT PDF PREPROCESSING")
print("========================================")

print(f"\nPDF file: {PDF_PATH}")
print(f"Total pages: {len(reader.pages)}")

pages = []

for page_number, page in enumerate(reader.pages, start=1):
    text = page.extract_text() or ""

    pages.append({
        "page": page_number,
        "text": text
    })

print("PDF text extraction completed.")


# ========================================
# 2. CLEAN PDF ARTIFACTS
# ========================================

clean_pages = []

for item in pages:

    page_number = item["page"]
    text = item["text"]

    # Remove URLs
    text = re.sub(r"https?://\S+", "", text)

    # Remove timestamp artifacts
    text = re.sub(
        r"\d{1,2}/\d{1,2}/\d{2,4},\s*\d{1,2}:\d{2}\s*[AP]M",
        "",
        text,
        flags=re.IGNORECASE
    )

    # Remove common SEC/PDF exhibit artifacts
    text = re.sub(r"\bEX-\d+(?:\.\d+)?\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bEX\s+\d+(?:\.\d+)?\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bExhibit\s+\d+(?:\.\d+)?\b", "", text, flags=re.IGNORECASE)

    # Remove standalone page numbering such as:
    # Page i
    # Page ii
    # Page 12
    text = re.sub(
        r"\bPage\s+(?:[ivxlcdm]+|\d+)\b",
        "",
        text,
        flags=re.IGNORECASE
    )

    # Remove PDF page-counter artifacts such as "/125"
    text = re.sub(r"/\s*\d+\b", "", text)

    # Remove excessive spaces
    text = re.sub(r"[ \t]+", " ", text)

    # Clean excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    text = text.strip()

    if text:
        clean_pages.append({
            "page": page_number,
            "text": text
        })


# ========================================
# 3. COMBINE CONTRACT TEXT
# ========================================

full_text = "\n\n".join(
    item["text"] for item in clean_pages
)

print(f"\nCleaned characters: {len(full_text):,}")


# ========================================
# 4. LOAD ROBERTA TOKENIZER
# ========================================

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)

# IMPORTANT:
# Do not use tokenizer.encode() on the entire document.
# tokenize() avoids the unnecessary 512-token warning.

tokens = tokenizer.tokenize(full_text)

print(f"Total tokens: {len(tokens):,}")


# ========================================
# 5. CREATE SLIDING-WINDOW CHUNKS
# ========================================

CHUNK_SIZE = 400
OVERLAP = 50
STEP = CHUNK_SIZE - OVERLAP

chunks = []

for start in range(0, len(tokens), STEP):

    chunk_tokens = tokens[start:start + CHUNK_SIZE]

    if not chunk_tokens:
        break

    chunk_text = tokenizer.convert_tokens_to_string(chunk_tokens)

    chunks.append({
        "chunk_id": len(chunks),
        "text": chunk_text
    })

    if start + CHUNK_SIZE >= len(tokens):
        break


# ========================================
# 6. DISPLAY RESULTS
# ========================================

print(f"Total chunks: {len(chunks)}")

print("\n========== FIRST 3 CHUNKS ==========\n")

for chunk in chunks[:3]:

    print(f"--- Chunk {chunk['chunk_id']} ---")
    print(chunk["text"][:1000])
    print("\n")


print("========================================")
print("   PREPROCESSING COMPLETED")
print("========================================")