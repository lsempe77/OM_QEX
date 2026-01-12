#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Two-Stage Extraction Pipeline: OM → QEX

Stage 1 (OM): Identify ALL outcomes and their precise locations
Stage 2 (QEX): Extract detailed statistical data using OM guidance

This approach ensures:
- Comprehensive outcome coverage (OM finds everything)
- Focused QEX extraction (only on identified outcomes)
- Lower token costs (QEX gets precise hints, not full paper)
- Better accuracy (QEX knows exactly where to look)

Usage:
  python run_twostage_extraction.py --keys PHRKN65M
  python run_twostage_extraction.py --sample 5
  python run_twostage_extraction.py --all
"""

from html import parser
import sys
import io
import argparse
import json
from pathlib import Path

# Force UTF-8 output encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from src.extraction_engine import ExtractionEngine, load_metadata_from_master


def run_twostage_extraction(tei_files, metadata_map, config_path, output_dir,
                           stage2_only=False, om_input_dir=None):
    """
    Run two-stage extraction pipeline.
    
    Args:
        tei_files: List of TEI file paths
        metadata_map: Dict mapping Key -> metadata
        config_path: Path to config.yaml
        output_dir: Base output directory
    
    Returns:
        Dict with OM and QEX results
    """
    output_dir = Path(output_dir)
    om_dir = output_dir / "stage1_om"
    qex_dir = output_dir / "stage2_qex"
        # If Stage 2 only: load OM results from disk (outputs/<...>/stage1_om/json/<key>.json)
    if stage2_only:
        om_dir = Path(om_input_dir) if om_input_dir else om_dir
        om_json_dir = om_dir / "json"

        om_results = []
        missing = []

        for tei_file in tei_files:
            key = tei_file.stem  # e.g., "ZBAE7IPZ.tei"
            om_json = om_json_dir / f"{key}.json"
            if not om_json.exists():
                missing.append(key)
                continue

            with open(om_json, "r", encoding="utf-8") as f:
                om_result = json.load(f)

            # Ensure key is present for downstream logging/saving
            om_result["_key"] = om_result.get("_key", key)
            om_results.append(om_result)

        if missing:
            print(f"⚠️  Stage2-only: missing OM JSON for {len(missing)}/{len(tei_files)} keys")
            print("    Missing examples:", ", ".join(missing[:5]))

        if not om_results:
            print("❌ Stage2-only failed: no OM JSONs found. Run Stage 1 once or point --om-input to the correct folder.")
            return None

        total_outcomes = sum(len(r.get("outcomes", [])) for r in om_results)
        print(f"✅ Loaded OM guidance from disk: {total_outcomes} outcomes across {len(om_results)} papers")

    else:
        # Existing Stage 1 OM flow (unchanged)
        om_engine = ExtractionEngine(config_path, mode="om")
        om_results = om_engine.extract_batch(tei_files, metadata_map)

        if not om_results:
            print("❌ Stage 1 (OM) failed - no outcomes identified")
            return None

        om_engine.save_results(om_results, om_dir)

        total_outcomes = sum(len(r.get('outcomes', [])) for r in om_results)
        print(f"\n✅ Stage 1 Complete: Found {total_outcomes} outcomes across {len(om_results)} papers")
    
    print(f"\n{'='*70}")
    print(f"TWO-STAGE EXTRACTION PIPELINE")
    print(f"{'='*70}")
    print(f"Papers to process: {len(tei_files)}")
    print(f"Output directory: {output_dir}")
    

    # ========================================================================
    # STAGE 2: QEX - Extract detailed data using OM guidance
    # ========================================================================
    print(f"\n{'='*70}")
    print(f"STAGE 2: QUANTITATIVE EXTRACTION (QEX)")
    print(f"Extracting detailed statistics using OM guidance...")
    print(f"{'='*70}\n")
    
    qex_engine = ExtractionEngine(config_path, mode="qex")
    
    # Extract with OM guidance
    qex_results = []
    for i, (tei_file, om_result) in enumerate(zip(tei_files, om_results), 1):
        key = tei_file.stem
        metadata = metadata_map.get(key) if metadata_map else None
        
        print(f"\n{'='*60}")
        print(f"Paper {i}/{len(tei_files)}: {tei_file.name}")
        print(f"{'='*60}")
        
        # Get OM outcomes as guidance
        om_outcomes = om_result.get('outcomes', [])
        print(f"OM found {len(om_outcomes)} outcomes - using as guidance for QEX")
        
        # Extract with guidance
        qex_result = qex_engine.extract_with_om_guidance(tei_file, metadata, om_outcomes)
        
        if qex_result:
            qex_result['_key'] = key
            qex_result['_tei_file'] = str(tei_file)
            qex_result['_om_outcome_count'] = len(om_outcomes)  # Track how many OM found
            qex_results.append(qex_result)
        else:
            print(f"⚠️  QEX extraction failed for {tei_file.name}")
    
    if not qex_results:
        print("\n❌ Stage 2 (QEX) failed - no detailed extractions")
        return None
    
    # Save QEX results
    qex_engine.save_results(qex_results, qex_dir)
    
    # Count QEX outcomes
    qex_outcomes = sum(len(r.get('outcomes', [])) for r in qex_results)
    print(f"\n✅ Stage 2 Complete: Extracted {qex_outcomes} outcomes with full details")
    print(f"   Average: {qex_outcomes / len(qex_results):.1f} detailed outcomes per paper")
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print(f"\n{'='*70}")
    print(f"TWO-STAGE PIPELINE COMPLETE")
    print(f"{'='*70}")
    print(f"\n📊 Results:")
    print(f"   Stage 1 (OM):  {total_outcomes} outcomes identified")
    print(f"   Stage 2 (QEX): {qex_outcomes} outcomes with full statistical details")
    print(f"   Conversion:    {qex_outcomes}/{total_outcomes} ({100*qex_outcomes/total_outcomes:.0f}%)")
    print(f"\n📂 Outputs:")
    print(f"   OM results:  {om_dir}")
    print(f"   QEX results: {qex_dir}")
    
    return {
        'om_results': om_results,
        'qex_results': qex_results,
        'om_outcome_count': total_outcomes,
        'qex_outcome_count': qex_outcomes
    }


def main():
    parser = argparse.ArgumentParser(description="Two-stage extraction: OM → QEX")
    parser.add_argument('--test', action='store_true', help='Test on 1 paper')
    parser.add_argument('--sample', type=int, help='Run on N sample papers')
    parser.add_argument('--all', action='store_true', help='Run on all papers')
    parser.add_argument('--keys', nargs='+', help='Run on specific keys')
    parser.add_argument('--output', type=str, default='outputs/twostage',
                        help='Output directory (default: outputs/twostage)')
    parser.add_argument('--stage2-only', action='store_true',
                    help='Skip Stage 1; run Stage 2 using saved OM JSONs from disk')
    parser.add_argument('--om-input', type=str, default=None,
                    help='Path to stage1_om directory (default: <output>/stage1_om)')
    
    args = parser.parse_args()
    
    # Paths
    project_root = Path(__file__).parent.parent
    config_path = Path(__file__).parent / "config" / "config.yaml"
    tei_dir = project_root / "data" / "grobid_outputs" / "tei"
    master_file = project_root / "data" / "raw" / "Master file of included studies (n=114) 11 Nov(data).csv"
    
    # Get TEI files
    all_tei_files = sorted(tei_dir.glob("*.tei.xml"))
    
    if args.test:
        tei_files = all_tei_files[:1]
        print(f"🧪 TEST MODE: Running on 1 paper")
    elif args.sample:
        tei_files = all_tei_files[:args.sample]
        print(f"📊 SAMPLE MODE: Running on {len(tei_files)} papers")
    elif args.keys:
        keys_norm = {k.replace(".tei.xml","").replace(".tei","") for k in args.keys}
        tei_files = [f for f in all_tei_files if f.name.replace('.tei.xml', '') in keys_norm]
        print(f"🎯 SPECIFIC KEYS: Running on {len(tei_files)} papers")
        if len(tei_files) != len(keys_norm):
            print(f"⚠️  Warning: Found {len(tei_files)} of {len(keys_norm)} requested keys")
    elif args.all:
        tei_files = all_tei_files
        print(f"🌐 ALL PAPERS: Running on {len(tei_files)} papers")
    else:
        print("❌ Must specify --test, --sample N, --keys, or --all")
        return 1
    
    # Load metadata
    print(f"\n📋 Loading metadata from master file...")
    try:
        metadata_map = load_metadata_from_master(master_file)
        print(f"✅ Loaded metadata for {len(metadata_map)} papers")
    except Exception as e:
        print(f"⚠️  Could not load metadata: {e}")
        metadata_map = None
    
    # Run two-stage extraction
    results = run_twostage_extraction(
    tei_files,
    metadata_map,
    config_path,
    args.output,
    stage2_only=args.stage2_only,
    om_input_dir=args.om_input,
)
    
    if results:
        return 0
    else:
        print("\n❌ Two-stage extraction failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
