# PROMPT ENGINEERING SOLUTIONS - TESTING GUIDE

## Problem Summary

**Current State:**
- Table 5 has 4 treatment arms in paragraph-embedded format
- LLM correctly identifies table exists and reports "4 outcomes" in metadata
- But only extracts 2/4 rows into JSON array
- Missing: "Lump-sum only" (0.189) and "Training-only" (0.710***)

**Root Cause:** 
Paragraph-embedded tables in single-line format cause incomplete row parsing. LLM stops after extracting first 1-2 rows.

---

## Solution 1: Row-by-Row Extraction (ALREADY APPLIED) ✅

**Status:** Implemented in current `phase3_tei_extraction.txt`

**Key Changes Made:**
1. Added systematic parsing steps for paragraph tables (lines ~103-107)
2. Enhanced example to show all 4 rows explicitly with numbered list (lines ~125-145)
3. Added self-check verification with row counting (lines ~188-193)

**What Changed:**
- Explicit 4-step process for paragraph table parsing
- Verification checklist: "count rows → count extracted → must match"
- Emphasized "don't stop after first 1-2 rows"

**Test Now:**
```powershell
cd "c:\Users\LucasSempe\OneDrive - International Initiative for Impact Evaluation\Desktop\Gen AI tools\8w-sr\OM_QEX\om_qex_extraction_v2"
python run_pipeline_v2.py --keys PHRKN65M --phases 3
```

**Verify Results:**
```powershell
python -c "import json; data = json.load(open('outputs/phase3/PHRKN65M_phase3.json')); t5 = [o for o in data['outcomes'] if o['table_number']=='5']; print(f'Table 5 outcomes: {len(t5)}/4'); [print(f'  - {o[\"treatment_arm\"]}: {o[\"effect_size\"]}') for o in t5]"
```

**Expected Output:**
```
Table 5 outcomes: 4/4
  - Project: 0.581
  - Lump-sum plus training: 0.799
  - Lump-sum only: 0.189
  - Training-only: 0.710
```

---

## Solution 2: Chain-of-Thought (ALTERNATIVE)

**Location:** `prompts/SOLUTION_2_chain_of_thought.txt`

**Approach:** Force explicit row enumeration before extraction

**Key Mechanism:**
```
STEP 1: List all rows (e.g., "4 rows: Project, Lump-sum plus training, Lump-sum only, Training-only")
STEP 2: Extract each row from Step 1 list
STEP 3: Verify count matches
```

**To Apply:**
1. Read `SOLUTION_2_chain_of_thought.txt`
2. Add the "EXTRACTION PROCESS (MANDATORY)" section before "## OUTPUT SCHEMA" in `phase3_tei_extraction.txt`
3. Re-run test (same commands as Solution 1)

**When to Use:**
- If Solution 1 still shows incomplete extraction
- For models that respond well to explicit step-by-step reasoning (like o1-preview)

**Pros:**
- Forces cognitive awareness of total row count
- Built-in self-verification
- Prevents "autopilot" extraction that stops early

**Cons:**
- More verbose prompt
- May increase token usage slightly

---

## Solution 3: Regex Pattern Instruction (ALTERNATIVE)

**Location:** `prompts/SOLUTION_3_regex_pattern.txt`

**Approach:** Provide algorithmic pattern-matching instructions

**Key Mechanism:**
```
Pattern: [Treatment_Name] [Number***] ([Number])
Algorithm: Find ALL occurrences of this pattern, don't stop until exhausted
```

**To Apply:**
1. Read `SOLUTION_3_regex_pattern.txt`
2. Replace the "### 1. Finding Tables in TEI XML" section's paragraph table part
3. Re-run test

**When to Use:**
- If Solutions 1 & 2 fail
- For models that excel at following algorithmic instructions
- When you need very explicit, mechanical guidance

**Pros:**
- Most explicit and algorithmic
- Leaves least room for interpretation
- Good for "literal-minded" models

**Cons:**
- Most verbose
- May not generalize to unusual formats
- Could confuse some models with "regex-like" terminology

---

## Testing Protocol

### Quick Test (5 minutes)
```powershell
# Test current Solution 1
cd "c:\Users\LucasSempe\OneDrive - International Initiative for Impact Evaluation\Desktop\Gen AI tools\8w-sr\OM_QEX\om_qex_extraction_v2"
python run_pipeline_v2.py --keys PHRKN65M --phases 3

# Check Table 5
python -c "import json; data = json.load(open('outputs/phase3/PHRKN65M_phase3.json')); t5 = [o for o in data['outcomes'] if o['table_number']=='5']; print(f'{len(t5)}/4 outcomes'); [print(f'{o[\"treatment_arm\"]}') for o in t5]"
```

