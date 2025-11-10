# Testing & Comparison Workflow

## Quick Reference: Test Papers

### Human Extraction Dataset (3 studies)

| Study ID | Author | Year | Program | Country | Key | Status |
|----------|--------|------|---------|---------|-----|--------|
| 121294984 | Burchi & Strupat | 2018 | TEEP | Malawi | **PHRKN65M** | ✅ In master |
| 121058364 | Maldonado et al. | 2019 | SOF | Paraguay | **ABM3E3ZP** | ✅ In master |
| 121498842 | Mahecha et al. | - | SOF | Paraguay | - | ❌ NOT in master |

**Only 2/3 papers can be tested** (121498842 was excluded from final dataset)

---

## Step-by-Step Testing Guide

### 1️⃣ Run Extraction on Test Papers

```powershell
cd om_qex_extraction
python run_extraction.py --keys PHRKN65M ABM3E3ZP
```

**Expected output:**
```
🎯 SPECIFIC KEYS: Running on 2 papers
Processing ABM3E3ZP.tei.xml...
✅ Successfully extracted data from ABM3E3ZP.tei.xml (X.Xs)
Processing PHRKN65M.tei.xml...
✅ Successfully extracted data from PHRKN65M.tei.xml (X.Xs)

Extraction complete: 2/2 successful
Results saved to: outputs/extractions/extracted_data.csv
```

**What to check:**
- Both papers extracted successfully (2/2)
- Output CSV created with 2 rows
- JSON files created for each paper

---

### 2️⃣ Run Comparison Against Human Ground Truth

```powershell
python compare_extractions.py
```

**Expected output:**
```
================================================================================
LLM vs HUMAN EXTRACTION COMPARISON
================================================================================

Human extraction: 8 week SR QEX Pierre SOF and TEEP(Quant Extraction Form).csv
LLM extraction: ...\outputs\extractions\extracted_data.csv
Output directory: ...\outputs\comparison

Loading data...

Comparing extractions...
No human extraction found for study_id: 121411131  # Expected - ABM3E3ZP may have different ID
Multiple human extractions found for study_id: 121294984, using first  # Expected - 9 outcomes
OK: Compared 1 papers

Calculating agreement metrics...
Saving results...

================================================================================
SUMMARY
================================================================================

Papers compared: 1-2
Overall agreement: 30-40%
```

**What to check:**
- At least 1 paper matched and compared
- Overall agreement ~35% (baseline)
- Output files created in `outputs/comparison/`

---

### 3️⃣ Review Results

#### Check detailed comparison:
```powershell
notepad outputs\comparison\detailed_comparison.csv
```

Look for:
- Which fields matched (True/False in _match columns)
- Mismatch reasons (in _reason columns)
- Actual values from LLM vs Human

#### Check summary report:
```powershell
notepad outputs\comparison\comparison_report.txt
```

Look for:
- Overall agreement rate
- Top/bottom fields by agreement
- Specific disagreement examples
- Recommendations for fields needing work

#### Check metrics JSON:
```powershell
notepad outputs\comparison\agreement_metrics.json
```

Use for:
- Programmatic tracking of agreement over time
- Detailed field-level statistics
- Automation/CI integration

---

## Expected Baseline Results

### Study 121294984 (Burchi 2018 - Malawi TEEP)

**Current agreement: ~35% (7/20 fields)**

#### ✅ Perfect matches (100%):
- study_id
- year_of_publication
- country  
- year_intervention_started
- consumption_support
- skills_training
- coaching

#### ❌ Known mismatches:

**Format differences:**
- author_name: "Beierl et al." vs "Burchi and Strupat"
- program_name: "...Pilot Project (EEP)" vs "...Programme (TEEP)"
- evaluation_design: "Cluster-Randomized Controlled Trial" vs "1"

**Multiple outcomes issue:**
- outcome_name: "Total consumption" vs "Amount savings"
- sample_size_treatment: 256 vs 6
- sample_size_control: 530 vs 24
- effect_size: 21519.0 vs NaN

