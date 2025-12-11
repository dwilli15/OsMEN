#!/usr/bin/env python3
"""
Batch ACSM Processor - Process multiple ACSM files through DRM liberation pipeline
"""

import base64
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import requests

# Add plugin paths
sys.path.insert(0, r"C:\Users\armad\AppData\Local\Temp\DeACSM_extract")
sys.path.insert(0, r"C:\Users\armad\AppData\Local\Temp\DeDRM_work")

import ineptepub
from asn1crypto import keys
from libadobeFulfill import fulfill

OUTPUT_DIR = Path(r"D:\OsMEN\content\ebooks\drm_free")
TEXTBOOK_DIR = Path(
    r"C:\Users\armad\OneDrive\Documents\Professional\MLTS\Timeline\Spiring 2026"
)
CALIBRE = Path(r"C:\Program Files\Calibre2\ebook-convert.exe")
PANDOC = Path(r"C:\Users\armad\AppData\Local\Pandoc\pandoc.exe")


def get_decryption_key():
    """Extract and convert DeACSM key from PKCS8 to raw RSA"""
    activation = Path(
        r"C:\Users\armad\AppData\Roaming\calibre\plugins\DeACSM\account\activation.xml"
    )
    with open(activation, "r") as f:
        content = f.read()
    root = ET.fromstring(content)
    for elem in root.iter():
        if elem.tag.endswith("privateLicenseKey") and elem.text:
            pkcs8 = base64.b64decode(elem.text.strip())
            pk_info = keys.PrivateKeyInfo.load(pkcs8)
            return pk_info["private_key"].parsed.dump()
    return None


def extract_download_url(xml_content):
    """Find download URL in fulfillment response"""
    root = ET.fromstring(xml_content)
    for elem in root.iter():
        if elem.tag.endswith("src") and elem.text:
            return elem.text.strip()
        if elem.tag.endswith("downloadURL") and elem.text:
            return elem.text.strip()
    return None


def extract_license_token(xml_content):
    """Extract licenseToken for rights.xml"""
    root = ET.fromstring(xml_content)
    for elem in root.iter():
        if elem.tag.endswith("licenseToken"):
            token_str = ET.tostring(elem, encoding="unicode")
            token_str = token_str.replace("ns0:", "adept:").replace(
                "xmlns:ns0", "xmlns:adept"
            )
            rights = '<?xml version="1.0" encoding="UTF-8"?>\n'
            rights += '<adept:rights xmlns:adept="http://ns.adobe.com/adept">\n'
            rights += token_str + "\n"
            rights += "</adept:rights>"
            return rights
    return None


def process_acsm(acsm_path, title_slug):
    """Full pipeline for one ACSM file"""
    print(f'\n{"="*60}')
    print(f"Processing: {title_slug}")
    print(f'{"="*60}')

    # 1. Fulfill
    print("  [1/6] Fulfilling ACSM...")
    success, response = fulfill(str(acsm_path))
    if not success:
        print(f"  FAILED: {response}")
        return None

    # 2. Download EPUB
    download_url = extract_download_url(response)
    if not download_url:
        print("  ERROR: No download URL found")
        return None

    print(f"  [2/6] Downloading EPUB...")
    epub_data = requests.get(download_url, timeout=60).content

    encrypted_epub = OUTPUT_DIR / f"{title_slug}_encrypted.epub"
    with open(encrypted_epub, "wb") as f:
        f.write(epub_data)
    print(f"        Downloaded: {len(epub_data):,} bytes")

    # 3. Create rights.xml
    print("  [3/6] Extracting license token...")
    rights_xml = extract_license_token(response)
    if not rights_xml:
        print("  ERROR: No licenseToken found")
        return None

    # 4. Inject rights.xml into EPUB
    print("  [4/6] Injecting rights.xml...")
    epub_with_rights = OUTPUT_DIR / f"{title_slug}_with_rights.epub"
    with zipfile.ZipFile(encrypted_epub, "r") as zin:
        with zipfile.ZipFile(epub_with_rights, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                zout.writestr(item, zin.read(item.filename))
            zout.writestr("META-INF/rights.xml", rights_xml.encode("utf-8"))

    # 5. Decrypt
    print("  [5/6] Decrypting...")
    key = get_decryption_key()
    decrypted_epub = OUTPUT_DIR / f"{title_slug}.epub"
    result = ineptepub.decryptBook(key, str(epub_with_rights), str(decrypted_epub))

    if result != 0:
        print(
            f"  Decryption result: {result} (0=success, 1=already DRM-free, 2=wrong key)"
        )
        if result == 2:
            return None

    print(f"        Decrypted: {decrypted_epub.name}")

    # 6. Convert formats
    print("  [6/6] Converting formats...")

    # PDF
    pdf_path = OUTPUT_DIR / f"{title_slug}.pdf"
    subprocess.run(
        [
            str(CALIBRE),
            str(decrypted_epub),
            str(pdf_path),
            "--pdf-page-numbers",
            "--pdf-add-toc",
        ],
        capture_output=True,
    )
    if pdf_path.exists():
        print(f"        PDF: {pdf_path.stat().st_size:,} bytes")

    # Markdown
    md_path = OUTPUT_DIR / f"{title_slug}.md"
    subprocess.run(
        [str(PANDOC), str(decrypted_epub), "-o", str(md_path), "--wrap=none"],
        capture_output=True,
    )
    if md_path.exists():
        print(f"        Markdown: {md_path.stat().st_size:,} bytes")

    return {
        "epub": decrypted_epub,
        "pdf": pdf_path if pdf_path.exists() else None,
        "md": md_path if md_path.exists() else None,
    }


def copy_to_textbooks(results, title_slug):
    """Copy converted files to textbook directory"""
    print(f"  Copying to textbook folder...")
    for fmt, path in results.items():
        if path and path.exists():
            dest = TEXTBOOK_DIR / path.name
            import shutil

            shutil.copy(path, dest)
            print(f"        {fmt.upper()}: {dest.name}")


def main():
    # Books to process
    books = [
        ("3118502.acsm", "Wolf_Shall_Dwell_With_Lamb"),
        ("31281304.acsm", "Blessing_It_All"),
    ]

    successes = []
    failures = []

    for acsm_file, title_slug in books:
        acsm_path = TEXTBOOK_DIR / acsm_file
        if not acsm_path.exists():
            print(f"SKIP: {acsm_file} not found")
            failures.append(title_slug)
            continue

        try:
            results = process_acsm(acsm_path, title_slug)
            if results:
                copy_to_textbooks(results, title_slug)
                successes.append(title_slug)
            else:
                failures.append(title_slug)
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback

            traceback.print_exc()
            failures.append(title_slug)

    # Summary
    print(f'\n{"="*60}')
    print("SUMMARY")
    print(f'{"="*60}')
    print(f"Successes: {len(successes)}")
    for s in successes:
        print(f"  ✓ {s}")
    print(f"Failures: {len(failures)}")
    for f in failures:
        print(f"  ✗ {f}")


if __name__ == "__main__":
    main()
    main()
