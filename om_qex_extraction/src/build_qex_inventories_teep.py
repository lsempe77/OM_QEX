import json
from pathlib import Path

import pandas as pd

from om_qex_extraction.src.table_normalizer import normalize_teep_nonfood_table16
from om_qex_extraction.src.qex_inventory_builder import build_qex_inventory_from_normalized_table


def main():
    # Where Camelot wrote the Malawi Table 16 CSVs
    base = Path("data/pdf/camelot_mvp_out_teep")
    header_df = pd.read_csv(base / "teep_table16_stream_0.csv", header=None)
    body_df = pd.read_csv(base / "teep_table16_stream_1.csv", header=None)

    # Step 1: normalize Table 16
    normalized = normalize_teep_nonfood_table16(header_df, body_df)

    # Step 2: build QEX inventory for this normalized table
    qex = build_qex_inventory_from_normalized_table(normalized)

    # Step 3: write it out
    out_path = Path("data/qex_mvp/TEEP_T16_nonfood_qex_inventory.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(qex, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote QEX inventory to {out_path}")


if __name__ == "__main__":
    main()
