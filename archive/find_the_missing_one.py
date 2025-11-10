import pandas as pd
import os

# Read master file (96 studies)
master = pd.read_csv('data/raw/Master file of included studies (n=96) 10 Nov(data).csv')

# Read metadata
metadata = pd.read_csv('data/raw/fulltext_metadata.csv')

# Get actual TEI files on disk
tei_dir = 'data/grobid_outputs/tei'
tei_files = set(f.replace('.tei.xml', '') for f in os.listdir(tei_dir) if f.endswith('.tei.xml'))

print("=" * 80)
print("FINDING THE MISSING STUDY")
print("=" * 80)
print(f"Master file: {len(master)} studies")
print(f"TEI files on disk: {len(tei_files)} files")
print(f"Missing: {len(master) - len(tei_files)} study\n")

# For each study in master, check if it has GROBID files
missing_studies = []

for idx, study in master.iterrows():
    study_id = study['ID']
    
    # Look up Key in metadata
    key_lookup = metadata[metadata['paper_id'] == study_id]
    
    if len(key_lookup) == 0:
        # No Key assigned at all
        missing_studies.append({
            'ID': study_id,
            'ShortTitle': study['ShortTitle'],
            'Year': study['Year'],
            'Country': study['Country'],
            'Program': study['Program'],
            'Key': 'NO KEY IN METADATA',
            'Has_TEI': False,
            'Issue': 'Missing from fulltext_metadata.csv'
        })
    else:
        key = key_lookup.iloc[0]['Key']
        has_tei = key in tei_files
        
        if not has_tei:
            missing_studies.append({
                'ID': study_id,
                'ShortTitle': study['ShortTitle'],
                'Year': study['Year'],
                'Country': study['Country'],
                'Program': study['Program'],
                'Key': key,
                'Has_TEI': False,
                'Issue': 'Key exists but TEI file missing'
            })

print("=" * 80)
print(f"STUDIES WITHOUT GROBID FILES: {len(missing_studies)}")
print("=" * 80)

for i, study in enumerate(missing_studies, 1):
    print(f"\n[{i}] ID: {study['ID']}")
    print(f"    ShortTitle: {study['ShortTitle']}")
    print(f"    Year: {study['Year']}")
    print(f"    Country: {study['Country']}")
    print(f"    Program: {study['Program']}")
    print(f"    Key: {study['Key']}")
    print(f"    Issue: {study['Issue']}")
    
    if study['Key'] != 'NO KEY IN METADATA':
        print(f"\n    Expected files:")
        print(f"      - data/grobid_outputs/tei/{study['Key']}.tei.xml")
        print(f"      - data/grobid_outputs/text/{study['Key']}.txt")

if len(missing_studies) == 0:
    print("\n✅ ALL 96 STUDIES HAVE GROBID FILES!")
    print("\nWait, that can't be right if there are only 95 files...")
    print("Let me verify the count:")
    print(f"\nActual TEI files counted: {len(tei_files)}")
