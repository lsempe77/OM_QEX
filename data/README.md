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
   - **How to use:** Look up a paper's ID (starts with 121...) to find its corresponding Key for GROBID files

## 🔗 How to Find Files

Papers have two identifiers:
- **ID** (e.g., 121058352) - Used in master file and human extraction
- **Key** (e.g., CV27ZK8Q) - Used for GROBID filenames

**To link them:**
1. Find your paper ID in the master file or human extraction
2. Look up that ID in `fulltext_metadata.csv` → get the Key
3. Use the Key to find the GROBID files: `[Key].tei.xml` and `[Key].txt`

**Quick tip:** `Master file (n=95) 10 Nov(data)_with_key.csv` already has the Key column merged in for convenience.

## 👤 Human Extraction (`human_extraction/`)

Manually extracted data from studies - serves as:
- **Ground truth** for LLM extraction comparison
- **Training data** for prompt engineering
- **Quality benchmark** for automated extraction validation

**Files:**
- **Extraction forms (CSV):**
  - `8 week SR QEX Pierre SOF and TEEP(Quant Extraction Form).csv` - Quantitative extraction
  - `8WR OM SOF - LLM Test(8wr).csv` - LLM test dataset

- **Original PDFs (for reference):**
  - `121058364.pdf` - Maldonado (2019) - Sembrando Oportunidades (SOF), Paraguay
  - `121294984.pdf` - TEEP program paper
  - `121498842.pdf` - Additional reference paper

**Note:** PDFs use ID naming (121...). To find these same papers in GROBID outputs, use fulltext_metadata.csv to map ID → Key.

## �📄 GROBID Outputs (`grobid_outputs/`)

Full-text extractions from 95 PDFs:

- **`tei/`** - TEI XML format (structured: sections, references, metadata)
- **`text/`** - Plain text format (cleaned full-text)

Each paper has two files with matching filenames (Key-based naming).
