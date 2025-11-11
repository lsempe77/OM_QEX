"""
Find Missing Studies in Zotero - Maps study IDs to Zotero items

This script:
1. Reads the 17-19 missing study IDs from Master file
2. Searches Zotero library for matching items
3. Creates a mapping CSV: study_id → zotero_key → pdf_status
4. Identifies which PDFs can be downloaded from Zotero
"""

import requests
import pandas as pd
from datetime import datetime
import time

# Configuration - UPDATE THESE!
ZOTERO_API_KEY = "BsaFwjyC5aKwZV7hyR77nzYV"  # From step_minus1_zotero_export.js
ZOTERO_GROUP_ID = "6248442"
ZOTERO_LIBRARY_TYPE = "groups"

# Zotero has a "Key" field that stores EPPI-Reviewer item IDs
# We'll search for this custom field

def log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def get_all_zotero_items():
    """Fetch all items from Zotero library"""
    log("Fetching all items from Zotero library...")
    
    base_url = f"https://api.zotero.org/{ZOTERO_LIBRARY_TYPE}/{ZOTERO_GROUP_ID}"
    headers = {"Zotero-API-Key": ZOTERO_API_KEY}
    
    all_items = []
    start = 0
    limit = 100
    
    while True:
        url = f"{base_url}/items?start={start}&limit={limit}&format=json"
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                items = response.json()
                
                if not items:
                    break
                    
                all_items.extend(items)
                start += limit
                
                log(f"  Retrieved {len(all_items)} items so far...")
                
                if len(items) < limit:
                    break
            else:
                log(f"  ERROR: HTTP {response.status_code}")
                break
                
        except Exception as e:
            log(f"  ERROR: {e}")
            break
            
        time.sleep(0.2)  # Rate limiting
    
    log(f"✓ Total items retrieved: {len(all_items)}")
    return all_items

def check_for_pdf_attachment(item_key):
    """Check if item has PDF attachment in Zotero"""
    base_url = f"https://api.zotero.org/{ZOTERO_LIBRARY_TYPE}/{ZOTERO_GROUP_ID}"
    headers = {"Zotero-API-Key": ZOTERO_API_KEY}
    url = f"{base_url}/items/{item_key}/children"
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            children = response.json()
            
            for child in children:
                if (child['data'].get('itemType') == 'attachment' and
                    'pdf' in child['data'].get('contentType', '').lower()):
                    return True, child['key']
                    
        return False, None
        
    except Exception as e:
        return False, None

def find_missing_studies():
    """Main function to map missing study IDs to Zotero items"""
    
    log("="*70)
    log("FIND MISSING STUDIES IN ZOTERO")
    log("="*70)
    
    # Load missing study IDs
    log("\nLoading missing study IDs...")
    master = pd.read_csv('data/raw/Master file of included studies (n=114) 11 Nov(data).csv')
    missing_ids = master[master['ShortTitle'].isna()]['ID'].astype(str).tolist()
    
    log(f"Missing study IDs: {len(missing_ids)}")
    for study_id in missing_ids:
        log(f"  - {study_id}")
    
    # Fetch all Zotero items
    log("\n" + "="*70)
    all_items = get_all_zotero_items()
    
    # Filter to regular items (not attachments)
    regular_items = [item for item in all_items if item['data'].get('itemType') != 'attachment']
    log(f"Regular bibliographic items: {len(regular_items)}")
    
    # Search for matching items
    log("\n" + "="*70)
    log("Searching for matches...")
    log("="*70)
    
    results = []
    
    for study_id in missing_ids:
        log(f"\nSearching for Study ID: {study_id}")
        
        matches = []
        
        # Search in various fields where study ID might be stored
        for item in regular_items:
            data = item['data']
            
            # Check Extra field (common place for custom IDs)
            extra = data.get('extra', '')
            if study_id in extra:
                matches.append({
                    'match_type': 'extra_field',
                    'item': item,
                    'snippet': extra[:100]
                })
                
            # Check Key field (if exists)
            key_field = data.get('Key', '')
            if study_id in str(key_field):
                matches.append({
                    'match_type': 'key_field',
                    'item': item,
                    'snippet': key_field
                })
                
            # Check URL (sometimes IDs are in URLs)
            url = data.get('url', '')
            if study_id in url:
                matches.append({
                    'match_type': 'url',
                    'item': item,
                    'snippet': url
                })
        
        if matches:
            log(f"  ✓ Found {len(matches)} potential match(es)")
            
            for match in matches:
                item = match['item']
                data = item['data']
                
                # Check for PDF
                has_pdf, pdf_key = check_for_pdf_attachment(item['key'])
                time.sleep(0.3)
                
                result = {
                    'study_id': study_id,
                    'zotero_key': item['key'],
                    'title': data.get('title', '')[:80],
                    'authors': ', '.join([c.get('lastName', '') for c in data.get('creators', [])[:2]]),
                    'year': data.get('date', '')[:4],
                    'match_type': match['match_type'],
                    'has_pdf': 'Yes' if has_pdf else 'No',
                    'pdf_attachment_key': pdf_key if has_pdf else '',
                    'item_type': data.get('itemType', '')
                }
                
                results.append(result)
                
                log(f"    Match: {result['title']}")
                log(f"    Zotero Key: {result['zotero_key']}")
                log(f"    PDF: {result['has_pdf']}")
                log(f"    Match via: {match['match_type']}")
        else:
            log(f"  ✗ No match found")
            
            # Add empty result
            results.append({
                'study_id': study_id,
                'zotero_key': '',
                'title': '',
                'authors': '',
                'year': '',
                'match_type': 'NOT FOUND',
                'has_pdf': '',
                'pdf_attachment_key': '',
                'item_type': ''
            })
    
    # Save results
    log("\n" + "="*70)
    log("SAVING RESULTS")
    log("="*70)
    
    df_results = pd.DataFrame(results)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"missing_studies_zotero_mapping_{timestamp}.csv"
    
    df_results.to_csv(output_file, index=False)
    log(f"✓ Results saved to: {output_file}")
    
    # Summary
    log("\n" + "="*70)
    log("SUMMARY")
    log("="*70)
    
    found = len(df_results[df_results['zotero_key'] != ''])
    not_found = len(df_results[df_results['zotero_key'] == ''])
    with_pdf = len(df_results[df_results['has_pdf'] == 'Yes'])
    
    log(f"Study IDs searched: {len(missing_ids)}")
    log(f"Matches found: {found}")
    log(f"Not found: {not_found}")
    log(f"With PDF in Zotero: {with_pdf}")
    
    if with_pdf > 0:
        log(f"\n✓ Can download {with_pdf} PDFs from Zotero")
        log(f"  Use sync_pdfs_from_zotero.py or step_minus1_zotero_export.js")
    
    if not_found > 0:
        log(f"\n⚠ {not_found} studies not found in Zotero")
        log(f"  These may need manual review or different search strategy")
    
    return df_results

if __name__ == "__main__":
    results = find_missing_studies()
