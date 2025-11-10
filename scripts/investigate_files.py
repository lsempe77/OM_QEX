import pandas as pd

# Check both CSV files
grad_file = r'C:\Users\LucasSempe\OneDrive - International Initiative for Impact Evaluation\Desktop\Gen AI tools\8w-sr\paper-screening-pipeline\data\input\fulltext\Grad approaches FTR & grey lit.csv'
master_file = r'c:\Users\LucasSempe\OneDrive - International Initiative for Impact Evaluation\Desktop\Gen AI tools\8w-sr\OM_QEX\Master file of included studies (n=95) 10 Nov(data)_with_key.csv'

# Read files
df_grad = pd.read_csv(grad_file)
df_master = pd.read_csv(master_file)

print("Grad file (in fulltext folder):")
print(f"  Rows: {len(df_grad)}")
print(f"  Sample keys: {df_grad['Key'].head(10).tolist()}")

print("\nMaster file (with added keys):")
df_master_with_key = df_master[df_master['key'].notna()]
print(f"  Rows with keys: {len(df_master_with_key)}")
print(f"  Sample keys: {df_master_with_key['key'].head(10).tolist()}")

# Check if grad file has file attachments
if 'File Attachments' in df_grad.columns:
    has_files = df_grad['File Attachments'].notna().sum()
    print(f"\nGrad file has {has_files} rows with File Attachments")
    sample = df_grad[df_grad['File Attachments'].notna()]['File Attachments'].head(3)
    print("Sample file paths:")
    for path in sample:
        print(f"  {path}")
