import pandas as pd
import shutil
import os
from pathlib import Path

# Paths
master_file = r'c:\Users\LucasSempe\OneDrive - International Initiative for Impact Evaluation\Desktop\Gen AI tools\8w-sr\OM_QEX\data\raw\Master file of included studies (n=114) 11 Nov(data).csv'
fulltext_metadata = r'c:\Users\LucasSempe\OneDrive - International Initiative for Impact Evaluation\Desktop\Gen AI tools\8w-sr\OM_QEX\data\raw\fulltext_metadata.csv'
source_folder = r'C:\Users\LucasSempe\OneDrive - International Initiative for Impact Evaluation\Desktop\Gen AI tools\8w-sr\pdf_parse_workspace\outputs_grobid'
destination_folder = r'c:\Users\LucasSempe\OneDrive - International Initiative for Impact Evaluation\Desktop\Gen AI tools\8w-sr\OM_QEX\selected_grobid_outputs'

# Create destination folder and subfolders if they don't exist
os.makedirs(destination_folder, exist_ok=True)
os.makedirs(os.path.join(destination_folder, 'tei'), exist_ok=True)
os.makedirs(os.path.join(destination_folder, 'text'), exist_ok=True)

# Load the files
df_master = pd.read_csv(master_file)
df_metadata = pd.read_csv(fulltext_metadata)

print(f"Master file: {len(df_master)} rows")
print(f"Fulltext metadata: {len(df_metadata)} rows")

# Create mapping from paper_id to Key using the fulltext_metadata
# paper_id -> Key
id_to_key = df_metadata.set_index('paper_id')['Key'].to_dict()

# Get the IDs from master file that we want to copy
master_ids = df_master['ID'].tolist()
print(f"\nLooking for {len(master_ids)} papers from master file")

# Find which keys correspond to our master file IDs
keys_to_copy = []
for paper_id in master_ids:
    if paper_id in id_to_key:
        keys_to_copy.append((paper_id, id_to_key[paper_id], df_master[df_master['ID'] == paper_id]['ShortTitle'].values[0]))

print(f"Found {len(keys_to_copy)} matching papers in fulltext metadata")

# Source paths
source_path = Path(source_folder)
tei_path = source_path / 'tei'
text_path = source_path / 'text'

# Copy files
copied_count = 0
not_found = []

for paper_id, key, short_title in keys_to_copy:
    found_any = False
    
    # Look for TEI files
    tei_file = tei_path / f'{key}.tei.xml'
    if tei_file.exists():
        dest_path = Path(destination_folder) / 'tei' / tei_file.name
        try:
            shutil.copy2(tei_file, dest_path)
            print(f"✓ TEI: {key} - {short_title}")
            copied_count += 1
            found_any = True
        except Exception as e:
            print(f"❌ Error copying TEI {key}: {e}")
    
    # Look for text files
    text_file = text_path / f'{key}.txt'
    if text_file.exists():
        dest_path = Path(destination_folder) / 'text' / text_file.name
        try:
            shutil.copy2(text_file, dest_path)
            print(f"✓ TXT: {key} - {short_title}")
            copied_count += 1
            found_any = True
        except Exception as e:
            print(f"❌ Error copying TXT {key}: {e}")
    
    if not found_any:
        not_found.append(f"{key} (ID: {paper_id}) - {short_title}")

print(f"\n{'='*60}")
print(f"✅ Successfully copied {copied_count} files to:")
print(f"   {destination_folder}")

if not_found:
    print(f"\n⚠️ Files not found for {len(not_found)} keys:")
    for item in not_found[:10]:  # Show first 10
        print(f"   - {item}")
    if len(not_found) > 10:
        print(f"   ... and {len(not_found) - 10} more")
