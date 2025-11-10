import re

with open('data/grobid_outputs/text/PHRKN65M.txt', encoding='utf-8') as f:
    txt = f.read()

# Find all table mentions
tables = re.findall(r'Table\s+(\d+)[:\s-]+(.*?)(?:\n|$)', txt)

print(f"Total table mentions: {len(tables)}")
print("\n" + "="*100)
print("ALL TABLES IN PAPER")
print("="*100)

# Get unique tables
seen = set()
for num, title in tables:
    if num not in seen:
        seen.add(num)
        print(f"Table {num}: {title[:90]}")
        
print("\n" + "="*100)
print(f"\nUnique tables found: {sorted([int(x) for x in seen])}")

# Check for Tables 13-17 specifically
print("\n" + "="*100)
print("CHECKING MISSED TABLES (13-17)")
print("="*100)
for target in [13, 15, 16, 17]:
    matches = [title for num, title in tables if num == str(target)]
    if matches:
        print(f"\nTable {target}: {matches[0][:90]}")
    else:
        print(f"\nTable {target}: NOT FOUND in text")
