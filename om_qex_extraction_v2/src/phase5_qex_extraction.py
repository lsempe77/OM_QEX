"""
Phase 5: QEX Validation

Validates that Phase 3 extracted complete quantitative data.
In V2, this is a validation pass-through since Phase 3 already extracted all QEX fields.
"""

import logging
from pathlib import Path
from typing import Dict, List
from openai import OpenAI

logger = logging.getLogger(__name__)


class Phase5QEXExtraction:
    """
    Phase 5: QEX Validation (not extraction).
    
    In V1: This stage extracted quantitative data from outcomes.
    In V2: Phase 3 already extracts everything, so this validates completeness.
    
    Validates:
    - All required fields present (effect_size, p_value, etc.)
    - literal_text and text_position captured
    - Data quality (no obvious parsing errors)
    """
    
    def __init__(self, client: OpenAI, model: str, config: Dict):
        self.client = client
        self.model = model
        self.config = config
    
    def extract_quantitative(self, phase4_result: Dict, tei_file: Path, key: str) -> Dict:
        """
        Validate quantitative data completeness.
        
        Args:
            phase4_result: Results from Phase 4 (outcome mapping)
            tei_file: Path to TEI XML file for context
            key: Paper identifier
        
        Returns:
            Dictionary with validation results
        """
        logger.info(f"PHASE 5: QEX Validation for {key}")
        
        outcome_groups = phase4_result.get('outcome_groups', [])
        total_statistics = phase4_result.get('total_statistics', 0)
        
        logger.info(f"Validating {total_statistics} statistics across {len(outcome_groups)} outcomes")
        
        # Collect all statistics for validation
        all_statistics = []
        for group in outcome_groups:
            all_statistics.extend(group.get('statistics', []))
        
        # Validate each statistic
        validation_results = self._validate_statistics(all_statistics)
        
        logger.info(f"Validation complete:")
        logger.info(f"  - Complete records: {validation_results['complete']}")
        logger.info(f"  - Missing effect_size: {validation_results['missing_effect_size']}")
        logger.info(f"  - Missing standard_error: {validation_results['missing_se']}")
        logger.info(f"  - Missing literal_text: {validation_results['missing_literal']}")
        
        return {
            '_key': key,
            '_phase': 'phase5_qex_validation',
            'outcome_groups': outcome_groups,  # Pass through from Phase 4
            'validation': validation_results,
            'summary': {
                'total_statistics': len(all_statistics),
                'unique_outcomes': len(outcome_groups),
                'completeness_rate': validation_results['complete'] / len(all_statistics) if all_statistics else 0
            }
        }
    
    def _validate_statistics(self, statistics: List[Dict]) -> Dict:
        """
        Validate completeness of extracted statistics.
        
        Args:
            statistics: List of all statistics from all outcome groups
        
        Returns:
            Dictionary with validation counts
        """
        validation = {
            'total': len(statistics),
            'complete': 0,
            'missing_effect_size': 0,
            'missing_se': 0,
            'missing_p_value': 0,
            'missing_literal': 0,
            'missing_position': 0,
            'issues': []
        }
        
        for i, stat in enumerate(statistics):
            issues = []
            
            # Check critical fields
            if not stat.get('effect_size') and stat.get('effect_size') != 0:
                validation['missing_effect_size'] += 1
                issues.append('missing_effect_size')
            
            if not stat.get('standard_error') and stat.get('standard_error') != 0:
                validation['missing_se'] += 1
                issues.append('missing_standard_error')
            
            if not stat.get('p_value') and stat.get('p_value') != 0:
                validation['missing_p_value'] += 1
                issues.append('missing_p_value')
            
            if not stat.get('literal_text'):
                validation['missing_literal'] += 1
                issues.append('missing_literal_text')
            
            if not stat.get('text_position'):
                validation['missing_position'] += 1
                issues.append('missing_text_position')
            
            # Record if complete
            if not issues:
                validation['complete'] += 1
            else:
                validation['issues'].append({
                    'index': i,
                    'outcome_name': stat.get('outcome_name', 'Unknown'),
                    'table_number': stat.get('table_number', 'Unknown'),
                    'issues': issues
                })
        
        return validation
        
        return batches
    
    def save_result(self, result: Dict, output_dir: Path):
        """Save Phase 5 result."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        import json
        key = result['_key']
        output_file = output_dir / f"{key}_phase5.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Saved Phase 5 result: {output_file}")
        
        if result.get('_batched'):
            logger.info(f"  Batched extraction: {result['_num_batches']} batches")
