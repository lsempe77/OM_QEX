# Zotero Sync Scripts - November 11, 2025

## Summary

Successfully identified and downloaded 19 missing PDFs from Zotero library for the OM_QEX systematic review project.

## Final Status

- **114 total studies** in systematic review
- **97 studies** already had GROBID outputs (TEI/TXT)
- **17 studies** truly needed PDFs from Zotero (downloaded)
- **2 studies** were duplicates (already had GROBID but missing metadata)
- **19 PDFs downloaded** to `data/pdfs_from_zotero/`

### Math Check
✅ 97 (existing GROBID) + 17 (new from Zotero) = 114 total studies

## Duplicate Studies (Already Had GROBID)
1. **121295095** (Key: `EPPZJVA8`) - Tackling Psychosocial and Capital Constraints...
2. **121295845** (Key: `VNFUPZUT`) - Impact Evaluation Of The DFID Programme...

These 2 need metadata filled in Master CSV, but already have processing files.

## Files in This Archive

### Analysis Scripts
- `analyze_raw_files.py` - Analyzed Master CSV and fulltext_metadata.csv
- `get_missing_ids.py` - Extracted list of 19 missing study IDs
- `check_pdf_coverage.py` - Calculated PDF coverage statistics
- `reconcile_counts.py` - Reconciled duplicate downloads
- `find_missing_files.py` - Identified 2 missing GROBID files
- `check_duplicates.py` - Found duplicate entries in fulltext_metadata
- `investigate_file_count.py` - Investigated 112 vs 114 file count
- `verify_extraction_ready.py` - Final verification (114/114 complete ✅)

### Documentation
- `ZOTERO_SYNC_ANALYSIS.md` - Analysis of Zotero sync scripts from paper-ftr
- `DOWNLOAD_SUCCESS_REPORT.md` - Complete download success report

### Data Files
- `missing_study_ids.txt` - List of 19 missing study IDs
- `missing_studies_zotero_mapping_20251111_102647.csv` - Study ID → Zotero Key mapping
- `pdf_download_log_20251111_103702.csv` - Download results log

## Scripts Kept in Project Root

### `find_missing_in_zotero.py`
**Purpose:** Search Zotero library for studies missing from GROBID outputs  
**Use when:** Need to find Zotero items matching EPPI-Reviewer study IDs  
**Output:** CSV mapping Study ID → Zotero Key → PDF status

### `download_missing_pdfs.py`
**Purpose:** Download PDFs from Zotero for missing studies  
**Use when:** Have mapping CSV and need to download PDFs  
**Output:** PDFs saved to `data/pdfs_from_zotero/`, download log CSV

## Next Steps

1. **Process 17 PDFs through GROBID** → Create TEI/TXT files
2. **Update fulltext_metadata.csv** → Add 17 new entries with Keys
3. **Update Master CSV** → Fill metadata for 19 NaN entries
4. **Run extractions** → All 114 studies ready for OM/QEX extraction

## Technical Notes

### How Matching Worked
- Searched 1,685 total items in Zotero (671 bibliographic)
- All 19 studies found via `extra` field containing EPPI-Reviewer IDs
- 100% match rate, 100% had PDFs attached

### Zotero Configuration
- **API Key:** `BsaFwjyC5aKwZV7hyR77nzYV`
- **Library Type:** groups
- **Group ID:** 6248442
- **Collection Key:** 8BXTNWER (grey lit collection)

### File Naming
- PDFs: `{study_id}_{zotero_key}.pdf`
- Recommended for GROBID: Use `{zotero_key}` as the file Key
- This keeps naming consistent with existing 97 studies

## References

External scripts analyzed (in `paper-ftr` directory):
- `step_minus1_zotero_export.js` - Node.js full export script
- `sync_pdfs_from_zotero.py` - Python incremental sync script

---

**Date:** November 11, 2025  
**Status:** ✅ Complete - All PDFs downloaded successfully  
**Next:** GROBID processing for 17 new PDFs
