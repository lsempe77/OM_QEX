import pandas as pd
import re

# Read both CSV files
grad_file = r'c:\Users\LucasSempe\OneDrive - International Initiative for Impact Evaluation\Desktop\Gen AI tools\8w-sr\OM_QEX\Grad approaches FTR & grey lit.csv'
master_file = r'c:\Users\LucasSempe\OneDrive - International Initiative for Impact Evaluation\Desktop\Gen AI tools\8w-sr\OM_QEX\Master file of included studies (n=95) 10 Nov(data).csv'

# Load the datasets
df_grad = pd.read_csv(grad_file)
df_master = pd.read_csv(master_file)

print("Grad file shape:", df_grad.shape)
print("Master file shape:", df_master.shape)
print("\nGrad file columns:", df_grad.columns.tolist())
print("Master file columns:", df_master.columns.tolist())

# Extract EPPI-Reviewer ID from the Extra column in grad file
def extract_eppi_id(extra_text):
    """Extract EPPI-Reviewer ID from the Extra column"""
    if pd.isna(extra_text):
        return None
    # Look for pattern "EPPI-Reviewer ID: 121XXXXXX"
    match = re.search(r'EPPI-Reviewer ID:\s*(\d+)', str(extra_text))
    if match:
        return int(match.group(1))
    return None

# Create a mapping dictionary from EPPI ID to Key
df_grad['eppi_id'] = df_grad['Extra'].apply(extract_eppi_id)
print(f"\nExtracted EPPI IDs from {df_grad['eppi_id'].notna().sum()} rows in grad file")
print("Sample EPPI IDs:", df_grad['eppi_id'].dropna().head())

# Create mapping dictionary: EPPI ID -> Key
# Handle duplicates by keeping the first occurrence
df_grad_unique = df_grad.dropna(subset=['eppi_id']).drop_duplicates(subset=['eppi_id'], keep='first')
eppi_to_key = df_grad_unique.set_index('eppi_id')['Key'].to_dict()
print(f"\nCreated mapping with {len(eppi_to_key)} entries")

# Check for duplicates
duplicates = df_grad[df_grad['eppi_id'].notna()].groupby('eppi_id').size()
duplicates = duplicates[duplicates > 1]
if len(duplicates) > 0:
    print(f"⚠️ Found {len(duplicates)} duplicate EPPI IDs (keeping first occurrence)")

# Map the Key column to master file using ID column
df_master['key'] = df_master['ID'].map(eppi_to_key)

print(f"\nMatched {df_master['key'].notna().sum()} out of {len(df_master)} rows in master file")
print("\nSample of master file with new key column:")
print(df_master[['ID', 'ShortTitle', 'key']].head(10))

# Check for unmatched IDs
unmatched = df_master[df_master['key'].isna()]
if len(unmatched) > 0:
    print(f"\n⚠️ Warning: {len(unmatched)} rows in master file have no matching key:")
    print(unmatched[['ID', 'ShortTitle']])

# Save the updated master file
output_file = r'c:\Users\LucasSempe\OneDrive - International Initiative for Impact Evaluation\Desktop\Gen AI tools\8w-sr\OM_QEX\Master file of included studies (n=95) 10 Nov(data)_with_key.csv'
df_master.to_csv(output_file, index=False)
print(f"\n✅ Updated file saved to: {output_file}")
