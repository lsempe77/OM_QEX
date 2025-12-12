#!/usr/bin/env python3
"""
Study-level evaluation of AUTO vs GT Quant Extraction data.

Usage:
  python3 src/evaluate_study_level_auto_vs_gt.py \
    --auto-csv outputs/quant_extraction_form_AUTO_pilot_with_ids.csv \
    --gt-csv data/human_extraction/quant_extraction_form_GT.csv
"""

import argparse
from pathlib import Path
import pandas as pd
import numpy as np


# Columns for the 7 graduation components in the Quant Extraction Form
COMPONENT_COLS = [
    "Consumption support (cash or in-kind) to stabilize food security and prevent households from selling assets to survive ",
    "Healthcare provision to address the basic health needs of individuals and households",
    "Assets transfer (often livestock, tools, or seed capital) to provide a foundation for an income-generation activity.",
    "Skills training to enable participants to productively manage and grow their assets.",
    "Savings facilitation (e.g., savings accounts or linkages to microfinance institutions) to foster financial discipline and resilience.",
    "Coaching and mentoring to offer continuous motivation and goal-setting support.",
    "Social empowerment and linkages to social protection, markets, and public services to encourage opportunities and inclusion in existing systems.",
]

TIMING_COLS = [
    "Length of follow up",
    "Exposure to intervention",
]

DESIGN_COL = "Evaluation Design"

STUDY_KEY_AUTO = "StudyID_GT"   # numeric StudyID from metadata in AUTO file
STUDY_KEY_GT = "StudyID"        # StudyID column in GT file

def compute_categorical_accuracy(df: pd.DataFrame, auto_col: str, gt_col: str) -> float:
    """
    Compute exact-match accuracy for categorical/binary fields
    at the study level.
    """
    a = pd.to_numeric(df[auto_col], errors="coerce")
    g = pd.to_numeric(df[gt_col], errors="coerce")

    mask_valid = ~a.isna() & ~g.isna()
    if mask_valid.sum() == 0:
        return float("nan")

    acc = (a[mask_valid] == g[mask_valid]).mean()
    return float(acc)

def compute_timing_accuracy(
    df: pd.DataFrame, auto_col: str, gt_col: str
) -> tuple[float, float]:
    """
    Compute exact-match and ±1-month accuracy for timing fields.

    Returns:
        (accuracy_exact, accuracy_within_1_month)
    """
    a = pd.to_numeric(df[auto_col], errors="coerce")
    g = pd.to_numeric(df[gt_col], errors="coerce")

    mask_valid = ~a.isna() & ~g.isna()
    if mask_valid.sum() == 0:
        return float("nan"), float("nan")

    diff = (a - g).abs()
    acc_exact = (diff[mask_valid] == 0).mean()
    acc_tol1 = (diff[mask_valid] <= 1).mean()

    return float(acc_exact), float(acc_tol1)

