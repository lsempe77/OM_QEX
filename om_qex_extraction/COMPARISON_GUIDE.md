# ✅ Comparison Tool - Testing Guide

## Quick Start: Testing Against Human Ground Truth

### Step 1: Identify Test Papers

The human extraction dataset has **3 studies**:
- Study 121294984 (Burchi 2018 - Malawi TEEP) → Key: **PHRKN65M** ✅ In master file
- Study 121058364 (Maldonado 2019 - Paraguay SOF) → Key: **ABM3E3ZP** ✅ In master file  
- Study 121498842 (Mahecha - Paraguay SOF) → ❌ NOT in master file (excluded from dataset)

**Only 2 papers can be extracted and compared!**

### Step 2: Run Extraction on Test Papers

```powershell
cd om_qex_extraction
python run_extraction.py --keys PHRKN65M ABM3E3ZP
```

Expected output:
```
🎯 SPECIFIC KEYS: Running on 2 papers
✅ Successfully extracted data from ABM3E3ZP.tei.xml
✅ Successfully extracted data from PHRKN65M.tei.xml
Extraction complete: 2/2 successful
```

### Step 3: Run Comparison

```powershell
python compare_extractions.py
```

Expected output:
```
Papers compared: 1-2
Overall agreement: 30-40%
```

**Note**: Study 121411131 (ABM3E3ZP) may not match if human extraction uses different study IDs.

---

## What We Built

A complete **LLM vs Human** extraction comparison system with:

### Features:
- ✅ Automatic matching by study_id
- ✅ Field-by-field agreement calculation
- ✅ Multiple comparison modes:
  - **Numeric**: Tolerance-based (default 1%)
  - **Categorical**: Exact match
  - **Text**: Substring and word overlap
  - **Component**: Yes/No/Not mentioned (handles 0/1 → Yes/No)
- ✅ Detailed reports with disagreement examples
- ✅ JSON metrics output
- ✅ CSV with all comparisons
- ✅ **Fixed**: Handles Python dict strings in graduation_components (uses `ast.literal_eval`)

## 🚀 Usage

### Basic Comparison
```powershell
cd om_qex_extraction
python compare_extractions.py
```

### Custom Paths
```powershell
# Specify custom LLM extraction
python compare_extractions.py --llm path/to/extracted_data.csv

# Specify custom human extraction
python compare_extractions.py --human path/to/human_extraction.csv

# Change numeric tolerance
python compare_extractions.py --tolerance 0.05  # 5% tolerance
```

## 📊 Outputs

After running comparison, you get:

```
outputs/comparison/
├── detailed_comparison.csv      # Row per paper with all field comparisons
├── agreement_metrics.json       # Overall statistics in JSON
└── comparison_report.txt        # Human-readable report
```

### Sample Report

```
LLM vs Human Extraction Comparison Report
===========================================

Total Papers Compared: 2
Overall Agreement Rate: 17.5%

Field-by-Field Agreement:
--------------------------

study_id:
  Agreements: 2/2 (100.0%)

year_of_publication:
  Agreements: 2/2 (100.0%)

author_name:
  Agreements: 0/2 (0.0%)
  Disagreements:
    - Study 121294984: LLM='Palermo et al.' vs Human='Burchi and Strupat'
```

## 📈 Understanding the Results

### Current Test Results (Study 121294984 - Burchi 2018 Malawi TEEP)

**Overall Agreement: 35% (7/20 fields)**

**Perfect matches (7 fields):**
- study_id, year_of_publication, country, year_intervention_started ✅
- consumption_support, skills_training, coaching ✅

**Common Issues Found:**

1. **Multiple outcome rows problem**:
   - Human extraction has **9 different outcome rows** for study 121294984
   - Comparison uses only the **first row** by default
   - This causes mismatches in: sample_size, effect_size, outcome_name
   - Example: LLM extracted "Total consumption" outcome, but human first row has "Amount savings"

