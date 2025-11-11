# Data Directory

## 📂 Raw Data (`raw/`)

CSV files containing study metadata:

1. **Master file of included studies (n=114) 11 Nov(data).csv** ✅ **USE THIS**
   - Primary dataset with study metadata
   - 114 total studies (95 with complete metadata, 19 pending)
   - Links to fulltext_metadata.csv via study ID → paper_id
   - Source: EPPI-Reviewer systematic review database
   - Primary dataset: **114 studies** on poverty graduation programs
   - Cleaned version (duplicate Study 121475488 removed from original n=96)
   - All 114 studies have GROBID files ready for extraction
   
2. **fulltext_metadata.csv**
   - Mapping file linking paper IDs to GROBID output Keys
   - Essential for connecting master file IDs to full-text files
   - **How to use:** Look up a paper's ID (starts with 121... or 122...) to find its corresponding Key for GROBID files
   - Contains 673 records (includes papers not in final master file)

## 🔗 How to Find Files

Papers have two identifiers:
- **ID** (e.g., 121058352) - Used in master file and human extraction
- **Key** (e.g., CV27ZK8Q) - Used for GROBID filenames

**To link them:**
1. Find your paper ID in the master file or human extraction
2. Look up that ID in `fulltext_metadata.csv` → get the Key
3. Use the Key to find the GROBID files: `[Key].tei.xml` and `[Key].txt`

**Quick tip:** Use `scripts/map_ids_to_keys.py` to map study IDs to Keys for batch processing.

## 👤 Human Extraction (`human_extraction/`)

Manually extracted data from studies - serves as:
- **Ground truth** for LLM extraction comparison
- **Training data** for prompt engineering
- **Quality benchmark** for automated extraction validation

### Files

**Main extraction form:**
- `8 week SR QEX Pierre SOF and TEEP(Quant Extraction Form).csv` - Quantitative extraction
  - **3 studies** total (121294984, 121058364, 121498842)
  - **2 studies** in master file (121294984, 121058364)
  - Study 121498842 NOT in master (excluded from final dataset)
  - Multiple rows per study (different outcomes/estimates)
  - Study 121294984 has **9 outcome rows**

**Test dataset:**
- `8WR OM SOF - LLM Test(8wr).csv` - LLM test dataset

### Test Papers for Comparison

| Study ID | Key | Author | Year | Program | Country | Rows | In Master |
|----------|-----|--------|------|---------|---------|------|-----------|
| 121294984 | PHRKN65M | Burchi & Strupat | 2018 | Tingathe EEP (TEEP) | Malawi | 9 | ✅ Yes |
| 121058364 | ABM3E3ZP | Maldonado et al. | 2019 | Sembrando Oportunidades (SOF) | Paraguay | ? | ✅ Yes |
| 121498842 | - | Mahecha et al. | - | SOF | Paraguay | ? | ❌ No |

**For testing:**
```powershell
# Extract the 2 papers with GROBID files
python run_extraction.py --keys PHRKN65M ABM3E3ZP

# Compare against human extraction
python compare_extractions.py
```

**Expected:** Only 1-2 papers will match in comparison (study ID matching).

**Original PDFs (for reference):**
  - `121058364.pdf` - Maldonado (2019) - Sembrando Oportunidades (SOF), Paraguay
  - `121294984.pdf` - TEEP program paper
  - `121498842.pdf` - Additional reference paper

**Note:** PDFs use ID naming (121...). To find these same papers in GROBID outputs, use fulltext_metadata.csv to map ID → Key.

## 📄 GROBID Outputs (`grobid_outputs/`)

Full-text extractions from PDFs:

- **`tei/`** - TEI XML format (structured: sections, references, metadata) - **95 files**
- **`text/`** - Plain text format (cleaned full-text) - **95 files**

**Status:** ✅ **100% coverage** - All 95 master file studies have GROBID outputs

**Recent updates:**
- Study 121294984 (Burchi 2018) - Key: PHRKN65M - Added
- Study 121475488 (Gulesci 2020) - Removed as duplicate (shared Key NMQBK8CD with Selim 2020)

Each paper has files named by its Key (e.g., `PHRKN65M.tei.xml` and `PHRKN65M.txt`).
