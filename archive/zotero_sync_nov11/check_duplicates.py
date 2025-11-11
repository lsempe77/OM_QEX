import pandas as pd
from pathlib import Path

# Load fulltext metadata
fulltext = pd.read_csv('data/raw/fulltext_metadata.csv')

print("="*70)
print("DUPLICATE INVESTIGATION")
print("="*70)

# Check for duplicate entries
duplicates = fulltext[fulltext.duplicated(subset=['paper_id'], keep=False)]
print(f"\nDuplicate paper_id entries: {len(duplicates)}")

if len(duplicates) > 0:
    print("\nDuplicate studies:")
    for paper_id in duplicates['paper_id'].unique():
        entries = fulltext[fulltext['paper_id'] == paper_id]
        print(f"\n  Study {paper_id}: {len(entries)} entries")
        for idx, row in entries.iterrows():
            has_title = 'with title' if pd.notna(row['Title']) else 'NO TITLE'
            print(f"    Row {idx}: Key={row['Key']}, {has_title}")

print("\n" + "="*70)
print("SOLUTION")
print("="*70)

print("\nYou need to:")
print("1. Remove duplicate entries from fulltext_metadata.csv")
print("2. Keep only the entries WITH titles (original entries)")
print("3. The GROBID files already exist for these 2 studies")
print("\nOr these 2 studies need to be processed through GROBID with keys:")
print("  - EPPZJVA8 for study 121295095")
print("  - VNFUPZUT for study 121295845")
