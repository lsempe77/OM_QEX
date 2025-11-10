# OM_QEX - Outcome Mapping Quality of Evidence Exchange

A curated dataset of 95 papers on poverty graduation programs with full-text extractions.

## 📁 Structure

```
OM_QEX/
├── data/
│   ├── raw/                  # 4 CSV metadata files
│   └── grobid_outputs/       # 95 papers × 2 formats (TEI XML + TXT)
├── scripts/                  # 2 core processing scripts
└── outputs/                  # Analysis results
```

## 📊 Dataset

**95 included studies** on poverty graduation and ultra-poor programs

### Raw Data (`data/raw/`)
- **Master file (n=95)** - Primary dataset with study metadata
- **Grad approaches FTR & grey lit** - Extended literature (1,312 records)
- **fulltext_metadata** - Links paper IDs to GROBID outputs

### Full-Text Outputs (`data/grobid_outputs/`)
- **tei/** - 95 TEI XML files (structured with sections, references, metadata)
- **text/** - 95 plain text files (cleaned full-text extraction)

## 🛠️ Scripts

- `add_key_column.py` - Matches and adds Key column to master file via EPPI-Reviewer IDs
- `copy_files_by_key.py` - Extracts GROBID outputs for specific paper IDs

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

## 📝 Notes

- 81 of 95 studies have matched keys linking to the extended literature
- Full-text processing performed using GROBID
- All IDs cross-referenced via fulltext_metadata.csv
