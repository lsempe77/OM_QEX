import pandas as pd
import shutil
import os

# Since the Zotero files don't exist, let's work with what we have in the processed folder
# and create a mapping to show which studies from the master file have processed versions

source_text = r'C:\Users\LucasSempe\OneDrive - International Initiative for Impact Evaluation\Desktop\Gen AI tools\8w-sr\paper-screening-pipeline\data\input\fulltext\processed\text'
source_tei = r'C:\Users\LucasSempe\OneDrive - International Initiative for Impact Evaluation\Desktop\Gen AI tools\8w-sr\paper-screening-pipeline\data\input\fulltext\processed\tei_xml'
grad_fulltext = r'C:\Users\LucasSempe\OneDrive - International Initiative for Impact Evaluation\Desktop\Gen AI tools\8w-sr\paper-screening-pipeline\data\input\fulltext\Grad approaches FTR & grey lit.csv'
master_file = r'c:\Users\LucasSempe\OneDrive - International Initiative for Impact Evaluation\Desktop\Gen AI tools\8w-sr\OM_QEX\Master file of included studies (n=95) 10 Nov(data)_with_key.csv'
output_dir = r'c:\Users\LucasSempe\OneDrive - International Initiative for Impact Evaluation\Desktop\Gen AI tools\8w-sr\OM_QEX\selected_papers'

# Read files
df_grad_fulltext = pd.read_csv(grad_fulltext)
df_master = pd.read_csv(master_file)

# Get all text files available
text_files = [f.replace('.txt', '') for f in os.listdir(source_text) if f.endswith('.txt')]
print(f"Available text files in processed folder: {len(text_files)}")
print(f"Sample: {text_files[:5]}")

# Get all tei files available
tei_files = [f.replace('.tei.xml', '') for f in os.listdir(source_tei) if f.endswith('.tei.xml')]
print(f"\nAvailable TEI XML files in processed folder: {len(tei_files)}")
print(f"Sample: {tei_files[:5]}")

# Check overlap between the 654-row grad file and the master file IDs
print(f"\n{'='*60}")
print("ANALYZING OVERLAP")
print(f"{'='*60}")

# Extract EPPI IDs from grad_fulltext
def extract_eppi_id(extra_text):
    if pd.isna(extra_text):
        return None
    import re
    match = re.search(r'EPPI-Reviewer ID:\s*(\d+)', str(extra_text))
    if match:
        return int(match.group(1))
    return None

df_grad_fulltext['eppi_id'] = df_grad_fulltext['Extra'].apply(extract_eppi_id)

# Find which keys in the processed folder correspond to master file IDs
master_ids = set(df_master['ID'].dropna())
grad_fulltext_with_eppi = df_grad_fulltext[df_grad_fulltext['eppi_id'].notna()]
overlap = grad_fulltext_with_eppi[grad_fulltext_with_eppi['eppi_id'].isin(master_ids)]

print(f"Master file IDs: {len(master_ids)}")
print(f"Grad fulltext entries with EPPI IDs: {len(grad_fulltext_with_eppi)}")
print(f"Overlap (IDs in both): {len(overlap)}")

if len(overlap) > 0:
    print(f"\n✅ Found {len(overlap)} studies from master file in the processed folder!")
    print("\nCopying files...")
    
    # Create output directories
    output_text = os.path.join(output_dir, 'text')
    output_tei = os.path.join(output_dir, 'tei_xml')
    os.makedirs(output_text, exist_ok=True)
    os.makedirs(output_tei, exist_ok=True)
    
    copied_text = 0
    copied_tei = 0
    
    for idx, row in overlap.iterrows():
        key = row['Key']
        eppi_id = int(row['eppi_id'])
        
        # Copy text file
        text_src = os.path.join(source_text, f"{key}.txt")
        if os.path.exists(text_src):
            # Rename to include EPPI ID for easy identification
            text_dest = os.path.join(output_text, f"{eppi_id}_{key}.txt")
            shutil.copy2(text_src, text_dest)
            copied_text += 1
        
        # Copy TEI XML file
        tei_src = os.path.join(source_tei, f"{key}.tei.xml")
        if os.path.exists(tei_src):
            tei_dest = os.path.join(output_tei, f"{eppi_id}_{key}.tei.xml")
            shutil.copy2(tei_src, tei_dest)
            copied_tei += 1
    
    print(f"\n{'='*60}")
    print(f"COPY SUMMARY")
    print(f"{'='*60}")
    print(f"Text files copied: {copied_text}")
    print(f"TEI XML files copied: {copied_tei}")
    print(f"\n✅ Files copied to: {output_dir}")
    
    # Save mapping file
    mapping = overlap[['eppi_id', 'Key', 'Author', 'Title', 'Publication Year']].copy()
    mapping_file = os.path.join(output_dir, 'id_to_key_mapping.csv')
    mapping.to_csv(mapping_file, index=False)
    print(f"✅ Mapping file saved to: {mapping_file}")
else:
    print("\n❌ No overlap found between master file and processed folder.")
    print("The processed folder contains a different set of papers.")
