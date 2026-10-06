import pandas as pd
import re

INPUT_FILE = "validated_contract_sections.csv"
OUTPUT_FILE = "evidence_validated_sections.csv"

df = pd.read_csv(INPUT_FILE)

print("=" * 80)
print("          CLAUSE EVIDENCE VALIDATION")
print("=" * 80)

print(f"\nInput sections : {len(df)}")


# ============================================================
# EVIDENCE PATTERNS
# ============================================================

patterns = {

    "Audit Rights": [
        r"\baudit\b",
        r"\baudits\b",
        r"\bauditor\b",
        r"\binspect\b.*\bbooks\b",
        r"\binspect\b.*\brecords\b",
        r"\bbooks and records\b",
        r"\bright to audit\b",
        r"\bright.*inspect\b"
    ],

    "Insurance": [
        r"\binsurance\b",
        r"\binsured\b",
        r"\bpolicy\b.*\binsurance\b",
        r"\bcoverage\b",
        r"\bliability insurance\b",
        r"\bcertificate of insurance\b",
        r"\bcommercial general liability\b"
    ],

    "Cap On Liability": [
        r"\blimitation of liability\b",
        r"\blimit.*liability\b",
        r"\baggregate liability\b",
        r"\bmaximum liability\b",
        r"\bliability.*shall not exceed\b",
        r"\bdamages.*shall not exceed\b",
        r"\bcap\b.*\bliability\b",
        r"\bexceed.*\$[\d,]+"
    ],

    "Uncapped Liability": [
        r"\buncapped\b",
        r"\bwithout limitation\b.*\bliability\b",
        r"\bnot subject to.*limitation\b",
        r"\bnotwithstanding.*limitation of liability\b",
        r"\bliability.*not.*limited\b"
    ],

    "Anti-Assignment": [
        r"\bassign\b",
        r"\bassignment\b",
        r"\btransfer\b.*\bagreement\b",
        r"\bmay not be assigned\b",
        r"\bwithout.*consent\b.*assign",
        r"\bdelegat"
    ],

    "Change Of Control": [
        r"\bchange of control\b",
        r"\bchange in control\b",
        r"\bchanges in control\b",
        r"\bownership.*control\b",
        r"\bcontrol.*ownership\b"
    ],

    "Post-Termination Services": [
        r"\bafter termination\b",
        r"\bafter expiration\b",
        r"\bfollowing termination\b",
        r"\bpost-termination\b",
        r"\btransition services\b",
        r"\bdisengagement assistance\b",
        r"\btermination or expiration\b",
        r"\btermination.*services\b"
    ],

    "Termination For Convenience": [
        r"\bterminate.*without cause\b",
        r"\btermination.*without cause\b",
        r"\bterminate.*for convenience\b",
        r"\btermination.*for convenience\b",
        r"\bterminate.*at any time\b",
        r"\bmay terminate.*without\b.*cause"
    ],

    "No-Solicit Of Employees": [
        r"\bsolicit\b.*\bemployees\b",
        r"\bsolicitation\b.*\bemployees\b",
        r"\bsolicit.*personnel\b",
        r"\bhire\b.*\bemployees\b",
        r"\bhire.*employee\b",
        r"\brecruit\b.*\bemployees\b",
        r"\bnon-hiring\b",
        r"\bnon.?solicit.*employees\b"
    ],

    "No-Solicit Of Customers": [
        r"\bsolicit\b.*\bcustomer\b",
        r"\bsolicitation\b.*\bcustomer\b",
        r"\bsolicit.*clients\b",
        r"\bnon.?solicit.*customer"
    ],

    "Non-Compete": [
        r"\bnon-compete\b",
        r"\bnoncompete\b",
        r"\bcompete\b.*\bparty\b",
        r"\bcompetitive\b.*\bactivities\b",
        r"\bshall not compete\b"
    ],

    "Non-Disparagement": [
        r"\bdisparag",
        r"\bderogatory\b",
        r"\bnegative statements\b"
    ],

    "Exclusivity": [
        r"\bexclusive\b",
        r"\bexclusivity\b",
        r"\bexclusively\b",
        r"\bsolely\b.*\bprovider\b"
    ],

    "License Grant": [
        r"\blicense\b.*\bgrant\b",
        r"\bgrants\b.*\blicense\b",
        r"\blicense.*right\b",
        r"\bright to use\b"
    ],

    "Non-Transferable License": [
        r"\bnon-transferable\b",
        r"\bnontransferable\b",
        r"\bmay not transfer\b.*\blicense\b",
        r"\blicense.*may not be transferred\b"
    ],

    "Ip Ownership Assignment": [
        r"\bassign.*intellectual property\b",
        r"\bintellectual property.*assign\b",
        r"\bownership.*intellectual property\b",
        r"\bassign.*IP\b",
        r"\bIP.*ownership\b"
    ],

    "Joint Ip Ownership": [
        r"\bjoint ownership\b",
        r"\bjointly owned\b",
        r"\bco-own\b",
        r"\bjoint.*intellectual property\b"
    ],

    "Warranty Duration": [
        r"\bwarranty\b",
        r"\bwarranties\b",
        r"\bwarranty period\b",
        r"\bwarranty.*period\b",
        r"\bmonths\b.*\bwarranty\b",
        r"\bdays\b.*\bwarranty\b",
        r"\byears\b.*\bwarranty\b"
    ],

    "Minimum Commitment": [
        r"\bminimum commitment\b",
        r"\bminimum purchase\b",
        r"\bminimum amount\b",
        r"\bminimum volume\b",
        r"\bminimum.*purchase\b",
        r"\bcommitted.*minimum\b"
    ],

    "Volume Restriction": [
        r"\bvolume restriction\b",
        r"\bmaximum number\b",
        r"\bmaximum volume\b",
        r"\bquantity limit\b",
        r"\busage limit\b"
    ],

    "Revenue/Profit Sharing": [
        r"\bprofit sharing\b",
        r"\brevenue sharing\b",
        r"\bshare.*revenue\b",
        r"\bshare.*profits\b",
        r"\bpercentage.*revenue\b",
        r"\bpercentage.*profit\b"
    ],

    "Liquidated Damages": [
        r"\bliquidated damages\b",
        r"\bliquidated damage\b"
    ],

    "Third Party Beneficiary": [
        r"\bthird party beneficiar",
        r"\bthird-party beneficiar",
        r"\bbeneficiary\b"
    ],

    "Rofr/Rofo/Rofn": [
        r"\bright of first refusal\b",
        r"\bright of first offer\b",
        r"\bright of first negotiation\b"
    ],

    "Covenant Not To Sue": [
        r"\bcovenant not to sue\b",
        r"\bagree.*not to sue\b",
        r"\bpromise not to sue\b"
    ],

    "Source Code Escrow": [
        r"\bsource code escrow\b",
        r"\bsource code\b.*\bescrow\b",
        r"\bescrow.*source code\b"
    ],

    "Price Restrictions": [
        r"\bprice restriction\b",
        r"\bpricing restriction\b",
        r"\bresale price\b",
        r"\bprice.*restriction\b"
    ],

    "Most Favored Nation": [
        r"\bmost favored nation\b",
        r"\bmost-favored-nation\b",
        r"\bno less favorable\b"
    ],

    "Unlimited/All-You-Can-Eat-License": [
        r"\bunlimited license\b",
        r"\bunlimited use\b",
        r"\ball-you-can-eat\b"
    ],

    "Affiliate License-Licensee": [
        r"\blicense.*affiliate\b",
        r"\blicense.*licensee affiliate\b"
    ],

    "Affiliate License-Licensor": [
        r"\blicense.*affiliate\b",
        r"\blicensor.*affiliate\b"
    ],

    "Competitive Restriction Exception": [
        r"\bexception\b.*\bcompetitive\b",
        r"\bcompetitive.*exception\b"
    ]
}


