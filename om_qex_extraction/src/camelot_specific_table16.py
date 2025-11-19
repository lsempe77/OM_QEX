from pathlib import Path
import camelot


def main():
    # Adjust path if your PDF lives somewhere else
    pdf_path = Path("data/pdf/121294984.pdf")
    out_dir = Path("data/pdf/camelot_mvp_out_teep")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Use the actual page number where Table 16 lives
    # If your viewer says "page 45", use "45" here
    tables = camelot.read_pdf(str(pdf_path), pages="45", flavor="stream")

    print(f"Found {len(tables)} tables on page 45")
    for i, t in enumerate(tables):
        first_row = t.df.iloc[0].tolist()
        print(f"[stream] Table {i}: shape={t.df.shape}, first_row={first_row}")

        out_csv = out_dir / f"teep_table16_stream_{i}.csv"
        t.to_csv(out_csv, index=False, header=False)
        print(f"  -> {out_csv}")


if __name__ == "__main__":
    main()
