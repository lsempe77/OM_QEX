# PROMPT ENGINEERING PROFESSIONAL ANALYSIS
## Complete Extraction Solution for Table 5 (and Similar Tables)

**Date:** November 12, 2025  
**Issue:** Incomplete extraction of paragraph-embedded tables  
**Specific Case:** Table 5 PHRKN65M - 2/4 outcomes extracted (50%)

---

## EXECUTIVE SUMMARY

As a prompt engineering professional, I've analyzed the extraction failure and identified **3 viable solutions** with increasing levels of explicitness. Solution 1 has been implemented and is ready for testing.

**Current Status:**
- ✅ Table 5 no longer dismissed (was extraction_success=false)
- ⚠️ Only 2/4 treatment arms extracted into JSON
- ✅ LLM correctly identifies 4 rows exist (metadata accurate)
- ❌ LLM fails to convert all 4 rows to JSON outcomes

**Root Cause:** Paragraph-embedded table format causes premature stopping during row-by-row extraction. LLM extracts first 1-2 pattern matches then moves on.

---

## PROPOSED SOLUTIONS (RANKED BY RECOMMENDATION)

### ⭐ SOLUTION 1: Enhanced Row-by-Row Instructions (IMPLEMENTED)

**Status:** ✅ Already applied to `phase3_tei_extraction.txt`

**Key Improvements:**
1. **Systematic parsing steps** for paragraph tables (4-step process)
2. **Enhanced example** showing all 4 rows explicitly with numbered list
3. **Self-verification** with explicit row counting requirement
4. **Error prevention** addressing "don't stop after 1-2 rows"

**Changes Made:**
```
Lines ~103-107: Added CRITICAL parsing steps
Lines ~125-145: Expanded example to show all 4 rows with verification
Lines ~188-193: Added self-check with row counting
```

**Why This Should Work:**
- Addresses the specific failure mode (premature stopping)
- Provides concrete verification checklist
- Builds on existing successful improvements
- Least disruptive to working parts of prompt

**Likelihood of Success:** 70-80%

**Test Command:**
```powershell
cd om_qex_extraction_v2
python run_pipeline_v2.py --keys PHRKN65M --phases 3
```

---

### 🔄 SOLUTION 2: Chain-of-Thought Extraction (ALTERNATIVE)

**Status:** 📄 Documented in `prompts/SOLUTION_2_chain_of_thought.txt`

**Approach:** Force explicit row enumeration before extraction

**Key Mechanism:**
```
STEP 1: IDENTIFY ALL ROWS
"Table 5 has 4 treatment rows:
 1. Project
 2. Lump-sum plus training
 3. Lump-sum only
 4. Training-only"

STEP 2: EXTRACT EACH ROW
[Extract all 4 rows from Step 1 list]

STEP 3: VERIFY COMPLETENESS
"4 rows identified → 4 outcomes extracted ✓"
```

**Why This Works:**
- **Cognitive forcing function** prevents autopilot extraction
- **Explicit commitment** to row count upfront
- **Built-in verification** catches mismatches
- Proven technique for complex reasoning tasks

**When to Use:**
- If Solution 1 achieves 3/4 but not 4/4
- For models that respond well to step-by-step reasoning (o1-preview, Claude)
- When you need maximum reliability

**Likelihood of Success:** 85-95%

**Trade-offs:**
- ✅ More reliable extraction
- ✅ Better debugging (can see Step 1 listing)
- ❌ Slightly longer prompts
- ❌ May increase token usage ~10%

---

### 🔍 SOLUTION 3: Regex Pattern Instruction (LAST RESORT)

**Status:** 📄 Documented in `prompts/SOLUTION_3_regex_pattern.txt`

**Approach:** Provide algorithmic pattern-matching instructions

**Key Mechanism:**
```
Pattern: [Treatment_Name] [Number***/**/*] ([Number])

Algorithm:
1. Read entire paragraph
2. Find ALL occurrences matching pattern
3. Continue until no more matches
4. Each match = one outcome

Example matches:
- "Project 0.581*** (0.135)" ✓
- "Lump-sum only 0.189 (0.159)" ✓
```

**Why This Works:**
- Most explicit and mechanical
- Removes all ambiguity about "what is a row"
- Good for literal-minded models
- Provides concrete search algorithm

