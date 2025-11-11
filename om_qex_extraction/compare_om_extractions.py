"""
Compare LLM OM extractions with human ground truth.

This script compares outcome measures (OM) extracted by the LLM against human-coded outcomes
to validate the LLM's ability to identify all relevant outcomes in a paper.

Usage:
  python compare_om_extractions.py --llm outputs/om_extractions/extracted_data.csv
  python compare_om_extractions.py --llm-json outputs/om_extractions/json/
"""

import sys
import json
import argparse
import pandas as pd
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))


class OMComparer:
    """Compare LLM OM extractions with human extractions."""
    
    # Studies to exclude (duplicates and qualitative-only)
    EXCLUDED_STUDIES = {'121498800', '121498801', '121498803'}
    
    def __init__(self):
        """Initialize OM comparer."""
        pass
    
    def load_human_om(self, human_csv: Path) -> pd.DataFrame:
        """
        Load human OM extraction data.
        
        Args:
            human_csv: Path to OM_human_extraction.csv
        
        Returns:
            DataFrame with human OM extractions
        """
        df = pd.read_csv(human_csv)
        
        # Extract base study ID (remove _1, _2 suffix)
        df['study_id_base'] = df['EPPI ID'].str.split('_').str[0]
        
        # Filter out excluded studies
        before = len(df)
        df = df[~df['study_id_base'].isin(self.EXCLUDED_STUDIES)]
        after = len(df)
        
        if before > after:
            print(f"  Excluded {before - after} rows from {len(self.EXCLUDED_STUDIES)} special case studies")
        
        print(f"  Loaded {len(df)} outcome rows from {df['study_id_base'].nunique()} studies")
        
        return df
    
    def load_llm_om(self, llm_csv: Path = None, llm_json_dir: Path = None) -> pd.DataFrame:
        """
        Load LLM OM extraction data.
        
        Args:
            llm_csv: Path to consolidated CSV from OM extraction
            llm_json_dir: Path to directory with individual JSON files
        
        Returns:
            DataFrame with LLM extractions
        """
        if llm_csv and llm_csv.exists():
            # Load from CSV (flattened multi-outcome format)
            df = pd.read_csv(llm_csv)
            
        elif llm_json_dir and llm_json_dir.exists():
            # Load from individual JSON files and flatten
            records = []
            for json_file in llm_json_dir.glob("*.json"):
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Extract study_id from filename or data
                if 'study_id' in data:
                    study_id = data['study_id']
                else:
                    # Parse from filename (e.g., PHRKN65M.tei.json)
                    study_id = json_file.stem.replace('.tei', '')
                
                # Handle outcomes as list or dict
                outcomes = data.get('outcomes', [])
                if isinstance(outcomes, dict):
                    outcomes = [outcomes]
                
                # Flatten each outcome
                for idx, outcome in enumerate(outcomes):
                    record = {
                        'study_id': study_id,
                        'outcome_number': idx + 1,
                        'outcome_name': outcome.get('outcome_name', ''),
                        'outcome_group': outcome.get('outcome_group', ''),
                        'effect_size': outcome.get('effect_size', ''),
                        'standard_error': outcome.get('standard_error', ''),
                        'p_value': outcome.get('p_value', ''),
                    }
                    records.append(record)
            
            df = pd.DataFrame(records)
        else:
            raise ValueError("Must provide either llm_csv or llm_json_dir")
        
        print(f"  Loaded {len(df)} outcome rows from {df['study_id'].nunique()} studies")
        
        return df
    
    def map_study_ids(self, project_root: Path) -> Dict[str, str]:
        """
        Create mapping from study IDs to Keys for matching.
        
        Args:
            project_root: Project root directory
        
        Returns:
            Dictionary mapping study_id -> key
        """
        # Load fulltext metadata
        metadata_file = project_root / "data" / "raw" / "fulltext_metadata.csv"
        if not metadata_file.exists():
            print(f"WARNING: Metadata file not found: {metadata_file}")
            return {}
        
        metadata = pd.read_csv(metadata_file)
        
        # Create mapping: paper_id (study ID) -> Key
        mapping = {}
        for _, row in metadata.iterrows():
            paper_id = str(row['paper_id'])
            key = row['Key']
            mapping[paper_id] = key
        
        return mapping
    
    def compare_studies(self, llm_df: pd.DataFrame, human_df: pd.DataFrame, 
                       id_mapping: Dict[str, str]) -> Dict[str, Dict]:
        """
        Compare LLM and human extractions by study.
        
        Args:
            llm_df: LLM extractions
            human_df: Human extractions
            id_mapping: Mapping from study_id -> key
        
        Returns:
            Dictionary with comparison results per study
        """
        results = {}
        
        # Reverse mapping: key -> study_id
        key_to_id = {v: k for k, v in id_mapping.items()}
        
        # Group human outcomes by study
        human_by_study = human_df.groupby('study_id_base')
        
        for study_id, human_group in human_by_study:
            # Find corresponding LLM data
            key = id_mapping.get(study_id)
            
            if not key:
                # Study ID not in mapping
                results[study_id] = {
                    'study_id': study_id,
                    'key': None,
                    'human_count': len(human_group),
                    'llm_count': 0,
                    'status': 'no_key_mapping'
                }
                continue
            
            # Get LLM outcomes for this key
            llm_group = llm_df[llm_df['study_id'] == key]
            
            human_count = len(human_group)
            llm_count = len(llm_group)
            
            # Get outcome names
            human_outcomes = set(human_group[human_group.columns[6]].dropna())  # "Outcome category" column
            llm_outcomes = set(llm_group['outcome_name'].dropna())
            
            # Calculate metrics
            if llm_count == 0:
                status = 'llm_missing'
                recall = 0.0
            else:
                recall = llm_count / human_count if human_count > 0 else 0.0
                if llm_count == human_count:
                    status = 'exact_match'
                elif llm_count > human_count:
                    status = 'llm_over_extracted'
                else:
                    status = 'llm_under_extracted'
            
            results[study_id] = {
                'study_id': study_id,
                'key': key,
                'author': human_group.iloc[0]['Author (year)'] if 'Author (year)' in human_group.columns else '',
                'human_count': human_count,
                'llm_count': llm_count,
                'recall': recall,
                'status': status,
                'human_outcomes': list(human_outcomes),
                'llm_outcomes': list(llm_outcomes)
            }
        
        return results
    
    def calculate_metrics(self, comparison_results: Dict[str, Dict]) -> Dict:
        """
        Calculate overall metrics from comparison results.
        
        Args:
            comparison_results: Results from compare_studies()
        
        Returns:
            Dictionary with aggregate metrics
        """
        total_studies = len(comparison_results)
        total_human_outcomes = sum(r['human_count'] for r in comparison_results.values())
        total_llm_outcomes = sum(r['llm_count'] for r in comparison_results.values())
        
        # Count by status
        status_counts = defaultdict(int)
        for result in comparison_results.values():
            status_counts[result['status']] += 1
        
        # Calculate recall (how many human outcomes did LLM find?)
        recalls = [r['recall'] for r in comparison_results.values() if r['status'] != 'no_key_mapping']
        avg_recall = sum(recalls) / len(recalls) if recalls else 0.0
        
        # Precision at study level (did LLM find at least 1 outcome?)
        studies_with_llm = sum(1 for r in comparison_results.values() if r['llm_count'] > 0)
        studies_with_human = sum(1 for r in comparison_results.values() if r['human_count'] > 0)
        
        return {
            'total_studies': total_studies,
            'total_human_outcomes': total_human_outcomes,
            'total_llm_outcomes': total_llm_outcomes,
            'avg_recall': avg_recall,
            'studies_with_llm_extraction': studies_with_llm,
            'studies_with_human_extraction': studies_with_human,
            'status_distribution': dict(status_counts),
            'outcome_recall': total_llm_outcomes / total_human_outcomes if total_human_outcomes > 0 else 0.0
        }
    
    def generate_report(self, comparison_results: Dict[str, Dict], 
                       metrics: Dict, output_file: Path):
        """
        Generate detailed comparison report.
        
        Args:
            comparison_results: Per-study comparison results
            metrics: Aggregate metrics
            output_file: Path to save report
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("OM EXTRACTION COMPARISON REPORT\n")
            f.write("="*80 + "\n\n")
            
            f.write("OVERALL METRICS\n")
            f.write("-"*80 + "\n")
            f.write(f"Total studies compared: {metrics['total_studies']}\n")
            f.write(f"Total human outcomes: {metrics['total_human_outcomes']}\n")
            f.write(f"Total LLM outcomes: {metrics['total_llm_outcomes']}\n")
            f.write(f"Average recall per study: {metrics['avg_recall']:.1%}\n")
            f.write(f"Overall outcome recall: {metrics['outcome_recall']:.1%}\n")
            f.write(f"Studies with LLM extraction: {metrics['studies_with_llm_extraction']}/{metrics['studies_with_human_extraction']}\n\n")
            
            f.write("STATUS DISTRIBUTION\n")
            f.write("-"*80 + "\n")
            for status, count in sorted(metrics['status_distribution'].items(), key=lambda x: -x[1]):
                f.write(f"  {status}: {count}\n")
            f.write("\n")
            
            f.write("PER-STUDY DETAILS\n")
            f.write("-"*80 + "\n\n")
            
            # Sort by recall (worst first)
            sorted_results = sorted(
                comparison_results.values(),
                key=lambda x: (x['status'] != 'llm_missing', x['recall'])
            )
            
            for result in sorted_results:
                f.write(f"Study: {result['study_id']} ({result['author']})\n")
                f.write(f"  Key: {result['key']}\n")
                f.write(f"  Human outcomes: {result['human_count']}\n")
                f.write(f"  LLM outcomes: {result['llm_count']}\n")
                f.write(f"  Recall: {result['recall']:.1%}\n")
                f.write(f"  Status: {result['status']}\n")
                
                if result['human_outcomes']:
                    f.write(f"  Human outcome names:\n")
                    for outcome in result['human_outcomes']:
                        f.write(f"    - {outcome}\n")
                
                if result['llm_outcomes']:
                    f.write(f"  LLM outcome names:\n")
                    for outcome in result['llm_outcomes']:
                        f.write(f"    - {outcome}\n")
                
                f.write("\n")


def main():
    parser = argparse.ArgumentParser(description="Compare LLM OM vs Human OM extractions")
    parser.add_argument('--llm', type=str, help='Path to LLM OM extraction CSV')
    parser.add_argument('--llm-json', type=str, help='Path to LLM OM extraction JSON directory')
    parser.add_argument('--human', type=str, help='Path to human OM CSV (optional, uses default)')
    parser.add_argument('--output', type=str, help='Output directory for comparison results')
    
    args = parser.parse_args()
    
    # Paths
    project_root = Path(__file__).parent.parent
    
    # Default human OM path
    if args.human:
        human_csv = Path(args.human)
    else:
        human_csv = project_root / "data" / "human_extraction" / "OM_human_extraction.csv"
    
    # LLM extraction path
    if args.llm:
        llm_csv = Path(args.llm)
        llm_json_dir = None
    elif args.llm_json:
        llm_csv = None
        llm_json_dir = Path(args.llm_json)
    else:
        # Default: use the outputs from OM extraction
        llm_csv = Path(__file__).parent / "outputs" / "om_extractions" / "extracted_data.csv"
        llm_json_dir = None
    
    # Output path
    if args.output:
        output_dir = Path(args.output)
    else:
        output_dir = Path(__file__).parent / "outputs" / "om_comparison"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Verify files exist
    if not human_csv.exists():
        print(f"ERROR: Human OM CSV not found: {human_csv}")
        return 1
    
    if llm_csv and not llm_csv.exists():
        print(f"ERROR: LLM OM CSV not found: {llm_csv}")
        return 1
    
    if llm_json_dir and not llm_json_dir.exists():
        print(f"ERROR: LLM OM JSON directory not found: {llm_json_dir}")
        return 1
    
    print("=" * 80)
    print("LLM vs HUMAN OM EXTRACTION COMPARISON")
    print("=" * 80)
    print(f"\nHuman OM: {human_csv.name}")
    if llm_csv:
        print(f"LLM OM: {llm_csv}")
    else:
        print(f"LLM OM: {llm_json_dir}")
    print(f"Output: {output_dir}\n")
    
    # Initialize comparer
    comparer = OMComparer()
    
    # Load data
    print("Loading data...")
    human_df = comparer.load_human_om(human_csv)
    llm_df = comparer.load_llm_om(llm_csv=llm_csv, llm_json_dir=llm_json_dir)
    
    # Load study ID mapping
    print("\nLoading study ID mapping...")
    id_mapping = comparer.map_study_ids(project_root)
    print(f"  Loaded {len(id_mapping)} study ID -> Key mappings")
    
    # Compare
    print("\nComparing extractions...")
    comparison_results = comparer.compare_studies(llm_df, human_df, id_mapping)
    
    if len(comparison_results) == 0:
        print("ERROR: No studies to compare")
        return 1
    
    print(f"  Compared {len(comparison_results)} studies")
    
    # Calculate metrics
    print("\nCalculating metrics...")
    metrics = comparer.calculate_metrics(comparison_results)
    
    # Save results
    print("\nSaving results...")
    
    # Save detailed comparison CSV
    comparison_df = pd.DataFrame.from_dict(comparison_results, orient='index')
    comparison_csv = output_dir / "om_comparison.csv"
    comparison_df.to_csv(comparison_csv, index=False)
    print(f"  - Detailed comparison: {comparison_csv}")
    
    # Save metrics JSON
    metrics_json = output_dir / "om_metrics.json"
    with open(metrics_json, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)
    print(f"  - Metrics JSON: {metrics_json}")
    
    # Generate report
    report_txt = output_dir / "om_comparison_report.txt"
    comparer.generate_report(comparison_results, metrics, report_txt)
    print(f"  - Report: {report_txt}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\nStudies compared: {metrics['total_studies']}")
    print(f"Total human outcomes: {metrics['total_human_outcomes']}")
    print(f"Total LLM outcomes: {metrics['total_llm_outcomes']}")
    print(f"Average recall per study: {metrics['avg_recall']:.1%}")
    print(f"Overall outcome recall: {metrics['outcome_recall']:.1%}")
    
    print("\nStatus distribution:")
    for status, count in sorted(metrics['status_distribution'].items(), key=lambda x: -x[1]):
        print(f"  {status}: {count}")
    
    print(f"\nFull results saved to: {output_dir}")
    print(f"Read the report: {report_txt}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
