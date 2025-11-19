from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import math
import re
from typing import Any, Dict, List, Optional
import pandas as pd


import math
import re
from typing import Any, Optional

def _is_nan(val: Any) -> bool:
    if val is None:
        return True
    if isinstance(val, float) and math.isnan(val):
        return True
    if isinstance(val, str) and val.strip() == "":
        return True
    return False

def parse_numeric_string(value: Any) -> Optional[float]:
    """
    Parse coefficients / SEs from a variety of formats:

    - ABM-style decimal commas:   '-4,89', '(21,35**)'  -> -4.89, 21.35
    - Thousands separators:       '8,857', '15,745'      -> 8857.0, 15745.0
    - Plain decimals:             '43.29', '(411.0)'     -> 43.29, 411.0

    Stars are removed, parentheses stripped.
    """
    if _is_nan(value):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    s = str(value).strip()

    # Strip surrounding parentheses
    if s.startswith("(") and s.endswith(")"):
        s = s[1:-1].strip()
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1].strip()

    # Remove significance stars
    s = re.sub(r"[*]+", "", s)

    # Drop thousands separators where appropriate
    # Pattern like: 1,234 or 15,745 or 1,234,567.89
    if re.match(r"^\d{1,3}(,\d{3})+(\.\d+)?$", s):
        s_clean = s.replace(",", "")
        try:
            return float(s_clean)
        except ValueError:
            return None

    # ABM-style decimal comma: digits, comma, digits
    if re.match(r"^-?\d+,\d+$", s):
        s_clean = s.replace(",", ".")
        try:
            return float(s_clean)
        except ValueError:
            return None

    # Fallback: just try plain float
    try:
        return float(s)
    except ValueError:
        return None


def parse_integer_with_thousands(value: Any) -> Optional[int]:
    """
    Parse sample sizes like '1,005' or '2.134' as integers.

    Logic:
      - If already int/float, cast to int.
      - Strip whitespace, parentheses, and stars.
      - If it looks like a thousands pattern (e.g., 1,005 or 2.134),
        remove the separators and parse as int.
      - Otherwise, just strip commas and parse.
    """
    if _is_nan(value):
        return None

    if isinstance(value, int):
        return value
    if isinstance(value, float):
        # Treat anything numeric here as an N-like value
        return int(value)

    s = str(value).strip()

    # Strip surrounding parentheses or brackets
    if s.startswith("(") and s.endswith(")"):
        s = s[1:-1].strip()
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1].strip()

    # Remove significance stars if any accidentally appear
    s = re.sub(r"[*]+", "", s)

    # If it matches a thousands pattern like 1,005 or 2.134.567
    if re.match(r"^\d{1,3}([.,]\d{3})+$", s):
        s_clean = re.sub(r"[.,]", "", s)
    else:
        # More conservative: just drop commas
        s_clean = s.replace(",", "")

    try:
        return int(s_clean)
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
        n_dict["IV"] = parse_integer_with_thousands(row_obs[1])
        n_dict["RE"] = parse_integer_with_thousands(row_obs[4])

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

import re
from typing import Any, Dict, List, Optional

import pandas as pd

# ... _is_nan, parse_numeric_string, parse_integer_with_thousands already defined above ...


def _clean_hyphenated_label(text: str) -> str:
    """
    Merge hyphenated line breaks like 'expendi-' 'tures' -> 'expenditures'.
    """
    text = re.sub(r"\s+", " ", text.strip())
    # Merge word- hyphen + space + word => single word
    text = re.sub(r"(\w+)-\s+(\w+)", r"\1\2", text)
    return text


