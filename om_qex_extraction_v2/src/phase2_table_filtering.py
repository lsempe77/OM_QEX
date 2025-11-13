"""
Phase 2: Table Filtering using LLM

Classifies tables as RESULTS or DESCRIPTIVE based on:
- Table caption/title
- Table headers
- Context in paper
"""

import json
import logging
from pathlib import Path
from typing import Dict, List
from openai import OpenAI

logger = logging.getLogger(__name__)


class Phase2TableFiltering:
    """
    Phase 2: LLM-based table classification.
    
    Filters out DESCRIPTIVE tables (baseline characteristics, balance, etc.)
    and keeps only RESULTS tables (treatment effects, impacts, etc.)
    """
    
    def __init__(self, client: OpenAI, model: str, config: Dict):
        self.client = client
        self.model = model
        self.config = config
        self.prompt_template = self._load_prompt()
    
    def _load_prompt(self) -> str:
        """Load Phase 2 prompt template."""
        # Get path relative to this file
        prompt_file = Path(__file__).parent.parent / "prompts" / "phase2_table_filtering.txt"
        with open(prompt_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _get_default_prompt(self) -> str:
        """Default filtering prompt (stub for now)."""
        return """
You are classifying tables as RESULTS or DESCRIPTIVE.

RESULTS tables contain:
- Treatment effects, coefficients, regression results
- Impact estimates, program effects
- Statistical tests, p-values, standard errors

DESCRIPTIVE tables contain:
- Baseline characteristics, summary statistics
- Balance tables, attrition analysis
- Sample demographics

For each table, output:
- table_number
- classification: "RESULTS" or "DESCRIPTIVE"
- confidence: 0.0-1.0
- reasoning: brief explanation
"""
    
    def filter_tables(self, phase1_result: Dict, tei_file: Path) -> Dict:
        """
        Main entry point: Filter tables from Phase 1.
        
        Args:
            phase1_result: Result from Phase 1 table discovery
            tei_file: Path to TEI XML (for extracting context)
        
        Returns:
            Dictionary with:
            - tables_classified: All tables with classifications
            - results_tables: Only RESULTS tables
            - descriptive_tables: Only DESCRIPTIVE tables
            - summary: Statistics
        """
        key = phase1_result['_key']
        logger.info(f"PHASE 2: Table Filtering for {key}")
        
        tables = phase1_result['tables_found']
        
        if not tables:
            logger.warning(f"No tables found in Phase 1, skipping filtering")
            return {
                '_key': key,
                '_phase': 'phase2_table_filtering',
                'tables_classified': [],
                'results_tables': [],
                'descriptive_tables': [],
                'summary': {
                    'total_tables': 0,
                    'results_tables': 0,
                    'descriptive_tables': 0
                }
            }
        
        # Check if LLM filtering is enabled
        if not self.config.get('phase2_table_filtering', {}).get('use_llm', True):
            logger.info("LLM filtering disabled, using heuristic filter")
            return self._heuristic_filter(tables, key)
        
        # Extract context for each table (TODO: implement)
        table_contexts = self._extract_contexts(tei_file, tables)
        
        # Create prompt
        prompt = self._create_prompt(tables, table_contexts)
        
        # Call LLM
        logger.info(f"Calling LLM for table filtering ({len(tables)} tables)")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=self.config.get('model', {}).get('phase2_max_tokens', 2000)
        )
        
        # Parse response
        result = self._parse_response(response.choices[0].message.content, key)
        
        # Filter by confidence threshold
        result = self._apply_threshold(result)
        
        # Log summary
        self._log_summary(result, key)
        
        return result
    
    def _extract_contexts(self, tei_file: Path, tables: List[Dict]) -> Dict:
        """
        Extract text context around each table.
        
        TODO: Implement proper context extraction
        For now, just use table titles as context.
        """
        contexts = {}
        for table in tables:
            table_num = table['table_number']
            contexts[table_num] = {
                'title': table.get('title', ''),
                'location': table.get('location', ''),
                'before': '',  # TODO: Extract text before table
                'after': ''    # TODO: Extract text after table
            }
        return contexts
    
    def _create_prompt(self, tables: List[Dict], contexts: Dict) -> str:
        """Create prompt for LLM classification."""
        prompt = self.prompt_template + "\n\n"
        prompt += f"Tables to classify ({len(tables)} total):\n\n"
        prompt += json.dumps(tables, indent=2)
        prompt += "\n\nContext excerpts:\n\n"
        prompt += json.dumps(contexts, indent=2)
        prompt += "\n\nReturn classification for each table in JSON format."
        return prompt
    
    def _parse_response(self, response_text: str, key: str) -> Dict:
        """Parse LLM response."""
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            # Try extracting from markdown
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
                result = json.loads(json_str)
            else:
                logger.error(f"Failed to parse filtering response")
                result = {'tables_classified': []}
        
        # Separate RESULTS and DESCRIPTIVE
        tables_classified = result.get('tables_classified', [])
        results_tables = [t for t in tables_classified if t.get('classification') == 'RESULTS']
        descriptive_tables = [t for t in tables_classified if t.get('classification') == 'DESCRIPTIVE']
        
        return {
            '_key': key,
            '_phase': 'phase2_table_filtering',
            'tables_classified': tables_classified,
            'results_tables': results_tables,
            'descriptive_tables': descriptive_tables,
            'summary': {
                'total_tables': len(tables_classified),
                'results_tables': len(results_tables),
                'descriptive_tables': len(descriptive_tables)
            }
        }
    
    def _apply_threshold(self, result: Dict) -> Dict:
        """Apply confidence threshold to filter results."""
        threshold = self.config.get('phase2_table_filtering', {}).get('confidence_threshold', 0.55)
        
        # Only keep RESULTS tables with confidence >= threshold
        results_tables = result['results_tables']
        filtered_results = [t for t in results_tables if t.get('confidence', 1.0) >= threshold]
        
        if len(filtered_results) < len(results_tables):
            logger.info(f"Filtered {len(results_tables) - len(filtered_results)} RESULTS tables below threshold {threshold}")
            result['results_tables'] = filtered_results
            result['summary']['results_tables'] = len(filtered_results)
        
        return result
    
    def _heuristic_filter(self, tables: List[Dict], key: str) -> Dict:
        """
        Fallback heuristic filtering (similar to V1 smart_table_filter.py).
        
        TODO: Implement heuristic rules
        For now, just classify all as RESULTS.
        """
        logger.info("Using heuristic filter (all tables classified as RESULTS)")
        
        tables_classified = []
        for table in tables:
            tables_classified.append({
                **table,
                'classification': 'RESULTS',
                'confidence': 0.8,
                'reasoning': 'Heuristic filter: default to RESULTS'
            })
        
        return {
            '_key': key,
            '_phase': 'phase2_table_filtering',
            'tables_classified': tables_classified,
            'results_tables': tables_classified,
            'descriptive_tables': [],
            'summary': {
                'total_tables': len(tables_classified),
                'results_tables': len(tables_classified),
                'descriptive_tables': 0
            }
        }
    
    def _log_summary(self, result: Dict, key: str):
        """Log filtering summary."""
        summary = result['summary']
        
        logger.info(f"\n{'='*60}")
        logger.info(f"PHASE 2 COMPLETE: {key}")
        logger.info(f"{'='*60}")
        logger.info(f"Total tables classified: {summary['total_tables']}")
        logger.info(f"  - RESULTS tables: {summary['results_tables']}")
        logger.info(f"  - DESCRIPTIVE tables: {summary['descriptive_tables']}")
        
        # List RESULTS table numbers
        results_nums = [t['table_number'] for t in result['results_tables']]
        logger.info(f"RESULTS table numbers: {sorted(results_nums, key=lambda x: (x.isdigit(), int(x) if x.isdigit() else 0, x))}")
    
    def save_result(self, result: Dict, output_dir: Path):
        """Save Phase 2 result to JSON file."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        key = result['_key']
        output_file = output_dir / f"{key}_phase2.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Saved Phase 2 result: {output_file}")
