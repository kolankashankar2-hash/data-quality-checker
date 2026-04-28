"""
Automated Data Quality Checker for Annotation Datasets
Author: Kolanka Bhavani Sankar
Description: Scans CSV annotation files for quality issues like duplicates,
             missing labels, inconsistencies and generates a detailed report.
"""

import pandas as pd
import json
import os
import sys
from datetime import datetime


# ── CONFIG ────────────────────────────────────────────────────────────────────
LABEL_COLUMN   = "label"       # Column that contains the annotation/label
TEXT_COLUMN    = "text"        # Column that contains the input text
ID_COLUMN      = "id"          # Column for unique record ID
VALID_LABELS   = ["positive", "negative", "neutral", "irrelevant"]  # Expected labels
# ─────────────────────────────────────────────────────────────────────────────


def load_data(filepath):
    """Load CSV or JSON annotation file."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".csv":
        df = pd.read_csv(filepath)
    elif ext == ".json":
        df = pd.read_json(filepath)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Use CSV or JSON.")
    print(f"[✓] Loaded {len(df)} records from '{filepath}'")
    return df


def check_missing_values(df):
    """Find rows with missing labels or text."""
    issues = []
    missing_labels = df[df[LABEL_COLUMN].isna() | (df[LABEL_COLUMN].astype(str).str.strip() == "")]
    missing_text   = df[df[TEXT_COLUMN].isna()  | (df[TEXT_COLUMN].astype(str).str.strip()  == "")]

    for idx in missing_labels.index:
        issues.append({"row": int(idx) + 2, "id": df.at[idx, ID_COLUMN], "issue": "Missing Label", "severity": "HIGH", "value": ""})
    for idx in missing_text.index:
        issues.append({"row": int(idx) + 2, "id": df.at[idx, ID_COLUMN], "issue": "Missing Text", "severity": "HIGH", "value": ""})

    return issues


def check_duplicate_rows(df):
    """Detect exact duplicate records."""
    issues = []
    dupes = df[df.duplicated(subset=[TEXT_COLUMN, LABEL_COLUMN], keep=False)]
    seen = set()
    for idx in dupes.index:
        key = (str(df.at[idx, TEXT_COLUMN]), str(df.at[idx, LABEL_COLUMN]))
        if key not in seen:
            seen.add(key)
            issues.append({"row": int(idx) + 2, "id": df.at[idx, ID_COLUMN], "issue": "Duplicate Record", "severity": "MEDIUM", "value": df.at[idx, TEXT_COLUMN][:60]})
    return issues


def check_invalid_labels(df):
    """Find labels that are not in the valid label set."""
    issues = []
    for idx, row in df.iterrows():
        lbl = str(row[LABEL_COLUMN]).strip().lower()
        if lbl not in VALID_LABELS and lbl not in ("nan", ""):
            issues.append({"row": int(idx) + 2, "id": row[ID_COLUMN], "issue": "Invalid Label", "severity": "HIGH", "value": row[LABEL_COLUMN]})
    return issues


def check_inconsistent_labels(df):
    """Same text annotated with different labels = inconsistency."""
    issues = []
    grouped = df.groupby(TEXT_COLUMN)[LABEL_COLUMN].nunique()
    inconsistent_texts = grouped[grouped > 1].index
    for text in inconsistent_texts:
        rows = df[df[TEXT_COLUMN] == text]
        labels_found = rows[LABEL_COLUMN].unique().tolist()
        for idx in rows.index:
            issues.append({"row": int(idx) + 2, "id": df.at[idx, ID_COLUMN], "issue": "Inconsistent Label", "severity": "HIGH", "value": f"Same text labelled as: {labels_found}"})
    return issues


def check_short_text(df, min_chars=5):
    """Flag suspiciously short text entries."""
    issues = []
    for idx, row in df.iterrows():
        text = str(row[TEXT_COLUMN]).strip()
        if 0 < len(text) < min_chars:
            issues.append({"row": int(idx) + 2, "id": row[ID_COLUMN], "issue": "Suspiciously Short Text", "severity": "LOW", "value": text})
    return issues


def calculate_quality_score(total_records, total_issues, high, medium, low):
    """Calculate overall dataset quality score out of 100."""
    if total_records == 0:
        return 0
    penalty = (high * 3) + (medium * 2) + (low * 1)
    max_penalty = total_records * 3
    score = max(0, 100 - round((penalty / max_penalty) * 100))
    return score


def generate_report(df, all_issues, output_dir="."):
    """Generate JSON + CSV quality report."""
    total    = len(df)
    high     = sum(1 for i in all_issues if i["severity"] == "HIGH")
    medium   = sum(1 for i in all_issues if i["severity"] == "MEDIUM")
    low      = sum(1 for i in all_issues if i["severity"] == "LOW")
    score    = calculate_quality_score(total, len(all_issues), high, medium, low)

    # Label distribution
    label_dist = df[LABEL_COLUMN].value_counts().to_dict()

    for issue in all_issues:
        for k, v in issue.items():
            if hasattr(v, 'item'):
                issue[k] = v.item()

    summary = {
        "generated_at":       datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_records":      total,
        "total_issues_found": len(all_issues),
        "quality_score":      f"{score}/100",
        "severity_breakdown": {"HIGH": high, "MEDIUM": medium, "LOW": low},
        "label_distribution": {str(k): int(v) for k, v in label_dist.items()},
        "issues": all_issues
    }

    # Save JSON report
    json_path = os.path.join(output_dir, "quality_report.json")
    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2)

    # Save CSV report
    csv_path = os.path.join(output_dir, "quality_report.csv")
    if all_issues:
        pd.DataFrame(all_issues).to_csv(csv_path, index=False)
    else:
        pd.DataFrame(columns=["row","id","issue","severity","value"]).to_csv(csv_path, index=False)

    return summary, json_path, csv_path


def print_summary(summary):
    """Print a clean summary to the terminal."""
    print("\n" + "="*55)
    print("       ANNOTATION DATASET QUALITY REPORT")
    print("="*55)
    print(f"  Generated At   : {summary['generated_at']}")
    print(f"  Total Records  : {summary['total_records']}")
    print(f"  Issues Found   : {summary['total_issues_found']}")
    print(f"  Quality Score  : {summary['quality_score']}")
    print("-"*55)
    print(f"  HIGH  severity : {summary['severity_breakdown']['HIGH']}")
    print(f"  MEDIUM severity: {summary['severity_breakdown']['MEDIUM']}")
    print(f"  LOW   severity : {summary['severity_breakdown']['LOW']}")
    print("-"*55)
    print("  Label Distribution:")
    for lbl, count in summary["label_distribution"].items():
        print(f"    {lbl:<15} : {count}")
    print("="*55)
    if summary["total_issues_found"] == 0:
        print("  ✅  No issues found! Dataset is clean.")
    else:
        print("  ⚠️   Issues detected. Check quality_report.csv")
    print("="*55 + "\n")


def run(filepath):
    df = load_data(filepath)

    # Validate required columns
    for col in [ID_COLUMN, TEXT_COLUMN, LABEL_COLUMN]:
        if col not in df.columns:
            print(f"[ERROR] Column '{col}' not found. Please check your CSV headers.")
            sys.exit(1)

    print("[•] Running quality checks...")
    all_issues = []
    all_issues += check_missing_values(df)
    all_issues += check_duplicate_rows(df)
    all_issues += check_invalid_labels(df)
    all_issues += check_inconsistent_labels(df)
    all_issues += check_short_text(df)

    summary, json_path, csv_path = generate_report(df, all_issues)
    print_summary(summary)
    print(f"[✓] JSON report saved → {json_path}")
    print(f"[✓] CSV  report saved → {csv_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python checker.py <path_to_annotation_file.csv>")
        print("Example: python checker.py sample_annotations.csv")
        sys.exit(1)
    run(sys.argv[1])
