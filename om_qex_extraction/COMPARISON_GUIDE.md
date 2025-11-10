# ✅ Comparison Tool Complete!

## What We Built

A complete **LLM vs Human** extraction comparison system with:

### Features:
- ✅ Automatic matching by study_id
- ✅ Field-by-field agreement calculation
- ✅ Multiple comparison modes:
  - **Numeric**: Tolerance-based (default 1%)
  - **Categorical**: Exact match
  - **Text**: Substring and word overlap
  - **Component**: Yes/No/Not mentioned
- ✅ Detailed reports with disagreement examples
- ✅ JSON metrics output
- ✅ CSV with all comparisons

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

### Agreement Metrics

**Field Types:**
- **100% agreement**: study_id, year_of_publication
- **Partial agreement**: effect_size (50%)
- **Low agreement**: author_name, program_name (0%)

**Why Low Agreement?**
1. **Multiple estimates per paper**: Human extraction has multiple rows for same study_id (different outcomes)
2. **Different papers matched**: LLM extracted different papers than what's in human set
3. **Field format differences**: Evaluation_design is "RCT" vs "1" in human data

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

## ⚠️ Current Limitations

### 1. Study ID Matching
- **Issue**: Human extraction has multiple rows per study (different outcomes)
- **Impact**: LLM extracts PRIMARY outcome, human might have different one first
- **Solution**: Match by study_id + outcome_name, or extract all outcomes

### 2. Format Differences
- **Issue**: Human uses codes (1/0, evaluation type codes)
- **Impact**: Direct comparison fails even when semantically correct
- **Solution**: Add normalization layer (1→Yes, "RCT"→"Randomized Controlled Trial")

### 3. Nested Components
- **Issue**: Graduation components stored as nested dict in LLM extraction
- **Impact**: Comparison needs special handling
- **Status**: ✅ Fixed with proper dict access

## 🎯 Next Steps

### To Improve Agreement:

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
