import pandas as pd
import ollama
import re
import os


# ============================================================
# SETTINGS
# ============================================================

INPUT_FILE = "final_verified_evidence.csv"
OUTPUT_FILE = "contract_risk_analysis.csv"

MODEL_NAME = "llama3.2:3b"
TEMPERATURE = 0

# ============================================================
# OUTPUT COLUMNS
# ============================================================

OUTPUT_COLUMNS = [
    "clause",
    "section",
    "risk_level",
    "why_risk_level",
    "what_contract_says",
    "key_evidence",
    "analysis"
]


# ============================================================
# LOAD VERIFIED EVIDENCE
# ============================================================

if not os.path.exists(INPUT_FILE):

    print(f"ERROR: {INPUT_FILE} not found.")

    pd.DataFrame(
        columns=OUTPUT_COLUMNS
    ).to_csv(
        OUTPUT_FILE,
        index=False
    )

    raise SystemExit(1)


try:

    df = pd.read_csv(INPUT_FILE)

except pd.errors.EmptyDataError:

    print("No verified clauses found.")

    pd.DataFrame(
        columns=OUTPUT_COLUMNS
    ).to_csv(
        OUTPUT_FILE,
        index=False
    )

    raise SystemExit(0)


print("=" * 80)
print("FINAL GENAI CONTRACT RISK ANALYSIS")
print("=" * 80)

print(f"\nInput file: {INPUT_FILE}")
print(f"Verified clauses: {len(df)}")


# ============================================================
# EMPTY DATASET
# ============================================================

if len(df) == 0:

    print(
        "\nNo clauses were verified by the strict validation pipeline."
    )

    pd.DataFrame(
        columns=OUTPUT_COLUMNS
    ).to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(
        f"Saved empty analysis result to: {OUTPUT_FILE}"
    )

    raise SystemExit(0)


# ============================================================
# SAFE VALUE
# ============================================================

def get_value(row, possible_columns, default=""):

    for column in possible_columns:

        if column not in row.index:
            continue

        value = row[column]

        if pd.isna(value):
            continue

        value = str(value).strip()

        if value:
            return value

    return default


# ============================================================
# GET SECTION
# ============================================================

def get_section(row):

    return get_value(
        row,
        [
            "section_number",
            "section"
        ],
        "Unknown"
    )


# ============================================================
# GET VERIFIED EVIDENCE
# ============================================================

def get_evidence(row):

    return get_value(
        row,
        [
            "key_evidence",
            "evidence",
            "text",
            "clause_text"
        ],
        ""
    )


# ============================================================
# OLLAMA ANALYSIS
# ============================================================

def analyze_clause(
    clause,
    section,
    evidence
):

    prompt = f"""
You are an evidence-grounded contract risk analysis system.

Analyze ONLY the supplied verified contract evidence.

CLAUSE CATEGORY:
{clause}

SECTION:
{section}

VERIFIED CONTRACT EVIDENCE:
{evidence}


IMPORTANT RULES:

1. Use ONLY the supplied contract evidence.
2. Do not use outside legal knowledge.
3. Do not invent facts.
4. Do not ask for additional contract text.
5. Preserve the grammatical subject of the contract.
6. Preserve conditions, exceptions, limitations and time periods.
7. Do not combine unrelated sentences.
8. The KEY EVIDENCE must directly support the analysis.
9. The WHAT THE CONTRACT SAYS statement must be supported by the evidence.
10. If multiple subclauses exist, use only the subsection relevant to the named clause.
11. Do not use unrelated provisions.


RISK LEVEL GUIDANCE:

LOW:
Limited or clearly defined contractual obligation or exposure
with clear boundaries or conditions.

MEDIUM:
Meaningful contractual obligation or exposure with limits,
conditions, exceptions or safeguards.

HIGH:
Substantial contractual exposure based on the actual supplied
evidence, such as broad obligations, significant stated monetary
exposure, lack of a stated limit, or limited restrictions.


IMPORTANT:

Select exactly ONE:

LOW
MEDIUM
HIGH

Do not output combinations such as:

LOW/MEDIUM
MEDIUM/HIGH
HIGH/MEDIUM

If the supplied evidence genuinely does not provide enough
information to select one level, use:

INSUFFICIENT EVIDENCE


RETURN EXACTLY:

RISK LEVEL: LOW/MEDIUM/HIGH/INSUFFICIENT EVIDENCE

WHY THIS RISK LEVEL:
Explain why the selected level follows from the supplied evidence.

WHAT THE CONTRACT SAYS:
Accurately describe what the contract explicitly states.

KEY EVIDENCE:
Copy the exact sentence or sentences from the supplied evidence
that directly support the analysis.

FINAL CHECK:
SUPPORTED BY EVIDENCE
"""

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        options={
            "temperature": 0
        }
    )

    return response["message"]["content"].strip()


