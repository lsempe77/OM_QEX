"""
V2 Pipeline Orchestrator

Main entry point for running the complete V2 extraction pipeline.

Usage:
    python run_pipeline_v2.py --keys PHRKN65M --verbose
    python run_pipeline_v2.py --keys PHRKN65M --phases 1,2,3 --verbose
    python run_pipeline_v2.py --sample 5
    python run_pipeline_v2.py --all
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional, Dict
import yaml
from openai import OpenAI

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from phase1_table_discovery import Phase1TableDiscovery
from phase2_table_filtering import Phase2TableFiltering
from phase3_tei_extraction import Phase3TEIExtraction
from phase3b_pdf_vision import Phase3bPDFVision
from phase4_outcome_mapping import Phase4OutcomeMapping
from phase5_qex_extraction import Phase5QEXExtraction
from phase6_postprocessing import Phase6PostProcessing

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class V2Pipeline:
    """
    V2 Extraction Pipeline Orchestrator.
    
    Runs phases 1-6 in sequence:
    1. Table Discovery (LLM)
    2. Table Filtering (LLM or heuristic)
    3. TEI Extraction (LLM)
    3b. PDF Vision (if needed)
    4. Outcome Mapping (OM)
    5. QEX Extraction (with batching)
    6. Post-Processing
    """
    
    def __init__(self, config_path: Path):
        self.config = self._load_config(config_path)
        self.client = self._initialize_client()
        self.model = self.config['model']['name']
        
        # Initialize phases
        self.phase1 = Phase1TableDiscovery(self.client, self.model, self.config)
        self.phase2 = Phase2TableFiltering(self.client, self.model, self.config)
        self.phase3 = Phase3TEIExtraction(self.client, self.model, self.config)
        self.phase3b = Phase3bPDFVision(self.client, self.model, self.config)
        self.phase4 = Phase4OutcomeMapping(self.client, self.model, self.config)
        self.phase5 = Phase5QEXExtraction(self.client, self.model, self.config)
        self.phase6 = Phase6PostProcessing(self.client, self.model, self.config)
        
        # Output directories
        self.output_base = Path(self.config['paths']['output_base'])
        self._create_output_dirs()
    
    def _load_config(self, config_path: Path) -> Dict:
        """Load configuration from YAML."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _initialize_client(self) -> OpenAI:
        """Initialize OpenRouter client."""
        return OpenAI(
            base_url=self.config['api']['openrouter']['base_url'],
            api_key=self.config['api']['openrouter']['api_key'].strip('${}')
        )
    
    def _create_output_dirs(self):
        """Create output directories for each phase."""
        for phase in ['phase1', 'phase2', 'phase3', 'phase3b', 'phase4', 'phase5', 'phase6']:
            phase_dir = self.output_base / phase
            phase_dir.mkdir(parents=True, exist_ok=True)
    
    def run(self, key: str, phases: Optional[List[int]] = None, verbose: bool = False) -> Dict:
        """
        Run pipeline for a single paper.
        
        Args:
            key: Paper identifier (e.g., "PHRKN65M")
            phases: List of phases to run (default: all)
            verbose: Enable verbose logging
        
        Returns:
            Dictionary with final results
        """
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
        logger.info(f"=" * 80)
        logger.info(f"V2 PIPELINE: {key}")
        logger.info(f"=" * 80)
        
        # Get file paths
        tei_dir = Path(self.config['paths']['tei_dir'])
        if not tei_dir.is_absolute():
            tei_dir = Path(__file__).parent.parent / tei_dir
        
        tei_file = tei_dir / f"{key}.tei.xml"
        
        pdf_dir = Path(self.config['paths'].get('pdf_dir', 'data/raw_pdfs'))
        if not pdf_dir.is_absolute():
            pdf_dir = Path(__file__).parent.parent / pdf_dir
        pdf_file = pdf_dir / f"{key}.pdf"
        
        if not tei_file.exists():
            logger.error(f"TEI file not found: {tei_file}")
            return {'error': 'TEI file not found'}
        
        results = {}
        
        # Determine which phases to run
        all_phases = phases or [1, 2, 3, 4, 5, 6]
        
        # Phase 1: Table Discovery
        if 1 in all_phases:
            logger.info("\n--- PHASE 1: Table Discovery ---")
            phase1_result = self.phase1.discover_tables(tei_file, key)
            self.phase1.save_result(phase1_result, self.output_base / 'phase1')
            results['phase1'] = phase1_result
        else:
            # Load existing result
            phase1_file = self.output_base / 'phase1' / f"{key}_phase1.json"
            if phase1_file.exists():
                import json
                with open(phase1_file, 'r') as f:
                    results['phase1'] = json.load(f)
        
        # Phase 2: Table Filtering
        if 2 in all_phases:
            logger.info("\n--- PHASE 2: Table Filtering ---")
            phase2_result = self.phase2.filter_tables(results['phase1'], tei_file)
            self.phase2.save_result(phase2_result, self.output_base / 'phase2')
            results['phase2'] = phase2_result
        else:
            # Load existing result
            phase2_file = self.output_base / 'phase2' / f"{key}_phase2.json"
            if phase2_file.exists():
                import json
                with open(phase2_file, 'r') as f:
                    results['phase2'] = json.load(f)
        
        # Phase 3: TEI Extraction
        if 3 in all_phases:
            logger.info("\n--- PHASE 3: TEI Extraction ---")
            phase3_result = self.phase3.extract_from_tei(results['phase2'], tei_file, key)
            self.phase3.save_result(phase3_result, self.output_base / 'phase3')
            results['phase3'] = phase3_result
            
            # Phase 3b: Check if PDF Vision needed
            should_trigger, missing_tables = self.phase3b.should_trigger(
                results['phase1'], 
                results['phase2'], 
                phase3_result
            )
            
            if should_trigger:
                logger.info("\n--- PHASE 3b: PDF Vision Fallback ---")
                logger.info(f"Triggering PDF vision for missing tables: {missing_tables}")
                
                if pdf_file.exists():
                    pdf_result = self.phase3b.extract_from_pdf(pdf_file, missing_tables, key)
                    self.phase3b.save_result(pdf_result, self.output_base / 'phase3b')
                    
                    # Merge with TEI results
                    phase3_result = self.phase3b.merge_with_tei_results(phase3_result, pdf_result)
                    
                    # Re-save merged Phase 3 result
                    self.phase3.save_result(phase3_result, self.output_base / 'phase3')
                    
                    results['phase3'] = phase3_result
                    results['phase3b'] = pdf_result
                else:
                    logger.warning(f"PDF file not found: {pdf_file}")
                    logger.warning("Skipping PDF vision fallback")
        else:
            # Load existing result
            phase3_file = self.output_base / 'phase3' / f"{key}_phase3.json"
            if phase3_file.exists():
                import json
                with open(phase3_file, 'r') as f:
                    results['phase3'] = json.load(f)
        
        # Phase 4: Outcome Mapping
        if 4 in all_phases:
            logger.info("\n--- PHASE 4: Outcome Mapping (OM) ---")
            phase4_result = self.phase4.map_outcomes(results['phase3'], tei_file, key)
            self.phase4.save_result(phase4_result, self.output_base / 'phase4')
            results['phase4'] = phase4_result
        else:
            # Load existing result
            phase4_file = self.output_base / 'phase4' / f"{key}_phase4.json"
            if phase4_file.exists():
                import json
                with open(phase4_file, 'r') as f:
                    results['phase4'] = json.load(f)
        
        # Phase 5: QEX Extraction
        if 5 in all_phases:
            logger.info("\n--- PHASE 5: QEX Extraction ---")
            phase5_result = self.phase5.extract_quantitative(results['phase4'], tei_file, key)
            self.phase5.save_result(phase5_result, self.output_base / 'phase5')
            results['phase5'] = phase5_result
        else:
            # Load existing result
            phase5_file = self.output_base / 'phase5' / f"{key}_phase5.json"
            if phase5_file.exists():
                import json
                with open(phase5_file, 'r') as f:
                    results['phase5'] = json.load(f)
        
        # Phase 6: Post-Processing
        if 6 in all_phases:
            logger.info("\n--- PHASE 6: Post-Processing ---")
            phase6_result = self.phase6.post_process(results['phase5'], key)
            self.phase6.save_result(phase6_result, self.output_base / 'phase6')
            results['phase6'] = phase6_result
        
        logger.info(f"\n{'=' * 80}")
        logger.info(f"PIPELINE COMPLETE: {key}")
        logger.info(f"{'=' * 80}")
        
        return results


