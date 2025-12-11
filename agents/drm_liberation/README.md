# 🔓 DRM Liberation Agent

**BLACKHAT MODE AUTONOMOUS AGENT**

> ⚠️ **THE WORKFLOW IS A DEMO, NOT A GOSPEL**
>
> The techniques demonstrated here worked on December 7, 2025 for a specific ACSM file.
> Future operations may require **completely different approaches**. DRM vendors actively
> patch exploits. Publishers change formats. Libraries update APIs.
>
> **INNOVATION > REPETITION**

## Overview

This agent autonomously converts DRM-protected ebooks (ACSM files) into DRM-free formats:

- **EPUB** (decrypted)
- **PDF** (with TOC and page numbers)
- **Markdown** (with extracted media)

## The Demo Workflow

The following pipeline was discovered through trial and error:

```
ACSM File
    │
    ▼
┌──────────────────────────────────────┐
│ 1. Parse ACSM                        │
│    - Extract metadata, license info   │
│    - Check expiration date           │
└──────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────┐
│ 2. Fulfill License (DeACSM)          │
│    - Import Adobe authorization       │
│    - Send fulfillment request         │
│    - Download encrypted EPUB          │
│    - Capture fulfillment response     │
└──────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────┐
│ 3. Extract Rights                     │
│    - Parse licenseToken from response │
│    - Create META-INF/rights.xml       │
│    - Contains encrypted book key      │
└──────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────┐
│ 4. Convert Key Format                 │
│    - DeACSM stores PKCS#8 (640 bytes) │
│    - DeDRM needs raw RSA (610 bytes)  │
│    - Use asn1crypto to extract        │
└──────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────┐
│ 5. Inject Rights into EPUB            │
│    - Add rights.xml to META-INF       │
│    - Creates "complete" DRM'd EPUB    │
└──────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────┐
│ 6. Decrypt (DeDRM/ineptepub)          │
│    - Load RSA key                      │
│    - Decrypt book key from rights.xml │
│    - Decrypt all content files        │
│    - Remove encryption.xml            │
└──────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────┐
│ 7. Convert Formats                    │
│    - EPUB → PDF (Calibre)             │
│    - EPUB → Markdown (Pandoc)         │
└──────────────────────────────────────┘
    │
    ▼
DRM-Free Files ✓
```

## When Things Break

**The above workflow will eventually fail.** When it does:

### 1. Fulfillment Fails

- Adobe changed their API
- Authorization expired/invalid
- Library changed DRM provider

**Pivot strategies:**

- Re-authorize with Adobe Digital Editions
- Try knock/libgourou (Linux)
- Check for updated DeACSM version
- Manual ADE fulfillment

### 2. Decryption Fails

- New DRM hardening
- Wrong key format
- Missing rights.xml

**Pivot strategies:**

- Check DeDRM GitHub issues
- Try ADE-extracted key instead
- Verify rights.xml has encryptedKey
- Check for LCP (Readium) DRM instead

### 3. Alternative Acquisition

When direct fulfillment is impossible:

- **Anna's Archive** - Largest shadow library search
- **Library Genesis** - Technical/academic books
- **Z-Library** - General collection
- **Internet Archive** - Borrowable scans
- **Publisher direct** - Some offer DRM-free
- **OCR fallback** - Screen capture → Tesseract

## Installation

### Dependencies

```bash
# Python packages
pip install pycryptodome oscrypto asn1crypto requests

# Pandoc (for Markdown)
winget install pandoc
```

### Calibre Plugins

1. **DeDRM** - <https://github.com/noDRM/DeDRM_tools>
2. **DeACSM** - <https://github.com/Leseratte10/acsm-calibre-plugin>

Install via Calibre > Preferences > Plugins > Load plugin from file

### Adobe Authorization

1. Install Adobe Digital Editions
2. Sign in with Adobe ID
3. DeACSM will import authorization automatically

## Usage

### Command Line

```bash
# Basic usage
python drm_liberation_agent.py book.acsm

# Custom output directory
python drm_liberation_agent.py --output ./textbooks book.acsm
```

### Python API

```python
from agents.drm_liberation.drm_liberation_agent import DRMLiberationAgent
from pathlib import Path

agent = DRMLiberationAgent(output_dir=Path("./output"))
result = agent.liberate(Path("book.acsm"))

if result.success:
    print(f"EPUB: {result.drm_free_path}")
    print(f"PDF: {result.pdf_path}")
    print(f"Markdown: {result.markdown_path}")
else:
    print(f"Failed: {result.error}")
    for note in result.notes:
        print(f"Tip: {note}")
```

## Troubleshooting Checklist

When operations fail, check these in order:

- [ ] Is the ACSM valid and not expired?
- [ ] Is Adobe Digital Editions installed and authorized?
- [ ] Has DeACSM imported the authorization? (Check calibre plugins folder)
- [ ] Does pycryptodome, oscrypto, asn1crypto exist? (`pip list | grep crypto`)
- [ ] Is Calibre's DeDRM plugin installed and up to date?
- [ ] Is the decryption key in correct format? (Should be 610 bytes, not 640)
- [ ] Does the EPUB have META-INF/rights.xml?
- [ ] Does rights.xml contain `<encryptedKey>`?

## Key Technical Discoveries

### The rights.xml Problem

DeACSM's `libadobeFulfill.fulfill()` returns a fulfillment XML response containing the `licenseToken` with the encrypted book key. However, when downloading the EPUB, it doesn't save this to `META-INF/rights.xml`.

DeDRM checks for `rights.xml` first - if it doesn't exist, it reports "DRM-free" even though the content is encrypted!

**Solution:** Extract `licenseToken` from fulfillment response, wrap in rights.xml, inject into EPUB.

### The Key Format Problem

DeACSM stores private keys as base64-encoded PKCS#8:

- Length: 640 bytes
- Header: `30 82 02 78` (SEQUENCE with algorithm OID)

DeDRM expects raw RSA DER format:

- Length: 610 bytes  
- Header: `30 82 02 5e` (SEQUENCE, RSA key only)

**Solution:** Use asn1crypto to parse PKCS#8 and extract inner RSA key.

## Legal Notice

This agent is intended for:

- Personal backup of legally purchased content
- Accessibility (format shifting for assistive technology)
- Archival of content you have legitimate access to

DRM circumvention laws vary by jurisdiction. In the US, DMCA Section 1201 prohibits circumvention, but there are exemptions for accessibility and personal use.

**You are responsible for ensuring your use is lawful in your jurisdiction.**

## Contributing

When you discover new techniques:

1. Document what worked and what didn't
2. Update the agent with new strategies
3. Add to the troubleshooting checklist
4. Share findings (responsibly)

## Related Tools

- **Calibre** - Ebook management
- **DeDRM** - DRM removal plugins
- **DeACSM** - ACSM fulfillment
- **knock** - ACSM fulfillment (Linux)
- **libgourou** - Adobe DRM library
- **Apprentice Alf's Blog** - DRM removal guides
