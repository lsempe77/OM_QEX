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

## 🛠️ Scripts

### Data Processing
- `add_key_column.py` - Matches and adds Key column to master file via EPPI-Reviewer IDs
- `copy_files_by_key.py` - Extracts GROBID outputs for specific paper IDs
- `analyze_extraction_fields.py` - Analyzes human extraction CSV structure

### LLM Extraction App (`om_qex_extraction/`)

**Automated data extraction using LLMs** - Extract structured quantitative data from research papers.

#### Features:
- ✅ TEI XML parser for GROBID outputs
- ✅ 15 core extraction fields (bibliographic, intervention, outcomes, statistics, graduation components)
- ✅ OpenRouter API integration (Claude 3.5 Haiku)
- ✅ Batch processing with retry logic
- ✅ JSON + CSV output with field completeness reports
- ✅ Tested on 5 papers with 100% success rate

#### Quick Start:
```bash
cd om_qex_extraction

# Setup (first time only)
cp config/config.yaml.template config/config.yaml
# Edit config.yaml and add your OpenRouter API key

# Install dependencies
pip install -r requirements.txt

# Test on 1 paper
python run_extraction.py --test

# Run on all 95 papers (~10-15 min, ~$0.50-1.00 cost)
python run_extraction.py --all
```

See `om_qex_extraction/EXTRACTION_READY.md` for full documentation.

#### Extracted Fields:
- **Bibliographic**: study_id, author_name, year_of_publication
- **Intervention**: program_name, country, year_intervention_started
- **Outcome**: outcome_name, outcome_description, evaluation_design
- **Statistics**: sample_size_treatment, sample_size_control, effect_size, p_value
- **Graduation Components**: consumption_support, healthcare, assets, skills_training, savings, coaching, social_empowerment

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/lsempe77/OM_QEX.git
cd OM_QEX

# View master dataset
# data/raw/Master file of included studies (n=95) 10 Nov(data)_with_key.csv

# Access full-text files
# data/grobid_outputs/tei/  (structured XML)
# data/grobid_outputs/text/ (plain text)
```

## � Linking IDs to Files

Papers are identified by **ID** (e.g., 121058352) in the master file and human extraction data, but GROBID files use **Key** (e.g., CV27ZK8Q).

**To find the corresponding GROBID files:**

1. Look up the paper ID in `data/raw/fulltext_metadata.csv`
2. Find the corresponding Key in the same row
3. Use that Key to locate files in `data/grobid_outputs/tei/` and `data/grobid_outputs/text/`

**Example:**
```
ID: 121058352 (Bandiera 2009)
→ fulltext_metadata.csv shows Key: CV27ZK8Q
→ Files: CV27ZK8Q.tei.xml and CV27ZK8Q.txt
```

Alternatively, use `Master file (n=95) 10 Nov(data)_with_key.csv` which already has the Key column merged.

##  Notes

- Full-text processing performed using GROBID
- All IDs cross-referenced via fulltext_metadata.csv
- LLM extraction uses Claude 3.5 Haiku via OpenRouter API
- Human extraction available for 22 papers as ground truth validation
