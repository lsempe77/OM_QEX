import pandas as pd

master = pd.read_csv('data/raw/Master file of included studies (n=114) 11 Nov(data).csv')
fulltext = pd.read_csv('data/raw/fulltext_metadata.csv')
downloaded = pd.read_csv('missing_studies_zotero_mapping_20251111_102647.csv')

print("="*70)
print("RECONCILING THE COUNTS")
print("="*70)

# Convert to strings for comparison
master['ID_str'] = master['ID'].astype(str)
fulltext['paper_id_str'] = fulltext['paper_id'].astype(str)
downloaded['study_id_str'] = downloaded['study_id'].astype(str)

# Missing from GROBID
missing_from_grobid = set(master['ID_str']) - set(fulltext['paper_id_str'])
print(f"\nStudies missing from GROBID: {len(missing_from_grobid)}")

# NaN entries (no metadata)
nan_entries = set(master[master['ShortTitle'].isna()]['ID_str'])
print(f"Studies with NaN metadata: {len(nan_entries)}")

# Downloaded
downloaded_ids = set(downloaded['study_id_str'])
print(f"PDFs downloaded from Zotero: {len(downloaded_ids)}")

print("\n" + "="*70)
print("OVERLAP ANALYSIS")
print("="*70)

# Are all NaN entries in downloaded?
nan_in_downloaded = nan_entries & downloaded_ids
print(f"\nNaN entries that were downloaded: {len(nan_in_downloaded)}")

# Are all downloaded in missing_from_grobid?
downloaded_in_missing = downloaded_ids & missing_from_grobid
print(f"Downloaded PDFs that were missing from GROBID: {len(downloaded_in_missing)}")

# Any downloaded that ALREADY had GROBID?
has_grobid = set(master['ID_str']) & set(fulltext['paper_id_str'])
downloaded_has_grobid = downloaded_ids & has_grobid
print(f"Downloaded PDFs that ALREADY have GROBID: {len(downloaded_has_grobid)}")

if downloaded_has_grobid:
    print("\nThese were unnecessary downloads (already have GROBID):")
    for study_id in sorted(downloaded_has_grobid):
        title = master[master['ID_str'] == study_id]['ShortTitle'].values[0]
        key = fulltext[fulltext['paper_id_str'] == study_id]['Key'].values[0]
        print(f"  {study_id}: {title} (Key: {key})")

print("\n" + "="*70)
print("FINAL STATUS")
print("="*70)

truly_missing = downloaded_ids - has_grobid
print(f"\nStudies that TRULY needed PDFs from Zotero: {len(truly_missing)}")
print(f"Studies that already had GROBID: {len(downloaded_has_grobid)}")
print(f"\nMath check:")
print(f"  {len(has_grobid)} (existing GROBID)")
print(f"+ {len(truly_missing)} (new from Zotero)")
print(f"= {len(has_grobid) + len(truly_missing)} total studies")
print(f"  Master file has: {len(master)} studies")

if len(has_grobid) + len(truly_missing) == len(master):
    print("\n✓ Perfect! All 114 studies accounted for!")
else:
    diff = len(master) - (len(has_grobid) + len(truly_missing))
    print(f"\n⚠ Gap of {diff} studies")
