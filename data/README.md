# Data Directory

## 📂 Raw Data (`raw/`)

3 CSV files containing study metadata:

1. **Master file of included studies (n=95) 10 Nov(data).csv**
   - Primary dataset: 95 studies on poverty graduation programs
   
2. **Master file of included studies (n=95) 10 Nov(data)_with_key.csv**
   - Same as above, with Key column added for linking to GROBID outputs

3. **fulltext_metadata.csv**
   - Mapping file linking paper IDs to GROBID output Keys
   - Essential for connecting master file IDs to full-text files

## � Human Extraction (`human_extraction/`)

Manually extracted data from studies - serves as:
- **Ground truth** for LLM extraction comparison
- **Training data** for prompt engineering
- **Quality benchmark** for automated extraction validation

Files:
- Quantitative extraction forms
- LLM test datasets

## �📄 GROBID Outputs (`grobid_outputs/`)

Full-text extractions from 95 PDFs:

- **`tei/`** - TEI XML format (structured: sections, references, metadata)
- **`text/`** - Plain text format (cleaned full-text)

Each paper has two files with matching filenames (Key-based naming).
