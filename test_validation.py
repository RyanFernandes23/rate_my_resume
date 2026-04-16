import sys

sys.path.insert(0, ".")

from app.extractors import extract
import pymupdf

# Create a 3-page PDF to test validation
doc = pymupdf.open()
for i in range(3):
    page = doc.new_page()
    page.insert_text((50, 50), f"Page {i + 1} content")
doc.save("tests/3page_test.pdf")
doc.close()

print("Testing 3-page PDF...")
try:
    extract("tests/3page_test.pdf")
    print("ERROR: Should have raised exception!")
except ValueError as e:
    print(f"Got expected error: {e}")

# Cleanup
import os

os.remove("tests/3page_test.pdf")
print("Test complete!")
