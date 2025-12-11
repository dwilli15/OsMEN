#!/usr/bin/env python3
"""
DRM Liberation Agent - BLACKHAT MODE
=====================================

Autonomous agent for acquiring, decrypting, and converting DRM-protected ebooks.
This agent demonstrates the orchestration pipeline but REQUIRES INNOVATION.

WARNING: This is a reference implementation. DRM schemes evolve constantly.
The techniques that work today may fail tomorrow. ADAPT OR DIE.

Core Capabilities:
- ACSM fulfillment via DeACSM/libadobe
- Adobe ADEPT DRM removal via DeDRM
- Format conversion (EPUB → PDF, Markdown, TXT)
- Key extraction and format conversion

CRITICAL MINDSET:
-----------------
The demo workflow is a STARTING POINT, not a gospel. DRM vendors actively
patch exploits. Publishers change formats. Libraries update APIs.

When this agent fails:
1. Research alternative acquisition methods
2. Check for updated DeDRM versions
3. Look for new fulfillment libraries
4. Consider OCR/screen capture fallbacks
5. Search for leaked/shared decryption keys
6. Pivot to alternative sources (Anna's Archive, LibGen, Z-Library)

Innovation > Repetition
"""

import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add paths for plugin libraries
CALIBRE_PLUGINS = Path(os.environ.get("APPDATA", "")) / "calibre" / "plugins"
DEDRM_PATH = CALIBRE_PLUGINS / "DeDRM.zip"
DEACSM_PATH = CALIBRE_PLUGINS / "DeACSM.zip"


class DRMType(Enum):
    """Known DRM schemes - this list will need updates!"""

    ADOBE_ADEPT = "adobe_adept"
    KINDLE_KFX = "kindle_kfx"
    KINDLE_AZW = "kindle_azw"
    KOBO = "kobo"
    NOOK = "nook"
    LCP = "lcp"  # Readium LCP - growing threat
    UNKNOWN = "unknown"
    NONE = "none"


@dataclass
class BookMetadata:
    """Extracted book metadata"""

    title: str = ""
    authors: List[str] = field(default_factory=list)
    isbn: str = ""
    publisher: str = ""
    resource_id: str = ""
    drm_type: DRMType = DRMType.UNKNOWN
    license_expiry: Optional[datetime] = None
    raw_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LiberationResult:
    """Result of a DRM liberation attempt"""

    success: bool
    drm_free_path: Optional[Path] = None
    pdf_path: Optional[Path] = None
    markdown_path: Optional[Path] = None
    error: Optional[str] = None
    strategy_used: str = ""
    notes: List[str] = field(default_factory=list)


