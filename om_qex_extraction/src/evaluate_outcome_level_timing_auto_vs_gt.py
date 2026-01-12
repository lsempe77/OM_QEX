#!/usr/bin/env python3
"""
Outcome-level timing evaluation of AUTO vs GT Quant Extraction data.

This evaluates timing fields at the estimate/outcome level (StudyID + EstimateID),
rather than collapsing to one row per study.

Key detail: GT uses numeric StudyID and EstimateID formatted like '<StudyID>_<n>'.
AUTO uses string StudyID keys and EstimateID like '<Key>_<n>' plus a StudyID_GT
crosswalk (numeric). We therefore derive EstimateID_GT as '<StudyID_GT>_<n>'.

Usage:
  python3 src/evaluate_outcome_level_timing_auto_vs_gt.py \
    --auto-csv outputs/quant_extraction_form_AUTO_pilot_with_ids.csv \
    --gt-csv data/human_extraction/quant_extraction_form_GT.csv \
    --out-csv outputs/eval_outcome_level_timing_AUTO_vs_GT.csv
"""

import argparse
from pathlib import Path
import pandas as pd
import numpy as np


TIMING_FIELDS = [
    "Exposure to intervention",
    "Length of follow up",
]


def read_csv_flexible(path: str) -> pd.DataFrame:
    """Read CSV with an encoding fallback (GT sometimes isn't UTF-8)."""
    p = Path(path)
    try:
        return pd.read_csv(p)
    except UnicodeDecodeError:
        return pd.read_csv(p, encoding="latin1")


def to_num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.astype(str).str.strip().replace({"": np.nan, "nan": np.nan}), errors="coerce")


def derive_estimateid_gt(auto: pd.DataFrame) -> pd.DataFrame:
    """Add EstimateID_GT if possible."""
    if "EstimateID_GT" in auto.columns:
        return auto

    if "StudyID_GT" not in auto.columns or "EstimateID" not in auto.columns:
        auto["EstimateID_GT"] = np.nan
        return auto

    # Suffix is whatever comes after the last underscore in EstimateID (typically an integer)
    suffix = auto["EstimateID"].astype(str).str.split("_").str[-1]
    # Keep only digit suffixes; else set missing
    suffix = suffix.where(suffix.str.fullmatch(r"\d+"), np.nan)

    auto["EstimateID_GT"] = auto["StudyID_GT"].astype("Int64").astype(str) + "_" + suffix
    auto.loc[suffix.isna(), "EstimateID_GT"] = np.nan
    return auto


def accuracy_exact(a: pd.Series, g: pd.Series) -> float:
    mask = a.notna() & g.notna()
    if mask.sum() == 0:
        return np.nan
    return float((a[mask] == g[mask]).mean())


def accuracy_within_1_month(a: pd.Series, g: pd.Series) -> float:
    mask = a.notna() & g.notna()
    if mask.sum() == 0:
        return np.nan
    return float((np.abs(a[mask] - g[mask]) <= 1).mean())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--auto-csv", required=True, help="AUTO Quant Extraction CSV with StudyID_GT column")
    ap.add_argument("--gt-csv", required=True, help="GT Quant Extraction CSV (human-coded)")
    ap.add_argument(
        "--out-csv",
        default="outputs/eval_outcome_level_timing_AUTO_vs_GT.csv",
        help="Output CSV path (default: outputs/eval_outcome_level_timing_AUTO_vs_GT.csv)",
    )
    args = ap.parse_args()

    auto = read_csv_flexible(args.auto_csv)
    gt = read_csv_flexible(args.gt_csv)

    auto = derive_estimateid_gt(auto)

    # Filter to rows where we can evaluate
    auto_eval = auto.dropna(subset=["StudyID_GT", "EstimateID_GT"]).copy()
    gt_eval = gt.dropna(subset=["StudyID", "EstimateID"]).copy()

    # Keep only overlapping EstimateID_GT
    merged = auto_eval.merge(
        gt_eval,
        left_on=["StudyID_GT", "EstimateID_GT"],
        right_on=["StudyID", "EstimateID"],
        how="inner",
        suffixes=("__AUTO", "__GT"),
        validate="one_to_one",
    )

    rows = []
    for f in TIMING_FIELDS:
        a = to_num(merged.get(f + "__AUTO", merged.get(f)))
        g = to_num(merged.get(f + "__GT", merged.get(f)))

        rows.append({
            "field": f,
            "n_estimates": int((a.notna() & g.notna()).sum()),
            "accuracy_exact": accuracy_exact(a, g),
            "accuracy_within_1_month": accuracy_within_1_month(a, g),
        })

    out = pd.DataFrame(rows)
    out_path = Path(args.out_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False)

    print("\nOutcome-level timing evaluation")
    print(out.to_string(index=False))
    print(f"\nWrote: {out_path}")


if __name__ == "__main__":
    main()
