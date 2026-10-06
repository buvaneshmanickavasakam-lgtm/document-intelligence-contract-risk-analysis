import pandas as pd
from sentence_transformers import SentenceTransformer, util

# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = "classified_contract_sections.csv"
OUTPUT_FILE = "validated_contract_sections.csv"

# Minimum semantic similarity
SIMILARITY_THRESHOLD = 0.40

# ============================================================
# LOAD DATA
# ============================================================

print("=" * 80)
print("          SEMANTIC VALIDATION OF CONTRACT SECTIONS")
print("=" * 80)

df = pd.read_csv(INPUT_FILE)

print(f"\nInput sections : {len(df)}")

# ============================================================
# CLAUSE DESCRIPTIONS
# ============================================================

clause_descriptions = {

    "Affiliate License-Licensee":
        "A license granted to an affiliate of the licensee.",

    "Affiliate License-Licensor":
        "A license granted to an affiliate of the licensor.",

    "Anti-Assignment":
        "Restrictions preventing a party from assigning, transferring, or delegating the agreement without consent.",

    "Audit Rights":
        "A contractual right allowing a party to inspect, audit, examine, or review another party's books, records, accounts, or compliance.",

    "Cap On Liability":
        "A contractual limitation that places a maximum monetary amount on liability or damages.",

    "Change Of Control":
        "A provision addressing what happens when ownership or control of a company changes.",

    "Competitive Restriction Exception":
        "An exception to a restriction on competitive activities.",

    "Covenant Not To Sue":
        "A contractual promise not to sue or bring certain legal claims.",

    "Exclusivity":
        "A provision requiring exclusive dealing or preventing a party from working with competitors or other parties.",

    "Insurance":
        "Requirements for maintaining insurance coverage, policies, limits, certificates, or proof of insurance.",

    "Ip Ownership Assignment":
        "A provision assigning ownership of intellectual property from one party to another.",

    "Irrevocable Or Perpetual License":
        "A license that is irrevocable, perpetual, or continues indefinitely.",

    "Joint Ip Ownership":
        "A provision establishing joint or shared ownership of intellectual property.",

    "License Grant":
        "A provision granting one party rights or permission to use intellectual property, software, technology, or other licensed materials.",

    "Liquidated Damages":
        "A predetermined amount of money payable as damages if a specified breach or event occurs.",

    "Minimum Commitment":
        "A requirement to purchase, spend, use, or commit to a minimum amount or volume.",

    "Most Favored Nation":
        "A provision requiring a party to receive terms or pricing no less favorable than those offered to other customers or parties.",

    "No-Solicit Of Customers":
        "A restriction preventing solicitation of the other party's customers.",

    "No-Solicit Of Employees":
        "A restriction preventing solicitation, hiring, or recruitment of the other party's employees.",

    "Non-Compete":
        "A restriction preventing a party from competing with another party or engaging in specified competing activities.",

    "Non-Disparagement":
        "A restriction preventing negative, disparaging, or damaging statements about a party.",

    "Non-Transferable License":
        "A license that cannot be transferred, assigned, or sublicensed.",

    "Post-Termination Services":
        "Obligations to continue providing services, assistance, transition support, data, or other services after termination or expiration.",

    "Price Restrictions":
        "Restrictions governing prices, pricing, resale prices, or changes to prices.",

    "Revenue/Profit Sharing":
        "A provision requiring revenue, profits, fees, or financial amounts to be shared between parties.",

    "Rofr/Rofo/Rofn":
        "A right of first refusal, right of first offer, or right of first negotiation.",

    "Source Code Escrow":
        "A requirement to place source code in escrow for release to another party under specified conditions.",

    "Termination For Convenience":
        "A right allowing a party to terminate the agreement without needing to prove a breach or other specified cause.",

    "Third Party Beneficiary":
        "A provision granting contractual rights or benefits to a third party that is not a contracting party.",

    "Uncapped Liability":
        "A provision stating that certain liabilities or damages are not subject to the contractual liability cap.",

    "Unlimited/All-You-Can-Eat-License":
        "A license allowing unlimited use, users, transactions, or access without a specified usage limitation.",

    "Volume Restriction":
        "A restriction limiting the volume, quantity, number of users, transactions, or usage.",

    "Warranty Duration":
        "A provision specifying how long a warranty remains valid or the duration of warranty coverage."
}

