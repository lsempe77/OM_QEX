import json
from pathlib import Path

import pandas as pd

from om_qex_extraction.src.table_normalizer import normalize_teep_nonfood_table16

def main():
    base = Path("data/pdf/camelot_mvp_out_teep")  # adjust if needed
    header_path = base / "teep_table16_stream_0.csv"
    body_path = base / "teep_table16_stream_1.csv"

    header_df = pd.read_csv(header_path, header=None)
    body_df = pd.read_csv(body_path, header=None)

    normalized = normalize_teep_nonfood_table16(header_df, body_df)

    print(json.dumps(normalized, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
