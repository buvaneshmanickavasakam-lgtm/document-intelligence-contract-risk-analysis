import pandas as pd
import torch
from transformers import RobertaTokenizer, RobertaForSequenceClassification
from tqdm import tqdm

# ============================================================
# CONFIGURATION
# ============================================================

SECTIONS_FILE = "contract_sections.csv"
MODEL_PATH = "contract_roberta_model"

MAX_LENGTH = 512
STRIDE = 128

# ============================================================
# LOAD MODEL
# ============================================================

print("=" * 80)
print("          CONTRACT SECTION CLASSIFICATION")
print("=" * 80)

print("\nLoading RoBERTa model...")

tokenizer = RobertaTokenizer.from_pretrained(MODEL_PATH)
model = RobertaForSequenceClassification.from_pretrained(MODEL_PATH)

model.eval()

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

print(f"Device : {device}")
print(f"Labels : {model.config.num_labels}")

# ============================================================
# LABEL MAPPING
# ============================================================

label_names = [
    "Affiliate License-Licensee",
    "Affiliate License-Licensor",
    "Anti-Assignment",
    "Audit Rights",
    "Cap On Liability",
    "Change Of Control",
    "Competitive Restriction Exception",
    "Covenant Not To Sue",
    "Exclusivity",
    "Insurance",
    "Ip Ownership Assignment",
    "Irrevocable Or Perpetual License",
    "Joint Ip Ownership",
    "License Grant",
    "Liquidated Damages",
    "Minimum Commitment",
    "Most Favored Nation",
    "No-Solicit Of Customers",
    "No-Solicit Of Employees",
    "Non-Compete",
    "Non-Disparagement",
    "Non-Transferable License",
    "Post-Termination Services",
    "Price Restrictions",
    "Revenue/Profit Sharing",
    "Rofr/Rofo/Rofn",
    "Source Code Escrow",
    "Termination For Convenience",
    "Third Party Beneficiary",
    "Uncapped Liability",
    "Unlimited/All-You-Can-Eat-License",
    "Volume Restriction",
    "Warranty Duration"
]

# ============================================================
# LOAD SECTIONS
# ============================================================

df = pd.read_csv(SECTIONS_FILE)

print(f"\nSections loaded : {len(df)}")

# ============================================================
# CLASSIFY ONE SECTION
# ============================================================

def classify_section(section_number, section_title, text):

    # Include heading because it provides useful context
    full_text = f"{section_number} {section_title}\n{text}"

    # Tokenize WITHOUT truncating the entire section.
    # This allows us to handle sections longer than 512 tokens.
    encoded = tokenizer(
        full_text,
        truncation=False,
        return_attention_mask=True
    )

    input_ids = encoded["input_ids"]
    attention_mask = encoded["attention_mask"]

    # --------------------------------------------------------
    # Create sliding windows
    # --------------------------------------------------------

    windows = []

    start = 0

    while start < len(input_ids):

        end = min(start + MAX_LENGTH, len(input_ids))

        window_ids = input_ids[start:end]
        window_mask = attention_mask[start:end]

        # RoBERTa needs special tokens
        if len(window_ids) > MAX_LENGTH:
            window_ids = window_ids[:MAX_LENGTH]
            window_mask = window_mask[:MAX_LENGTH]

        windows.append(
            (
                window_ids,
                window_mask
            )
        )

        if end == len(input_ids):
            break

        start += MAX_LENGTH - STRIDE

    # --------------------------------------------------------
    # Run RoBERTa on each window
    # --------------------------------------------------------

    window_logits = []

    with torch.no_grad():

        for ids, mask in windows:

            input_tensor = torch.tensor(
                [ids],
                dtype=torch.long
            ).to(device)

            mask_tensor = torch.tensor(
                [mask],
                dtype=torch.long
            ).to(device)

            outputs = model(
                input_ids=input_tensor,
                attention_mask=mask_tensor
            )

            window_logits.append(
                outputs.logits[0].cpu()
            )

    # --------------------------------------------------------
    # Aggregate window predictions
    # --------------------------------------------------------

    # Average logits across all windows
    logits = torch.stack(window_logits).mean(dim=0)

    probabilities = torch.softmax(logits, dim=0)

    predicted_id = torch.argmax(probabilities).item()

    confidence = probabilities[predicted_id].item()

    predicted_clause = label_names[predicted_id]

    return (
        predicted_clause,
        confidence,
        len(windows)
    )


# ============================================================
# CLASSIFY ALL CONTRACT SECTIONS
# ============================================================

results = []

print("\nClassifying contract sections...\n")

for index, row in tqdm(
    df.iterrows(),
    total=len(df)
):

    predicted_clause, confidence, num_windows = classify_section(
        row["section_number"],
        row["section_title"],
        row["text"]
    )

    results.append({
        "section_number": row["section_number"],
        "section_title": row["section_title"],
        "predicted_clause": predicted_clause,
        "confidence": confidence,
        "num_windows": num_windows,
        "text": row["text"]
    })


# ============================================================
# SAVE RESULTS
# ============================================================

results_df = pd.DataFrame(results)

results_df.to_csv(
    "classified_contract_sections.csv",
    index=False
)

# ============================================================
# DISPLAY RESULTS
# ============================================================

print("\n" + "=" * 80)
print("          CLASSIFICATION COMPLETED")
print("=" * 80)

print(f"\nTotal sections : {len(results_df)}")

print("\nTop predictions:")

display_df = results_df.sort_values(
    "confidence",
    ascending=False
).head(30)

for _, row in display_df.iterrows():

    print(
        f"\nSection {row['section_number']} - "
        f"{row['section_title']}"
    )

    print(
        f"Prediction : {row['predicted_clause']}"
    )

    print(
        f"Confidence : {row['confidence']:.2%}"
    )

    print(
        f"Windows    : {row['num_windows']}"
    )

print("\n" + "=" * 80)
print("Saved: classified_contract_sections.csv")
print("=" * 80)