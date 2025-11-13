"""
Phase 3b: PDF Vision Fallback

Intelligently triggers PDF vision extraction when Phase 1 found tables
that Phase 3 failed to extract from TEI.

Only extracts specific missing tables (targeted approach).
"""

import logging
from pathlib import Path
from typing import Dict, List, Set
from openai import OpenAI

logger = logging.getLogger(__name__)


class Phase3bPDFVision:
    """
    Phase 3b: Targeted PDF vision extraction for missing tables.
    
    Triggers when:
    - Phase 1 found tables that Phase 3 couldn't extract
    - Specific table numbers are missing from extraction
    """
    
    def __init__(self, client: OpenAI, model: str, config: Dict):
        self.client = client
        self.model = model
        self.config = config
    
    def should_trigger(self, phase1_result: Dict, phase2_result: Dict, phase3_result: Dict) -> tuple[bool, List[str]]:
        """
        Determine if PDF vision should trigger and which tables to extract.
        
        Args:
            phase1_result: Phase 1 table discovery results (can be None if Phase 1 not run)
            phase2_result: Phase 2 table filtering results (RESULTS vs DESCRIPTIVE)
            phase3_result: Phase 3 TEI extraction results
        
        Returns:
            (should_trigger, missing_table_numbers)
        """
        trigger_mode = self.config.get('pipeline', {}).get('phase3b_pdf_vision', {}).get('trigger_mode', 'intelligent')
        
        if trigger_mode == 'never':
            return False, []
        
        # Handle missing phase2_result gracefully
        if not phase2_result:
            logger.warning("Phase 2 results missing - cannot determine which tables need PDF vision")
            return False, []
        
        if trigger_mode == 'always':
            # Always extract all RESULTS tables from PDF
            results_tables = phase2_result.get('results_tables', [])
            return True, [t['table_number'] for t in results_tables]
        
        # Intelligent mode: check for missing RESULTS tables only
        # Don't count DESCRIPTIVE tables as missing
        results_tables = {t['table_number'] for t in phase2_result.get('results_tables', [])}
        phase3_extracted = {t['table_number'] for t in phase3_result.get('tables_extracted', []) 
                           if t.get('extraction_success', False)}
        
        missing = results_tables - phase3_extracted
        
        if missing:
            logger.info(f"Phase 3 failed to extract {len(missing)} RESULTS tables: {sorted(missing)}")
            return True, list(missing)
        
        return False, []
    
    def extract_from_pdf(self, pdf_file: Path, missing_tables: List[str], key: str) -> Dict:
        """
        Extract specific tables from PDF using vision API.
        
        Args:
            pdf_file: Path to PDF file
            missing_tables: List of table numbers to extract
            key: Paper identifier
        
        Returns:
            Dictionary with extracted outcomes from missing tables
        """
        logger.info(f"PHASE 3b: PDF Vision for {key}")
        logger.info(f"Extracting missing tables: {sorted(missing_tables)}")
        
        # Convert PDF to images
        logger.info(f"Converting PDF to images: {pdf_file.name}")
        images = self._pdf_to_images(pdf_file)
        
        if not images:
            logger.error("Failed to convert PDF to images")
            return {
                '_key': key,
                '_phase': 'phase3b_pdf_vision',
                'missing_tables_requested': missing_tables,
                'tables_extracted': [],
                'outcomes': [],
                'summary': {
                    'requested': len(missing_tables),
                    'extracted': 0,
                    'failed': len(missing_tables),
                    'error': 'pdf_conversion_failed'
                }
            }
        
        logger.info(f"Converted {len(images)} pages from PDF")
        
        # Extract tables using vision API
        outcomes = self._extract_with_vision(images, missing_tables, key)
        
        # Group outcomes by table
        tables_extracted = []
        tables_by_num = {}
        
        for outcome in outcomes:
            table_num = outcome.get('_table_number', 'unknown')
            if table_num not in tables_by_num:
                tables_by_num[table_num] = {
                    'table_number': table_num,
                    'extraction_success': True,
                    'outcomes_found': 0,
                    'extraction_method': 'pdf_vision'
                }
            tables_by_num[table_num]['outcomes_found'] += 1
        
        tables_extracted = list(tables_by_num.values())
        
        # Calculate summary
        extracted_count = len([t for t in missing_tables if str(t) in tables_by_num])
        failed_count = len(missing_tables) - extracted_count
        
        logger.info(f"Phase 3b extracted {len(outcomes)} outcomes from {extracted_count}/{len(missing_tables)} tables")
        
        return {
            '_key': key,
            '_phase': 'phase3b_pdf_vision',
            'missing_tables_requested': missing_tables,
            'tables_extracted': tables_extracted,
            'outcomes': outcomes,
            'summary': {
                'requested': len(missing_tables),
                'extracted': extracted_count,
                'failed': failed_count,
                'total_outcomes': len(outcomes)
            }
        }
    
    def _pdf_to_images(self, pdf_path: Path, dpi: int = 150) -> List[Dict]:
        """
        Convert PDF pages to images using PyMuPDF.
        
        Args:
            pdf_path: Path to PDF file
            dpi: Resolution for image conversion (150 is good balance)
        
        Returns:
            List of dicts with page_number, image_data (base64 encoded PNG)
        """
        import base64
        import fitz  # PyMuPDF
        
        images = []
        
        try:
            pdf_document = fitz.open(pdf_path)
            
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                
                # Render page to image
                zoom = dpi / 72  # 72 DPI is default
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to PNG bytes
                img_bytes = pix.pil_tobytes(format="PNG")
                
                # Base64 encode for API
                img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                
                images.append({
                    'page_number': page_num + 1,
                    'image_data': img_base64,
                    'width': pix.width,
                    'height': pix.height
                })
                
                logger.debug(f"  Converted page {page_num + 1} ({pix.width}x{pix.height})")
            
            pdf_document.close()
            logger.info(f"Converted {len(images)} pages from PDF")
            
            return images
        
        except Exception as e:
            logger.error(f"Failed to convert PDF to images: {e}")
            return []
    
    def _extract_with_vision(self, images: List[Dict], missing_tables: List[str], 
                            key: str, batch_size: int = 20) -> List[Dict]:
        """
        Extract tables from PDF images using vision API.
        
        Args:
            images: List of page images (from _pdf_to_images)
            missing_tables: Specific table numbers to extract
            key: Paper identifier
            batch_size: Maximum images per API call (20 for Claude via Bedrock)
        
        Returns:
            List of extracted outcomes
        """
        import json
        import re
        
        all_outcomes = []
        total_pages = len(images)
        num_batches = (total_pages + batch_size - 1) // batch_size
        
        logger.info(f"Processing {total_pages} pages in {num_batches} batch(es)...")
        
        for batch_idx in range(num_batches):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, total_pages)
            batch_images = images[start_idx:end_idx]
            
            logger.info(f"Batch {batch_idx + 1}/{num_batches}: Pages {start_idx + 1}-{end_idx}")
            
            # Create targeted prompt for specific tables
            tables_str = ", ".join(missing_tables)
            prompt = f"""You are analyzing a research paper PDF (pages {start_idx + 1}-{end_idx} of {total_pages}) to extract quantitative outcome data from SPECIFIC tables.

TABLES TO EXTRACT: {tables_str}

TASK:
1. Find ONLY the tables listed above (ignore all other tables)
2. These may be embedded in paragraphs or formatted as traditional tables
3. Extract ALL outcomes from these specific tables with their statistics

OUTPUT FORMAT (JSON):
{{
  "results_tables": [
    {{
      "table_number": "10",
      "page_number": 12,
      "outcomes": [
        {{
          "outcome_name": "Total consumption",
          "outcome_category": "Economic",
          "effect_size": 0.23,
          "standard_error": 0.08,
          "p_value": 0.004,
          "ci_lower": 0.07,
          "ci_upper": 0.39,
          "n_observations": 1250,
          "literal_text": "Total consumption | 0.23*** (0.08)",
          "text_position": "Table 10, Row 'Total consumption'"
        }}
      ]
    }}
  ]
}}

EXTRACTION RULES:
- Extract ONLY tables: {tables_str}
- Include all statistical data: effect sizes, SE, p-values, CI, sample sizes
- Mark significance: *** p<0.01, ** p<0.05, * p<0.1
- Papers may be in English or Spanish (Table/Cuadro, Figure/Figura)
- Capture exact text for verification

Return ONLY valid JSON (or {{"results_tables": []}} if target tables not found on these pages):"""
            
            # Build messages with vision content
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
            
            # Add images
            for img in batch_images:
                messages[0]["content"].append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{img['image_data']}"
                    }
                })
            
            try:
                # Call vision API
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.0,
                    max_tokens=16000
                )
                
                content = response.choices[0].message.content
                
                if not content:
                    logger.warning(f"Empty response for batch {batch_idx + 1}")
                    continue
                
                # Parse JSON response
                parsed = None
                if '```json' in content:
                    json_match = re.search(r'```json\s*(\{[\s\S]*?\})\s*```', content, re.DOTALL)
                    if json_match:
                        try:
                            parsed = json.loads(json_match.group(1))
                        except json.JSONDecodeError:
                            pass
                
                if parsed is None:
                    json_match = re.search(r'(\{[\s\S]*\})', content, re.DOTALL)
                    if json_match:
                        try:
                            parsed = json.loads(json_match.group(1))
                        except json.JSONDecodeError:
                            pass
                
                if parsed is None:
                    logger.warning(f"Failed to parse JSON from batch {batch_idx + 1}")
                    logger.warning(f"Raw response (first 500 chars): {content[:500]}")
                    continue
                
                # Extract outcomes and add metadata
                results_tables = parsed.get('results_tables', [])
                
                for table_info in results_tables:
                    table_outcomes = table_info.get('outcomes', [])
                    
                    for outcome in table_outcomes:
                        outcome['_key'] = key
                        outcome['_extraction_method'] = 'pdf_vision'
                        outcome['_table_source'] = 'pdf_image'
                        outcome['_table_number'] = table_info.get('table_number', 'unknown')
                        outcome['_page_number'] = table_info.get('page_number', 'unknown')
                    
                    all_outcomes.extend(table_outcomes)
                    logger.info(f"  Table {table_info.get('table_number')}: {len(table_outcomes)} outcomes")
                
                logger.info(f"Batch {batch_idx + 1}: {len(results_tables)} tables, {sum(len(t.get('outcomes', [])) for t in results_tables)} outcomes")
            
            except Exception as e:
                logger.error(f"Vision API call failed for batch {batch_idx + 1}: {e}")
                continue
        
        logger.info(f"Total outcomes from PDF vision: {len(all_outcomes)}")
        return all_outcomes
    
    def merge_with_tei_results(self, phase3_result: Dict, pdf_result: Dict) -> Dict:
        """
        Merge PDF vision results with TEI extraction results.
        
        Args:
            phase3_result: Results from Phase 3 (TEI)
            pdf_result: Results from Phase 3b (PDF vision)
        
        Returns:
            Combined result dictionary
        """
        logger.info("Merging TEI and PDF vision results")
        
        # Combine outcomes
        all_outcomes = phase3_result.get('outcomes', []) + pdf_result.get('outcomes', [])
        
        # Mark PDF outcomes
        for outcome in pdf_result.get('outcomes', []):
            outcome['_extraction_source'] = 'pdf_vision'
            outcome['_supplemented'] = True
        
        merged = {
            **phase3_result,
            'outcomes': all_outcomes,
            '_supplemented_from_pdf': True,
            '_pdf_tables_extracted': pdf_result.get('missing_tables_requested', []),
            'summary': {
                'tei_tables': phase3_result.get('summary', {}).get('extracted', 0),
                'pdf_tables': pdf_result.get('summary', {}).get('extracted', 0),
                'total_tables': phase3_result.get('summary', {}).get('extracted', 0) + pdf_result.get('summary', {}).get('extracted', 0)
            }
        }
        
        return merged
    
    def save_result(self, result: Dict, output_dir: Path):
        """Save Phase 3b result."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        import json
        key = result['_key']
        output_file = output_dir / f"{key}_phase3b.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Saved Phase 3b result: {output_file}")
