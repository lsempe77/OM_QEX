import pandas as pd

# Compare old and new master files
master_96 = pd.read_csv('data/raw/Master file of included studies (n=96) 10 Nov(data).csv')
master_95 = pd.read_csv('data/raw/Master file of included studies (n=95) 10 Nov(data)_with_key.csv')

# Find the difference
new_ids = set(master_96['ID']) - set(master_95['ID'])

print("=" * 80)
print("FINDING THE 96TH STUDY")
print("=" * 80)

if new_ids:
    print(f"Found {len(new_ids)} new study added to the master file:\n")
    for study_id in new_ids:
        study = master_96[master_96['ID'] == study_id].iloc[0]
        print(f"ID: {study['ID']}")
        print(f"ShortTitle: {study['ShortTitle']}")
        print(f"Full Title: {study['Title']}")
        print(f"Year: {study['Year']}")
        print(f"Country: {study['Country']}")
        print(f"Program: {study['Program']}")
        print()
        
        # Check if it has a Key
        metadata = pd.read_csv('data/raw/fulltext_metadata.csv')
        key_row = metadata[metadata['paper_id'] == study_id]
        
        if len(key_row) > 0:
            print(f"✅ Has Key: {key_row.iloc[0]['Key']}")
        else:
            print("❌ NO KEY in fulltext_metadata.csv")
            print("   This study cannot have GROBID files without a Key!")
else:
    print("No new studies found - both files have the same IDs")
    print("The difference must be something else (updated data perhaps)")
