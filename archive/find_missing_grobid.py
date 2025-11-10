import pandas as pd
import os

# Read master file
master = pd.read_csv('data/raw/Master file of included studies (n=96) 10 Nov(data).csv')

# Get TEI files
tei_dir = 'data/grobid_outputs/tei'
tei_files = {f.replace('.tei.xml', '') for f in os.listdir(tei_dir) if f.endswith('.tei.xml')}

print(f'Master file: {len(master)} studies')
print(f'TEI files: {len(tei_files)} files')
print(f'\nStudies in master file WITHOUT GROBID outputs:')
print('=' * 80)

missing_studies = []
for idx, row in master.iterrows():
    study_id = str(row['ID'])
    if study_id not in tei_files:
        missing_studies.append(row)
        print(f'  ID: {study_id}')
        print(f'  Title: {row["ShortTitle"]}')
        print(f'  Year: {row["Year"]}')
        print(f'  Country: {row["Country"]}')
        print()

print(f'\nTotal missing: {len(missing_studies)} studies')
