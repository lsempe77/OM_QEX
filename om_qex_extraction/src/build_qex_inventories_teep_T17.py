# om_qex_extraction/src/build_qex_inventories_teep_T17.py

import json
from pathlib import Path

import pandas as pd

from om_qex_extraction.src.table_normalizer import normalize_teep_consumption_poverty_table17
from om_qex_extraction.src.qex_inventory_builder import build_qex_inventory_from_normalized_table


def main():
    base = Path("data/pdf/camelot_mvp_out_teep")
    header_df = pd.read_csv(base / "teep_table17_stream_0.csv", header=None)
    body_df = pd.read_csv(base / "teep_table17_stream_1.csv", header=None)

    normalized = normalize_teep_consumption_poverty_table17(header_df, body_df)

    qex = build_qex_inventory_from_normalized_table(normalized)

    out_path = Path("data/qex_mvp/TEEP_T17_consumption_poverty_qex_inventory.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(qex, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote QEX inventory to {out_path}")


if __name__ == "__main__":
    main()
