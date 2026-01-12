"""
Extraction Engine - LLM-based data extraction from research papers.

Key goals for this rebuild
- Enforce structured JSON outputs via OpenRouter `response_format` (json_schema / strict) for QEX.
- Robustly parse/repair "almost JSON" responses (code fences, stray text, invalid control characters).
- Never crash on common model quirks (e.g., "…existing fields remain unchanged", list-like timepoint values).
- Preserve the existing public API used by run_twostage_extraction.py:
  - ExtractionEngine.extract_from_tei(...)
  - ExtractionEngine.extract_with_om_guidance(...)
  - ExtractionEngine.extract_batch(...)
  - load_metadata_from_master(...)
  - save_results(...)
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from openai import OpenAI

from .tei_parser import TEIParser

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# ----------------------------
# Utilities
# ----------------------------

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)


def _now_ms() -> int:
    return int(time.time() * 1000)


def _to_number_or_none(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        if isinstance(x, bool):
            return None
        if isinstance(x, (int, float)):
            return float(x)
        if isinstance(x, str):
            s = x.strip()
            if s == "" or s.lower() in {"na", "n/a", "null", "none"}:
                return None
            # remove commas in numbers like "1,234"
            s = s.replace(",", "")
            return float(s)
        return None
    except Exception:
        return None


def _months_from_value_unit(value: Any, unit: Any) -> Optional[float]:
    v = _to_number_or_none(value)
    if v is None:
        return None
    if not isinstance(unit, str):
        return None
    u = unit.strip().lower()
    if u in {"month", "months"}:
        return v
    if u in {"year", "years"}:
        return v * 12.0
    if u in {"week", "weeks"}:
        return v * (12.0 / 52.0)
    if u in {"day", "days"}:
        return v * (12.0 / 365.0)
    return None


# ----------------------------
# Extraction Engine
# ----------------------------

@dataclass
class _LLMCallResult:
    data: Dict[str, Any]
    raw_text: str
    used_response_format: bool
    provider_error: Optional[str] = None


class ExtractionEngine:
    """
    Modes:
      - "om": Outcome mapping (Stage 1)
      - "qex": Quant extraction (Stage 2)
    """

    def __init__(self, config_path: Path, mode: str = "qex", model_override: Optional[str] = None):
        self.config_path = Path(config_path)
        self.mode = mode.lower().strip()
        if self.mode not in {"om", "qex"}:
            raise ValueError(f"mode must be 'om' or 'qex', got: {mode}")

        self.config = self._load_config()

        # Model selection: allow override, else config.model[mode]
        cfg_model = (self.config.get("model") or {}).get(self.mode)
        self.model = model_override or cfg_model
        if not self.model:
            raise ValueError(f"No model configured for mode={self.mode}. Set config.model.{self.mode}")

        self.client = self._initialize_client()

        # Prompt loading
        self.prompts_dir = (Path(__file__).resolve().parent.parent / "prompts")
        self.prompt_template = self._load_prompt_template()

        logger.info(
            f"Initialized ExtractionEngine in {self.mode.upper()} mode with model: {self.model}"
        )

    # ----------------------------
    # Config / client
    # ----------------------------

    def _load_config(self) -> Dict[str, Any]:
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _initialize_client(self) -> OpenAI:
        # OpenRouter uses the OpenAI-compatible client with a custom base_url.
        # We support api_key in config or env var.
        api_cfg = (self.config.get("api") or {}).get("openrouter") or {}
        api_key = api_cfg.get("api_key") or os.getenv("OPENROUTER_API_KEY") or ""
        api_key = str(api_key).strip()

        # Allow "environment variable format" placeholders: ${OPENROUTER_API_KEY}
        if api_key.startswith("${") and api_key.endswith("}"):
            env_name = api_key[2:-1].strip()
            api_key = os.getenv(env_name, "").strip()

        if not api_key:
            raise ValueError(
                "OpenRouter API key not found. Set config.api.openrouter.api_key "
                "or environment variable OPENROUTER_API_KEY."
            )

        base_url = api_cfg.get("base_url", "https://openrouter.ai/api/v1")
        logger.info(f"OpenRouter client initialized with base URL: {base_url}")
        return OpenAI(api_key=api_key, base_url=base_url)

    # ----------------------------
    # Prompts
    # ----------------------------

    def _load_prompt_template(self) -> str:
        """
        Loads the appropriate prompt file for the engine mode.
        - OM default: prompts/om_extraction_prompt.txt
        - QEX default: prompts/extraction_prompt.txt (single-stage) or prompts/qex_focused_prompt.txt (two-stage)
        """
        prompt_cfg = (self.config.get("extraction") or {}).get("prompt_file")
        if prompt_cfg:
            candidate = Path(prompt_cfg)
            if not candidate.is_absolute():
                candidate = self.prompts_dir / candidate
            if candidate.exists():
                return candidate.read_text(encoding="utf-8")

        if self.mode == "om":
            candidates = [
                self.prompts_dir / "om_extraction_prompt.txt",
                self.prompts_dir / "om_extraction_prompt_arch2.txt",
            ]
        else:
            candidates = [
                self.prompts_dir / "extraction_prompt.txt",
                self.prompts_dir / "extraction_prompt_arch2.txt",
            ]

        for p in candidates:
            if p.exists():
                return p.read_text(encoding="utf-8")

        raise FileNotFoundError(
            f"Could not find a prompt template for mode={self.mode}. "
            f"Looked in: {self.prompts_dir}"
        )

    def _load_qex_focused_prompt(self) -> str:
        candidates = [
            self.prompts_dir / "qex_focused_prompt.txt",
            self.prompts_dir / "qex_focused_prompt_arch2.txt",
        ]
        for p in candidates:
            if p.exists():
                return p.read_text(encoding="utf-8")
        raise FileNotFoundError(
            f"Could not find qex focused prompt. Looked in: {self.prompts_dir}"
        )

    # ----------------------------
    # Structured outputs
    # ----------------------------

    def _qex_json_schema(self) -> Dict[str, Any]:
        """
        Minimal-yet-useful schema:
        - Requires top-level `outcomes` array.
        - Requires timing fields per outcome, but allows nulls.
        - Allows either a scalar or an array for timepoint_value/months_since_intervention_end_computed to avoid hard-failing
          on multi-wave papers; downstream code will canonicalize.
        """
        num_or_numarr = {
            "anyOf": [
                {"type": "number"},
                {"type": "array", "items": {"type": "number"}},
                {"type": "null"},
            ]
        }
        str_or_null = {"type": ["string", "null"]}
        int_or_null = {"type": ["integer", "null"]}
        return {
            "type": "object",
            "additionalProperties": True,
            "properties": {
                # Study-level fields (mostly optional)
                "study_id": str_or_null,
                "program_name": str_or_null,
                "country": str_or_null,
                "year_intervention_started": int_or_null,
                "evaluation_design": str_or_null,
                "evaluation_design_code": str_or_null,
                "evaluation_method": str_or_null,
                "evaluation_method_code": str_or_null,
                "intervention_description": str_or_null,
                "exposure_to_intervention": str_or_null,
                "length_of_follow_up": str_or_null,
                "intervention_start_year": int_or_null,
                "intervention_start_month": int_or_null,
                "intervention_end_year": int_or_null,
                "intervention_end_month": int_or_null,
                "final_followup_year": int_or_null,
                "final_followup_month": int_or_null,
                "timing_anchors": {"type": ["object", "null"], "additionalProperties": True},
                "notes": str_or_null,
                # Outcomes
                "outcomes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": True,
                        "properties": {
                            "outcome_name": str_or_null,
                            "outcome_description": str_or_null,
                            "sample_size_treatment": str_or_null,
                            "sample_size_control": str_or_null,
                            "effect_size": str_or_null,
                            "p_value": str_or_null,
                            "standard_error": str_or_null,
                            "confidence_interval_lower": str_or_null,
                            "confidence_interval_upper": str_or_null,
                            "literal_text": str_or_null,
                            "text_position": str_or_null,
                            "outcome_timepoint_label": str_or_null,
                            "outcome_measurement_year": int_or_null,
                            "outcome_measurement_month": int_or_null,
                            "months_since_intervention_end": str_or_null,
                            "timepoint_value": num_or_numarr,
                            "timepoint_unit": {"type": ["string", "null"]},
                            "timepoint_origin": {"type": ["string", "null"]},
                            "months_since_intervention_end_computed": num_or_numarr,
                            "timing_confidence": {"type": ["string", "null"]},
                            "timing_evidence": {"type": ["string", "null"]},
                            "outcome_timing_literal_text": {"type": ["string", "null"]},
                            "outcome_timing_text_position": {"type": ["string", "null"]},
                        },
                        "required": [
                            "outcome_name",
                            "timepoint_origin",
                            "timing_confidence",
                            "timing_evidence",
                            "timepoint_value",
                            "timepoint_unit",
                            "months_since_intervention_end_computed",
                        ],
                    },
                },
            },
            "required": ["outcomes"],
        }

    def _build_response_format(self) -> Dict[str, Any]:
        """
        OpenRouter response_format payload. We only apply this for QEX.
        Some providers reject json_schema; caller will fall back.
        """
        schema = self._qex_json_schema()
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "qex_extraction",
                "strict": True,
                "schema": schema,
            },
        }

    # ----------------------------
    # JSON sanitization / parsing
    # ----------------------------

    def _strip_code_fences(self, text: str) -> str:
        m = _JSON_FENCE_RE.search(text)
        if m:
            return m.group(1).strip()
        return text.strip()

    def _extract_first_json_object(self, text: str) -> str:
        """
        Extract the first top-level JSON object/array from mixed text.
        This is robust to preambles like "Sure! Here's the JSON:".
        """
        s = text.strip()
        # Fast path: already looks like JSON
        if s.startswith("{") and s.endswith("}"):
            return s
        if s.startswith("[") and s.endswith("]"):
            return s

        # Find first '{' or '[' and parse bracket matching
        start_idx = None
        opener = None
        for i, ch in enumerate(s):
            if ch in "{[":
                start_idx = i
                opener = ch
                break
        if start_idx is None:
            return s

        closer = "}" if opener == "{" else "]"
        depth = 0
        in_str = False
        esc = False
        for j in range(start_idx, len(s)):
            ch = s[j]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            else:
                if ch == '"':
                    in_str = True
                    continue
                if ch == opener:
                    depth += 1
                elif ch == closer:
                    depth -= 1
                    if depth == 0:
                        return s[start_idx : j + 1].strip()

        return s[start_idx:].strip()

    def _sanitize_json_text(self, text: str) -> str:
        """
        Clean common non-JSON artifacts before json.loads:
        - code fences
        - placeholder tokens: "...existing fields remain unchanged"
        - JS-style ellipses / trailing commas
        - smart quotes
        """
        s = text or ""
        s = self._strip_code_fences(s)
        s = self._extract_first_json_object(s)

        # Remove well-known "placeholder" fragments the model sometimes emits
        s = re.sub(r"\.\.\.\s*existing fields remain unchanged", "", s, flags=re.IGNORECASE)
        s = re.sub(r"\u2026\s*existing fields remain unchanged", "", s, flags=re.IGNORECASE)

        # Replace smart quotes with straight quotes
        s = s.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")

        # Remove trailing commas before } or ]
        s = re.sub(r",\s*([}\]])", r"\1", s)

        return s.strip()

    def _escape_control_chars_in_strings(self, text: str) -> str:
        """
        Escape unescaped control characters inside JSON string literals
        (e.g., raw newlines embedded in a quoted string) which cause:
        json.JSONDecodeError: Invalid control character.
        """
        s = text
        out: List[str] = []
        in_str = False
        esc = False
        for ch in s:
            if not in_str:
                if ch == '"':
                    in_str = True
                    out.append(ch)
                else:
                    out.append(ch)
                continue

            # in_str:
            if esc:
                out.append(ch)
                esc = False
                continue

            if ch == "\\":
                out.append(ch)
                esc = True
                continue

            if ch == '"':
                out.append(ch)
                in_str = False
                continue

            code = ord(ch)
            if code < 0x20:
                # Control char inside string: escape it
                if ch == "\n":
                    out.append("\\n")
                elif ch == "\r":
                    out.append("\\r")
                elif ch == "\t":
                    out.append("\\t")
                else:
                    out.append("\\u%04x" % code)
            else:
                out.append(ch)

        return "".join(out)

    def _json_loads_with_repairs(self, raw_text: str) -> Dict[str, Any]:
        """
        Attempt json.loads with increasingly aggressive repairs.
        Raises JSONDecodeError on final failure.
        """
        s0 = self._sanitize_json_text(raw_text)

        try:
            return json.loads(s0)
        except json.JSONDecodeError as e1:
            # Invalid control characters are common; escape then retry.
            s1 = self._escape_control_chars_in_strings(s0)
            try:
                return json.loads(s1)
            except json.JSONDecodeError:
                # As a last resort, remove any ASCII control chars outside strings too.
                s2 = re.sub(r"[\x00-\x1f]", "", s1)
                return json.loads(s2)

    def _canonicalize_timing_fields(self, qex: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make timing fields safe and downstream-friendly:
        - Convert list-like timepoint_value / months_since_intervention_end_computed to a scalar
          (heuristic: take max value, and annotate label if needed).
        - If months_since_intervention_end_computed missing but timepoint_value+unit+origin exist,
          compute it for origin == intervention_end.
        """
        outcomes = qex.get("outcomes") or []
        if not isinstance(outcomes, list):
            return qex

        for o in outcomes:
            if not isinstance(o, dict):
                continue

            # Convert arrays to scalar (max) to avoid object dtype downstream
            for fld in ["timepoint_value", "months_since_intervention_end_computed"]:
                v = o.get(fld)
                if isinstance(v, list) and v:
                    # pick max (conservative: longest follow-up)
                    try:
                        o[fld] = float(max(v))
                        # mark label if it was multi
                        lbl = o.get("outcome_timepoint_label")
                        if not lbl:
                            o["outcome_timepoint_label"] = "Multiple timepoints (max used)"
                    except Exception:
                        pass

            # If computed months absent, compute when origin is intervention_end
            if _to_number_or_none(o.get("months_since_intervention_end_computed")) is None:
                origin = (o.get("timepoint_origin") or "").strip().lower()
                if origin == "intervention_end":
                    m = _months_from_value_unit(o.get("timepoint_value"), o.get("timepoint_unit"))
                    if m is not None:
                        o["months_since_intervention_end_computed"] = float(round(m, 0))

        return qex

    # ----------------------------
    # LLM calling
    # ----------------------------

    def _call_llm(self, prompt: str, *, use_response_format: bool = True) -> _LLMCallResult:
        """
        Calls OpenRouter chat.completions. For QEX we attempt structured output first;
        if the provider rejects response_format, we automatically fall back.
        """
        # Config defaults
        ex_cfg = self.config.get("extraction") or {}
        temperature = ex_cfg.get("temperature", 0.0)
        max_tokens = ex_cfg.get("max_tokens", 4000)

        system_msg = (
            "You are a precise information extraction engine. "
            "Return ONLY valid JSON. Do not include commentary, markdown, or placeholders."
        )

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt},
        ]

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        used_rf = False
        if self.mode == "qex" and use_response_format:
            kwargs["response_format"] = self._build_response_format()
            used_rf = True

        last_err: Optional[str] = None
        last_raw: str = ""

        retries = int(ex_cfg.get("retries", 3))
        backoff = float(ex_cfg.get("retry_backoff_seconds", 2.0))

        for attempt in range(1, retries + 1):
            try:
                resp = self.client.chat.completions.create(**kwargs)
                # OpenAI compatible: resp.choices[0].message.content
                content = resp.choices[0].message.content
                last_raw = content if isinstance(content, str) else json.dumps(content)
                data = self._json_loads_with_repairs(last_raw)
                if self.mode == "qex":
                    data = self._canonicalize_timing_fields(data)
                return _LLMCallResult(data=data, raw_text=last_raw, used_response_format=used_rf)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                last_err = str(e)
                # Common OpenRouter/provider error when response_format is unsupported
                if used_rf and ("response_format" in last_err or "json_schema" in last_err or "Invalid" in last_err):
                    logger.warning(
                        f"Provider rejected response_format; retrying without structured outputs. Error: {last_err}"
                    )
                    kwargs.pop("response_format", None)
                    used_rf = False
                    # Immediately retry without counting against retries budget too harshly
                    continue

                logger.error(f"LLM call failed (attempt {attempt}/{retries}): {last_err}")
                if attempt < retries:
                    time.sleep(backoff * attempt)

        # If we get here, we failed all attempts
        raise RuntimeError(f"LLM call failed after {retries} attempts. Last error: {last_err}. Raw head: {last_raw[:500]}")

    # ----------------------------
    # Public API
    # ----------------------------

    def extract_from_tei(self, tei_file: Path, paper_metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Single-stage extraction (OM or QEX) using the mode's prompt_template.
        """
        tei_file = Path(tei_file)
        logger.info(f"Processing: {tei_file.name}")

        try:
            parser = TEIParser(tei_file)
            paper_text = parser.get_full_text(include_abstract=True)
        except Exception as e:
            logger.error(f"Failed to parse TEI file {tei_file.name}: {e}")
            return None

        prompt = self.prompt_template.replace("{paper_text}", paper_text)

        try:
            result = self._call_llm(prompt, use_response_format=(self.mode == "qex"))
            extraction = result.data
            if paper_metadata:
                extraction.update(paper_metadata)
            logger.info(f"✅ Successfully extracted data from {tei_file.name}")
            return extraction
        except Exception as e:
            logger.error(f"Extraction failed for {tei_file.name}: {e}")
            return None

    def extract_with_om_guidance(
        self,
        tei_file: Path,
        paper_metadata: Optional[Dict[str, Any]] = None,
        om_outcomes: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Two-stage QEX extraction with OM guidance. This method:
        - loads prompts/qex_focused_prompt*.txt
        - injects {om_guidance} and {paper_text}
        - calls the LLM with structured outputs if supported
        """
        tei_file = Path(tei_file)
        logger.info(f"Processing with OM guidance: {tei_file.name}")

        # Parse TEI file
        try:
            parser = TEIParser(tei_file)
            paper_text = parser.get_full_text(include_abstract=True)
        except Exception as e:
            logger.error(f"Failed to parse TEI file {tei_file.name}: {e}")
            return None

        # Build OM guidance string
        guidance_lines: List[str] = []
        om_outcomes = om_outcomes or []
        guidance_lines.append("OM GUIDANCE (Outcome Mapping Results):")
        guidance_lines.append("Use the guidance below to focus extraction on the listed outcomes.")
        guidance_lines.append("For each outcome below, extract full statistical details and outcome-specific timing.")
        guidance_lines.append("")
        for i, outcome in enumerate(om_outcomes, 1):
            if not isinstance(outcome, dict):
                continue
            guidance_lines.append(f"{i}. {outcome.get('outcome_category', outcome.get('outcome_name', 'Unknown'))}")
            guidance_lines.append(f"   Location: {outcome.get('location', 'Not specified')}")
            lit = outcome.get("literal_text")
            if lit:
                guidance_lines.append(f"   Text: {lit}")
            # optional timing hints from OM
            for k in ["timepoint_label", "outcome_timepoint_label"]:
                if outcome.get(k):
                    guidance_lines.append(f"   Timepoint: {outcome.get(k)}")
                    break
            for k in ["timepoint_months_since_intervention_end", "months_since_intervention_end"]:
                if outcome.get(k):
                    guidance_lines.append(f"   Months since intervention end: {outcome.get(k)}")
                    break
            guidance_lines.append("")

        om_guidance = "\n".join(guidance_lines).strip()

        # Create focused prompt
        try:
            focused_template = self._load_qex_focused_prompt()
        except Exception as e:
            logger.error(f"Could not load qex focused prompt: {e}")
            return None

        prompt = focused_template.replace("{paper_text}", paper_text).replace("{om_guidance}", om_guidance)

        # Call LLM
        try:
            logger.info(f"Created focused prompt with OM guidance ({len(om_outcomes)} outcomes)")
            logger.info("Calling LLM with focused prompt...")
            result = self._call_llm(prompt, use_response_format=True)
            extraction = result.data
            if paper_metadata:
                extraction.update(paper_metadata)
            logger.info(f"✅ Successfully extracted QEX data from {tei_file.name}")
            return extraction
        except Exception as e:
            logger.error(f"QEX extraction failed for {tei_file.name}: {e}")
            return None

    def extract_batch(
        self,
        tei_files: List[Path],
        metadata_map: Optional[Dict[str, Dict[str, Any]]] = None,
        output_dir: Optional[Path] = None,
    ) -> List[Dict[str, Any]]:
        """
        Batch extraction helper used by run scripts.
        """
        results: List[Dict[str, Any]] = []
        success = 0

        for tei_file in tei_files:
            tei_file = Path(tei_file)
            key = tei_file.name.replace(".tei.xml", "")

            md = metadata_map.get(key) if metadata_map else None
            data = self.extract_from_tei(tei_file, md)
            if data:
                results.append(data)
                success += 1

        logger.info("\n============================================================")
        logger.info(f"Extraction complete: {success}/{len(tei_files)} successful")
        logger.info("============================================================")
        return results
    def save_results(self, results, output_dir: Path):
        """
        Backward-compatible instance method expected by run_twostage_extraction.py.

        Writes:
        - output_dir/json/<key>.json  (one file per paper)
        - output_dir/extracted_data.csv (flattened rows, one per outcome/estimate)
        """
        import json
        from pathlib import Path

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 1) Write per-paper JSONs
        json_dir = output_dir / "json"
        json_dir.mkdir(parents=True, exist_ok=True)

        for i, r in enumerate(results or []):
            key = r.get("_key") or r.get("key") or f"result_{i:04d}"
            out_path = json_dir / f"{key}.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(r, f, ensure_ascii=False, indent=2, default=str)

        # 2) Write flattened CSV using the module-level save_results() helper
        # IMPORTANT: this calls the *module-level* function named save_results,
        # not this method (Python resolves this name in module globals).
        csv_path = output_dir / "extracted_data.csv"
        save_results(results, csv_path)

