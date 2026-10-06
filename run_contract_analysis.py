import subprocess
import sys
import os

# ============================================================
# CONTRACT RISK ANALYSIS - MASTER PIPELINE
# ============================================================

if len(sys.argv) > 1:
    pdf_file = sys.argv[1]
else:
    pdf_file = "Service_agreement.pdf"

if not os.path.exists(pdf_file):
    print(f"\nERROR: PDF file not found:")
    print(pdf_file)
    sys.exit(1)

PIPELINE = [
    "pdf_extractor.py",
    "preprocess_contract.py",
    "extract_contract_sections.py",
    "classify_contract_sections.py",
    "validate_section_predictions.py",
    "validate_clause_evidence.py",
    "strict_clause_validation.py",
    "prepare_final_evidence.py",
    "generate_final_risk_report.py",
    "generate_contract_report.py"
]

print("=" * 80)
print("          CONTRACT RISK ANALYSIS - MASTER PIPELINE")
print("=" * 80)

print(f"\nInput PDF: {pdf_file}")

for step, script in enumerate(PIPELINE, start=1):

    print("\n" + "=" * 80)
    print(f"STEP {step}/{len(PIPELINE)} : {script}")
    print("=" * 80)

    try:

        result = subprocess.run(
            [sys.executable, script, pdf_file],
            check=True
        )

        print(f"\nCompleted: {script}")

    except subprocess.CalledProcessError as e:

        print("\n" + "!" * 80)
        print("✗ PIPELINE STOPPED")
        print(f"Failed script: {script}")
        print(f"Exit code: {e.returncode}")
        print("!" * 80)

        sys.exit(e.returncode)

print("\n" + "=" * 80)
print("              PIPELINE COMPLETED")
print("=" * 80)

print("\nFinal report:")
print("Contract_Risk_Report.pdf")

print("\nAll processing completed successfully.")