import pandas as pd

# Read files
master = pd.read_csv('data/raw/Master file of included studies (n=96) 10 Nov(data).csv')
metadata = pd.read_csv('data/raw/fulltext_metadata.csv')

# Merge to find studies without Keys
merged = master.merge(metadata, left_on='ID', right_on='paper_id', how='left')
no_key = merged[merged['Key'].isna()]

print("=" * 80)
print(f"Studies in Master File WITHOUT a Key in fulltext_metadata.csv")
print("=" * 80)
print(f"Count: {len(no_key)}\n")

if len(no_key) > 0:
    for idx, row in no_key.iterrows():
        print(f"ID: {row['ID']}")
        print(f"Title: {row['ShortTitle']}")
        print(f"Year: {row['Year']}")
        print(f"Country: {row['Country']}")
        print(f"Program: {row['Program']}")
        print()
    print("⚠️ These studies are in the master file but NOT in fulltext_metadata.csv")
    print("   They cannot have GROBID files without a Key assignment.")
else:
    print("✅ All master file studies have Keys in the metadata!")
    print("\nThis means the discrepancy (96 vs 95) is due to one study")
    print("having a Key but missing GROBID files despite being in metadata.")
