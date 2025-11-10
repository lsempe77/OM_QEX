# Quick Reference Card

## Test Papers (Human Ground Truth)

```
PHRKN65M - Burchi 2018 - Malawi TEEP    ✅ In master (9 outcome rows)
ABM3E3ZP - Maldonado 2019 - Paraguay SOF ✅ In master
```

## Commands

### Extraction
```powershell
# Test papers
python run_extraction.py --keys PHRKN65M ABM3E3ZP

# Sample
python run_extraction.py --sample 10

# All
python run_extraction.py --all
```

### Comparison
```powershell
# Compare
python compare_extractions.py

# View results
notepad outputs\comparison\comparison_report.txt
notepad outputs\comparison\detailed_comparison.csv
```

## Expected Baseline

- **Papers compared**: 1-2
- **Agreement**: ~35%
- **Perfect fields (7)**: study_id, year, country, intervention_year, consumption_support, skills_training, coaching

## Known Issues

1. **Multiple outcomes** - Human has 9 rows for PHRKN65M, LLM extracts 1 → sample size/effect size mismatch
2. **Components** - Assets & savings disagreement (LLM=Yes, Human=0) → needs investigation
3. **Formats** - Author names, eval codes differ → add normalization
4. **Parsing** - Comma in p-value "1,369" fails → strip commas

## File Locations

```
outputs/
├── extractions/
│   ├── extracted_data.csv       # LLM results
│   └── json/                    # Individual JSONs
└── comparison/
    ├── detailed_comparison.csv  # All comparisons
    ├── agreement_metrics.json   # Stats
    └── comparison_report.txt    # Human-readable
```

## Code Fixes Applied

✅ **run_extraction.py:52** - Fixed .tei.xml extension matching
```python
# OLD: f.stem in args.keys
# NEW: f.name.replace('.tei.xml', '') in args.keys
```

✅ **comparer.py:337-351** - Fixed graduation_components parsing
```python
# Added ast.literal_eval() fallback for Python dict strings
```

## Next Actions

1. [ ] Fix comma parsing in numerics
2. [ ] Add eval design code mapping
3. [ ] Investigate assets/savings disagreements
4. [ ] Handle multiple outcomes (major)

See TESTING_WORKFLOW.md for details.
