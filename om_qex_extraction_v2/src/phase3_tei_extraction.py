"""
Phase 3: TEI Extraction

Extracts outcomes from RESULTS tables using TEI XML content.
Handles both structured <figure> tables and paragraph-embedded <p> tables.
"""

import logging
import json
from pathlib import Path
from typing import Dict, List
from openai import OpenAI

logger = logging.getLogger(__name__)


class Phase3TEIExtraction:
    """
    Phase 3: Extract outcomes from TEI XML.
    
    Uses LLM to extract statistical data from tables in TEI format,
    handling both structured and paragraph-embedded tables.
    """
    
    def __init__(self, client: OpenAI, model: str, config: Dict):
        self.client = client
        self.model = model
        self.config = config
        self.prompt_template = self._load_prompt()
        self.output_dir = Path(__file__).parent.parent / "outputs" / "phase3"
    
    def _load_prompt(self) -> str:
        """Load Phase 3 prompt template."""
        prompt_file = Path(__file__).parent.parent / "prompts" / "phase3_tei_extraction.txt"
        with open(prompt_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    def extract_from_tei(self, phase2_result: Dict, tei_file: Path, key: str) -> Dict:
        """
        Extract outcomes from RESULTS tables in TEI XML.
        
        Args:
            phase2_result: Results from Phase 2 (filtered tables)
            tei_file: Path to TEI XML file
            key: Paper identifier
        
        Returns:
            Dictionary with extracted outcomes
        """
        logger.info(f"PHASE 3: TEI Extraction for {key}")
        
        # Get RESULTS tables
        results_tables = phase2_result.get('results_tables', [])
        logger.info(f"Extracting from {len(results_tables)} RESULTS tables")
        
        if not results_tables:
            logger.warning("No RESULTS tables to extract from")
            return {
                '_key': key,
                '_phase': 'phase3_tei_extraction',
                'tables_extracted': [],
                'outcomes': [],
                'total_outcomes_extracted': 0
            }
        
        # Read TEI XML once
        tei_content = self._read_tei(tei_file)
        
        # Truncate if too large
        phase3_config = self.config.get('pipeline', {}).get('phase3_tei_extraction', {})
        max_chars = phase3_config.get('max_tei_chars', 150000)
        if len(tei_content) > max_chars:
            logger.warning(f"TEI content too large ({len(tei_content)} chars), truncating to {max_chars}")
            tei_content = tei_content[:max_chars]
        
        # Batch extraction: Process tables in smaller groups
        batch_size = phase3_config.get('batch_size', 5)
        logger.info(f"Using batch size: {batch_size} tables per API call")
        
        all_outcomes = []
        all_tables_extracted = []
        
        # Process in batches
        for i in range(0, len(results_tables), batch_size):
            batch = results_tables[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(results_tables) + batch_size - 1) // batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches}: {len(batch)} tables")
            
            # Create prompt for this batch
            prompt = self._create_prompt(batch, tei_content)
            
            # Call LLM
            logger.info(f"Calling LLM for batch {batch_num} ({len(tei_content)} chars TEI)")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=self.config.get('model', {}).get('phase3_max_tokens', 8000)
            )
            
            # Parse response
            response_text = response.choices[0].message.content or ""
            batch_result = self._parse_response(response_text, f"{key}_batch{batch_num}")
            
            # Accumulate results
            all_outcomes.extend(batch_result.get('outcomes', []))
            all_tables_extracted.extend(batch_result.get('tables_extracted', []))
            
            logger.info(f"Batch {batch_num} extracted {len(batch_result.get('outcomes', []))} outcomes")
        
        # Combine results
        result = {
            '_key': key,
            '_phase': 'phase3_tei_extraction',
            'tables_extracted': all_tables_extracted,
            'outcomes': all_outcomes,
            'total_outcomes_extracted': len(all_outcomes)
        }
        
        # Log summary
        self._log_summary(result, key)
        
        return result
    
    def _read_tei(self, tei_file: Path) -> str:
        """Read TEI XML content."""
        with open(tei_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _create_prompt(self, results_tables: List[Dict], tei_content: str) -> str:
        """Create extraction prompt."""
        # Format tables list
        tables_list = "RESULTS tables to extract:\n\n"
        for table in results_tables:
            tables_list += f"- Table {table['table_number']}: {table.get('title', 'No title')}\n"
            tables_list += f"  Location: {table.get('location', 'Unknown')}\n"
            tables_list += f"  Classification confidence: {table.get('confidence', 1.0)}\n\n"
        
        # Build full prompt
        prompt = self.prompt_template
        prompt = prompt.replace("{tables_list}", tables_list)
        prompt = prompt.replace("{tei_content}", tei_content)
        
        return prompt
    
    def _parse_response(self, response_text: str, key: str) -> Dict:
        """Parse LLM response."""
        # Save raw response for debugging
        raw_file = self.output_dir / "raw_responses" / f"{key}_phase3_raw.txt"
        raw_file.parent.mkdir(parents=True, exist_ok=True)
        with open(raw_file, 'w', encoding='utf-8') as f:
            f.write(response_text)
        
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            # Try extracting from markdown
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
                result = json.loads(json_str)
            elif "```" in response_text:
                # Try generic code block
                json_str = response_text.split("```")[1].split("```")[0].strip()
                result = json.loads(json_str)
            else:
                logger.error(f"Failed to parse Phase 3 response")
                logger.error(f"Raw response saved to: {raw_file}")
                logger.error(f"Response preview: {response_text[:500]}...")
                result = {
                    'tables_extracted': [],
                    'outcomes': [],
                    'total_outcomes_extracted': 0
                }
        
        # Add metadata
        result['_key'] = key
        result['_phase'] = 'phase3_tei_extraction'
        
        return result
    
    def _log_summary(self, result: Dict, key: str):
        """Log extraction summary."""
        logger.info("\n" + "=" * 60)
        logger.info(f"PHASE 3 COMPLETE: {key}")
        logger.info("=" * 60)
        
        tables_extracted = result.get('tables_extracted', [])
        total_outcomes = result.get('total_outcomes_extracted', 0)
        
        logger.info(f"Tables processed: {len(tables_extracted)}")
        logger.info(f"Total outcomes extracted: {total_outcomes}")
        
        # Log per-table summary
        for table in tables_extracted:
            table_num = table.get('table_number', 'Unknown')
            success = table.get('extraction_success', False)
            outcomes = table.get('outcomes_found', 0)
            status = "SUCCESS" if success else "FAILED"
            logger.info(f"  Table {table_num}: {status} - {outcomes} outcomes")
    
    def save_result(self, result: Dict, output_dir: Path):
        """Save Phase 3 result."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        key = result['_key']
        output_file = output_dir / f"{key}_phase3.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Saved Phase 3 result: {output_file}")
