#!/usr/bin/env python3
"""Extract text from Skovholt PDF"""

from pathlib import Path

from integrations.calibre.calibre_manager import CalibreManager

manager = CalibreManager()

pdf_path = r"D:\OsMEN\content\courses\M483INT_Pastoral_Ministry\downloads\Skovholt_ReslientPractitioner.pdf"
output_dir = Path(r"D:\OsMEN\content\courses\M483INT_Pastoral_Ministry\text")
output_dir.mkdir(parents=True, exist_ok=True)

# Extract text from PDF
print("📚 Extracting text from Skovholt PDF...")
text_file = manager.extract_text(pdf_path, output_dir)

if text_file and text_file.exists():
    size = text_file.stat().st_size
    with open(text_file, "r", encoding="utf-8", errors="ignore") as f:
        lines = len(f.readlines())
    print(f"✅ Text extracted: {text_file.name}")
    print(f"📊 Size: {size} bytes, {lines} lines")
else:
    print(f"⚠️ Extraction might have failed")
    print(f"⚠️ Extraction might have failed")
