import os
import shutil
from pathlib import Path

# Define the project structure
project_root = Path(__file__).parent
print(f"Organizing project in: {project_root}\n")

# Create directory structure
directories = {
    'data': {
        'raw': 'Original CSV files and metadata',
        'processed': 'Processed and cleaned data',
        'grobid_outputs': {
            'tei': 'TEI XML files from GROBID',
            'text': 'Plain text files from GROBID'
        }
    },
    'scripts': 'Python scripts for data processing',
    'docs': 'Documentation and notes',
    'outputs': 'Analysis outputs and results'
}

def create_structure(base_path, structure, level=0):
    """Recursively create directory structure"""
    for name, desc in structure.items():
        if isinstance(desc, dict):
            # It's a subdirectory
            dir_path = base_path / name
            dir_path.mkdir(exist_ok=True)
            print(f"{'  ' * level}📁 {name}/")
            create_structure(dir_path, desc, level + 1)
        else:
            # It's a description
            dir_path = base_path / name
            dir_path.mkdir(exist_ok=True)
            print(f"{'  ' * level}📁 {name}/ - {desc}")

print("Creating directory structure:")
create_structure(project_root, directories)

# Define file movements
file_moves = {
    # Raw data files
    'data/raw': [
        'Master file of included studies (n=95) 10 Nov(data).csv',
        'Master file of included studies (n=95) 10 Nov(data)_with_key.csv',
        'Grad approaches FTR & grey lit.csv',
        'fulltext_metadata.csv'
    ],
    # Scripts
    'scripts': [
        'add_key_column.py',
        'check_key_overlap.py',
        'copy_files_by_key.py',
        'copy_from_zotero.py',
        'copy_processed_files.py',
        'find_key_origin.py',
        'organize_project.py'
    ]
}

print("\n" + "="*60)
print("Moving files to organized structure:")
print("="*60)

for dest_folder, files in file_moves.items():
    dest_path = project_root / dest_folder
    for filename in files:
        src = project_root / filename
        if src.exists():
            dest = dest_path / filename
            try:
                shutil.move(str(src), str(dest))
                print(f"✓ Moved: {filename} → {dest_folder}/")
            except Exception as e:
                print(f"⚠️ Could not move {filename}: {e}")
        else:
            print(f"⚠️ File not found: {filename}")

# Move GROBID outputs
print("\nMoving GROBID outputs...")
grobid_src = project_root / 'selected_grobid_outputs'
if grobid_src.exists():
    # Move tei folder
    tei_src = grobid_src / 'tei'
    if tei_src.exists():
        tei_dest = project_root / 'data' / 'grobid_outputs' / 'tei'
        for file in tei_src.glob('*'):
            shutil.move(str(file), str(tei_dest / file.name))
        tei_src.rmdir()
        print(f"✓ Moved TEI files to data/grobid_outputs/tei/")
    
    # Move text folder
    text_src = grobid_src / 'text'
    if text_src.exists():
        text_dest = project_root / 'data' / 'grobid_outputs' / 'text'
        for file in text_src.glob('*'):
            shutil.move(str(file), str(text_dest / file.name))
        text_src.rmdir()
        print(f"✓ Moved text files to data/grobid_outputs/text/")
    
    # Remove empty folder
    if grobid_src.exists() and not list(grobid_src.iterdir()):
        grobid_src.rmdir()
        print(f"✓ Removed empty selected_grobid_outputs folder")

# Check for selected_papers folder
selected_papers = project_root / 'selected_papers'
if selected_papers.exists():
    if list(selected_papers.iterdir()):
        print(f"\n⚠️ Note: 'selected_papers/' folder exists with content")
        print(f"   Review and manually move to appropriate location if needed")
    else:
        selected_papers.rmdir()
        print(f"✓ Removed empty selected_papers folder")

# Create README files
print("\n" + "="*60)
print("Creating documentation:")
print("="*60)

readme_content = """# OM_QEX Project

## Project Structure

```
OM_QEX/
├── data/                          # Data files
│   ├── raw/                       # Original CSV files and metadata
│   ├── processed/                 # Processed and cleaned data
│   └── grobid_outputs/           # GROBID processed PDFs
│       ├── tei/                   # TEI XML format
│       └── text/                  # Plain text format
├── scripts/                       # Python scripts
├── docs/                          # Documentation
└── outputs/                       # Analysis results
```

## Data Files

### Raw Data
- `Master file of included studies (n=95) 10 Nov(data).csv` - Original master file (95 studies)
- `Master file of included studies (n=95) 10 Nov(data)_with_key.csv` - Master file with added Key column
- `Grad approaches FTR & grey lit.csv` - Graduate approaches literature (1312 records)
- `fulltext_metadata.csv` - Metadata linking paper IDs to GROBID output keys

### GROBID Outputs
- 95 TEI XML files (structured full text)
- 95 TXT files (plain text extraction)

## Scripts

- `add_key_column.py` - Adds Key column to master file by matching EPPI-Reviewer IDs
- `copy_files_by_key.py` - Copies GROBID outputs based on master file IDs
- Additional utility scripts for data processing

## Getting Started

1. Review the data files in `data/raw/`
2. GROBID outputs are available in `data/grobid_outputs/`
3. Run analysis scripts from the `scripts/` folder
4. Save results to `outputs/`

## Notes

- The Key column links records between the Grad approaches file and GROBID outputs
- Master file IDs are linked to GROBID files via the fulltext_metadata.csv mapping
- 81 out of 95 studies have matched keys from the Grad approaches dataset
"""

readme_path = project_root / 'README.md'
with open(readme_path, 'w', encoding='utf-8') as f:
    f.write(readme_content)
print(f"✓ Created README.md")

# Create .gitignore
gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
*.egg-info/
.pytest_cache/

# Data files (optional - uncomment to exclude large data files)
# data/grobid_outputs/

# Outputs
*.log

# IDEs
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
"""

gitignore_path = project_root / '.gitignore'
with open(gitignore_path, 'w', encoding='utf-8') as f:
    f.write(gitignore_content)
print(f"✓ Created .gitignore")

# Create data README
data_readme = """# Data Directory

## Raw Data (`raw/`)
Original CSV files containing study metadata and literature references.

## Processed Data (`processed/`)
Cleaned and transformed datasets ready for analysis.

## GROBID Outputs (`grobid_outputs/`)
Full-text extractions from PDF files processed through GROBID:
- `tei/` - TEI XML format (structured with sections, references, etc.)
- `text/` - Plain text format
"""

data_readme_path = project_root / 'data' / 'README.md'
with open(data_readme_path, 'w', encoding='utf-8') as f:
    f.write(data_readme)
print(f"✓ Created data/README.md")

print("\n" + "="*60)
print("✅ Project organization complete!")
print("="*60)
print(f"\nProject root: {project_root}")
print("\nNext steps:")
print("1. Review the README.md for project overview")
print("2. Check data/raw/ for your datasets")
print("3. Use scripts/ for data processing")
print("4. Save analysis results to outputs/")
