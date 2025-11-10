# Comparison Analysis: Improved OM vs Human Extraction
## Study: PHRKN65M (121294984)

### Results Summary

**Outcome Count:**
- Human extraction: 9 outcomes from 7 tables
- Original OM (v1): 10 outcomes from 7 tables  
- **Improved OM (v2): 14 outcomes from 10 tables** ✅

### Version Comparison

**Original OM (v1):**
- Tables: 4, 6, 7, 8, 9, 10, 11
- Stopped at Table 11
- Missed Tables 13, 15, 16, 17 (agricultural/consumption outcomes)
- Recall vs human: 3/7 tables = 43%

**Improved OM (v2) - After prompt update:**
- Tables: 5, 6, 7, 9, 10, 12, 13, 15, 17, 18
- Continues through results section
- Found Tables 13, 15, 17 ✅
- Still missing Tables 8, 11, 16
- Recall vs human: 4/7 tables = 57%

### Detailed Table Coverage

**Human extracted from:**
1. Table 6: Amount savings (MWK)
2. Table 8: Number of working hours ❌ Missing in LLM
3. Table 11: Asset wealth index ❌ Missing in LLM  
4. Table 13: Per capita value of harvest (MWK) ✅ Found
5. Table 15: Per capita food consumption (MWK), Diet diversity score ✅ Found (partial - only diet diversity)
6. Table 16: Per capita non-food expenditure (MWK) ❌ Missing in LLM
7. Table 17: Per capita total consumption (MWK), Poverty (yes/no) ✅ Found

**Improved OM extracted from:**
1. Table 5: Financial literacy index ⭐ Extra
2. Table 6: Saving uptake (yes/no), Amount savings (MWK), Loan uptake (yes/no) ✅ Overlap
3. Table 7: Start non-farm business (yes/no) ⭐ Extra
4. Table 9: Per capita number of livestock, Per capita wealth of livestock (MWK) ⭐ Extra
5. Table 10: Per capita number of assets ⭐ Extra
6. Table 12: Per capita quantity of harvest (kg) ⭐ Extra
7. Table 13: Per capita value of harvest (MWK) ✅ Overlap
8. Table 15: Diet diversity score ✅ Overlap (but human also had "Per capita food consumption")
9. Table 17: Per capita total consumption (MWK), Poor household (yes/no) ✅ Overlap
10. Table 18: Drought recovery (yes/no) ⭐ Extra

### Critical Finding: Different Table Selection

**The LLM is not "worse" - it's extracting DIFFERENT outcomes!**

**LLM found 6 additional tables (5, 7, 9, 10, 12, 18) that human didn't extract:**
- Financial literacy (Table 5)
- Non-farm business (Table 7)
- Livestock (Table 9)
- Assets (Table 10)
- Harvest quantity (Table 12)
- Drought recovery (Table 18)

**LLM missed 3 tables (8, 11, 16) that human extracted:**
- Working hours (Table 8)
- Asset wealth index (Table 11)
- Non-food expenditure (Table 16)

**Paper has 22 total results tables** - both human and LLM are selecting subsets!

### Root Cause Analysis

**Why is LLM missing some tables?**

Possible explanations:
1. **Random variation** - LLM focuses on different outcome categories each run
2. **Token limit on output** - May be hitting response length limits
3. **Attention patterns** - Model focuses on certain table types over others
4. **Extraction criteria** - Different interpretation of what constitutes a "result"

The fact that LLM skipped Tables 8, 11, 16 but found 8, 9, 10, 11 in v1 suggests this is NOT strictly sequential - it's selective.

### Impact Assessment

**Coverage:**
- Human: 9 outcomes from 9% of tables (7/22)
- Improved OM: 14 outcomes from 12% of tables (10/22)
- **Improvement: +56% more outcomes**

**Precision**: Need to verify if LLM outcomes are correctly extracted (next step)

**Recall**: 
- Against human selection: 57% (4/7 tables)
- Against full paper: Unknown (would need to extract ALL 22 tables)

### Key Insights

1. **✅ Prompt improvement worked:** v1 → v2 increased outcomes from 10 → 14 (+40%)

2. **✅ Better coverage of later tables:** Now finds Tables 13, 15, 17 (agricultural outcomes)

3. **⚠️ Still incomplete:** Missing 3 human-selected tables (8, 11, 16)

4. **⭐ Discovering new outcomes:** Found 6 tables human didn't extract - potentially valuable

5. **❓ Need precision check:** Are the 14 LLM outcomes correctly extracted?

### Next Steps

1. **✅ COMPLETED:** Improved OM prompt to scan entire results section

2. **IN PROGRESS:** Compare specific outcome names and verify correctness
   - Do Table 6 outcomes match? (savings, loans)
   - Do Table 13/15/17 outcomes match? (harvest, diet, consumption, poverty)

3. **TODO:** Investigate why Tables 8, 11, 16 are skipped
   - Are they smaller tables?
   - Different formatting?
   - Less statistical detail?

4. **TODO:** Test improved prompt on second paper (ABM3E3ZP)

5. **TODO:** Precision analysis - check if extracted values (effect_size, p_value) match human extraction

### Recommendations

**Option 1: Accept current performance**
- 14 outcomes is MORE than human's 9
- Focus on precision (correctness) over recall (completeness)
- Document that different tables may be selected across runs

**Option 2: Further improve coverage**
- Add explicit instruction to extract from EVERY table
- Process paper in chunks if hitting length limits
- Run multiple passes and merge results

**Option 3: Hybrid approach**
- Use LLM for breadth (find all tables)
- Human verification for critical outcomes
- Accept that some variation is expected
