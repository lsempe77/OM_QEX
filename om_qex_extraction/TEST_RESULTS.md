# Test Results & Findings - Nov 10, 2025

## Summary

**First test run** of LLM extraction against human ground truth completed successfully.

- **Papers tested**: 2 (PHRKN65M, ABM3E3ZP)
- **Papers compared**: 1 (Study 121294984 - Burchi 2018 Malawi TEEP)
- **Overall agreement**: 35% (7/20 fields)
- **Status**: ✅ System working, baseline established

---

## Test Setup

### Papers Used
1. **PHRKN65M** (Study 121294984) - Burchi & Strupat 2018 - Malawi TEEP
   - ✅ Extracted successfully
   - ✅ Compared with human extraction
   - Human data has **9 outcome rows** for this study

2. **ABM3E3ZP** (Study 121058364?) - Maldonado 2019 - Paraguay SOF
   - ✅ Extracted successfully
   - ❌ No human extraction match found (study ID mismatch)

### Commands Run
```powershell
# Extraction
python run_extraction.py --keys PHRKN65M ABM3E3ZP
# Result: 2/2 successful, ~18 seconds total

# Comparison
python compare_extractions.py
# Result: 1 paper compared, 35% agreement
```

---

## Detailed Results: Study 121294984 (Burchi 2018)

### ✅ Perfect Matches (7 fields - 100% agreement)

| Field | LLM Value | Human Value | Status |
|-------|-----------|-------------|--------|
| study_id | 121294984 | 121294984 | ✅ |
| year_of_publication | 2018 | 2018 | ✅ |
| country | Malawi | Malawi | ✅ |
| year_intervention_started | 2016 | 2016 | ✅ |
| consumption_support | Yes | 1 | ✅ (normalized) |
| skills_training | Yes | 1 | ✅ (normalized) |
| coaching | Yes | 1 | ✅ (normalized) |

### ❌ Mismatches (13 fields)

#### Format Differences (fixable)
| Field | LLM | Human | Issue |
|-------|-----|-------|-------|
| author_name | "Beierl et al." | "Burchi and Strupat" | Different citation style |
| program_name | "...Pilot Project (EEP)" | "...Programme (TEEP)" | Minor text difference |
| evaluation_design | "Cluster-Randomized Controlled Trial" | "1" | Text vs numeric code |

#### Multiple Outcomes Issue (expected)
| Field | LLM | Human | Issue |
|-------|-----|-------|-------|
| outcome_name | "Total consumption" | "Amount savings (MWK)" | Different outcome rows |
| outcome_description | "Sum of food and non-food..." | "Amount savings (MWK)" | Different outcome rows |
| sample_size_treatment | 256 | 6 | Different outcome rows |
| sample_size_control | 530 | 24 | Different outcome rows |
| effect_size | 21519.0 | NaN | Different outcome rows |

#### Parsing Errors (fixable)
| Field | LLM | Human | Issue |
|-------|-----|-------|-------|
| p_value | 0.05 | "1,369" | Comma separator fails numeric parse |

#### Component Disagreements (needs investigation)
| Field | LLM | Human | Agreement |
|-------|-----|-------|-----------|
| consumption_support | Yes | 1 | ✅ Match |
| skills_training | Yes | 1 | ✅ Match |
| coaching | Yes | 1 | ✅ Match |
| healthcare | Not mentioned | 0 | ❌ Different (not mentioned ≠ no) |
| assets | Yes | 0 | ❌ **LLM says yes, human says no** |
| savings | Yes | 0 | ❌ **LLM says yes, human says no** |
| social_empowerment | Not mentioned | 0 | ❌ Different (not mentioned ≠ no) |

**Component agreement: 3/7 (43%)**

---

## Key Findings

### 1. Multiple Outcomes Problem (Critical)

**Issue**: Human extraction has multiple rows per study (different outcomes/estimates), but LLM extracts one primary outcome.

**Impact**: 
- Causes mismatches in: outcome_name, outcome_description, sample_size, effect_size, p_value
- Example: Study 121294984 has **9 different outcomes** in human data
- LLM extracted "Total consumption" but comparison used human's first row "Amount savings"

**Solution needed**: 
- Option A: Extract all outcomes (1:many extraction)
- Option B: Match by outcome_name after extraction
- Option C: Specify which outcome to prioritize in prompt

### 2. Component Extraction Accuracy

**Disagreements found:**
- **Assets**: LLM says "Yes", human coded "0" (No)
- **Savings**: LLM says "Yes", human coded "0" (No)

**Questions:**
1. Is the LLM over-detecting components?
2. Is the human under-coding? (Maybe components mentioned but not emphasized?)
3. What evidence did LLM use to say "Yes"?

