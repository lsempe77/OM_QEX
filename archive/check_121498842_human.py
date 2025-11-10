import pandas as pd

# Read human extraction
df = pd.read_csv('data/human_extraction/8 week SR QEX Pierre SOF and TEEP(Quant Extraction Form).csv', skiprows=3)

# Find study 121498842
study = df[df.iloc[:, 2] == 121498842]

print("=" * 80)
print("STUDY 121498842 IN HUMAN EXTRACTION")
print("=" * 80)

if len(study) > 0:
    print(f"\nRows with this study ID: {len(study)}")
    print(f"\nFirst occurrence:")
    print(f"  StudyID: {study.iloc[0, 2]}")
    print(f"  Author: {study.iloc[0, 4]}")
    print(f"  Year: {study.iloc[0, 5]}")
    print(f"  Country: {study.iloc[0, 9]}")
    print(f"  Program: {study.iloc[0, 7]}")
    
    print("\n" + "=" * 80)
    print("ANALYSIS:")
    print("=" * 80)
    print("This study is in the human extraction CSV but:")
    print("  ❌ NOT in the master file")
    print("  ❌ NOT in fulltext_metadata.csv")
    print("  ❌ Therefore NO GROBID files")
    print("\nConclusion: Cannot extract with LLM - no TEI/TXT files available")
else:
    print("\nNot found in human extraction")
