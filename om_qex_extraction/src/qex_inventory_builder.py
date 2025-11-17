from __future__ import annotations

from typing import Any, Dict, List, Optional


def build_qex_inventory_from_normalized_table(
    normalized_table: Dict[str, Any],
    om_outcome_id: Optional[str] = None,
    outcome_family: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Turn a normalized regression table (like ABM Table 7) into a QEX 'analysis inventory'.

    normalized_table: output of normalize_abm_income_table_t7(...), i.e.:
        {
          "study_id": "...",
          "table_id": "...",
          "caption": "...",
          "estimators": ["IV", "RE"],
          "n": {"IV": 1005.0, "RE": 854.0},
          "rows": [
            {
              "row_id": "T7_row1",
              "variable_label": "...",
              "raw_label_lines": [...],
              "effects": {
                "IV": {
                  "estimator_label": "IV",
                  "estimate": ...,
                  "se": ...,
                  "aux_label": "SD of CG",
                  "aux_value": ...
                },
                "RE": {
                  "estimator_label": "RE",
                  "estimate": ...,
                  "se": ...,
                  "aux_label": "SD of BL",
                  "aux_value": ...
                }
              }
            },
            ...
          ],
          "notes": "...",
          "header_rows": [...]
        }

    Returns:
        {
          "study_id": "...",
          "table_id": "...",
          "outcome_family": "...",
          "om_outcome_id": "... or null",
          "caption": "...",
          "notes": "...",
          "header_rows": [...],
          "analyses": [
            {
              "analysis_id": "...",
              "study_id": "...",
              "table_id": "...",
              "row_id": "...",
              "estimator": "IV" | "RE",
              "outcome_label": "...",
              "om_outcome_id": "... or null",
              "effect_metric": "raw_scale",
              "estimate": <float>,
              "se": <float>,
              "n_total": <float or null>,
              "extra_metrics": { "SD of CG": 0.24, ... },
              "notes": ""
            },
            ...
          ]
        }
    """
    study_id = normalized_table.get("study_id", "")
    table_id = normalized_table.get("table_id", "")
    caption = normalized_table.get("caption")
    estimators: List[str] = list(normalized_table.get("estimators", []))
    n_dict: Dict[str, Any] = normalized_table.get("n", {})
    notes = normalized_table.get("notes")
    header_rows = normalized_table.get("header_rows", [])

    analyses: List[Dict[str, Any]] = []

    for row in normalized_table.get("rows", []):
        row_id = row.get("row_id")
        variable_label = row.get("variable_label")

        effects = row.get("effects", {})
        for est_key in estimators:
            eff = effects.get(est_key, {}) or {}
            est_label = eff.get("estimator_label", est_key)

            estimate = eff.get("estimate")
            se = eff.get("se")

            # If we don't have both estimate and se, skip this analysis
            if estimate is None or se is None:
                continue

            n_total = n_dict.get(est_key)

            # Pull auxiliary metric (e.g., "SD of CG", "SD of BL") into extra_metrics
            aux_label = eff.get("aux_label")
            aux_value = eff.get("aux_value")

            extra_metrics: Dict[str, Any] = {}
            if aux_label is not None and aux_value is not None:
                # Use the header label as the key, so we don't hard-code semantics
                extra_metrics[str(aux_label)] = aux_value

            analysis_id = f"{study_id}_{table_id}_{row_id}_{est_key}"

            analyses.append(
                {
                    "analysis_id": analysis_id,
                    "study_id": study_id,
                    "table_id": table_id,
                    "row_id": row_id,
                    "estimator": est_label,
                    "outcome_label": variable_label,
                    "om_outcome_id": om_outcome_id,
                    # Natural outcome scale; semantics can be refined later.
                    "effect_metric": "raw_scale",
                    "estimate": estimate,
                    "se": se,
                    "n_total": n_total,
                    "extra_metrics": extra_metrics,
                    "notes": "",
                }
            )

    return {
        "study_id": study_id,
        "table_id": table_id,
        "outcome_family": outcome_family,
        "om_outcome_id": om_outcome_id,
        "caption": caption,
        "notes": notes,
        "header_rows": header_rows,
        "analyses": analyses,
    }
