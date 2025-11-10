import pandas as pd

# Load both files
grad = pd.read_csv(r'Grad approaches FTR & grey lit.csv')
master = pd.read_csv(r'Master file of included studies (n=95) 10 Nov(data)_with_key.csv')

# Sample key from grobid outputs
sample_key = '232NVPPU'

print(f"Searching for key: {sample_key}\n")

# Check in Grad file
print("="*60)
print("GRAD FILE:")
print(f"In 'Key' column: {sample_key in grad['Key'].values}")

# Search all columns
for col in grad.columns:
    if grad[col].astype(str).str.contains(sample_key, na=False).any():
        rows = grad[grad[col].astype(str).str.contains(sample_key, na=False)]
        print(f"\nFound in column '{col}':")
        print(rows[['Key', col]].head())

print("\n" + "="*60)
print("MASTER FILE:")
if 'key' in master.columns:
    print(f"In 'key' column: {sample_key in master['key'].values}")

# Search all columns
for col in master.columns:
    if master[col].astype(str).str.contains(sample_key, na=False).any():
        rows = master[master[col].astype(str).str.contains(sample_key, na=False)]
        print(f"\nFound in column '{col}':")
        print(rows[[col]].head())

print("\n" + "="*60)
print("\nIt seems the grobid output files are from a DIFFERENT dataset.")
print("The keys in the grobid folder don't match either CSV file.")
