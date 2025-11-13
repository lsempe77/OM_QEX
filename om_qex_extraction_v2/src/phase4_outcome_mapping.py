"""
Phase 4: Outcome Mapping (OM)

Groups Phase 3 extraction results by outcome name for better organization.
In V2, this is primarily for readability since Phase 3 already extracted everything.
"""

import logging
from pathlib import Path
from typing import Dict, List
from openai import OpenAI

logger = logging.getLogger(__name__)


class Phase4OutcomeMapping:
    """
    Phase 4: Outcome Mapping stage.
    
    Takes Phase 3 extraction results and groups them by outcome name.
    This provides a clearer view of:
    - How many unique outcomes were found
    - Multiple treatment arms for the same outcome
    - Which tables contain each outcome
    """
    
    def __init__(self, client: OpenAI, model: str, config: Dict):
        self.client = client
        self.model = model
        self.config = config
    
    def map_outcomes(self, phase3_result: Dict, tei_file: Path, key: str) -> Dict:
        """
        Map outcomes from extracted table data.
        
        Args:
            phase3_result: Results from Phase 3 (or Phase 3b if supplemented)
            tei_file: Path to TEI XML file for additional context
            key: Paper identifier
        
        Returns:
            Dictionary with outcome mapping results
        """
        logger.info(f"PHASE 4: Outcome Mapping for {key}")
        
        outcomes = phase3_result.get('outcomes', [])
        logger.info(f"Processing {len(outcomes)} extracted statistics")
        
        # Group by outcome name
        outcome_groups = self._group_by_outcome(outcomes)
        
        logger.info(f"Identified {len(outcome_groups)} unique outcomes")
        
        # Log outcomes with multiple treatment arms
        multi_arm = [g for g in outcome_groups if g['num_variations'] > 1]
        if multi_arm:
            logger.info(f"  - {len(multi_arm)} outcomes with multiple treatment arms")
        
        return {
            '_key': key,
            '_phase': 'phase4_outcome_mapping',
            'outcome_groups': outcome_groups,
            'total_statistics': len(outcomes),
            'unique_outcomes': len(outcome_groups),
            'summary': {
                'total_statistics': len(outcomes),
                'unique_outcomes': len(outcome_groups),
                'multi_arm_outcomes': len(multi_arm),
                'tables_with_outcomes': len(set(o.get('table_number') for o in outcomes if o.get('table_number')))
            }
        }
    
    def _group_by_outcome(self, outcomes: List[Dict]) -> List[Dict]:
        """
        Group statistics by outcome name.
        
        Creates groups where each group represents one outcome variable
        (e.g., "Financial literacy index") with all its variations
        (different treatment arms, subgroups, specifications).
        
        Args:
            outcomes: List of outcome dictionaries from Phase 3
        
        Returns:
            List of outcome groups, sorted by outcome name
        """
        groups = {}
        
        for outcome in outcomes:
            name = outcome.get('outcome_name', 'Unknown')
            description = outcome.get('outcome_description', '')
            
            if name not in groups:
                groups[name] = {
                    'outcome_name': name,
                    'outcome_description': description,
                    'statistics': [],
                    'tables': set(),
                    'treatment_arms': set(),
                    'subgroups': set()
                }
            
            # Add this statistic to the group
            groups[name]['statistics'].append(outcome)
            
            # Track metadata
            if outcome.get('table_number'):
                groups[name]['tables'].add(outcome['table_number'])
            if outcome.get('treatment_arm'):
                groups[name]['treatment_arms'].add(outcome['treatment_arm'])
            if outcome.get('subgroup'):
                groups[name]['subgroups'].add(outcome['subgroup'])
        
        # Convert to list and format
        result = []
        for name, group in sorted(groups.items()):
            result.append({
                'outcome_name': name,
                'outcome_description': group['outcome_description'],
                'num_variations': len(group['statistics']),
                'tables': sorted(list(group['tables'])),
                'treatment_arms': sorted(list(group['treatment_arms'])),
                'subgroups': sorted(list(group['subgroups'])) if group['subgroups'] else [],
                'statistics': group['statistics']
            })
        
        return result
    
    def save_result(self, result: Dict, output_dir: Path):
        """Save Phase 4 result."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        import json
        key = result['_key']
        output_file = output_dir / f"{key}_phase4.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Saved Phase 4 result: {output_file}")
