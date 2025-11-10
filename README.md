# OM_QEX Project

## Project Structure

```
OM_QEX/
├── data/                          # Data files
│   ├── raw/                       # Original CSV files and metadata
│   ├── processed/                 # Processed and cleaned data
│   └── grobid_outputs/           # GROBID processed PDFs
│       ├── tei/                   # TEI XML format
│       └── text/                  # Plain text format
├── scripts/                       # Python scripts
├── docs/                          # Documentation
└── outputs/                       # Analysis results
```

## Data Files

### Raw Data
- `Master file of included studies (n=95) 10 Nov(data).csv` - Original master file (95 studies)
- `Master file of included studies (n=95) 10 Nov(data)_with_key.csv` - Master file with added Key column
- `Grad approaches FTR & grey lit.csv` - Graduate approaches literature (1312 records)
- `fulltext_metadata.csv` - Metadata linking paper IDs to GROBID output keys

### GROBID Outputs
- 95 TEI XML files (structured full text)
- 95 TXT files (plain text extraction)

## Scripts

- `add_key_column.py` - Adds Key column to master file by matching EPPI-Reviewer IDs
- `copy_files_by_key.py` - Copies GROBID outputs based on master file IDs
- Additional utility scripts for data processing

## Getting Started

1. Review the data files in `data/raw/`
2. GROBID outputs are available in `data/grobid_outputs/`
3. Run analysis scripts from the `scripts/` folder
4. Save results to `outputs/`

## Notes

- The Key column links records between the Grad approaches file and GROBID outputs
- Master file IDs are linked to GROBID files via the fulltext_metadata.csv mapping
- 81 out of 95 studies have matched keys from the Grad approaches dataset