def collapse_study_level(df: pd.DataFrame, key_col: str, cols: list) -> pd.DataFrame:
    """
    For each StudyID, collapse potentially multiple rows down to a single
    representative value per column (first non-missing).
    """
    def first_nonmissing(s: pd.Series):
        s2 = s.dropna()
        return s2.iloc[0] if len(s2) > 0 else np.nan

    out = (
        df.groupby(key_col)[cols]
        .agg(first_nonmissing)
        .reset_index()
    )
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--auto-csv",
        type=str,
        required=True,
        help="AUTO Quant Extraction CSV with StudyID_GT column",
    )
    parser.add_argument(
        "--gt-csv",
        type=str,
        required=True,
        help="GT Quant Extraction CSV (human-coded)",
    )
    args = parser.parse_args()

    # ---- Read AUTO ----
    auto = pd.read_csv(args.auto_csv)

    # ---- Read GT (handle non-UTF8) ----
    try:
        gt = pd.read_csv(args.gt_csv)
    except UnicodeDecodeError:
        print("UTF-8 decoding failed for GT CSV, retrying with latin1 encoding...")
        gt = pd.read_csv(args.gt_csv, encoding="latin1")

    # ---- Sanity: ensure key columns exist ----
    if STUDY_KEY_AUTO not in auto.columns:
        raise SystemExit(f"AUTO file missing '{STUDY_KEY_AUTO}' column.")
    if STUDY_KEY_GT not in gt.columns:
        raise SystemExit(f"GT file missing '{STUDY_KEY_GT}' column.")

    # ------------------------------------------------------------------
    # 1) NORMALISE STUDY IDS → StudyID_eval (numeric) ON BOTH SIDES
    # ------------------------------------------------------------------
    # AUTO: use StudyID_GT as the evaluation StudyID
    auto["StudyID_eval"] = (
        pd.to_numeric(auto[STUDY_KEY_AUTO], errors="coerce")
        .astype("Int64")
    )

    # GT: use StudyID (human-coded file)
    gt["StudyID_eval"] = (
        pd.to_numeric(gt[STUDY_KEY_GT], errors="coerce")
        .astype("Int64")
    )

    # Drop rows where we failed to get a numeric StudyID
    auto = auto[auto["StudyID_eval"].notna()].copy()
    gt = gt[gt["StudyID_eval"].notna()].copy()

    # Optional debugging / sanity check
    auto_ids = sorted(auto["StudyID_eval"].dropna().unique())
    gt_ids = sorted(gt["StudyID_eval"].dropna().unique())
    overlap_ids = sorted(set(auto_ids) & set(gt_ids))

    print("\nAUTO StudyID_eval (unique):", auto_ids)
    print("GT StudyID_eval (unique, first 30):", gt_ids[:30])
    print("Overlapping StudyID_eval values:", overlap_ids)

    # ---- Subset to the fields we care about ----
    all_cols_needed = COMPONENT_COLS + TIMING_COLS + [DESIGN_COL]

    missing_auto = [c for c in all_cols_needed if c not in auto.columns]
    missing_gt = [c for c in all_cols_needed if c not in gt.columns]

    if missing_auto:
        print("WARNING: Missing columns in AUTO:", missing_auto)
    if missing_gt:
        print("WARNING: Missing columns in GT:", missing_gt)

    # Only keep columns that exist in both for evaluation
    eval_cols = [c for c in all_cols_needed if c in auto.columns and c in gt.columns]
    print("Evaluating study-level fields:", eval_cols)

    # ------------------------------------------------------------------
    # 2) COLLAPSE TO STUDY LEVEL USING THE NORMALISED ID
    # ------------------------------------------------------------------
    auto_study = collapse_study_level(auto, "StudyID_eval", eval_cols)
    gt_study = collapse_study_level(gt, "StudyID_eval", eval_cols)

    # Standardise the key column name for merging
    auto_study = auto_study.rename(columns={"StudyID_eval": "StudyID"})
    gt_study = gt_study.rename(columns={"StudyID_eval": "StudyID"})

    # ------------------------------------------------------------------
    # 3) Restrict to overlapping studies and MERGE
    # ------------------------------------------------------------------
    common_ids = sorted(set(auto_study["StudyID"]).intersection(gt_study["StudyID"]))
    auto_study = auto_study[auto_study["StudyID"].isin(common_ids)].reset_index(drop=True)
    gt_study = gt_study[gt_study["StudyID"].isin(common_ids)].reset_index(drop=True)

    print(f"Number of overlapping studies: {len(common_ids)}")

    merged = auto_study.merge(gt_study, on="StudyID", suffixes=("_AUTO", "_GT"))
    print(f"Merged study-level rows: {len(merged)}")

    if merged.empty:
        print("\nNo overlapping studies after merging on StudyID_eval. "
              "Check that your AUTO file really covers the same StudyIDs as GT.")
        return

    # ---- Compute accuracy stats ----
    rows = []
    for field in eval_cols:
        auto_col = f"{field}_AUTO"
        gt_col = f"{field}_GT"

        if field in TIMING_COLS:
            exact, within_1 = compute_timing_accuracy(merged, auto_col, gt_col)
            rows.append({
                "field": field,
                "n_studies": merged[[auto_col, gt_col]].dropna().shape[0],
                "accuracy_exact": exact,
                "accuracy_within_1_month": within_1,
            })
        else:
            acc = compute_categorical_accuracy(merged, auto_col, gt_col)
            rows.append({
                "field": field,
                "n_studies": merged[[auto_col, gt_col]].dropna().shape[0],
                "accuracy_exact": acc,
                "accuracy_within_1_month": float("nan"),
            })

    results = pd.DataFrame(rows)
    print("\n=== Study-level accuracy (AUTO vs GT) ===")
    print(results.to_string(index=False))

    # ---- Compute accuracy per component ----
    results = []

    # Components & design: exact match
    for col in COMPONENT_COLS + [DESIGN_COL]:
        if f"{col}_AUTO" not in merged.columns or f"{col}_GT" not in merged.columns:
            continue

        a = pd.to_numeric(merged[f"{col}_AUTO"], errors="coerce")
        g = pd.to_numeric(merged[f"{col}_GT"], errors="coerce")

        mask_valid = ~a.isna() & ~g.isna()
        if mask_valid.sum() == 0:
            acc = np.nan
        else:
            acc = (a[mask_valid] == g[mask_valid]).mean()

        results.append({
            "field": col,
            "n_studies": int(mask_valid.sum()),
            "accuracy_exact": float(acc) if not np.isnan(acc) else np.nan,
        })

    # Timing: exact and within ±1 month
    for col in TIMING_COLS:
        if f"{col}_AUTO" not in merged.columns or f"{col}_GT" not in merged.columns:
            continue

        a = pd.to_numeric(merged[f"{col}_AUTO"], errors="coerce")
        g = pd.to_numeric(merged[f"{col}_GT"], errors="coerce")

        mask_valid = ~a.isna() & ~g.isna()
        if mask_valid.sum() == 0:
            acc_exact = acc_tol1 = np.nan
        else:
            diff = (a - g).abs()
            acc_exact = (diff[mask_valid] == 0).mean()
            acc_tol1 = (diff[mask_valid] <= 1).mean()

        results.append({
            "field": col,
            "n_studies": int(mask_valid.sum()),
            "accuracy_exact": float(acc_exact) if not np.isnan(acc_exact) else np.nan,
            "accuracy_within_1_month": float(acc_tol1) if not np.isnan(acc_tol1) else np.nan,
        })

    res_df = pd.DataFrame(results)
    print("\n=== Study-level accuracy (AUTO vs GT) ===")
    print(res_df.to_string(index=False))

    # Optionally, write to CSV for your notes
    out_path = Path("outputs/eval_study_level_AUTO_vs_GT.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    res_df.to_csv(out_path, index=False)
    print(f"\nSaved study-level evaluation summary to: {out_path}")


if __name__ == "__main__":
    main()
