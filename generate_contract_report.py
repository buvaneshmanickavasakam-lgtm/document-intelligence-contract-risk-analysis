import pandas as pd
import os
import sys
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether
)
from xml.sax.saxutils import escape


# =========================================================
# CONFIGURATION
# =========================================================

INPUT_FILE = "contract_risk_analysis.csv"
OUTPUT_FILE = "Contract_Risk_Report.pdf"


# =========================================================
# SOURCE PDF
# =========================================================

if len(sys.argv) > 1:
    SOURCE_PDF = os.path.basename(sys.argv[1])
else:
    SOURCE_PDF = "Not specified"


# =========================================================
# CHECK INPUT
# =========================================================

if not os.path.exists(INPUT_FILE):

    print(
        f"ERROR: {INPUT_FILE} not found."
    )

    raise SystemExit(1)


try:

    df = pd.read_csv(
        INPUT_FILE
    )

except pd.errors.EmptyDataError:

    df = pd.DataFrame()


print("=" * 80)
print("CONTRACT RISK REPORT GENERATION")
print("=" * 80)

print(
    f"\nInput file: {INPUT_FILE}"
)

print(
    f"Source contract: {SOURCE_PDF}"
)

print(
    f"Verified risk findings: {len(df)}"
)


# =========================================================
# SAFE TEXT
# =========================================================

def safe_text(value, default="Not available"):

    if value is None:
        return default

    try:

        if pd.isna(value):
            return default

    except Exception:
        pass

    value = str(value).strip()

    if not value:
        return default

    return value


# =========================================================
# ESCAPE PDF TEXT
# =========================================================

def escape_text(
    value,
    default="Not available"
):

    return escape(
        safe_text(
            value,
            default
        )
    )


# =========================================================
# RISK HELPERS
# =========================================================

def normalize_risk(value):

    risk = safe_text(
        value,
        "UNKNOWN"
    ).upper()

    allowed = {
        "HIGH",
        "MEDIUM",
        "LOW",
        "UNKNOWN",
        "INSUFFICIENT EVIDENCE"
    }

    if risk not in allowed:
        return "UNKNOWN"

    return risk


def risk_symbol(risk):

    symbols = {
        "HIGH": "[HIGH]",
        "MEDIUM": "[MEDIUM]",
        "LOW": "[LOW]",
        "UNKNOWN": "[UNKNOWN]",
        "INSUFFICIENT EVIDENCE":
            "[INSUFFICIENT EVIDENCE]"
    }

    return symbols.get(
        risk,
        "[UNKNOWN]"
    )


# =========================================================
# RISK COUNTS
# =========================================================

verified_count = len(df)

if (
    verified_count > 0
    and "risk_level" in df.columns
):

    normalized_risks = (
        df["risk_level"]
        .apply(normalize_risk)
    )

    risk_counts = (
        normalized_risks
        .value_counts()
        .to_dict()
    )

else:

    risk_counts = {}


high_count = risk_counts.get(
    "HIGH",
    0
)

medium_count = risk_counts.get(
    "MEDIUM",
    0
)

low_count = risk_counts.get(
    "LOW",
    0
)

unknown_count = risk_counts.get(
    "UNKNOWN",
    0
)

insufficient_count = risk_counts.get(
    "INSUFFICIENT EVIDENCE",
    0
)


# =========================================================
# STYLES
# =========================================================

styles = getSampleStyleSheet()


title_style = ParagraphStyle(
    "TitleCustom",
    parent=styles["Title"],
    fontName="Helvetica-Bold",
    fontSize=22,
    leading=26,
    alignment=TA_CENTER,
    spaceAfter=8
)


subtitle_style = ParagraphStyle(
    "SubtitleCustom",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=10,
    leading=14,
    alignment=TA_CENTER,
    spaceAfter=16
)


meta_style = ParagraphStyle(
    "MetaCustom",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=8.5,
    leading=11,
    alignment=TA_CENTER,
    spaceAfter=4
)


section_style = ParagraphStyle(
    "SectionCustom",
    parent=styles["Heading2"],
    fontName="Helvetica-Bold",
    fontSize=14,
    leading=17,
    spaceBefore=10,
    spaceAfter=8
)


