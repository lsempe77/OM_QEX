import pandas as pd
import re

# Load improved OM results
om = pd.read_csv('om_qex_extraction/outputs/om_extractions/extracted_data.csv')

# Extract table numbers
def get_table_num(location_str):
    match = re.search(r'[Tt]able\s+(\d+)', str(location_str))
    return int(match.group(1)) if match else None

om['table'] = om['location'].apply(get_table_num)

print("="*100)
print("IMPROVED OM EXTRACTION - PHRKN65M")
print("="*100)
print(f"Total outcomes found: {len(om)}")

tables = sorted([t for t in om['table'].dropna().unique()])
print(f"Tables extracted from: {tables}")

print("\n" + "="*100)
print("OUTCOMES BY TABLE")
print("="*100)

for table_num in tables:
    outcomes = om[om['table'] == table_num]['outcome_category'].tolist()
    print(f"\nTable {int(table_num)}:")
    for outcome in outcomes:
        print(f"  - {outcome}")

# Compare to human extraction  
print("\n" + "="*100)
print("COMPARISON TO HUMAN EXTRACTION")
print("="*100)

human_tables = [6, 8, 11, 13, 15, 16, 17]  # From earlier analysis
om_tables = [int(t) for t in tables]

print(f"\nHuman extracted from tables: {human_tables}")
print(f"Improved OM found tables:    {om_tables}")

overlap = set(human_tables) & set(om_tables)
still_missing = set(human_tables) - set(om_tables)
extra = set(om_tables) - set(human_tables)

print(f"\nBoth found:       {sorted(overlap)}")
print(f"Still missing:    {sorted(still_missing)}")
print(f"OM found extra:   {sorted(extra)}")

if still_missing:
    print("\n⚠️ STILL MISSING TABLES:")
    missing_mapping = {
        13: "Per capita value of harvest (MWK)",
        15: "Per capita food consumption (MWK), Diet diversity score",
        16: "Per capita non-food expenditure (MWK)",
        17: "Per capita total consumption (MWK), Poverty (yes/no)"
    }
    for t in sorted(still_missing):
        print(f"  Table {t}: {missing_mapping.get(t, 'Unknown')}")
else:
    print("\n✅ All human tables found!")

print(f"\nRecall: {len(overlap)}/{len(human_tables)} = {len(overlap)/len(human_tables)*100:.1f}%")
