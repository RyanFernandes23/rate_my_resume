import sys

sys.path.insert(0, ".")

from app.extractors import extract

pdf_path = "tests/Your life.docx"

print("Extracting PDF...")
result = extract(pdf_path)

print(f"\n--- Extracted {len(result)} characters ---\n")
print(result[:5000])

if len(result) > 5000:
    print(f"\n... (truncated, total: {len(result)} chars)")
