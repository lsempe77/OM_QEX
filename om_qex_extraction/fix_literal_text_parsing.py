"""
Post-processing script to parse numeric fields from literal_text when they are missing.
Handles common formats from impact evaluation tables.
"""
import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple


def parse_effect_and_se(literal_text: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Parse effect size and standard error from literal text.
    
    Handles formats like:
    - "9,079*** (1,864)"
    - "-4.89 (4.90)"
    - "0.84** (0.43)"
    - "311** (119) [0.01]"
    - "13.93*** (--)"
    
    Returns:
        (effect_size, standard_error) tuple, or (None, None) if parsing fails
    """
    if not literal_text or literal_text.strip() == "":
        return None, None
    
    # Pattern: number (possibly negative, with commas, with asterisks) followed by (number)
    # Format: effect*** (se)
    pattern = r'(-?[\d,]+\.?\d*)\s*\*{0,3}\s*\((-?[\d,]+\.?\d*|--)\)'
    
    match = re.search(pattern, literal_text)
    if match:
        effect_str = match.group(1).replace(',', '')
        se_str = match.group(2).replace(',', '')
        
        try:
            effect = float(effect_str)
        except ValueError:
            effect = None
        
        # Handle "--" for missing SE
        if se_str == '--':
            se = None
        else:
            try:
                se = float(se_str)
            except ValueError:
                se = None
        
        return effect, se
    
    return None, None


def parse_observations(literal_text: str) -> Optional[int]:
    """
    Parse observation count from literal text.
    
    Handles formats like:
    - "[N=500]"
    - "(n=1234)"
    - "N: 500"
    
    Returns:
        observations count or None
    """
    if not literal_text:
        return None
    
    # Pattern: N=number or n=number
    pattern = r'[Nn]\s*[=:]\s*(\d+)'
    
    match = re.search(pattern, literal_text)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    
    return None


def should_parse_outcome(outcome: Dict[str, Any]) -> bool:
    """
    Determine if outcome needs post-processing.
    
    Returns True if:
    - Has literal_text with numbers
    - Missing effect_size or standard_error
    """
    has_literal = outcome.get('literal_text') and outcome['literal_text'].strip()
    
    # Check if numeric fields are missing
    missing_effect = outcome.get('effect_size') is None or outcome.get('effect_size') == 'N/A'
    missing_se = outcome.get('standard_error') is None or outcome.get('standard_error') == 'N/A'
    
    # Check if literal has numbers
    has_numbers = has_literal and re.search(r'\d', outcome['literal_text'])
    
    return has_numbers and (missing_effect or missing_se)


def fix_outcome(outcome: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse and fill missing numeric fields from literal_text.
    
    Returns updated outcome dict with parsed fields.
    """
    literal_text = outcome.get('literal_text', '')
    
    # Parse effect and SE
    effect, se = parse_effect_and_se(literal_text)
    
    # Only update if we found values and they're currently missing
    if effect is not None and (outcome.get('effect_size') is None or outcome.get('effect_size') == 'N/A'):
        outcome['effect_size'] = effect
        outcome['_parsed_effect'] = True
    
    if se is not None and (outcome.get('standard_error') is None or outcome.get('standard_error') == 'N/A'):
        outcome['standard_error'] = se
        outcome['_parsed_se'] = True
    
    # Try to parse observations
    obs = parse_observations(literal_text)
    if obs is not None and outcome.get('observations') is None:
        outcome['observations'] = obs
        outcome['_parsed_obs'] = True
    
    return outcome


def process_extraction_file(json_path: Path) -> Dict[str, Any]:
    """
    Process extraction JSON file and fix missing fields.
    
    Returns:
        dict with 'fixed', 'total', 'outcomes' keys
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    fixed_count = 0
    total_outcomes = len(data.get('outcomes', []))
    
    for i, outcome in enumerate(data['outcomes']):
        if should_parse_outcome(outcome):
            data['outcomes'][i] = fix_outcome(outcome)
            fixed_count += 1
    
    return {
        'fixed': fixed_count,
        'total': total_outcomes,
        'data': data
    }


def main():
    """
    Main function to fix validation set outcomes.
    """
    # Keys from validation_set1.csv with parsing issues
    problem_keys = [
        'PHRKN65M',   # outcome 0
        '949EZS93',   # outcome 4
        'DXHZBI2X',   # outcome 1
        'V5P2S7S3',   # outcomes 15-17 (will need re-extraction)
        'XWDVG8KS',   # outcomes 4, 7
        'ABM3E3ZP',   # outcome 5
        'CG73D75P',   # outcome 0
    ]
    
    base_path = Path('outputs/twopass_extractions/json')
    
    print("POST-PROCESSING: Parsing literal_text to fix missing fields")
    print("=" * 80)
    
    total_fixed = 0
    total_processed = 0
    
    for key in problem_keys:
        json_file = base_path / f"{key}.json"
        
        if not json_file.exists():
            print(f"\n⚠️  {key}: JSON not found")
            continue
        
        print(f"\n{key}:")
        result = process_extraction_file(json_file)
        
        print(f"  Processed: {result['total']} outcomes")
        print(f"  Fixed: {result['fixed']} outcomes")
        
        if result['fixed'] > 0:
            # Save fixed version
            output_path = base_path / f"{key}.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result['data'], f, indent=2, ensure_ascii=False)
            print(f"  ✅ Saved to: {output_path}")
        
        total_fixed += result['fixed']
        total_processed += result['total']
    
    print("\n" + "=" * 80)
    print(f"SUMMARY: Fixed {total_fixed} outcomes across {len(problem_keys)} papers")
    print("=" * 80)


if __name__ == '__main__':
    main()
