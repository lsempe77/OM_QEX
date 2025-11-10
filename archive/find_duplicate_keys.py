import pandas as pd

# Read files
master = pd.read_csv('data/raw/Master file of included studies (n=96) 10 Nov(data).csv')
metadata = pd.read_csv('data/raw/fulltext_metadata.csv')

# Merge
master_with_keys = master.merge(metadata, left_on='ID', right_on='paper_id', how='left')

# Find duplicate Keys
key_counts = master_with_keys['Key'].value_counts()
duplicate_keys = key_counts[key_counts > 1]

print("=" * 80)
print("FINDING DUPLICATE KEYS")
print("=" * 80)
print(f"Total studies: {len(master)}")
print(f"Total unique Keys: {master_with_keys['Key'].nunique()}")
print(f"Keys appearing more than once: {len(duplicate_keys)}\n")

if len(duplicate_keys) > 0:
    print("=" * 80)
    print("DUPLICATE KEYS (2 studies sharing the same GROBID files):")
    print("=" * 80)
    
    for key, count in duplicate_keys.items():
        print(f"\nKey: {key} (appears {count} times)")
        print("-" * 80)
        
        studies = master_with_keys[master_with_keys['Key'] == key]
        for idx, study in studies.iterrows():
            print(f"\n  Study ID: {study['ID']}")
            print(f"  ShortTitle: {study['ShortTitle']}")
            print(f"  Year: {study['Year']}")
            print(f"  Country: {study['Country']}")
            print(f"  Program: {study['Program']}")
else:
    print("No duplicate Keys found - something else is wrong!")
