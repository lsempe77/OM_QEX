# Data Directory

## 📂 Raw Data (`raw/`)

4 CSV files containing study metadata and literature references:

1. **Master file of included studies (n=95) 10 Nov(data).csv**
   - Primary dataset: 95 studies on poverty graduation programs
   
2. **Master file of included studies (n=95) 10 Nov(data)_with_key.csv**
   - Same as above, with Key column added for linking to GROBID outputs

3. **Grad approaches FTR & grey lit.csv**
   - Extended literature dataset: 1,312 records
   - Contains additional references and grey literature

4. **fulltext_metadata.csv**
   - Mapping file linking paper IDs to GROBID output Keys
   - Essential for connecting master file IDs to full-text files

## 📄 GROBID Outputs (`grobid_outputs/`)

Full-text extractions from 95 PDFs:

- **`tei/`** - TEI XML format (structured: sections, references, metadata)
- **`text/`** - Plain text format (cleaned full-text)

Each paper has two files with matching filenames (Key-based naming).
