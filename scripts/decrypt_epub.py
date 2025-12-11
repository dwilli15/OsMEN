#!/usr/bin/env python3
"""Decrypt Adobe ADEPT DRM EPUB using extracted key."""

import os
import shutil
import sys
import zipfile
from pathlib import Path

# Add DeDRM extracted path
sys.path.insert(0, os.path.expandvars(r"%TEMP%\DeDRM_extract"))


def decrypt_epub():
    """Decrypt the EPUB using DeDRM ineptepub module."""
    try:
        from ineptepub import decryptBook

        key_path = os.path.expandvars(
            r"%APPDATA%\calibre\plugins\DeDRM\adobekey_extracted.der"
        )
        epub_path = r"D:\OsMEN\content\ebooks\drm_free\The_Resilient_Practitioner.epub"
        output_path = r"D:\OsMEN\content\ebooks\drm_free\The_Resilient_Practitioner_DECRYPTED.epub"

        print(f"Key: {key_path}")
        print(f"Input: {epub_path}")
        print(f"Output: {output_path}")

        if not os.path.exists(key_path):
            print(f"ERROR: Key file not found: {key_path}")
            return False

        if not os.path.exists(epub_path):
            print(f"ERROR: EPUB file not found: {epub_path}")
            return False

        result = decryptBook(key_path, epub_path, output_path)
        print(f"Decryption result: {result}")

        if os.path.exists(output_path):
            print(f"Output file size: {os.path.getsize(output_path)} bytes")
            return True
        return False

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    decrypt_epub()
