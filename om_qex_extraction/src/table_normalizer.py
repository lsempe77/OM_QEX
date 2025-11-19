from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import math
import re
from typing import Any, Dict, List, Optional
import pandas as pd


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
        
        unique_lines: List[str] = []
        for ln in label_lines:
            if ln not in unique_lines:
                unique_lines.append(ln)

        label_raw = " ".join(unique_lines)
        outcome_label = _clean_hyphenated_label(label_raw) if label_raw else None

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


import re
from typing import Any, Dict, List, Optional

import pandas as pd

# assumes _is_nan, parse_numeric_string, parse_integer_with_thousands already exist

def _clean_hyphenated_label(text: str) -> str:
    """Merge hyphenated line breaks like 'expendi-' 'tures' -> 'expenditures'."""
    text = re.sub(r"\s+", " ", text.strip())
    text = re.sub(r"(\w+)-\s+(\w+)", r"\1\2", text)
    return text


def normalize_teep_multiarm_table(
    header_df: pd.DataFrame,
    body_df: pd.DataFrame,
    *,
    study_id: str,
    table_id: str,
    arms_config: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Generic normalizer for TEEP-style multi-arm regression tables.

    Assumes:
      - header_df: top chunk (caption + multi-row headers)
      - body_df:   bottom chunk (coeff rows, SE rows, Observations, Notes)
      - arms_config: list of dicts like:
          {"group_label": "Project", "effect_row": 0, "se_row": 2}
    """

    # ---- Caption + raw header rows ----
    caption = str(header_df.iloc[0, 0]).strip()
    header_rows: List[List[Any]] = header_df.values.tolist()

    # ---- Column metadata from header ----
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

    # ---- Observations row + Notes row in body ----
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
        n_val = body_df.iloc[obs_row_idx, 1]
        n_total = parse_integer_with_thousands(n_val)

    notes = ""
    if notes_row_idx is not None:
        notes = str(body_df.iloc[notes_row_idx, 0]).strip()

    # ---- Arms: coeff + SE rows per arm ----
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
                continue

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

    return {
        "study_id": study_id,
        "table_id": table_id,
        "caption": caption,
        "header_rows": header_rows,
        "n": n_total,
        "columns": columns,
        "rows": rows,
        "notes": notes,
    }

def normalize_teep_nonfood_table16(
    header_df: pd.DataFrame,
    body_df: pd.DataFrame,
    study_id: str = "TEEP_Malawi",
    table_id: str = "T16_nonfood",
) -> Dict[str, Any]:
    """
    Wrapper for Table 16: Project impact on non-food expenditures.
    """
    arms_config = [
        {"group_label": "Project", "effect_row": 0, "se_row": 2},
        {"group_label": "Lump-sum plus training", "effect_row": 3, "se_row": 6},
        {"group_label": "Lump-sum only", "effect_row": 7, "se_row": 10},
        {"group_label": "Training-only", "effect_row": 11, "se_row": 13},
    ]

    return normalize_teep_multiarm_table(
        header_df=header_df,
        body_df=body_df,
        study_id=study_id,
        table_id=table_id,
        arms_config=arms_config,
    )

import pandas as pd
from typing import Any, Dict, List, Optional

# assumes _is_nan, _clean_hyphenated_label, parse_numeric_string,
# and parse_integer_with_thousands already exist above


def normalize_teep_consumption_poverty_table17(
    header_df: pd.DataFrame,  # unused, but kept for consistent signature
    body_df: pd.DataFrame,
    study_id: str = "TEEP_Malawi",
    table_id: str = "T17_consumption_poverty",
) -> Dict[str, Any]:
    """
    Normalize Table 17: Project impact on total consumption and poverty.

    Note: Camelot's 'header' chunk is useless here, so we ignore header_df
    and derive caption + column metadata from body_df.
    """

    # ---- Caption from row 3 ----
    cap_parts: List[str] = []
    v0 = body_df.iloc[3, 0]
    v1 = body_df.iloc[3, 1]
    if isinstance(v0, str) and v0.strip():
        cap_parts.append(v0.strip())
    if isinstance(v1, str) and v1.strip():
        cap_parts.append(v1.strip())
    caption = " ".join(cap_parts)

    # ---- Header rows: keep rows 3–7 for reference ----
    header_rows = body_df.iloc[3:8].values.tolist()

    # ---- Column metadata from rows 4–7 ----
    columns: List[Dict[str, Any]] = []
    n_cols = body_df.shape[1]

    for j in range(1, n_cols):
        # tags: row 4 has "(1) (2)", "(3)", "(4)"
        tag_cell = body_df.iloc[4, j]
        col_tag: Optional[str] = None
        if isinstance(tag_cell, str) and tag_cell.strip():
            col_tag = " ".join(tag_cell.split())  # collapse spaces/newlines

        # label lines from rows 5–7
        label_lines: List[str] = []
        for r in range(5, 8):
            cell = body_df.iloc[r, j]
            if isinstance(cell, str) and cell.strip():
                label_lines.append(cell.strip())

        label_raw = " ".join(label_lines)
        outcome_label: Optional[str] = (
            _clean_hyphenated_label(label_raw) if label_raw else None
        )

        columns.append(
            {
                "column_index": j,
                "column_tag": col_tag,
                "outcome_label": outcome_label,
                "raw_header_lines": label_lines,
            }
        )

    # ---- Observations row (row 16) ----
    obs_row_idx = 16
    n_total: Optional[int] = None
    if obs_row_idx < body_df.shape[0]:
        raw_obs = body_df.iloc[obs_row_idx, 1]  # e.g., "776 776"
        n_token = None

    if isinstance(raw_obs, str):
        # grab first integer-like token: "776" out of "776 776"
        m = re.search(r"\d[\d,\.]*", raw_obs)
        if m:
            n_token = m.group(0)
    else:
        n_token = raw_obs

    if n_token is not None:
        n_total = parse_integer_with_thousands(n_token)


    # ---- Notes from rows 17–19 ----
    notes_parts: List[str] = []
    for i in range(17, body_df.shape[0]):
        for c in range(0, min(2, body_df.shape[1])):  # first two cols have the text
            cell = body_df.iloc[i, c]
            if isinstance(cell, str) and cell.strip():
                notes_parts.append(cell.strip())
    notes = " ".join(notes_parts)

    # ---- Arms: effect + SE rows ----
    arms_config = [
        {"group_label": "Project", "effect_row": 8, "se_row": 9},
        {"group_label": "Lump-sum plus training", "effect_row": 10, "se_row": 11},
        {"group_label": "Lump-sum only", "effect_row": 12, "se_row": 13},
        {"group_label": "Training-only", "effect_row": 14, "se_row": 15},
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
                continue

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

    return {
        "study_id": study_id,
        "table_id": table_id,
        "caption": caption,
        "header_rows": header_rows,
        "n": n_total,
        "columns": columns,
        "rows": rows,
        "notes": notes,
    }