# ============================================================
# STRICT RETRY
# ============================================================

def retry_analysis(
    clause,
    section,
    evidence
):

    prompt = f"""
Perform a strict evidence-only contract analysis.

CLAUSE:
{clause}

SECTION:
{section}

VERIFIED EVIDENCE:
{evidence}


The evidence above is already verified.

Do NOT:
- ask for more contract text
- say the evidence is missing
- use outside legal knowledge
- invent facts
- invent obligations
- invent consequences


Return ONLY:

RISK LEVEL: LOW/MEDIUM/HIGH/INSUFFICIENT EVIDENCE

WHY THIS RISK LEVEL:
One complete sentence based only on the evidence.

WHAT THE CONTRACT SAYS:
One complete sentence describing the provision.

KEY EVIDENCE:
Copy the exact relevant sentence from the evidence.

FINAL CHECK:
SUPPORTED BY EVIDENCE
"""

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        options={
            "temperature": 0
        }
    )

    return response["message"]["content"].strip()


# ============================================================
# VALIDATE OLLAMA RESPONSE
# ============================================================

def is_valid_response(response):

    if not response:
        return False

    required = [
        "RISK LEVEL:",
        "WHY THIS RISK LEVEL:",
        "WHAT THE CONTRACT SAYS:",
        "KEY EVIDENCE:"
    ]

    for item in required:

        if item not in response.upper():

            return False


    invalid_phrases = [
        "PLEASE PROVIDE THE CONTRACT TEXT",
        "PLEASE PROVIDE THE EVIDENCE",
        "PROVIDE THE CONTRACT TEXT",
        "PROVIDE THE EVIDENCE",
        "I'M READY TO ANALYZE",
        "I AM READY TO ANALYZE"
    ]

    upper_response = response.upper()

    for phrase in invalid_phrases:

        if phrase in upper_response:

            return False


    risk_match = re.search(
        r"RISK LEVEL:\s*(LOW|MEDIUM|HIGH|INSUFFICIENT EVIDENCE)",
        response,
        re.IGNORECASE
    )

    if not risk_match:

        return False


    return True


# ============================================================
# PARSE RESPONSE
# ============================================================