clause_style = ParagraphStyle(
    "ClauseCustom",
    parent=styles["Heading3"],
    fontName="Helvetica-Bold",
    fontSize=11,
    leading=14,
    spaceBefore=5,
    spaceAfter=5
)


body_style = ParagraphStyle(
    "BodyCustom",
    parent=styles["BodyText"],
    fontName="Helvetica",
    fontSize=9,
    leading=12,
    spaceAfter=5
)


small_style = ParagraphStyle(
    "SmallCustom",
    parent=styles["BodyText"],
    fontName="Helvetica",
    fontSize=7.8,
    leading=10,
    spaceAfter=3
)


label_style = ParagraphStyle(
    "LabelCustom",
    parent=body_style,
    fontName="Helvetica-Bold",
    spaceAfter=2
)


quote_style = ParagraphStyle(
    "QuoteCustom",
    parent=body_style,
    fontName="Helvetica-Oblique",
    leftIndent=10,
    rightIndent=8,
    fontSize=8.5,
    leading=11.5,
    spaceBefore=4,
    spaceAfter=7
)


footer_style = ParagraphStyle(
    "FooterCustom",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=7,
    leading=9,
    alignment=TA_CENTER
)


# =========================================================
# PAGE HEADER / FOOTER
# =========================================================

def add_page_number(
    canvas,
    doc
):

    canvas.saveState()

    width, height = A4

    canvas.setStrokeColor(
        colors.HexColor("#CCCCCC")
    )

    canvas.line(
        15 * mm,
        10 * mm,
        width - 15 * mm,
        10 * mm
    )

    canvas.setFont(
        "Helvetica",
        7
    )

    canvas.setFillColor(
        colors.HexColor("#666666")
    )

    canvas.drawString(
        15 * mm,
        6 * mm,
        "Automated contract screening - not legal advice."
    )

    canvas.drawRightString(
        width - 15 * mm,
        6 * mm,
        f"Page {doc.page}"
    )

    canvas.restoreState()


# =========================================================
# PDF DOCUMENT
# =========================================================

doc = SimpleDocTemplate(
    OUTPUT_FILE,
    pagesize=A4,
    rightMargin=15 * mm,
    leftMargin=15 * mm,
    topMargin=15 * mm,
    bottomMargin=16 * mm
)


story = []


# =========================================================
# COVER / REPORT HEADER
# =========================================================

story.append(
    Spacer(
        1,
        12 * mm
    )
)


story.append(
    Paragraph(
        "CONTRACT RISK<br/>"
        "INTELLIGENCE REPORT",
        title_style
    )
)


story.append(
    Paragraph(
        "Evidence-Grounded Contract Analysis",
        subtitle_style
    )
)


# =========================================================
# SOURCE CONTRACT
# =========================================================

source_table = Table(
    [[
        Paragraph(
            "<b>Source Contract</b><br/>"
            + escape(SOURCE_PDF),
            meta_style
        )
    ]],
    colWidths=[
        165 * mm
    ]
)


source_table.setStyle(
    TableStyle([
        (
            "BOX",
            (0, 0),
            (-1, -1),
            0.6,
            colors.HexColor("#D0D0D0")
        ),
        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "MIDDLE"
        ),
        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            8
        ),
        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            8
        )
    ])
)


story.append(
    source_table
)


story.append(
    Spacer(
        1,
        3 * mm
    )
)


# =========================================================
# ANALYSIS INFORMATION
# =========================================================

meta_data = [
    [
        Paragraph(
            "<b>Analysis Status</b><br/>"
            "Completed",
            meta_style
        ),
        Paragraph(
            f"<b>Verified Findings</b><br/>"
            f"{verified_count}",
            meta_style
        ),
        Paragraph(
            f"<b>Analysis Date</b><br/>"
            f"{datetime.now().strftime('%d %b %Y')}",
            meta_style
        )
    ]
]


meta_table = Table(
    meta_data,
    colWidths=[
        55 * mm,
        55 * mm,
        55 * mm
    ]
)


