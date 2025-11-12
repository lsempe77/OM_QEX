"""
Smart table filtering to identify results tables vs descriptive tables.

Uses three signals:
1. Text context - references to tables near outcome keywords
2. Table caption - presence of result/impact/effect keywords
3. Table headers - statistical indicators (coef, SE, p-value, etc.)
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple


# Keywords for identifying results tables
RESULT_KEYWORDS = [
    # Impact/effect language
    'impact', 'effect', 'estimate', 'result', 'outcome', 'coefficient',
    'treatment', 'intervention', 'program',
    
    # Statistical terms
    'regression', 'ols', 'fixed effect', 'difference-in-difference', 'did',
    'iv', 'instrumental variable', 'rct', 'randomized',
    
    # Quasi-experimental methods
    'rdd', 'regression discontinuity', 'propensity score', 'psm', 'matching',
    'synthetic control', 'interrupted time series', 'its',
    'difference in differences', 'difindif', 'panel data',
    
    # Model types
    'model', 'models', 'specification', 'estimation',
    'logit', 'probit', 'tobit', 'poisson', 'negative binomial',
    'fixed effects', 'random effects', 'gls', 'gmm',
    '2sls', 'two stage', 'control function',
    
    # Randomized trials
    'randomized controlled trial', 'randomized control trial',
    'randomised', 'experimental', 'trial',
    
    # Outcome domains
    'income', 'consumption', 'expenditure', 'employment', 'education',
    'health', 'nutrition', 'poverty', 'asset', 'saving', 'productivity'
]

DESCRIPTIVE_KEYWORDS = [
    'summary statistics', 'descriptive statistics', 'sample characteristics',
    'baseline characteristics', 'balance', 'attrition', 'sample size',
    'demographic', 'respondent characteristics'
]

STATISTICAL_HEADERS = [
    # Coefficient indicators
    'coef', 'coefficient', 'estimate', 'beta', 'b',
    
    # Standard errors
    'se', 'std. err', 'standard error', 'std err',
    
    # Significance
    'p-value', 'p value', 't-stat', 't-statistic', 'z-stat',
    'sig', 'significance', '*', '**', '***',
    
    # Confidence intervals
    'ci', '95% ci', 'confidence interval',
    
    # Columns
    '(1)', '(2)', '(3)', '(4)', '(5)', '(6)', '(7)', '(8)'
]


def score_table_caption(caption: str) -> Tuple[float, str]:
    """
    Score a table caption for likelihood of being a results table.
    
    Returns:
        (score, reason) - score from 0-1, reason for classification
    """
    if not caption:
        return (0.5, "No caption")
    
    caption_lower = caption.lower()
    
    # CRITICAL: Filter out figures/charts (they are NOT tables)
    figure_keywords = ['figure', 'fig.', 'fig ', 'chart', 'graph', 'diagram', 'plot']
    for keyword in figure_keywords:
        if keyword in caption_lower:
            return (-999, f"FIGURE/CHART detected: '{keyword}' - NOT A TABLE")
    
    # Strong negative signals
    for keyword in DESCRIPTIVE_KEYWORDS:
        if keyword in caption_lower:
            return (0.1, f"Descriptive keyword: '{keyword}'")
    
    # Positive signals
    result_matches = sum(1 for kw in RESULT_KEYWORDS if kw in caption_lower)
    
    if result_matches >= 2:
        return (0.9, f"Strong result indicators ({result_matches} keywords)")
    elif result_matches == 1:
        return (0.7, f"Result indicator present")
    else:
        return (0.5, "No clear indicators")


def score_table_headers(rows: List[Dict]) -> Tuple[float, str]:
    """
    Score table headers for statistical indicators.
    
    Returns:
        (score, reason) - score from 0-1, reason for classification
    """
    if not rows or len(rows) < 2:
        return (0.5, "Insufficient rows")
    
    # Get first 3 rows (usually contain headers)
    header_text = ""
    for row in rows[:3]:
        for cell in row.get('cells', []):
            header_text += " " + cell.get('text', '').lower()
    
    # Count statistical indicators
    stat_matches = sum(1 for indicator in STATISTICAL_HEADERS if indicator in header_text)
    
    # Check for numbered columns (1), (2), etc.
    numbered_cols = len(re.findall(r'\(\d+\)', header_text))
    
    if stat_matches >= 3 or numbered_cols >= 3:
        return (0.9, f"Strong statistical indicators ({stat_matches} keywords, {numbered_cols} numbered cols)")
    elif stat_matches >= 1 or numbered_cols >= 1:
        return (0.7, f"Some statistical indicators ({stat_matches} keywords, {numbered_cols} numbered cols)")
    else:
        return (0.3, "No statistical indicators")


def find_table_references_in_text(text: str, table_number: int) -> Tuple[float, str]:
    """
    Check if table is referenced near outcome/result keywords in text.
    
    Returns:
        (score, reason) - score from 0-1, reason for classification
    """
    if not text:
        return (0.5, "No text available")
    
    text_lower = text.lower()
    
    # Find all references to this table
    patterns = [
        f'table {table_number}',
        f'table{table_number}',
        f'tab. {table_number}',
        f'tab {table_number}'
    ]
    
    references = []
    for pattern in patterns:
        for match in re.finditer(pattern, text_lower):
            # Get context (500 chars before and after)
            start = max(0, match.start() - 500)
            end = min(len(text_lower), match.end() + 500)
            context = text_lower[start:end]
            references.append(context)
    
    if not references:
        return (0.5, f"Table {table_number} not referenced in text")
    
    # Check if any reference is near result keywords
    result_nearby = 0
    for context in references:
        nearby_keywords = sum(1 for kw in RESULT_KEYWORDS if kw in context)
        if nearby_keywords > 0:
            result_nearby += 1
    
    if result_nearby >= len(references) * 0.5:  # Majority of refs near results
        return (0.8, f"{result_nearby}/{len(references)} references near result keywords")
    elif result_nearby > 0:
        return (0.6, f"{result_nearby}/{len(references)} references near result keywords")
    else:
        return (0.4, "Table referenced but not near result keywords")


def classify_table(
    table_json: Dict,
    full_text: Optional[str] = None
) -> Tuple[bool, float, Dict[str, Tuple[float, str]]]:
    """
    Classify a table as results vs descriptive.
    
    Args:
        table_json: Table JSON with caption, rows, table_number
        full_text: Full paper text (optional, for context analysis)
    
    Returns:
        (is_results_table, confidence_score, signal_details)
    """
    caption = table_json.get('caption', '')
    rows = table_json.get('rows', [])
    table_number = table_json.get('table_number', 0)
    
    # Get scores from each signal
    caption_score, caption_reason = score_table_caption(caption)
    
    # CRITICAL: Skip figures entirely (score = -999)
    if caption_score == -999:
        return (False, 0.0, {'caption': (caption_score, caption_reason)})
    
    header_score, header_reason = score_table_headers(rows)
    
    signals = {
        'caption': (caption_score, caption_reason),
        'headers': (header_score, header_reason)
    }
    
    # Add text context if available
    if full_text:
        text_score, text_reason = find_table_references_in_text(full_text, table_number)
        signals['text_context'] = (text_score, text_reason)
        
        # Weighted average (text context is less reliable)
        overall_score = (caption_score * 0.4 + header_score * 0.4 + text_score * 0.2)
    else:
        # Without text, use caption and headers equally
        overall_score = (caption_score * 0.5 + header_score * 0.5)
    
    # More conservative threshold: 0.55 (lowered from 0.6 to include more tables)
    # Better to include a false positive than miss a results table
    is_results = overall_score >= 0.55
    
    return (is_results, overall_score, signals)


def filter_results_tables(
    tables_dir: Path,
    text_dir: Path,
    key: str,
    verbose: bool = False
) -> List[Dict]:
    """
    Load all tables for a paper and filter to results tables only.
    
    Args:
        tables_dir: Directory containing table JSON files
        text_dir: Directory containing full text files
        key: Paper key (e.g., 'PHRKN65M')
        verbose: Print classification details
    
    Returns:
        List of classified tables with metadata
    """
    # Load full text
    text_file = text_dir / f"{key}.txt"
    full_text = None
    if text_file.exists():
        full_text = text_file.read_text(encoding='utf-8')
    
    # Find all tables for this paper
    table_files = sorted(tables_dir.glob(f"{key}_table_*.json"))
    
    results_tables = []
    
    for table_file in table_files:
        with open(table_file, 'r', encoding='utf-8') as f:
            table_json = json.load(f)
        
        is_results, score, signals = classify_table(table_json, full_text)
        
        table_info = {
            'file': table_file.name,
            'table_number': table_json.get('table_number'),
            'caption': table_json.get('caption', ''),
            'is_results': is_results,
            'confidence': score,
            'signals': signals,
            'table_data': table_json
        }
        
        if verbose:
            status = "[RESULTS]" if is_results else "[SKIP]"
            print(f"\n{status} [{score:.2f}] Table {table_json.get('table_number')}")
            print(f"  Caption: {table_json.get('caption', 'N/A')[:80]}...")
            for signal_name, (signal_score, signal_reason) in signals.items():
                print(f"  {signal_name}: {signal_score:.2f} - {signal_reason}")
        
        if is_results:
            results_tables.append(table_info)
    
    return results_tables


if __name__ == "__main__":
    # Test on Macours paper
    from pathlib import Path
    import sys
    
    # Determine if running from om_qex_extraction/ or project root
    cwd = Path.cwd()
    if cwd.name == "om_qex_extraction":
        tables_dir = Path("../data/final_114_combined/tables")
        text_dir = Path("../data/final_114_combined/text")
    else:
        tables_dir = Path("data/final_114_combined/tables")
        text_dir = Path("data/final_114_combined/text")
    
    # Get key from command line or use default
    key = sys.argv[1] if len(sys.argv) > 1 else "9BUBMDBG"
    
    print(f"=== Testing Smart Table Filter on {key} ===\n")
    
    results = filter_results_tables(tables_dir, text_dir, key, verbose=True)
    
    print(f"\n=== Summary ===")
    total_tables = len(list(tables_dir.glob(f'{key}_table_*.json')))
    print(f"Found {len(results)} results tables (out of {total_tables} total)")
    print(f"Filtered out: {total_tables - len(results)} descriptive/balance tables")
    
    for table in results:
        print(f"  - Table {table['table_number']}: {table['caption'][:60]}...")
