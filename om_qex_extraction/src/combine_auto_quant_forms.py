#!/usr/bin/env python3
"""
Combine per-study Quant Extraction Forms into a single AUTO dataset.

Usage:
  python3 src/combine_auto_quant_forms.py \
    --input-dir outputs/hitl \
    --output-csv outputs/quant_extraction_form_AUTO_pilot.csv
"""

import argparse
from pathlib import Path
import pandas as pd


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-dir",
        type=str,
        default="outputs/hitl",
        help="Directory containing quant_extraction_form_<KEY>.csv files",
    )
    parser.add_argument(
        "--output-csv",
        type=str,
        default="outputs/quant_extraction_form_AUTO_pilot.csv",
        help="Path for combined AUTO CSV",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    files = sorted(input_dir.glob("quant_extraction_form_*.csv"))

    if not files:
        raise SystemExit(f"No quant_extraction_form_*.csv found in {input_dir}")

    dfs = []
    for f in files:
        key = f.stem.replace("quant_extraction_form_", "")
        df = pd.read_csv(f)
        # Track which GROBID/Zotero key this row came from
        df["_key"] = key
        dfs.append(df)

    combined = pd.concat(dfs, ignore_index=True)

    output_path = Path(args.output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(output_path, index=False)

    print(f"Combined {len(files)} files into: {output_path}")
    print(f"Total rows: {len(combined)}")
    print("Example keys:", combined["_key"].dropna().unique()[:10])


if __name__ == "__main__":
    main()
