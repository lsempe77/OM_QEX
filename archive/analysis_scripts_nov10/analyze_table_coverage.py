import pandas as pd
import re

# Load human extraction
human = pd.read_csv('data/human_extraction/8 week SR QEX Pierre SOF and TEEP(Quant Extraction Form).csv', skiprows=2)
study = human[human['StudyID'] == '121294984'].copy()

# Extract table numbers from human source
study['table_num'] = study['Source'].apply(lambda x: int(re.search(r'table:\s*(\d+)', x).group(1)) if re.search(r'table:\s*(\d+)', x) else None)

# Load LLM extraction
llm = pd.read_csv('om_qex_extraction/outputs/twostage/stage2_qex/extracted_data.csv')

# Extract table numbers from LLM text_position
def extract_table_from_position(pos):
    if pd.isna(pos):
        return None
    match = re.search(r'Table\s+(\d+)', str(pos))
    return int(match.group(1)) if match else None

llm['table_num'] = llm['text_position'].apply(extract_table_from_position)

print("="*100)
print("TABLE COVERAGE ANALYSIS - PHRKN65M")
print("="*100)

human_tables = sorted(study['table_num'].dropna().unique())
llm_tables = sorted(llm['table_num'].dropna().unique())

print(f"\nHuman extracted from tables: {human_tables}")
print(f"LLM extracted from tables:   {llm_tables}")

overlap = set(human_tables) & set(llm_tables)
human_only = set(human_tables) - set(llm_tables)
llm_only = set(llm_tables) - set(human_tables)

print(f"\nBoth extracted:      {sorted(overlap)}")
print(f"Human only:          {sorted(human_only)}")
print(f"LLM only:            {sorted(llm_only)}")

print("\n" + "="*100)
print("HUMAN OUTCOMES BY TABLE")
print("="*100)
for table in human_tables:
    outcomes = study[study['table_num'] == table]['Outcome name'].tolist()
    print(f"\nTable {table}:")
    for outcome in outcomes:
        print(f"  - {outcome}")

print("\n" + "="*100)
print("LLM OUTCOMES BY TABLE")
print("="*100)
for table in llm_tables:
    outcomes = llm[llm['table_num'] == table]['outcome_name'].tolist()
    print(f"\nTable {table}:")
    for outcome in outcomes:
        print(f"  - {outcome}")

print("\n" + "="*100)
print("MISSING TABLES (Human extracted, LLM missed)")
print("="*100)
for table in sorted(human_only):
    outcomes = study[study['table_num'] == table]['Outcome name'].tolist()
    print(f"\nTable {table} (MISSED BY LLM):")
    for outcome in outcomes:
        print(f"  - {outcome}")
