"""
Comparison Engine - Compare LLM extractions with human ground truth.
Calculates agreement/disagreement metrics for validation.
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Any
import logging

logger = logging.getLogger(__name__)


class ExtractionComparer:
    """Compare LLM extractions with human extractions."""
    
    def __init__(self, numeric_tolerance: float = 0.01):
        """
        Initialize comparer.
        
        Args:
            numeric_tolerance: Tolerance for numeric comparisons (1% default)
        """
        self.numeric_tolerance = numeric_tolerance
        self.field_mapping = self._create_field_mapping()
    
    def _create_field_mapping(self) -> Dict[str, str]:
        """
        Map LLM field names to human extraction column names.
        
        Returns:
            Dictionary mapping LLM fields -> Human CSV columns (simplified names)
        """
        return {
            # Bibliographic
            'study_id': 'StudyID',
            'author_name': 'Author name',
            'year_of_publication': 'Year of publication',
            
            # Intervention
            'program_name': 'Intervention abbreviation and name',
            'country': 'Country',
            'year_intervention_started': 'First year of intervention',
            
            # Outcome
            'outcome_name': 'Outcome name',
            'outcome_description': 'Outcome description',
            'evaluation_design': 'Evaluation Design',
            
            # Statistics
            'sample_size_treatment': 'N treatment',
            'sample_size_control': 'N control',
            'effect_size': 'Coeff reg',
            'p_value': 'P value exact',
            
            # Graduation components (will use simplified column names)
            'consumption_support': 'consumption_support',
            'healthcare': 'healthcare',
            'assets': 'assets',
            'skills_training': 'skills_training',
            'savings': 'savings',
            'coaching': 'coaching',
            'social_empowerment': 'social_empowerment'
        }
    
    def load_human_extraction(self, human_csv: Path) -> pd.DataFrame:
        """
        Load human extraction data.
        
        Args:
            human_csv: Path to human extraction CSV
        
        Returns:
            DataFrame with human extractions
        """
        # Read with header row 3 (0-indexed = row 2), skipping first 3 rows
        df = pd.read_csv(human_csv, skiprows=3)
        
        # Create simplified column names for easier access
        # Column positions based on the CSV structure
        col_map = {
            2: 'StudyID',  # "This is the study ID..."
            4: 'Author name',  # "Author(s) name..."
            5: 'Year of publication',  # "Year published..."
            7: 'Intervention abbreviation and name',  # "Provide intervention abbreviation..."
            9: 'Country',  # "Country of intervention"
            10: 'First year of intervention',  # "The earliest year..."
            22: 'Outcome name',  # Outcome name column
            23: 'Outcome description',  # Outcome description column
            20: 'Evaluation Design',  # Evaluation Design
            58: 'N treatment',  # Sample size treatment
            59: 'N control',  # Sample size control
            48: 'Coeff reg',  # Regression coefficient (effect size)
            53: 'P value exact',  # P-value
            # Graduation components (based on order)
            13: 'consumption_support',
            14: 'healthcare',
            15: 'assets',
            16: 'skills_training',
            17: 'savings',
            18: 'coaching',
            19: 'social_empowerment'
        }
        
        # Rename columns by position
        new_cols = {}
        for i, col in enumerate(df.columns):
            if i in col_map:
                new_cols[col] = col_map[i]
        
        df = df.rename(columns=new_cols)
        
        logger.info(f"Loaded {len(df)} human extractions")
        return df
    
    def load_llm_extractions(self, llm_csv: Path = None, llm_json_dir: Path = None) -> pd.DataFrame:
        """
        Load LLM extraction data.
        
        Args:
            llm_csv: Path to consolidated LLM extraction CSV
            llm_json_dir: Path to directory with individual JSON files
        
        Returns:
            DataFrame with LLM extractions
        """
        if llm_csv and llm_csv.exists():
            df = pd.read_csv(llm_csv)
        elif llm_json_dir and llm_json_dir.exists():
            # Load from individual JSON files
            records = []
            for json_file in llm_json_dir.glob("*.json"):
                with open(json_file, 'r', encoding='utf-8') as f:
                    records.append(json.load(f))
            df = pd.DataFrame(records)
        else:
            raise ValueError("Must provide either llm_csv or llm_json_dir")
        
        logger.info(f"Loaded {len(df)} LLM extractions")
        return df
    
    def compare_value(self, llm_val: Any, human_val: Any, field_type: str) -> Tuple[bool, str]:
        """
        Compare a single value between LLM and human extraction.
        
        Args:
            llm_val: Value from LLM extraction
            human_val: Value from human extraction
            field_type: Type of field ('numeric', 'categorical', 'text', 'component')
        
        Returns:
            Tuple of (is_match, reason)
        """
        # Handle missing values
        if pd.isna(llm_val) and pd.isna(human_val):
            return True, "both_null"
        if pd.isna(llm_val):
            return False, "llm_missing"
        if pd.isna(human_val):
            return False, "human_missing"
        
        # Numeric comparison
        if field_type == 'numeric':
            try:
                llm_num = float(llm_val)
                human_num = float(human_val)
                
                # Check if within tolerance
                if human_num == 0:
                    match = llm_num == 0
                else:
                    relative_diff = abs(llm_num - human_num) / abs(human_num)
                    match = relative_diff <= self.numeric_tolerance
                
                return match, f"exact_match" if match else f"numeric_diff_{relative_diff:.3f}"
            except (ValueError, TypeError):
                return False, "numeric_parse_error"
        
        # Categorical comparison (exact match)
        elif field_type == 'categorical':
            llm_str = str(llm_val).strip()
            human_str = str(human_val).strip()
            
            # Normalize whitespace and case
            llm_normalized = ' '.join(llm_str.split()).lower()
            human_normalized = ' '.join(human_str.split()).lower()
            
            # Check for "unclear" and similar special codes
            special_codes = ['unclear', 'not reported', 'nr', 'n/a', 'na', '?', 'unknown']
            llm_is_unclear = any(code in llm_normalized for code in special_codes)
            human_is_unclear = any(code in human_normalized for code in special_codes)
            
            # Both unclear = match
            if llm_is_unclear and human_is_unclear:
                return True, "both_unclear"
            
            # Exact match
            if llm_normalized == human_normalized:
                return True, "exact_match"
            
            # Check if one contains the other (e.g., "RCT" in "Randomized Controlled Trial")
            if llm_normalized in human_normalized or human_normalized in llm_normalized:
                return True, "substring_match"
            
            return False, "categorical_mismatch"
        
        # Component comparison (Yes/No/Not mentioned)
        elif field_type == 'component':
            # Normalize component values - CONTENT-BASED
            llm_str = str(llm_val).strip().lower()
            human_str = str(human_val).strip().lower()
            
            # Map human values (might be 0/1 or "unclear") to Yes/No/Unclear
            if human_str in ['1', '1.0', 'yes', 'y', 'true']:
                human_str = 'yes'
            elif human_str in ['0', '0.0', 'no', 'n', 'false']:
                human_str = 'no'
            elif human_str in ['unclear', 'not reported', 'nr', 'n/a', 'na', '?', 'unknown']:
                human_str = 'unclear'
            elif human_str in ['not mentioned', 'not_mentioned', 'nan', 'none', '']:
                human_str = 'not_mentioned'
            
            # Normalize LLM values
            if llm_str in ['yes', 'y', '1', '1.0', 'true']:
                llm_str = 'yes'
            elif llm_str in ['no', 'n', '0', '0.0', 'false']:
                llm_str = 'no'
            elif llm_str in ['unclear', 'not reported', 'nr', 'n/a', 'na', '?', 'unknown']:
                llm_str = 'unclear'
            elif llm_str in ['not mentioned', 'not_mentioned', 'nan', 'none', '']:
                llm_str = 'not_mentioned'
            
            match = llm_str == human_str
            return match, "content_match" if match else f"component_diff_{llm_str}_vs_{human_str}"
        
        # Text comparison (flexible matching)
        elif field_type == 'text':
            llm_str = str(llm_val).strip()
            human_str = str(human_val).strip()
            
            # Normalize whitespace and case for comparison
            llm_normalized = ' '.join(llm_str.split()).lower()
            human_normalized = ' '.join(human_str.split()).lower()
            
            # Check for exact match
            if llm_normalized == human_normalized:
                return True, "exact_match"
            
            # Check for substring match (one contains the other)
            if llm_normalized in human_normalized or human_normalized in llm_normalized:
                return True, "substring_match"
            
            # Check for significant word overlap (content similarity)
            llm_words = set(llm_normalized.split())
            human_words = set(human_normalized.split())
            
            # Remove common stopwords for better content comparison
            stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be'}
            llm_words = llm_words - stopwords
            human_words = human_words - stopwords
            
            if len(llm_words) > 0 and len(human_words) > 0:
                overlap = len(llm_words & human_words) / len(llm_words | human_words)
                if overlap > 0.5:  # >50% word overlap = content match
                    return True, f"word_overlap_{overlap:.2f}"
            
            return False, "text_content_mismatch"
        
        return False, "unknown_type"
    
    def compare_extractions(self, llm_df: pd.DataFrame, human_df: pd.DataFrame) -> pd.DataFrame:
        """
        Compare LLM and human extractions.
        
        Args:
            llm_df: DataFrame with LLM extractions
            human_df: DataFrame with human extractions
        
        Returns:
            DataFrame with comparison results
        """
        results = []
        
        # Match by study_id
        for _, llm_row in llm_df.iterrows():
            llm_study_id = str(llm_row.get('study_id', ''))
            
            # Find matching human extraction
            human_match = human_df[human_df['StudyID'].astype(str) == llm_study_id]
            
            if len(human_match) == 0:
                logger.warning(f"No human extraction found for study_id: {llm_study_id}")
                continue
            
            if len(human_match) > 1:
                logger.warning(f"Multiple human extractions found for study_id: {llm_study_id}, using first")
            
            human_row = human_match.iloc[0]
            
            # Compare each field
            comparison = {
                'study_id': llm_study_id,
                'author': llm_row.get('author_name', ''),
                'year': llm_row.get('year_of_publication', '')
            }
            
            # Define field types
            field_types = {
                'study_id': 'text',
                'author_name': 'text',
                'year_of_publication': 'numeric',
                'program_name': 'text',
                'country': 'categorical',
                'year_intervention_started': 'numeric',
                'outcome_name': 'text',
                'outcome_description': 'text',
                'evaluation_design': 'categorical',
                'sample_size_treatment': 'numeric',
                'sample_size_control': 'numeric',
                'effect_size': 'numeric',
                'p_value': 'numeric',
                'consumption_support': 'component',
                'healthcare': 'component',
                'assets': 'component',
                'skills_training': 'component',
                'savings': 'component',
                'coaching': 'component',
                'social_empowerment': 'component'
            }
            
            # Compare each field
            for llm_field, human_field in self.field_mapping.items():
                llm_val = llm_row.get(llm_field)
                
                # Handle nested graduation_components
                if llm_field in ['consumption_support', 'healthcare', 'assets', 'skills_training', 
                                'savings', 'coaching', 'social_empowerment']:
                    grad_components = llm_row.get('graduation_components', {})
                    if isinstance(grad_components, str):
                        # Parse JSON string if needed
                        try:
                            import json
                            grad_components = json.loads(grad_components)
                        except:
                            grad_components = {}
                    llm_val = grad_components.get(llm_field) if isinstance(grad_components, dict) else None
                
                human_val = human_row.get(human_field)
                
                field_type = field_types.get(llm_field, 'text')
                is_match, reason = self.compare_value(llm_val, human_val, field_type)
                
                comparison[f'{llm_field}_match'] = is_match
                comparison[f'{llm_field}_llm'] = llm_val
                comparison[f'{llm_field}_human'] = human_val
                comparison[f'{llm_field}_reason'] = reason
            
            results.append(comparison)
        
        return pd.DataFrame(results)
    
    def calculate_agreement_metrics(self, comparison_df: pd.DataFrame) -> Dict:
        """
        Calculate overall agreement metrics.
        
        Args:
            comparison_df: DataFrame from compare_extractions()
        
        Returns:
            Dictionary with agreement statistics
        """
        metrics = {
            'total_papers': len(comparison_df),
            'field_agreements': {},
            'overall_agreement': 0.0
        }
        
        # Get all match columns
        match_cols = [col for col in comparison_df.columns if col.endswith('_match')]
        
        total_agreements = 0
        total_comparisons = 0
        
        for col in match_cols:
            field_name = col.replace('_match', '')
            agreements = comparison_df[col].sum()
            total = comparison_df[col].notna().sum()
            
            if total > 0:
                agreement_rate = agreements / total
                metrics['field_agreements'][field_name] = {
                    'agreements': int(agreements),
                    'total': int(total),
                    'rate': float(agreement_rate)
                }
                
                total_agreements += agreements
                total_comparisons += total
        
        if total_comparisons > 0:
            metrics['overall_agreement'] = total_agreements / total_comparisons
        
        return metrics
    
    def generate_report(self, comparison_df: pd.DataFrame, metrics: Dict, output_path: Path):
        """
        Generate comparison report.
        
        Args:
            comparison_df: Comparison results DataFrame
            metrics: Agreement metrics dictionary
            output_path: Path to save report
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("LLM vs Human Extraction Comparison Report\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Total Papers Compared: {metrics['total_papers']}\n")
            f.write(f"Overall Agreement Rate: {metrics['overall_agreement']:.1%}\n\n")
            
            f.write("Field-by-Field Agreement:\n")
            f.write("-" * 80 + "\n")
            
            # Sort by agreement rate
            sorted_fields = sorted(
                metrics['field_agreements'].items(),
                key=lambda x: x[1]['rate'],
                reverse=True
            )
            
            for field, stats in sorted_fields:
                f.write(f"\n{field}:\n")
                f.write(f"  Agreements: {stats['agreements']}/{stats['total']} ({stats['rate']:.1%})\n")
                
                # Show examples of disagreements
                disagreements = comparison_df[comparison_df[f'{field}_match'] == False]
                if len(disagreements) > 0 and len(disagreements) <= 3:
                    f.write(f"  Disagreements:\n")
                    for _, row in disagreements.head(3).iterrows():
                        llm_val = row.get(f'{field}_llm', 'N/A')
                        human_val = row.get(f'{field}_human', 'N/A')
                        reason = row.get(f'{field}_reason', 'N/A')
                        f.write(f"    - Study {row['study_id']}: LLM='{llm_val}' vs Human='{human_val}' ({reason})\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("Recommendations:\n")
            f.write("-" * 80 + "\n")
            
            low_agreement_fields = [
                field for field, stats in metrics['field_agreements'].items()
                if stats['rate'] < 0.7
            ]
            
            if low_agreement_fields:
                f.write(f"\nFields with <70% agreement (may need prompt refinement):\n")
                for field in low_agreement_fields:
                    rate = metrics['field_agreements'][field]['rate']
                    f.write(f"  - {field}: {rate:.1%}\n")
            else:
                f.write("\nAll fields have >70% agreement! ✓\n")
        
        logger.info(f"Report saved to {output_path}")


if __name__ == "__main__":
    # Test the comparer
    logging.basicConfig(level=logging.INFO)
    
    print("Comparison engine ready for testing")
    print("\nTo use:")
    print("1. Run LLM extraction on papers")
    print("2. Run comparison against human extraction")
    print("3. Review agreement metrics and report")
