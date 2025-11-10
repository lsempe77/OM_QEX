"""
Extraction Engine - LLM-based data extraction from research papers.
Uses OpenRouter API to extract structured data from TEI XML papers.
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, Optional, List
import yaml
from openai import OpenAI

from .tei_parser import TEIParser
from .models import ExtractionRecord, PublicationInfo, InterventionInfo, GeneralInfo
from .models import MethodInfo, OutcomeInfo, TreatmentVariableInfo, EstimateInfo, EstimateData


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ExtractionEngine:
    """LLM-based extraction engine using OpenRouter."""
    
    def __init__(self, config_path: Path):
        """Initialize the extraction engine with configuration."""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.client = self._initialize_client()
        self.prompt_template = self._load_prompt_template()
        
        logger.info(f"Initialized ExtractionEngine with model: {self.config['model']['name']}")
    
    def _load_config(self) -> Dict:
        """Load configuration from YAML file."""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    
    def _initialize_client(self) -> OpenAI:
        """Initialize OpenAI client for OpenRouter."""
        api_key = self.config['api']['openrouter']['api_key']
        
        # Remove ${} wrapper if present (environment variable format)
        if api_key.startswith("${") and api_key.endswith("}"):
            api_key = api_key[2:-1]
        
        base_url = self.config['api']['openrouter']['base_url']
        
        client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        logger.info(f"OpenRouter client initialized with base URL: {base_url}")
        return client
    
    def _load_prompt_template(self) -> str:
        """Load the extraction prompt template."""
        prompt_path = Path(__file__).parent.parent / "prompts" / "extraction_prompt.txt"
        with open(prompt_path, 'r', encoding='utf-8') as f:
            template = f.read()
        return template
    
    def extract_from_tei(self, tei_file: Path, paper_metadata: Optional[Dict] = None) -> Optional[Dict]:
        """
        Extract data from a TEI XML file.
        
        Args:
            tei_file: Path to TEI XML file
            paper_metadata: Optional metadata from master file (study_id, author, year, country)
        
        Returns:
            Extracted data as dictionary, or None if extraction fails
        """
        logger.info(f"Processing: {tei_file.name}")
        
        # Parse TEI file
        try:
            parser = TEIParser(tei_file)
            paper_text = parser.get_full_text(include_abstract=True)
        except Exception as e:
            logger.error(f"Failed to parse TEI file {tei_file.name}: {e}")
            return None
        
        # Create prompt
        prompt = self.prompt_template.replace("{paper_text}", paper_text)
        
        # Call LLM
        try:
            extraction = self._call_llm(prompt)
            
            # Merge with metadata if provided
            if paper_metadata:
                extraction.update(paper_metadata)
            
            logger.info(f"✅ Successfully extracted data from {tei_file.name}")
            return extraction
            
        except Exception as e:
            logger.error(f"Extraction failed for {tei_file.name}: {e}")
            return None
    
    def _call_llm(self, prompt: str, retry_count: int = 0) -> Dict:
        """
        Call LLM via OpenRouter API.
        
        Args:
            prompt: Complete prompt including template and paper text
            retry_count: Current retry attempt
        
        Returns:
            Extracted data as dictionary
        """
        max_retries = self.config['extraction']['max_retries']
        retry_delay = self.config['extraction']['retry_delay']
        
        try:
            response = self.client.chat.completions.create(
                model=self.config['model']['name'],
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.config['model']['temperature'],
                max_tokens=self.config['model']['max_tokens'],
                top_p=self.config['model']['top_p']
            )
            
            # Extract JSON from response
            response_text = response.choices[0].message.content.strip()
            
            # Handle markdown code blocks
            if response_text.startswith("```json"):
                response_text = response_text[7:]  # Remove ```json
            if response_text.startswith("```"):
                response_text = response_text[3:]  # Remove ```
            if response_text.endswith("```"):
                response_text = response_text[:-3]  # Remove trailing ```
            
            response_text = response_text.strip()
            
            # Parse JSON
            extracted_data = json.loads(response_text)
            
            # Log token usage
            if hasattr(response, 'usage'):
                logger.debug(f"Tokens used: {response.usage.total_tokens}")
            
            return extracted_data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.debug(f"Response text: {response_text[:500]}")
            
            if retry_count < max_retries:
                logger.info(f"Retrying... (attempt {retry_count + 1}/{max_retries})")
                time.sleep(retry_delay)
                return self._call_llm(prompt, retry_count + 1)
            else:
                raise
        
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            
            if retry_count < max_retries:
                logger.info(f"Retrying... (attempt {retry_count + 1}/{max_retries})")
                time.sleep(retry_delay)
                return self._call_llm(prompt, retry_count + 1)
            else:
                raise
    
    def extract_batch(self, tei_files: List[Path], metadata_map: Optional[Dict] = None) -> List[Dict]:
        """
        Extract data from multiple TEI files.
        
        Args:
            tei_files: List of TEI file paths
            metadata_map: Dict mapping Key -> metadata dict
        
        Returns:
            List of extraction results
        """
        results = []
        
        for i, tei_file in enumerate(tei_files, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"Paper {i}/{len(tei_files)}: {tei_file.name}")
            logger.info(f"{'='*60}")
            
            # Get metadata for this paper
            key = tei_file.stem  # Filename without extension
            metadata = metadata_map.get(key) if metadata_map else None
            
            # Extract
            result = self.extract_from_tei(tei_file, metadata)
            
            if result:
                result['_key'] = key  # Add key for tracking
                result['_tei_file'] = str(tei_file)
                results.append(result)
            else:
                logger.warning(f"⚠️  Skipping {tei_file.name} due to extraction failure")
            
            # Small delay to avoid rate limits
            time.sleep(0.5)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Extraction complete: {len(results)}/{len(tei_files)} successful")
        logger.info(f"{'='*60}")
        
        return results
    
    def save_results(self, results: List[Dict], output_dir: Path):
        """
        Save extraction results as JSON and CSV.
        
        Args:
            results: List of extraction dictionaries
            output_dir: Directory to save outputs
        """
        import pandas as pd
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save individual JSON files
        json_dir = output_dir / "json"
        json_dir.mkdir(exist_ok=True)
        
        for result in results:
            key = result.get('_key', 'unknown')
            json_file = json_dir / f"{key}.json"
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Saved {len(results)} JSON files to {json_dir}")
        
        # Save consolidated CSV
        csv_file = output_dir / "extracted_data.csv"
        df = pd.DataFrame(results)
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        logger.info(f"✅ Saved consolidated CSV to {csv_file}")
        
        # Save summary
        summary_file = output_dir / "extraction_summary.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"Extraction Summary\n")
            f.write(f"{'='*60}\n\n")
            f.write(f"Total papers processed: {len(results)}\n")
            f.write(f"Output directory: {output_dir}\n")
            f.write(f"JSON files: {json_dir}\n")
            f.write(f"CSV file: {csv_file}\n\n")
            
            f.write(f"Field Completeness:\n")
            f.write(f"{'-'*60}\n")
            
            # Calculate completeness for each field
            for col in df.columns:
                if col.startswith('_'):
                    continue  # Skip internal fields
                non_null = df[col].notna().sum()
                total = len(df)
                pct = (non_null / total * 100) if total > 0 else 0
                f.write(f"{col}: {non_null}/{total} ({pct:.1f}%)\n")
        
        logger.info(f"✅ Saved summary to {summary_file}")


def load_metadata_from_master(master_file: Path) -> Dict:
    """
    Load metadata from master CSV file.
    
    Returns:
        Dictionary mapping Key -> metadata dict
    """
    import pandas as pd
    
    df = pd.read_csv(master_file)
    
    metadata_map = {}
    
    for _, row in df.iterrows():
        key = row.get('Key')
        if pd.notna(key):
            metadata_map[key] = {
                'study_id': str(row.get('ItemId', '')),
                'author_name': row.get('Short Title', ''),
                'country': row.get('Country', ''),
                'year_of_publication': int(row.get('Year', 0)) if pd.notna(row.get('Year')) else None
            }
    
    return metadata_map


if __name__ == "__main__":
    # Quick test
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    engine = ExtractionEngine(config_path)
    
    # Test on one file
    tei_dir = Path(__file__).parent.parent.parent / "data" / "grobid_outputs" / "tei"
    tei_files = list(tei_dir.glob("*.tei.xml"))[:1]  # Just first file
    
    if tei_files:
        print(f"\n🧪 Testing extraction on: {tei_files[0].name}\n")
        result = engine.extract_from_tei(tei_files[0])
        
        if result:
            print("\n✅ Extraction successful!")
            print(json.dumps(result, indent=2))
        else:
            print("\n❌ Extraction failed")
    else:
        print("No TEI files found for testing")