def parse_response(response):

    risk_level = "UNKNOWN"
    why = ""
    contract_says = ""
    evidence = ""

    lines = response.splitlines()

    current_section = None


    for raw_line in lines:

        line = raw_line.strip()

        if not line:
            continue

        line = line.replace("**", "").strip()

        upper = line.upper()


        # ----------------------------------------------------
        # RISK LEVEL
        # ----------------------------------------------------

        if upper.startswith("RISK LEVEL:"):

            value = line.split(
                ":",
                1
            )[1].strip().upper()

            if value in {
                "LOW",
                "MEDIUM",
                "HIGH",
                "INSUFFICIENT EVIDENCE"
            }:

                risk_level = value

            else:

                risk_level = "UNKNOWN"

            current_section = "risk"

            continue


        # ----------------------------------------------------
        # WHY
        # ----------------------------------------------------

        if upper.startswith("WHY THIS RISK LEVEL:"):

            value = line.split(
                ":",
                1
            )[1].strip()

            if value:
                why = value

            current_section = "why"

            continue


        # ----------------------------------------------------
        # WHAT CONTRACT SAYS
        # ----------------------------------------------------

        if upper.startswith("WHAT THE CONTRACT SAYS:"):

            value = line.split(
                ":",
                1
            )[1].strip()

            if value:
                contract_says = value

            current_section = "contract"

            continue


        # ----------------------------------------------------
        # KEY EVIDENCE
        # ----------------------------------------------------

        if upper.startswith("KEY EVIDENCE:"):

            value = line.split(
                ":",
                1
            )[1].strip()

            if value:
                evidence = value

            current_section = "evidence"

            continue


        # ----------------------------------------------------
        # FINAL CHECK
        # ----------------------------------------------------

        if upper.startswith("FINAL CHECK:"):

            current_section = None

            continue


        # ----------------------------------------------------
        # CONTINUATION LINES
        # ----------------------------------------------------

        if current_section == "why":

            if why:
                why += " " + line
            else:
                why = line


        elif current_section == "contract":

            if contract_says:
                contract_says += " " + line
            else:
                contract_says = line


        elif current_section == "evidence":

            if evidence:
                evidence += " " + line
            else:
                evidence = line


        elif current_section == "risk":

            # Some Ollama responses omit the WHY heading.
            if (
                line.upper()
                not in {
                    "LOW",
                    "MEDIUM",
                    "HIGH",
                    "INSUFFICIENT EVIDENCE"
                }
            ):

                if why:
                    why += " " + line
                else:
                    why = line


    return (
        risk_level,
        why.strip(),
        contract_says.strip(),
        evidence.strip()
    )


# ============================================================
# SAFE FALLBACK
# ============================================================

def safe_fallback(evidence):

    return {
        "risk_level": "UNKNOWN",

        "why_risk_level": (
            "The verified contract evidence was retained, "
            "but a valid generated risk assessment was not produced."
        ),

        "what_contract_says": evidence,

        "key_evidence": evidence,

        "analysis": (
            "Verified evidence retained without generating "
            "unsupported conclusions."
        )
    }


# ============================================================
# PROCESS CLAUSES
# ============================================================

results = []


