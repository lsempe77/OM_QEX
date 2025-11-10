# OM_QEX - Outcome Mapping Quality of Evidence Exchange

A curated dataset of 95 papers on poverty graduation programs with full-text extractions and LLM-based data extraction tools.

## 📁 Structure

```
OM_QEX/
├── data/
│   ├── raw/                  # 3 CSV metadata files
│   ├── human_extraction/     # Manual extractions (ground truth)
│   └── grobid_outputs/       # 95 papers × 2 formats (TEI XML + TXT)
├── om_qex_extraction/        # 🆕 LLM-based extraction app
│   ├── src/                  # Extraction engine and parsers
│   ├── prompts/              # LLM extraction prompts
│   ├── config/               # Configuration (API keys)
│   └── outputs/              # Extracted data (JSON + CSV)
├── scripts/                  # Data processing scripts
└── outputs/                  # Analysis results
```

## 📊 Dataset

**95 included studies** on poverty graduation and ultra-poor programs

### Raw Data (`data/raw/`)
- **Master file (n=95)** - Primary dataset with study metadata
- **fulltext_metadata** - Links paper IDs to GROBID outputs

### Human Extraction (`data/human_extraction/`)
- **Manual data extraction** - Ground truth for comparison with LLM extraction
- **Prompt engineering input** - Reference data for developing extraction prompts
- **Quality benchmark** - Validation standard for automated extraction

