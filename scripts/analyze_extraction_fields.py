import pandas as pd

# Read with multi-level header
df = pd.read_csv('data/human_extraction/8 week SR QEX Pierre SOF and TEEP(Quant Extraction Form).csv', header=[0, 1])

print("="*80)
print("EXTRACTION FORM - MULTI-LEVEL HEADER STRUCTURE")
print("="*80)
print(f"\nRows: {len(df)}")
print(f"Columns: {len(df.columns)}")

print("\n" + "="*80)
print("FIELD CATEGORIES AND SPECIFIC FIELDS:")
print("="*80)

# Group by main category
current_category = None
for col in df.columns:
    category, field = col
    if category != current_category:
        current_category = category
        print(f"\n[{category}]")
    print(f"  - {field}")

print("\n" + "="*80)
print("SAMPLE EXTRACTED DATA (First Paper):")
print("="*80)
for col in df.columns:
    category, field = col
    value = df[col].iloc[0]
    if pd.notna(value) and str(value).strip() and str(value) not in ['Use OM', 'Extract if available / relevant']:
        print(f"\n[{category}] {field}:")
        value_str = str(value)[:150] + "..." if len(str(value)) > 150 else str(value)
        print(f"  {value_str}")
