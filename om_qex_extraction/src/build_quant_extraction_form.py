#!/usr/bin/env python3
"""
Build Quantitative Extraction Form CSV from Stage 2 (QEX) outputs.

Design goals:
- Preserve per-estimate rows (StudyID + EstimateID).
- Timing fields:
  - Exposure to intervention: study-level months (broadcast to each estimate row).
  - Length of follow up: estimate-level months since intervention end when available,
    with fallbacks to study-level anchors and then free-text parsing.
- Keep output column names stable for downstream steps.
"""

import argparse
import re
import ast
from pathlib import Path
from typing import Optional, Iterable, Tuple

import numpy as np
import pandas as pd

# Consistent conversion constants
WEEKS_PER_MONTH = 4.345
DAYS_PER_MONTH = 30.437

# -------------------------
# I/O helpers
# -------------------------

def read_csv_robust(path: Path) -> pd.DataFrame:
    """
    Read CSV with a small encoding fallback ladder to avoid hard failures on cp1252/latin1 sources.
    """
    encodings = [None, "utf-8", "utf-8-sig", "cp1252", "latin1"]
    for enc in encodings:
        try:
            if enc is None:
                return pd.read_csv(path)
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path, encoding="latin1", encoding_errors="replace")


# -------------------------
# Generic helpers
# -------------------------

def find_col(df: pd.DataFrame, candidates: Iterable[str]) -> Optional[str]:
    cols_lower = {c.lower(): c for c in df.columns}
    for cand in candidates:
        lc = cand.lower()
        if lc in cols_lower:
            return cols_lower[lc]
    return None

def first_nonmissing(s: pd.Series):
    s2 = s.dropna()
    return s2.iloc[0] if len(s2) > 0 else np.nan

def round_to_half_months(x):
    if pd.isna(x):
        return np.nan
    try:
        v = float(x)
    except Exception:
        return np.nan
    return round(v * 2) / 2.0

def yes_no_to_binary(x: Optional[str]) -> Optional[int]:
    """Map 'Yes'/'No'/'Not mentioned'/None to 1/0/None."""
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return None
    s = str(x).strip().lower()
    if s == "yes":
        return 1
    if s in {"no", "not mentioned"}:
        return 0
    return None


# -------------------------
# Parsing helpers
# -------------------------

_NUM_RE = re.compile(r"(-?\d+(?:\.\d+)?)")

def extract_numbers(text: str) -> list[float]:
    return [float(x) for x in _NUM_RE.findall(text)]

def duration_to_months(text: Optional[str], prefer: str = "max") -> Optional[float]:
    """
    Convert a free-text duration into months.
    Handles examples:
      - '12 months', '18 month', '3 years', '4 yrs', '6 weeks', '90 days'
      - ranges like '6-12 months' (prefer='max' -> 12)
    Returns None if cannot parse.
    """
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return None
    t = str(text).strip().lower()
    if not t:
        return None

    nums = extract_numbers(t)
    if not nums:
        return None

    if prefer == "max":
        v = max(nums)
    elif prefer == "min":
        v = min(nums)
    else:
        v = nums[0]

    if re.search(r"\byear|years|yrs?\b", t):
        return v * 12.0
    if re.search(r"\bweek|weeks|wks?\b", t):
        return v / WEEKS_PER_MONTH
    if re.search(r"\bday|days|dys?\b", t):
        return v / DAYS_PER_MONTH
    if re.search(r"\bmonth|months|mos?\b", t):
        return v

    # No explicit unit: treat as months (conservative default)
    return v

def unit_value_to_months(value: float, unit: str) -> float:
    u = str(unit).strip().lower()
    if u == "years":
        return value * 12.0
    if u == "months":
        return value
    if u == "weeks":
        return value / WEEKS_PER_MONTH
    if u == "days":
        return value / DAYS_PER_MONTH
    return np.nan

def normalize_numeric_to_months_from_label(value, label: Optional[str]) -> float:
    """
    If label contains explicit units, convert value accordingly.
    Otherwise, return value unchanged.
    """
    if pd.isna(value):
        return np.nan
    try:
        v = float(value)
    except Exception:
        return np.nan

    if label is None or (isinstance(label, float) and pd.isna(label)):
        return v

    t = str(label).strip().lower()
    if re.search(r"\byear|years|yrs?\b", t):
        return v * 12.0
    if re.search(r"\bweek|weeks|wks?\b", t):
        return v / WEEKS_PER_MONTH
    if re.search(r"\bday|days|dys?\b", t):
        return v / DAYS_PER_MONTH
    if re.search(r"\bmonth|months|mos?\b", t):
        return v

    return v

