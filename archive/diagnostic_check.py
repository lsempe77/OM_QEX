import pandas as pd
import os

# Read files
master = pd.read_csv('data/raw/Master file of included studies (n=96) 10 Nov(data).csv')
metadata = pd.read_csv('data/raw/fulltext_metadata.csv')

# Get TEI files from disk
tei_dir = 'data/grobid_outputs/tei'
tei_files = set(f.replace('.tei.xml', '') for f in os.listdir(tei_dir) if f.endswith('.tei.xml'))

# Get Keys from master file
merged = master.merge(metadata, left_on='ID', right_on='paper_id', how='left')
master_keys = set(merged['Key'].dropna())

print("=" * 80)
print("DIAGNOSTIC: Master File vs GROBID Files")
print("=" * 80)
print(f"Master file studies: {len(master)}")
print(f"Master file studies with Keys: {len(master_keys)}")
print(f"TEI files on disk: {len(tei_files)}")
print()
print(f"Master Keys WITH TEI files: {len(master_keys & tei_files)}")
print(f"Master Keys WITHOUT TEI files: {len(master_keys - tei_files)}")
print()

if len(master_keys - tei_files) > 0:
    print("=" * 80)
    print("MISSING GROBID FILES:")
    print("=" * 80)
    missing_keys = master_keys - tei_files
    for key in missing_keys:
        study = merged[merged['Key'] == key].iloc[0]
        print(f"\nKey: {key}")
        print(f"ID: {study['ID']}")
        print(f"Title: {study['ShortTitle']}")
        print(f"Year: {study['Year']}")
        print(f"Country: {study['Country']}")
else:
    print("✅ ALL MASTER FILE STUDIES HAVE GROBID FILES!")
    print()
    print("Wait... let me check if there are EXTRA TEI files not in master:")
    extra_tei = tei_files - master_keys
    if len(extra_tei) > 0:
        print(f"\n⚠️ Found {len(extra_tei)} TEI files NOT in current master file:")
        for key in list(extra_tei)[:10]:  # Show first 10
            print(f"  - {key}")
        if len(extra_tei) > 10:
            print(f"  ... and {len(extra_tei) - 10} more")