for index, row in df.iterrows():

    clause = get_value(
        row,
        ["clause"],
        "Unknown"
    )

    section = get_section(row)

    evidence = get_evidence(row)


    print("\n" + "=" * 80)

    print(
        f"Analyzing {index + 1}/{len(df)}"
    )

    print(
        f"Clause  : {clause}"
    )

    print(
        f"Section : {section}"
    )


    # --------------------------------------------------------
    # NO EVIDENCE
    # --------------------------------------------------------

    if not evidence:

        print(
            "WARNING: No verified evidence available."
        )

        fallback = safe_fallback(
            "No verified contract evidence available."
        )

        results.append(
            {
                "clause": clause,
                "section": section,
                **fallback
            }
        )

        continue


    # --------------------------------------------------------
    # FIRST ATTEMPT
    # --------------------------------------------------------

    try:

        response = analyze_clause(
            clause,
            section,
            evidence
        )

    except Exception as e:

        print(
            f"WARNING: Ollama error: {e}"
        )

        response = ""


    print("\n--- RAW OLLAMA RESPONSE ---")

    print(response)

    print("--- END RAW OLLAMA RESPONSE ---")


    # --------------------------------------------------------
    # PRESERVE INITIAL RISK LEVEL
    # --------------------------------------------------------

    initial_risk_level, _, _, _ = parse_response(response)


    # --------------------------------------------------------
    # VALIDATE FIRST ATTEMPT
    # --------------------------------------------------------

    if not is_valid_response(response):

        print(
            f"\nWARNING: Initial Ollama analysis failed "
            f"for {clause}."
        )

        print(
            "Retrying with strict evidence-only prompt..."
        )


        # ----------------------------------------------------
        # SECOND ATTEMPT
        # ----------------------------------------------------

        try:

            response = retry_analysis(
                clause,
                section,
                evidence
            )

        except Exception as e:

            print(
                f"WARNING: Ollama retry failed: {e}"
            )

            response = ""


        print("\n--- RETRY OLLAMA RESPONSE ---")

        print(response)

        print("--- END RETRY OLLAMA RESPONSE ---")


    # --------------------------------------------------------
    # FINAL VALIDATION
    # --------------------------------------------------------

    if not is_valid_response(response):

        print(
            "\nWARNING: Ollama failed to produce a valid "
            "structured analysis."
        )

        print(
            "Using verified contract evidence safely."
        )

        fallback = safe_fallback(
            evidence
        )

        results.append(
            {
                "clause": clause,
                "section": section,
                **fallback
            }
        )

        print(
            f"Risk Level: {fallback['risk_level']}"
        )

        continue


    # --------------------------------------------------------
    # PARSE
    # --------------------------------------------------------

    (
        risk_level,
        why,
        contract_says,
        generated_evidence
    ) = parse_response(response)


    # --------------------------------------------------------
    # RISK LEVEL LOCK
    # --------------------------------------------------------

    if initial_risk_level in {
        "LOW",
        "MEDIUM",
        "HIGH",
        "INSUFFICIENT EVIDENCE"
    }:

        if risk_level != initial_risk_level:

            print(
                f"Risk level preserved from initial analysis: "
                f"{initial_risk_level}"
            )

        risk_level = initial_risk_level


    # --------------------------------------------------------
    # EVIDENCE SAFETY
    # --------------------------------------------------------

    if not generated_evidence:

        print(
            "WARNING: Ollama omitted KEY EVIDENCE."
        )

        generated_evidence = evidence


    if not contract_says:

        print(
            "WARNING: Ollama omitted contract description."
        )

        contract_says = evidence


    if not why:

        print(
            "WARNING: Ollama omitted risk explanation."
        )

        why = (
            "The provision represents the selected risk level "
            "based only on the supplied verified evidence."
        )



 # =========================================================
    # RISK-EXPLANATION CONSISTENCY CHECK
    # =========================================================

    def has_risk_contradiction(risk_level, text):

        text = text.upper()

        if risk_level == "HIGH":

            contradictory_phrases = [
                "LOW RISK",
                "LOWER RISK",
                "MINIMAL RISK",
                "LIMITED RISK",
                "RELATIVELY LOW",
                "LOW EXPOSURE"
            ]

        elif risk_level == "MEDIUM":

            contradictory_phrases = [
                "LOW RISK",
                "LOWER RISK",
                "MINIMAL RISK",
                "LIMITED RISK",
                "RELATIVELY LOW",
                "HIGH RISK",
                "HIGHER RISK",
                "SUBSTANTIAL RISK",
                "SEVERE RISK"
            ]

        elif risk_level == "LOW":

            contradictory_phrases = [
                "HIGH RISK",
                "HIGHER RISK",
                "SUBSTANTIAL RISK",
                "SEVERE RISK"
            ]

        else:

            return False

        return any(
            phrase in text
            for phrase in contradictory_phrases
        )


    if has_risk_contradiction(
        risk_level,
        why
    ):

        print(
            "\nWARNING: Risk explanation contradicts "
            f"locked risk level ({risk_level})."
        )

        why = (
            f"The provision is classified as {risk_level} "
            "based only on the verified contract evidence. "
            "The stated contractual terms determine the "
            "level of contractual exposure identified by "
            "the analysis."
        )

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    results.append(
        {
            "clause": clause,
            "section": section,
            "risk_level": risk_level,
            "why_risk_level": why,
            "what_contract_says": contract_says,
            "key_evidence": generated_evidence,
            "analysis": response
        }
    )


    print(
        f"\nRisk Level: {risk_level}"
    )

    print(
        f"Why: {why}"
    )

    print(
        f"Evidence: {generated_evidence}"
    )


# ============================================================
# SAVE CSV
# ============================================================

result_df = pd.DataFrame(
    results,
    columns=OUTPUT_COLUMNS
)


result_df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 80)
print("GENAI RISK ANALYSIS COMPLETED")
print("=" * 80)

print(
    f"\nClauses analyzed: {len(result_df)}"
)

if len(result_df) > 0:

    print("\nRisk levels:")

    print(
        result_df[
            "risk_level"
        ].value_counts()
    )

print(
    f"\nSaved: {OUTPUT_FILE}"
)

print("=" * 80)