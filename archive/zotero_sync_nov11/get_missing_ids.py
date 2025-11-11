import pandas as pd

# Get the 17 missing study IDs
master = pd.read_csv('data/raw/Master file of included studies (n=114) 11 Nov(data).csv')
missing_ids = master[master['ShortTitle'].isna()]['ID'].tolist()

print("="*70)
print("17 MISSING STUDY IDs (Need from Zotero)")
print("="*70)
print()

for i, study_id in enumerate(missing_ids, 1):
    print(f"{i:2}. {study_id}")

print()
print("="*70)
print("SAVE THIS LIST")
print("="*70)

# Save to file for easy reference
with open('missing_study_ids.txt', 'w') as f:
    for study_id in missing_ids:
        f.write(f"{study_id}\n")

print("✓ Saved to: missing_study_ids.txt")
print()
print("Next: Use this list to find matching items in Zotero")
