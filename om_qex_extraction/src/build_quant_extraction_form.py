#!/usr/bin/env python
"""
Build Quantitative Extraction Form CSV from QEX outputs + master metadata.

Usage (example):

    cd om_qex_extraction

    python build_quant_extraction_form.py \
        --qex-csv outputs/qex_extraction_results.csv \
        --master-csv ../data/raw/Master_file_included_studies.csv \
        --out-csv outputs/quant_extraction_form.csv

Adjust the default paths or CLI args to your repo layout.
"""

import argparse
import re
from pathlib import Path
from typing import Optional

import pandas as pd


# -------------------------
# Helpers
# -------------------------


def yes_no_to_binary(x: Optional[str]) -> Optional[int]:
    """Map 'Yes'/'No'/'Not mentioned'/None to 1/0/None (for quant form)."""
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return None

    s = str(x).strip().lower()
    if s == "yes":
        return 1
    if s in {"no", "not mentioned"}:
        return 0

    # Fallback – unknown code
    return None


def duration_to_months(text: Optional[str]) -> Optional[float]:
    """
    Convert a free-text duration into months.

    Expected patterns:
      - '12 months', '18 month', '3 years', '4 yrs', '6 weeks', etc.
    If cannot parse, returns None.
    """
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return None

    t = str(text).lower().strip()
    if not t:
        return None

    # Months
    m = re.search(r"([\d\.]+)\s*(month|months|mo)\b", t)
    if m:
        return float(m.group(1))

    # Years
    y = re.search(r"([\d\.]+)\s*(year|years|yr|yrs)\b", t)
    if y:
        return float(y.group(1)) * 12.0

    # Weeks (approximate: 4 weeks ~ 1 month)
    w = re.search(r"([\d\.]+)\s*(week|weeks|wk|wks)\b", t)
    if w:
        return float(w.group(1)) / 4.0

    # If already looks like a bare number, treat as months
    bare = re.fullmatch(r"[\d\.]+", t)
    if bare:
        return float(t)

    return None


def find_column(df: pd.DataFrame, candidates):
    """
    Find the first column in df that matches any candidate name (case-insensitive).
    Raises KeyError if none found.
    """
    cols_lower = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand is None:
            continue
        lc = cand.lower()
        if lc in cols_lower:
            return cols_lower[lc]
    raise KeyError(f"None of the candidate columns {candidates} found in DataFrame.")


# -------------------------
# Main builder
# -------------------------


