import pandas as pd
pd.set_option('display.max_colwidth', 80)
pd.set_option('display.width', 150)

# Load human extraction
human = pd.read_csv('data/human_extraction/8 week SR QEX Pierre SOF and TEEP(Quant Extraction Form).csv', skiprows=2)

# Filter for study 121294984 (PHRKN65M)
study = human[human['StudyID'] == '121294984'].copy()

print("="*100)
print("HUMAN EXTRACTION (Pierre) - Study 121294984 (PHRKN65M)")
print("="*100)
print(f"Number of outcomes: {len(study)}\n")

# Show outcome names
for i, (idx, row) in enumerate(study.iterrows(), 1):
    outcome = row['Outcome name']
    print(f"{i}. {outcome}")

# Load two-stage QEX results
twostage = pd.read_csv('om_qex_extraction/outputs/twostage/stage2_qex/extracted_data.csv')

print("\n" + "="*100)
print("TWO-STAGE QEX EXTRACTION - PHRKN65M")
print("="*100)
print(f"Number of outcomes: {len(twostage)}\n")

# Show outcomes with their text_position
for i, (idx, row) in enumerate(twostage.iterrows(), 1):
    outcome = row['outcome_name']
    position = row.get('text_position', 'N/A')
    literal = str(row.get('literal_text', 'N/A'))[:100]
    print(f"{i}. {outcome}")
    print(f"   Location: {position}")
    print(f"   Text: {literal}...")
    print()

# Simple name matching
print("="*100)
print("COMPARISON")
print("="*100)
print(f"Human extracted:     {len(study)} outcomes")
print(f"Two-stage extracted: {len(twostage)} outcomes")
print(f"Difference:          {len(twostage) - len(study):+d} outcomes")

# Check if any names match (fuzzy)
print("\nLooking for potential matches...")
for h_name in study['Outcome name'].tolist():
    h_lower = h_name.lower()
    for t_name in twostage['outcome_name'].tolist():
        t_lower = t_name.lower()
        # Check if any words overlap
        h_words = set(h_lower.split())
        t_words = set(t_lower.split())
        overlap = h_words & t_words
        if len(overlap) > 1:  # At least 2 words match
            print(f"  HUMAN: '{h_name}' ≈ LLM: '{t_name}' (overlap: {overlap})")
