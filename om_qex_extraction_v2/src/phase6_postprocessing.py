"""
Phase 6: Post-Processing and CSV Export

Formats Phase 5 results into final CSV-ready output.
Adds study metadata and ensures all fields are CSV-compatible.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional
import json
import csv

logger = logging.getLogger(__name__)


class Phase6PostProcessing:
    """
    Phase 6: Post-processing and CSV export.
    
    - Flattens outcome groups into individual rows
    - Adds study metadata
    - Exports to CSV format
    - Creates human-readable summary
    """
    
    def __init__(self, client, model: str, config: Dict):
        self.client = client
        self.model = model
        self.config = config
    
    def post_process(self, phase5_result: Dict, key: str, study_id: Optional[str] = None) -> Dict:
        """
        Post-process and format results for final output.
        
        Args:
            phase5_result: Results from Phase 5 (validation)
            key: Paper identifier
            study_id: Optional study ID for linking to master data
        
        Returns:
            Dictionary with final formatted data
        """
        logger.info(f"PHASE 6: Post-Processing for {key}")
        
        outcome_groups = phase5_result.get('outcome_groups', [])
        validation = phase5_result.get('validation', {})
        
        # Flatten outcome groups into individual records
        records = self._flatten_outcome_groups(outcome_groups, key, study_id)
        
        logger.info(f"Created {len(records)} final records")
        
        # Identify any data quality issues
        quality_issues = self._check_quality(records, validation)
        
        if quality_issues:
            logger.warning(f"Data quality issues found: {len(quality_issues)}")
            for issue in quality_issues[:5]:  # Log first 5
                logger.warning(f"  - {issue}")
        
        return {
            '_key': key,
            '_phase': 'phase6_postprocessing',
            'study_id': study_id or key,
            'records': records,
            'validation': validation,
            'quality_issues': quality_issues,
            'summary': {
                'total_records': len(records),
                'unique_outcomes': len(outcome_groups),
                'quality_score': 1.0 - (len(quality_issues) / len(records)) if records else 0
            }
        }
    
    def _flatten_outcome_groups(self, outcome_groups: List[Dict], key: str, study_id: Optional[str] = None) -> List[Dict]:
        """
        Flatten outcome groups into individual CSV-ready records.
        
        Args:
            outcome_groups: List of outcome groups from Phase 5
            key: Paper identifier
            study_id: Optional study ID
        
        Returns:
            List of flattened records
        """
        records = []
        
        for group in outcome_groups:
            outcome_name = group.get('outcome_name', '')
            outcome_description = group.get('outcome_description', '')
            statistics = group.get('statistics', [])
            
            for stat in statistics:
                record = {
                    'study_id': study_id or key,
                    'key': key,
                    'outcome_name': outcome_name,
                    'outcome_description': outcome_description,
                    'treatment_arm': stat.get('treatment_arm', ''),
                    'subgroup': stat.get('subgroup', ''),
                    'table_number': stat.get('table_number', ''),
                    'effect_size': stat.get('effect_size', ''),
                    'standard_error': stat.get('standard_error', ''),
                    'p_value': stat.get('p_value', ''),
                    'confidence_interval': stat.get('confidence_interval', ''),
                    'sample_size': stat.get('sample_size', ''),
                    'literal_text': stat.get('literal_text', ''),
                    'text_position': stat.get('text_position', '')
                }
                records.append(record)
        
        return records
    
    def _check_quality(self, records: List[Dict], validation: Dict) -> List[str]:
        """
        Check data quality and identify issues.
        
        Args:
            records: List of final records
            validation: Validation results from Phase 5
        
        Returns:
            List of quality issue descriptions
        """
        issues = []
        
        # Check for missing critical fields
        missing_effect = validation.get('missing_effect_size', 0)
        if missing_effect > 0:
            issues.append(f"{missing_effect} records missing effect_size")
        
        missing_se = validation.get('missing_se', 0)
        if missing_se > 0:
            issues.append(f"{missing_se} records missing standard_error")
        
        missing_literal = validation.get('missing_literal', 0)
        if missing_literal > 0:
            issues.append(f"{missing_literal} records missing literal_text")
        
        # Check for potential data issues
        for i, record in enumerate(records):
            # Check for unrealistic effect sizes (absolute value > 1000)
            try:
                effect = float(record.get('effect_size', 0) or 0)
                if abs(effect) > 1000:
                    issues.append(f"Record {i}: Suspiciously large effect_size ({effect})")
            except (ValueError, TypeError):
                pass
            
            # Check for p-values > 1
            try:
                p_val = float(record.get('p_value', 0) or 0)
                if p_val > 1:
                    issues.append(f"Record {i}: Invalid p_value ({p_val} > 1)")
            except (ValueError, TypeError):
                pass
        
        return issues
    
    def save_result(self, result: Dict, output_dir: Path):
        """
        Save Phase 6 result as both JSON and CSV.
        
        Args:
            result: Phase 6 result dictionary
            output_dir: Output directory
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        key = result['_key']
        
        # Save JSON
        json_file = output_dir / f"{key}_final.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved JSON: {json_file}")
        
        # Save CSV
        csv_file = output_dir / f"{key}_final.csv"
        records = result.get('records', [])
        
        if records:
            fieldnames = [
                'study_id', 'key', 'outcome_name', 'outcome_description',
                'treatment_arm', 'subgroup', 'table_number',
                'effect_size', 'standard_error', 'p_value',
                'confidence_interval', 'sample_size',
                'literal_text', 'text_position'
            ]
            
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(records)
            
            logger.info(f"Saved CSV: {csv_file} ({len(records)} rows)")
        else:
            logger.warning(f"No records to save for {key}")