**When to Use:**
- If Solutions 1 & 2 both fail
- For models that excel at following algorithms
- When you need absolute explicitness

**Likelihood of Success:** 75-85%

**Trade-offs:**
- ✅ Most explicit guidance
- ✅ Least room for interpretation
- ❌ Most verbose
- ❌ May not generalize to unusual formats
- ❌ Could confuse some models with technical terminology

---

## TESTING PROTOCOL

### Phase 1: Validate Solution 1 (5 minutes)

```powershell
# Run extraction
cd om_qex_extraction_v2
python run_pipeline_v2.py --keys PHRKN65M --phases 3

# Verify Table 5
python -c "import json; data = json.load(open('outputs/phase3/PHRKN65M_phase3.json')); t5 = [o for o in data['outcomes'] if o['table_number']=='5']; print(f'Table 5: {len(t5)}/4 outcomes'); [print(f'  {i+1}. {o[\"treatment_arm\"]}: {o[\"effect_size\"]}') for i, o in enumerate(t5)]"
```

**Expected Output:**
```
Table 5: 4/4 outcomes
  1. Project: 0.581
  2. Lump-sum plus training: 0.799
  3. Lump-sum only: 0.189
  4. Training-only: 0.71
```

**Decision Tree:**
- ✅ **4/4 outcomes** → Success! Test on 5 more papers to validate
- ⚠️ **3/4 outcomes** → Try Solution 2 (Chain-of-Thought)
- ❌ **Still 2/4** → Try Solution 2, then Solution 3 if needed

---

### Phase 2: If Needed, Apply Solution 2 (10 minutes)

1. Open `prompts/SOLUTION_2_chain_of_thought.txt`
2. Copy the "EXTRACTION PROCESS (MANDATORY)" section
3. Insert into `phase3_tei_extraction.txt` before "## OUTPUT SCHEMA" (around line 30)
4. Re-run test commands from Phase 1
5. Compare results

---

### Phase 3: If Needed, Apply Solution 3 (10 minutes)

1. Open `prompts/SOLUTION_3_regex_pattern.txt`
2. Replace the paragraph table section in `phase3_tei_extraction.txt`
3. Re-run test
4. Compare results

---

## DIAGNOSTIC TOOLS

### View Table 5 Raw Content
```powershell
python -c "text = open('data/grobid_outputs/text/PHRKN65M.txt', encoding='utf-8').read(); import re; match = re.search(r'Table 5.*?Observations', text, re.DOTALL); print(match.group(0) if match else 'Not found')"
```

### Check LLM Raw Response
```powershell
cat om_qex_extraction_v2/outputs/phase3/raw_responses/PHRKN65M_batch1_phase3_raw.txt | Select-String -Pattern '"table_number": "5"' -Context 10
```

### Compare Before/After Extraction
```powershell
# Before test
cp outputs/phase3/PHRKN65M_phase3.json outputs/phase3_before.json

# Run test
python run_pipeline_v2.py --keys PHRKN65M --phases 3

# Compare
python -c "import json; b = json.load(open('outputs/phase3_before.json')); a = json.load(open('outputs/phase3/PHRKN65M_phase3.json')); print(f'Before: {len([o for o in b[\"outcomes\"] if o[\"table_number\"]==\"5\"])}'); print(f'After: {len([o for o in a[\"outcomes\"] if o[\"table_number\"]==\"5\"])}'); print(f'Total: Before {len(b[\"outcomes\"])} → After {len(a[\"outcomes\"])}')"
```

---

## SUCCESS CRITERIA

### Minimum Acceptable
- ✅ Table 5: 4/4 outcomes extracted
- ✅ All treatment arm names correct
- ✅ All effect sizes and SEs correct
- ✅ No regression on other tables

### Ideal
- ✅ All paragraph tables: 100% row extraction
- ✅ Total outcome count: 50+ (currently 46)
- ✅ Consistent across multiple papers

---

## CONTINGENCY PLANS

### If All Solutions Fail (2/4 extraction persists)

**Accept Partial Success:**
- 50% extraction is better than 0% (before prompt fix)
- Table is no longer dismissed entirely
- 2/4 rows is progress

