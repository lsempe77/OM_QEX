# OM_QEX - Outcome Mapping Quality of Evidence Exchange

A curated dataset of 95 papers on poverty graduation programs with full-text extractions and LLM-based data extraction tools.

**📖 Comprehensive Documentation**: See [`docs/`](docs/) for technical reports and performance analysis

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
├── docs/                     # 📄 Documentation
│   ├── BASELINE_PERFORMANCE_REPORT.md    # Technical performance analysis
│   ├── BASELINE_RESULTS_EMAIL.md         # Stakeholder summary
│   ├── HUMAN_COMPARISON_RESULTS.md       # LLM vs human comparison
│   └── CLEANUP_LOG.md                    # Project organization log
├── scripts/                  # Data processing utilities (2 reusable scripts)
└── archive/                  # Historical files and one-time scripts
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

**Automated outcome extraction from research papers using LLMs with dual-mode operation.**

#### 🆕 Two Extraction Modes

**1. OM (Outcome Mapping)** - Comprehensive outcome identification
- Identifies ALL outcomes with statistical analysis
- Simple categorization (outcome_group, outcome_category, location)
- Output: ~14 outcomes per paper
- Use case: Systematic review mapping, outcome inventory

**2. QEX (Quantitative Extraction)** - Detailed statistical extraction  
- Extracts complete statistical data for outcomes
- Full details (effect_size, p_value, sample_sizes, graduation_components)
- Output: Detailed data for meta-analysis
- Use case: Statistical synthesis, detailed data extraction

**3. Two-Stage Pipeline** - OM guides QEX for maximum coverage
- Stage 1 (OM): Find all outcomes with locations
- Stage 2 (QEX): Extract details using OM hints
- Result: 118% more outcomes than standalone QEX
- 100% OM→QEX conversion rate

#### 🚀 Quick Start
```powershell
cd om_qex_extraction

# Run two-stage extraction (recommended)
python run_twostage_extraction.py --keys PHRKN65M

# Or run modes separately:
python run_extraction.py --mode om --keys PHRKN65M    # Find all outcomes
python run_extraction.py --mode qex --keys PHRKN65M   # Extract details
```

#### 📊 Baseline Performance (Nov 10, 2025)

**Test Paper: PHRKN65M (Burchi & Strupat 2018, Malawi TEEP)**

| Approach | Outcomes Found | Tables Covered | vs Human (9 outcomes) |
|----------|---------------|----------------|----------------------|
| Human extraction | 9 | Tables 6,8,11,13,15,16,17 | Baseline |
| Regular QEX | 6 | Tables 4,6,7,8,9,10,11 | 67% coverage |
| Two-stage (OM→QEX) | 14 | Tables 5,6,7,9,10,12,13,15,17,18 | 156% of human |
| Improved OM (v2) | 14 | 10 tables | **+56% vs human** |

**Key Findings:**
- ✅ Two-stage pipeline: **118% improvement** over regular QEX (6→14 outcomes)
- ✅ 100% OM→QEX conversion rate (all identified outcomes extracted)
- ⚠️ Different table selection than human (57% overlap)
- ⚠️ Paper has 22 results tables - both human and LLM select subsets
- 📈 LLM found 6 additional tables human didn't extract

**Verification fields added:**
- `literal_text`: Exact quote from paper for manual verification
- `text_position`: Precise location (Table X, Row Y, Column Z)

#### 📚 Documentation
- **[HUMAN_COMPARISON_RESULTS.md](HUMAN_COMPARISON_RESULTS.md)** - Detailed comparison analysis ⭐ NEW
- **[TESTING_WORKFLOW.md](om_qex_extraction/TESTING_WORKFLOW.md)** - Complete testing guide
- **[TEST_RESULTS.md](om_qex_extraction/TEST_RESULTS.md)** - Historical baseline results
- **[QUICK_REFERENCE.md](om_qex_extraction/QUICK_REFERENCE.md)** - Commands cheat sheet

#### ✅ System Status (Nov 10, 2025)
- **Architecture**: Dual-mode (OM + QEX) with two-stage pipeline
- **Model**: Claude 3.5 Haiku via OpenRouter API
- **Extraction**: Working end-to-end with network retry logic
- **Test papers**: 2 papers analyzed (PHRKN65M, ABM3E3ZP)
- **Baseline**: 14 outcomes per paper (56% more than human extraction)
- **Coverage**: Finding different tables than human - not necessarily worse
- **Precision**: To be validated (next step)
- **Status**: **Ready for prompt engineering improvements**

#### 🔧 Features
- ✅ Dual-mode extraction: OM (outcome mapping) + QEX (quantitative extraction)
- ✅ Two-stage pipeline: OM guides QEX for 118% better coverage
- ✅ TEI XML parser for GROBID outputs
- ✅ Verification fields (literal_text, text_position) for manual checking
- ✅ Batch processing with robust network retry logic
- ✅ JSON + CSV output formats
- ✅ Handles complex multi-outcome papers (10-20+ outcomes per paper)
- ✅ Comprehensive results scanning (continues through entire paper)

#### 📊 Extracted Fields

**OM (Outcome Mapping) Fields:**
- outcome_group (high-level category: Poverty, Income, Assets, etc.)
- outcome_category (specific outcome name)
- location (page, table, section reference)
- literal_text (exact quote from paper)
- text_position (precise location for verification)

**QEX (Quantitative Extraction) Fields:**
- All OM fields plus:
- outcome_description, evaluation_design, sample_sizes
- effect_size, standard_error, p_value, confidence_interval
- graduation_components (7 components: consumption, healthcare, assets, skills, savings, coaching, social)

See `om_qex_extraction/prompts/` for prompt templates.

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

# Two-stage extraction (recommended - best coverage)
python run_twostage_extraction.py --keys PHRKN65M

# Or run modes separately:
python run_extraction.py --mode om --keys PHRKN65M    # Find all outcomes
python run_extraction.py --mode qex --keys PHRKN65M   # Extract detailed stats

# View results
python -c "import pandas as pd; df = pd.read_csv('outputs/twostage/stage2_qex/extracted_data.csv'); print(df[['outcome_category', 'literal_text', 'text_position']])"
```

**Current baseline**: 14 outcomes per paper, 56% more than human extraction.

See **[HUMAN_COMPARISON_RESULTS.md](HUMAN_COMPARISON_RESULTS.md)** for detailed analysis.

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
- **Extraction modes**: OM (outcome mapping) + QEX (quantitative extraction) + Two-stage pipeline
- **Baseline performance**: 14 outcomes per paper (56% more than human extraction)
- **Coverage**: Different table selection than human (57% overlap, 6 additional tables found)
- **Status**: System working, baseline established, **ready for prompt engineering improvements**
- **Next steps**: Improve table coverage (missing 3/7 human-selected tables), validate precision

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
**Extraction system**: Dual-mode (OM + QEX) with two-stage pipeline established  
**Baseline performance**: 14 outcomes/paper, 118% improvement over standalone QEX  
**Status**: Ready for prompt engineering optimization  
**Repository**: https://github.com/lsempe77/OM_QEX