2. **Graduation components (3/7 = 43% agreement)**:
   - Human coding: consumption=1, healthcare=0, assets=0, skills=1, savings=0, coaching=1, social=0
   - LLM extraction: consumption=Yes, healthcare=Not mentioned, assets=Yes, skills=Yes, savings=Yes, coaching=Yes, social=Not mentioned
   - **Real disagreements** on assets and savings components require investigation

3. **Format differences**:
   - Author name: "Beierl et al." (LLM) vs "Burchi and Strupat" (Human) - different citation styles
   - Evaluation design: "Cluster-Randomized Controlled Trial" vs "1" (human uses numeric codes)
   - P-value: 0.05 vs "1,369" (comma separator in human data causes parse error)

4. **"Not mentioned" vs "0" interpretation**:
   - LLM: "Not mentioned" = couldn't find evidence in paper
   - Human: "0" = definitively NO (component not present)
   - These **should mismatch** - they have different meanings

### Agreement Metrics by Field Type

**100% agreement fields:**
- study_id, year_of_publication, country, year_intervention_started
- consumption_support, skills_training, coaching

**0% agreement fields needing investigation:**
- author_name (citation format)
- program_name (minor text differences)
- outcome_name, outcome_description (multiple outcomes issue)
- evaluation_design (text vs numeric code)
- sample_size_treatment, sample_size_control (multiple outcomes issue)
- effect_size, p_value (multiple outcomes + parsing)
- healthcare, assets, savings, social_empowerment (component disagreements)

### Why Low Agreement on Some Fields?

1. **Multiple estimates per paper**: Human extraction has multiple rows for same study_id (different outcomes)
   - Each row = different outcome/estimate
   - LLM extracts one "primary" outcome
   - Solution: Need to handle 1:many matching or specify which outcome to extract

2. **Field format differences**: 
   - Evaluation_design: "Cluster-RCT" (LLM) vs "1" (human code)
   - Author name: Full citation vs first author
   - Numeric parsing: Comma separators in human data

3. **Component interpretation differences**:
   - LLM may be more conservative ("Not mentioned" when uncertain)
   - Human coder may infer from context (code as "0" = definitively absent)

### Comparison Modes

**Numeric (with tolerance):**
```python
# Example: sample sizes
LLM: 359
Human: 6
Result: MISMATCH (diff > 1%)
```

**Categorical (exact match):**
```python
# Example: country
LLM: "Haiti"
Human: "Malawi"
Result: MISMATCH
```

**Text (flexible):**
```python
# Checks: exact match → substring → word overlap
LLM: "Randomized Controlled Trial"
Human: "RCT"
Result: MISMATCH (could be improved with normalization)
```

**Component (Yes/No/Not mentioned):**
```python
# Normalized: 1→Yes, 0→No
LLM: "Yes"
Human: "1"  
Result: MATCH (after normalization)
```

## 🔧 How to Use for Validation

### Step 1: Extract with LLM
```powershell
python run_extraction.py --sample 10
```

### Step 2: Run Comparison
```powershell
python compare_extractions.py
```

### Step 3: Review Report
```powershell
notepad outputs\comparison\comparison_report.txt
```

### Step 4: Identify Issues
Look for fields with <70% agreement:
- Check if prompt needs refinement
- Look at disagreement examples
- Adjust extraction rules

### Step 5: Iterate
- Update `prompts/extraction_prompt.txt`
- Re-run extraction on same papers
- Compare again
- Measure improvement

## ⚠️ Current Limitations & Known Issues

### 1. Study ID Matching
- **Issue**: Human extraction has multiple rows per study (different outcomes/estimates)
  - Example: Study 121294984 has **9 outcome rows** in human extraction
- **Impact**: LLM extracts ONE primary outcome, comparison uses only FIRST human row
  - Causes mismatches in: sample_size, effect_size, outcome_name
- **Solution Options**:
  - Match by study_id + outcome_name (requires outcome matching logic)
  - Extract all outcomes from LLM (1:many extraction)
  - Specify which outcome to extract in prompt