meta_table.setStyle(
    TableStyle([
        (
            "BOX",
            (0, 0),
            (-1, -1),
            0.6,
            colors.HexColor("#D0D0D0")
        ),
        (
            "INNERGRID",
            (0, 0),
            (-1, -1),
            0.4,
            colors.HexColor("#E5E5E5")
        ),
        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "MIDDLE"
        ),
        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            8
        ),
        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            8
        )
    ])
)


story.append(
    meta_table
)


story.append(
    Spacer(
        1,
        10 * mm
    )
)


# =========================================================
# 1. EXECUTIVE SUMMARY
# =========================================================

story.append(
    Paragraph(
        "1. Executive Summary",
        section_style
    )
)


if verified_count == 0:

    summary_text = (
        "No contractual provisions passed "
        "the strict verification stage."
    )

else:

    summary_text = (
        f"The analysis identified "
        f"{verified_count} verified "
        f"contractual provision"
        f"{'s' if verified_count != 1 else ''} "
        "requiring review."
    )


story.append(
    Paragraph(
        escape_text(summary_text),
        body_style
    )
)


# =========================================================
# RISK DASHBOARD
# =========================================================

story.append(
    Spacer(
        1,
        3 * mm
    )
)


dashboard_data = [
    [
        Paragraph(
            "<b>HIGH</b>",
            meta_style
        ),
        Paragraph(
            "<b>MEDIUM</b>",
            meta_style
        ),
        Paragraph(
            "<b>LOW</b>",
            meta_style
        ),
        Paragraph(
            "<b>OTHER</b>",
            meta_style
        )
    ],
    [
        Paragraph(
            f"<b>{high_count}</b>",
            title_style
        ),
        Paragraph(
            f"<b>{medium_count}</b>",
            title_style
        ),
        Paragraph(
            f"<b>{low_count}</b>",
            title_style
        ),
        Paragraph(
            f"<b>"
            f"{unknown_count + insufficient_count}"
            f"</b>",
            title_style
        )
    ]
]


dashboard = Table(
    dashboard_data,
    colWidths=[
        42 * mm,
        42 * mm,
        42 * mm,
        42 * mm
    ]
)


dashboard.setStyle(
    TableStyle([
        (
            "BOX",
            (0, 0),
            (-1, -1),
            0.7,
            colors.HexColor("#C8C8C8")
        ),
        (
            "INNERGRID",
            (0, 0),
            (-1, -1),
            0.4,
            colors.HexColor("#DDDDDD")
        ),
        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "MIDDLE"
        ),
        (
            "ALIGN",
            (0, 0),
            (-1, -1),
            "CENTER"
        ),
        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            6
        ),
        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            6
        )
    ])
)


story.append(
    dashboard
)


# =========================================================
# 2. KEY FINDINGS
# =========================================================

story.append(
    Paragraph(
        "2. Key Findings",
        section_style
    )
)


if verified_count == 0:

    story.append(
        Paragraph(
            "No verified clauses were identified.",
            body_style
        )
    )

else:

    findings_data = [
        [
            Paragraph(
                "<b>Clause</b>",
                small_style
            ),
            Paragraph(
                "<b>Section</b>",
                small_style
            ),
            Paragraph(
                "<b>Risk</b>",
                small_style
            )
        ]
    ]


    for _, row in df.iterrows():

        clause = escape_text(
            row.get(
                "clause",
                "Unknown"
            )
        )

        section = escape_text(
            row.get(
                "section",
                "Unknown"
            )
        )

        risk = normalize_risk(
            row.get(
                "risk_level",
                "UNKNOWN"
            )
        )

        findings_data.append(
            [
                Paragraph(
                    clause,
                    small_style
                ),
                Paragraph(
                    section,
                    small_style
                ),
                Paragraph(
                    risk_symbol(risk),
                    small_style
                )
            ]
        )


    findings_table = Table(
        findings_data,
        colWidths=[
            95 * mm,
            35 * mm,
            35 * mm
        ],
        repeatRows=1
    )


    findings_table.setStyle(
        TableStyle([
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.6,
                colors.HexColor("#CCCCCC")
            ),
            (
                "INNERGRID",
                (0, 0),
                (-1, -1),
                0.4,
                colors.HexColor("#E0E0E0")
            ),
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#F1F1F1")
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                6
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                6
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                5
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                5
            )
        ])
    )


    story.append(
        findings_table
    )