# ----------------------------
# Metadata loading / output
# ----------------------------

def load_metadata_from_master(master_csv: Path) -> Dict[str, Dict[str, Any]]:
    """
    Load metadata from the master CSV into a dict keyed by TEI key (no extension).
    The master file schema can vary; we look for common columns.
    """
    import pandas as pd

    master_csv = Path(master_csv)
    df = pd.read_csv(master_csv, dtype=str, encoding_errors="replace")

    # Candidate columns (robust to different naming conventions)
    col_key = None
    for c in df.columns:
        if c.strip().lower() in {"key", "_key", "tei_key", "paper_key"}:
            col_key = c
            break
    if col_key is None:
        # fallback: if there's an xml filename column
        for c in df.columns:
            if "tei" in c.lower() and "xml" in c.lower():
                col_key = c
                break
    if col_key is None:
        raise ValueError("Could not find a key column in master CSV (expected 'Key' or similar).")

    def pick(*names: str) -> Optional[str]:
        for n in names:
            if n in df.columns:
                return n
        return None

    col_study_id = pick("paper_id", "StudyID", "study_id", "studyid")
    col_author = pick("Author", "author", "author_name")
    col_year = pick("Publication Year", "year", "Year", "pub_year")
    col_country = pick("Country", "country")

    metadata_map: Dict[str, Dict[str, Any]] = {}
    for _, row in df.iterrows():
        k = str(row[col_key]).strip()
        if not k or k.lower() in {"nan", "none"}:
            continue
        k = k.replace(".tei", "").replace(".tei.xml", "")

        md: Dict[str, Any] = {}
        if col_study_id and str(row.get(col_study_id, "")).strip():
            md["study_id"] = str(row.get(col_study_id)).strip()
        if col_author and str(row.get(col_author, "")).strip():
            md["author_name"] = str(row.get(col_author)).strip()
        if col_year and str(row.get(col_year, "")).strip():
            md["year_of_publication"] = str(row.get(col_year)).strip()
        if col_country and str(row.get(col_country, "")).strip():
            md["country"] = str(row.get(col_country)).strip()

        metadata_map[k] = md

    return metadata_map


def save_results(results: List[Dict[str, Any]], output_file: Path) -> None:
    """
    Flatten results (including outcome rows) to CSV.
    This mirrors the existing repo behavior: one row per outcome/estimate when possible.
    """
    import pandas as pd

    rows: List[Dict[str, Any]] = []
    for r in results:
        if not isinstance(r, dict):
            continue

        base = {k: v for k, v in r.items() if k != "outcomes"}
        outcomes = r.get("outcomes") or []
        if isinstance(outcomes, list) and outcomes:
            for o in outcomes:
                if isinstance(o, dict):
                    row = dict(base)
                    row.update(o)
                    rows.append(row)
        else:
            rows.append(base)

    df = pd.DataFrame(rows)

    # Optional: coerce key columns
    if "_key" not in df.columns and "Key" in df.columns:
        df["_key"] = df["Key"]

    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)
    logger.info(f"Saved {len(df)} rows to: {output_file}")
