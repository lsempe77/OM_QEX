"""
Test the basic setup - TEI parser and data models.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.tei_parser import TEIParser
from src.models import create_empty_record

def test_tei_parser():
    """Test TEI parser on a sample file."""
    print("=" * 60)
    print("Testing TEI Parser")
    print("=" * 60)
    
    # Path to a sample TEI file
    tei_dir = Path(__file__).parent.parent / "data" / "grobid_outputs" / "tei"
    
    # Get first TEI file
    tei_files = list(tei_dir.glob("*.tei.xml"))
    
    if not tei_files:
        print("❌ No TEI files found in data/grobid_outputs/tei/")
        return False
    
    sample_file = tei_files[0]
    print(f"\n📄 Parsing: {sample_file.name}\n")
    
    try:
        parser = TEIParser(sample_file)
        
        print(f"Title: {parser.get_title()}")
        print(f"Authors: {parser.get_authors()}")
        print(f"Year: {parser.get_publication_year()}")
        print(f"Abstract length: {len(parser.get_abstract())} chars")
        print(f"Body text length: {len(parser.get_body_text())} chars")
        print(f"References: {len(parser.get_references())} found")
        
        print("\n✅ TEI Parser working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error parsing TEI file: {e}")
        return False


def test_data_models():
    """Test Pydantic data models."""
    print("\n" + "=" * 60)
    print("Testing Data Models")
    print("=" * 60 + "\n")
    
    try:
        # Create a sample record
        record = create_empty_record(
            study_id="121058364",
            author="Maldonado",
            year=2019,
            country="Colombia"
        )
        
        # Add some data
        record.intervention_info.consumption_support = "Yes"
        record.intervention_info.assets = "Yes"
        record.estimate_data.mean_post_t = 0.45
        record.estimate_data.p_value = 0.023
        
        # Test JSON serialization
        json_output = record.model_dump_json(indent=2)
        print("JSON serialization: ✅")
        
        # Test flat dict for CSV
        flat_dict = record.to_flat_dict()
        print(f"Flat dict conversion: ✅ ({len(flat_dict)} fields)")
        
        # Show sample fields
        print("\nSample extracted fields:")
        print(f"  - study_id: {flat_dict.get('study_id')}")
        print(f"  - author_name: {flat_dict.get('author_name')}")
        print(f"  - year_of_publication: {flat_dict.get('year_of_publication')}")
        print(f"  - consumption_support: {flat_dict.get('consumption_support')}")
        print(f"  - mean_post_t: {flat_dict.get('mean_post_t')}")
        
        print("\n✅ Data models working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error with data models: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("OM_QEX EXTRACTION - SETUP VERIFICATION")
    print("=" * 60 + "\n")
    
    results = {
        "TEI Parser": test_tei_parser(),
        "Data Models": test_data_models()
    }
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 All tests passed! Ready for Phase 2 (Prompt Engineering)")
        print("\nNext steps:")
        print("1. Create extraction prompt template")
        print("2. Test on 2-3 sample papers manually")
        print("3. Build extraction_engine.py")
    else:
        print("\n⚠️  Some tests failed. Check errors above.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
