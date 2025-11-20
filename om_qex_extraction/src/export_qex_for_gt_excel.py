# om_qex_extraction/src/export_qex_for_gt_excel.py

import json
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd


def load_qex_analyses(path: Path) -> List[Dict[str, Any]]:
    """
    Load a QEX inventory JSON file and return a flat list of analyses.

    Supports two shapes:
      1) Dict with top-level 'analyses' key  (e.g., TEEP files)
      2) List of table dicts, each with its own 'analyses' key (e.g., ABM file)
    """
    data = json.loads(path.read_text(encoding="utf-8"))

    analyses: List[Dict[str, Any]] = []

    if isinstance(data, dict) and "analyses" in data:
        # Single table inventory
        for a in data["analyses"]:
            analyses.append(a)

    elif isinstance(data, list):
        # List of table inventories (ABM)
        for table_block in data:
            if isinstance(table_block, dict) and "analyses" in table_block:
                for a in table_block["analyses"]:
                    analyses.append(a)

    return analyses


def main():
    repo_root = Path(".").resolve()
    qex_dir = repo_root / "data" / "qex_mvp"

    if not qex_dir.exists():
        raise SystemExit(f"QEX directory not found: {qex_dir}")

    # Grab any JSON with 'qex' in the name
    candidate_files = sorted(qex_dir.glob("*qex*.json"))
    if not candidate_files:
        raise SystemExit(f"No qex-related JSON files found in {qex_dir}")

    all_rows: List[Dict[str, Any]] = []
    used_files: List[Path] = []

    for fp in candidate_files:
        try:
            analyses = load_qex_analyses(fp)
        except Exception as e:
            print(f"Skipping {fp.name} due to error: {e}")
            continue

        if not analyses:
            continue

        used_files.append(fp)
        print(f"Loaded {len(analyses)} analyses from {fp.name}")

        for a in analyses:
            row = {
                # Core QEX fields from the pipeline
                "study_id": a.get("study_id"),
                "analysis_id": a.get("analysis_id"),
                "table_id": a.get("table_id"),
                "row_id": a.get("row_id"),
                "arm_label": a.get("arm_label"),
                "contrast_label": a.get("contrast_label"),
                "estimator": a.get("estimator"),
                "effect_metric": a.get("effect_metric"),
                "outcome_label": a.get("outcome_label"),
                "om_outcome_id": a.get("om_outcome_id"),
                "estimate": a.get("estimate"),
                "se": a.get("se"),
                "n_total": a.get("n_total"),

                # GT annotation fields (to be filled by you)
                "gt_is_valid": "",            # 1 = usable analysis, 0 = not
                "gt_is_preferred_spec": "",   # 1 = preferred spec in cluster

                "gt_outcome_group": "",       # optional; outcome family label
                "gt_effect_type": "",         # IV / RE / OLS / ITT / TOT, etc.
                "gt_notes": "",               # free text rationale

                # Optional numeric GT (fill only when you verify)
                "gt_estimate": "",            # numeric ground truth
                "gt_se": "",
                "gt_n_total": "",
            }
            all_rows.append(row)

    if not used_files:
        raise SystemExit(
            f"No usable QEX inventory JSONs found in {qex_dir} (no analyses)."
        )

    print("\nUsing QEX inventory files:")
    for fp in used_files:
        print(f"  - {fp.relative_to(repo_root)}")

    if not all_rows:
        raise SystemExit("No analyses collected from any QEX inventory JSONs.")

    df = pd.DataFrame(all_rows)
    df = df.sort_values(by=["study_id", "table_id", "row_id", "analysis_id"])

    out_path = qex_dir / "GT_QEX_ABM_TEEP_seed.xlsx"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(out_path, index=False)

    print(f"\nWrote GT Excel seed to: {out_path}")
    print("Open this in Excel or Sheets and annotate the GT_* columns.")


if __name__ == "__main__":
    main()
