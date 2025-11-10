import pandas as pd

human = pd.read_csv('data/human_extraction/8 week SR QEX Pierre SOF and TEEP(Quant Extraction Form).csv', skiprows=2)
cols = human.columns.tolist()

print(f'Total columns: {len(cols)}')
print('\nAll column names:')
for i, col in enumerate(cols, 1):
    if i > 50:  # Limit output
        print(f'... and {len(cols) - 50} more columns')
        break
    print(f'{i}. {col}')

# Find outcome-related columns
print('\n' + '='*80)
print('Looking for outcome-related columns:')
outcome_cols = [col for col in cols if 'outcome' in col.lower() or 'name' in col.lower()]
for col in outcome_cols:
    print(f'  - {col}')
