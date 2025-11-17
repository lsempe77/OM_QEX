#!/usr/bin/env python3
import sys
from pathlib import Path

import camelot


def run_camelot(pdf_path: Path):
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found at: {pdf_path}")

    print(f"=== Camelot MVP on: {pdf_path} ===\n")

    flavor = "stream"
    print(f"--- Trying flavor='{flavor}' on all pages ---")
    try:
        tables = camelot.read_pdf(str(pdf_path), pages="all", flavor=flavor)
    except Exception as e:
        print(f"[{flavor}] ERROR: {e}")
        return

    print(f"[{flavor}] Found {tables.n} tables")

    for i, t in enumerate(tables):
        print(
            f"[{flavor}] Table {i}: page={t.page}, "
            f"shape={t.df.shape}, "
            f"first_row={list(t.df.iloc[0].astype(str))}"
        )

    if tables.n == 0:
        return

    out_dir = pdf_path.parent / "camelot_mvp_out"
    out_dir.mkdir(exist_ok=True)
    print(f"[{flavor}] Exporting selected tables to {out_dir}")

    # Hand-picked candidate regression tables by index for ABM
    # (from your log): 23, 26, 30, 32, 36, 38
    candidate_indices = [23, 26, 30, 32, 36, 38]

    for idx in candidate_indices:
        if idx >= tables.n:
            continue
        out_csv = out_dir / f"{pdf_path.stem}_{flavor}_table{idx}.csv"
        tables[idx].to_csv(out_csv)
        print(f"[{flavor}]   -> exported regression-like table {idx} to {out_csv}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/camelot_abm_mvp.py path/to/file.pdf")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    run_camelot(pdf_path)


if __name__ == "__main__":
    main()
