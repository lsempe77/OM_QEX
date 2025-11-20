# om_qex_extraction/src/eval_qex_against_gt.py

"""
Evaluate QEX inventories against GT annotations.

Reads:  data/qex_mvp/GT_QEX_ABM_TEEP_seed.xlsx

Outputs:
- Per-study / per-table GT coverage:
    * n_rows
    * n_valid (gt_is_valid = 1)
    * n_preferred (gt_is_preferred_spec = 1)
    * n_missing_n_total (n_total is NaN in QEX)
    * n_rows_with_numeric_gt (any of gt_estimate/gt_se/gt_n_total non-null)
- List of rows where gt_notes contains 'MISSING'
- Spec-selection evaluation (classification metrics):
    * Overall accuracy
    * Precision, recall, F1 for "preferred spec" (gt_is_preferred_spec == 1)
    * Per-study / per-table accuracy
- N-total accuracy vs GT:
    * match / missing / disagree counts (overall + per table)
- Estimate & SE accuracy vs GT:
    * match / missing / disagree counts
    * MAE, RMSE, Pearson r (where both model + GT present)

Row-recall metrics become more meaningful once synthetic GT rows for
missing conceptual rows are added.
"""

from pathlib import Path
from typing import List

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------
# Loading GT
# ---------------------------------------------------------------------


