import json
from pathlib import Path

import pandas as pd

from .table_normalizer import normalize_abm_income_table_t7
from .qex_inventory_builder import build_qex_inventory_from_normalized_table


def main():
    """
    Normalize all key ABM SOF IV/RE tables (6–11) and build QEX-style analysis inventories.
    Assumes Camelot 'stream' outputs already exist as CSVs, e.g.:

      data/pdf/camelot_mvp_out/ABM_SOF_2019_stream_table23.csv  -> Table 6 (assets)
      data/pdf/camelot_mvp_out/ABM_SOF_2019_stream_table26.csv  -> Table 7 (income)
      data/pdf/camelot_mvp_out/ABM_SOF_2019_stream_table30.csv  -> Table 8 (savings)
      data/pdf/camelot_mvp_out/ABM_SOF_2019_stream_table32.csv  -> Table 9 (expenditure)
      data/pdf/camelot_mvp_out/ABM_SOF_2019_stream_table36.csv  -> Table 10 (wellbeing)
      data/pdf/camelot_mvp_out/ABM_SOF_2019_stream_table38.csv  -> Table 11 (empowerment)
    """

    study_id = "ABM3E3ZP"

    base_dir = Path("data/pdf/camelot_mvp_out")

    # Map Camelot table index -> logical table_id + outcome family label
    TABLE_CONFIGS = [
        {"camelot_idx": 23, "table_id": "T6_assets",       "outcome_family": "assets"},
        {"camelot_idx": 26, "table_id": "T7_income",       "outcome_family": "income"},
        {"camelot_idx": 30, "table_id": "T8_savings",      "outcome_family": "savings"},
        {"camelot_idx": 32, "table_id": "T9_expenditure",  "outcome_family": "expenditure"},
        {"camelot_idx": 36, "table_id": "T10_wellbeing",   "outcome_family": "wellbeing"},
        {"camelot_idx": 38, "table_id": "T11_empowerment", "outcome_family": "empowerment"},
    ]

    inventories = []

    for cfg in TABLE_CONFIGS:
        idx = cfg["camelot_idx"]
        table_id = cfg["table_id"]
        family = cfg["outcome_family"]

        csv_path = base_dir / f"ABM_SOF_2019_stream_table{idx}.csv"
        if not csv_path.exists():
            print(f"[WARN] CSV not found for table index {idx}: {csv_path}")
            continue

        print(f"[INFO] Processing ABM table {table_id} from {csv_path}")

        df = pd.read_csv(csv_path, header=None)

        # Reuse the ABM IV/RE normalizer; the name says 'income' but logic is pattern-based.
        normalized = normalize_abm_income_table_t7(
            df=df,
            study_id=study_id,
            table_id=table_id,
        )

        inventory = build_qex_inventory_from_normalized_table(
            normalized_table=normalized,
            om_outcome_id=None,      # you'll fill this later once OM mapping is clear
            outcome_family=family,
        )

        inventories.append(inventory)

    # Write a combined JSON for this study
    out_dir = Path("data/qex_mvp")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{study_id}_qex_inventories.json"

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(inventories, f, indent=2, ensure_ascii=False)

    print(f"[INFO] Wrote {len(inventories)} QEX inventories to {out_path}")


if __name__ == "__main__":
    main()
