#!/usr/bin/env python3
"""
Add numeric StudyID (paper_id from fulltext_metadata.csv) to an AUTO Quant form.

Usage:
  python3 src/add_numeric_studyid_to_auto.py \
    --auto-csv outputs/quant_extraction_form_AUTO_pilot_GT.csv \
    --metadata-csv ../data/raw/fulltext_metadata.csv \
    --out-csv outputs/quant_extraction_form_AUTO_pilot_GT_with_ids.csv
"""

import argparse
from pathlib import Path
import pandas as pd
import numpy as np


def detect_auto_key_column(auto: pd.DataFrame) -> str:
    """
    Figure out which column in AUTO holds the GROBID/Zotero key.

    Priority:
      1. '_key'  (often like 'RSAW8CHM.tei')
      2. 'Key'
      3. 'StudyID' when it looks non-numeric (e.g., 'RSAW8CHM')
    """
    if "_key" in auto.columns:
        return "_key"
    if "Key" in auto.columns:
        return "Key"

    if "StudyID" in auto.columns:
        # If StudyID is mostly non-numeric, treat it as the key.
        s = auto["StudyID"].astype(str)
        numeric = pd.to_numeric(s, errors="coerce")
        frac_numeric = numeric.notna().mean()
        if frac_numeric < 0.5:
            # Mostly not numeric → very likely a Zotero key like 'RSAW8CHM'
            return "StudyID"

    raise SystemExit(
        "Could not detect a key column in AUTO. "
        "Looked for '_key', 'Key', or non-numeric 'StudyID'. "
        f"Available columns: {list(auto.columns)}"
    )


def normalise_key_series(s: pd.Series) -> pd.Series:
    """
    Normalise key strings so they match metadata 'Key' values:

      - strip whitespace
      - drop .tei / .xml / .tei.xml suffixes if present
    """
    s = s.astype(str).str.strip()

    # Remove common suffixes like '.tei', '.xml', '.tei.xml'
    for suff in [".tei.xml", ".tei", ".xml"]:
        s = s.str.replace(suff + "$", "", regex=True)

    return s


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--auto-csv",
        type=str,
        required=True,
        help="AUTO Quant Extraction CSV (combined)",
    )
    parser.add_argument(
        "--metadata-csv",
        type=str,
        required=True,
        help="fulltext_metadata CSV with Key <-> paper_id mapping",
    )
    parser.add_argument(
        "--out-csv",
        type=str,
        required=True,
        help="Output CSV with numeric StudyID_GT added",
    )
    args = parser.parse_args()

    auto_path = Path(args.auto_csv)
    meta_path = Path(args.metadata_csv)

    if not auto_path.exists():
        raise SystemExit(f"AUTO CSV not found: {auto_path}")
    if not meta_path.exists():
        raise SystemExit(f"Metadata CSV not found: {meta_path}")

    auto = pd.read_csv(auto_path)
    meta = pd.read_csv(meta_path)

    print(f"AUTO columns: {list(auto.columns)}")
    print(f"Metadata columns: {list(meta.columns)}")

    # 1) Detect key column on AUTO side
    auto_key_col = detect_auto_key_column(auto)
    print(f"Using '{auto_key_col}' in AUTO as the key to join on metadata.")

    # 2) Check metadata has 'Key' and some StudyID-like column
    if "Key" not in meta.columns:
        raise SystemExit(
            "Metadata CSV missing 'Key' column. "
            f"Available columns: {list(meta.columns)}"
        )

    # Prefer 'paper_id' as the numeric StudyID
    if "paper_id" in meta.columns:
        studyid_col_meta = "paper_id"
    else:
        # Fallbacks if ever needed
        for cand in ["StudyID", "study_id", "ID"]:
            if cand in meta.columns:
                studyid_col_meta = cand
                break
        else:
            raise SystemExit(
                "Metadata CSV missing a StudyID-like column "
                "(expected one of: 'paper_id', 'StudyID', 'study_id', 'ID')."
            )

    print(f"Using 'Key' in metadata as the key column and '{studyid_col_meta}' as StudyID source.")

    # 3) Build crosswalk Key -> StudyID
    crosswalk = meta[["Key", studyid_col_meta]].drop_duplicates()

    # Warn about duplicates and deduplicate
    dup_counts = crosswalk["Key"].value_counts()
    problem_keys = dup_counts[dup_counts > 1].index.tolist()
    if problem_keys:
        print("WARNING: The following Keys appear multiple times in metadata crosswalk:")
        for k in problem_keys:
            sub = crosswalk[crosswalk["Key"] == k]
            unique_ids = sub[studyid_col_meta].unique().tolist()
            print(f"  - Key={k} -> StudyIDs={unique_ids}")
        crosswalk = crosswalk.drop_duplicates(subset=["Key"], keep="first")
        print("Deduplicated crosswalk to one row per Key (keeping first occurrence).")

    assert crosswalk["Key"].is_unique, "Crosswalk Key still not unique after dedup."

    # 4) Normalise keys on AUTO side and merge
    auto["__key_for_join"] = normalise_key_series(auto[auto_key_col])
    crosswalk["Key_norm"] = normalise_key_series(crosswalk["Key"])

    merged = auto.merge(
        crosswalk[["Key_norm", studyid_col_meta]],
        left_on="__key_for_join",
        right_on="Key_norm",
        how="left",
        validate="many_to_one",
    )

    merged = merged.drop(columns=["__key_for_join", "Key_norm"])

    # 5) Create StudyID_GT from metadata StudyID column
    merged["StudyID_GT"] = merged[studyid_col_meta]

    # 5b) Create EstimateID_GT if EstimateID is present and has a numeric suffix.
    # GT EstimateID is formatted as '<StudyID>_<n>'. AUTO typically uses '<Key>_<n>'.
    # After mapping StudyID_GT, we can construct EstimateID_GT as '<StudyID_GT>_<n>'.
    if "EstimateID" in merged.columns:
        suffix = merged["EstimateID"].astype(str).str.split("_").str[-1]
        suffix = suffix.where(suffix.str.fullmatch(r"\d+"), np.nan)
        merged["EstimateID_GT"] = merged["StudyID_GT"].astype("Int64").astype(str) + "_" + suffix
        merged.loc[suffix.isna(), "EstimateID_GT"] = np.nan

    # Sanity: show unmatched keys (if any)
    unmatched = merged[merged["StudyID_GT"].isna()]
    if not unmatched.empty:
        keys_unmatched = sorted(unmatched[auto_key_col].dropna().unique())
        print("WARNING: Some AUTO rows did not match any metadata Key. Example keys:")
        for k in keys_unmatched[:20]:
            print(f"  - {k}")
    else:
        print("All AUTO rows matched to a StudyID in metadata.")

    # 6) Write out
    out_path = Path(args.out_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(out_path, index=False)

    print(f"Wrote AUTO+IDs file to: {out_path}")
    print("Columns now include 'StudyID_GT' alongside the original AUTO fields.")


if __name__ == "__main__":
    main()