**Action needed**: Manually review paper to determine ground truth.

### 3. "Not Mentioned" vs "0" Interpretation

**Current behavior:**
- LLM: "Not mentioned" = couldn't find evidence in text
- Human: "0" = definitively NO (component not present)

**These mismatch by design** - they have different meanings.

**Decision needed**: Should we map "Not mentioned" → "No" for comparison purposes?

### 4. Format/Code Differences (Easy Fixes)

Several mismatches are due to format, not content:
- Author citation styles differ
- Evaluation design: text vs numeric code
- Numeric fields with comma separators

**Estimated improvement**: +5-10% agreement after normalization

---

## Technical Issues Found & Fixed

### ✅ Fixed During Testing

1. **TEI filename matching** (`run_extraction.py:52`)
   - Problem: `Path.stem` on "KEY.tei.xml" returns "KEY.tei" not "KEY"
   - Fix: Changed to `f.name.replace('.tei.xml', '')`

2. **Graduation components parsing** (`comparer.py:337-351`)
   - Problem: CSV contains Python dict string (single quotes), not JSON
   - Fix: Added `ast.literal_eval()` fallback after `json.loads()`
   - Result: Component comparisons now work correctly

### ⚠️ Outstanding Issues

1. **Numeric comma parsing**: "1,369" fails to parse as float
2. **Study ID matching**: ABM3E3ZP didn't match (different ID in human data?)
3. **Evaluation design codes**: Need mapping table (1→RCT, 2→Quasi, etc.)

---

## Improvement Roadmap

### Quick Wins (1-2 hours)

1. **Strip commas from numeric fields** before comparison
   - Estimated improvement: +2% agreement
   - Files to modify: `comparer.py` numeric parsing

2. **Add evaluation design code mapping**
   - Map: 1→"Randomized Controlled Trial", etc.
   - Estimated improvement: +3% agreement
   - Create mapping table in `comparer.py`

3. **Normalize author name formats**
   - Strip "et al.", compare first author only
   - Estimated improvement: +2% agreement

**Total quick wins: ~+7% → 42% agreement**

### Medium Effort (1 day)

4. **Investigate component disagreements**
   - Manually review papers with LLM="Yes", Human="0"
   - Check if LLM prompts need refinement
   - Check if human coding needs updating
   - Estimated improvement: +5% on components

5. **Add program name fuzzy matching**
   - Allow minor text differences (EEP vs TEEP, Pilot vs Programme)
   - Estimated improvement: +2% agreement

**Total after medium: ~+14% → 49% agreement**

### Major Refactor (3-5 days)

6. **Handle multiple outcomes per paper**
   - Modify extraction to return list of outcomes
   - Match outcomes by description similarity
   - Compare matched pairs
   - Estimated improvement: +20-25% agreement (fixes 6 fields)

**Potential final: ~+40% → 75% agreement**

---

## Recommendations

### Before Running Full Dataset

1. ✅ Fix quick wins (commas, codes, normalization)
2. ✅ Investigate component disagreements manually
3. ✅ Test again on same 2 papers to measure improvement
4. ⚠️ Decide on multiple outcomes strategy
5. ⚠️ Run on full dataset only after 50%+ agreement on test papers

### For Next Test Cycle

1. Make quick win fixes
2. Re-run: `python run_extraction.py --keys PHRKN65M ABM3E3ZP`
3. Re-compare: `python compare_extractions.py`
4. Measure improvement
5. Document changes and new agreement %

### Ground Truth Validation

Before finalizing, manually review these papers:
- Study 121294984 (Burchi 2018) - for assets & savings components
- Check if LLM extracted correct outcome or if human first row is arbitrary
- Validate graduation components presence in text

---

## Files Generated

```
outputs/
├── extractions/
│   ├── extracted_data.csv                    # LLM results (2 papers)
│   └── json/
│       ├── ABM3E3ZP.json
│       └── PHRKN65M.json
└── comparison/
    ├── detailed_comparison.csv               # Field-by-field comparison
    ├── agreement_metrics.json                # Statistics
    └── comparison_report.txt                 # Human-readable report
```

All files saved and ready for review.

---

## Conclusion

**System Status**: ✅ Working end-to-end

**Baseline established**: 35% agreement on test paper (7/20 fields)

**Main issues identified**:
1. Multiple outcomes per paper (major impact)
2. Component extraction accuracy (needs validation)
3. Format/code differences (easy to fix)

**Next steps clear**: Quick wins → manual validation → major refactor

**Ready for**: Iterative improvement cycle
