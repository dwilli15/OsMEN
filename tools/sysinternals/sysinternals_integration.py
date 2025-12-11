#!/usr/bin/env python3
"""
Sysinternals Integration
Provides programmatic access to Sysinternals Suite tools
"""

import csv
import json
import os
import platform
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class SysinternalsIntegration:
    """Integration with Microsoft Sysinternals Suite"""

    def __init__(self):
        self.sysinternals_path = Path(
            os.getenv("SYSINTERNALS_PATH", "C:\\Tools\\Sysinternals")
        )
        self.is_windows = platform.system() == "Windows"

    def _check_tool_exists(self, tool_name: str) -> bool:
        """Check if a Sysinternals tool exists"""
        tool_path = self.sysinternals_path / tool_name
        return tool_path.exists() if self.is_windows else False

    def _run_command(self, cmd: List[str], timeout: int = 300) -> tuple:
        """Run a command and return (returncode, stdout, stderr)"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=subprocess.CREATE_NO_WINDOW if self.is_windows else 0,
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"Command timed out after {timeout}s"
        except FileNotFoundError:
            return -2, "", f"Tool not found: {cmd[0]}"
        except Exception as e:
            return -3, "", str(e)

    def run_autoruns(self, output_file: Optional[str] = None) -> Dict:
        """Run Autoruns to analyze startup programs

        Uses autorunsc.exe (command-line version) to export autorun entries
        to CSV format for programmatic analysis.
        """
        autorunsc_exe = self.sysinternals_path / "autorunsc.exe"

        result = {
            "tool": "Autoruns",
            "timestamp": self._get_timestamp(),
            "status": "not_executed",
            "output_file": output_file,
            "findings": [],
            "error": None,
        }

        if not self.is_windows:
            result["error"] = "Sysinternals tools require Windows"
            return result

        if not self._check_tool_exists("autorunsc.exe"):
            result["error"] = f"autorunsc.exe not found at {autorunsc_exe}"
            result["status"] = "tool_missing"
            return result

        # Create temp file for output if not specified
        if not output_file:
            output_file = tempfile.mktemp(suffix=".csv", prefix="autoruns_")

        # Run autorunsc with CSV output
        # -a * = all entry types
        # -c = CSV output
        # -h = show file hashes
        # -s = verify digital signatures
        # -v = show VirusTotal detection
        # -accepteula = accept EULA automatically
        cmd = [
            str(autorunsc_exe),
            "-accepteula",
            "-a",
            "*",
            "-c",
            "-h",
            "-s",
            "-nobanner",
        ]

        returncode, stdout, stderr = self._run_command(cmd, timeout=120)

        if returncode == 0 and stdout:
            result["status"] = "executed"
            result["output_file"] = output_file

            # Write CSV output to file
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(stdout)

            # Parse CSV output for findings
            try:
                lines = stdout.strip().split("\n")
                if len(lines) > 1:
                    reader = csv.DictReader(lines)
                    for row in reader:
                        # Flag suspicious entries
                        entry = {
                            "location": row.get("Entry Location", ""),
                            "entry": row.get("Entry", ""),
                            "enabled": row.get("Enabled", ""),
                            "description": row.get("Description", ""),
                            "publisher": row.get("Publisher", ""),
                            "image_path": row.get("Image Path", ""),
                            "signer": row.get("Signer", ""),
                            "company": row.get("Company", ""),
                        }

                        # Flag entries without valid signatures
                        is_suspicious = (
                            entry["signer"] in ["(Not verified)", ""]
                            or not entry["publisher"]
                            or "temp" in entry["image_path"].lower()
                        )

                        if is_suspicious:
                            entry["suspicious"] = True
                            result["findings"].append(entry)

            except Exception as e:
                result["parse_error"] = str(e)
        else:
            result["status"] = "failed"
            result["error"] = stderr or "Unknown error"

        return result

    def run_process_monitor(
        self, duration_seconds: int = 60, output_file: Optional[str] = None
    ) -> Dict:
        """Run Process Monitor to capture system activity

        Uses procmon.exe with backing file to capture events for specified duration.
        """
        procmon_exe = self.sysinternals_path / "Procmon.exe"

        result = {
            "tool": "Process Monitor",
            "timestamp": self._get_timestamp(),
            "duration": duration_seconds,
            "status": "not_executed",
            "events_captured": 0,
            "output_file": output_file,
            "error": None,
        }

        if not self.is_windows:
            result["error"] = "Sysinternals tools require Windows"
            return result

        if not self._check_tool_exists("Procmon.exe"):
            result["error"] = f"Procmon.exe not found at {procmon_exe}"
            result["status"] = "tool_missing"
            return result

        # Create temp file for output if not specified
        if not output_file:
            output_file = tempfile.mktemp(suffix=".pml", prefix="procmon_")

        try:
            # Start Process Monitor with backing file
            # /Quiet = don't show UI
            # /Minimized = minimize on start
            # /BackingFile = file to save events
            # /AcceptEula = accept EULA
            start_cmd = [
                str(procmon_exe),
                "/AcceptEula",
                "/Quiet",
                "/Minimized",
                "/BackingFile",
                output_file,
            ]

            # Start procmon
            proc = subprocess.Popen(
                start_cmd,
                creationflags=subprocess.CREATE_NO_WINDOW if self.is_windows else 0,
            )

            result["status"] = "running"

            # Wait for specified duration
            import time

            time.sleep(duration_seconds)

            # Terminate procmon
            stop_cmd = [str(procmon_exe), "/Terminate"]
            subprocess.run(
                stop_cmd,
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW if self.is_windows else 0,
            )

            result["status"] = "executed"
            result["output_file"] = output_file

            # Get file size as proxy for events captured
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                # Rough estimate: ~1KB per event
                result["events_captured"] = file_size // 1024

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)

        return result

    def run_process_explorer(self) -> Dict:
        """Launch Process Explorer for interactive use"""
        procexp_exe = self.sysinternals_path / "procexp.exe"

        result = {
            "tool": "Process Explorer",
            "timestamp": self._get_timestamp(),
            "status": "not_executed",
            "error": None,
        }

        if not self.is_windows:
            result["error"] = "Sysinternals tools require Windows"
            return result

        if not self._check_tool_exists("procexp.exe"):
            result["error"] = f"procexp.exe not found at {procexp_exe}"
            result["status"] = "tool_missing"
            return result

        try:
            # Launch Process Explorer (non-blocking)
            subprocess.Popen(
                [str(procexp_exe), "/accepteula"],
                creationflags=subprocess.CREATE_NO_WINDOW if self.is_windows else 0,
            )
            result["status"] = "launched"
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)

        return result

    def run_tcpview(self) -> Dict:
        """Launch TCPView to monitor network connections"""
        tcpview_exe = self.sysinternals_path / "Tcpview.exe"

        result = {
            "tool": "TCPView",
            "timestamp": self._get_timestamp(),
            "status": "not_executed",
            "error": None,
        }

        if not self.is_windows:
            result["error"] = "Sysinternals tools require Windows"
            return result

        if not self._check_tool_exists("Tcpview.exe"):
            result["error"] = f"Tcpview.exe not found at {tcpview_exe}"
            result["status"] = "tool_missing"
            return result

        try:
            subprocess.Popen(
                [str(tcpview_exe), "/accepteula"],
                creationflags=subprocess.CREATE_NO_WINDOW if self.is_windows else 0,
            )
            result["status"] = "launched"
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)

        return result

    def run_rootkit_revealer(self) -> Dict:
        """Run RootkitRevealer for rootkit detection

        Note: RootkitRevealer is deprecated but still useful.
        Consider using other tools like GMER for modern systems.
        """
        rootkit_exe = self.sysinternals_path / "RootkitRevealer.exe"

        result = {
            "tool": "RootkitRevealer",
            "timestamp": self._get_timestamp(),
            "status": "not_executed",
            "threats_found": 0,
            "findings": [],
            "error": None,
            "warning": "RootkitRevealer is deprecated. Consider using modern alternatives.",
        }

        if not self.is_windows:
            result["error"] = "Sysinternals tools require Windows"
            return result

        if not self._check_tool_exists("RootkitRevealer.exe"):
            result["error"] = f"RootkitRevealer.exe not found at {rootkit_exe}"
            result["status"] = "tool_missing"
            return result

        # Create temp file for output
        output_file = tempfile.mktemp(suffix=".log", prefix="rootkit_")

        try:
            cmd = [
                str(rootkit_exe),
                "-accepteula",
                "-a",  # Scan everything
                "-c",
                output_file,  # Save to file
            ]

            returncode, stdout, stderr = self._run_command(cmd, timeout=600)

            if returncode == 0:
                result["status"] = "executed"

                # Parse output file for findings
                if os.path.exists(output_file):
                    with open(output_file, "r") as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("Rootkit"):
                                result["findings"].append(line)
                                result["threats_found"] += 1
            else:
                result["status"] = "failed"
                result["error"] = stderr or "Unknown error"

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)

        return result

    def get_listdlls(self, process_name: Optional[str] = None) -> Dict:
        """List DLLs loaded by processes using ListDLLs"""
        listdlls_exe = self.sysinternals_path / "listdlls.exe"

        result = {
            "tool": "ListDLLs",
            "timestamp": self._get_timestamp(),
            "process": process_name or "all",
            "status": "not_executed",
            "dlls": [],
            "error": None,
        }

        if not self.is_windows:
            result["error"] = "Sysinternals tools require Windows"
            return result

        if not self._check_tool_exists("listdlls.exe"):
            result["status"] = "tool_missing"
            return result

        cmd = [str(listdlls_exe), "-accepteula"]
        if process_name:
            cmd.append(process_name)

        returncode, stdout, stderr = self._run_command(cmd, timeout=60)

        if returncode == 0:
            result["status"] = "executed"
            # Parse output (basic parsing, could be enhanced)
            lines = stdout.strip().split("\n")
            for line in lines:
                if ".dll" in line.lower():
                    result["dlls"].append(line.strip())
        else:
            result["status"] = "failed"
            result["error"] = stderr

        return result

    def get_handle(
        self, process_name: Optional[str] = None, file_or_dir: Optional[str] = None
    ) -> Dict:
        """List open handles using Handle"""
        handle_exe = self.sysinternals_path / "handle.exe"

        result = {
            "tool": "Handle",
            "timestamp": self._get_timestamp(),
            "filter": process_name or file_or_dir or "none",
            "status": "not_executed",
            "handles": [],
            "error": None,
        }

        if not self.is_windows:
            result["error"] = "Sysinternals tools require Windows"
            return result

        if not self._check_tool_exists("handle.exe"):
            result["status"] = "tool_missing"
            return result

        cmd = [str(handle_exe), "-accepteula", "-nobanner"]
        if process_name:
            cmd.extend(["-p", process_name])
        if file_or_dir:
            cmd.append(file_or_dir)

        returncode, stdout, stderr = self._run_command(cmd, timeout=60)

        if returncode == 0:
            result["status"] = "executed"
            result["handles"] = [
                line.strip() for line in stdout.strip().split("\n") if line.strip()
            ]
        else:
            result["status"] = "failed"
            result["error"] = stderr

        return result

    def analyze_system_health(self) -> Dict:
        """Comprehensive system health analysis using multiple tools"""
        analysis = {
            "timestamp": self._get_timestamp(),
            "platform": platform.system(),
            "sysinternals_path": str(self.sysinternals_path),
            "tools_available": {},
            "autoruns": None,
            "recommendations": [],
        }

        # Check which tools are available
        tools = [
            "autorunsc.exe",
            "Procmon.exe",
            "procexp.exe",
            "Tcpview.exe",
            "handle.exe",
            "listdlls.exe",
            "RootkitRevealer.exe",
        ]
        for tool in tools:
            analysis["tools_available"][tool] = self._check_tool_exists(tool)

        if not self.is_windows:
            analysis["recommendations"].append(
                "Run on Windows for full Sysinternals support"
            )
            return analysis

        # Run autoruns analysis if available
        if analysis["tools_available"].get("autorunsc.exe"):
            analysis["autoruns"] = self.run_autoruns()

            # Generate recommendations based on findings
            if analysis["autoruns"].get("findings"):
                num_suspicious = len(analysis["autoruns"]["findings"])
                analysis["recommendations"].append(
                    f"Review {num_suspicious} suspicious startup entries in Autoruns output"
                )
        else:
            analysis["recommendations"].append(
                f"Install Sysinternals Suite to {self.sysinternals_path} for startup analysis"
            )

        # Add general recommendations
        analysis["recommendations"].extend(
            [
                "Run Process Monitor to capture system activity during suspicious behavior",
                "Use Process Explorer to identify hidden or malicious processes",
                "Check TCPView for unexpected network connections",
                "Regularly review startup entries with Autoruns",
            ]
        )

        return analysis

    def get_available_tools(self) -> Dict[str, bool]:
        """Get a dictionary of available Sysinternals tools"""
        tools = {
            "autorunsc.exe": "Startup program analyzer (CLI)",
            "Autoruns.exe": "Startup program analyzer (GUI)",
            "Procmon.exe": "Process Monitor",
            "procexp.exe": "Process Explorer",
            "Tcpview.exe": "TCP/UDP connection viewer",
            "handle.exe": "Handle viewer",
            "listdlls.exe": "DLL lister",
            "RootkitRevealer.exe": "Rootkit detector (deprecated)",
            "PsExec.exe": "Remote execution",
            "PsInfo.exe": "System information",
            "PsList.exe": "Process list",
            "PsService.exe": "Service manager",
            "Sigcheck.exe": "Signature checker",
            "strings.exe": "String extractor",
            "AccessChk.exe": "Access rights checker",
        }

        return {
            tool: {
                "available": self._check_tool_exists(tool),
                "description": desc,
                "path": str(self.sysinternals_path / tool),
            }
            for tool, desc in tools.items()
        }

    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp"""
        return datetime.now().isoformat()


def main():
    """Test the integration"""
    integration = SysinternalsIntegration()

    print("=== Sysinternals Integration Test ===\n")

    # Check available tools
    print("Available Tools:")
    tools = integration.get_available_tools()
    for tool, info in tools.items():
        status = "✓" if info["available"] else "✗"
        print(f"  {status} {tool}: {info['description']}")

    print("\n--- System Health Analysis ---")
    analysis = integration.analyze_system_health()
    print(json.dumps(analysis, indent=2, default=str))


if __name__ == "__main__":
    main()
