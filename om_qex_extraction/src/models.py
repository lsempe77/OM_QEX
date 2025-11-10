"""
Data models for extraction fields.
Defines the structure of extracted data matching human extraction format.
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


# ============================================================================
# General Info
# ============================================================================

class GeneralInfo(BaseModel):
    """General extraction metadata."""
    coder_name: str = "LLM Extraction"
    notes: Optional[str] = None


# ============================================================================
# Publication Info
# ============================================================================

class PublicationInfo(BaseModel):
    """Publication metadata - mostly from master file."""
    study_id: str = Field(..., description="EPPI-Reviewer ID starting with 121...")
    estimate_id: Optional[str] = Field(None, description="Unique ID for this estimate")
    author_name: str = Field(..., description="Lead author last name")
    year_of_publication: int = Field(..., description="Publication year")
    publication_type: Optional[str] = Field(None, description="Journal article, working paper, etc.")


# ============================================================================
# Intervention Info
# ============================================================================

class InterventionInfo(BaseModel):
    """Graduation program intervention details."""
    intervention_abbreviation: Optional[str] = None
    intervention_name: Optional[str] = None
    intervention_description: Optional[str] = Field(None, description="Brief description of intervention")
    country: str = Field(..., description="Country where intervention took place")
    first_year_of_intervention: Optional[int] = Field(None, description="Year intervention started")
    length_of_follow_up: Optional[str] = Field(None, description="Follow-up period (e.g., '12 months', '3 years')")
    exposure_to_intervention: Optional[str] = Field(None, description="Duration of intervention exposure")
    
    # Graduation program components (binary: Yes/No/Not mentioned)
    consumption_support: Optional[Literal["Yes", "No", "Not mentioned"]] = None
    healthcare: Optional[Literal["Yes", "No", "Not mentioned"]] = None
    assets: Optional[Literal["Yes", "No", "Not mentioned"]] = None
    skills_training: Optional[Literal["Yes", "No", "Not mentioned"]] = None
    savings: Optional[Literal["Yes", "No", "Not mentioned"]] = None
    coaching: Optional[Literal["Yes", "No", "Not mentioned"]] = None
    social_empowerment: Optional[Literal["Yes", "No", "Not mentioned"]] = None


# ============================================================================
# Method Info
# ============================================================================

class MethodInfo(BaseModel):
    """Evaluation methodology."""
    evaluation_design: Optional[str] = Field(None, description="RCT, quasi-experimental, etc.")
    evaluation_method: Optional[str] = Field(None, description="Specific method: DiD, RDD, IV, etc.")


# ============================================================================
# Outcome Info
# ============================================================================

class OutcomeInfo(BaseModel):
    """Outcome variable details."""
    outcome_name: Optional[str] = Field(None, description="Short name of outcome")
    outcome_description: Optional[str] = Field(None, description="Full description of outcome variable")
    reverse_sign: Optional[Literal["Yes", "No"]] = Field(None, description="Whether to reverse sign for interpretation")
    outcome_dataset: Optional[str] = Field(None, description="Dataset source for outcome")


# ============================================================================
# Treatment Variable Info
# ============================================================================

class TreatmentVariableInfo(BaseModel):
    """Treatment and comparison group details."""
    treatment: Optional[str] = Field(None, description="Treatment group description")
    comparison: Optional[str] = Field(None, description="Comparison/control group description")
    subgroup: Optional[str] = Field(None, description="Subgroup analysis identifier")
    subgroup_information: Optional[str] = Field(None, description="Details about subgroup")


# ============================================================================
# Estimate Info
# ============================================================================

class EstimateInfo(BaseModel):
    """Analysis approach details."""
    analysis_type: Optional[str] = Field(None, description="Type of analysis performed")
    unit_of_analysis: Optional[str] = Field(None, description="Individual, household, village, etc.")
    covariate_adjustment: Optional[str] = Field(None, description="Covariates included in model")
    source: Optional[str] = Field(None, description="Table/figure source in paper")


# ============================================================================
# Estimate Data (Statistical Results)
# ============================================================================

class EstimateData(BaseModel):
    """Statistical estimates - the core quantitative data."""
    
    # Pre-intervention data
    mean_pre_t: Optional[float] = Field(None, description="Pre-intervention mean - treatment")
    sd_pre_t: Optional[float] = Field(None, description="Pre-intervention SD - treatment")
    n_pre_t: Optional[int] = Field(None, description="Pre-intervention sample size - treatment")
    mean_pre_c: Optional[float] = Field(None, description="Pre-intervention mean - control")
    sd_pre_c: Optional[float] = Field(None, description="Pre-intervention SD - control")
    n_pre_c: Optional[int] = Field(None, description="Pre-intervention sample size - control")
    
    # Post-intervention data
    mean_post_t: Optional[float] = Field(None, description="Post-intervention mean - treatment")
    sd_post_t: Optional[float] = Field(None, description="Post-intervention SD - treatment")
    n_post_t: Optional[int] = Field(None, description="Post-intervention sample size - treatment")
    mean_post_c: Optional[float] = Field(None, description="Post-intervention mean - control")
    sd_post_c: Optional[float] = Field(None, description="Post-intervention SD - control")
    n_post_c: Optional[int] = Field(None, description="Post-intervention sample size - control")
    
    # Effect sizes and statistics
    effect_size: Optional[float] = Field(None, description="Reported effect size (various metrics)")
    effect_size_type: Optional[str] = Field(None, description="Type: Cohen's d, SMD, etc.")
    regression_coefficient: Optional[float] = Field(None, description="Regression coefficient/beta")
    standard_error: Optional[float] = Field(None, description="Standard error of estimate")
    
    # Confidence intervals
    ci_lower: Optional[float] = Field(None, description="Lower bound of 95% CI")
    ci_upper: Optional[float] = Field(None, description="Upper bound of 95% CI")
    ci_level: Optional[float] = Field(None, description="Confidence level (typically 95)")
    
    # Statistical significance
    p_value: Optional[float] = Field(None, description="P-value")
    t_statistic: Optional[float] = Field(None, description="T-statistic")
    
    # Clustering and design
    number_of_clusters_t: Optional[int] = Field(None, description="Number of clusters - treatment")
    number_of_clusters_c: Optional[int] = Field(None, description="Number of clusters - control")
    
    # Additional estimates
    correlation_pre_post: Optional[float] = Field(None, description="Correlation between pre and post measures")
    icc: Optional[float] = Field(None, description="Intra-class correlation coefficient")
    
    # Notes
    estimate_notes: Optional[str] = Field(None, description="Additional notes about estimation")


# ============================================================================
# Complete Extraction Record
# ============================================================================

class ExtractionRecord(BaseModel):
    """Complete extraction for one estimate from one paper.
    
    Note: One paper may have multiple estimates (different outcomes, subgroups, etc.)
    so we may extract multiple records per paper.
    """
    
    # Metadata
    extraction_timestamp: datetime = Field(default_factory=datetime.now)
    extraction_version: str = "1.0"
    
    # All extraction sections
    general_info: GeneralInfo
    publication_info: PublicationInfo
    intervention_info: InterventionInfo
    method_info: MethodInfo
    outcome_info: OutcomeInfo
    treatment_variable_info: TreatmentVariableInfo
    estimate_info: EstimateInfo
    estimate_data: EstimateData
    
    def to_flat_dict(self) -> dict:
        """Flatten nested structure to single-level dict for CSV export."""
        flat = {}
        
        # Add all fields from nested models
        for section_name in ['general_info', 'publication_info', 'intervention_info', 
                             'method_info', 'outcome_info', 'treatment_variable_info',
                             'estimate_info', 'estimate_data']:
            section = getattr(self, section_name)
            flat.update(section.model_dump())
        
        # Add metadata
        flat['extraction_timestamp'] = self.extraction_timestamp.isoformat()
        flat['extraction_version'] = self.extraction_version
        
        return flat
    
    class Config:
        """Pydantic config."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ============================================================================
# Helper Functions
# ============================================================================

def create_empty_record(study_id: str, author: str, year: int, country: str) -> ExtractionRecord:
    """Create an empty extraction record with minimal required fields."""
    return ExtractionRecord(
        general_info=GeneralInfo(),
        publication_info=PublicationInfo(
            study_id=study_id,
            author_name=author,
            year_of_publication=year
        ),
        intervention_info=InterventionInfo(country=country),
        method_info=MethodInfo(),
        outcome_info=OutcomeInfo(),
        treatment_variable_info=TreatmentVariableInfo(),
        estimate_info=EstimateInfo(),
        estimate_data=EstimateData()
    )


if __name__ == "__main__":
    # Test model creation
    record = create_empty_record(
        study_id="121058364",
        author="Maldonado",
        year=2019,
        country="Colombia"
    )
    
    # Add some data
    record.intervention_info.consumption_support = "Yes"
    record.estimate_data.mean_post_t = 0.45
    record.estimate_data.p_value = 0.023
    
    # Test serialization
    print("JSON output:")
    print(record.model_dump_json(indent=2))
    
    print("\nFlat dict for CSV:")
    import json
    print(json.dumps(record.to_flat_dict(), indent=2))
