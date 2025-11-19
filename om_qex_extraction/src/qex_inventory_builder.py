from typing import Any, Dict, List, Optional


def _build_extra_metrics_from_effect(effect: Dict[str, Any]) -> Dict[str, Any]:
    extra: Dict[str, Any] = {}
    if "aux_label" in effect and effect.get("aux_value") is not None:
        extra[str(effect["aux_label"])] = effect["aux_value"]
    if "sd" in effect and effect.get("sd") is not None:
        extra["sd"] = effect["sd"]
    return extra


def build_qex_inventory_from_normalized_table(table: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a normalized table (ABM pattern or TEEP pattern) into a flat QEX inventory.

    Unified row schema:

      analysis_id
      study_id
      table_id
      row_id
      column_index
      column_tag
      outcome_label
      om_outcome_id
      arm_label
      contrast_label
      estimator
      effect_metric
      estimate
      se
      n_total
      extra_metrics
      notes
    """
    study_id = table["study_id"]
    table_id = table["table_id"]
    notes = table.get("notes", "")

    analyses: List[Dict[str, Any]] = []

    # -------- Case 1: ABM-style (estimators IV/RE, outcomes in rows) --------
    if "estimators" in table:
        estimators: List[str] = table["estimators"]
        n_dict: Dict[str, Any] = table.get("n", {})

        for row in table["rows"]:
            row_id = row["row_id"]
            outcome_label = row["variable_label"]
            effects: Dict[str, Dict[str, Any]] = row["effects"]

            for est_name in estimators:
                effect = effects.get(est_name)
                if effect is None:
                    continue

                analysis_id = f"{study_id}_{table_id}_{row_id}_{est_name}"

                analyses.append(
                    {
                        "analysis_id": analysis_id,
                        "study_id": study_id,
                        "table_id": table_id,
                        "row_id": row_id,
                        "column_index": None,
                        "column_tag": None,
                        "outcome_label": outcome_label,
                        "om_outcome_id": None,
                        "arm_label": None,
                        "contrast_label": None,
                        "estimator": est_name,
                        "effect_metric": "raw_scale",
                        "estimate": effect.get("estimate"),
                        "se": effect.get("se"),
                        "n_total": n_dict.get(est_name),
                        "extra_metrics": _build_extra_metrics_from_effect(effect),
                        "notes": notes,
                    }
                )

    # -------- Case 2: TEEP-style (arms in rows, outcomes in columns) --------
    elif "columns" in table:
        n_total: Optional[int] = table.get("n")

        for row in table["rows"]:
            row_id = row["row_id"]
            outcome_label = row["outcome_label"]
            col_index = row["column_index"]
            col_tag = row.get("column_tag")
            arm_label = row["group_label"]

            analysis_id = f"{study_id}_{table_id}_{row_id}"

            analyses.append(
                {
                    "analysis_id": analysis_id,
                    "study_id": study_id,
                    "table_id": table_id,
                    "row_id": row_id,
                    "column_index": col_index,
                    "column_tag": col_tag,
                    "outcome_label": outcome_label,
                    "om_outcome_id": None,
                    "arm_label": arm_label,
                    "contrast_label": None,
                    "estimator": None,  # fill with "OLS" or similar later if you want
                    "effect_metric": "raw_scale",
                    "estimate": row.get("estimate"),
                    "se": row.get("se"),
                    "n_total": n_total,
                    "extra_metrics": {},
                    "notes": notes,
                }
            )

    else:
        raise ValueError(f"Unsupported normalized table format for table_id={table_id}")

    return {
        "study_id": study_id,
        "table_id": table_id,
        "analyses": analyses,
    }
