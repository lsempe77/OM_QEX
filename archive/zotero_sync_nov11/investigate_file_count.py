import pandas as pd
from pathlib import Path

# Load data
master = pd.read_csv('data/raw/Master file of included studies (n=114) 11 Nov(data).csv')
fulltext = pd.read_csv('data/raw/fulltext_metadata.csv')

# Get unique fulltext entries for master studies
master_ids = set(master['ID'].astype(str))
fulltext_master = fulltext[fulltext['paper_id'].astype(str).isin(master_ids)]

# Remove duplicates, keeping first occurrence (the ones with titles)
fulltext_unique = fulltext_master.drop_duplicates(subset=['paper_id'], keep='first')

print("="*70)
print("FILE COUNT INVESTIGATION")
print("="*70)

print(f"\nMaster file studies: {len(master)}")
print(f"Fulltext entries for master studies: {len(fulltext_master)}")
print(f"Unique fulltext entries (after dedup): {len(fulltext_unique)}")

# Get files on disk
tei_dir = Path('data/grobid_outputs/tei')
txt_dir = Path('data/grobid_outputs/text')

tei_files = sorted([f.stem.replace('.tei', '') for f in tei_dir.glob('*.xml')])
txt_files = sorted([f.stem for f in txt_dir.glob('*.txt')])

print(f"\nTEI files on disk: {len(tei_files)}")
print(f"TXT files on disk: {len(txt_files)}")

# Get expected keys from metadata
expected_keys = set(fulltext_unique['Key'].astype(str))
actual_tei_keys = set(tei_files)
actual_txt_keys = set(txt_files)

print(f"Expected unique keys: {len(expected_keys)}")

# Find missing files
missing_tei = expected_keys - actual_tei_keys
missing_txt = expected_keys - actual_txt_keys

print("\n" + "="*70)
print("MISSING FILES")
print("="*70)

if missing_tei:
    print(f"\nMissing TEI files: {len(missing_tei)}")
    for key in sorted(missing_tei):
        row = fulltext_unique[fulltext_unique['Key'] == key]
        if not row.empty:
            paper_id = row.iloc[0]['paper_id']
            title = str(row.iloc[0]['Title'])[:70]
            print(f"  {key}: Study {paper_id}")
            print(f"    Title: {title}")
else:
    print("\n✅ All expected TEI files are present")

if missing_txt:
    print(f"\nMissing TXT files: {len(missing_txt)}")
    for key in sorted(missing_txt):
        row = fulltext_unique[fulltext_unique['Key'] == key]
        if not row.empty:
            paper_id = row.iloc[0]['paper_id']
            title = str(row.iloc[0]['Title'])[:70]
            print(f"  {key}: Study {paper_id}")
            print(f"    Title: {title}")
else:
    print("\n✅ All expected TXT files are present")

# Check for extra files (files on disk not in metadata)
extra_tei = actual_tei_keys - expected_keys
extra_txt = actual_txt_keys - expected_keys

if extra_tei or extra_txt:
    print("\n" + "="*70)
    print("EXTRA FILES (not needed for master studies)")
    print("="*70)
    
    if extra_tei:
        print(f"\nExtra TEI files: {len(extra_tei)}")
        for key in sorted(list(extra_tei)[:10]):
            print(f"  {key}")
    
    if extra_txt:
        print(f"\nExtra TXT files: {len(extra_txt)}")

# Summary
print("\n" + "="*70)
print("SUMMARY")
print("="*70)

print(f"\n114 studies in Master file")
print(f"114 unique entries needed in fulltext_metadata")
print(f"112 TEI files on disk")
print(f"112 TXT files on disk")
print(f"\nGap: {len(expected_keys) - len(actual_tei_keys)} files missing")

if len(missing_tei) > 0:
    print(f"\n⚠ Need to process {len(missing_tei)} more PDFs through GROBID")
    print(f"\nCheck if PDFs exist:")
    pdf_dir = Path('data/pdfs_from_zotero')
    if pdf_dir.exists():
        for key in sorted(missing_tei):
            row = fulltext_unique[fulltext_unique['Key'] == key]
            if not row.empty:
                paper_id = row.iloc[0]['paper_id']
                matching_pdfs = list(pdf_dir.glob(f'*{paper_id}*.pdf'))
                if matching_pdfs:
                    print(f"  ✓ PDF found: {matching_pdfs[0].name}")
                else:
                    print(f"  ✗ No PDF for study {paper_id}")