# =========================================================
# 3. RISKS & IMPORTANT CLAUSES
# =========================================================

story.append(
    Paragraph(
        "3. Risks &amp; Important Clauses",
        section_style
    )
)


if verified_count == 0:

    story.append(
        Paragraph(
            "No verified clauses were identified.",
            body_style
        )
    )

else:

    for index, row in df.iterrows():

        clause = safe_text(
            row.get(
                "clause",
                "Unknown"
            )
        )

        section = safe_text(
            row.get(
                "section",
                "Unknown"
            )
        )

        risk = normalize_risk(
            row.get(
                "risk_level",
                "UNKNOWN"
            )
        )

        why = safe_text(
            row.get(
                "why_risk_level",
                ""
            )
        )

        what = safe_text(
            row.get(
                "what_contract_says",
                ""
            )
        )

        evidence = safe_text(
            row.get(
                "key_evidence",
                ""
            )
        )


        block = []


        block.append(
            Paragraph(
                f"{index + 1}. "
                f"{escape_text(clause)}",
                clause_style
            )
        )


        block.append(
            Paragraph(
                f"<b>Section:</b> "
                f"{escape_text(section)}"
                f"&nbsp;&nbsp;&nbsp;"
                f"<b>Risk:</b> "
                f"{risk_symbol(risk)}",
                label_style
            )
        )


        block.append(
            Paragraph(
                "<b>Why It Matters</b>",
                body_style
            )
        )


        block.append(
            Paragraph(
                escape_text(why),
                body_style
            )
        )


        block.append(
            Paragraph(
                "<b>What the Contract Says</b>",
                body_style
            )
        )


        block.append(
            Paragraph(
                escape_text(what),
                body_style
            )
        )


        block.append(
            Paragraph(
                "<b>Exact Contract Evidence</b>",
                body_style
            )
        )


        block.append(
            Paragraph(
                f"“{escape_text(evidence)}”",
                quote_style
            )
        )


        story.append(
            KeepTogether(block)
        )


# =========================================================
# 4. QUESTIONS TO CONSIDER BEFORE SIGNING
# =========================================================

story.append(
    Paragraph(
        "4. Questions to Consider Before Signing",
        section_style
    )
)

if verified_count == 0:

    story.append(
        Paragraph(
            "No verified clauses were available "
            "for review.",
            body_style
        )
    )

else:

    for _, row in df.iterrows():

        clause = safe_text(
            row.get(
                "clause",
                "this provision"
            )
        )

        what = safe_text(
            row.get(
                "what_contract_says",
                ""
            )
        )

        clause_upper = clause.upper()

        # -------------------------------------------------
        # CLAUSE-SPECIFIC QUESTIONS
        # -------------------------------------------------

        if "CAP ON LIABILITY" in clause_upper:

            question = (
                "• Are the scope and exclusions of the stated "
                "liability cap clearly understood before signing, "
                "based on the contract evidence?"
            )

        elif "INSURANCE" in clause_upper:

            question = (
                "• Are the required insurance types and minimum "
                "coverage limits clearly understood before signing?"
            )

        elif "NO-SOLICIT" in clause_upper:

            question = (
                "• Are the scope, duration, and conditions of the "
                "no-solicitation provision clearly understood "
                "before signing, based on the contract evidence?"
            )

        elif "POST-TERMINATION SERVICES" in clause_upper:

            question = (
                "• Are the services, obligations, and conditions "
                "that continue after termination clearly understood "
                "before signing?"
            )

        else:

            question = (
                f"• What specific requirement, limitation, "
                f"exception, or condition does the {clause} "
                f"provision state, and is it clearly understood "
                f"before signing?"
            )

        story.append(
            Paragraph(
                escape_text(question),
                body_style
            )
        )
# =========================================================
# 5. IMPORTANT EVIDENCE
# =========================================================

