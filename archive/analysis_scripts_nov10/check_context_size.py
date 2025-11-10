from pathlib import Path

tei_path = Path('data/grobid_outputs/tei/PHRKN65M.tei.xml')
txt_path = Path('data/grobid_outputs/text/PHRKN65M.txt')

print("="*100)
print("FILE SIZE ANALYSIS - PHRKN65M")
print("="*100)

# Check file sizes
print(f"\nTEI file size: {tei_path.stat().st_size:,} bytes")
print(f"TXT file size: {txt_path.stat().st_size:,} bytes")

# Count characters/tokens
with open(tei_path, encoding='utf-8') as f:
    tei_content = f.read()
    tei_chars = len(tei_content)
    tei_tokens_est = tei_chars // 4  # Rough estimate: 1 token ~ 4 characters
    
with open(txt_path, encoding='utf-8') as f:
    txt_content = f.read()
    txt_chars = len(txt_content)
    txt_tokens_est = txt_chars // 4

print(f"\nTEI characters: {tei_chars:,}")
print(f"TXT characters: {txt_chars:,}")

print(f"\nEstimated input tokens (TEI): ~{tei_tokens_est:,}")
print(f"Estimated input tokens (TXT): ~{txt_tokens_est:,}")

# Claude 3.5 Haiku has 200K context window
print(f"\nClaude 3.5 Haiku context window: 200,000 tokens")
print(f"TEI uses ~{tei_tokens_est/200000*100:.1f}% of context")
print(f"TXT uses ~{txt_tokens_est/200000*100:.1f}% of context")

# Check what we're actually sending
# The extraction engine uses TEI parsed text
print("\n" + "="*100)
print("WHAT'S BEING SENT TO LLM")
print("="*100)
print("OM extraction uses: TEI parsed (body text only, not full XML)")
print("Estimated: Smaller than full TEI, but still large")
