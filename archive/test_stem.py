from pathlib import Path

tei_dir = Path('data/grobid_outputs/tei')
files = list(tei_dir.glob('*.tei.xml'))

print("Checking Path.stem behavior:")
print("=" * 60)

for f in files[:3]:
    print(f"\nFilename: {f.name}")
    print(f"Stem: {f.stem}")
    print(f"Suffixes: {f.suffixes}")

# Check if our keys would match
test_keys = ['PHRKN65M', 'ABM3E3ZP']
print("\n" + "=" * 60)
print("Testing key matching:")
print("=" * 60)

for key in test_keys:
    matching = [f for f in files if f.stem == key]
    print(f"\nKey '{key}': {len(matching)} matches")
    if matching:
        print(f"  Found: {matching[0].name}")