story.append(
    Paragraph(
        "5. Important Evidence",
        section_style
    )
)


if verified_count == 0:

    story.append(
        Paragraph(
            "No verified evidence was available.",
            body_style
        )
    )

else:

    for _, row in df.iterrows():

        clause = safe_text(
            row.get(
                "clause",
                "Unknown"
            )
        )

        section = safe_text(
            row.get(
                "section",
                "Unknown"
            )
        )

        evidence = safe_text(
            row.get(
                "key_evidence",
                ""
            )
        )


        story.append(
            Paragraph(
                f"<b>{escape_text(clause)} "
                f"— Section "
                f"{escape_text(section)}:</b>",
                body_style
            )
        )


        story.append(
            Paragraph(
                f"“{escape_text(evidence)}”",
                quote_style
            )
        )


# =========================================================
# 6. ANALYSIS METHODOLOGY
# =========================================================

story.append(
    Paragraph(
        "6. Analysis Methodology",
        section_style
    )
)


methodology = (
    "The contract is processed through a multi-stage "
    "evidence-grounded analysis pipeline. Contract text "
    "is extracted and prepared before clause categories "
    "are identified using RoBERTa. Candidate findings are "
    "then validated using semantic similarity and strict "
    "evidence validation. Only verified evidence is passed "
    "to the generative analysis stage, which uses Llama 3.2 3B "
    "to produce an evidence-grounded explanation."
)


story.append(
    Paragraph(
        methodology,
        body_style
    )
)


method_steps = [
    [
        "1",
        "PDF Extraction"
    ],
    [
        "2",
        "Contract Section Detection"
    ],
    [
        "3",
        "RoBERTa Clause Classification"
    ],
    [
        "4",
        "MiniLM Semantic Validation"
    ],
    [
        "5",
        "Strict Evidence Validation"
    ],
    [
        "6",
        "Evidence Preparation"
    ],
    [
        "7",
        "Llama 3.2 3B Risk Analysis"
    ],
    [
        "8",
        "Automated Risk Report"
    ]
]


method_table = Table(
    method_steps,
    colWidths=[
        12 * mm,
        153 * mm
    ]
)


method_table.setStyle(
    TableStyle([
        (
            "BOX",
            (0, 0),
            (-1, -1),
            0.5,
            colors.HexColor("#D0D0D0")
        ),
        (
            "INNERGRID",
            (0, 0),
            (-1, -1),
            0.3,
            colors.HexColor("#E5E5E5")
        ),
        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "MIDDLE"
        ),
        (
            "ALIGN",
            (0, 0),
            (0, -1),
            "CENTER"
        ),
        (
            "LEFTPADDING",
            (0, 0),
            (-1, -1),
            6
        ),
        (
            "RIGHTPADDING",
            (0, 0),
            (-1, -1),
            6
        ),
        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            5
        ),
        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            5
        )
    ])
)


story.append(
    method_table
)


# =========================================================
# 7. IMPORTANT NOTICE
# =========================================================

story.append(
    Paragraph(
        "7. Important Notice",
        section_style
    )
)


disclaimer = (
    "This report is produced by an automated "
    "contract-screening system. The findings are based "
    "on the contract evidence identified and verified "
    "by the system. They are intended to support review "
    "and discussion and do not constitute legal advice, "
    "a legal opinion, or a substitute for review by a "
    "qualified legal professional."
)


story.append(
    Paragraph(
        disclaimer,
        body_style
    )
)


story.append(
    Spacer(
        1,
        5 * mm
    )
)


story.append(
    Paragraph(
        "<b>Automated contract screening — "
        "not legal advice.</b>",
        footer_style
    )
)


# =========================================================
# BUILD PDF
# =========================================================

doc.build(
    story,
    onFirstPage=add_page_number,
    onLaterPages=add_page_number
)


# =========================================================
# COMPLETE
# =========================================================

print(
    "\n" + "=" * 80
)

print(
    "CONTRACT RISK PDF GENERATED"
)

print(
    "=" * 80
)

print(
    f"\nSaved: {OUTPUT_FILE}"
)

print(
    "\nPDF generation completed successfully."
)