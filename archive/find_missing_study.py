import pandas as pd
import os

# Read master file
master = pd.read_csv('data/raw/Master file of included studies (n=96) 10 Nov(data).csv')

# Read metadata
metadata = pd.read_csv('data/raw/fulltext_metadata.csv')

# Get TEI files
tei_dir = 'data/grobid_outputs/tei'
tei_files = {f.replace('.tei.xml', '') for f in os.listdir(tei_dir) if f.endswith('.tei.xml')}

# Merge master with metadata to get Keys
master_with_keys = master.merge(metadata, left_on='ID', right_on='paper_id', how='left')

# Find studies WITHOUT GROBID files
missing = master_with_keys[~master_with_keys['Key'].isin(tei_files)]

print("=" * 80)
print(f"MISSING GROBID FILES: {len(missing)} study")
print("=" * 80)

if len(missing) > 0:
    for idx, row in missing.iterrows():
        print(f"\nStudy ID: {row['ID']}")
        print(f"Key: {row['Key']}")
        print(f"Title: {row['ShortTitle']}")
        print(f"Year: {row['Year']}")
        print(f"Country: {row['Country']}")
        print(f"Program: {row['Program']}")
        print(f"\nExpected files:")
        print(f"  - data/grobid_outputs/tei/{row['Key']}.tei.xml")
        print(f"  - data/grobid_outputs/text/{row['Key']}.txt")
else:
    print("\n✅ ALL STUDIES HAVE GROBID FILES!")

print("\n" + "=" * 80)
print(f"Total: {len(master)} studies in master file")
print(f"Have GROBID: {len(tei_files)} studies")
print(f"Missing: {len(missing)} studies")
print("=" * 80)