def build_quant_form(qex_csv: Path, master_csv: Path, out_csv: Path):
    # --- Load data ---
    qex = pd.read_csv(qex_csv)
    meta = pd.read_csv(master_csv)

    # --- Identify StudyID, no master merge (for now) ---

    # Try to use a study_id-like column if it exists AND has values
    study_col = None
    try:
        study_col = find_column(qex, ["study_id", "StudyID", "study"])
    except KeyError:
        study_col = None

    if study_col is not None and not qex[study_col].isna().all():
        qex = qex.rename(columns={study_col: "StudyID"})
    else:
        # Fall back to TEI key (e.g., 'PHRKN65M.tei') and strip the extension
        if "_key" in qex.columns:
            print(
                "WARNING: StudyID missing in QEX CSV; using _key (without .tei) as StudyID."
            )
            qex["StudyID"] = (
                qex["_key"].astype(str).str.replace(r"\.tei$", "", regex=True)
            )
        else:
            print(
                "WARNING: No study_id or _key found; using row index as StudyID."
            )
            qex["StudyID"] = qex.index.astype(str)

    # For now, we do NOT merge with the master file; we rely on QEX columns.
    df = qex.copy()



    # --- EstimateID ---
    # If QEX already has an 'EstimateID' column, use it; otherwise construct one.
    if "EstimateID" not in df.columns:
        # group per StudyID and enumerate
        df["_est_idx"] = df.groupby("StudyID").cumcount() + 1
        df["EstimateID"] = df["StudyID"].astype(str) + "_" + df["_est_idx"].astype(str)
        df.drop(columns=["_est_idx"], inplace=True)

    # --- Intervention abbreviation + name ---
    # We assume QEX CSV has columns from InterventionInfo, e.g.:
    #   'intervention_abbreviation', 'intervention_name', 'intervention_description',
    #   'first_year_of_intervention', 'length_of_follow_up', 'exposure_to_intervention',
    #   'consumption_support', 'healthcare', 'assets', 'skills_training', 'savings',
    #   'coaching', 'social_empowerment'
    #
    # Adjust names below if your flattened CSV uses dotted paths, e.g.
    # 'intervention_info.intervention_abbreviation', etc.

    cand_abbrev = [c for c in df.columns if "intervention_abbreviation" in c]
    cand_name = [c for c in df.columns if "intervention_name" in c and "abbreviation" not in c]
    cand_desc = [c for c in df.columns if "intervention_description" in c]
    cand_first_year = [c for c in df.columns if "first_year_of_intervention" in c]
    cand_followup = [c for c in df.columns if "length_of_follow_up" in c]
    cand_exposure = [c for c in df.columns if "exposure_to_intervention" in c]

    abbrev_col = cand_abbrev[0] if cand_abbrev else None
    name_col = cand_name[0] if cand_name else None
    desc_col = cand_desc[0] if cand_desc else None
    first_year_col = cand_first_year[0] if cand_first_year else None
    followup_col = cand_followup[0] if cand_followup else None
    exposure_col = cand_exposure[0] if cand_exposure else None

    # Combined intervention abbrev + name
    def combine_abbrev_name(row):
        abbr = row[abbrev_col] if abbrev_col and pd.notna(row.get(abbrev_col)) else ""
        nm = row[name_col] if name_col and pd.notna(row.get(name_col)) else ""
        if abbr and nm:
            return f"{abbr} {nm}"
        return nm or abbr or ""

    if abbrev_col or name_col:
        df["Intervention abbreviation and name"] = df.apply(combine_abbrev_name, axis=1)
    else:
        df["Intervention abbreviation and name"] = ""

    # Intervention description
    if desc_col:
        df["Intervention description"] = df[desc_col]
    else:
        df["Intervention description"] = ""

    # --- Frist year of intervention (from QEX) ---

    # Prefer the QEX field `year_intervention_started` and do NOT overwrite
    # it later from the master metadata (which doesn't know about PHRKN65M).
    if "year_intervention_started" in df.columns:
        df["Frist year of intervention"] = (
            pd.to_numeric(df["year_intervention_started"], errors="coerce")
            .astype("Int64")
        )
    else:
        df["Frist year of intervention"] = pd.Series([pd.NA] * len(df), dtype="Int64")

    # Length of follow up (months)
    if followup_col:
        df["Length of follow up"] = df[followup_col].apply(duration_to_months)
    else:
        df["Length of follow up"] = None

    # Exposure to intervention (months)
    if exposure_col:
        df["Exposure to intervention"] = df[exposure_col].apply(duration_to_months)
    else:
        df["Exposure to intervention"] = None

    # --- Intervention name fields ---

    # Use program_name from QEX for the Quant form's
    # "Intervention abbreviation and name" column.
    if "program_name" in df.columns:
        df["Intervention abbreviation and name"] = df["program_name"].fillna("")
    else:
        df["Intervention abbreviation and name"] = ""

    # Detailed intervention description (from LLM)
    if "intervention_description" in df.columns:
        df["Intervention description"] = df["intervention_description"].fillna("")
    else:
        df["Intervention description"] = ""

    # Timing fields – keep as-is for now (LLM returns numeric-ish strings)
    if "length_of_follow_up" in df.columns:
        df["Length of follow up"] = df["length_of_follow_up"]
    else:
        df["Length of follow up"] = ""

    if "exposure_to_intervention" in df.columns:
        df["Exposure to intervention"] = df["exposure_to_intervention"]
    else:
        df["Exposure to intervention"] = ""

    # --- Components (Yes/No/Not mentioned -> 0/1/None) ---
    comp_map = {
        "Consumption support (cash or in-kind) to stabilize food security and prevent households from selling assets to survive ": "consumption_support",
        "Healthcare provision to address the basic health needs of individuals and households": "healthcare",
        "Assets transfer (often livestock, tools, or seed capital) to provide a foundation for an income-generation activity.": "assets",
        "Skills training to enable participants to productively manage and grow their assets.": "skills_training",
        "Savings facilitation (e.g., savings accounts or linkages to microfinance institutions) to foster financial discipline and resilience.": "savings",
        "Coaching and mentoring to offer continuous motivation and goal-setting support.": "coaching",
        "Social empowerment and linkages to social protection, markets, and public services to encourage opportunities and inclusion in existing systems.": "social_empowerment",
    }
    
    # --- Outcome name mapping into Quant form ---

    if "outcome_name" in df.columns:
        df["Outcome name"] = df["outcome_name"]
    else:
        df["Outcome name"] = ""

    for out_col, base_name in comp_map.items():
        # In QEX output, components are named like 'component_<base_name>'
        candidates = [
            c
            for c in df.columns
            if c.lower() == base_name.lower()
            or c.lower() == f"component_{base_name}".lower()
            or c.lower().endswith("_" + base_name.lower())
        ]
        if candidates:
            src_col = candidates[0]
            df[out_col] = df[src_col].apply(yes_no_to_binary)
        else:
            df[out_col] = None


    # --- Evaluation design & method codes ---
    # MethodInfo-coded fields we just added: evaluation_design_code, evaluation_method_code
    cand_ed_code = [c for c in df.columns if "evaluation_design_code" in c]
    cand_em_code = [c for c in df.columns if "evaluation_method_code" in c]

    eval_design_col = cand_ed_code[0] if cand_ed_code else None
    eval_method_col = cand_em_code[0] if cand_em_code else None

    if eval_design_col:
        df["Evaluation Design"] = pd.to_numeric(df[eval_design_col], errors="coerce").astype("Int64")
    else:
        df["Evaluation Design"] = pd.Series([pd.NA] * len(df), dtype="Int64")

    if eval_method_col:
        df["Evaluation Method"] = df[eval_method_col].astype("string")
    else:
        df["Evaluation Method"] = pd.Series([pd.NA] * len(df), dtype="string")

    # --- Metadata fields for the form (from master) ---
        # Use QEX-derived metadata for now
    author_col = "author_name" if "author_name" in df.columns else None
    year_col = "year_of_publication" if "year_of_publication" in df.columns else None
    pubtype_col = None  # no publication type in QEX yet
    country_col = "country" if "country" in df.columns else None


    # Author name
    df["Author name"] = df[author_col] if author_col else ""

    # Year of publication
    if year_col:
        df["Year of publication"] = pd.to_numeric(df[year_col], errors="coerce").astype("Int64")
    else:
        df["Year of publication"] = pd.Series([pd.NA] * len(df), dtype="Int64")

    # Publication type
    if pubtype_col:
        df["Publication type"] = pd.to_numeric(df[pubtype_col], errors="coerce").astype("Int64")
    else:
        df["Publication type"] = pd.Series([pd.NA] * len(df), dtype="Int64")

    # Country from metadata (override anything from LLM if present)
    if country_col:
        df["Country"] = df[country_col]
    else:
        df["Country"] = ""

    # --- Final column ordering for Quant Extraction Form ---
    # Coder name + Notes intentionally left blank for humans.
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
    ]

    # Ensure columns exist; if not, create blanks
    for col in quant_cols:
        if col not in df.columns:
            df[col] = pd.NA

    out_df = df[quant_cols].copy()

    # Blank coder + notes
    out_df["Coder name"] = ""
    out_df["Notes"] = ""

    # --- Write CSV ---
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_csv, index=False)
    print(f"Quant Extraction Form written to: {out_csv}")


def main():
    parser = argparse.ArgumentParser(description="Build Quant Extraction Form from QEX outputs.")
    parser.add_argument(
        "--qex-csv",
        type=Path,
        required=True,
        help="Path to QEX extraction CSV (per-estimate output).",
    )
    parser.add_argument(
        "--master-csv",
        type=Path,
        required=True,
        help="Path to master metadata CSV (Study-level info).",
    )
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