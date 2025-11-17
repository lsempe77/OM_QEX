import json
from pathlib import Path

import pandas as pd

from .table_normalizer import normalize_abm_income_table_t7
from .qex_inventory_builder import build_qex_inventory_from_normalized_table


def main():
    csv_path = Path("data/pdf/camelot_mvp_out/ABM_SOF_2019_stream_table26.csv")
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found at: {csv_path}")

    df = pd.read_csv(csv_path, header=None)

    # Step 1: normalize the regression table
    normalized = normalize_abm_income_table_t7(df)

    # Step 2: build a QEX analysis inventory from this table
    inventory = build_qex_inventory_from_normalized_table(
        normalized_table=normalized,
        om_outcome_id=None,          # e.g., "income_daily_pc" later
        outcome_family="income",
    )

    print(json.dumps(inventory, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
