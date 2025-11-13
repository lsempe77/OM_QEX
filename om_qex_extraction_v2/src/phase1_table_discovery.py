"""
Phase 1: Table Discovery using LLM

Reads TEI XML and finds ALL table references, including:
- Structured tables in <figure> tags
- Paragraph-embedded tables in <p> tags
- Text references to tables
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)


class Phase1TableDiscovery:
    """
    Phase 1: LLM-based table discovery from TEI XML.
    
    Solves the critical issue where Python XML parsers miss paragraph-embedded tables.
    """
    
    def __init__(self, client: OpenAI, model: str, config: Dict):
        self.client = client
        self.model = model
        self.config = config
        self.prompt_template = self._load_prompt()
    
    def _load_prompt(self) -> str:
        """Load Phase 1 prompt template."""
        # Get path relative to this file
        prompt_file = Path(__file__).parent.parent / "prompts" / "phase1_table_discovery.txt"
        with open(prompt_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    def discover_tables(self, tei_file: Path, key: str) -> Dict:
        """
        Main entry point: Discover all tables in a TEI XML file.
        
        Args:
            tei_file: Path to TEI XML file
            key: Paper identifier (e.g., "PHRKN65M")
        
        Returns:
            Dictionary with:
            - tables_found: List of table metadata
            - total_tables_found: Count
            - warnings: List of issues detected
            - summary: Statistics
        """
        logger.info(f"PHASE 1: Table Discovery for {key}")
        
        # Read TEI XML
        tei_content = self._read_tei(tei_file)
        
        # Truncate if too large (to avoid token limits)
        max_chars = self.config.get('phase1_table_discovery', {}).get('max_tei_chars', 100000)
        if len(tei_content) > max_chars:
            logger.warning(f"TEI content too large ({len(tei_content)} chars), truncating to {max_chars}")
            tei_content = tei_content[:max_chars]
        
        # Create prompt
        prompt = self.prompt_template + "\n\n" + tei_content
        
        # Call LLM
        logger.info(f"Calling LLM for table discovery (TEI size: {len(tei_content)} chars)")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=self.config.get('model', {}).get('phase1_max_tokens', 3000)
        )
        
        # Get raw response text
        raw_response = response.choices[0].message.content or ""
        
        # Parse response
        result = self._parse_response(raw_response, key)
        
        # Save raw response for debugging (especially useful when parsing fails)
        result['_raw_response'] = raw_response
        result['_raw_response_length'] = len(raw_response)
        
        # Validate and add warnings
        result = self._validate_result(result)
        
        # Log summary
        self._log_summary(result, key)
        
        return result
    
    def _read_tei(self, tei_file: Path) -> str:
        """Read TEI XML file."""
        with open(tei_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _parse_response(self, response_text: str, key: str) -> Dict:
        """
        Parse LLM response into structured result.
        
        Handles:
        - Pure JSON
        - Markdown-wrapped JSON (```json or ```)
        - Text prefix + JSON (e.g., "Here's the JSON: {...}")
        """
        try:
            # Try direct JSON parsing
            result = json.loads(response_text)
        except json.JSONDecodeError as e:
            # Try extracting JSON from markdown code blocks
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
                try:
                    result = json.loads(json_str)
                except json.JSONDecodeError as e2:
                    logger.error(f"Failed to parse JSON from markdown block: {e2}")
                    logger.error(f"Response preview: {response_text[:1000]}")
                    result = {
                        "tables_found": [],
                        "total_tables_found": 0,
                        "warnings": [f"Failed to parse LLM response: {str(e2)}"],
                        "summary": {}
                    }
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
                try:
                    result = json.loads(json_str)
                except json.JSONDecodeError as e2:
                    logger.error(f"Failed to parse JSON from code block: {e2}")
                    logger.error(f"Response preview: {response_text[:1000]}")
                    result = {
                        "tables_found": [],
                        "total_tables_found": 0,
                        "warnings": [f"Failed to parse LLM response: {str(e2)}"],
                        "summary": {}
                    }
            else:
                # Try to find JSON by looking for first '{' character
                # This handles cases like "Here's the result: {...}"
                json_start = response_text.find('{')
                if json_start > 0:
                    logger.info(f"Detected text prefix before JSON, stripping first {json_start} chars")
                    json_str = response_text[json_start:]
                    try:
                        result = json.loads(json_str)
                        logger.info(f"Successfully parsed JSON after stripping text prefix")
                    except json.JSONDecodeError as e2:
                        logger.error(f"Failed to parse JSON after stripping prefix: {e2}")
                        logger.error(f"Response preview: {response_text[:1000]}")
                        result = {
                            "tables_found": [],
                            "total_tables_found": 0,
                            "warnings": [f"Failed to parse LLM response: {str(e2)}"],
                            "summary": {}
                        }
                else:
                    logger.error(f"Failed to parse LLM response as JSON: {e}")
                    logger.error(f"Response length: {len(response_text)} chars")
                    logger.error(f"Response preview (first 1000 chars): {response_text[:1000]}")
                    logger.error(f"Response preview (last 500 chars): {response_text[-500:]}")
                    result = {
                        "tables_found": [],
                        "total_tables_found": 0,
                        "warnings": [f"Failed to parse LLM response: {str(e)}"],
                        "summary": {}
                    }
        
        # Add metadata
        result['_key'] = key
        result['_phase'] = 'phase1_table_discovery'
        
        return result
    
    def _validate_result(self, result: Dict) -> Dict:
        """
        Validate result and add warnings.
        
        Checks:
        - Table numbering gaps
        - Confidence thresholds
        - Duplicate table numbers
        """
        warnings = result.get('warnings', [])
        tables = result.get('tables_found', [])
        
        # Check confidence threshold
        threshold = self.config.get('phase1_table_discovery', {}).get('confidence_threshold', 0.5)
        low_confidence = [t for t in tables if t.get('confidence', 1.0) < threshold]
        if low_confidence:
            warnings.append(f"{len(low_confidence)} tables below confidence threshold {threshold}")
        
        # Check for duplicate table numbers
        table_numbers = [t['table_number'] for t in tables]
        if len(table_numbers) != len(set(table_numbers)):
            duplicates = [n for n in table_numbers if table_numbers.count(n) > 1]
            warnings.append(f"Duplicate table numbers found: {set(duplicates)}")
        
        # Check for gaps in numbering (if warn_on_gaps enabled)
        if self.config.get('phase1_table_discovery', {}).get('warn_on_gaps', True):
            numeric_tables = [int(n) for n in table_numbers if n.isdigit()]
            if numeric_tables:
                numeric_tables = sorted(numeric_tables)
                for i in range(len(numeric_tables) - 1):
                    if numeric_tables[i+1] - numeric_tables[i] > 1:
                        missing = list(range(numeric_tables[i]+1, numeric_tables[i+1]))
                        warnings.append(f"Gap in table numbering: found Table {numeric_tables[i]} and {numeric_tables[i+1]}, missing {missing}")
        
        result['warnings'] = warnings
        return result
    
    def _log_summary(self, result: Dict, key: str):
        """Log summary of discovery results."""
        summary = result.get('summary', {})
        total = result.get('total_tables_found', 0)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"PHASE 1 COMPLETE: {key}")
        logger.info(f"{'='*60}")
        logger.info(f"Total tables found: {total}")
        logger.info(f"  - Structured (<figure>): {summary.get('structured_tables', 0)}")
        logger.info(f"  - Paragraph-embedded (<p>): {summary.get('paragraph_tables', 0)}")
        logger.info(f"  - Text references only: {summary.get('text_references_only', 0)}")
        
        if result.get('warnings'):
            logger.warning(f"Warnings:")
            for warning in result['warnings']:
                logger.warning(f"  - {warning}")
        
        # List table numbers found
        table_numbers = [t['table_number'] for t in result.get('tables_found', [])]
        logger.info(f"Table numbers: {sorted(table_numbers, key=lambda x: (x.isdigit(), int(x) if x.isdigit() else 0, x))}")
    
    def save_result(self, result: Dict, output_dir: Path):
        """Save Phase 1 result to JSON file."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        key = result['_key']
        output_file = output_dir / f"{key}_phase1.json"
        
        # Save raw response to separate file for debugging
        if '_raw_response' in result:
            raw_dir = output_dir / "raw_responses"
            raw_dir.mkdir(parents=True, exist_ok=True)
            raw_file = raw_dir / f"{key}_phase1_raw.txt"
            
            with open(raw_file, 'w', encoding='utf-8') as f:
                f.write(result['_raw_response'])
            
            logger.info(f"Saved raw response: {raw_file}")
            
            # Remove from JSON to keep it clean
            del result['_raw_response']
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Saved Phase 1 result: {output_file}")
