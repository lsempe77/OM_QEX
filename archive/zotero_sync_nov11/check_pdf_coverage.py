import pandas as pd

# Load both files
master = pd.read_csv('data/raw/Master file of included studies (n=114) 11 Nov(data).csv')
fulltext = pd.read_csv('data/raw/fulltext_metadata.csv')

print("="*70)
print("PDF STATUS FOR 114 STUDIES")
print("="*70)

total_studies = len(master)
print(f"\nTotal studies in Master file: {total_studies}")

# Studies with GROBID fulltext
has_grobid = set(master['ID']) & set(fulltext['paper_id'])
print(f"Studies with GROBID fulltext (TEI/TXT): {len(has_grobid)}")

# Studies WITHOUT GROBID fulltext
missing_grobid = set(master['ID']) - set(fulltext['paper_id'])
print(f"Studies WITHOUT GROBID fulltext: {len(missing_grobid)}")

print("\n" + "="*70)
print("EXPECTED PDF SOURCES")
print("="*70)

print(f"\n✓ {len(has_grobid)} studies have PDFs already processed by GROBID")
print(f"  Location: data/grobid_outputs/tei/ and data/grobid_outputs/text/")

print(f"\n? {len(missing_grobid)} studies need PDFs from Zotero")
print(f"  These should be downloaded from Zotero library")

# Check which missing ones have metadata
missing_studies = master[master['ID'].isin(missing_grobid)].copy()
has_metadata = missing_studies['ShortTitle'].notna().sum()
no_metadata = missing_studies['ShortTitle'].isna().sum()

print(f"\n  Of the {len(missing_grobid)} missing:")
print(f"    - {no_metadata} are placeholder entries (all NaN)")
print(f"    - {has_metadata} have study metadata")

if has_metadata > 0:
    print(f"\n  Studies with metadata that need Zotero PDFs:")
    complete = missing_studies[missing_studies['ShortTitle'].notna()][['ID', 'ShortTitle', 'Year', 'Country']]
    for _, row in complete.iterrows():
        print(f"    {row['ID']}: {row['ShortTitle']} ({row['Year']}, {row['Country']})")

print("\n" + "="*70)
print("MATH CHECK")
print("="*70)
print(f"{len(has_grobid)} (GROBID) + {len(missing_grobid)} (Zotero) = {len(has_grobid) + len(missing_grobid)} total")

if len(has_grobid) + len(missing_grobid) == total_studies:
    print("✓ Math checks out! All 114 studies accounted for.")
else:
    print("✗ Warning: Numbers don't add up!")

print("\n" + "="*70)
print("NEXT STEPS")
print("="*70)
print("1. Check Zotero library for the missing studies")
print("2. Download PDFs from Zotero using sync scripts")
print("3. Process new PDFs through GROBID")
print("4. Update fulltext_metadata.csv with new entries")
print("5. Then you'll have all 114 studies ready for extraction")
