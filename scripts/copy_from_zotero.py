import pandas as pd
import shutil
import os
import re
from pathlib import Path

# Paths
grad_file = r'c:\Users\LucasSempe\OneDrive - International Initiative for Impact Evaluation\Desktop\Gen AI tools\8w-sr\OM_QEX\Grad approaches FTR & grey lit.csv'
master_file = r'c:\Users\LucasSempe\OneDrive - International Initiative for Impact Evaluation\Desktop\Gen AI tools\8w-sr\OM_QEX\Master file of included studies (n=95) 10 Nov(data)_with_key.csv'
output_dir = r'c:\Users\LucasSempe\OneDrive - International Initiative for Impact Evaluation\Desktop\Gen AI tools\8w-sr\OM_QEX\selected_papers'

# Create output directory
os.makedirs(output_dir, exist_ok=True)

# Read files
df_grad = pd.read_csv(grad_file)
df_master = pd.read_csv(master_file)

# Filter master file to only rows with keys
df_master_with_key = df_master[df_master['key'].notna()].copy()

print(f"Total studies in master file: {len(df_master)}")
print(f"Studies with key: {len(df_master_with_key)}")

# Get the keys we need
needed_keys = set(df_master_with_key['key'].str.upper())
print(f"\nKeys to find: {len(needed_keys)}")

# Find matching rows in grad file
df_grad['key_upper'] = df_grad['Key'].str.upper()
df_matches = df_grad[df_grad['key_upper'].isin(needed_keys)].copy()

print(f"Matches found in grad file: {len(df_matches)}")

# Copy files
copied = 0
missing = 0
no_attachments = 0

for idx, row in df_matches.iterrows():
    key = row['Key']
    attachments = row['File Attachments']
    
    if pd.isna(attachments):
        no_attachments += 1
        continue
    
    # Split multiple file paths (separated by semicolons)
    file_paths = [f.strip() for f in str(attachments).split(';')]
    
    # Copy each file
    for file_path in file_paths:
        if os.path.exists(file_path):
            # Create output filename: KEY_originalname.ext
            original_name = os.path.basename(file_path)
            output_name = f"{key}_{original_name}"
            output_path = os.path.join(output_dir, output_name)
            
            try:
                shutil.copy2(file_path, output_path)
                copied += 1
                print(f"✓ Copied: {key} -> {original_name}")
            except Exception as e:
                print(f"✗ Error copying {file_path}: {e}")
                missing += 1
        else:
            print(f"✗ File not found: {file_path}")
            missing += 1

print(f"\n{'='*60}")
print(f"COPY SUMMARY")
print(f"{'='*60}")
print(f"Studies matched: {len(df_matches)}/{len(needed_keys)}")
print(f"Files copied: {copied}")
print(f"Files missing/errors: {missing}")
print(f"Studies with no attachments: {no_attachments}")
print(f"\n✅ Files copied to: {output_dir}")

# Show which keys weren't found
not_found = needed_keys - set(df_matches['key_upper'])
if not_found:
    print(f"\n⚠️ {len(not_found)} keys not found in grad file:")
    for key in list(not_found)[:10]:
        study = df_master_with_key[df_master_with_key['key'].str.upper() == key]['ShortTitle'].iloc[0]
        print(f"  - {key} ({study})")
    if len(not_found) > 10:
        print(f"  ... and {len(not_found) - 10} more")