# ============================================================
# LOAD EMBEDDING MODEL
# ============================================================

print("\nLoading MiniLM...")

model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

# Create embeddings for all clause descriptions
clause_names = list(clause_descriptions.keys())

description_embeddings = model.encode(
    list(clause_descriptions.values()),
    convert_to_tensor=True
)

# ============================================================
# VALIDATE EACH SECTION
# ============================================================

validated_rows = []

print("\nValidating sections...\n")

for _, row in df.iterrows():

    predicted_clause = row["predicted_clause"]

    section_title = str(row["section_title"])
    section_text = str(row["text"])

    # --------------------------------------------------------
    # Combine section heading + text
    # --------------------------------------------------------

    section_content = (
        section_title + ". " + section_text
    )

    # --------------------------------------------------------
    # Create embedding
    # --------------------------------------------------------

    section_embedding = model.encode(
        section_content,
        convert_to_tensor=True
    )

    # --------------------------------------------------------
    # Compare with ALL 33 clause descriptions
    # --------------------------------------------------------

    similarities = util.cos_sim(
        section_embedding,
        description_embeddings
    )[0]

    best_index = int(similarities.argmax())

    best_clause = clause_names[best_index]

    best_similarity = float(
        similarities[best_index]
    )

    # Similarity of RoBERTa's predicted class
    predicted_index = clause_names.index(
        predicted_clause
    )

    predicted_similarity = float(
        similarities[predicted_index]
    )

    # --------------------------------------------------------
    # Validation decision
    # --------------------------------------------------------

    if (
        predicted_similarity >= SIMILARITY_THRESHOLD
        and predicted_similarity >= best_similarity - 0.05
    ):
        validation = "SUPPORTED"
    else:
        validation = "REVIEW"

    validated_rows.append({

        "section_number":
            row["section_number"],

        "section_title":
            section_title,

        "roberta_clause":
            predicted_clause,

        "roberta_confidence":
            row["confidence"],

        "semantic_similarity":
            predicted_similarity,

        "best_semantic_clause":
            best_clause,

        "best_semantic_similarity":
            best_similarity,

        "validation":
            validation,

        "text":
            section_text
    })

# ============================================================
# SAVE RESULTS
# ============================================================

result = pd.DataFrame(validated_rows)

result.to_csv(
    OUTPUT_FILE,
    index=False
)

# ============================================================
# SUMMARY
# ============================================================

print("=" * 80)
print("          VALIDATION COMPLETED")
print("=" * 80)

print(f"\nTotal sections : {len(result)}")

print(
    f"Supported      : "
    f"{(result['validation'] == 'SUPPORTED').sum()}"
)

print(
    f"Needs review   : "
    f"{(result['validation'] == 'REVIEW').sum()}"
)

# ============================================================
# SUPPORTED CLAUSES
# ============================================================

supported = result[
    result["validation"] == "SUPPORTED"
].sort_values(
    "roberta_confidence",
    ascending=False
)

print("\n" + "-" * 80)
print("SUPPORTED CLAUSE CANDIDATES")
print("-" * 80)

for _, row in supported.iterrows():

    print(
        f"\nSection {row['section_number']} - "
        f"{row['section_title']}"
    )

    print(
        f"RoBERTa       : "
        f"{row['roberta_clause']} "
        f"({row['roberta_confidence']:.2%})"
    )

    print(
        f"Semantic      : "
        f"{row['semantic_similarity']:.2%}"
    )

    print(
        f"Best semantic : "
        f"{row['best_semantic_clause']} "
        f"({row['best_semantic_similarity']:.2%})"
    )

# ============================================================
# SAVE
# ============================================================

print("\n" + "=" * 80)
print(f"Saved: {OUTPUT_FILE}")
print("=" * 80)