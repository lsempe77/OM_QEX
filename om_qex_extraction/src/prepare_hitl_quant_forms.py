#!/usr/bin/env python3
"""
Prepare per-study Quant Extraction Form CSVs for HITL review.

For each key in the keys file:
- Reads outputs/twostage/<KEY>/stage2_qex/extracted_data.csv
- Calls build_quant_extraction_form.py to create outputs/hitl/quant_extraction_form_<KEY>.csv
- Ensures HITL columns exist: Coder name, HITL_reviewer, HITL_status, HITL_notes

Usage:
    python3 src/prepare_hitl_quant_forms.py \
        --keys-file study_keys_pilot.txt \
        --master-csv "../data/raw/Master file of included studies (n=114) 11 Nov(data).csv"
"""

import argparse
import subprocess
from pathlib import Path

import pandas as pd


def build_quant_for_key(
    key: str,
    output_root: Path,
    master_csv: Path,
    hitl_dir: Path,
) -> None:
    key = key.strip()
    if not key:
        return

    qex_csv = output_root / key / "stage2_qex" / "extracted_data.csv"
    if not qex_csv.exists():
        print(f"⚠️ QEX CSV not found for key {key}: {qex_csv}")
        return

    hitl_dir.mkdir(parents=True, exist_ok=True)
    out_csv = hitl_dir / f"quant_extraction_form_{key}.csv"

    print(f"\nBuilding Quant Extraction Form for {key}")
    print(f"  QEX CSV:   {qex_csv}")
    print(f"  Master:    {master_csv}")
    print(f"  Output:    {out_csv}")

    cmd = [
        "python3",
        "src/build_quant_extraction_form.py",
        "--qex-csv",
        str(qex_csv),
        "--master-csv",
        str(master_csv),
        "--out-csv",
        str(out_csv),
    ]

    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"⚠️ build_quant_extraction_form failed for {key}")
        return

    # Add HITL columns for RAs
    df = pd.read_csv(out_csv)

    # Ensure these columns exist
    for col in ["Coder name", "HITL_reviewer", "HITL_status", "HITL_notes"]:
        if col not in df.columns:
            df[col] = ""

    df.to_csv(out_csv, index=False)
    print(f"  ✓ Wrote HITL-ready file: {out_csv}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--keys-file",
        required=True,
        help="Text file with one GROBID key per line (same as used for batch extraction)",
    )
    parser.add_argument(
        "--output-root",
        default="outputs/twostage",
        help="Root directory where per-study outputs were written (default: outputs/twostage)",
    )
    parser.add_argument(
        "--master-csv",
        required=True,
        help="Path to the master included-studies file (for metadata)",
    )
    parser.add_argument(
        "--hitl-dir",
        default="outputs/hitl",
        help="Directory where per-study Quant Extraction Forms will be written",
    )
    args = parser.parse_args()

    keys_path = Path(args.keys_file)
    output_root = Path(args.output_root)
    master_csv = Path(args.master_csv)
    hitl_dir = Path(args.hitl_dir)

    if not keys_path.exists():
        raise FileNotFoundError(f"Keys file not found: {keys_path}")
    if not master_csv.exists():
        raise FileNotFoundError(f"Master CSV not found: {master_csv}")

    keys = [
        line.strip()
        for line in keys_path.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    print(f"Preparing HITL Quant Extraction Forms for {len(keys)} studies:")
    for k in keys:
        print(f"  - {k}")

    for key in keys:
        build_quant_for_key(key, output_root, master_csv, hitl_dir)


if __name__ == "__main__":
    main()
