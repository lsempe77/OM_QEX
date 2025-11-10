import os
import shutil
from pathlib import Path

project_root = Path(__file__).parent

print("Cleaning up project...\n")

# Remove empty selected_papers folder
selected_papers = project_root / 'data' / 'selected_papers'
if selected_papers.exists():
    try:
        shutil.rmtree(selected_papers)
        print(f"✓ Removed: data/selected_papers/")
    except Exception as e:
        print(f"⚠️ Could not remove selected_papers: {e}")

# Remove redundant/one-time-use scripts
scripts_to_remove = [
    'check_key_overlap.py',
    'copy_from_zotero.py',
    'copy_processed_files.py',
    'find_key_origin.py',
    'investigate_files.py',
    'organize_project.py',
    'cleanup_project.py'  # Remove itself after running
]

print("\nRemoving one-time setup scripts:")
for script in scripts_to_remove:
    script_path = project_root / 'scripts' / script
    if script_path.exists():
        os.remove(script_path)
        print(f"✓ Removed: scripts/{script}")

# Keep only essential scripts
print("\n✅ Keeping essential scripts:")
print("  - add_key_column.py (adds keys to master file)")
print("  - copy_files_by_key.py (copies GROBID outputs by ID)")

print("\n" + "="*60)
print("Cleanup complete!")
print("="*60)