def normalize_teep_nonfood_table16(
    header_df: pd.DataFrame,
    body_df: pd.DataFrame,
    study_id: str = "TEEP_Malawi",
    table_id: str = "T16_nonfood",
) -> Dict[str, Any]:
    """
    Normalize Table 16: Project impact on non-food expenditures (Malawi paper).

    Pattern:
      - Header chunk (header_df) contains caption + multi-row column headers.
      - Body chunk (body_df) contains:
          - coefficients for each arm in specific rows
          - SE rows beneath
          - 'Observations' row with N
          - Notes row.

    Output format is compatible with a generalized QEX builder.
    """

    # Caption & raw header rows
    caption = str(header_df.iloc[0, 0]).strip()
    header_rows: List[List[Any]] = header_df.values.tolist()

    # Build column metadata (for columns 1..12)
    columns: List[Dict[str, Any]] = []
    n_cols = header_df.shape[1]

    for j in range(1, n_cols):
        col_tag_raw = header_df.iloc[1, j]
        col_tag = str(col_tag_raw).strip() if isinstance(col_tag_raw, str) else None

        label_lines: List[str] = []
        for r in range(2, header_df.shape[0]):
            cell = header_df.iloc[r, j]
            if isinstance(cell, str) and cell.strip():
                label_lines.append(cell.strip())

        label_raw = " ".join(label_lines)
        outcome_label = _clean_hyphenated_label(label_raw) if label_raw else None

        columns.append(
            {
                "column_index": j,
                "column_tag": col_tag,
                "outcome_label": outcome_label,
                "raw_header_lines": label_lines,
            }
        )

    # Find Observations row and Notes row in body
    obs_row_idx: Optional[int] = None
    notes_row_idx: Optional[int] = None

    for i in range(body_df.shape[0]):
        v0 = body_df.iloc[i, 0]
        if isinstance(v0, str):
            s = v0.strip()
            if s.lower().startswith("observations"):
                obs_row_idx = i
            elif s.lower().startswith("notes"):
                notes_row_idx = i

    n_total: Optional[int] = None
    if obs_row_idx is not None:
        # N is repeated across columns, we just take column 1 and parse as integer
        n_val = body_df.iloc[obs_row_idx, 1]
        from typing import cast
        n_total = parse_integer_with_thousands(cast(Any, n_val))

    notes = ""
    if notes_row_idx is not None:
        notes = str(body_df.iloc[notes_row_idx, 0]).strip()

    # Arm configuration: map each arm to its coefficient & SE rows
    arms_config = [
        {"group_label": "Project", "effect_row": 0, "se_row": 2},
        {"group_label": "Lump-sum plus training", "effect_row": 3, "se_row": 6},
        {"group_label": "Lump-sum only", "effect_row": 7, "se_row": 10},
        {"group_label": "Training-only", "effect_row": 11, "se_row": 13},
    ]

    rows: List[Dict[str, Any]] = []

    for arm in arms_config:
        group_label = arm["group_label"]
        eff_idx = arm["effect_row"]
        se_idx = arm["se_row"]

        effect_row = body_df.iloc[eff_idx]
        se_row = body_df.iloc[se_idx]

        for col in columns:
            j = col["column_index"]

            effect_raw = effect_row[j]
            if _is_nan(effect_raw):
                continue  # no effect in this column for this arm

            se_raw = se_row[j] if se_idx < body_df.shape[0] else None

            estimate = parse_numeric_string(effect_raw)
            se_val = parse_numeric_string(se_raw) if not _is_nan(se_raw) else None

            row_id = f"{table_id}_{group_label.replace(' ', '').replace('-', '')}_col{j}"

            rows.append(
                {
                    "row_id": row_id,
                    "group_label": group_label,
                    "column_index": j,
                    "column_tag": col["column_tag"],
                    "outcome_label": col["outcome_label"],
                    "estimate_raw": effect_raw,
                    "estimate": estimate,
                    "se_raw": se_raw,
                    "se": se_val,
                }
            )

    normalized: Dict[str, Any] = {
        "study_id": study_id,
        "table_id": table_id,
        "caption": caption,
        "header_rows": header_rows,
        "n": n_total,
        "columns": columns,
        "rows": rows,
        "notes": notes,
    }

    return normalized