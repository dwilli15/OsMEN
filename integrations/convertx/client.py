"""
ConvertX Client - Python SDK for file format conversion
========================================================

Provides a clean interface to the ConvertX service for file conversions.
Supports both synchronous and async operations.
"""

import asyncio
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import aiohttp
import requests

logger = logging.getLogger(__name__)

CONVERTX_URL = os.getenv("CONVERTX_URL", "http://localhost:3000")


@dataclass
class ConversionResult:
    """Result of a file conversion operation."""

    success: bool
    output_path: Optional[str] = None
    original_format: Optional[str] = None
    target_format: Optional[str] = None
    error: Optional[str] = None
    job_id: Optional[str] = None
    duration_seconds: float = 0.0


class ConvertXClient:
    """
    ConvertX API Client for file format conversions.

    Supports 1000+ file formats including:
    - Video: mp4, mkv, avi, webm, mov, etc. (FFmpeg)
    - Audio: mp3, wav, flac, aac, ogg, etc. (FFmpeg)
    - Images: jpg, png, webp, heic, avif, svg, etc. (Vips, GraphicsMagick)
    - Documents: pdf, docx, md, html, epub, etc. (Pandoc, Calibre)
    - 3D Models: obj, stl, fbx, gltf, etc. (Assimp)
    - LaTeX: tex to pdf (XeLaTeX)

    Usage:
        client = ConvertXClient()
        result = client.convert("video.mp4", "webm")
        print(result.output_path)
    """

    def __init__(self, base_url: str = None, timeout: int = 300):
        """
        Initialize ConvertX client.

        Args:
            base_url: ConvertX service URL (default: http://localhost:3000)
            timeout: Request timeout in seconds (default: 300 for large files)
        """
        self.base_url = (base_url or CONVERTX_URL).rstrip("/")
        self.timeout = timeout
        self.session: Optional[requests.Session] = None
        self._auth_cookie = None

    def _get_session(self) -> requests.Session:
        """Get or create requests session."""
        if self.session is None:
            self.session = requests.Session()
            self.session.timeout = self.timeout
        return self.session

    def health_check(self) -> bool:
        """Check if ConvertX service is healthy."""
        try:
            resp = requests.get(f"{self.base_url}/", timeout=5)
            return resp.status_code == 200
        except Exception as e:
            logger.warning(f"ConvertX health check failed: {e}")
            return False

    def get_converters(self) -> Dict[str, Any]:
        """
        Get list of available converters and their supported formats.

        Returns:
            Dict with converter names as keys and format info as values
        """
        try:
            resp = self._get_session().get(f"{self.base_url}/converters")
            if resp.status_code == 200:
                # Parse HTML response to extract converter info
                # ConvertX returns HTML, not JSON for this endpoint
                return {"status": "ok", "html": resp.text}
            return {"error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    def convert(
        self,
        input_path: Union[str, Path],
        target_format: str,
        output_path: Optional[Union[str, Path]] = None,
        wait: bool = True,
        poll_interval: float = 1.0,
    ) -> ConversionResult:
        """
        Convert a file to a different format.

        Args:
            input_path: Path to input file
            target_format: Target format extension (e.g., 'webm', 'pdf', 'png')
            output_path: Optional output path (auto-generated if not provided)
            wait: Wait for conversion to complete (default: True)
            poll_interval: Seconds between status checks when waiting

        Returns:
            ConversionResult with success status and output path
        """
        start_time = time.time()
        input_path = Path(input_path)

        if not input_path.exists():
            return ConversionResult(
                success=False,
                error=f"Input file not found: {input_path}",
                original_format=input_path.suffix.lstrip("."),
                target_format=target_format,
            )

        # Generate output path if not provided
        if output_path is None:
            output_path = input_path.with_suffix(f".{target_format.lstrip('.')}")
        else:
            output_path = Path(output_path)

        original_format = input_path.suffix.lstrip(".")
        session = self._get_session()

        try:
            # Step 1: Upload file
            logger.info(f"Uploading {input_path.name} to ConvertX...")
            with open(input_path, "rb") as f:
                files = {"file": (input_path.name, f)}
                upload_resp = session.post(
                    f"{self.base_url}/upload",
                    files=files,
                )

            if upload_resp.status_code not in (200, 302):
                return ConversionResult(
                    success=False,
                    error=f"Upload failed: HTTP {upload_resp.status_code}",
                    original_format=original_format,
                    target_format=target_format,
                    duration_seconds=time.time() - start_time,
                )

            # Step 2: Request conversion
            logger.info(f"Requesting conversion to {target_format}...")
            convert_data = {
                "convert_to": target_format.lstrip("."),
                "file_names": input_path.name,
            }
            convert_resp = session.post(
                f"{self.base_url}/convert",
                data=convert_data,
                allow_redirects=False,
            )

            # Extract job ID from redirect URL
            job_id = None
            if convert_resp.status_code == 302:
                location = convert_resp.headers.get("Location", "")
                if "/results/" in location:
                    job_id = location.split("/results/")[-1]

            if not job_id:
                return ConversionResult(
                    success=False,
                    error="Failed to start conversion job",
                    original_format=original_format,
                    target_format=target_format,
                    duration_seconds=time.time() - start_time,
                )

            logger.info(f"Conversion job started: {job_id}")

            # Step 3: Wait for completion if requested
            if wait:
                completed = self._wait_for_completion(session, job_id, poll_interval)
                if not completed:
                    return ConversionResult(
                        success=False,
                        error="Conversion timed out or failed",
                        original_format=original_format,
                        target_format=target_format,
                        job_id=job_id,
                        duration_seconds=time.time() - start_time,
                    )

            # Step 4: Download result
            # Get user ID from session (simplified - using "1" for unauthenticated)
            user_id = "1"
            output_filename = f"{input_path.stem}.{target_format.lstrip('.')}"
            download_url = (
                f"{self.base_url}/download/{user_id}/{job_id}/{output_filename}"
            )

            logger.info(f"Downloading converted file...")
            download_resp = session.get(download_url)

            if download_resp.status_code == 200:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(download_resp.content)

                logger.info(f"Conversion complete: {output_path}")
                return ConversionResult(
                    success=True,
                    output_path=str(output_path),
                    original_format=original_format,
                    target_format=target_format,
                    job_id=job_id,
                    duration_seconds=time.time() - start_time,
                )
            else:
                return ConversionResult(
                    success=False,
                    error=f"Download failed: HTTP {download_resp.status_code}",
                    original_format=original_format,
                    target_format=target_format,
                    job_id=job_id,
                    duration_seconds=time.time() - start_time,
                )

        except Exception as e:
            logger.error(f"Conversion error: {e}")
            return ConversionResult(
                success=False,
                error=str(e),
                original_format=original_format,
                target_format=target_format,
                duration_seconds=time.time() - start_time,
            )

    def _wait_for_completion(
        self,
        session: requests.Session,
        job_id: str,
        poll_interval: float,
        max_wait: int = None,
    ) -> bool:
        """Wait for conversion job to complete."""
        max_wait = max_wait or self.timeout
        start = time.time()

        while time.time() - start < max_wait:
            try:
                resp = session.post(f"{self.base_url}/progress/{job_id}")
                if resp.status_code == 200:
                    # Check if conversion is complete (look for download links in HTML)
                    if (
                        "download" in resp.text.lower()
                        and "pending" not in resp.text.lower()
                    ):
                        return True
                    if "completed" in resp.text.lower():
                        return True
            except Exception as e:
                logger.warning(f"Progress check failed: {e}")

            time.sleep(poll_interval)

        return False

    def close(self):
        """Close the client session."""
        if self.session:
            self.session.close()
            self.session = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class AsyncConvertXClient:
    """
    Async version of ConvertX client for concurrent conversions.
    """

    def __init__(self, base_url: str = None, timeout: int = 300):
        self.base_url = (base_url or CONVERTX_URL).rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self._session

    async def health_check(self) -> bool:
        """Check if ConvertX service is healthy."""
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/") as resp:
                return resp.status == 200
        except Exception:
            return False

    async def convert(
        self,
        input_path: Union[str, Path],
        target_format: str,
        output_path: Optional[Union[str, Path]] = None,
    ) -> ConversionResult:
        """
        Convert a file asynchronously.

        Args:
            input_path: Path to input file
            target_format: Target format extension
            output_path: Optional output path

        Returns:
            ConversionResult with success status and output path
        """
        start_time = time.time()
        input_path = Path(input_path)

        if not input_path.exists():
            return ConversionResult(
                success=False,
                error=f"Input file not found: {input_path}",
            )

        if output_path is None:
            output_path = input_path.with_suffix(f".{target_format.lstrip('.')}")
        else:
            output_path = Path(output_path)

        original_format = input_path.suffix.lstrip(".")
        session = await self._get_session()

        try:
            # Upload file
            data = aiohttp.FormData()
            data.add_field(
                "file",
                open(input_path, "rb"),
                filename=input_path.name,
            )

            async with session.post(f"{self.base_url}/upload", data=data) as resp:
                if resp.status not in (200, 302):
                    return ConversionResult(
                        success=False,
                        error=f"Upload failed: HTTP {resp.status}",
                        original_format=original_format,
                        target_format=target_format,
                    )

            # Request conversion
            convert_data = {
                "convert_to": target_format.lstrip("."),
                "file_names": input_path.name,
            }
            async with session.post(
                f"{self.base_url}/convert",
                data=convert_data,
                allow_redirects=False,
            ) as resp:
                job_id = None
                if resp.status == 302:
                    location = resp.headers.get("Location", "")
                    if "/results/" in location:
                        job_id = location.split("/results/")[-1]

            if not job_id:
                return ConversionResult(
                    success=False,
                    error="Failed to start conversion",
                    original_format=original_format,
                    target_format=target_format,
                )

            # Wait for completion
            await self._wait_for_completion(session, job_id)

            # Download result
            user_id = "1"
            output_filename = f"{input_path.stem}.{target_format.lstrip('.')}"
            download_url = (
                f"{self.base_url}/download/{user_id}/{job_id}/{output_filename}"
            )

            async with session.get(download_url) as resp:
                if resp.status == 200:
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, "wb") as f:
                        f.write(await resp.read())

                    return ConversionResult(
                        success=True,
                        output_path=str(output_path),
                        original_format=original_format,
                        target_format=target_format,
                        job_id=job_id,
                        duration_seconds=time.time() - start_time,
                    )
                else:
                    return ConversionResult(
                        success=False,
                        error=f"Download failed: HTTP {resp.status}",
                        original_format=original_format,
                        target_format=target_format,
                        job_id=job_id,
                        duration_seconds=time.time() - start_time,
                    )

        except Exception as e:
            return ConversionResult(
                success=False,
                error=str(e),
                original_format=original_format,
                target_format=target_format,
                duration_seconds=time.time() - start_time,
            )

    async def _wait_for_completion(self, session: aiohttp.ClientSession, job_id: str):
        """Wait for job to complete."""
        max_wait = self.timeout.total or 300
        start = time.time()

        while time.time() - start < max_wait:
            try:
                async with session.post(f"{self.base_url}/progress/{job_id}") as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        if "download" in text.lower() and "pending" not in text.lower():
                            return
                        if "completed" in text.lower():
                            return
            except Exception:
                pass

            await asyncio.sleep(1.0)

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()


# Convenience functions
def convert_file(
    input_path: Union[str, Path],
    target_format: str,
    output_path: Optional[Union[str, Path]] = None,
) -> ConversionResult:
    """
    Quick function to convert a file.

    Args:
        input_path: Path to input file
        target_format: Target format (e.g., 'pdf', 'mp4', 'png')
        output_path: Optional output path

    Returns:
        ConversionResult

    Example:
        result = convert_file("document.docx", "pdf")
        if result.success:
            print(f"Saved to: {result.output_path}")
    """
    with ConvertXClient() as client:
        return client.convert(input_path, target_format, output_path)


def get_supported_formats() -> Dict[str, Any]:
    """
    Get information about supported file formats.

    Returns:
        Dict with converter information
    """
    with ConvertXClient() as client:
        return client.get_converters()
        return client.get_converters()
