import pandas as pd

# Read metadata
meta = pd.read_csv('data/raw/fulltext_metadata.csv')

# Study IDs from human extraction
study_ids = [121294984, 121058364, 121498842]

print("=" * 80)
print("MAPPING STUDY IDs TO KEYS")
print("=" * 80)

keys = []
for sid in study_ids:
    row = meta[meta['paper_id'] == sid]
    if len(row) > 0:
        key = row.iloc[0]['Key']
        title = row.iloc[0]['Title']
        keys.append(key)
        print(f"\nStudy ID: {sid}")
        print(f"Key: {key}")
        print(f"Title: {title[:80]}...")
    else:
        print(f"\n⚠️ NOT FOUND: {sid}")

print("\n" + "=" * 80)
print("COMMAND TO RUN EXTRACTION:")
print("=" * 80)
print(f"\npython run_extraction.py --keys {' '.join(keys)}")
