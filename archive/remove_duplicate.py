import pandas as pd

# Read the current 96-study file
df = pd.read_csv('data/raw/Master file of included studies (n=96) 10 Nov(data).csv')

print("=" * 80)
print("REMOVING DUPLICATE STUDY")
print("=" * 80)
print(f"Before: {len(df)} studies")

# Get the study to remove
removed_study = df[df['ID'] == 121475488].iloc[0]
print(f"\nRemoving:")
print(f"  ID: {removed_study['ID']}")
print(f"  ShortTitle: {removed_study['ShortTitle']}")
print(f"  Year: {removed_study['Year']}")
print(f"  Country: {removed_study['Country']}")
print(f"  Reason: Duplicate - shares Key NMQBK8CD with study 121306716 (Selim 2020)")

# Remove the duplicate
df_cleaned = df[df['ID'] != 121475488].copy()

print(f"\nAfter: {len(df_cleaned)} studies")

# Save the cleaned file
output_file = 'data/raw/Master file of included studies (n=95) 10 Nov(data).csv'
df_cleaned.to_csv(output_file, index=False)

print(f"\n✅ Saved cleaned file as: {output_file}")
print("=" * 80)
