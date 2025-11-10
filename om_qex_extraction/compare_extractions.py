"""
Compare LLM extractions with human ground truth.

Usage:
  python compare_extractions.py --llm outputs/extractions/extracted_data.csv
"""

import sys
import argparse
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from src.comparer import ExtractionComparer


def main():
    parser = argparse.ArgumentParser(description="Compare LLM vs Human extractions")
    parser.add_argument('--llm', type=str, help='Path to LLM extraction CSV')
    parser.add_argument('--llm-json', type=str, help='Path to LLM extraction JSON directory')
    parser.add_argument('--human', type=str, help='Path to human extraction CSV (optional, uses default)')
    parser.add_argument('--output', type=str, help='Output directory for comparison results')
    parser.add_argument('--tolerance', type=float, default=0.01, help='Numeric tolerance (default: 0.01 = 1%%)')
    
    args = parser.parse_args()
    
    # Paths
    project_root = Path(__file__).parent.parent
    
    # Default human extraction path
    if args.human:
        human_csv = Path(args.human)
    else:
        human_csv = project_root / "data" / "human_extraction" / "8 week SR QEX Pierre SOF and TEEP(Quant Extraction Form).csv"
    
    # LLM extraction path
    if args.llm:
        llm_csv = Path(args.llm)
        llm_json_dir = None
    elif args.llm_json:
        llm_csv = None
        llm_json_dir = Path(args.llm_json)
    else:
        # Default: use the outputs from extraction
        llm_csv = Path(__file__).parent / "outputs" / "extractions" / "extracted_data.csv"
        llm_json_dir = None
    
    # Output path
    if args.output:
        output_dir = Path(args.output)
    else:
        output_dir = Path(__file__).parent / "outputs" / "comparison"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Verify files exist
    if not human_csv.exists():
        print(f"ERROR: Human extraction CSV not found: {human_csv}")
        return 1
    
    if llm_csv and not llm_csv.exists():
        print(f"ERROR: LLM extraction CSV not found: {llm_csv}")
        return 1
    
    if llm_json_dir and not llm_json_dir.exists():
        print(f"ERROR: LLM extraction JSON directory not found: {llm_json_dir}")
        return 1
    
    print("=" * 80)
    print("LLM vs HUMAN EXTRACTION COMPARISON")
    print("=" * 80)
    print(f"\nHuman extraction: {human_csv.name}")
    if llm_csv:
        print(f"LLM extraction: {llm_csv}")
    else:
        print(f"LLM extraction: {llm_json_dir}")
    print(f"Output directory: {output_dir}\n")
    
    # Initialize comparer
    comparer = ExtractionComparer(numeric_tolerance=args.tolerance)
    
    # Load data
    print("Loading data...")
    human_df = comparer.load_human_extraction(human_csv)
    llm_df = comparer.load_llm_extractions(llm_csv=llm_csv, llm_json_dir=llm_json_dir)
    
    # Compare
    print("\nComparing extractions...")
    comparison_df = comparer.compare_extractions(llm_df, human_df)
    
    if len(comparison_df) == 0:
        print("ERROR: No matching papers found between LLM and human extractions")
        print("\nPossible issues:")
        print("  - Study IDs don't match")
        print("  - LLM extractions are empty")
        print("  - Human extraction CSV format incorrect")
        return 1
    
    print(f"OK: Compared {len(comparison_df)} papers")
    
    # Calculate metrics
    print("\nCalculating agreement metrics...")
    metrics = comparer.calculate_agreement_metrics(comparison_df)
    
    # Save results
    print("\nSaving results...")
    
    # Save detailed comparison CSV
    comparison_csv = output_dir / "detailed_comparison.csv"
    comparison_df.to_csv(comparison_csv, index=False)
    print(f"  - Detailed comparison: {comparison_csv}")
    
    # Save metrics JSON
    import json
    metrics_json = output_dir / "agreement_metrics.json"
    with open(metrics_json, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)
    print(f"  - Metrics JSON: {metrics_json}")
    
    # Generate report
    report_txt = output_dir / "comparison_report.txt"
    comparer.generate_report(comparison_df, metrics, report_txt)
    print(f"  - Report: {report_txt}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\nPapers compared: {metrics['total_papers']}")
    print(f"Overall agreement: {metrics['overall_agreement']:.1%}")
    
    print("\nTop 5 fields by agreement:")
    sorted_fields = sorted(
        metrics['field_agreements'].items(),
        key=lambda x: x[1]['rate'],
        reverse=True
    )
    for field, stats in sorted_fields[:5]:
        print(f"  {field}: {stats['rate']:.1%} ({stats['agreements']}/{stats['total']})")
    
    print("\nBottom 5 fields by agreement:")
    for field, stats in sorted_fields[-5:]:
        print(f"  {field}: {stats['rate']:.1%} ({stats['agreements']}/{stats['total']})")
    
    print(f"\nFull results saved to: {output_dir}")
    print(f"Read the report: {report_txt}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
