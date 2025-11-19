import sys
from pathlib import Path

import camelot


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 -m om_qex_extraction.src.camelot_generic_mvp <pdf_path>")
        sys.exit(1)

    pdf_path = Path(sys.argv[0] if sys.argv[0].endswith(".pdf") else sys.argv[1])
    if not pdf_path.exists():
        print(f"[ERROR] PDF not found at: {pdf_path}")
        sys.exit(1)

    out_dir = Path("data/pdf/camelot_mvp_out") / pdf_path.stem
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== Camelot MVP on: {pdf_path} ===")

    # 1) Try stream on all pages
    print("\n--- Trying flavor='stream' on all pages ---")
    tables = camelot.read_pdf(str(pdf_path), pages="all", flavor="stream")

    print(f"[stream] Found {len(tables)} tables")
    for i, t in enumerate(tables):
        first_row = t.df.iloc[0].tolist()
        print(f"[stream] Table {i}: page={t.page}, shape={t.df.shape}, first_row={first_row}")

    # Export first few tables for inspection
    max_export = min(5, len(tables))
    print(f"[stream] Exporting up to first {max_export} tables to {out_dir}")
    for i in range(max_export):
        out_csv = out_dir / f"{pdf_path.stem}_stream_table{i}.csv"
        tables[i].to_csv(out_csv, index=False, header=False)
        print(f"[stream]   -> {out_csv}")


if __name__ == "__main__":
    main()