#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Run data extraction on papers.

Usage:
  python run_extraction.py --test         # Test on 1 paper
  python run_extraction.py --sample 5     # Run on 5 papers
  python run_extraction.py --all          # Run on all 95 papers
"""

import sys
import io

# Force UTF-8 output encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import argparse
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from src.extraction_engine import ExtractionEngine, load_metadata_from_master


def main():
    parser = argparse.ArgumentParser(description="Run LLM-based data extraction")
    parser.add_argument('--mode', type=str, choices=['om', 'qex'], default='qex',
                        help='Extraction mode: "om" for outcome mapping or "qex" for quantitative extraction')
    parser.add_argument('--test', action='store_true', help='Test on 1 paper')
    parser.add_argument('--sample', type=int, help='Run on N sample papers')
    parser.add_argument('--all', action='store_true', help='Run on all papers')
    parser.add_argument('--keys', nargs='+', help='Run on specific keys (e.g., CV27ZK8Q 35NWH5BA)')
    parser.add_argument('--output', type=str, help='Custom output directory')
    
    args = parser.parse_args()
    
    # Paths
    project_root = Path(__file__).parent.parent
    config_path = Path(__file__).parent / "config" / "config.yaml"
    tei_dir = project_root / "data" / "grobid_outputs" / "tei"
    master_file = project_root / "data" / "raw" / "Master file of included studies (n=114) 11 Nov(data).csv"
    
    # Default output directory based on mode
    if args.output:
        output_dir = Path(args.output)
    else:
        output_dir = Path(__file__).parent / "outputs" / f"{args.mode}_extractions"
    
    # Get TEI files
    all_tei_files = sorted(list(tei_dir.glob("*.tei.xml")))
    
    if not all_tei_files:
        print("❌ No TEI files found in data/grobid_outputs/tei/")
        return 1
    
    # Select files based on arguments
    if args.test:
        tei_files = all_tei_files[:1]
        print(f"🧪 TEST MODE ({args.mode.upper()}): Running on 1 paper")
    elif args.sample:
        tei_files = all_tei_files[:args.sample]
        print(f"📊 SAMPLE MODE ({args.mode.upper()}): Running on {len(tei_files)} papers")
    elif args.keys:
        # Extract key from filename (remove .tei.xml extension)
        tei_files = [f for f in all_tei_files if f.name.replace('.tei.xml', '') in args.keys]
        print(f"🎯 SPECIFIC KEYS ({args.mode.upper()}): Running on {len(tei_files)} papers")
        if len(tei_files) != len(args.keys):
            print(f"⚠️  Warning: Found {len(tei_files)} of {len(args.keys)} requested keys")
    elif args.all:
        tei_files = all_tei_files
        print(f"🚀 FULL RUN ({args.mode.upper()}): Running on all {len(tei_files)} papers")
    else:
        print("Please specify --test, --sample N, --keys [KEYS], or --all")
        parser.print_help()
        return 1
    
    # Load metadata
    print(f"\n📋 Loading metadata from master file...")
    try:
        metadata_map = load_metadata_from_master(master_file)
        print(f"✅ Loaded metadata for {len(metadata_map)} papers")
    except Exception as e:
        print(f"⚠️  Could not load metadata: {e}")
        metadata_map = None
    
    # Initialize engine
    print(f"\n🔧 Initializing extraction engine ({args.mode.upper()} mode)...")
    engine = ExtractionEngine(config_path, mode=args.mode)
    
    # Run extraction
    print(f"\n{'='*60}")
    print(f"STARTING EXTRACTION")
    print(f"{'='*60}\n")
    
    results = engine.extract_batch(tei_files, metadata_map)
    
    # Save results
    if results:
        print(f"\n💾 Saving results...")
        engine.save_results(results, output_dir)
        
        print(f"\n{'='*60}")
        print(f"✅ EXTRACTION COMPLETE")
        print(f"{'='*60}")
        print(f"\n📊 Results:")
        print(f"  - Successful: {len(results)}/{len(tei_files)} papers")
        print(f"  - Output directory: {output_dir}")
        print(f"  - JSON files: {output_dir / 'json'}")
        print(f"  - CSV file: {output_dir / 'extracted_data.csv'}")
        print(f"  - Summary: {output_dir / 'extraction_summary.txt'}")
    else:
        print(f"\n❌ No successful extractions")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
