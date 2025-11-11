# Zotero Sync Scripts Analysis

## Overview
Two scripts for syncing PDFs from Zotero to local filesystem for systematic review processing.

---

## File 1: `step_minus1_zotero_export.js` (Node.js)

### Purpose
**Complete Zotero-to-CSV export pipeline** - Exports entire Zotero collection metadata to CSV and downloads all PDFs in one comprehensive run.

### Key Features

#### 1. **Collection Handling**
- Fetches from specific collection by key or entire library
- **Recursive subcollection support**: `INCLUDE_SUBCOLLECTIONS = true`
- Can traverse entire collection tree automatically

#### 2. **Data Export**
- Exports to CSV with schema:
  - `item_id`, `title`, `authors`, `journal`, `year`, `doi`, `url`, `abstract`
  - `zotero_key`, `has_pdf_in_zotero`, `pdf_downloaded_from_zotero`, `zotero_pdf_filename`
- Proper CSV escaping for commas, quotes, newlines
- JSON summary statistics

#### 3. **PDF Download**
- Downloads ALL PDFs during export
- Naming: `{item_key}_{attachment_title}.pdf`
- Saves to `pdfs/zotero/` directory
- Tracks success/failure per item

#### 4. **Configuration**
```javascript
const ZOTERO_API_KEY = "BsaFwjyC5aKwZV7hyR77nzYV"
const LIBRARY_ID = "6248442"
const LIBRARY_TYPE = "groups"
const COLLECTION_KEY = process.argv[2] || "8BXTNWER"
```

#### 5. **Output Files**
- `screening_results_ZOTERO_{timestamp}.csv` - Main data
- `logs/zotero_export_log_{timestamp}.txt` - Processing log
- `logs/zotero_export_summary_{timestamp}.json` - Statistics
- `pdfs/zotero/` - Downloaded PDFs

#### 6. **Statistics Tracked**
- Total items processed
- Items with/without PDF
- PDFs downloaded vs failed
- Items with/without DOI
- Items with linked (not stored) PDFs

### Usage
```bash
# Export default collection
node step_minus1_zotero_export.js

# Export specific collection
node step_minus1_zotero_export.js COLLECTION_KEY_HERE
```

### Use Case
**Initial setup** - First time exporting an entire Zotero collection for systematic review. Gets everything at once.

---

## File 2: `sync_pdfs_from_zotero.py` (Python)

### Purpose
**Incremental PDF sync** - Checks existing CSV, identifies missing PDFs, and downloads only what's needed.

### Key Features

#### 1. **CSV-Driven**
- Reads existing CSV: `logs/step5_final_with_keys_20251031_174331.csv`
- Only processes records with `zotero_key_existing`
- Updates CSV with new downloads

#### 2. **Smart Filtering**
Only downloads PDFs for records that:
- Have a Zotero key
- Either `pdf_found != 'True'` OR `pdf_filename` is missing

#### 3. **Incremental Approach**
- Checks if file already exists locally before downloading
- Skips already-downloaded PDFs
- Updates CSV after each batch

#### 4. **Configuration**
```python
ZOTERO_API_KEY = "1Ud0XfDxFMjQuykznLvgQjRW"  # Different key!
ZOTERO_GROUP_ID = "6248442"
PDF_DIR = "pdfs"
CSV_FILE = "logs/step5_final_with_keys_20251031_174331.csv"
```

#### 5. **Output**
- Downloads to `pdfs/` directory
- Naming: `{item_id}_{original_filename}.pdf`
- Creates new CSV: `logs/step5_final_synced_{timestamp}.csv`
- Updates `pdf_filename` and `pdf_found` columns

#### 6. **Progress Tracking**
- Logs every 50 items
- Shows: checked, found, downloaded counts
- Rate limiting: 0.2-1 second delays

### Usage
```bash
python sync_pdfs_from_zotero.py
```

### Use Case
**Ongoing maintenance** - After initial export, when you have new items or need to fill gaps. Only downloads what's missing.

