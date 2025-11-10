import pandas as pd
import os

# Paths
master_file = r'c:\Users\LucasSempe\OneDrive - International Initiative for Impact Evaluation\Desktop\Gen AI tools\8w-sr\OM_QEX\Master file of included studies (n=95) 10 Nov(data)_with_key.csv'
source_dir_text = r'C:\Users\LucasSempe\OneDrive - International Initiative for Impact Evaluation\Desktop\Gen AI tools\8w-sr\paper-screening-pipeline\data\input\fulltext\processed\text'

# Read master file
df = pd.read_csv(master_file)
df_with_key = df[df['key'].notna()].copy()

# Get keys from master file
master_keys = set(df_with_key['key'].str.upper())
print(f"Keys in master file: {len(master_keys)}")
print(f"Sample keys from master: {list(master_keys)[:10]}")

# Get files from directory
text_files = [f.replace('.txt', '') for f in os.listdir(source_dir_text) if f.endswith('.txt')]
text_keys = set([f.upper() for f in text_files])
print(f"\nFiles in processed folder: {len(text_keys)}")
print(f"Sample keys from folder: {list(text_keys)[:10]}")

# Find matches
matches = master_keys.intersection(text_keys)
print(f"\n✅ Matching keys: {len(matches)}")
if matches:
    print(f"Sample matches: {list(matches)[:10]}")

# Find missing
missing = master_keys - text_keys
print(f"\n❌ Keys in master but NOT in folder: {len(missing)}")
if missing:
    print(f"Sample missing: {list(missing)[:10]}")
