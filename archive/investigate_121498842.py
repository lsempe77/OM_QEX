import pandas as pd

# Check if 121498842 is in metadata
meta = pd.read_csv('data/raw/fulltext_metadata.csv')
study = meta[meta['paper_id'] == 121498842]

print("=" * 80)
print("INVESTIGATING STUDY 121498842")
print("=" * 80)

if len(study) > 0:
    print("\n✅ FOUND in fulltext_metadata.csv:")
    print(f"  Key: {study.iloc[0]['Key']}")
    print(f"  Title: {study.iloc[0]['Title']}")
    print(f"  Author: {study.iloc[0]['Author']}")
    print(f"  Year: {study.iloc[0]['Publication Year']}")
else:
    print("\n❌ NOT FOUND in fulltext_metadata.csv")
    print("\nChecking if it's in the old master file...")
    
    # Check in old master file
    try:
        old_master = pd.read_csv('data/raw/Master file of included studies (n=95) 10 Nov(data)_with_key.csv')
        old_study = old_master[old_master['ID'] == 121498842]
        
        if len(old_study) > 0:
            print("\n✅ FOUND in old master file:")
            print(f"  ID: {old_study.iloc[0]['ID']}")
            print(f"  ShortTitle: {old_study.iloc[0]['ShortTitle']}")
            print(f"  Year: {old_study.iloc[0]['Year']}")
            if 'Key' in old_study.columns:
                print(f"  Key: {old_study.iloc[0]['Key']}")
        else:
            print("❌ NOT in old master file either")
    except:
        print("Could not check old master file")

    # Check current master
    print("\nChecking current master file...")
    current_master = pd.read_csv('data/raw/Master file of included studies (n=95) 10 Nov(data).csv')
    current_study = current_master[current_master['ID'] == 121498842]
    
    if len(current_study) > 0:
        print("\n✅ FOUND in current master file:")
        print(f"  ID: {current_study.iloc[0]['ID']}")
        print(f"  ShortTitle: {current_study.iloc[0]['ShortTitle']}")
        print(f"  Year: {current_study.iloc[0]['Year']}")
        print(f"  Country: {current_study.iloc[0]['Country']}")
    else:
        print("❌ NOT in current master file")

print("\n" + "=" * 80)
