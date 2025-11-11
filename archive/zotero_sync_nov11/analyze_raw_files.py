import pandas as pd

# Load both files
master = pd.read_csv('data/raw/Master file of included studies (n=114) 11 Nov(data).csv')
fulltext = pd.read_csv('data/raw/fulltext_metadata.csv')

print("="*60)
print("MASTER FILE ANALYSIS")
print("="*60)
print(f"Total rows: {len(master)}")
print(f"Columns: {master.columns.tolist()}")
print(f"\nColumn info:")
for col in master.columns:
    non_null = master[col].notna().sum()
    print(f"  {col}: {non_null}/{len(master)} non-null values")

print(f"\nSample records:")
print(master.head(3)[['ID', 'ShortTitle', 'Year', 'Country', 'Program']])

print("\n" + "="*60)
print("FULLTEXT METADATA ANALYSIS")
print("="*60)
print(f"Total rows: {len(fulltext)}")
print(f"Columns: {fulltext.columns.tolist()}")
print(f"\nColumn info:")
for col in fulltext.columns:
    non_null = fulltext[col].notna().sum()
    print(f"  {col}: {non_null}/{len(fulltext)} non-null values")

print(f"\nFiles with fulltext:")
print(f"  has_fulltext=TRUE: {fulltext['has_fulltext'].sum()}")
print(f"  txt_exists=TRUE: {fulltext['txt_exists'].sum()}")
print(f"  xml_exists=TRUE: {fulltext['xml_exists'].sum()}")

print("\n" + "="*60)
print("RELATIONSHIP BETWEEN FILES")
print("="*60)
overlap = set(master['ID']) & set(fulltext['paper_id'])
print(f"Studies in BOTH files: {len(overlap)}/{len(master)} master studies")
print(f"Studies ONLY in master: {len(set(master['ID']) - set(fulltext['paper_id']))}")
print(f"Studies ONLY in fulltext: {len(set(fulltext['paper_id']) - set(master['ID']))}")

print(f"\nSample overlapping study IDs:")
for study_id in list(overlap)[:3]:
    master_title = master[master['ID'] == study_id]['ShortTitle'].values[0]
    fulltext_key = fulltext[fulltext['paper_id'] == study_id]['Key'].values[0]
    print(f"  ID {study_id}: {master_title} -> Key: {fulltext_key}")

print("\n" + "="*60)
print("KEY INSIGHTS")
print("="*60)
print("Master file contains:")
print("  - 114 included studies for the systematic review")
print("  - Study metadata: ID, title, year, country, program info")
print("  - Flags for qualitative/cost data availability")
print("")
print("Fulltext metadata contains:")
print("  - 654 papers (much larger - includes all processed papers)")
print("  - File location info (paths to .txt and .xml files)")
print("  - 'Key' identifier used for filenames")
print("  - Flags for which files actually exist")
print("")
print("The Master file ID maps to fulltext paper_id")
print("The fulltext 'Key' is used to locate TEI/TXT files in data/grobid_outputs/")
