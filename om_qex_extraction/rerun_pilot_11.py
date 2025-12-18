#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# -----------------------------------------------------------------------------
# Configure pilot keys (these match the 11-study pilot you shared)
# NOTE: run_twostage_extraction.py expects stems like "ZBAE7IPZ.tei"
# -----------------------------------------------------------------------------
PILOT_KEYS = [
    "9UCQN8H8",
    "A3SDHNSC",
    "CG73D75P",
    "Q8XK3EIW",
    "RSAW8CHM",
    "TSGTVT7T",
    "TUJ6CUI3",
    "VAUQIN7W",
    "XIPIMS2M",
    "XP5HHJBR",
    "ZBAE7IPZ",
]

def norm_key(k: str) -> str:
    return k.replace(".tei.xml", "").replace(".tei", "").replace(".xml", "")

HERE = Path(__file__).resolve().parent          # .../om_qex_extraction
REPO_ROOT = HERE.parent                         # repo root (expects ../data/...)


def pick_script(*candidates: str) -> str:
    """Return the first existing script path among candidates."""
    for c in candidates:
        if (HERE / c).exists():
            return str(HERE / c)
    raise FileNotFoundError(f"Could not find any of these scripts: {candidates}")


def run(cmd: list[str], cwd: Path = HERE) -> None:
    print("\n>>>", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=str(cwd))


def main() -> None:
    # ---- 1) Two-stage extraction (OM -> QEX)
    run([
        sys.executable,
        pick_script("run_twostage_extraction.py"),
        "--keys", *PILOT_KEYS,
        "--output", "outputs/twostage",
    ])

    # ---- 2) Build Quant Extraction Form from Stage 2 CSV
    qex_csv = HERE / "outputs/twostage/stage2_qex/extracted_data.csv"
    master_csv = REPO_ROOT / "data/raw/Master file of included studies (n=114) 11 Nov(data).csv"

    auto_quant_csv = HERE / "outputs/twostage/stage2_qex/quant_extraction_form_AUTO_pilot.csv"

    run([
        sys.executable,
        pick_script("build_quant_extraction_form.py", "src/build_quant_extraction_form.py"),
        "--qex-csv", str(qex_csv),
        "--master-csv", str(master_csv),
        "--out-csv", str(auto_quant_csv),
    ])

    # ---- 3) Add numeric StudyID mapping (StudyID_GT)
    metadata_csv = REPO_ROOT / "data/raw/fulltext_metadata.csv"
    auto_with_ids_csv = HERE / "outputs/twostage/stage2_qex/quant_extraction_form_AUTO_pilot_with_ids.csv"

    run([
        sys.executable,
        pick_script("add_numeric_studyid_to_auto.py", "src/add_numeric_studyid_to_auto.py"),
        "--auto-csv", str(auto_quant_csv),
        "--metadata-csv", str(metadata_csv),
        "--out-csv", str(auto_with_ids_csv),
    ])

    # ---- 4) Evaluate AUTO vs GT
    gt_csv = REPO_ROOT / "data/human_extraction/quant_extraction_form_GT.csv"

    run([
        sys.executable,
        pick_script("evaluate_study_level_auto_vs_gt.py", "src/evaluate_study_level_auto_vs_gt.py"),
        "--auto-csv", str(auto_with_ids_csv),
        "--gt-csv", str(gt_csv),
    ])

    print("\nDone.")
    print(f"Stage 2 extracted CSV: {qex_csv}")
    print(f"AUTO quant form:       {auto_quant_csv}")
    print(f"AUTO + IDs:            {auto_with_ids_csv}")


if __name__ == "__main__":
    main()
