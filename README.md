# Automated Data Quality Checker for Annotation Datasets

**Author:** Kolanka Bhavani Sankar  
**Tech Stack:** Python, Pandas, JSON, CSV

---

## What It Does

This tool automatically scans annotation datasets (CSV or JSON) for quality issues that commonly occur in AI/ML labelling workflows. It generates a detailed report with a quality score, helping data annotators and AI trainers catch errors before they enter model training pipelines.

## Issues Detected

| Check | Severity |
|---|---|
| Missing labels or text | HIGH |
| Invalid / unexpected labels | HIGH |
| Same text with conflicting labels | HIGH |
| Duplicate records | MEDIUM |
| Suspiciously short text entries | LOW |

## Output

- `quality_report.json` — Full structured report with all issues
- `quality_report.csv` — Spreadsheet-friendly issue list for review

## How to Run

### 1. Install requirements
```bash
pip install pandas
```

### 2. Run on your annotation file
```bash
python checker.py sample_annotations.csv
```

### 3. View the report
Open `quality_report.csv` in Excel or Google Sheets to review flagged records.

## Sample Output

```
=======================================================
       ANNOTATION DATASET QUALITY REPORT
=======================================================
  Generated At   : 2026-04-28 10:30:00
  Total Records  : 25
  Issues Found   : 7
  Quality Score  : 74/100
-------------------------------------------------------
  HIGH   severity : 4
  MEDIUM severity : 2
  LOW    severity : 1
=======================================================
```

## Configuration

Edit the top of `checker.py` to match your dataset:

```python
LABEL_COLUMN = "label"       # Your label column name
TEXT_COLUMN  = "text"        # Your text column name
ID_COLUMN    = "id"          # Your ID column name
VALID_LABELS = ["positive", "negative", "neutral"]  # Your expected labels
```

## Use Cases

- Pre-training data validation for LLMs
- Quality assurance in freelance annotation projects
- Compatible with exports from Labelbox, CVAT, and SuperAnnotate
