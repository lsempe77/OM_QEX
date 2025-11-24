#!/usr/bin/env python3
"""
Run the two-stage extraction pipeline for a list of GROBID keys.

For each key K:
- Calls run_twostage_extraction.py --keys K --output outputs/twostage/K
- So each study gets its own subdirectory with its OM and QEX outputs.

Usage:
    python3 run_batch_twostage.py study_keys_pilot.txt
"""

import argparse
import subprocess
from pathlib import Path


def run_for_key(key: str, output_root: Path) -> None:
    key = key.strip()
    if not key:
        return

    out_dir = output_root / key
    out_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 70)
    print(f"Running two-stage extraction for key: {key}")
    print(f"Output directory: {out_dir}")
    print("=" * 70)

    cmd = [
        "python3",
        "run_twostage_extraction.py",
        "--keys",
        key,
        "--output",
        str(out_dir),
    ]

    # Let run_twostage_extraction handle logging / errors
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"⚠️ Extraction failed for key {key} (return code {result.returncode})")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "keys_file",
        help="Text file with one GROBID key per line (e.g. study_keys_pilot.txt)",
    )
    parser.add_argument(
        "--output-root",
        default="outputs/twostage",
        help="Root directory for per-study outputs (default: outputs/twostage)",
    )
    args = parser.parse_args()

    keys_path = Path(args.keys_file)
    output_root = Path(args.output_root)

    if not keys_path.exists():
        raise FileNotFoundError(f"Keys file not found: {keys_path}")

    keys = [
        line.strip()
        for line in keys_path.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    print(f"Found {len(keys)} keys in {keys_path}:")
    for k in keys:
        print(f"  - {k}")

    output_root.mkdir(parents=True, exist_ok=True)

    for key in keys:
        run_for_key(key, output_root)


if __name__ == "__main__":
    main()
