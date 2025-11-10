import pandas as pd
import os

# Read master file
master = pd.read_csv('data/raw/Master file of included studies (n=96) 10 Nov(data).csv')
metadata = pd.read_csv('data/raw/fulltext_metadata.csv')

print("=" * 80)
print("DETAILED COUNT CHECK")
print("=" * 80)
print(f"Master file rows: {len(master)}")
print(f"Master file unique IDs: {master['ID'].nunique()}")

# Count TEI files
tei_dir = 'data/grobid_outputs/tei'
tei_files = [f for f in os.listdir(tei_dir) if f.endswith('.tei.xml')]
print(f"TEI files on disk: {len(tei_files)}")

# Get master IDs that have Keys
master_with_meta = master.merge(metadata, left_on='ID', right_on='paper_id', how='left')
has_key = master_with_meta['Key'].notna().sum()
no_key = master_with_meta['Key'].isna().sum()

print(f"\nMaster studies WITH Key in metadata: {has_key}")
print(f"Master studies WITHOUT Key in metadata: {no_key}")

# Show the studies without keys
if no_key > 0:
    print("\n" + "=" * 80)
    print("STUDIES WITHOUT KEYS (CANNOT HAVE GROBID FILES):")
    print("=" * 80)
    no_key_studies = master_with_meta[master_with_meta['Key'].isna()]
    for idx, row in no_key_studies.iterrows():
        print(f"\nID: {row['ID']}")
        print(f"ShortTitle: {row['ShortTitle']}")
        print(f"Year: {row['Year']}")
        print(f"Country: {row['Country']}")
        print(f"Program: {row['Program']}")

# Now check if all Keys have TEI files
tei_keys = set(f.replace('.tei.xml', '') for f in tei_files)
master_keys = set(master_with_meta['Key'].dropna())

print(f"\n" + "=" * 80)
print("KEY MATCHING:")
print("=" * 80)
print(f"Unique Keys in master: {len(master_keys)}")
print(f"Unique Keys in TEI folder: {len(tei_keys)}")
print(f"Master Keys found in TEI: {len(master_keys & tei_keys)}")
print(f"Master Keys NOT in TEI: {len(master_keys - tei_keys)}")

if len(master_keys - tei_keys) > 0:
    print("\n" + "=" * 80)
    print("KEYS IN MASTER BUT NOT IN TEI FOLDER:")
    print("=" * 80)
    for key in master_keys - tei_keys:
        study = master_with_meta[master_with_meta['Key'] == key].iloc[0]
        print(f"\nKey: {key}")
        print(f"ID: {study['ID']}")
        print(f"ShortTitle: {study['ShortTitle']}")