### Full Validation (15 minutes)
```powershell
# Test on multiple papers with paragraph tables
python run_pipeline_v2.py --keys PHRKN65M,ABM3E3ZP,3NHEK42R --phases 3

# Check all Table 5 extractions
python -c "import json, glob; files = glob.glob('outputs/phase3/*_phase3.json'); [print(f'{f}: {len([o for o in json.load(open(f))[\"outcomes\"] if o[\"table_number\"]==\"5\"])} Table 5 outcomes') for f in files]"
```

### Comparison Test (20 minutes)
Test all 3 solutions:
1. Run with Solution 1 (current) → Save outputs to `outputs/phase3_solution1/`
2. Apply Solution 2 → Run again → Save to `outputs/phase3_solution2/`
3. Apply Solution 3 → Run again → Save to `outputs/phase3_solution3/`
4. Compare extraction counts

---

## Success Criteria

**Minimum Acceptable:**
- Table 5: 4/4 outcomes extracted (100%)
- All outcome names correct
- All effect sizes correct

**Ideal:**
- All paragraph tables: 100% row extraction
- No regression on structured `<figure>` tables
- Total outcome count increases (currently 46, should be 50+)

---

## Diagnostic Commands

### Check what's in Table 5 TEI
```powershell
python -c "text = open('c:/Users/LucasSempe/OneDrive - International Initiative for Impact Evaluation/Desktop/Gen AI tools/8w-sr/OM_QEX/data/grobid_outputs/text/PHRKN65M.txt', encoding='utf-8').read(); import re; match = re.search(r'Table 5.*?Observations', text, re.DOTALL); print(match.group(0) if match else 'Not found')"
```

### Check raw LLM response
```powershell
cat om_qex_extraction_v2/outputs/phase3/raw_responses/PHRKN65M_batch1_phase3_raw.txt | Select-String -Pattern '"table_number": "5"' -Context 15
```

### Compare before/after
```powershell
# Save current results
cp outputs/phase3/PHRKN65M_phase3.json outputs/phase3/PHRKN65M_phase3_before.json

# Run new version
python run_pipeline_v2.py --keys PHRKN65M --phases 3

# Compare
python -c "import json; before = json.load(open('outputs/phase3/PHRKN65M_phase3_before.json')); after = json.load(open('outputs/phase3/PHRKN65M_phase3.json')); print(f'Before: {len([o for o in before[\"outcomes\"] if o[\"table_number\"]==\"5\"])} Table 5 outcomes'); print(f'After: {len([o for o in after[\"outcomes\"] if o[\"table_number\"]==\"5\"])} Table 5 outcomes')"
```

---

## Recommended Testing Order

1. **Test Solution 1 first** (already applied) - 5 min
   - Most conservative, builds on existing improvements
   - If this works → Done!

2. **If Solution 1 fails** (still 2/4 outcomes):
   - Try Solution 2 (Chain-of-Thought) - 10 min
   - Best for models that need explicit reasoning steps

3. **If Solution 2 fails**:
   - Try Solution 3 (Regex Pattern) - 10 min
   - Most explicit, leaves least to interpretation

4. **If all fail**:
   - Document as known limitation
   - Use Phase 3b PDF vision fallback for paragraph tables
   - Focus on improving structured `<figure>` table extraction

---

## Next Steps After Testing

**If successful (4/4 extraction):**
1. Test on 5-10 more papers to verify consistency
2. Document the improvement
3. Proceed to Phases 4-6 implementation
4. Consider: Should all tables use this enhanced approach?

**If partially successful (3/4 extraction):**
1. Investigate which specific row patterns are problematic
2. Consider hybrid approach: TEI for 3 rows + PDF for 1 missing row
3. May need to tune prompt further

**If still failing (2/4 extraction):**
1. Accept 50% improvement as progress (vs 0% before)
2. Implement Phase 3b PDF vision as primary solution for paragraph tables
3. Keep improved prompt for structured tables
4. Document paragraph-embedded format as known TEI limitation

---

## Key Insights for Future Prompt Engineering

**What We Learned:**
1. LLMs can identify/count table rows correctly but fail during JSON conversion
2. Paragraph-embedded formats are harder than structured XML tags
3. Explicit verification steps help but don't guarantee completeness
4. May need different prompts for structured vs paragraph tables

**General Principles:**
- **Counting before extracting** helps (chain-of-thought)
- **Explicit examples** with all rows enumerated help
- **Pattern descriptions** help for algorithmic models
- **Self-verification** catches some but not all errors
- **Format matters**: Structured `<table>` tags > paragraph text

**Future Research:**
- Test if different models (Claude, GPT-4o) handle paragraph tables better
- Consider pre-processing: Convert paragraph tables to pseudo-structured format before LLM
- Explore: Can we use smaller model to identify row boundaries, larger model to extract?
