from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import math
import pandas as pd


def _is_nan(x: Any) -> bool:
    """Return True if x is a float NaN."""
    return isinstance(x, float) and math.isnan(x)


def parse_numeric_string(s: Any) -> Optional[float]:
    """
    Parse a numeric string from the regression table into a float.

    Handles:
    - European decimals: '4,52*' -> 4.52
    - Dotted decimals:   '3.45***' -> 3.45
    - Values in parens:  '(4,96)' -> 4.96
    - Strips stars, percent signs, whitespace.

    Returns None if no reasonable numeric value can be parsed.
    """
    if s is None:
        return None
    if isinstance(s, float) and not math.isnan(s):
        return float(s)
    if not isinstance(s, str):
        return None

    s = s.strip()
    if not s:
        return None

    # Remove stars and spaces
    s_clean = s.replace("*", "").replace(" ", "")

    # Strip parentheses for SEs like "(4,96)"
    if s_clean.startswith("(") and s_clean.endswith(")"):
        s_clean = s_clean[1:-1]

    # Strip percent sign
    s_clean = s_clean.replace("%", "")

    # Handle decimal separators:
    # - If both ',' and '.', assume '.' are thousands separators and ',' is decimal.
    # - If only ',', treat ',' as decimal.
    # - Else, '.' is decimal or no decimal separator.
    if "," in s_clean and "." in s_clean:
        s_clean = s_clean.replace(".", "")
        s_clean = s_clean.replace(",", ".")
    elif "," in s_clean:
        s_clean = s_clean.replace(",", ".")

    try:
        return float(s_clean)
    except ValueError:
        return None