**Component disagreements (requires investigation):**
- healthcare: "Not mentioned" vs "0" (No)
- assets: "Yes" vs "0" (No) ⚠️ Real disagreement
- savings: "Yes" vs "0" (No) ⚠️ Real disagreement
- social_empowerment: "Not mentioned" vs "0" (No)

**Parsing errors:**
- p_value: 0.05 vs "1,369" (comma separator)

---

## Troubleshooting

### Issue: "No matching papers found"
**Cause**: Study IDs don't match between LLM and human extractions
**Solution**: 
1. Check `extracted_data.csv` study_id column
2. Check human extraction CSV study_id column
3. Verify study IDs are strings, not ints
4. Check for leading/trailing spaces

### Issue: "Found 0 of 2 requested keys"
**Cause**: TEI filename matching fails
**Solution**: ✅ Already fixed in `run_extraction.py` line 52
- Changed from `f.stem` to `f.name.replace('.tei.xml', '')`
- Handles double extension (.tei.xml) correctly

### Issue: "graduation_components showing llm_missing"
**Cause**: Dict string not parsing correctly
**Solution**: ✅ Already fixed in `comparer.py` lines 337-351
- Added `ast.literal_eval()` fallback after `json.loads()`
- Handles both JSON and Python dict strings

### Issue: Low agreement on all fields
**Causes**:
1. Extracting different papers than human set
2. Different outcome rows being compared
3. Field format mismatches

**Solutions**:
1. Verify you're using `--keys PHRKN65M ABM3E3ZP`
2. Check human extraction has those study IDs
3. Review detailed_comparison.csv for patterns

---

## Tracking Improvements

### Baseline (Current)
- **Date**: Nov 10, 2025
- **Papers**: 1 (Study 121294984)
- **Agreement**: 35% (7/20 fields)
- **Perfect fields**: study_id, year, country, intervention_year, consumption_support, skills_training, coaching

### After Each Change

Document improvements:
```markdown
### [Date] - [Change Description]
- **Papers tested**: X
- **Overall agreement**: X%
- **Improvement**: +X%
- **Fixed fields**: [field1, field2, ...]
- **New issues**: [any new problems found]
```

---

## Next Actions After Testing

Based on test results, prioritize:

1. **Quick wins** (do first):
   - [ ] Fix numeric parsing (comma stripping)
   - [ ] Add evaluation design code mapping
   - Expected: +5-7% agreement

2. **Medium effort**:
   - [ ] Normalize author name formats
   - [ ] Add program name fuzzy matching
   - Expected: +3-5% agreement

3. **Major refactor** (later):
   - [ ] Handle multiple outcomes per paper
   - [ ] Match outcomes by description
   - Expected: +15-25% agreement

4. **Validation work**:
   - [ ] Manually review papers with component disagreements
   - [ ] Determine if LLM or human is correct
   - [ ] Refine component extraction prompts
   - Expected: +5-10% on components

---

## Full Extraction Testing

Once test papers look good, run on full dataset:

```powershell
# Extract all 95 papers
python run_extraction.py --all

# Compare (but note: only 2 papers have human ground truth)
python compare_extractions.py
```

**Note**: Agreement metrics will be based on only 2 papers, but you can:
- Manually review a random sample of outputs
- Check for extraction failures
- Validate format consistency
- Look for obvious errors

---

## File Locations

```
om_qex_extraction/
├── run_extraction.py              # Run LLM extraction
├── compare_extractions.py         # Compare LLM vs human
├── outputs/
│   ├── extractions/
│   │   ├── extracted_data.csv    # LLM extraction results
│   │   └── json/                 # Individual JSON files
│   └── comparison/
│       ├── detailed_comparison.csv      # Full comparison data
│       ├── agreement_metrics.json       # Metrics
│       └── comparison_report.txt        # Human-readable report
└── data/
    └── human_extraction/
        └── 8 week SR QEX Pierre SOF and TEEP(Quant Extraction Form).csv
```

---

## Tips

- **Always run comparison after extraction** to catch issues early
- **Save test outputs** before making changes (for before/after comparison)
- **Track agreement metrics** over time in a spreadsheet
- **Review disagreements manually** to understand patterns
- **Test incrementally** - make one change at a time and measure impact