def main():
    parser = argparse.ArgumentParser(description='V2 Extraction Pipeline')
    
    # Paper selection
    paper_group = parser.add_mutually_exclusive_group(required=True)
    paper_group.add_argument('--keys', type=str, help='Comma-separated paper keys (e.g., PHRKN65M,ABM3E3ZP)')
    paper_group.add_argument('--sample', type=int, help='Random sample of N papers')
    paper_group.add_argument('--all', action='store_true', help='Process all papers')
    
    # Phase selection
    parser.add_argument('--phases', type=str, help='Comma-separated phases to run (default: all)')
    
    # Options
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--config', type=str, default='config/config.yaml', help='Config file path')
    
    args = parser.parse_args()
    
    # Parse phases
    phases = None
    if args.phases:
        phases = [int(p) for p in args.phases.split(',')]
    
    # Initialize pipeline
    config_path = Path(__file__).parent / args.config
    pipeline = V2Pipeline(config_path)
    
    # Get paper keys
    if args.keys:
        keys = args.keys.split(',')
    elif args.sample:
        # TODO: Implement sampling
        logger.error("--sample not yet implemented")
        return
    elif args.all:
        # TODO: Implement all papers
        logger.error("--all not yet implemented")
        return
    
    # Run pipeline for each paper
    for key in keys:
        try:
            pipeline.run(key, phases=phases, verbose=args.verbose)
        except Exception as e:
            logger.error(f"Error processing {key}: {e}", exc_info=True)


if __name__ == '__main__':
    main()
