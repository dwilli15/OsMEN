#!/usr/bin/env python3
"""
DRM Handler - Manages DRM removal and ACSM processing for OsMEN
Integrates with DeDRM and DeACSM Calibre plugins.
"""

import json
import logging
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class DRMType(Enum):
    """Types of DRM"""

    NONE = "none"
    ADOBE = "adobe"
    KINDLE = "kindle"
    KOBO = "kobo"
    BARNES_NOBLE = "barnes_noble"
    APPLE = "apple"
    UNKNOWN = "unknown"


class ACSMStatus(Enum):
    """ACSM file status"""

    VALID = "valid"
    EXPIRED = "expired"
    INVALID = "invalid"
    ALREADY_FULFILLED = "already_fulfilled"


@dataclass
class DRMResult:
    """Result of DRM operation"""

    success: bool
    input_file: str
    output_file: Optional[str] = None
    drm_type: DRMType = DRMType.UNKNOWN
    message: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ACSMInfo:
    """ACSM file information"""

    file_path: str
    status: ACSMStatus
    title: Optional[str] = None
    fulfillment_id: Optional[str] = None
    expiration: Optional[datetime] = None
    download_url: Optional[str] = None
    message: str = ""


class DRMHandler:
    """
    Handles DRM removal and ACSM processing.

    Features:
    - DRM detection across formats
    - DeDRM integration for removal
    - DeACSM integration for ACSM->EPUB
    - Key management (Adobe, Kindle, Kobo)
    - Batch processing
    """

    def __init__(
        self,
        calibre_path: Optional[Path] = None,
        plugins_dir: Optional[Path] = None,
        output_dir: Optional[Path] = None,
    ):
        self.calibre_path = calibre_path or Path(r"C:\Program Files\Calibre2")
        self.plugins_dir = (
            plugins_dir or Path.home() / "AppData" / "Roaming" / "calibre" / "plugins"
        )
        self.output_dir = output_dir or Path("D:/OsMEN/content/ebooks/drm_free")

        self.dedrm_config_path = self.plugins_dir / "dedrm.json"
        self.deacsm_config_path = self.plugins_dir / "deacsm.json"

        self._validate()
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _validate(self) -> None:
        """Validate DRM tools are available"""
        if not self.calibre_path.exists():
            raise FileNotFoundError(f"Calibre not found: {self.calibre_path}")
        if not self.plugins_dir.exists():
            raise FileNotFoundError(f"Plugins directory not found: {self.plugins_dir}")

    @property
    def calibre_debug(self) -> Path:
        return self.calibre_path / "calibre-debug.exe"

    @property
    def ebook_convert(self) -> Path:
        return self.calibre_path / "ebook-convert.exe"

    def get_dedrm_config(self) -> Dict[str, Any]:
        """Get DeDRM configuration"""
        if self.dedrm_config_path.exists():
            with open(self.dedrm_config_path) as f:
                return json.load(f)
        return {}

    def get_dedrm_keys(self) -> Dict[str, List[str]]:
        """Get available DRM keys by type"""
        config = self.get_dedrm_config()
        return {
            "adobe": list(config.get("adeptkeys", {}).keys()),
            "kindle": list(config.get("kindlekeys", {}).keys()),
            "kobo": list(config.get("koboserial", {}).keys()),
            "barnes_noble": list(config.get("bnkeys", {}).keys()),
        }

    def detect_drm(self, file_path: str) -> DRMType:
        """
        Detect DRM type on an ebook.

        Args:
            file_path: Path to ebook file

        Returns:
            DRMType enum value
        """
        path = Path(file_path)
        if not path.exists():
            return DRMType.UNKNOWN

        ext = path.suffix.lower()

        # Simple detection based on file analysis
        try:
            with open(path, "rb") as f:
                header = f.read(1024)

            # Check for Adobe DRM markers
            if b"META-INF/rights.xml" in header or b"adept:resource" in header:
                return DRMType.ADOBE

            # Check for Kindle DRM
            if ext in [".azw", ".azw3", ".mobi"]:
                if b"EXTH" in header:
                    return DRMType.KINDLE

            # No DRM detected
            if ext in [".epub", ".pdf", ".mobi"]:
                return DRMType.NONE

        except Exception as e:
            logger.debug(f"DRM detection error: {e}")

        return DRMType.UNKNOWN

    def check_acsm(self, acsm_path: str) -> ACSMInfo:
        """
        Check ACSM file status and extract information.

        Args:
            acsm_path: Path to ACSM file

        Returns:
            ACSMInfo with status and details
        """
        path = Path(acsm_path)
        if not path.exists():
            return ACSMInfo(
                file_path=acsm_path, status=ACSMStatus.INVALID, message="File not found"
            )

        try:
            import xml.etree.ElementTree as ET

            tree = ET.parse(path)
            root = tree.getroot()

            # Extract namespace
            ns = {"adobe": "http://ns.adobe.com/adept"}

            # Get fulfillment info
            fulfillment_id = None
            expiration = None
            title = None

            for elem in root.iter():
                tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag

                if tag == "fulfillmentId":
                    fulfillment_id = elem.text
                elif tag == "expiration":
                    try:
                        # Parse ISO format: 2025-12-02T20:51:09+00:00
                        exp_str = elem.text
                        if exp_str:
                            exp_str = exp_str.replace("+00:00", "").replace("Z", "")
                            expiration = datetime.fromisoformat(exp_str)
                    except Exception:
                        pass
                elif tag == "dc:title" or tag == "title":
                    title = elem.text

            # Check expiration
            if expiration:
                if expiration < datetime.now():
                    return ACSMInfo(
                        file_path=acsm_path,
                        status=ACSMStatus.EXPIRED,
                        title=title,
                        fulfillment_id=fulfillment_id,
                        expiration=expiration,
                        message=f"ACSM expired on {expiration.isoformat()}",
                    )

            return ACSMInfo(
                file_path=acsm_path,
                status=ACSMStatus.VALID,
                title=title,
                fulfillment_id=fulfillment_id,
                expiration=expiration,
                message="ACSM is valid and can be fulfilled",
            )

        except Exception as e:
            return ACSMInfo(
                file_path=acsm_path,
                status=ACSMStatus.INVALID,
                message=f"Failed to parse ACSM: {e}",
            )

    def process_acsm(
        self, acsm_path: str, output_dir: Optional[Path] = None
    ) -> DRMResult:
        """
        Process ACSM file to EPUB using DeACSM plugin.

        Args:
            acsm_path: Path to ACSM file
            output_dir: Output directory for downloaded EPUB

        Returns:
            DRMResult with operation status
        """
        acsm_info = self.check_acsm(acsm_path)

        if acsm_info.status == ACSMStatus.EXPIRED:
            return DRMResult(
                success=False,
                input_file=acsm_path,
                drm_type=DRMType.ADOBE,
                message=f"ACSM expired: {acsm_info.message}",
            )

        if acsm_info.status != ACSMStatus.VALID:
            return DRMResult(
                success=False,
                input_file=acsm_path,
                drm_type=DRMType.ADOBE,
                message=f"Invalid ACSM: {acsm_info.message}",
            )

        output_dir = output_dir or self.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        # Use DeACSM through Calibre
        # DeACSM processes ACSM when adding to library
        try:
            from .calibre_manager import CalibreManager

            manager = CalibreManager()

            book_id = manager.add_book(acsm_path)
            if book_id:
                # Export the DRM-free version
                output_path = manager.export_book(book_id, output_dir, "epub")
                if output_path:
                    return DRMResult(
                        success=True,
                        input_file=acsm_path,
                        output_file=str(output_path),
                        drm_type=DRMType.ADOBE,
                        message="ACSM fulfilled and DRM removed successfully",
                    )

            return DRMResult(
                success=False,
                input_file=acsm_path,
                drm_type=DRMType.ADOBE,
                message="Failed to process ACSM through Calibre",
            )

        except Exception as e:
            return DRMResult(
                success=False,
                input_file=acsm_path,
                drm_type=DRMType.ADOBE,
                message=f"ACSM processing error: {e}",
            )

    def remove_drm(
        self, input_file: str, output_dir: Optional[Path] = None
    ) -> DRMResult:
        """
        Remove DRM from ebook by adding to Calibre (which triggers DeDRM).

        Args:
            input_file: Path to DRM-protected ebook
            output_dir: Output directory for DRM-free file

        Returns:
            DRMResult with operation status
        """
        path = Path(input_file)
        if not path.exists():
            return DRMResult(
                success=False, input_file=input_file, message="Input file not found"
            )

        drm_type = self.detect_drm(input_file)
        output_dir = output_dir or self.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            from .calibre_manager import CalibreManager

            manager = CalibreManager()

            # Adding book triggers DeDRM plugin
            book_id = manager.add_book(input_file)

            if book_id:
                # Get the format
                ext = path.suffix.lower().replace(".", "")
                output_path = manager.export_book(book_id, output_dir, ext)

                if output_path and output_path.exists():
                    # Verify DRM was removed by checking the output
                    new_drm = self.detect_drm(str(output_path))

                    if new_drm == DRMType.NONE:
                        return DRMResult(
                            success=True,
                            input_file=input_file,
                            output_file=str(output_path),
                            drm_type=drm_type,
                            message=f"DRM removed successfully ({drm_type.value})",
                        )
                    else:
                        return DRMResult(
                            success=False,
                            input_file=input_file,
                            output_file=str(output_path),
                            drm_type=drm_type,
                            message=f"DRM removal may have failed - output still shows {new_drm.value}",
                        )

            return DRMResult(
                success=False,
                input_file=input_file,
                drm_type=drm_type,
                message="Failed to add book to Calibre for DRM removal",
            )

        except Exception as e:
            return DRMResult(
                success=False,
                input_file=input_file,
                drm_type=drm_type,
                message=f"DRM removal error: {e}",
            )

    def batch_remove_drm(
        self, input_files: List[str], output_dir: Optional[Path] = None
    ) -> List[DRMResult]:
        """
        Remove DRM from multiple ebooks.

        Args:
            input_files: List of input file paths
            output_dir: Output directory

        Returns:
            List of DRMResult objects
        """
        results = []
        for file_path in input_files:
            ext = Path(file_path).suffix.lower()
            if ext == ".acsm":
                result = self.process_acsm(file_path, output_dir)
            else:
                result = self.remove_drm(file_path, output_dir)
            results.append(result)
        return results

    def add_adobe_key(self, key_path: str) -> Tuple[bool, str]:
        """
        Add Adobe key to DeDRM configuration.

        Args:
            key_path: Path to Adobe key file (.der)

        Returns:
            Tuple of (success, message)
        """
        if not Path(key_path).exists():
            return False, f"Key file not found: {key_path}"

        try:
            config = self.get_dedrm_config()
            if "adeptkeys" not in config:
                config["adeptkeys"] = {}

            key_name = Path(key_path).stem
            with open(key_path, "rb") as f:
                import base64

                key_data = base64.b64encode(f.read()).decode()

            config["adeptkeys"][key_name] = key_data

            with open(self.dedrm_config_path, "w") as f:
                json.dump(config, f, indent=2)

            return True, f"Added Adobe key: {key_name}"

        except Exception as e:
            return False, f"Failed to add key: {e}"

    def health_check(self) -> Dict[str, Any]:
        """Check DRM handler health and capabilities"""
        health = {
            "calibre_path": str(self.calibre_path),
            "calibre_installed": self.calibre_path.exists(),
            "plugins_dir_exists": self.plugins_dir.exists(),
            "dedrm_config_exists": self.dedrm_config_path.exists(),
            "deacsm_config_exists": self.deacsm_config_path.exists(),
            "output_dir": str(self.output_dir),
        }

        # Get key counts
        keys = self.get_dedrm_keys()
        health["keys"] = {k: len(v) for k, v in keys.items()}

        # Check for DeDRM/DeACSM plugins
        try:
            dedrm_plugin = self.plugins_dir / "DeDRM.zip"
            deacsm_plugin = self.plugins_dir / "DeACSM.zip"
            health["dedrm_plugin_exists"] = (
                dedrm_plugin.exists() or (self.plugins_dir / "dedrm").exists()
            )
            health["deacsm_plugin_exists"] = (
                deacsm_plugin.exists() or (self.plugins_dir / "deacsm").exists()
            )
        except Exception:
            health["dedrm_plugin_exists"] = False
            health["deacsm_plugin_exists"] = False

        health["status"] = (
            "healthy"
            if all(
                [
                    health["calibre_installed"],
                    health["plugins_dir_exists"],
                    health["dedrm_config_exists"],
                ]
            )
            else "degraded"
        )

        health["timestamp"] = datetime.now().isoformat()
        return health


def main():
    """Test DRM Handler"""
    handler = DRMHandler()

    # Health check
    print("=== DRM Handler Health ===")
    health = handler.health_check()
    print(json.dumps(health, indent=2))

    # Show available keys
    print("\n=== DRM Keys ===")
    keys = handler.get_dedrm_keys()
    for key_type, key_list in keys.items():
        if key_list:
            print(f"  {key_type}: {len(key_list)} key(s)")


if __name__ == "__main__":
    main()