def months_between(start_year, start_month, end_year, end_month):
    """
    Compute approximate months between two dates given year/month.
    If years are missing, returns NaN.
    If months are missing, approximate as June (6) (mid-year).
    """
    if pd.isna(start_year) or pd.isna(end_year):
        return np.nan
    try:
        sy = int(start_year)
        ey = int(end_year)
    except Exception:
        return np.nan

    sm = 6 if pd.isna(start_month) else int(start_month)
    em = 6 if pd.isna(end_month) else int(end_month)

    return (ey - sy) * 12 + (em - sm)

def coerce_scalar_number(x) -> float:
    """
    Return float if scalar-like; NaN if list-like (e.g., "[6, 18]") or non-numeric.
    """
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return np.nan
    if isinstance(x, (int, float, np.integer, np.floating)):
        return float(x)
    if isinstance(x, str):
        s = x.strip()
        # list-like -> ambiguous for single-value quant form
        if s.startswith("[") and s.endswith("]"):
            try:
                _ = ast.literal_eval(s)
                return np.nan
            except Exception:
                return np.nan
        try:
            return float(s)
        except Exception:
            return np.nan
    return np.nan


# -------------------------
# ID normalization
# -------------------------

def ensure_ids(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure StudyID and EstimateID exist and are stable.
    """
    if "StudyID" not in df.columns:
        if "_key" in df.columns:
            print("WARNING: StudyID missing in QEX CSV; using _key (without .tei/.tei.xml) as StudyID.")
            df["StudyID"] = (
                df["_key"]
                .astype(str)
                .str.replace(".tei.xml", "", regex=False)
                .str.replace(".tei", "", regex=False)
            )
        else:
            raise KeyError("QEX CSV must contain either StudyID or _key.")

    if "EstimateID" not in df.columns:
        alt = find_col(df, ["estimate_id", "estimateid", "estimateId"])
        if alt:
            df["EstimateID"] = df[alt].astype(str)
        else:
            # deterministic per-study sequence
            df["EstimateID"] = df.groupby("StudyID").cumcount().add(1).astype(str)

    return df


# -------------------------
# Timing computation
# -------------------------

def compute_exposure_months_study(df: pd.DataFrame) -> pd.Series:
    """
    Exposure months (study-level): prefer anchor start->end, else free-text.
    Broadcast to all estimate rows.
    """
    int_start_y = find_col(df, ["intervention_start_year"])
    int_start_m = find_col(df, ["intervention_start_month"])
    int_end_y   = find_col(df, ["intervention_end_year"])
    int_end_m   = find_col(df, ["intervention_end_month"])

    if int_start_y and int_end_y:
        anchor = df.apply(
            lambda r: months_between(
                r[int_start_y],
                r[int_start_m] if int_start_m else np.nan,
                r[int_end_y],
                r[int_end_m] if int_end_m else np.nan,
            ),
            axis=1,
        )
    else:
        anchor = pd.Series([np.nan] * len(df), index=df.index)

    anchor_by_study = anchor.groupby(df["StudyID"]).agg(first_nonmissing)

    exposure_text_col = find_col(df, ["exposure_to_intervention", "exposure_duration", "treatment_duration"])
    exposure_text_months = (
        df[exposure_text_col].apply(lambda x: duration_to_months(x, prefer="max"))
        if exposure_text_col else pd.Series([np.nan] * len(df), index=df.index)
    )
    text_by_study = exposure_text_months.groupby(df["StudyID"]).agg(first_nonmissing)

    out = df["StudyID"].map(anchor_by_study)
    m = out.isna()
    out.loc[m] = df.loc[m, "StudyID"].map(text_by_study)
    out = out.apply(round_to_half_months)
    return out


def compute_followup_months_estimate(df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
    """
    Follow-up months (estimate-level, months since intervention end):

    Priority:
      1) months_since_intervention_end_computed (canonical per-estimate; scalar only)
      2) timepoint_value + timepoint_unit (ONLY if timepoint_origin == intervention_end; scalar only)
      3) timepoint_value + units inferred from outcome_timepoint_label (ONLY if origin == intervention_end; scalar only)
      4) study-level anchor: intervention_end -> final_followup
      5) free-text follow-up duration parse

    Returns:
      (followup_months_estimate, source_label)
    """
    n = len(df)

    # 4) anchor (study-level end -> final follow-up)
    int_end_y   = find_col(df, ["intervention_end_year"])
    int_end_m   = find_col(df, ["intervention_end_month"])
    final_fu_y  = find_col(df, ["final_followup_year", "final_follow_up_year"])
    final_fu_m  = find_col(df, ["final_followup_month", "final_follow_up_month"])

    if int_end_y and final_fu_y:
        anchor = df.apply(
            lambda r: months_between(
                r[int_end_y],
                r[int_end_m] if int_end_m else np.nan,
                r[final_fu_y],
                r[final_fu_m] if final_fu_m else np.nan,
            ),
            axis=1,
        )
    else:
        anchor = pd.Series([np.nan] * n, index=df.index)

    anchor_by_study = anchor.groupby(df["StudyID"]).agg(first_nonmissing)

    # 5) text fallback
    followup_text_col = find_col(df, ["length_of_follow_up", "length_of_followup", "follow_up_length"])
    followup_text_months = (
        df[followup_text_col].apply(lambda x: duration_to_months(x, prefer="max"))
        if followup_text_col else pd.Series([np.nan] * n, index=df.index)
    )

    # 1) canonical computed months (scalar only)
    computed_raw = df.get("months_since_intervention_end_computed", pd.Series([np.nan] * n))
    computed = pd.Series([coerce_scalar_number(x) for x in computed_raw], index=df.index)
    out = pd.to_numeric(computed, errors="coerce")
    source = pd.Series(["computed_months_since_end"] * n, index=df.index)

    # only allow computed override from timepoint_* if origin == intervention_end
    origin = df.get("timepoint_origin", pd.Series([None] * n))
    origin_end_mask = origin.astype(str).str.strip().str.lower().eq("intervention_end")

    # 2) timepoint_value + timepoint_unit (scalar only)
    tp_val_raw = df.get("timepoint_value", pd.Series([np.nan] * n))
    tp_val = pd.Series([coerce_scalar_number(x) for x in tp_val_raw], index=df.index)
    tp_unit = df.get("timepoint_unit", pd.Series([np.nan] * n))

    m = out.isna() & origin_end_mask & tp_val.notna() & tp_unit.notna()
    if m.any():
        out.loc[m] = [
            unit_value_to_months(v, u) for v, u in zip(tp_val.loc[m].tolist(), tp_unit.loc[m].tolist())
        ]
        source.loc[m] = "timepoint_value+unit"

    # 3) label-embedded units (scalar only)
    label = df.get("outcome_timepoint_label", pd.Series([None] * n))
    m = out.isna() & origin_end_mask & tp_val.notna() & label.notna()
    if m.any():
        out.loc[m] = [
            normalize_numeric_to_months_from_label(v, lbl) for v, lbl in zip(tp_val.loc[m].tolist(), label.loc[m].tolist())
        ]
        source.loc[m] = "timepoint_value+label_units"

    # 4) anchor fallback
    m = out.isna()
    if m.any():
        out.loc[m] = df.loc[m, "StudyID"].map(anchor_by_study)
        source.loc[m & out.notna()] = "study_anchor_end_to_final"

    # 5) text fallback
    m = out.isna()
    if m.any():
        out.loc[m] = followup_text_months.loc[m]
        source.loc[m & out.notna()] = "text_duration_parse"

    out = pd.to_numeric(out, errors="coerce").round(0)
    return out, source


# -------------------------
# Main builder
# -------------------------

def build_quant_form(qex_csv: Path, master_csv: Path, out_csv: Path):
    qex = read_csv_robust(qex_csv)
    _ = read_csv_robust(master_csv)  # keep CLI compatibility; can enrich later

    df = ensure_ids(qex.copy())

    # ---- Timing ----
    df["_exposure_months_study"] = compute_exposure_months_study(df)
    df["_followup_months_est"], df["_followup_source"] = compute_followup_months_estimate(df)

    df["Exposure to intervention"] = df["_exposure_months_study"]
    df["Length of follow up"] = df["_followup_months_est"]

    # ---- Bibliographic + program fields (pass-through where available) ----
    if "author_name" in df.columns:
        df["Author name"] = df["author_name"]
    elif "Author" in df.columns:
        df["Author name"] = df["Author"]
    else:
        df["Author name"] = ""

    if "year_of_publication" in df.columns:
        df["Year of publication"] = df["year_of_publication"]
    elif "publication_year" in df.columns:
        df["Year of publication"] = df["publication_year"]
    elif "year" in df.columns:
        df["Year of publication"] = df["year"]
    else:
        df["Year of publication"] = pd.NA

    if "publication_type" in df.columns:
        df["Publication type"] = df["publication_type"]
    else:
        df["Publication type"] = ""

    if "country" in df.columns:
        df["Country"] = df["country"]
    else:
        df["Country"] = ""

    # Keep misspelling for backward compatibility
    if "first_year_of_intervention" in df.columns:
        df["Frist year of intervention"] = df["first_year_of_intervention"]
    elif "year_intervention_started" in df.columns:
        df["Frist year of intervention"] = df["year_intervention_started"]
    else:
        df["Frist year of intervention"] = pd.NA

    if "program_name" in df.columns:
        df["Intervention abbreviation and name"] = df["program_name"].fillna("")
    else:
        df["Intervention abbreviation and name"] = ""

    if "intervention_description" in df.columns:
        df["Intervention description"] = df["intervention_description"].fillna("")
    else:
        df["Intervention description"] = ""

    # ---- Components ----
    comp_map = {
        "Consumption support (cash or in-kind) to stabilize food security and prevent households from selling assets to survive ": "consumption_support",
        "Healthcare provision to address the basic health needs of individuals and households": "healthcare",
        "Assets transfer (often livestock, tools, or seed capital) to provide a foundation for an income-generation activity.": "assets",
        "Skills training to enable participants to productively manage and grow their assets.": "skills_training",
        "Savings facilitation (e.g., savings accounts or linkages to microfinance institutions) to foster financial discipline and resilience.": "savings",
        "Coaching and mentoring to offer continuous motivation and goal-setting support.": "coaching",
        "Social empowerment and linkages to social protection, markets, and public services to encourage opportunities and inclusion in existing systems.": "social_empowerment",
    }

    for quant_col, qex_col in comp_map.items():
        if qex_col in df.columns:
            df[quant_col] = df[qex_col].apply(yes_no_to_binary)
        else:
            df[quant_col] = pd.NA

    # ---- Evaluation design & method codes ----
    eval_design_col = find_col(df, ["evaluation_design_code"])
    eval_method_col = find_col(df, ["evaluation_method_code"])

    if eval_design_col:
        df["Evaluation Design"] = pd.to_numeric(df[eval_design_col], errors="coerce").astype("Int64")
    else:
        df["Evaluation Design"] = pd.Series([pd.NA] * len(df), dtype="Int64")

    if eval_method_col:
        df["Evaluation Method"] = pd.to_numeric(df[eval_method_col], errors="coerce").astype("Int64")
    else:
        df["Evaluation Method"] = pd.Series([pd.NA] * len(df), dtype="Int64")

    # ---- Outcome name ----
    if "outcome_name" in df.columns:
        df["Outcome name"] = df["outcome_name"]
    else:
        df["Outcome name"] = ""

    # ---- Final column ordering (unchanged) ----
    quant_cols = [
        "Coder name",
        "Notes",
        "StudyID",
        "EstimateID",
        "Author name",
        "Year of publication",
        "Publication type",
        "Intervention abbreviation and name",
        "Intervention description",
        "Country",
        "Frist year of intervention",
        "Length of follow up",
        "Exposure to intervention",
        "Consumption support (cash or in-kind) to stabilize food security and prevent households from selling assets to survive ",
        "Healthcare provision to address the basic health needs of individuals and households",
        "Assets transfer (often livestock, tools, or seed capital) to provide a foundation for an income-generation activity.",
        "Skills training to enable participants to productively manage and grow their assets.",
        "Savings facilitation (e.g., savings accounts or linkages to microfinance institutions) to foster financial discipline and resilience.",
        "Coaching and mentoring to offer continuous motivation and goal-setting support.",
        "Social empowerment and linkages to social protection, markets, and public services to encourage opportunities and inclusion in existing systems.",
        "Evaluation Design",
        "Evaluation Method",
        "Outcome name",
        "_key",
    ]

    for col in quant_cols:
        if col not in df.columns:
            df[col] = pd.NA

    out_df = df[quant_cols].copy()
    out_df["Coder name"] = ""
    out_df["Notes"] = ""

    out_csv = Path(out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_csv, index=False)
    print(f"Quant Extraction Form written to: {out_csv}")


def main():
    parser = argparse.ArgumentParser(description="Build Quant Extraction Form from QEX outputs.")
    parser.add_argument("--qex-csv", type=Path, required=True, help="Path to QEX extraction CSV (per-estimate output).")
    parser.add_argument("--master-csv", type=Path, required=True, help="Path to master metadata CSV (Study-level info).")
    parser.add_argument(
        "--out-csv",
        type=Path,
        default=Path("outputs/quant_extraction_form.csv"),
        help="Output path for Quant Extraction Form CSV.",
    )
    args = parser.parse_args()
    build_quant_form(args.qex_csv, args.master_csv, args.out_csv)

if __name__ == "__main__":
    main()
