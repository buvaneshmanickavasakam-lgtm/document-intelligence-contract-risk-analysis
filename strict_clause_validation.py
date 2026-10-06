import pandas as pd
import re

INPUT_FILE = "evidence_validated_sections.csv"
OUTPUT_FILE = "final_clause_candidates.csv"

df = pd.read_csv(INPUT_FILE)

print("=" * 80)
print("          STRICT CONTRACT CLAUSE VALIDATION")
print("=" * 80)

print(f"\nInput sections : {len(df)}")

# ============================================================
# STRICT EVIDENCE PATTERNS
# ============================================================

patterns = {

    "Cap On Liability": [
        r"aggregate liability",
        r"total liability",
        r"liability.*limited",
        r"limited.*liability",
        r"\$[\d,]+",
        r"million dollars"
    ],

    "Insurance": [
        r"maintain.*insurance",
        r"insurance.*coverage",
        r"commercial general liability",
        r"cyber.?liability insurance",
        r"fidelity insurance"
    ],

    "No-Solicit Of Employees": [
        r"solicit.*employment",
        r"solicit.*employee",
        r"employ.*employee",
        r"without.*written approval",
        r"months.*thereafter"
    ],

    "Post-Termination Services": [
        r"continue to provide.*services",
        r"following termination",
        r"following.*expiration",
        r"after.*termination",
        r"wind.?down",
        r"disengagement assistance"
    ],

    "Change Of Control": [
        r"change of control",
        r"change in control"
    ]
}

# ============================================================
# HELPER
# ============================================================

def count_matches(text, patterns_list):

    text = str(text).lower()

    matches = 0

    for pattern in patterns_list:

        if re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        ):
            matches += 1

    return matches


# ============================================================
# VALIDATE
# ============================================================

verified_rows = []

for _, row in df.iterrows():

    clause = str(row["clause"]).strip()
    text = str(row["text"])

    if clause not in patterns:
        continue

    matches = count_matches(
        text,
        patterns[clause]
    )

    # ========================================================
    # CHANGE OF CONTROL — EXTRA STRICT VALIDATION
    # ========================================================
    #
    # A mere reference such as:
    #
    # "If Customer undergoes a Change in Control..."
    #
    # is not enough.
    #
    # Require a contractual consequence/condition involving
    # assignment, termination, consent, rights, obligations,
    # or continuation of the agreement.
    # ========================================================

    if clause == "Change Of Control":

        change_control_context = re.search(
            r"(change\s+of\s+control|change\s+in\s+control)"
            r".{0,500}"
            r"(assignment|assign|terminate|termination|consent|"
            r"right|obligation|agreement|shall|may|continue)",
            text,
            flags=re.IGNORECASE | re.DOTALL
        )

        reverse_context = re.search(
            r"(assignment|assign|terminate|termination|consent|"
            r"right|obligation|agreement|shall|may|continue)"
            r".{0,500}"
            r"(change\s+of\s+control|change\s+in\s+control)",
            text,
            flags=re.IGNORECASE | re.DOTALL
        )

        if (
            change_control_context is None
            and reverse_context is None
        ):
            continue

        # Require at least two supporting signals.
        if matches < 2:
            continue

    # ========================================================
    # GENERAL STRICT REQUIREMENT
    # ========================================================

    if matches < 1:
        continue

    verified_rows.append({
        "section_number": row["section_number"],
        "section_title": row["section_title"],
        "clause": clause,
        "roberta_confidence": row["roberta_confidence"],
        "semantic_similarity": row["semantic_similarity"],
        "evidence_matches": matches,
        "status": "VERIFIED",
        "text": text
    })

# ============================================================
# REMOVE DUPLICATES
# ============================================================

result = pd.DataFrame(verified_rows)

if len(result) > 0:

    result = result.sort_values(
        by=[
            "clause",
            "semantic_similarity",
            "roberta_confidence",
            "evidence_matches"
        ],
        ascending=[
            True,
            False,
            False,
            False
        ]
    )

    result = result.drop_duplicates(
        subset=["clause"],
        keep="first"
    )

# ============================================================
# SAVE
# ============================================================

result.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8"
)

# ============================================================
# DISPLAY
# ============================================================

print("\n" + "=" * 80)
print("          VERIFIED CONTRACT CLAUSES")
print("=" * 80)

print(
    f"\nVerified unique clauses : "
    f"{len(result)}"
)

for _, row in result.iterrows():

    print(
        f"\n{row['clause']}"
    )

    print(
        f"Section      : "
        f"{row['section_number']} - "
        f"{row['section_title']}"
    )

    print(
        f"RoBERTa      : "
        f"{float(row['roberta_confidence']):.2%}"
    )

    print(
        f"Semantic     : "
        f"{float(row['semantic_similarity']):.2%}"
    )

    print(
        f"Evidence     : "
        f"{row['evidence_matches']} match(es)"
    )

print("\n" + "=" * 80)
print(f"Saved: {OUTPUT_FILE}")
print("=" * 80)