def normalize_abm_income_table_t7(
    df: pd.DataFrame,
    study_id: str = "ABM3E3ZP",
    table_id: str = "T7",
) -> Dict[str, Any]:
    """
    Normalize ABM Table 7 (Camelot 'stream' output, 7 columns) into a structured dict.

    Assumes a layout like:

      row 0: caption in col 1
      row 1: header row with 'IV' and 'ER'
      row 2: header row with 'Variables', 'Effect', 'SD of CG', 'Effects', 'SD of BL'
      rows 3..(n-3): blocks of:
          - 1 or 2 rows of variable label text in col 0 (first row has numeric values)
          - 1 row of SEs (values in parentheses) in numeric columns
      'Observations' row: 'Observations', N_IV, ..., N_RE, ...
      final row: note about standard errors and p-value stars

    Returns a dict with keys:
      - study_id
      - table_id
      - caption
      - estimators = ["IV", "RE"]
      - n = {"IV": n_iv, "RE": n_re}
      - header_rows = [header1, header2]
      - rows: list of {
          row_id,
          variable_label,
          raw_label_lines,
          effects: {
            "IV": {
              estimator_label,
              estimate_raw, estimate,
              se_raw, se,
              aux_label, aux_value_raw, aux_value
            },
            "RE": { ... }
          }
        }
      - notes
    """
    # Caption (row 0, col 1)
    cap = df.iloc[0, 1]
    caption = None if _is_nan(cap) else str(cap)

    # Header rows (we'll keep them for context + to label aux metrics)
    header1 = df.iloc[1].tolist()
    header2 = df.iloc[2].tolist()

    # For this table, header2 looks like:
    # ['Variables', 'Effect', '', 'SD of CG', 'Effects', '', 'SD of BL']
    iv_aux_label = None
    re_aux_label = None
    if isinstance(header2[3], str) and header2[3].strip():
        iv_aux_label = header2[3].strip()   # "SD of CG"
    if isinstance(header2[6], str) and header2[6].strip():
        re_aux_label = header2[6].strip()   # "SD of BL"

    # Estimator labels: table says "IV" and "ER" but ER corresponds to RE in text.
    estimators_raw = {"IV": "IV", "ER": "RE"}

    # Locate Observations row
    obs_idx: Optional[int] = None
    for i in range(len(df)):
        val = df.iloc[i, 0]
        if isinstance(val, str) and val.strip().lower().startswith("observations"):
            obs_idx = i
            break

    n_dict: Dict[str, Optional[float]] = {}
    if obs_idx is not None:
        row_obs = df.iloc[obs_idx]
        # Column indices are specific to this table layout
        n_dict["IV"] = parse_numeric_string(row_obs[1])
        n_dict["RE"] = parse_numeric_string(row_obs[4])

    # Notes row: the row immediately after Observations, if any
    notes: Optional[str] = None
    if obs_idx is not None and obs_idx + 1 < len(df):
        note_val = df.iloc[obs_idx + 1, 0]
        if isinstance(note_val, str):
            notes = note_val.strip()

    rows: List[Dict[str, Any]] = []

    # Data blocks start at row index 3 and continue until the Observations row
    i = 3
    row_counter = 1
    n_rows, n_cols = df.shape

    while i < n_rows:
        val0 = df.iloc[i, 0]

        # Stop when we hit the Observations row
        if isinstance(val0, str) and val0.strip().lower().startswith("observations"):
            break

        # Skip completely empty rows (defensive)
        if all(_is_nan(df.iloc[i, c]) for c in range(n_cols)):
            i += 1
            continue

        # Collect variable label lines (1 or 2 lines)
        label_lines: List[str] = []
        if isinstance(val0, str) and val0.strip():
            label_lines.append(val0.strip())

        # Possible continuation of the label on the next row
        next_idx = i + 1
        used_next_as_label = False
        if next_idx < n_rows:
            nxt = df.iloc[next_idx, 0]
            if (
                isinstance(nxt, str)
                and nxt.strip()
                and not nxt.strip().startswith("(")
                and not nxt.strip().lower().startswith("observations")
            ):
                # If this row has no numeric values, treat it as a continuation of the label
                if all(_is_nan(df.iloc[next_idx, c]) for c in range(1, n_cols)):
                    label_lines.append(nxt.strip())
                    used_next_as_label = True

        variable_label = " ".join(label_lines)

        # The "main" numeric row is the first label line row (index i)
        main = df.iloc[i]

        # The SE row comes immediately after the last label line
        se_idx = i + 1 + (1 if used_next_as_label else 0)
        se = df.iloc[se_idx] if se_idx < n_rows else None

        # Extract raw values using the fixed column mapping for this table:
        #   col 1: IV estimate
        #   col 3: IV aux metric (header2[3] = "SD of CG")
        #   col 4: ER/RE estimate
        #   col 6: ER/RE aux metric (header2[6] = "SD of BL")
        iv_est_raw = main[1] if not _is_nan(main[1]) else None
        iv_aux_raw = main[3] if not _is_nan(main[3]) else None
        re_est_raw = main[4] if not _is_nan(main[4]) else None
        re_aux_raw = main[6] if not _is_nan(main[6]) else None

        iv_se_raw = None
        re_se_raw = None
        if se is not None:
            iv_se_raw = se[1] if not _is_nan(se[1]) else None
            re_se_raw = se[4] if not _is_nan(se[4]) else None

        # Only keep rows that have at least one numeric estimate
        has_any_estimate = any(
            v is not None and not (isinstance(v, float) and math.isnan(v))
            for v in (iv_est_raw, re_est_raw)
        )
        if has_any_estimate:
            row_dict: Dict[str, Any] = {
                "row_id": f"{table_id}_row{row_counter}",
                "variable_label": variable_label,
                "raw_label_lines": label_lines,
                "effects": {
                    "IV": {
                        "estimator_label": estimators_raw["IV"],
                        "estimate_raw": iv_est_raw,
                        "estimate": (
                            parse_numeric_string(iv_est_raw)
                            if iv_est_raw is not None
                            else None
                        ),
                        "se_raw": iv_se_raw,
                        "se": (
                            parse_numeric_string(iv_se_raw)
                            if iv_se_raw is not None
                            else None
                        ),
                        "aux_label": iv_aux_label,       # e.g. "SD of CG"
                        "aux_value_raw": iv_aux_raw,
                        "aux_value": (
                            parse_numeric_string(iv_aux_raw)
                            if iv_aux_raw is not None
                            else None
                        ),
                    },
                    "RE": {
                        "estimator_label": estimators_raw["ER"],
                        "estimate_raw": re_est_raw,
                        "estimate": (
                            parse_numeric_string(re_est_raw)
                            if re_est_raw is not None
                            else None
                        ),
                        "se_raw": re_se_raw,
                        "se": (
                            parse_numeric_string(re_se_raw)
                            if re_se_raw is not None
                            else None
                        ),
                        "aux_label": re_aux_label,       # e.g. "SD of BL"
                        "aux_value_raw": re_aux_raw,
                        "aux_value": (
                            parse_numeric_string(re_aux_raw)
                            if re_aux_raw is not None
                            else None
                        ),
                    },
                },
            }
            rows.append(row_dict)
            row_counter += 1

        # Advance i to the row after the SE row for this variable
        i = se_idx + 1

    result: Dict[str, Any] = {
        "study_id": study_id,
        "table_id": table_id,
        "caption": caption,
        "estimators": ["IV", "RE"],
        "n": n_dict,
        "rows": rows,
        "notes": notes,
        "header_rows": [header1, header2],
    }
    return result
