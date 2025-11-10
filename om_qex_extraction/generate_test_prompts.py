"""
Manual testing helper - prepares paper text and prompt for manual LLM testing.
This script generates a complete prompt that you can copy-paste to ChatGPT/Claude.
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from src.tei_parser import TEIParser

def create_test_prompt(tei_file: Path, output_file: Path = None):
    """Create complete prompt for manual testing."""
    
    # Parse the TEI file
    parser = TEIParser(tei_file)
    
    # Get paper text
    full_text = parser.get_full_text(include_abstract=True)
    
    # Load prompt template
    prompt_template_path = Path(__file__).parent / "prompts" / "extraction_prompt.txt"
    with open(prompt_template_path, 'r', encoding='utf-8') as f:
        prompt_template = f.read()
    
    # Replace placeholder with actual text
    complete_prompt = prompt_template.replace("{paper_text}", full_text)
    
    # Print info
    print("=" * 80)
    print(f"TEST PROMPT GENERATED: {tei_file.name}")
    print("=" * 80)
    print(f"\n📄 Paper: {parser.get_title()}")
    print(f"👥 Authors: {', '.join([a.get('full_name', 'Unknown') for a in parser.get_authors()][:3])}")
    print(f"📅 Year: {parser.get_publication_year()}")
    print(f"\n📏 Paper text length: {len(full_text):,} characters")
    print(f"📏 Complete prompt length: {len(complete_prompt):,} characters")
    print(f"📏 Estimated tokens: ~{len(complete_prompt) // 4:,}")
    
    # Save to file if specified
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(complete_prompt)
        print(f"\n✅ Saved to: {output_file}")
        print(f"\nTo test manually:")
        print(f"1. Open {output_file}")
        print(f"2. Copy the entire content")
        print(f"3. Paste into ChatGPT, Claude, or your preferred LLM")
        print(f"4. Verify the JSON output matches the schema")
    else:
        print("\n" + "=" * 80)
        print("COMPLETE PROMPT (copy below)")
        print("=" * 80)
        print(complete_prompt)
    
    return complete_prompt


def main():
    """Generate test prompts for sample papers."""
    
    # Path to TEI files
    tei_dir = Path(__file__).parent.parent / "data" / "grobid_outputs" / "tei"
    output_dir = Path(__file__).parent / "outputs" / "test_prompts"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get first 3 TEI files for testing
    tei_files = sorted(list(tei_dir.glob("*.tei.xml")))[:3]
    
    if not tei_files:
        print("❌ No TEI files found")
        return 1
    
    print(f"\n🧪 Generating test prompts for {len(tei_files)} papers...\n")
    
    for i, tei_file in enumerate(tei_files, 1):
        print(f"\n{'='*80}")
        print(f"PAPER {i}/{len(tei_files)}")
        print(f"{'='*80}")
        
        output_file = output_dir / f"test_prompt_{tei_file.stem}.txt"
        
        try:
            create_test_prompt(tei_file, output_file)
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("✅ TEST PROMPTS GENERATED")
    print("=" * 80)
    print(f"\n📁 Location: {output_dir}")
    print(f"\n📋 Next steps:")
    print(f"1. Open one of the test prompt files")
    print(f"2. Copy entire content")
    print(f"3. Paste into ChatGPT (GPT-4) or Claude (Claude 3.5)")
    print(f"4. Verify JSON output is valid and complete")
    print(f"5. Check if extracted data makes sense")
    print(f"6. Note any issues for prompt refinement")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
