# OM_QEX Data Extraction Application

Automated quantitative data extraction from research papers using LLMs.

## 📁 Structure

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

✅ **Phase 1 Complete** - Project setup
- [x] Folder structure created
- [x] TEI parser implemented
- [x] Pydantic models defined (66 fields)
- [x] Config template created
- [x] Dependencies listed

🔄 **Phase 2 In Progress** - Prompt engineering
- [ ] Create extraction prompt
- [ ] Add field definitions and examples
- [ ] Test on sample papers

⏳ **Phase 3 Pending** - Engine development
- [ ] Build extraction_engine.py
- [ ] Implement LLM API calls
- [ ] Add validation logic

⏳ **Phase 4 Pending** - Testing
- [ ] Compare with human extraction
- [ ] Calculate accuracy metrics
- [ ] Refine prompts

## 📖 Usage Example

```python
from src.models import create_empty_record
from src.tei_parser import TEIParser

# Parse paper
parser = TEIParser("data/grobid_outputs/tei/CV27ZK8Q.tei.xml")
print(f"Title: {parser.get_title()}")
print(f"Authors: {parser.get_authors()}")

# Create extraction record
record = create_empty_record(
    study_id="121058364",
    author="Maldonado",
    year=2019,
    country="Colombia"
)

# Export
record.model_dump_json(indent=2)  # JSON
record.to_flat_dict()  # Dict for CSV
```

## 🔗 Data Sources

- **Input**: 95 TEI XML files in `../data/grobid_outputs/tei/`
- **Metadata**: `../data/raw/Master file of included studies (n=95) 10 Nov(data)_with_key.csv`
- **Ground Truth**: `../data/human_extraction/` (22 papers)

## 🛠️ Next Steps

1. **Prompt Engineering**: Create extraction prompt with field definitions
2. **Engine Implementation**: Build extraction_engine.py with OpenRouter API
3. **Testing**: Run on sample papers, compare with human extraction
4. **Full Extraction**: Process all 95 papers

## 📝 Notes

- **Model Recommendation**: Start with Claude 3.5 Haiku (fast, cheap)
- **Validation**: Compare against 22 human-extracted papers
- **Output**: Both JSON (individual papers) and CSV (consolidated)
