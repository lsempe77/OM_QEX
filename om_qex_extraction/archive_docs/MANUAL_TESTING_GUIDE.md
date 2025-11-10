# 🧪 Manual Testing Guide

## What We Created

✅ **Extraction Prompt** (`prompts/extraction_prompt.txt`)
- 15 core fields (simplified from 66)
- Clear JSON schema
- Field definitions and examples
- ~5,500 characters

✅ **Test Prompts Generated** (3 sample papers)
- Ready to copy-paste into ChatGPT/Claude
- Complete prompts = template + paper text
- Located in: `outputs/test_prompts/`

## 📋 The 15 Core Fields

### Bibliographic (3)
1. `study_id` - EPPI ID or identifier
2. `author_name` - Formatted author name
3. `year_of_publication` - 4-digit year

### Intervention (3)
4. `program_name` - Full intervention name
5. `country` - Where it happened
6. `year_intervention_started` - When it started

### Outcome (3)
7. `outcome_name` - Short outcome name
8. `outcome_description` - Full description
9. `evaluation_design` - RCT, quasi-experimental, etc.

### Statistics (2)
10. `sample_size_treatment` - N treatment group
11. `sample_size_control` - N control group
12. `effect_size` - Main effect
13. `p_value` - Statistical significance

### Graduation Components (7 binary fields)
14-20. consumption_support, healthcare, assets, skills_training, savings, coaching, social_empowerment

## 🎯 Manual Testing Instructions

### Step 1: Choose a Test Prompt

Navigate to: `om_qex_extraction/outputs/test_prompts/`

You'll find 3 files:
- `test_prompt_35NWH5BA.tei.txt` - Bangladesh TUPP (5,639 tokens)
- `test_prompt_3AD7ZNC6.tei.txt` - Livestock transfers (5,720 tokens)
- `test_prompt_3J6UUQJ4.tei.txt` - Haiti social protection (9,141 tokens)

**Recommendation**: Start with the shortest one (35NWH5BA)

### Step 2: Open the File

```powershell
notepad "C:\Users\LucasSempe\OneDrive - International Initiative for Impact Evaluation\Desktop\Gen AI tools\8w-sr\OM_QEX\om_qex_extraction\outputs\test_prompts\test_prompt_35NWH5BA.tei.txt"
```

### Step 3: Copy Everything

- Press Ctrl+A to select all
- Press Ctrl+C to copy

### Step 4: Paste into LLM

#### Option A: ChatGPT (Recommended)
1. Go to: https://chat.openai.com/
2. Select GPT-4 or GPT-4 Turbo
3. Paste the prompt
4. Wait for JSON response

#### Option B: Claude
1. Go to: https://claude.ai/
2. Select Claude 3.5 Sonnet
3. Paste the prompt
4. Wait for JSON response

### Step 5: Verify the Output

Check that the response:
- ✅ Is valid JSON (no syntax errors)
- ✅ Contains all 15 fields
- ✅ Uses correct data types (strings, integers, floats, nulls)
- ✅ Graduation components are "Yes", "No", or "Not mentioned"
- ✅ Extracted data matches paper content

### Step 6: Save the Result

Create a file: `outputs/test_prompts/result_35NWH5BA.json`

Paste the LLM's JSON output.

### Step 7: Compare (Optional)

If this paper is in the human extraction set, compare:
- Field-by-field accuracy
- Missing data handling
- Component classification

## 📊 What to Look For

### Good Signs ✅
- All required fields present
- Reasonable values (years in range, sample sizes positive)
- Graduation components logically classified
- Null values for truly missing data

### Red Flags ⚠️
- Missing fields
- Invalid years (e.g., 2030, 1850)
- Negative sample sizes
- "Not mentioned" when components are clearly described
- Effect sizes that don't match the paper

## 🔄 Iteration Process

After testing 2-3 papers:

1. **Document Issues**: Note any extraction errors
2. **Refine Prompt**: Update field definitions if needed
3. **Re-test**: Try the same paper with updated prompt
4. **Compare**: Check if refinements improved accuracy

## 📝 Testing Checklist

```
[ ] Generated test prompts (3 papers)
[ ] Tested prompt #1 in ChatGPT/Claude
[ ] Validated JSON output
[ ] Tested prompt #2
[ ] Validated JSON output
[ ] Tested prompt #3
[ ] Validated JSON output
[ ] Documented any issues
[ ] Refined prompt (if needed)
[ ] Ready to build extraction engine
```

## 🚀 Next Phase

Once manual testing confirms the prompt works well:
1. Build `extraction_engine.py` 
2. Automate the extraction process
3. Run on all 95 papers
4. Compare with human extraction

## 💡 Tips

- **Token limits**: All 3 test papers fit within context limits for GPT-4 and Claude
- **Consistency**: Test the same prompt on all 3 papers before making changes
- **Ground truth**: Paper 35NWH5BA is about Bangladesh TUPP - check if components match known graduation programs
- **Null handling**: LLMs should use `null` for missing numbers, not 0 or empty strings

## 🐛 Common Issues

### JSON Syntax Errors
- Ask LLM to re-format with valid JSON
- Check for trailing commas
- Verify quotation marks

### Hallucinated Data
- Compare specific values against paper text
- Check if sample sizes seem reasonable
- Verify components mentioned in the paper

### Missing Fields
- Ensure prompt template wasn't truncated
- Check if LLM provided partial response
- May need to explicitly request all fields

---

**Status**: ✅ Prompt ready for manual testing
**Next**: Test on 2-3 papers, then build engine
