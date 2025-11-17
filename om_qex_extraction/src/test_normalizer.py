import json
from pathlib import Path

import pandas as pd

from .table_normalizer import normalize_abm_income_table_t7

df = pd.read_csv("data/pdf/camelot_mvp_out/ABM_SOF_2019_stream_table26.csv", header=None)
normalized = normalize_abm_income_table_t7(df)

import json
print(json.dumps(normalized, indent=2, ensure_ascii=False))