### 2. Format Differences
- **Issue**: Human uses codes, LLM uses descriptive text
  - Evaluation design: "1" (human) vs "Cluster-Randomized Controlled Trial" (LLM)
  - Author name: "Burchi and Strupat" vs "Beierl et al." (different citation styles)
- **Impact**: Semantically correct extractions marked as mismatches
- **Solution**: Add normalization layer or code mapping table

### 3. Nested Components (✅ FIXED)
- **Issue**: Graduation components stored as Python dict string in CSV
  - Example: `"{'consumption_support': 'Yes', 'assets': 'Yes'}"`
- **Impact**: Comparison needs to parse dict string
- **Status**: ✅ Fixed with `ast.literal_eval()` fallback after `json.loads()`
- **Code**: `om_qex_extraction/src/comparer.py` lines 337-351

### 4. "Not Mentioned" vs "No" Semantic Difference
- **Issue**: Different meanings between LLM and human
  - LLM "Not mentioned" = no evidence found in text
  - Human "0" = definitively absent (component not present)
- **Impact**: These **should mismatch** - they're semantically different
- **Decision needed**: Should "Not mentioned" map to "No" for comparison purposes?

### 5. Numeric Parsing Errors
- **Issue**: Human data has comma separators in numbers
  - Example: P-value = "1,369" fails to parse as float
- **Impact**: Valid numeric comparisons fail
- **Solution**: Add comma stripping in numeric parsing

## 🎯 Next Steps

### To Improve Agreement:

1. **Fix numeric parsing** (easy win):
   - Strip commas from human numeric fields before comparison
   - Expected improvement: +2-3% overall agreement

2. **Add code mapping** (medium effort):
   - Map evaluation design codes (1,2,3) to text descriptions
   - Map author citation formats
   - Expected improvement: +5-10% overall agreement

3. **Handle multiple outcomes** (major refactor):
   - Extract all outcomes from each paper
   - Match outcomes by name/description
   - Compare matched outcome pairs
   - Expected improvement: +15-25% overall agreement (fixes sample size, effect size, outcome fields)

4. **Investigate component disagreements** (validation):
   - Review papers where LLM says "Yes" but human says "0" (assets, savings)
   - Determine if LLM is over-detecting or human under-detecting
   - Refine component extraction prompts
   - Expected improvement: +5-10% on component fields

### Testing Workflow:



1. **Add Normalization**
   - Map evaluation design codes to names
   - Normalize Yes/No variations
   - Standardize author name formats

2. **Extract Multiple Outcomes**
   - Modify prompt to extract ALL outcomes
   - Create multiple records per paper
   - Match by study_id + outcome_name

3. **Refine Prompts Based on Disagreements**
   - Look at common errors
   - Add examples to prompt
   - Clarify ambiguous instructions

4. **Increase Sample Size**
   - Test on more papers from human extraction set
   - Get statistically significant agreement metrics

## 📊 Expected Agreement Rates

**Target Benchmarks:**

| Field Type | Target | Typical |
|------------|--------|---------|
| IDs, Years | 95%+ | ✅ 100% |
| Bibliographic | 85%+ | ❌ 0-50% |
| Intervention | 80%+ | ❌ 0% |
| Outcomes | 75%+ | ❌ 0% |
| Statistics | 70%+ | ❌ 0-50% |
| Components | 80%+ | ❌ 0% |

**Current status**: Low agreement due to:
- Small sample (only 2 matching papers)
- Multiple estimates issue
- Format normalization needed

## 💡 Pro Tips

1. **Start Small**: Test on 5-10 papers first
2. **Match Carefully**: Ensure LLM and human extracted same papers
3. **Normalize**: Add format conversions before comparing
4. **Iterate**: Use disagreements to improve prompts
5. **Track Progress**: Save comparison reports for each iteration

---

**Status**: ✅ Comparison tool ready
**Next**: Run full extraction, then comprehensive comparison