def load_gt_excel(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"GT Excel not found at: {path}")

    df = pd.read_excel(path)

    # Sanity check on required columns
    required_cols: List[str] = [
        "study_id",
        "analysis_id",
        "table_id",
        "row_id",
        "gt_is_valid",
        "gt_is_preferred_spec",
        "gt_notes",
        "estimate",
        "se",
        "n_total",
        "gt_estimate",
        "gt_se",
        "gt_n_total",
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise SystemExit(f"GT Excel is missing required columns: {missing}")

    # Ensure GT flags are numeric so sums/means behave
    for col in ["gt_is_valid", "gt_is_preferred_spec"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Coerce numeric columns to floats
    for col in ["estimate", "se", "n_total", "gt_estimate", "gt_se", "gt_n_total"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


# ---------------------------------------------------------------------
# Coverage summaries
# ---------------------------------------------------------------------


def summarize_by_study_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Produce per-study / per-table summary with basic GT coverage and
    numeric GT indicators.
    """
    df = df.copy()

    # Boolean flag: do we have any numeric GT for this row?
    df["has_numeric_gt"] = df[["gt_estimate", "gt_se", "gt_n_total"]].notna().any(
        axis=1
    )

    summary = (
        df.groupby(["study_id", "table_id"], dropna=False)
        .agg(
            n_rows=("analysis_id", "size"),
            n_valid=("gt_is_valid", "sum"),
            n_preferred=("gt_is_preferred_spec", "sum"),
            n_missing_n_total=("n_total", lambda s: s.isna().sum()),
            n_rows_with_numeric_gt=("has_numeric_gt", "sum"),
        )
        .reset_index()
        .sort_values(["study_id", "table_id"])
    )

    return summary


def list_missing_notes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return rows where gt_notes contains 'MISSING' (case-insensitive).
    These are typically:
      - missing conceptual rows in the table
      - missing Ns in the original PDF
      - any other anomalies you flagged manually.
    """
    notes = df["gt_notes"].fillna("").astype(str)
    mask = notes.str.contains("MISSING", case=False)
    missing_df = df.loc[
        mask, ["study_id", "table_id", "row_id", "analysis_id", "gt_notes"]
    ].sort_values(["study_id", "table_id", "row_id", "analysis_id"])
    return missing_df

# ---------------------------------------------------------------------
# Row recall evaluation
# ---------------------------------------------------------------------

def evaluate_row_recall(df: pd.DataFrame) -> None:
    """
    Evaluate row-level recall: among all conceptual GT rows (gt_is_valid == 1),
    what fraction have *any* numeric QEX output (estimate, se, or n_total)?

    This treats:
      - Denominator: conceptual rows (gt_is_valid == 1)
      - Numerator: conceptual rows where at least one of
        {estimate, se, n_total} is non-null.

    This will naturally count your synthetic 'MISSING ROW ...' entries
    as uncovered (recall failures).
    """
    df = df.copy()
    conceptual = df[df["gt_is_valid"] == 1].copy()

    print("\n=== Row recall (conceptual rows) ===")
    if conceptual.empty:
        print("No rows with gt_is_valid==1; nothing to evaluate.")
        return

    # Has QEX output?
    conceptual["has_any_model"] = conceptual[["estimate", "se", "n_total"]].notna().any(axis=1)

    n_conceptual = len(conceptual)
    n_covered = int(conceptual["has_any_model"].sum())
    overall_recall = n_covered / n_conceptual if n_conceptual > 0 else float("nan")

    print(f"Total conceptual rows (gt_is_valid==1): {n_conceptual}")
    print(f"  covered by QEX (any estimate/se/n_total): {n_covered}")
    print(f"  overall row recall: {overall_recall:.3f}")

    # Per-study / per-table breakdown
    per_table = (
        conceptual.groupby(["study_id", "table_id"])
        .agg(
            n_conceptual=("analysis_id", "size"),
            n_covered=("has_any_model", "sum"),
        )
        .reset_index()
        .sort_values(["study_id", "table_id"])
    )
    per_table["row_recall"] = (
        per_table["n_covered"] / per_table["n_conceptual"]
    )

    print("\nPer-study / per-table row recall:")
    for _, row in per_table.iterrows():
        print(
            f"- {row['study_id']} / {row['table_id']}: "
            f"n_conceptual={int(row['n_conceptual'])}, "
            f"n_covered={int(row['n_covered'])}, "
            f"row_recall={row['row_recall']:.3f}"
        )

    # Optional: list conceptual rows with no QEX numeric output
    missing = conceptual.loc[
        ~conceptual["has_any_model"],
        ["study_id", "table_id", "row_id", "analysis_id", "gt_notes"],
    ].sort_values(["study_id", "table_id", "row_id", "analysis_id"])

    print("\nConceptual rows with NO QEX numeric output:")
    if missing.empty:
        print("(none)")
    else:
        for _, row in missing.iterrows():
            print(
                f"- {row['study_id']} / {row['table_id']} / {row['row_id']}\n"
                f"    analysis_id: {row['analysis_id']}\n"
                f"    gt_notes   : {row['gt_notes']}"
            )


# ---------------------------------------------------------------------
# Spec-selection heuristic vs GT
# ---------------------------------------------------------------------


def add_spec_prediction(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a column 'pred_is_preferred_spec' based on a simple heuristic:

    - For ABM3E3ZP:
        If gt_is_valid == 1 and estimator == "IV" -> predicted preferred (1)
        Else -> 0

    - For TEEP_Malawi:
        If gt_is_valid == 1 and arm_label != "Project" -> predicted preferred (1)
        If arm_label == "Project" -> predicted non-preferred (0)

    For any other study_ids (future), default = 0 for now.
    """
    df = df.copy()

    def _predict(row: pd.Series) -> int:
        study = row.get("study_id")
        valid = row.get("gt_is_valid", 0) == 1

        if not valid:
            return 0

        if study == "ABM3E3ZP":
            # Prefer IV over RE (or anything else)
            return 1 if row.get("estimator") == "IV" else 0

        if study == "TEEP_Malawi":
            arm = str(row.get("arm_label") or "").strip()
            # Prefer arm-level specs, not the aggregate "Project"
            if arm == "Project":
                return 0
            return 1

        # Default for other studies (if/when they appear)
        return 0

    df["pred_is_preferred_spec"] = df.apply(_predict, axis=1)
    return df


def evaluate_spec_selection(df: pd.DataFrame) -> None:
    """
    Compare the heuristic spec-selection ('pred_is_preferred_spec') to GT
    ('gt_is_preferred_spec'), overall and by study/table, only on rows
    where gt_is_valid == 1.

    Reports:
      - overall accuracy
      - precision/recall/F1 for preferred spec (positive class)
      - per-study / per-table accuracy
      - (if any) rows where heuristic disagrees with GT
    """
    df = df.copy()
    df = add_spec_prediction(df)

    # Only evaluate on rows you marked as valid and with GT preferred flag
    mask_eval = (
        (df["gt_is_valid"] == 1)
        & df["gt_is_preferred_spec"].isin([0, 1])
        & df["estimator"].notna()    # <--- add this line
    )

    print("\n=== Spec-selection evaluation ===")
    if not mask_eval.any():
        print("No rows with gt_is_valid==1 and gt_is_preferred_spec in {0,1}.")
        return

    eval_df = df.loc[mask_eval].copy()
    eval_df["correct"] = (
        eval_df["pred_is_preferred_spec"] == eval_df["gt_is_preferred_spec"]
    )

    # Overall accuracy
    overall_acc = eval_df["correct"].mean()

    # Classification metrics for "preferred spec" as positive class
    gt = eval_df["gt_is_preferred_spec"].astype(int)
    pred = eval_df["pred_is_preferred_spec"].astype(int)

    tp = int(((gt == 1) & (pred == 1)).sum())
    fp = int(((gt == 0) & (pred == 1)).sum())
    fn = int(((gt == 1) & (pred == 0)).sum())
    tn = int(((gt == 0) & (pred == 0)).sum())

    precision = tp / (tp + fp) if (tp + fp) > 0 else np.nan
    recall = tp / (tp + fn) if (tp + fn) > 0 else np.nan
    if np.isnan(precision) or np.isnan(recall) or precision + recall == 0:
        f1 = np.nan
    else:
        f1 = 2 * precision * recall / (precision + recall)

    print(f"Overall accuracy (on valid rows): {overall_acc:.3f}")
    print(f"Evaluated rows: {len(eval_df)}")
    print(f"  TP={tp}, FP={fp}, FN={fn}, TN={tn}")
    print(f"  Precision (preferred=1): {precision:.3f}" if not np.isnan(precision) else "  Precision (preferred=1): NA")
    print(f"  Recall    (preferred=1): {recall:.3f}" if not np.isnan(recall) else "  Recall    (preferred=1): NA")
    print(f"  F1        (preferred=1): {f1:.3f}" if not np.isnan(f1) else "  F1        (preferred=1): NA")

    # Per-study / per-table accuracy
    per_table = (
        eval_df.groupby(["study_id", "table_id"])
        .agg(
            n_rows=("analysis_id", "size"),
            accuracy=("correct", "mean"),
        )
        .reset_index()
        .sort_values(["study_id", "table_id"])
    )

    print("\nPer-study / per-table spec-selection accuracy:")
    for _, row in per_table.iterrows():
        print(
            f"- {row['study_id']} / {row['table_id']}: "
            f"n_rows={int(row['n_rows'])}, "
            f"accuracy={row['accuracy']:.3f}"
        )

    # Show mismatches, if any
    mismatches = eval_df.loc[
        ~eval_df["correct"],
        [
            "study_id",
            "table_id",
            "row_id",
            "analysis_id",
            "estimator",
            "arm_label",
            "gt_is_preferred_spec",
            "pred_is_preferred_spec",
            "gt_notes",
        ],
    ].sort_values(["study_id", "table_id", "row_id", "analysis_id"])

    if mismatches.empty:
        print("\nNo mismatches: heuristic matches GT on all evaluated rows.")
    else:
        print("\nRows where heuristic disagrees with GT:")
        for _, row in mismatches.iterrows():
            print(
                f"- {row['study_id']} / {row['table_id']} / {row['row_id']}\n"
                f"    analysis_id         : {row['analysis_id']}\n"
                f"    estimator           : {row['estimator']}\n"
                f"    arm_label           : {row['arm_label']}\n"
                f"    gt_is_preferred_spec: {row['gt_is_preferred_spec']}\n"
                f"    pred_is_preferred   : {row['pred_is_preferred_spec']}\n"
                f"    gt_notes            : {row['gt_notes']}"
            )


# ---------------------------------------------------------------------
# N-total accuracy
# ---------------------------------------------------------------------


def evaluate_n_accuracy(df: pd.DataFrame) -> None:
    """
    Evaluate how well QEX captured n_total where GT n_total is known.

    Categories (only on rows with non-null gt_n_total):
      - match: n_total == gt_n_total
      - missing: n_total is NaN but gt_n_total present
      - disagree: both present but not equal
    """
    df = df.copy()

    mask_gt_n = df["gt_n_total"].notna()
    subset = df.loc[mask_gt_n].copy()

    print("\n=== N-total accuracy (rows with gt_n_total filled) ===")
    if subset.empty:
        print("No rows have gt_n_total; nothing to evaluate.")
        return

    subset["has_qex_n"] = subset["n_total"].notna()
    subset["n_match"] = subset["has_qex_n"] & (subset["n_total"] == subset["gt_n_total"])
    subset["n_missing"] = ~subset["has_qex_n"]
    subset["n_disagree"] = subset["has_qex_n"] & ~subset["n_match"]

    n_rows = len(subset)
    n_match = subset["n_match"].sum()
    n_missing = subset["n_missing"].sum()
    n_disagree = subset["n_disagree"].sum()

    print(f"Total rows with gt_n_total: {n_rows}")
    print(f"  match    : {int(n_match)}")
    print(f"  missing  : {int(n_missing)}")
    print(f"  disagree : {int(n_disagree)}")

    # Per-study / per-table
    per_table = (
        subset.groupby(["study_id", "table_id"])
        .agg(
            n_rows=("analysis_id", "size"),
            n_match=("n_match", "sum"),
            n_missing=("n_missing", "sum"),
            n_disagree=("n_disagree", "sum"),
        )
        .reset_index()
        .sort_values(["study_id", "table_id"])
    )

    print("\nPer-study / per-table N-total status:")
    for _, row in per_table.iterrows():
        print(
            f"- {row['study_id']} / {row['table_id']}: "
            f"n_rows={int(row['n_rows'])}, "
            f"match={int(row['n_match'])}, "
            f"missing={int(row['n_missing'])}, "
            f"disagree={int(row['n_disagree'])}"
        )


# ---------------------------------------------------------------------
# Numeric accuracy for estimates / SEs
# ---------------------------------------------------------------------


def evaluate_numeric_accuracy(
    df: pd.DataFrame,
    model_col: str,
    gt_col: str,
    label: str,
    tol: float = 1e-6,
) -> None:
    """
    Evaluate how well QEX captured a numeric column (estimate or se)
    where GT values are known.

    Only considers rows with non-null GT in `gt_col`.

    Categories:
      - match: model_col and gt_col both present, abs(diff) <= tol
      - missing: model_col is NaN but gt_col present
      - disagree: both present but abs(diff) > tol

    Also reports MAE, RMSE, and Pearson r on rows where both model and GT
    are present (regardless of 'match' threshold).
    """
    df = df.copy()
    mask_gt = df[gt_col].notna()
    subset = df.loc[mask_gt].copy()

    print(f"\n=== {label} accuracy (rows with {gt_col} filled) ===")
    if subset.empty:
        print(f"No rows have {gt_col}; nothing to evaluate.")
        return

    subset["has_model"] = subset[model_col].notna()
    subset["match"] = subset["has_model"] & (
        (subset[model_col] - subset[gt_col]).abs() <= tol
    )
    subset["missing"] = ~subset["has_model"]
    subset["disagree"] = subset["has_model"] & ~subset["match"]

    n_rows = len(subset)
    n_match = subset["match"].sum()
    n_missing = subset["missing"].sum()
    n_disagree = subset["disagree"].sum()

    print(f"Total rows with {gt_col}: {n_rows}")
    print(f"  match    : {int(n_match)}")
    print(f"  missing  : {int(n_missing)}")
    print(f"  disagree : {int(n_disagree)}")

    # Per-study / per-table breakdown
    per_table = (
        subset.groupby(["study_id", "table_id"])
        .agg(
            n_rows=("analysis_id", "size"),
            n_match=("match", "sum"),
            n_missing=("missing", "sum"),
            n_disagree=("disagree", "sum"),
        )
        .reset_index()
        .sort_values(["study_id", "table_id"])
    )

    print(f"\nPer-study / per-table {label} status:")
    for _, row in per_table.iterrows():
        print(
            f"- {row['study_id']} / {row['table_id']}: "
            f"n_rows={int(row['n_rows'])}, "
            f"match={int(row['n_match'])}, "
            f"missing={int(row['n_missing'])}, "
            f"disagree={int(row['n_disagree'])}"
        )

    # Error metrics only on rows where both model and GT are present
    both_mask = subset["has_model"]
    both = subset.loc[both_mask, [model_col, gt_col]]

    if both.empty:
        print(f"\nNo rows with both model and GT for {label}; cannot compute MAE/RMSE/r.")
        return

    diffs = both[model_col] - both[gt_col]
    mae = diffs.abs().mean()
    rmse = np.sqrt((diffs**2).mean())
    if len(both) > 1:
        r = np.corrcoef(both[model_col], both[gt_col])[0, 1]
    else:
        r = np.nan

    print(f"\n{label} error metrics (rows with both model and GT present):")
    print(f"  n_rows_both : {len(both)}")
    print(f"  MAE         : {mae:.6f}")
    print(f"  RMSE        : {rmse:.6f}")
    print(f"  Pearson r   : {r:.3f}" if not np.isnan(r) else "  Pearson r   : NA")

# ---------------------------------------------------------------------
# Show numeric mismatches
# ---------------------------------------------------------------------

def show_numeric_mismatches(
    df: pd.DataFrame,
    model_col: str,
    gt_col: str,
    label: str,
    tol: float = 1e-6,
) -> None:
    """
    Print rows where QEX numeric column and GT differ by more than `tol`.
    Only considers rows where GT is non-null and model_col is non-null.
    """
    df = df.copy()
    mask_gt = df[gt_col].notna()
    mask_model = df[model_col].notna()
    subset = df.loc[mask_gt & mask_model].copy()

    if subset.empty:
        print(f"\nNo rows with both GT and model for {label}; cannot show mismatches.")
        return

    subset["abs_diff"] = (subset[model_col] - subset[gt_col]).abs()
    mismatches = subset[subset["abs_diff"] > tol].sort_values(
        ["study_id", "table_id", "row_id", "analysis_id"]
    )

    print(f"\n=== {label} mismatches (|diff| > {tol}) ===")
    if mismatches.empty:
        print("(none)")
        return

    for _, row in mismatches.iterrows():
        print(
            f"- {row['study_id']} / {row['table_id']} / {row['row_id']}\n"
            f"    analysis_id : {row['analysis_id']}\n"
            f"    {label}_QEX : {row[model_col]}\n"
            f"    {label}_GT  : {row[gt_col]}\n"
            f"    abs_diff    : {row['abs_diff']}"
        )

# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------


def main():
    repo_root = Path(".").resolve()
    gt_path = repo_root / "data" / "qex_mvp" / "GT_QEX_ABM_TEEP_seed.xlsx"

    print(f"Loading GT from: {gt_path}")
    gt_df = load_gt_excel(gt_path)

    # --- Per-table summary ---
    summary = summarize_by_study_table(gt_df)

    print("\n=== Per-study / per-table GT coverage ===")
    for _, row in summary.iterrows():
        print(
            f"- {row['study_id']} / {row['table_id']}: "
            f"n_rows={row['n_rows']}, "
            f"n_valid={row['n_valid']}, "
            f"n_preferred={row['n_preferred']}, "
            f"n_missing_n_total={row['n_missing_n_total']}, "
            f"n_rows_with_numeric_gt={row['n_rows_with_numeric_gt']}"
        )

    # --- Rows you flagged as missing / problematic in gt_notes ---
    missing_df = list_missing_notes(gt_df)

    print("\n=== Rows flagged as MISSING in gt_notes ===")
    if missing_df.empty:
        print("(none)")
    else:
        for _, row in missing_df.iterrows():
            print(
                f"- {row['study_id']} / {row['table_id']} / {row['row_id']}\n"
                f"    analysis_id: {row['analysis_id']}\n"
                f"    gt_notes   : {row['gt_notes']}"
            )

    # --- Spec-selection evaluation vs GT ---
    evaluate_spec_selection(gt_df)

    # --- Row recall (conceptual rows) ---
    evaluate_row_recall(gt_df)

    # --- N-total accuracy vs GT ---
    evaluate_n_accuracy(gt_df)

    # --- Estimate and SE accuracy vs GT ---
    evaluate_numeric_accuracy(
        gt_df, model_col="estimate", gt_col="gt_estimate", label="Estimate"
    )
    evaluate_numeric_accuracy(
        gt_df, model_col="se", gt_col="gt_se", label="SE"
    )
    # Show which rows actually disagree on estimate / SE
    show_numeric_mismatches(
        gt_df, model_col="estimate", gt_col="gt_estimate", label="Estimate"
    )
    show_numeric_mismatches(
        gt_df, model_col="se", gt_col="gt_se", label="SE"
    )

    print("\nDone.")


if __name__ == "__main__":
    main()