### Full-Text Outputs (`data/grobid_outputs/`)
- **tei/** - 95 TEI XML files (structured with sections, references, metadata)
- **text/** - 95 plain text files (cleaned full-text extraction)

## 🛠️ Tools & Scripts

### LLM Extraction Application (`om_qex_extraction/`) ⭐

**Automated quantitative data extraction from research papers using LLMs.**

#### 🚀 Quick Start
```powershell
cd om_qex_extraction

# Test on 2 papers with human ground truth
python run_extraction.py --keys PHRKN65M ABM3E3ZP

# Compare with human extraction
python compare_extractions.py

# Review results
notepad outputs\comparison\comparison_report.txt
```

**Expected baseline**: ~35% agreement (7/20 fields) on test papers.

#### 📚 Documentation
- **[TESTING_WORKFLOW.md](om_qex_extraction/TESTING_WORKFLOW.md)** - Complete testing guide (START HERE)
- **[TEST_RESULTS.md](om_qex_extraction/TEST_RESULTS.md)** - Current baseline & findings
- **[QUICK_REFERENCE.md](om_qex_extraction/QUICK_REFERENCE.md)** - Commands cheat sheet
- **[COMPARISON_GUIDE.md](om_qex_extraction/COMPARISON_GUIDE.md)** - Understanding comparison results
- **[EXTRACTION_READY.md](om_qex_extraction/EXTRACTION_READY.md)** - Full system documentation

#### ✅ System Status (Nov 10, 2025)
- **Extraction**: Working end-to-end with OpenRouter (Claude 3.5 Haiku)
- **Comparison**: LLM vs human validation system complete
- **Test papers**: 2 papers with human ground truth (PHRKN65M, ABM3E3ZP)
- **Baseline agreement**: 35% (7/20 fields)
- **Perfect match fields**: study_id, year, country, intervention_year, 3 graduation components
- **Known issues**: Multiple outcomes per paper, component disagreements, format differences
- **Next steps**: Quick wins (+7%), medium effort (+7%), major refactor (+25%) → potential 75% agreement

#### 🔧 Features
- ✅ TEI XML parser for GROBID outputs
- ✅ 15 core extraction fields + 7 graduation components
- ✅ Batch processing with retry logic
- ✅ JSON + CSV output formats
- ✅ LLM vs human comparison tool
- ✅ Content-based field matching (not character-based)
- ✅ Handles 0/1 → Yes/No normalization
- ✅ Multiple comparison modes (numeric, categorical, text, component)

#### 📊 Extracted Fields
- **Bibliographic**: study_id, author_name, year_of_publication
- **Intervention**: program_name, country, year_intervention_started
- **Outcome**: outcome_name, outcome_description, evaluation_design
- **Statistics**: sample_size_treatment, sample_size_control, effect_size, p_value
- **Graduation Components** (7): consumption_support, healthcare, assets, skills_training, savings, coaching, social_empowerment

See `om_qex_extraction/README.md` for full documentation and usage examples.

---

### Data Processing Scripts (`scripts/`)

**Utility scripts for data management and analysis:**
**Utility scripts for data management and analysis:**

- `add_key_column.py` - Links paper IDs to GROBID Keys via fulltext_metadata
- `copy_files_by_key.py` - Extracts GROBID outputs for specific paper Keys
- `analyze_extraction_fields.py` - Analyzes human extraction CSV structure
- `get_human_study_ids.py` - Lists studies in human extraction dataset
- `map_ids_to_keys.py` - Maps study IDs to GROBID Keys for testing

---

### Diagnostic Scripts (`archive/`)

**Historical diagnostic scripts used during data cleaning:**

- `find_duplicate_keys.py` - Found duplicate study (121475488) sharing same Key
- `remove_duplicate.py` - Cleaned master file from 96 → 95 studies
- `test_stem.py` - Diagnosed Path.stem behavior with .tei.xml files
- `check_121498842_human.py` - Verified study 121498842 not in master file
- Other diagnostic tools from data validation phase

These scripts are archived for reference but not needed for normal use.

---

## 🚀 Quick Start

### View the Dataset

### View the Dataset

```bash
# Clone the repository
git clone https://github.com/lsempe77/OM_QEX.git
cd OM_QEX

# View master dataset
# data/raw/Master file of included studies (n=95) 10 Nov(data).csv

# Access full-text files
# data/grobid_outputs/tei/  (95 TEI XML files - structured)
# data/grobid_outputs/text/ (95 TXT files - plain text)
```

### Test LLM Extraction

```powershell
cd om_qex_extraction

# Extract 2 test papers (with human ground truth)
python run_extraction.py --keys PHRKN65M ABM3E3ZP

# Compare against human extraction
python compare_extractions.py

# View results
notepad outputs\comparison\comparison_report.txt
```

See **[TESTING_WORKFLOW.md](om_qex_extraction/TESTING_WORKFLOW.md)** for complete testing guide.

### Run Full Extraction

```powershell
cd om_qex_extraction

# Setup API key (first time only)
cp config/config.yaml.template config/config.yaml
# Edit config.yaml and add your OpenRouter API key

# Install dependencies
pip install -r requirements.txt

# Extract all 95 papers (~10-15 min, ~$0.50-1.00)
python run_extraction.py --all
```

---

---

## 🔗 Linking IDs to Files

Papers have two identifiers:
- **Study ID** (e.g., 121058352) - Used in master file and human extraction
- **Key** (e.g., CV27ZK8Q) - Used for GROBID filenames

**To find GROBID files for a paper:**

1. Look up Study ID in `data/raw/fulltext_metadata.csv`
2. Find corresponding Key in the same row
3. Access files: `data/grobid_outputs/tei/[Key].tei.xml` and `data/grobid_outputs/text/[Key].txt`

**Example:**
```
Study ID: 121058352 (Bandiera 2009)
→ fulltext_metadata.csv: Key = CV27ZK8Q
→ Files: CV27ZK8Q.tei.xml, CV27ZK8Q.txt
```

**Shortcut**: Use `data/raw/Master file (n=95) 10 Nov(data).csv` which already has Key column merged.

---

## 📊 Test Papers (Human Ground Truth)

For LLM validation, 3 studies have manual human extraction:

| Study ID | Key | Author | Year | Program | Country | Status |
|----------|-----|--------|------|---------|---------|--------|
| 121294984 | PHRKN65M | Burchi & Strupat | 2018 | TEEP | Malawi | ✅ In master (9 outcomes) |
| 121058364 | ABM3E3ZP | Maldonado et al. | 2019 | SOF | Paraguay | ✅ In master |
| 121498842 | - | Mahecha et al. | - | SOF | Paraguay | ❌ Not in master |

**Only 2/3 papers can be tested** (121498842 was excluded from final dataset).

See `om_qex_extraction/TESTING_WORKFLOW.md` for testing details.

---

## 📝 Notes

## 📝 Notes

- **Dataset**: 95 poverty graduation program studies (cleaned from 96 - duplicate removed)
- **Full-text processing**: GROBID PDF extraction → TEI XML + plain text
- **ID linking**: All Study IDs mapped to Keys via fulltext_metadata.csv
- **LLM extraction**: Claude 3.5 Haiku via OpenRouter API
- **Human validation**: 2 test papers with ground truth (35% baseline agreement)
- **Status**: System working end-to-end, ready for iterative improvement

## 📂 Repository Contents

```
OM_QEX/
├── README.md                          # This file - project overview
├── DOCUMENTATION_UPDATE.md            # Documentation changelog (Nov 10, 2025)
├── EXTRACTION_PLAN.md                 # Original extraction planning document
├── .gitignore                         # Git ignore rules
│
├── data/                              # Dataset files
│   ├── README.md                      # Data documentation with test papers
│   ├── raw/                           # Metadata CSVs
│   │   ├── Master file (n=95).csv     # Primary dataset ✅
│   │   └── fulltext_metadata.csv      # ID → Key mapping
│   ├── human_extraction/              # Ground truth (3 studies, 2 in master)
│   └── grobid_outputs/                # Full-text extractions (95 × 2)
│       ├── tei/                       # TEI XML (structured)
│       └── text/                      # Plain text
│
├── om_qex_extraction/                 # LLM extraction application ⭐
│   ├── README.md                      # App documentation
│   ├── TESTING_WORKFLOW.md            # Complete testing guide
│   ├── TEST_RESULTS.md                # Current baseline & findings
│   ├── QUICK_REFERENCE.md             # Commands cheat sheet
│   ├── COMPARISON_GUIDE.md            # Understanding results
│   ├── EXTRACTION_READY.md            # System documentation
│   ├── run_extraction.py              # Main extraction CLI
│   ├── compare_extractions.py         # LLM vs human comparison
│   ├── requirements.txt               # Python dependencies
│   ├── src/                           # Source code
│   │   ├── models.py                  # Pydantic data models
│   │   ├── tei_parser.py              # TEI XML parser
│   │   ├── extraction_engine.py       # LLM extraction logic
│   │   └── comparer.py                # Comparison system
│   ├── prompts/                       # LLM prompts
│   ├── config/                        # Configuration files
│   └── outputs/                       # Extraction results (gitignored)
│
├── scripts/                           # Utility scripts
│   ├── add_key_column.py              # ID → Key mapping
│   ├── copy_files_by_key.py           # File extraction
│   ├── get_human_study_ids.py         # List test papers
│   └── map_ids_to_keys.py             # ID → Key lookup
│
└── archive/                           # Diagnostic scripts (historical)
    ├── find_duplicate_keys.py         # Found duplicate study
    ├── remove_duplicate.py            # Cleaned master file
    ├── test_stem.py                   # Path.stem diagnostics
    └── ...                            # Other data cleaning tools
```

## 🔍 Key Files

- **Start here**: `om_qex_extraction/TESTING_WORKFLOW.md`
- **Master dataset**: `data/raw/Master file of included studies (n=95) 10 Nov(data).csv`
- **Test results**: `om_qex_extraction/TEST_RESULTS.md`
- **Run extraction**: `om_qex_extraction/run_extraction.py`
- **Compare results**: `om_qex_extraction/compare_extractions.py`

---

## 🤝 Contributing

This is a research dataset with LLM extraction tools. For questions or improvements:
- Review existing documentation in `om_qex_extraction/`
- Check `TEST_RESULTS.md` for known issues and improvement roadmap
- Follow `TESTING_WORKFLOW.md` for testing changes

## 📄 License

[Add license information]

---

**Last updated**: November 10, 2025  
**Dataset version**: 95 studies (duplicate removed)  
**Extraction system**: Working baseline established (35% agreement)  
**Repository**: https://github.com/lsempe77/OM_QEX