**Implement Hybrid Approach:**
1. Use TEI extraction for structured `<figure>` tables (works well)
2. Use Phase 3b PDF vision for paragraph-embedded tables
3. Merge results from both methods

**Document Limitation:**
- Paragraph-embedded format is known limitation
- TEI XML doesn't preserve row structure well for inline tables
- PDF vision may be more reliable for this format

---

## KEY INSIGHTS FOR FUTURE WORK

### What We Learned

1. **LLMs can identify but not extract completely**
   - Metadata shows correct count (4 rows)
   - JSON shows incomplete extraction (2 rows)
   - Suggests execution gap, not comprehension gap

2. **Format matters significantly**
   - Structured `<table>` tags: High success rate
   - Paragraph-embedded: 50% success rate
   - Same content, different XML format, different results

3. **Verification helps but isn't sufficient**
   - Added explicit "count your extractions" reminder
   - LLM still reports 4 in metadata but delivers 2 in JSON
   - Suggests verification happens before final JSON serialization

### Prompt Engineering Principles Applied

✅ **Explicit examples** - Showed all 4 rows enumerated  
✅ **Error prevention** - Listed common mistakes to avoid  
✅ **Self-verification** - Added counting checklist  
✅ **Progressive disclosure** - Start simple, add detail where needed  
🔄 **Chain-of-thought** - Solution 2 implements this  
🔄 **Pattern matching** - Solution 3 implements this  

### Recommendations for Similar Problems

**For incomplete extractions:**
1. Start with explicit examples showing ALL items
2. Add self-verification with counting
3. If fails: Try chain-of-thought approach
4. If fails: Try algorithmic/pattern-based instructions
5. If all fail: Consider format limitations

**For paragraph-embedded data:**
- Consider pre-processing to structured format
- May need different prompt than structured data
- PDF vision fallback is valid strategy
- Test multiple models (some handle text parsing better)

---

## IMMEDIATE ACTION ITEMS

**Priority 1: Test Solution 1** (NEXT 5 MINUTES)
```powershell
cd om_qex_extraction_v2
python run_pipeline_v2.py --keys PHRKN65M --phases 3
```

Check Table 5 outcome count. If 4/4 → Success! If not → proceed to Priority 2.

**Priority 2: Document Results** (AFTER TESTING)
Record in testing log:
- Solution tested
- Outcome count achieved
- Which rows extracted/missing
- Decision on next steps

**Priority 3: If Successful** (AFTER 4/4 ACHIEVED)
1. Test on 5 additional papers
2. Verify no regression on structured tables
3. Document successful approach
4. Proceed to Phases 4-6

**Priority 4: If Unsuccessful** (IF STILL 2/4)
1. Apply Solution 2 (Chain-of-Thought)
2. Re-test
3. If still failing → Solution 3
4. If all fail → Accept hybrid approach (TEI + PDF vision)

---

## FILES CREATED/MODIFIED

### Modified
- ✅ `prompts/phase3_tei_extraction.txt` - Solution 1 implemented
  - Lines ~103-107: Enhanced paragraph table parsing
  - Lines ~125-145: Expanded 4-row example
  - Lines ~188-193: Self-verification with counting

### Created
- ✅ `prompts/SOLUTION_2_chain_of_thought.txt` - Alternative approach
- ✅ `prompts/SOLUTION_3_regex_pattern.txt` - Last resort approach
- ✅ `prompts/TESTING_GUIDE.md` - Comprehensive testing protocol
- ✅ `prompts/PROMPT_ENGINEERING_ANALYSIS.md` - This document

---

## CONCLUSION

As a prompt engineering professional, I've implemented **Solution 1** (enhanced row-by-row instructions) which has the best balance of:
- ✅ Addresses the specific failure mode
- ✅ Conservative change to working prompt
- ✅ Clear verification mechanism
- ✅ 70-80% likelihood of success

**Next Step:** Test Solution 1 now. If it achieves 4/4 extraction, we're done. If not, Solutions 2 and 3 are ready as escalation paths.

The systematic approach ensures we:
1. Try most conservative fix first
2. Have escalation paths ready
3. Can measure improvement objectively
4. Learn from each iteration

**Ready to test?** Run the command and let's see if Solution 1 solves it! 🎯
