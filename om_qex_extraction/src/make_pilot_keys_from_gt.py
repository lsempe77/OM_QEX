#!/usr/bin/env python3
"""
Construct a pilot list of study keys based on GT quant extraction and metadata.

It:
  - Reads the GT quant extraction form (human-coded),
  - Filters to studies with any timing info,
  - Joins to fulltext_metadata to get GROBID 'Key',
  - Selects up to N studies,
  - Writes a keys file: one Key per line.

Usage:
  python3 src/make_pilot_keys_from_gt.py \
    --gt-csv ../data/human_extraction/quant_extraction_form_GT.csv \
    --metadata-csv ../data/raw/fulltext_metadata.csv \
    --n-studies 11 \
    --out-keys ../data/human_extraction/study_keys_pilot_v2.txt
"""

import argparse
from pathlib import Path
import pandas as pd


def find_column(df: pd.DataFrame, candidates):
    lower_map = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]
    raise KeyError(f"None of {candidates} found in {df.columns.tolist()}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gt-csv", required=True, help="GT quant extraction CSV")
    parser.add_argument("--metadata-csv", required=True, help="fulltext_metadata CSV")
    parser.add_argument(
        "--n-studies",
        type=int,
        default=11,
        help="Number of pilot studies to select (max if fewer available)",
    )
    parser.add_argument(
        "--out-keys",
        required=True,
        help="Output text file with one GROBID Key per line",
    )
    args = parser.parse_args()

    gt = pd.read_csv(args.gt_csv, encoding="latin1")
    meta = pd.read_csv(args.metadata_csv)

    # Core column names
    studyid_col = find_column(gt, ["StudyID", "studyid", "study_id"])
    len_col = "Length of follow up"
    exp_col = "Exposure to intervention"

    # Filter to studies with *any* timing info (length OR exposure)
    timing_mask = (~gt[len_col].isna()) | (~gt[exp_col].isna())
    gt_timing = gt.loc[timing_mask, [studyid_col, len_col, exp_col]].copy()

    # Unique StudyIDs with timing
    study_ids = sorted(gt_timing[studyid_col].dropna().unique().tolist())
    print(f"GT has timing for {len(study_ids)} unique StudyIDs.")

    # Map StudyID -> Key using fulltext_metadata.csv
    key_col = find_column(meta, ["Key", "key", "ZoteroKey"])
    paper_id_col = find_column(meta, ["paper_id", "StudyID", "study_id", "ID"])

    meta_sub = meta[[key_col, paper_id_col]].drop_duplicates()

    crosswalk = meta_sub[meta_sub[paper_id_col].isin(study_ids)].copy()
    crosswalk = crosswalk.drop_duplicates(subset=[paper_id_col])

    print(f"Metadata has {len(crosswalk)} StudyIDs with GROBID keys.")

    # Select up to N studies deterministically (sorted by StudyID)
    crosswalk = crosswalk.sort_values(by=paper_id_col)
    n = min(args.n_studies, len(crosswalk))
    pilot = crosswalk.head(n)

    print("Selected pilot StudyIDs and Keys:")
    for _, row in pilot.iterrows():
        print(f"  StudyID={row[paper_id_col]}  Key={row[key_col]}")

    # Write keys file (one per line)
    out_path = Path(args.out_keys)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pilot[key_col].to_csv(out_path, index=False, header=False)

    print(f"Wrote pilot keys file with {n} keys to: {out_path}")


if __name__ == "__main__":
    main()
