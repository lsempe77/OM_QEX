import pandas as pd
from pathlib import Path

# Load data
fulltext = pd.read_csv('data/raw/fulltext_metadata.csv')
master = pd.read_csv('data/raw/Master file of included studies (n=114) 11 Nov(data).csv')

# Get fulltext entries for master studies only
master_ids = set(master['ID'].astype(str))
fulltext_master = fulltext[fulltext['paper_id'].astype(str).isin(master_ids)]

print("="*70)
print("FINDING MISSING FILES")
print("="*70)

print(f"\nFulltext entries for 114 master studies: {len(fulltext_master)}")

# Get existing files
tei_dir = Path('data/grobid_outputs/tei')
txt_dir = Path('data/grobid_outputs/text')

existing_tei_keys = set([f.stem.replace('.tei', '') for f in tei_dir.glob('*.xml')])
existing_txt_keys = set([f.stem for f in txt_dir.glob('*.txt')])

print(f"TEI files on disk: {len(existing_tei_keys)}")
print(f"TXT files on disk: {len(existing_txt_keys)}")

# Get keys from metadata
fulltext_keys = set(fulltext_master['Key'].astype(str))
print(f"Keys in metadata: {len(fulltext_keys)}")

# Find missing
missing_tei = fulltext_keys - existing_tei_keys
missing_txt = fulltext_keys - existing_txt_keys

print(f"\n{'='*70}")
print("MISSING FILES")
print("="*70)

if missing_tei:
    print(f"\nKeys in metadata but TEI files missing: {len(missing_tei)}")
    for key in sorted(list(missing_tei)):
        row = fulltext_master[fulltext_master['Key'] == key]
        if not row.empty:
            paper_id = row.iloc[0]['paper_id']
            title = str(row.iloc[0]['Title'])[:60]
            print(f"  {key}: Study {paper_id} - {title}")
else:
    print("\n✅ All TEI files present!")

if missing_txt:
    print(f"\nKeys in metadata but TXT files missing: {len(missing_txt)}")
    for key in sorted(list(missing_txt)):
        row = fulltext_master[fulltext_master['Key'] == key]
        if not row.empty:
            paper_id = row.iloc[0]['paper_id']
            title = str(row.iloc[0]['Title'])[:60]
            print(f"  {key}: Study {paper_id} - {title}")
else:
    print("\n✅ All TXT files present!")

# Check if files exist but with wrong naming
print(f"\n{'='*70}")
print("DIAGNOSTICS")
print("="*70)

if missing_tei:
    print("\nChecking if PDFs exist for missing entries:")
    pdf_dir = Path('data/pdfs_from_zotero')
    if pdf_dir.exists():
        pdf_files = list(pdf_dir.glob('*.pdf'))
        print(f"PDFs in data/pdfs_from_zotero/: {len(pdf_files)}")
        
        for key in sorted(list(missing_tei)):
            row = fulltext_master[fulltext_master['Key'] == key]
            if not row.empty:
                paper_id = row.iloc[0]['paper_id']
                # Check if PDF exists with study_id pattern
                matching_pdfs = [f for f in pdf_files if str(paper_id) in f.name]
                if matching_pdfs:
                    print(f"  ✓ PDF exists: {matching_pdfs[0].name}")
                else:
                    print(f"  ✗ No PDF found for study {paper_id}")