---

## Key Differences

| Aspect | step_minus1_zotero_export.js | sync_pdfs_from_zotero.py |
|--------|------------------------------|--------------------------|
| **Language** | Node.js (JavaScript) | Python |
| **Approach** | Full export from scratch | Incremental sync from CSV |
| **Data Source** | Zotero API (fresh fetch) | Existing CSV file |
| **Output** | Creates new CSV + PDFs | Updates existing CSV |
| **PDF Naming** | `{zotero_key}_{title}.pdf` | `{item_id}_{filename}.pdf` |
| **PDF Dir** | `pdfs/zotero/` | `pdfs/` |
| **When to Use** | First time, complete refresh | Fill gaps, maintenance |
| **API Key** | `BsaFwjyC5aKwZV7hyR77nzYV` | `1Ud0XfDxFMjQuykznLvgQjRW` |
| **Collection Support** | Recursive subcollections | N/A (uses CSV) |

---

## Workflow Recommendation

### Initial Setup
1. **Run `step_minus1_zotero_export.js`** to:
   - Export entire collection to CSV
   - Download all available PDFs
   - Get baseline metadata

### Ongoing Use
2. **Run `sync_pdfs_from_zotero.py`** to:
   - Fill in missing PDFs from CSV
   - Update after adding items to Zotero
   - Recover from download failures

---

## Integration with OM_QEX Project

### Current State
Your OM_QEX project uses:
- **Master CSV**: `data/raw/Master file of included studies (n=114) 11 Nov(data).csv`
  - Contains study IDs but NO Zotero keys
  - 114 studies total
  
- **Fulltext Metadata**: `data/raw/fulltext_metadata.csv`
  - Contains `Key` (for filenames) and `paper_id` (study ID)
  - 654 papers total, 97 overlap with Master

### Missing Link
**You need to map Zotero keys to your study IDs!**

### Suggested Workflow

#### Option 1: Export from Zotero with study IDs
1. Ensure your Zotero collection has custom field with study IDs (121058352, etc.)
2. Modify `step_minus1_zotero_export.js` to export this field
3. Run export to get `item_id` → `zotero_key` → `study_id` mapping

#### Option 2: Manual mapping CSV
1. Create mapping file: `zotero_key`, `study_id`, `paper_id`
2. Join with Master file on `study_id` or `paper_id`
3. Use Python script to sync PDFs for your 114 studies

#### Option 3: Add Zotero keys to Master file
1. Export from Zotero using JS script
2. Match on title/author/year
3. Add `zotero_key` column to Master CSV
4. Use Python script for incremental syncs

---

## Recommendations

### For Your Project
1. **Add `zotero_key` column to Master file** - This enables automated PDF sync
2. **Create mapping script** - Match Master studies to Zotero items
3. **Use Python script for maintenance** - After initial mapping, sync missing PDFs

### Script Improvements Needed
1. **Unify PDF naming convention** - Both scripts should use same pattern
2. **Unify PDF directory** - Pick one location (`pdfs/` or `pdfs/zotero/`)
3. **Add study ID support** - Export custom Zotero fields for study IDs
4. **Better error recovery** - Retry logic for failed downloads

### Next Steps
1. Check if your Zotero items have study ID field
2. Export Zotero metadata with study IDs
3. Create mapping between Master CSV and Zotero keys
4. Sync PDFs for the 97 studies you need

---

## API Notes

### Endpoints Used
- **Get collection items**: `GET /groups/{id}/collections/{key}/items`
- **Get subcollections**: `GET /groups/{id}/collections/{key}/collections`
- **Get children**: `GET /groups/{id}/items/{key}/children`
- **Download file**: `GET /groups/{id}/items/{key}/file`

### Rate Limiting
- JS script: 100ms between items
- Python script: 200ms-1s between requests
- Zotero API: 120 requests/minute for authenticated users

### Authentication
Both scripts use different API keys - ensure you have valid keys with read access to group 6248442.
