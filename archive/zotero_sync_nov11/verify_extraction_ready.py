import pandas as pd

# Load both files
master = pd.read_csv('data/raw/Master file of included studies (n=114) 11 Nov(data).csv')
fulltext = pd.read_csv('data/raw/fulltext_metadata.csv')

print("="*70)
print("MASTER FILE STATUS - November 11, 2025")
print("="*70)

print(f"\nTotal studies in Master: {len(master)}")
print(f"Studies with metadata: {master['ShortTitle'].notna().sum()}")
print(f"Studies with NaN metadata: {master['ShortTitle'].isna().sum()}")

print("\n" + "="*70)
print("FULLTEXT METADATA STATUS")
print("="*70)

print(f"\nTotal entries: {len(fulltext)}")
print(f"Unique paper_ids: {fulltext['paper_id'].nunique()}")

print("\n" + "="*70)
print("EXTRACTION READINESS")
print("="*70)

# Check coverage
master_ids = set(master['ID'].astype(str))
fulltext_ids = set(fulltext['paper_id'].astype(str))

has_grobid = master_ids & fulltext_ids
missing_grobid = master_ids - fulltext_ids

print(f"\nStudies with GROBID outputs: {len(has_grobid)}")
print(f"Studies missing GROBID: {len(missing_grobid)}")

print("\n" + "="*70)
print("FINAL VERDICT")
print("="*70)

if len(has_grobid) == len(master):
    print("\n✅ YES! All 114 studies have GROBID outputs!")
    print("\n🎉 PROJECT READY FOR FULL EXTRACTION!")
    print("\nYou can now run:")
    print("  cd om_qex_extraction")
    print("  python run_twostage_extraction.py --all")
else:
    print(f"\n❌ No. Only {len(has_grobid)}/{len(master)} studies ready")
    print(f"\nStill missing: {len(missing_grobid)} studies")
    
    if missing_grobid:
        print("\nMissing study IDs:")
        for study_id in sorted(list(missing_grobid))[:20]:
            title = master[master['ID'].astype(str) == study_id]['ShortTitle'].values
            title_str = title[0] if len(title) > 0 and pd.notna(title[0]) else "NaN"
            print(f"  {study_id}: {title_str}")

# Additional verification - check TEI files exist
print("\n" + "="*70)
print("FILE VERIFICATION")
print("="*70)

import os
from pathlib import Path

tei_dir = Path("data/grobid_outputs/tei")
txt_dir = Path("data/grobid_outputs/text")

if tei_dir.exists():
    tei_count = len(list(tei_dir.glob("*.xml")))
    print(f"\nTEI XML files in data/grobid_outputs/tei/: {tei_count}")
else:
    tei_count = 0
    print(f"\n⚠ TEI directory not found")

if txt_dir.exists():
    txt_count = len(list(txt_dir.glob("*.txt")))
    print(f"TXT files in data/grobid_outputs/text/: {txt_count}")
else:
    txt_count = 0
    print(f"⚠ TXT directory not found")

print(f"\n{'✅' if tei_count >= 114 else '⚠'} Expected: 114 TEI files, Found: {tei_count}")
print(f"{'✅' if txt_count >= 114 else '⚠'} Expected: 114 TXT files, Found: {txt_count}")
