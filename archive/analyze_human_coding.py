import pandas as pd
import numpy as np
import sys

# Read the human extraction CSV
csv_path = r"c:\Users\LucasSempe\OneDrive - International Initiative for Impact Evaluation\Desktop\Gen AI tools\8w-sr\OM_QEX\data\human_extraction\8 week SR QEX Pierre SOF and TEEP(Quant Extraction Form).csv"
df = pd.read_csv(csv_path, skiprows=3)

print("=" * 80)
print("HUMAN EXTRACTION CODING PATTERN ANALYSIS")
print("=" * 80)

print(f"\nTotal rows: {len(df)}")
print(f"Total columns: {len(df.columns)}")

# Function to analyze a column
def analyze_column(df, col_idx, col_name):
    print(f"\n{'='*80}")
    print(f"{col_name} (Column {col_idx})")
    print(f"{'='*80}")
    
    col_data = df.iloc[:, col_idx]
    
    # Count patterns
    total = len(col_data)
    non_empty = col_data.notna().sum()
    empty = col_data.isna().sum()
    
    print(f"Non-empty: {non_empty}/{total} ({non_empty/total*100:.1f}%)")
    print(f"Empty (NaN): {empty}/{total} ({empty/total*100:.1f}%)")
    
    # Check for special values
    if col_data.dtype == 'object':
        # String patterns
        unique_vals = col_data.dropna().unique()
        print(f"\nUnique values: {len(unique_vals)}")
        
        # Look for special codes
        special_codes = ['unclear', 'Unclear', 'UNCLEAR', 'NA', 'N/A', 'n/a', 
                        'not reported', 'Not reported', 'NR', 'nr', '?', 
                        'unknown', 'Unknown', '-', '']
        
        found_codes = []
        for code in special_codes:
            if code in unique_vals:
                count = (col_data == code).sum()
                found_codes.append(f"{code} ({count})")
        
        if found_codes:
            print(f"Special codes found: {', '.join(found_codes)}")
        else:
            print("No standard special codes found (unclear, NA, etc.)")
        
        # Show value distribution if not too many
        if len(unique_vals) <= 20:
            print("\nValue distribution:")
            print(col_data.value_counts(dropna=False))
        else:
            print(f"\nTop 10 most common values:")
            print(col_data.value_counts(dropna=False).head(10))
            
        # Show sample values
        if len(unique_vals) > 0:
            print("\nSample values:")
            for val in unique_vals[:5]:
                val_str = str(val)
                if len(val_str) > 100:
                    print(f"  - {val_str[:100]}...")
                else:
                    print(f"  - {val_str}")
    else:
        # Numeric patterns
        print("\nValue distribution:")
        print(col_data.value_counts(dropna=False))

# Analyze key columns
print("\n" + "="*80)
print("ANALYZING KEY FIELDS")
print("="*80)

# Bibliographic fields
analyze_column(df, 4, "AUTHOR NAME")
analyze_column(df, 5, "YEAR OF PUBLICATION")
analyze_column(df, 6, "PUBLICATION TYPE")

# Intervention fields
analyze_column(df, 7, "PROGRAM NAME")
analyze_column(df, 9, "COUNTRY")
analyze_column(df, 10, "YEAR INTERVENTION STARTED")

# Graduation components (0/1 coded)
analyze_column(df, 13, "CONSUMPTION SUPPORT")
analyze_column(df, 14, "HEALTHCARE")
analyze_column(df, 15, "ASSETS")
analyze_column(df, 16, "SKILLS TRAINING")
analyze_column(df, 17, "SAVINGS")
analyze_column(df, 18, "COACHING")
analyze_column(df, 19, "SOCIAL EMPOWERMENT")

# Method fields
analyze_column(df, 20, "EVALUATION DESIGN")
analyze_column(df, 21, "EVALUATION METHOD")

# Outcome fields
analyze_column(df, 22, "OUTCOME NAME")
analyze_column(df, 23, "OUTCOME DESCRIPTION")

# Numeric fields
analyze_column(df, 57, "N TREATMENT")
analyze_column(df, 58, "N CONTROL")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
