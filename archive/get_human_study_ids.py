import pandas as pd

# Read human extraction
df = pd.read_csv('data/human_extraction/8 week SR QEX Pierre SOF and TEEP(Quant Extraction Form).csv', skiprows=3)

# Get unique study IDs (column 2 = index 2)
study_ids = df.iloc[:, 2].unique()

print("=" * 80)
print("HUMAN EXTRACTION STUDY IDs")
print("=" * 80)
print(f"Total unique studies: {len(study_ids)}\n")

for study_id in study_ids:
    print(f"  {study_id}")

print("\n" + "=" * 80)
print("These are the study IDs we should extract with the LLM to compare")
print("=" * 80)
