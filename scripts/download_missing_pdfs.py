"""
Download the 19 missing PDFs from Zotero

This script uses the mapping file to download PDFs for the 19 studies
that are missing from GROBID outputs.
"""

import requests
import pandas as pd
import os
import time
from datetime import datetime

# Configuration
ZOTERO_API_KEY = "BsaFwjyC5aKwZV7hyR77nzYV"
ZOTERO_GROUP_ID = "6248442"
ZOTERO_LIBRARY_TYPE = "groups"

# Output directory - match your existing structure
PDF_OUTPUT_DIR = "data/pdfs_from_zotero"

def log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def download_pdf(attachment_key, save_path, item_title):
    """Download PDF from Zotero"""
    url = f"https://api.zotero.org/{ZOTERO_LIBRARY_TYPE}/{ZOTERO_GROUP_ID}/items/{attachment_key}/file"
    headers = {"Zotero-API-Key": ZOTERO_API_KEY}
    
    try:
        log(f"  Downloading: {item_title[:60]}")
        response = requests.get(url, headers=headers, timeout=120, stream=True)
        
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size = os.path.getsize(save_path) / 1024  # KB
            log(f"  ✓ Downloaded ({file_size:.1f} KB)")
            return True, f"Success ({file_size:.1f} KB)"
        else:
            log(f"  ✗ HTTP {response.status_code}")
            return False, f"HTTP {response.status_code}"
            
    except Exception as e:
        log(f"  ✗ Error: {e}")
        return False, str(e)

def get_pdf_attachment_key(item_key):
    """Get PDF attachment key for a Zotero item"""
    url = f"https://api.zotero.org/{ZOTERO_LIBRARY_TYPE}/{ZOTERO_GROUP_ID}/items/{item_key}/children"
    headers = {"Zotero-API-Key": ZOTERO_API_KEY}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            children = response.json()
            
            for child in children:
                if (child['data'].get('itemType') == 'attachment' and
                    'pdf' in child['data'].get('contentType', '').lower()):
                    return child['key'], child['data'].get('filename', 'document.pdf')
                    
        return None, None
        
    except Exception as e:
        log(f"  Error getting attachment: {e}")
        return None, None

def main():
    log("="*70)
    log("DOWNLOAD 19 MISSING PDFs FROM ZOTERO")
    log("="*70)
    
    # Create output directory
    os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)
    log(f"\nOutput directory: {PDF_OUTPUT_DIR}")
    
    # Load mapping file
    mapping_file = "missing_studies_zotero_mapping_20251111_102647.csv"
    
    if not os.path.exists(mapping_file):
        log(f"\n✗ ERROR: Mapping file not found: {mapping_file}")
        log("Run find_missing_in_zotero.py first!")
        return
    
    df = pd.read_csv(mapping_file)
    log(f"\nLoaded mapping file: {len(df)} studies")
    
    # Filter to items with PDFs
    df_with_pdf = df[df['has_pdf'] == 'Yes'].copy()
    log(f"Studies with PDFs in Zotero: {len(df_with_pdf)}")
    
    # Download PDFs
    log("\n" + "="*70)
    log("DOWNLOADING PDFs")
    log("="*70)
    
    results = []
    downloaded = 0
    failed = 0
    skipped = 0
    
    for idx, row in df_with_pdf.iterrows():
        study_id = row['study_id']
        zotero_key = row['zotero_key']
        title = row['title']
        pdf_attachment_key = row.get('pdf_attachment_key', '')
        
        log(f"\n[{idx+1}/{len(df_with_pdf)}] Study ID: {study_id}")
        
        # Create filename: {study_id}_{zotero_key}.pdf
        filename = f"{study_id}_{zotero_key}.pdf"
        filepath = os.path.join(PDF_OUTPUT_DIR, filename)
        
        # Check if already downloaded
        if os.path.exists(filepath):
            log(f"  ⊙ Already exists: {filename}")
            skipped += 1
            results.append({
                'study_id': study_id,
                'zotero_key': zotero_key,
                'filename': filename,
                'status': 'Already existed',
                'size_kb': os.path.getsize(filepath) / 1024
            })
            time.sleep(0.2)
            continue
        
        # Get PDF attachment key if not in mapping
        if not pdf_attachment_key or pd.isna(pdf_attachment_key):
            pdf_attachment_key, original_filename = get_pdf_attachment_key(zotero_key)
            time.sleep(0.3)
            
            if not pdf_attachment_key:
                log(f"  ✗ No PDF attachment found")
                failed += 1
                results.append({
                    'study_id': study_id,
                    'zotero_key': zotero_key,
                    'filename': filename,
                    'status': 'No PDF attachment',
                    'size_kb': 0
                })
                continue
        
        # Download
        success, message = download_pdf(pdf_attachment_key, filepath, title)
        
        if success:
            downloaded += 1
            results.append({
                'study_id': study_id,
                'zotero_key': zotero_key,
                'filename': filename,
                'status': 'Downloaded',
                'size_kb': os.path.getsize(filepath) / 1024
            })
        else:
            failed += 1
            results.append({
                'study_id': study_id,
                'zotero_key': zotero_key,
                'filename': filename,
                'status': f'Failed: {message}',
                'size_kb': 0
            })
        
        # Rate limiting
        time.sleep(1)
    
    # Save download log
    log("\n" + "="*70)
    log("SAVING RESULTS")
    log("="*70)
    
    df_results = pd.DataFrame(results)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"pdf_download_log_{timestamp}.csv"
    df_results.to_csv(log_file, index=False)
    log(f"✓ Download log saved: {log_file}")
    
    # Summary
    log("\n" + "="*70)
    log("DOWNLOAD COMPLETE")
    log("="*70)
    log(f"Total PDFs processed: {len(df_with_pdf)}")
    log(f"Downloaded: {downloaded}")
    log(f"Already existed: {skipped}")
    log(f"Failed: {failed}")
    log(f"\nPDFs saved to: {PDF_OUTPUT_DIR}")
    
    if downloaded > 0 or skipped > 0:
        log(f"\n✓ {downloaded + skipped} PDFs now available")
        log(f"\nNext steps:")
        log(f"1. Process these PDFs through GROBID to create TEI/TXT files")
        log(f"2. Add entries to fulltext_metadata.csv")
        log(f"3. Update Master CSV with study metadata")
        log(f"4. Then you'll have all 114 studies ready for extraction!")

if __name__ == "__main__":
    main()
