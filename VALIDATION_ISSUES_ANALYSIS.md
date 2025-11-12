# VALIDATION ISSUES SUMMARY & ROOT CAUSES

## Overall Performance
- **47.1% Correct** (8/17 outcomes)
- **47.1% Incorrect** (8/17 outcomes)  
- **5.9% Not Outcome** (1/17 outcomes)

---

## ISSUE CATEGORIES

### 1. **FIELDS NOT EXTRACTED (N/A values)** - 7 outcomes
**Papers affected**: PHRKN65M, 949EZS93, DXHZBI2X, V5P2S7S3

**Problem**: LLM extracted `outcome_category` and `literal_text` but failed to parse them into structured fields (effect_size, standard_error, observations).

**Examples**:
- **PHRKN65M outcome 0**: 
  - Literal: `"Project | 9,079*** (1,864)"`
  - Should extract: effect=9079, SE=1864
  - Got: effect=N/A, SE=N/A ❌

- **V5P2S7S3 outcomes 15-17**:
  - Literal: `"0.0000 (0.0000)"`
  - From TEI fallback (not regular extraction)
  - Got all N/A fields ❌

**Root cause**: 
- Extraction prompt may not have clear instructions to parse numeric fields from `literal_text`
- TEI fallback extraction (`_extraction_method: tei_fallback`) seems to have formatting issues
- 949EZS93 outcome 4 has only text "Total labor hours" with no numbers

---

### 2. **WRONG VALUES EXTRACTED** - 1 outcome
**Paper**: XWDVG8KS outcome 4

**Problem**: SE extracted as 4.9 when validator says it should be 4.96

**Details**:
- Literal text: `"-4.89 (4.90)"`
- Extracted SE: `4.9`
- Expected SE: `4.96`
- Effect: `-4.89` (correct ✓)

**Root cause**: 
- Possible transcription error in the PDF/GROBID parsing?
- Or validator error? (literal shows 4.90, not 4.96)
- **Need clarification**: Does paper actually say 4.90 or 4.96?

---

### 3. **MISSING FIELDS** - 4 outcomes
**Papers**: ABM3E3ZP (1), XWDVG8KS (3)

**Problem A: Missing SE** (XWDVG8KS outcome 7)
- Literal: `"13.93*** (--)"` 
- Extracted SE: `None`
- Validator says SE should be: `0.05`
- **Root cause**: SE was marked as `--` (not reported), but validator found it elsewhere?

**Problem B: Missing N (observations)** (3 outcomes)
- ABM3E3ZP outcome 5: Has effect & SE, missing N
- XWDVG8KS outcomes 0, 2: Have effect & SE, missing N
- **Root cause**: Observation counts may be:
  1. In a different table (sample size table)
  2. In table headers/footers
  3. Mentioned in text only
  4. Not extracting N from literal text properly

---

### 4. **FALSE POSITIVE (Not an Outcome)** - 1 outcome
**Paper**: CG73D75P outcome 0

**Problem**: Extracted as outcome, but validator says it's NOT an outcome

**Details**:
- Outcome category: `"Monthly consumption per capita (pesos) - Group Livelihood vs Control"`
- Literal: `"311** (119) [0.01]"`
- Location: Table 10, Row 'T1: Grp LH / Grp C', Column '(1)'

**Possible reasons**:
1. This is a comparison between treatment groups (not treatment vs control)?
2. This is a summary statistic, not an impact estimate?
3. Validator doesn't consider consumption a relevant outcome?
4. **Need clarification**: Why is this not an outcome?

---

## PRIORITY FIXES

### 🔴 **HIGH PRIORITY**: Fix field parsing (7 outcomes)
**Impact**: 41% of issues (7/17)

**Solutions**:
1. **Improve prompt**: Add explicit instruction to parse `literal_text` into numeric fields
2. **Add post-processing**: Extract numbers from literal_text if fields are N/A
3. **Fix TEI fallback**: V5P2S7S3 outcomes all have `0.0000 (0.0000)` - clearly wrong parsing
4. **Add validation**: Reject outcomes where literal_text has numbers but fields are N/A

**Example fix for PHRKN65M**:
```python
# If literal_text = "9,079*** (1,864)" and effect_size is None:
import re
match = re.search(r'([\d,.-]+)\s*\*+\s*\(([\d,.-]+)\)', literal_text)
if match:
    effect_size = float(match.group(1).replace(',', ''))
    standard_error = float(match.group(2).replace(',', ''))
```

---

### 🟡 **MEDIUM PRIORITY**: Extract observation counts (3-4 outcomes)
**Impact**: 18-24% of issues

**Solutions**:
1. **Look in table headers**: Many tables have N in column headers like "(N=500)"
2. **Check footnotes**: Sample sizes often in table notes
3. **Cross-reference**: Look for sample size tables in the paper
4. **Prompt improvement**: Explicitly ask for N from multiple locations

---

### 🟢 **LOW PRIORITY**: Investigate edge cases
1. **XWDVG8KS SE 4.9 vs 4.96**: Verify which is correct
2. **XWDVG8KS outcome 7 missing SE**: Check if 0.05 is in text/footnotes
3. **CG73D75P false positive**: Clarify outcome definition criteria

---

## IMMEDIATE ACTIONS

1. **Check V5P2S7S3 TEI extraction**: All values are `0.0000` - clearly wrong
2. **Add post-processing regex** to parse literal_text when fields are N/A
3. **Review extraction prompt** for numeric field extraction instructions
4. **Test fixes on validation set** before full re-extraction

---

## QUESTIONS FOR VALIDATOR

1. **XWDVG8KS outcome 4**: Paper shows SE as 4.90 in literal text - is 4.96 correct or typo?
2. **XWDVG8KS outcome 7**: SE marked as `--` in results table - where is 0.05 mentioned?
3. **CG73D75P outcome 0**: Why is "Monthly consumption per capita" not an outcome?
4. **Missing N**: Should we expect N for every outcome, or only when available in results table?
