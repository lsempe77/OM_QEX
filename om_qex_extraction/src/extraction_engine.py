"""
Extraction Engine - LLM-based data extraction from research papers.
Uses OpenRouter API to extract structured data from TEI XML papers.
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, Optional, List
import yaml
from openai import OpenAI

from .tei_parser import TEIParser
from .models import ExtractionRecord, PublicationInfo, InterventionInfo, GeneralInfo
from .models import MethodInfo, OutcomeInfo, TreatmentVariableInfo, EstimateInfo, EstimateData


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ExtractionEngine:
    """LLM-based extraction engine using OpenRouter."""
    
    def __init__(self, config_path: Path, mode: str = "qex"):
        """
        Initialize the extraction engine with configuration.
        
        Args:
            config_path: Path to config.yaml
            mode: Extraction mode - "om" for outcome mapping or "qex" for quantitative extraction
        """
        self.config_path = Path(config_path)
        self.mode = mode.lower()
        self.config = self._load_config()
        self.client = self._initialize_client()
        self.prompt_template = self._load_prompt_template(mode=self.mode)
        
        logger.info(f"Initialized ExtractionEngine in {self.mode.upper()} mode with model: {self.config['model']['name']}")
    
    def _load_config(self) -> Dict:
        """Load configuration from YAML file."""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    
    def _initialize_client(self) -> OpenAI:
        """Initialize OpenAI client for OpenRouter."""
        from openai import Timeout
        
        api_key = self.config['api']['openrouter']['api_key']
        
        # Remove ${} wrapper if present (environment variable format)
        if api_key.startswith("${") and api_key.endswith("}"):
            api_key = api_key[2:-1]
        
        base_url = self.config['api']['openrouter']['base_url']
        
        # Create client with explicit timeout settings
        client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=Timeout(
                connect=15.0,   # 15 seconds to establish connection
                read=300.0,     # 5 minutes to read response (increased for unstable connections)
                write=15.0,     # 15 seconds to send request
                pool=15.0       # 15 seconds for connection pool
            ),
            max_retries=5  # More retries for unstable connections
        )
        
        logger.info(f"OpenRouter client initialized with base URL: {base_url}")
        return client
    
    def _load_prompt_template(self, mode: str = "qex") -> str:
        """
        Load the extraction prompt template.
        
        Args:
            mode: "om" for outcome mapping or "qex" for quantitative extraction
        """
        if mode == "om":
            prompt_file = "om_extraction_prompt.txt"
        else:
            prompt_file = "extraction_prompt.txt"
            
        prompt_path = Path(__file__).parent.parent / "prompts" / prompt_file
        with open(prompt_path, 'r', encoding='utf-8') as f:
            template = f.read()
        return template
    
    def extract_from_tei(self, tei_file: Path, paper_metadata: Optional[Dict] = None) -> Optional[Dict]:
        """
        Extract data from a TEI XML file.
        
        Args:
            tei_file: Path to TEI XML file
            paper_metadata: Optional metadata from master file (study_id, author, year, country)
        
        Returns:
            Extracted data as dictionary, or None if extraction fails
        """
        logger.info(f"Processing: {tei_file.name}")
        
        # Parse TEI file
        try:
            parser = TEIParser(tei_file)
            paper_text = parser.get_full_text(include_abstract=True)
        except Exception as e:
            logger.error(f"Failed to parse TEI file {tei_file.name}: {e}")
            return None
        
        # Create prompt
        prompt = self.prompt_template.replace("{paper_text}", paper_text)
        
        # Call LLM
        try:
            extraction = self._call_llm(prompt)
            
            # Merge with metadata if provided
            if paper_metadata:
                extraction.update(paper_metadata)
            
            logger.info(f"✅ Successfully extracted data from {tei_file.name}")
            return extraction
            
        except Exception as e:
            logger.error(f"Extraction failed for {tei_file.name}: {e}")
            return None
    
    def extract_with_om_guidance(self, tei_file: Path, paper_metadata: Optional[Dict] = None, 
                                  om_outcomes: Optional[List[Dict]] = None) -> Optional[Dict]:
        """
        Extract QEX data using OM outcomes as guidance.
        
        This is the key method for two-stage extraction. It uses OM outcomes
        to create a focused prompt that tells the LLM exactly where to look.
        
        Args:
            tei_file: Path to TEI XML file
            paper_metadata: Optional metadata from master file
            om_outcomes: List of OM outcomes with location/literal_text hints
        
        Returns:
            Extracted QEX data as dictionary, or None if extraction fails
        """
        logger.info(f"Processing with OM guidance: {tei_file.name}")
        
        # Parse TEI file
        try:
            parser = TEIParser(tei_file)
            paper_text = parser.get_full_text(include_abstract=True)
        except Exception as e:
            logger.error(f"Failed to parse TEI file {tei_file.name}: {e}")
            return None
        
        # Load focused prompt template if available, otherwise use standard
        focused_prompt_path = Path(__file__).parent.parent / "prompts" / "qex_focused_prompt.txt"
        if focused_prompt_path.exists():
            with open(focused_prompt_path, 'r', encoding='utf-8') as f:
                template = f.read()
        else:
            logger.info("Focused prompt not found, using standard QEX prompt")
            template = self.prompt_template
        
        # Create OM guidance section
        if om_outcomes and len(om_outcomes) > 0:
            om_guidance = "\n\n# OM GUIDANCE - IDENTIFIED OUTCOMES\n\n"
            om_guidance += f"Stage 1 (Outcome Mapping) identified {len(om_outcomes)} outcomes in this paper.\n"
            om_guidance += "For each outcome below, extract the full statistical details:\n\n"
            
            for i, outcome in enumerate(om_outcomes, 1):
                om_guidance += f"{i}. {outcome.get('outcome_category', 'Unknown')}\n"
                om_guidance += f"   Location: {outcome.get('location', 'Not specified')}\n"
                tp = outcome.get('timepoint_label') or outcome.get('timepoint') or outcome.get('wave') or outcome.get('timepoint_months')
                if tp is not None:
                    om_guidance += f"   Timepoint: {tp}\n"

                if 'literal_text' in outcome:
                    om_guidance += f"   Text: {outcome.get('literal_text')}\n"
                om_guidance += "\n"
            
            om_guidance += "Extract ALL of these outcomes with complete statistical details.\n"
            
            # Insert guidance before the paper text
            prompt = template.replace("{paper_text}", om_guidance + "\n\n# PAPER TEXT\n\n{paper_text}")
            prompt = prompt.replace("{paper_text}", paper_text)
            
            logger.info(f"Created focused prompt with OM guidance ({len(om_outcomes)} outcomes)")
            logger.debug(f"Prompt length: {len(prompt)} characters")
        else:
            # No OM guidance - use standard extraction
            logger.info("No OM outcomes provided, using standard extraction")
            prompt = template.replace("{paper_text}", paper_text)
        
        # Call LLM
        try:
            logger.info(f"Calling LLM with focused prompt...")
            extraction = self._call_llm(prompt)
            
            # Merge with metadata if provided
            if paper_metadata:
                extraction.update(paper_metadata)
            
            logger.info(f"✅ Successfully extracted data with OM guidance from {tei_file.name}")
            return extraction
            
        except Exception as e:
            logger.error(f"Extraction failed for {tei_file.name}: {e}")
            return None

    # ---------------------------------------------------------------------
    # Structured outputs (OpenRouter response_format) + robust JSON parsing
    # ---------------------------------------------------------------------

    def _qex_json_schema(self) -> Dict:
        """JSON Schema for Stage 2 (QEX) structured outputs.

        Keys are required to exist, but values may be null when truly unknown.
        """
        return {
            "type": "object",
            "additionalProperties": True,
            "required": [
                "study_id",
                "program_name",
                "country",
                "year_intervention_started",
                "evaluation_design",
                "evaluation_design_code",
                "evaluation_method",
                "evaluation_method_code",
                "intervention_description",
                "exposure_to_intervention",
                "length_of_follow_up",
                "intervention_start_year",
                "intervention_start_month",
                "intervention_end_year",
                "intervention_end_month",
                "final_followup_year",
                "final_followup_month",
                "timing_anchors",
                "sample_size_treatment",
                "sample_size_control",
                "graduation_components",
                "graduation_components_rationale",
                "outcomes",
                "notes",
            ],
            "properties": {
                "study_id": {"type": ["string", "null"]},
                "program_name": {"type": ["string", "null"]},
                "country": {"type": ["string", "null"]},
                "year_intervention_started": {"type": ["integer", "null"]},

                "evaluation_design": {"type": ["string", "null"]},
                "evaluation_design_code": {"type": ["integer", "null"]},
                "evaluation_method": {"type": ["string", "null"]},
                "evaluation_method_code": {"type": ["string", "null"]},

                "intervention_description": {"type": ["string", "null"]},

                # Numeric string in months (e.g., "24") for compatibility with your existing CSV builder
                "exposure_to_intervention": {"type": ["string", "null"]},
                "length_of_follow_up": {"type": ["string", "null"]},

                "intervention_start_year": {"type": ["integer", "null"]},
                "intervention_start_month": {"type": ["integer", "null"]},
                "intervention_end_year": {"type": ["integer", "null"]},
                "intervention_end_month": {"type": ["integer", "null"]},
                "final_followup_year": {"type": ["integer", "null"]},
                "final_followup_month": {"type": ["integer", "null"]},

                "timing_anchors": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["intervention_start", "intervention_end", "final_followup"],
                    "properties": {
                        "intervention_start": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["literal_text", "text_position"],
                            "properties": {
                                "literal_text": {"type": ["string", "null"]},
                                "text_position": {"type": ["string", "null"]},
                            },
                        },
                        "intervention_end": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["literal_text", "text_position"],
                            "properties": {
                                "literal_text": {"type": ["string", "null"]},
                                "text_position": {"type": ["string", "null"]},
                            },
                        },
                        "final_followup": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["literal_text", "text_position"],
                            "properties": {
                                "literal_text": {"type": ["string", "null"]},
                                "text_position": {"type": ["string", "null"]},
                            },
                        },
                    },
                },

                "sample_size_treatment": {"type": ["integer", "null"]},
                "sample_size_control": {"type": ["integer", "null"]},

                "graduation_components": {"type": "object"},
                "graduation_components_rationale": {"type": "object"},

                "outcomes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": True,
                        "required": [
                            "outcome_name",
                            "outcome_description",
                            "effect_size",
                            "p_value",
                            "standard_error",
                            "confidence_interval_lower",
                            "confidence_interval_upper",
                            "literal_text",
                            "text_position",
                            # Per-outcome timing (from qex_focused_prompt.txt)
                            "outcome_timepoint_label",
                            "outcome_measurement_year",
                            "outcome_measurement_month",
                            "months_since_intervention_end",
                            "outcome_timing_anchor",
                        ],
                        "properties": {
                            "outcome_name": {"type": ["string", "null"]},
                            "outcome_description": {"type": ["string", "null"]},
                            "effect_size": {"type": ["number", "null"]},
                            "p_value": {"type": ["number", "null"]},
                            "standard_error": {"type": ["number", "null"]},
                            "confidence_interval_lower": {"type": ["number", "null"]},
                            "confidence_interval_upper": {"type": ["number", "null"]},
                            "literal_text": {"type": ["string", "null"]},
                            "text_position": {"type": ["string", "null"]},
                            "outcome_timepoint_label": {"type": ["string", "null"]},
                            "outcome_measurement_year": {"type": ["integer", "null"]},
                            "outcome_measurement_month": {"type": ["integer", "null"]},
                            "months_since_intervention_end": {"type": ["string", "number", "null"]},
                            "outcome_timing_anchor": {
                                "type": "object",
                                "additionalProperties": False,
                                "required": ["literal_text", "text_position"],
                                "properties": {
                                    "literal_text": {"type": ["string", "null"]},
                                    "text_position": {"type": ["string", "null"]},
                                },
                            },
                        },
                    },
                },

                "notes": {"type": ["string", "null"]},
            },
        }

    def _build_response_format(self) -> Optional[Dict]:
        """Return an OpenRouter/OpenAI-compatible response_format dict."""
        if getattr(self, "mode", None) != "qex":
            return None

        use_json_schema = bool(self.config.get("extraction", {}).get("use_json_schema", True))
        if not use_json_schema:
            return {"type": "json_object"}

        return {
            "type": "json_schema",
            "json_schema": {
                "name": "om_qex_stage2_qex",
                "strict": True,
                "schema": self._qex_json_schema(),
            },
        }

    @staticmethod
    def _extract_first_balanced_json(text: str) -> Optional[str]:
        """Extract the first balanced JSON object/array substring from arbitrary text."""
        if not text:
            return None
        starts = [i for i in (text.find("{"), text.find("[")) if i != -1]
        if not starts:
            return None
        start = min(starts)
        opener = text[start]
        closer = "}" if opener == "{" else "]"

        stack = []
        in_str = False
        esc = False

        for i, ch in enumerate(text[start:], start=start):
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":  # escape
                    esc = True
                elif ch == '"':
                    in_str = False
                continue

            if ch == '"':
                in_str = True
                continue

            if ch == opener:
                stack.append(opener)
            elif ch == closer and stack:
                stack.pop()
                if not stack:
                    return text[start:i + 1]
        return None

    def _parse_llm_json(self, content) -> Dict:
        """Parse LLM response content into a dict, with robust fallbacks."""
        if content is None:
            raise ValueError("Empty response from API (content=None)")

        if isinstance(content, dict):
            return content

        response_text = str(content).strip()
        if not response_text:
            raise ValueError("Empty response from API (empty string)")

        # Strip markdown code fences if present
        if "```" in response_text:
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                if json_end > json_start:
                    response_text = response_text[json_start:json_end].strip()
            else:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                if json_end > json_start:
                    response_text = response_text[json_start:json_end].strip()

        # Fast path
        try:
            return json.loads(response_text)
        except Exception:
            pass

        # Balanced extraction path
        candidate = self._extract_first_balanced_json(response_text)
        if candidate:
            return json.loads(candidate)

        # Last resort: slice from first JSON opener
        starts = [i for i in (response_text.find("{"), response_text.find("[")) if i != -1]
        if starts:
            return json.loads(response_text[min(starts):])

        raise json.JSONDecodeError("Could not locate JSON in response", response_text, 0)

    def _call_llm(self, prompt: str, retry_count: int = 0) -> Dict:
        """
        Call LLM via OpenRouter API with robust error handling.

        Args:
            prompt: Complete prompt including template and paper text
            retry_count: Current retry attempt

        Returns:
            Extracted data as dictionary
        """
        max_retries = self.config["extraction"]["max_retries"]
        retry_delay = self.config["extraction"]["retry_delay"]

        try:
            logger.debug(f"Calling LLM API (attempt {retry_count + 1})...")

            # --------- Build kwargs and enable JSON mode in QEX ----------
            llm_kwargs = {
                "model": self.config["model"]["name"],
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": self.config["model"]["temperature"],
                "max_tokens": self.config["model"]["max_tokens"],
                "top_p": self.config["model"]["top_p"],
            }

            response_format = self._build_response_format()
            if response_format is not None:
                llm_kwargs["response_format"] = response_format

            # First attempt (schema/JSON mode if configured)
            try:
                response = self.client.chat.completions.create(**llm_kwargs)
            except Exception as api_err:
                # If response_format is not supported by the selected model/provider,
                # fall back to plain json_object and retry once.
                err_msg = str(api_err).lower()
                if "response_format" in err_msg or "json_schema" in err_msg or "invalid" in err_msg:
                    logger.warning(
                        "response_format rejected by API/model; falling back to {type: json_object} for this call."
                    )
                    llm_kwargs["response_format"] = {"type": "json_object"}
                    response = self.client.chat.completions.create(**llm_kwargs)
                else:
                    raise

            # ------------------------------------------------------------

            logger.info("✓ API call successful, parsing response...")

            # Extract + parse JSON from response (robust)
            extracted_data = self._parse_llm_json(response.choices[0].message.content)
            logger.info(
                "✓ Successfully parsed JSON with "
                f"{len(extracted_data.get('outcomes', []))} outcomes"
            )

            # Log token usage
            if hasattr(response, "usage"):
                try:
                    logger.info(f"Tokens used: {response.usage.total_tokens}")
                except Exception:
                    logger.info("Tokens used: <usage info not available>")

            return extracted_data

        except KeyboardInterrupt:
            # KeyboardInterrupt during socket read is actually a network timeout
            logger.error("Network timeout/interruption during response reading")

            if retry_count < max_retries:
                wait_time = retry_delay * (retry_count + 1) * 2  # Longer backoff for network issues
                logger.info(
                    f"Network issue detected. Retrying after {wait_time}s... "
                    f"(attempt {retry_count + 1}/{max_retries})"
                )
                time.sleep(wait_time)
                return self._call_llm(prompt, retry_count + 1)
            else:
                logger.error("Max retries reached after network timeouts")
                raise Exception("Network connection unstable - max retries exceeded") from None

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            bad_text = getattr(e, "doc", None) or ""
            if bad_text:
                logger.error(f"Bad response (first 800 chars): {bad_text[:800]}")
                logger.error(f"Bad response (last 200 chars): {bad_text[-200:]}")

            if retry_count < max_retries:
                logger.info(f"Retrying with JSON repair... (attempt {retry_count + 1}/{max_retries})")
                repair_prompt = (
                    "You previously returned invalid or non-conforming JSON. "
                    "Return EXACTLY ONE valid JSON object that matches the required schema. "
                    "Do not include any explanation or extra text.\n\n"
                    "INVALID_RESPONSE_START\n"
                    f"{bad_text[:6000]}\n"
                    "INVALID_RESPONSE_END"
                )
                time.sleep(retry_delay)
                return self._call_llm(repair_prompt, retry_count + 1)
            else:
                raise

        except Exception as e:
            logger.error(f"LLM API call failed: {type(e).__name__}: {e}")

            # Check if it's a timeout or connection error
            error_type = type(e).__name__
            error_msg = str(e).lower()
            is_retryable = any(
                x in error_type.lower() for x in ["timeout", "connection", "http", "network"]
            ) or any(
                x in error_msg for x in ["timeout", "connection", "timed out", "network"]
            )

            if retry_count < max_retries and is_retryable:
                wait_time = retry_delay * (retry_count + 1)  # Exponential backoff
                logger.info(
                    f"Retrying after {wait_time}s... "
                    f"(attempt {retry_count + 1}/{max_retries})"
                )
                time.sleep(wait_time)
                return self._call_llm(prompt, retry_count + 1)
            else:
                raise

    def extract_batch(self, tei_files: List[Path], metadata_map: Optional[Dict] = None) -> List[Dict]:
        """
        Extract data from multiple TEI files.
        
        Args:
            tei_files: List of TEI file paths
            metadata_map: Dict mapping Key -> metadata dict
        
        Returns:
            List of extraction results
        """
        results = []
        
        for i, tei_file in enumerate(tei_files, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"Paper {i}/{len(tei_files)}: {tei_file.name}")
            logger.info(f"{'='*60}")
            
            # Get metadata for this paper
            key = tei_file.stem  # Filename without extension
            metadata = metadata_map.get(key) if metadata_map else None
            
            # Extract
            result = self.extract_from_tei(tei_file, metadata)
            
            if result:
                result['_key'] = key  # Add key for tracking
                result['_tei_file'] = str(tei_file)
                results.append(result)
            else:
                logger.warning(f"⚠️  Skipping {tei_file.name} due to extraction failure")
            
            # Small delay to avoid rate limits
            time.sleep(0.5)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Extraction complete: {len(results)}/{len(tei_files)} successful")
        logger.info(f"{'='*60}")
        
        return results
    
    def save_results(self, results: List[Dict], output_dir: Path):
        """
        Save extraction results as JSON and CSV.
        
        Args:
            results: List of extraction dictionaries
            output_dir: Directory to save outputs
        """
        import pandas as pd
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save individual JSON files (with nested outcomes)
        json_dir = output_dir / "json"
        json_dir.mkdir(exist_ok=True)
        
        for result in results:
            key = result.get('_key', 'unknown')
            json_file = json_dir / f"{key}.json"
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Saved {len(results)} JSON files to {json_dir}")
        
        # Flatten outcomes for CSV - create one row per outcome
        flattened_rows = []
        
        for result in results:
            outcomes = result.get('outcomes', [])
            
            if self.mode == "om":
                # OM mode: simpler structure
                for outcome in outcomes:
                    row = {
                        '_key': result.get('_key'),
                        'study_id': result.get('study_id'),
                        'outcome_group': outcome.get('outcome_group'),
                        'outcome_category': outcome.get('outcome_category'),
                        'location': outcome.get('location'),
                        'literal_text': outcome.get('literal_text'),
                        'text_position': outcome.get('text_position')
                    }
                    flattened_rows.append(row)
            else:
                # QEX mode: full extraction with graduation components
                base_fields = {
                    '_key': result.get('_key'),
                    '_tei_file': result.get('_tei_file'),
                    'study_id': result.get('study_id'),
                    'author_name': result.get('author_name'),
                    'year_of_publication': result.get('year_of_publication'),
                    'program_name': result.get('program_name'),
                    'country': result.get('country'),
                    'year_intervention_started': result.get('year_intervention_started'),
                    'evaluation_design': result.get('evaluation_design'),
                    # NEW: intervention description + timing
                     "intervention_description": result.get("intervention_description"),
                      "exposure_to_intervention": result.get("exposure_to_intervention"),
                      "length_of_follow_up": result.get("length_of_follow_up"),
                      "intervention_start_year": result.get("intervention_start_year"),
                      "intervention_start_month": result.get("intervention_start_month"),
                      "intervention_end_year": result.get("intervention_end_year"),
                      "intervention_end_month": result.get("intervention_end_month"),
                      "final_followup_year": result.get("final_followup_year"),
                      "final_followup_month": result.get("final_followup_month"),

                     # NEW: coded evaluation fields
                     "evaluation_design_code": result.get("evaluation_design_code"),
                      "evaluation_method": result.get("evaluation_method"),
                     "evaluation_method_code": result.get("evaluation_method_code"),

                    'sample_size_treatment': result.get('sample_size_treatment'),
                    'sample_size_control': result.get('sample_size_control')
                }
                
                # Flatten graduation components
                if 'graduation_components' in result:
                    for comp, value in result['graduation_components'].items():
                        base_fields[f'component_{comp}'] = value
                
                if outcomes and isinstance(outcomes, list):
                    # Create one row per outcome
                    for outcome in outcomes:
                        row = base_fields.copy()
                        row.update({
                            'outcome_name': outcome.get('outcome_name'),
                            'outcome_description': outcome.get('outcome_description'),
                            'effect_size': outcome.get('effect_size'),
                            'p_value': outcome.get('p_value'),
                            'standard_error': outcome.get('standard_error'),
                            'confidence_interval_lower': outcome.get('confidence_interval_lower'),
                            'confidence_interval_upper': outcome.get('confidence_interval_upper'),
                            'literal_text': outcome.get('literal_text'),
                            'text_position': outcome.get('text_position'),

                            # Per-outcome timing overrides (optional but schema-recommended)
                            'outcome_timepoint_label': outcome.get('outcome_timepoint_label'),
                            'outcome_measurement_year': outcome.get('outcome_measurement_year'),
                            'outcome_measurement_month': outcome.get('outcome_measurement_month'),
                            'outcome_months_since_intervention_end': outcome.get('months_since_intervention_end'),
                            'outcome_timing_anchor_literal_text': (outcome.get('outcome_timing_anchor') or {}).get('literal_text'),
                            'outcome_timing_anchor_text_position': (outcome.get('outcome_timing_anchor') or {}).get('text_position'),
                        })
                        flattened_rows.append(row)
                else:
                    # No outcomes - create one row with base fields only
                    row = base_fields.copy()
                    row.update({
                        'outcome_name': None,
                        'outcome_description': None,
                        'effect_size': None,
                        'p_value': None,
                        'literal_text': None,
                        'text_position': None
                    })
                    flattened_rows.append(row)
        
        # Save consolidated CSV
        csv_file = output_dir / "extracted_data.csv"
        df = pd.DataFrame(flattened_rows)
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        logger.info(f"✅ Saved consolidated CSV to {csv_file} ({len(flattened_rows)} outcome rows)")
        
        # Save summary
        summary_file = output_dir / "extraction_summary.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"Extraction Summary\n")
            f.write(f"{'='*60}\n\n")
            f.write(f"Total papers processed: {len(results)}\n")
            f.write(f"Total outcome rows: {len(flattened_rows)}\n")
            f.write(f"Average outcomes per paper: {len(flattened_rows) / len(results):.1f}\n\n")
            f.write(f"Output directory: {output_dir}\n")
            f.write(f"JSON files: {json_dir}\n")
            f.write(f"CSV file: {csv_file}\n\n")
            
            f.write(f"Field Completeness:\n")
            f.write(f"{'-'*60}\n")
            
            # Calculate completeness for each field
            for col in df.columns:
                if col.startswith('_'):
                    continue  # Skip internal fields
                non_null = df[col].notna().sum()
                total = len(df)
                pct = (non_null / total * 100) if total > 0 else 0
                f.write(f"{col}: {non_null}/{total} ({pct:.1f}%)\n")
        
        logger.info(f"✅ Saved summary to {summary_file}")


def load_metadata_from_master(master_file: Path) -> Dict:
    """
    Load metadata from master CSV file.
    
    Returns:
        Dictionary mapping key -> metadata dict
    """
    import pandas as pd
    
    df = pd.read_csv(master_file)
    
    metadata_map = {}
    
    for _, row in df.iterrows():
        key = row.get('key')
        if pd.notna(key):
            metadata_map[key] = {
                'study_id': str(row.get('ID', '')),
                'author_name': row.get('ShortTitle', ''),
                'year_of_publication': int(row.get('Year', 0)) if pd.notna(row.get('Year')) else None,
                'country': row.get('Country', '')
            }
    
    return metadata_map


if __name__ == "__main__":
    # Quick test
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    engine = ExtractionEngine(config_path)
    
    # Test on one file
    tei_dir = Path(__file__).parent.parent.parent / "data" / "grobid_outputs" / "tei"
    tei_files = list(tei_dir.glob("*.tei.xml"))[:1]  # Just first file
    
    if tei_files:
        print(f"\n🧪 Testing extraction on: {tei_files[0].name}\n")
        result = engine.extract_from_tei(tei_files[0])
        
        if result:
            print("\n✅ Extraction successful!")
            print(json.dumps(result, indent=2))
        else:
            print("\n❌ Extraction failed")
    else:
        print("No TEI files found for testing")
