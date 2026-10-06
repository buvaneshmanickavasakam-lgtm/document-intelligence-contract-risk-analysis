import pandas as pd
import os

INPUT_FILE = "final_clause_candidates.csv"
OUTPUT_FILE = "final_verified_evidence.csv"

print("=" * 80)
print("          PREPARING FINAL VERIFIED CONTRACT EVIDENCE")
print("=" * 80)

# ============================================================
# REQUIRED OUTPUT COLUMNS
# ============================================================

required_columns = [
    "section_number",
    "section_title",
    "clause",
    "roberta_confidence",
    "semantic_similarity",
    "evidence_matches",
    "text"
]

# ============================================================
# CHECK INPUT FILE
# ============================================================

if not os.path.exists(INPUT_FILE):
    raise FileNotFoundError(
        f"Input file not found: {INPUT_FILE}"
    )

# ============================================================
# READ INPUT SAFELY
# ============================================================

try:
    df = pd.read_csv(INPUT_FILE)

except pd.errors.EmptyDataError:

    print("\nStrict candidates : 0")
    print("\nNo clauses passed strict validation.")

    pd.DataFrame(
        columns=required_columns
    ).to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8"
    )

    print("\nFinal verified clauses : 0")
    print("\nNo supported contract-risk clauses were verified.")
    print(f"Saved: {OUTPUT_FILE}")

    print("\n" + "=" * 80)

    raise SystemExit


print(f"\nStrict candidates : {len(df)}")

# ============================================================
# HANDLE EMPTY DATAFRAME
# ============================================================

if len(df) == 0:

    print("\nNo clauses passed strict validation.")

    pd.DataFrame(
        columns=required_columns
    ).to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8"
    )

    print("\nFinal verified clauses : 0")
    print(f"Saved: {OUTPUT_FILE}")

    print("\n" + "=" * 80)

    raise SystemExit


# ============================================================
# REMOVE KNOWN FALSE-POSITIVE TYPES
# ============================================================

df = df[
    df["clause"].astype(str).str.strip() != "Change Of Control"
].copy()

print(
    f"After false-positive filtering : {len(df)}"
)

# ============================================================
# HANDLE EMPTY DATA AFTER FILTERING
# ============================================================

if len(df) == 0:

    print("\nNo clauses remained after strict filtering.")

    pd.DataFrame(
        columns=required_columns
    ).to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8"
    )

    print("\nFinal verified clauses : 0")
    print(f"Saved: {OUTPUT_FILE}")

    print("\n" + "=" * 80)

    raise SystemExit


# ============================================================
# SELECT STRONGEST EVIDENCE FOR EACH CLAUSE
# ============================================================

final_rows = []

for clause, group in df.groupby("clause"):

    group = group.copy()

    # --------------------------------------------------------
    # Post-Termination Services
    # --------------------------------------------------------

    if clause == "Post-Termination Services":

        title_text = (
            group["section_title"]
            .astype(str)
            .str.lower()
        )

        preferred = group[
            title_text.str.contains(
                "disengagement|termination assistance",
                regex=True,
                na=False
            )
        ]

        if len(preferred) > 0:
            group = preferred

    # --------------------------------------------------------
    # Choose strongest evidence
    # --------------------------------------------------------

    group = group.sort_values(
        by=[
            "semantic_similarity",
            "roberta_confidence",
            "evidence_matches"
        ],
        ascending=False
    )

    final_rows.append(
        group.iloc[0]
    )


# ============================================================
# CREATE FINAL DATAFRAME
# ============================================================

final_df = pd.DataFrame(final_rows)

missing = [
    col
    for col in required_columns
    if col not in final_df.columns
]

if missing:
    raise ValueError(
        f"Missing required columns: {missing}"
    )

final_df = final_df[required_columns]


# ============================================================
# SAVE
# ============================================================

final_df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8"
)


# ============================================================
# DISPLAY
# ============================================================

print("\n" + "=" * 80)
print("          FINAL VERIFIED CLAUSES")
print("=" * 80)

print(
    f"\nFinal verified clauses : "
    f"{len(final_df)}"
)

for _, row in final_df.iterrows():

    print(
        f"\nClause  : {row['clause']}"
    )

    print(
        f"Section : "
        f"{row['section_number']} - "
        f"{row['section_title']}"
    )

    print(
        f"RoBERTa : "
        f"{float(row['roberta_confidence']):.2%}"
    )

    print(
        f"Semantic: "
        f"{float(row['semantic_similarity']):.2%}"
    )

    print(
        f"Evidence: "
        f"{row['evidence_matches']} match(es)"
    )

print("\n" + "=" * 80)
print(f"Saved: {OUTPUT_FILE}")
print("=" * 80)