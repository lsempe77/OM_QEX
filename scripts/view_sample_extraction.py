"""
View sample extraction data to understand core fields.
"""

import pandas as pd
from pathlib import Path

# Read with multi-level headers
csv_path = Path("data/human_extraction/8 week SR QEX Pierre SOF and TEEP(Quant Extraction Form).csv")
df = pd.read_csv(csv_path, header=[0, 1, 2])  # 3 header rows

# Get first data row (row 4 in file = index 0 after 3 header rows)
first_row = df.iloc[0]

# Show non-null fields
print("=" * 80)
print("SAMPLE EXTRACTION - First Paper (Maldonado 2019)")
print("=" * 80)

print("\n📋 PUBLICATION INFO:")
print(f"  Study ID: {first_row.get(('Publication info', 'Use OM'), 'N/A')}")
print(f"  Author: {first_row.get(('Unnamed: 4_level_0', 'Use OM'), 'N/A')}")
print(f"  Year: {first_row.get(('Unnamed: 5_level_0', 'Maldonado et al.'), 'N/A')}")

print("\n🌍 INTERVENTION INFO:")
print(f"  Program: {first_row.get(('Intervention info', 'Use OM (\"Program name\")'), 'N/A')}")
print(f"  Country: {first_row.get(('Unnamed: 9_level_0', 'Use OM'), 'N/A')}")

print("\n📊 OUTCOME INFO:")
outcome_cols = [col for col in df.columns if 'Outcome' in col[0]]
for col in outcome_cols[:5]:
    val = first_row.get(col, 'N/A')
    if pd.notna(val) and val != '':
        print(f"  {col[1]}: {val}")

print("\n📈 ESTIMATE DATA (Statistical):")
estimate_cols = [col for col in df.columns if 'Estimate data' in col[0]]
count = 0
for col in estimate_cols:
    val = first_row.get(col, 'N/A')
    if pd.notna(val) and val != '' and str(val) != 'nan':
        print(f"  {col[1]}: {val}")
        count += 1
        if count >= 10:  # Show first 10
            print(f"  ... ({len(estimate_cols) - count} more fields)")
            break

print("\n" + "=" * 80)
print("CORE FIELDS ANALYSIS")
print("=" * 80)

# Count non-null values per category
categories = {}
for col in df.columns:
    category = col[0]
    if category not in categories:
        categories[category] = {'total': 0, 'filled': 0}
    categories[category]['total'] += 1
    if pd.notna(first_row.get(col)) and str(first_row.get(col)) != '' and str(first_row.get(col)) != 'nan':
        categories[category]['filled'] += 1

print("\nData completeness by category:")
for cat, stats in categories.items():
    if cat and 'Unnamed' not in cat:
        pct = (stats['filled'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"  {cat}: {stats['filled']}/{stats['total']} fields ({pct:.0f}%)")