# ============================================================
# VALIDATE
# ============================================================

results = []

for _, row in df.iterrows():

    text = (
        str(row["section_title"]) +
        " " +
        str(row["text"])
    ).lower()

    predicted = row["roberta_clause"]

    matched_patterns = []

    if predicted in patterns:

        for pattern in patterns[predicted]:

            if re.search(pattern, text):
                matched_patterns.append(pattern)

    evidence_count = len(matched_patterns)

    if evidence_count >= 1:
        evidence_status = "SUPPORTED"
    else:
        evidence_status = "REJECTED"

    results.append({

        "section_number":
            row["section_number"],

        "section_title":
            row["section_title"],

        "clause":
            predicted,

        "roberta_confidence":
            row["roberta_confidence"],

        "semantic_similarity":
            row["semantic_similarity"],

        "evidence_matches":
            evidence_count,

        "evidence_status":
            evidence_status,

        "text":
            row["text"]
    })


result = pd.DataFrame(results)

result.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# SUMMARY
# ============================================================

supported = result[
    result["evidence_status"] == "SUPPORTED"
]

rejected = result[
    result["evidence_status"] == "REJECTED"
]

print("\n" + "=" * 80)
print("          EVIDENCE VALIDATION COMPLETED")
print("=" * 80)

print(f"\nTotal sections : {len(result)}")
print(f"Supported      : {len(supported)}")
print(f"Rejected       : {len(rejected)}")


# ============================================================
# SUPPORTED CANDIDATES
# ============================================================

print("\n" + "-" * 80)
print("SUPPORTED CLAUSE CANDIDATES")
print("-" * 80)

for _, row in supported.sort_values(
    "roberta_confidence",
    ascending=False
).iterrows():

    print(
        f"\nSection {row['section_number']} - "
        f"{row['section_title']}"
    )

    print(
        f"Clause       : {row['clause']}"
    )

    print(
        f"RoBERTa      : "
        f"{row['roberta_confidence']:.2%}"
    )

    print(
        f"Semantic     : "
        f"{row['semantic_similarity']:.2%}"
    )

    print(
        f"Evidence     : "
        f"{row['evidence_matches']} match(es)"
    )


print("\n" + "=" * 80)
print(f"Saved: {OUTPUT_FILE}")
print("=" * 80)