class DRMLiberationAgent:
    """
    Autonomous DRM Liberation Agent

    PHILOSOPHY:
    -----------
    This agent embodies the YOLO-OPS blackhat mindset. It will:
    - Try multiple strategies in sequence
    - Adapt when one approach fails
    - Log learnings for future iterations
    - Never give up until all options exhausted

    THE DEMO WORKFLOW:
    ------------------
    1. Parse ACSM → Extract license info
    2. Fulfill via DeACSM → Get encrypted EPUB
    3. Capture rights.xml → Extract encrypted book key
    4. Convert key format → PKCS8 to raw RSA
    5. Inject rights.xml → Create decryptable EPUB
    6. DeDRM decrypt → Remove Adobe ADEPT
    7. Convert formats → PDF, Markdown

    BUT REMEMBER: This workflow was discovered through trial and error.
    Future tasks may require completely different approaches!
    """

    def __init__(self, output_dir: Path = None, work_dir: Path = None):
        self.output_dir = output_dir or Path("D:/OsMEN/content/ebooks/drm_free")
        self.work_dir = work_dir or Path(tempfile.mkdtemp(prefix="drm_lib_"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Tool paths - THESE MAY NEED UPDATING
        self.calibre_path = Path("C:/Program Files/Calibre2")
        self.pandoc_path = (
            Path(os.environ.get("LOCALAPPDATA", "")) / "Pandoc" / "pandoc.exe"
        )

        # Plugin extraction paths
        self.dedrm_extract = self.work_dir / "DeDRM"
        self.deacsm_extract = self.work_dir / "DeACSM"

        # Logging
        self.log: List[str] = []

    def _log(self, message: str):
        """Log a message with timestamp"""
        entry = f"[{datetime.now().isoformat()}] {message}"
        self.log.append(entry)
        print(entry)

    def _extract_plugin(self, plugin_zip: Path, extract_to: Path) -> bool:
        """Extract a Calibre plugin for direct use"""
        if not plugin_zip.exists():
            self._log(f"Plugin not found: {plugin_zip}")
            return False

        if extract_to.exists():
            shutil.rmtree(extract_to)
        extract_to.mkdir(parents=True)

        with zipfile.ZipFile(plugin_zip, "r") as zf:
            zf.extractall(extract_to)

        self._log(f"Extracted {plugin_zip.name} to {extract_to}")
        return True

    def parse_acsm(self, acsm_path: Path) -> BookMetadata:
        """
        Parse ACSM file to extract metadata and license info.

        NOTE: ACSM format may change! Monitor for:
        - New XML namespaces
        - Changed element names
        - Additional DRM flags
        """
        metadata = BookMetadata()

        try:
            with open(acsm_path, "r", encoding="utf-8") as f:
                content = f.read()

            root = ET.fromstring(content)
            ns = {"adept": "http://ns.adobe.com/adept"}

            # Extract standard fields
            for elem in root.iter():
                tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                text = elem.text.strip() if elem.text else ""

                if tag == "title":
                    metadata.title = text
                elif tag == "creator":
                    metadata.authors.append(text)
                elif tag == "identifier":
                    metadata.isbn = text
                elif tag == "publisher":
                    metadata.publisher = text
                elif tag == "resource":
                    metadata.resource_id = text
                elif tag == "expiration":
                    try:
                        metadata.license_expiry = datetime.fromisoformat(
                            text.replace("Z", "+00:00")
                        )
                    except:
                        pass

                metadata.raw_metadata[tag] = text

            metadata.drm_type = DRMType.ADOBE_ADEPT
            self._log(f"Parsed ACSM: {metadata.title} by {', '.join(metadata.authors)}")

        except Exception as e:
            self._log(f"ACSM parse error: {e}")

        return metadata

    def fulfill_acsm(self, acsm_path: Path) -> Tuple[Optional[Path], Optional[str]]:
        """
        Fulfill ACSM license and download encrypted EPUB.

        STRATEGY EVOLUTION:
        - Primary: DeACSM library fulfillment
        - Fallback 1: Adobe Digital Editions
        - Fallback 2: knock/libgourou (Linux)
        - Fallback 3: Alternative acquisition

        INNOVATION REQUIRED: If Adobe changes their fulfillment API,
        this entire function may need rewriting!
        """
        self._log("Attempting ACSM fulfillment...")

        # Strategy 1: DeACSM
        epub_path, fulfillment_xml = self._fulfill_via_deacsm(acsm_path)
        if epub_path:
            return epub_path, fulfillment_xml

        # Strategy 2: ADE (requires GUI interaction)
        self._log("DeACSM failed, trying ADE...")
        epub_path = self._fulfill_via_ade(acsm_path)
        if epub_path:
            return epub_path, None

        # Strategy 3: Alternative sources
        self._log("Direct fulfillment failed. Consider alternative acquisition.")
        return None, None

    def _fulfill_via_deacsm(
        self, acsm_path: Path
    ) -> Tuple[Optional[Path], Optional[str]]:
        """Fulfill using DeACSM library"""
        try:
            # Extract DeACSM if needed
            if not self.deacsm_extract.exists():
                self._extract_plugin(DEACSM_PATH, self.deacsm_extract)

            # Import DeACSM modules
            sys.path.insert(0, str(self.deacsm_extract))

            # Import authorization module
            from libadobeFulfill import fulfill
            from libadobeImportAccount import importADEactivationWindows

            # Ensure authorization is imported
            self._log("Checking Adobe authorization...")
            auth_result = importADEactivationWindows()
            if not auth_result[0]:
                self._log(f"Authorization import failed: {auth_result[1]}")
                return None, None

            # Fulfill
            self._log("Fulfilling ACSM...")
            success, response = fulfill(str(acsm_path))

            if not success:
                self._log(f"Fulfillment failed: {response}")
                return None, None

            # Save fulfillment response
            fulfillment_path = self.work_dir / "fulfillment_response.xml"
            with open(fulfillment_path, "w", encoding="utf-8") as f:
                f.write(response)

            # Extract download URL and fetch EPUB
            epub_path = self._download_from_fulfillment(response)

            return epub_path, response

        except ImportError as e:
            self._log(f"DeACSM import error: {e}")
            self._log("TIP: Install dependencies: pip install oscrypto asn1crypto")
        except Exception as e:
            self._log(f"DeACSM error: {e}")

        return None, None

    def _download_from_fulfillment(self, fulfillment_xml: str) -> Optional[Path]:
        """Extract download URL from fulfillment and fetch EPUB"""
        try:
            import requests

            root = ET.fromstring(fulfillment_xml)

            # Find downloadURL
            download_url = None
            for elem in root.iter():
                if elem.tag.endswith("downloadURL") and elem.text:
                    download_url = elem.text.strip()
                    break

            if not download_url:
                self._log("No download URL in fulfillment")
                return None

            self._log(f"Downloading from: {download_url[:60]}...")

            response = requests.get(download_url, timeout=60)
            response.raise_for_status()

            epub_path = self.work_dir / "downloaded.epub"
            with open(epub_path, "wb") as f:
                f.write(response.content)

            self._log(f"Downloaded {len(response.content)} bytes")
            return epub_path

        except Exception as e:
            self._log(f"Download error: {e}")
            return None

    def _fulfill_via_ade(self, acsm_path: Path) -> Optional[Path]:
        """
        Fulfill via Adobe Digital Editions.
        Requires ADE to be installed and user to complete the process.
        """
        ade_path = Path(
            "C:/Program Files (x86)/Adobe/Adobe Digital Editions 4.5/DigitalEditions.exe"
        )

        if not ade_path.exists():
            self._log("ADE not found")
            return None

        try:
            # Launch ADE with ACSM
            subprocess.Popen([str(ade_path), str(acsm_path)])
            self._log("Launched ADE - complete fulfillment manually")

            # Check ADE Documents folder for new files
            ade_docs = (
                Path(os.environ.get("USERPROFILE", ""))
                / "Documents"
                / "My Digital Editions"
            )

            self._log(f"Check {ade_docs} for fulfilled EPUB")
            # In a real scenario, we'd poll for the new file

            return None  # Manual intervention required

        except Exception as e:
            self._log(f"ADE launch error: {e}")
            return None

    def extract_rights_from_fulfillment(self, fulfillment_xml: str) -> Optional[str]:
        """
        Extract licenseToken from fulfillment response and create rights.xml

        THIS IS A CRITICAL DISCOVERY:
        -----------------------------
        DeACSM fulfillment returns the license token, but doesn't save it
        to the EPUB. We must manually create rights.xml and inject it!

        If this stops working, check:
        - Changed XML structure in fulfillment response
        - New encryption of license token
        - Different namespace prefixes
        """
        try:
            root = ET.fromstring(fulfillment_xml)

            # Find licenseToken
            license_token = None
            for elem in root.iter():
                if elem.tag.endswith("licenseToken"):
                    license_token = elem
                    break

            if license_token is None:
                self._log("No licenseToken in fulfillment")
                return None

            # Serialize with proper namespace
            license_str = ET.tostring(license_token, encoding="unicode")
            license_str = license_str.replace("ns0:", "adept:").replace(
                "xmlns:ns0", "xmlns:adept"
            )

            # Create rights.xml
            rights_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<adept:rights xmlns:adept="http://ns.adobe.com/adept">
{license_str}
</adept:rights>"""

            rights_path = self.work_dir / "rights.xml"
            with open(rights_path, "w", encoding="utf-8") as f:
                f.write(rights_xml)

            self._log("Created rights.xml from fulfillment")
            return str(rights_path)

        except Exception as e:
            self._log(f"Rights extraction error: {e}")
            return None

    def inject_rights_into_epub(self, epub_path: Path, rights_path: Path) -> Path:
        """
        Inject rights.xml into EPUB META-INF folder.

        This creates a "complete" DRM'd EPUB that DeDRM can decrypt.
        """
        output_path = self.work_dir / "epub_with_rights.epub"

        with open(rights_path, "rb") as f:
            rights_data = f.read()

        with zipfile.ZipFile(epub_path, "r") as zin:
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zout:
                for item in zin.infolist():
                    zout.writestr(item, zin.read(item.filename))
                zout.writestr("META-INF/rights.xml", rights_data)

        self._log(f"Injected rights.xml into EPUB")
        return output_path

    def extract_decryption_key(self) -> Optional[Path]:
        """
        Extract Adobe decryption key from DeACSM activation.

        KEY FORMAT GOTCHA:
        ------------------
        DeACSM stores keys in PKCS#8 format (640 bytes)
        DeDRM expects raw RSA DER format (610 bytes)

        We must extract the inner RSA key using asn1crypto!

        If this breaks, check:
        - Changed key storage format
        - New key encryption
        - Different activation structure
        """
        deacsm_account = CALIBRE_PLUGINS / "DeACSM" / "account" / "activation.xml"

        if not deacsm_account.exists():
            self._log("DeACSM activation not found")
            return None

        try:
            with open(deacsm_account, "r", encoding="utf-8") as f:
                content = f.read()

            root = ET.fromstring(content)

            # Find privateLicenseKey
            private_key_b64 = None
            for elem in root.iter():
                if elem.tag.endswith("privateLicenseKey") and elem.text:
                    private_key_b64 = elem.text.strip()
                    break

            if not private_key_b64:
                self._log("No private key in activation")
                return None

            # Decode from base64
            pkcs8_key = base64.b64decode(private_key_b64)
            self._log(f"Found PKCS8 key: {len(pkcs8_key)} bytes")

            # Convert PKCS8 to raw RSA using asn1crypto
            from asn1crypto import keys

            pk_info = keys.PrivateKeyInfo.load(pkcs8_key)
            raw_rsa = pk_info["private_key"].parsed.dump()

            self._log(f"Converted to raw RSA: {len(raw_rsa)} bytes")

            key_path = self.work_dir / "decryption_key.der"
            with open(key_path, "wb") as f:
                f.write(raw_rsa)

            return key_path

        except ImportError:
            self._log("asn1crypto not installed: pip install asn1crypto")
        except Exception as e:
            self._log(f"Key extraction error: {e}")

        return None

    def decrypt_epub(self, epub_path: Path, key_path: Path) -> Optional[Path]:
        """
        Decrypt Adobe ADEPT DRM using DeDRM's ineptepub.

        DECRYPTION EVOLUTION:
        - Current: ineptepub with RSA key
        - Future: May need new decryption methods
        - Watch for: New ADEPT versions, hardening
        """
        try:
            # Extract DeDRM if needed
            if not self.dedrm_extract.exists():
                self._extract_plugin(DEDRM_PATH, self.dedrm_extract)

            sys.path.insert(0, str(self.dedrm_extract))

            import ineptepub

            with open(key_path, "rb") as f:
                key_data = f.read()

            output_path = self.output_dir / f"{epub_path.stem}_decrypted.epub"

            result = ineptepub.decryptBook(key_data, str(epub_path), str(output_path))

            if result == 0:
                self._log(f"Decryption successful: {output_path}")
                return output_path
            elif result == 1:
                self._log("Book reported as DRM-free (check if actually decrypted)")
                return output_path
            else:
                self._log(f"Decryption failed with code {result}")

        except ImportError:
            self._log("pycryptodome not installed: pip install pycryptodome")
        except Exception as e:
            self._log(f"Decryption error: {e}")

        return None

    def convert_to_pdf(self, epub_path: Path) -> Optional[Path]:
        """Convert EPUB to PDF using Calibre"""
        output_path = (
            self.output_dir / f"{epub_path.stem.replace('_decrypted', '')}.pdf"
        )

        convert_exe = self.calibre_path / "ebook-convert.exe"
        if not convert_exe.exists():
            self._log("Calibre ebook-convert not found")
            return None

        try:
            result = subprocess.run(
                [
                    str(convert_exe),
                    str(epub_path),
                    str(output_path),
                    "--pdf-page-numbers",
                    "--pdf-add-toc",
                ],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if output_path.exists():
                self._log(f"PDF created: {output_path}")
                return output_path
            else:
                self._log(f"PDF conversion failed: {result.stderr[:200]}")

        except Exception as e:
            self._log(f"PDF conversion error: {e}")

        return None

    def convert_to_markdown(self, epub_path: Path) -> Optional[Path]:
        """Convert EPUB to Markdown using Pandoc"""
        output_path = self.output_dir / f"{epub_path.stem.replace('_decrypted', '')}.md"
        media_dir = self.output_dir / "media"

        if not self.pandoc_path.exists():
            self._log("Pandoc not found - install via: winget install pandoc")
            return None

        try:
            result = subprocess.run(
                [
                    str(self.pandoc_path),
                    str(epub_path),
                    "-o",
                    str(output_path),
                    f"--extract-media={media_dir}",
                    "--wrap=none",
                ],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if output_path.exists():
                self._log(f"Markdown created: {output_path}")
                return output_path
            else:
                self._log(f"Markdown conversion failed: {result.stderr[:200]}")

        except Exception as e:
            self._log(f"Markdown conversion error: {e}")

        return None

    def liberate(self, acsm_path: Path) -> LiberationResult:
        """
        Main liberation pipeline.

        THE DEMO WORKFLOW:
        1. Parse ACSM
        2. Fulfill license
        3. Extract rights
        4. Extract key
        5. Inject rights
        6. Decrypt
        7. Convert

        REMEMBER: This is just ONE possible workflow!
        Adapt based on what you encounter.
        """
        result = LiberationResult(success=False)

        self._log("=" * 60)
        self._log("DRM LIBERATION AGENT - BLACKHAT MODE ENGAGED")
        self._log("=" * 60)

        # Step 1: Parse ACSM
        metadata = self.parse_acsm(acsm_path)
        if not metadata.title:
            result.error = "Failed to parse ACSM"
            return result

        result.notes.append(f"Title: {metadata.title}")

        # Step 2: Fulfill
        epub_path, fulfillment_xml = self.fulfill_acsm(acsm_path)
        if not epub_path:
            result.error = "Fulfillment failed"
            result.notes.append("TIP: Check authorization, try manual ADE fulfillment")
            return result

        # Step 3: Extract rights from fulfillment
        if fulfillment_xml:
            rights_path = self.extract_rights_from_fulfillment(fulfillment_xml)
            if rights_path:
                # Step 4: Inject rights into EPUB
                epub_path = self.inject_rights_into_epub(epub_path, Path(rights_path))

        # Step 5: Extract decryption key
        key_path = self.extract_decryption_key()
        if not key_path:
            result.error = "Key extraction failed"
            result.notes.append("TIP: Check DeACSM activation, re-import from ADE")
            return result

        # Step 6: Decrypt
        decrypted_path = self.decrypt_epub(epub_path, key_path)
        if not decrypted_path:
            result.error = "Decryption failed"
            result.notes.append("TIP: Wrong key? Try ADE-extracted key instead")
            return result

        result.drm_free_path = decrypted_path
        result.strategy_used = "DeACSM fulfillment + rights injection + DeDRM"

        # Step 7: Convert
        result.pdf_path = self.convert_to_pdf(decrypted_path)
        result.markdown_path = self.convert_to_markdown(decrypted_path)

        result.success = True
        self._log("=" * 60)
        self._log("LIBERATION COMPLETE")
        self._log("=" * 60)

        return result

    def cleanup(self):
        """Clean up temporary files"""
        if self.work_dir.exists():
            shutil.rmtree(self.work_dir, ignore_errors=True)


# =============================================================================
# AGENT INSTRUCTIONS FOR FUTURE USE
# =============================================================================
"""
## CRITICAL NOTES FOR OPERATORS

### THE WORKFLOW IS A DEMO, NOT A GUARANTEE

The pipeline demonstrated here (DeACSM → rights injection → DeDRM) worked for
a specific ACSM file on December 7, 2025. Future operations may require:

1. **Different Fulfillment Methods**
   - Adobe may change their API
   - Libraries may use different DRM servers
   - New authentication requirements

2. **Different Decryption Tools**
   - DeDRM may be patched/detected
   - New DRM hardening techniques
   - Different key formats

3. **Alternative Acquisition**
   - Direct PDF download if available
   - Inter-library loan of physical
   - Purchase + return after conversion
   - Academic/institutional access
   - Gray sources (Anna's Archive, LibGen, Z-Library)

### TROUBLESHOOTING CHECKLIST

When the standard pipeline fails:

□ Is the ACSM valid and not expired?
□ Is Adobe authorization imported correctly?
□ Does rights.xml exist in the fulfilled EPUB?
□ Is the decryption key in the correct format (raw RSA, not PKCS8)?
□ Are all dependencies installed (pycryptodome, oscrypto, asn1crypto)?
□ Is Calibre/DeDRM up to date?

### INNOVATION STRATEGIES

1. **Research Phase**
   - Check DeDRM GitHub for issues/updates
   - Search for ACSM fulfillment alternatives
   - Look for publisher-specific bypasses

2. **Pivot Phase**
   - Try different tools (knock, libgourou)
   - Use OCR on screen captures as last resort
   - Consider purchasing DRM-free version if available

3. **Documentation Phase**
   - Log what worked and what didn't
   - Update this agent with new techniques
   - Share findings (responsibly)

### DEPENDENCIES

```bash
pip install pycryptodome oscrypto asn1crypto requests
winget install pandoc
```

### CALIBRE PLUGINS REQUIRED

- DeDRM (https://github.com/noDRM/DeDRM_tools)
- DeACSM (https://github.com/Leseratte10/acsm-calibre-plugin)

### LEGAL NOTICE

This agent is for personal backup of legally acquired content only.
You must own or have legitimate access to the content being decrypted.
DRM circumvention laws vary by jurisdiction.
"""


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="DRM Liberation Agent - BLACKHAT MODE",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python drm_liberation_agent.py book.acsm
  python drm_liberation_agent.py --output ./books book.acsm
  
The workflow is a DEMO. Innovation may be required!
        """,
    )
    parser.add_argument("acsm", type=Path, help="Path to ACSM file")
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Output directory for converted files",
    )

    args = parser.parse_args()

    if not args.acsm.exists():
        print(f"Error: ACSM file not found: {args.acsm}")
        sys.exit(1)

    agent = DRMLiberationAgent(output_dir=args.output)

    try:
        result = agent.liberate(args.acsm)

        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)
        print(f"Success: {result.success}")
        if result.drm_free_path:
            print(f"EPUB: {result.drm_free_path}")
        if result.pdf_path:
            print(f"PDF: {result.pdf_path}")
        if result.markdown_path:
            print(f"Markdown: {result.markdown_path}")
        if result.error:
            print(f"Error: {result.error}")
        for note in result.notes:
            print(f"Note: {note}")

        sys.exit(0 if result.success else 1)

    finally:
        agent.cleanup()


if __name__ == "__main__":
    main()
