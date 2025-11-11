# OM_QEX Data Extraction Application

Automated quantitative data extraction from research papers using LLMs.

## � Documentation Quick Links

- **[TESTING_WORKFLOW.md](TESTING_WORKFLOW.md)** - Complete testing guide with human ground truth
- **[COMPARISON_GUIDE.md](COMPARISON_GUIDE.md)** - Understanding comparison results and metrics
- **[EXTRACTION_READY.md](EXTRACTION_READY.md)** - Full extraction system documentation
- **[MANUAL_TESTING_GUIDE.md](MANUAL_TESTING_GUIDE.md)** - Manual testing procedures

## 🚀 Quick Start for Testing

### Test on Human-Validated Papers

```powershell
# 1. Extract 2 test papers (with human ground truth)
python run_extraction.py --keys PHRKN65M ABM3E3ZP

# 2. Compare against human extraction
python compare_extractions.py

# 3. Review results
notepad outputs\comparison\comparison_report.txt
```

**Expected**: ~35% agreement (baseline) on 1-2 papers

See **[TESTING_WORKFLOW.md](TESTING_WORKFLOW.md)** for detailed instructions.

---

## �📁 Structure

```
om_qex_extraction/
├── config/
│   └── config.yaml          # Configuration (API keys, models, paths)
├── prompts/
│   └── extraction_prompt.txt # LLM prompt template
├── src/
│   ├── __init__.py
│   ├── models.py            # Pydantic data models (66 fields)
│   ├── tei_parser.py        # TEI XML parser for GROBID outputs
│   ├── extraction_engine.py # LLM extraction logic (TODO)
│   └── validator.py         # Data validation (TODO)
├── outputs/
│   └── extractions/         # Extracted data (JSON + CSV)
└── requirements.txt         # Python dependencies
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd om_qex_extraction
pip install -r requirements.txt
```

### 2. Configure API Key

Edit `config/config.yaml` and add your API key:

```yaml
api:
  openrouter:
    api_key: "YOUR_KEY_HERE"  # Get from https://openrouter.ai/keys
```

### 3. Run Extraction (TODO - not yet implemented)

```bash
python -m src.extraction_engine
```

## 📊 Extraction Fields

The system extracts **66 fields** organized into 8 categories:

1. **General Info** (2): Coder, notes
2. **Publication Info** (5): StudyID, author, year, type
3. **Intervention Info** (12): Program details, 7 components
4. **Method Info** (2): Design, method
5. **Outcome Info** (4): Name, description, dataset
6. **Treatment Info** (4): Treatment, comparison, subgroups
7. **Estimate Info** (4): Analysis type, unit, covariates
8. **Estimate Data** (31): Pre/post stats, effect sizes, CIs

## 🎯 Current Status

✅ **Complete & Working**
- [x] Extraction system built and tested
- [x] TEI parser for GROBID outputs
- [x] Pydantic models (15 core fields + 7 graduation components)
- [x] LLM extraction via OpenRouter (Claude 3.5 Haiku)
- [x] Comparison tool for LLM vs Human validation
- [x] Handles Python dict strings in CSV (ast.literal_eval)
- [x] CLI tools: run_extraction.py, compare_extractions.py
- [x] JSON + CSV output formats

📊 **Test Results** (Nov 10, 2025)
- **Papers tested**: 2 (PHRKN65M, ABM3E3ZP)
- **Papers compared**: 1 (Study 121294984 - Burchi 2018)
- **Baseline agreement**: 35% (7/20 fields)
- **Perfect match fields**: study_id, year, country, intervention_year, consumption_support, skills_training, coaching

🔧 **Known Issues**
- Multiple outcomes per paper (human has 9 rows, LLM extracts 1)
- Component disagreements on assets/savings need investigation
- Format differences (author names, evaluation codes)
- Numeric parsing with comma separators

📈 **Next Steps**
1. Fix numeric parsing (comma stripping) - Quick win
2. Add evaluation design code mapping
3. Investigate component disagreements (manual review)
4. Handle multiple outcomes per paper (major refactor)

See **[TESTING_WORKFLOW.md](TESTING_WORKFLOW.md)** for improvement plan.

## 📖 Usage Examples

```python
### Extract Specific Papers

```python
# Extract 2 test papers
python run_extraction.py --keys PHRKN65M ABM3E3ZP

# Extract random sample
python run_extraction.py --sample 10

# Extract all 95 papers
python run_extraction.py --all
```

### Compare with Human Extraction

```python
# Compare using default paths
python compare_extractions.py

# Custom paths
python compare_extractions.py --llm outputs/extractions/extracted_data.csv --human data/human_extraction/custom.csv

# Adjust numeric tolerance
python compare_extractions.py --tolerance 0.05  # 5% tolerance
```

### Programmatic Usage

```python
from src.models import ExtractionRecord
from src.tei_parser import TEIParser
from src.extraction_engine import ExtractionEngine

# Parse paper
parser = TEIParser("data/grobid_outputs/tei/PHRKN65M.tei.xml")
text = parser.get_full_text()

# Extract data
engine = ExtractionEngine(config_path="config/config.yaml")
result = engine.extract(text, study_id="121294984")

# Access fields
print(f"Author: {result.author_name}")
print(f"Year: {result.year_of_publication}")
print(f"Components: {result.graduation_components}")
```

## 🔗 Data Sources

- **Input**: 114 TEI XML files in `../data/grobid_outputs/tei/`
- **Metadata**: `../data/raw/Master file of included studies (n=114) 11 Nov(data).csv`
- **Human Ground Truth**: `../data/human_extraction/8 week SR QEX Pierre SOF and TEEP(Quant Extraction Form).csv` (3 studies, 2 in master)

## � Test Papers

| Study ID | Key | Author | Year | Program | Country | In Human Extraction |
|----------|-----|--------|------|---------|---------|-------------------|
| 121294984 | PHRKN65M | Burchi & Strupat | 2018 | TEEP | Malawi | ✅ Yes (9 outcomes) |
| 121058364 | ABM3E3ZP | Maldonado et al. | 2019 | SOF | Paraguay | ✅ Yes |
| 121498842 | - | Mahecha et al. | - | SOF | Paraguay | ❌ Not in master |

## 🛠️ Improvement Roadmap

See **[TESTING_WORKFLOW.md](TESTING_WORKFLOW.md)** for detailed action items.

**Quick Wins:**
1. Fix numeric comma parsing (+2-3% agreement)
2. Add evaluation design code mapping (+3-5% agreement)

**Medium Effort:**
3. Normalize author name formats (+2-3% agreement)
4. Investigate component disagreements (validation)

**Major Refactor:**
5. Handle multiple outcomes per paper (+15-25% agreement)

4. **Full Extraction**: Process all 95 papers

## 📝 Notes

- **Model Recommendation**: Start with Claude 3.5 Haiku (fast, cheap)
- **Validation**: Compare against 22 human-extracted papers
- **Output**: Both JSON (individual papers) and CSV (consolidated)
