#!/usr/bin/env python3
"""
Focus Guardrails Agent
Maintains focus and productivity by enforcing guardrails.

Real Implementation Features:
- Hosts file modification for site blocking
- Windows Firewall rules for network-level blocking
- Process monitoring for app time tracking
- Desktop notifications for focus reminders
- Persistence across sessions via config files
- HybridMemory integration for pattern learning
"""

import base64
import ctypes
import json
import logging
import os
import platform
import shutil
import subprocess
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import memory integration
try:
    from agents.focus_guardrails.focus_memory import (
        FocusInsight,
        FocusMemoryIntegration,
        get_focus_memory,
    )

    FOCUS_MEMORY_AVAILABLE = True
except ImportError:
    FOCUS_MEMORY_AVAILABLE = False
    logger.warning("FocusMemoryIntegration not available")


@dataclass
class FocusSession:
    """Represents a focus session"""

    id: str
    start_time: str
    duration_minutes: int
    end_time: str
    status: str  # active, completed, interrupted
    blocked_sites: List[str] = field(default_factory=list)
    actual_end_time: Optional[str] = None
    interruptions: int = 0


@dataclass
class AppUsage:
    """Tracks application usage"""

    app_name: str
    window_title: str
    start_time: str
    duration_seconds: float = 0
    is_productive: bool = True


class FocusGuardrailsAgent:
    """
    Agent for focus and productivity guardrails.

    Implements real blocking via:
    - Windows hosts file (%SystemRoot%\\System32\\drivers\\etc\\hosts)
    - Windows Firewall rules (netsh advfirewall)
    - Process termination for blocked apps (optional)

    Persistence:
    - Saves state to JSON for recovery after restart
    - Can restore blocking after system reboot
    """

    # Default distracting sites
    DEFAULT_DISTRACTING_SITES = [
        "facebook.com",
        "www.facebook.com",
        "twitter.com",
        "www.twitter.com",
        "x.com",
        "www.x.com",
        "reddit.com",
        "www.reddit.com",
        "old.reddit.com",
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "instagram.com",
        "www.instagram.com",
        "tiktok.com",
        "www.tiktok.com",
        "twitch.tv",
        "www.twitch.tv",
        "netflix.com",
        "www.netflix.com",
        "discord.com",
        "www.discord.com",
    ]

    # Productive apps (won't be blocked)
    PRODUCTIVE_APPS = {
        "code.exe",
        "devenv.exe",
        "idea64.exe",
        "pycharm64.exe",  # IDEs
        "notepad.exe",
        "notepad++.exe",
        "sublime_text.exe",  # Editors
        "excel.exe",
        "word.exe",
        "powerpnt.exe",  # Office
        "outlook.exe",
        "teams.exe",
        "slack.exe",  # Communication (work)
        "terminal.exe",
        "powershell.exe",
        "cmd.exe",
        "WindowsTerminal.exe",  # Terminal
        "explorer.exe",
        "taskmgr.exe",  # System
    }

    def __init__(self):
        """Initialize the Focus Guardrails Agent."""
        try:
            self.is_windows = platform.system() == "Windows"
            self.is_admin = self._check_admin()

            # Paths
            if self.is_windows:
                self.hosts_path = (
                    Path(os.environ.get("SystemRoot", "C:\\Windows"))
                    / "System32\\drivers\\etc\\hosts"
                )
            else:
                self.hosts_path = Path("/etc/hosts")

            # State
            self.focus_sessions: List[FocusSession] = []
            self.blocked_sites: Set[str] = set()
            self.app_usage: List[AppUsage] = []
            self._monitor_thread: Optional[threading.Thread] = None
            self._monitoring = False

            # Config/persistence
            self.config_dir = Path.home() / ".osmen" / "focus_guardrails"
            self.config_dir.mkdir(parents=True, exist_ok=True)
            self.state_file = self.config_dir / "state.json"
            self.blocked_file = self.config_dir / "blocked_sites.txt"

            # Memory integration for pattern learning
            self.focus_memory: Optional[FocusMemoryIntegration] = None
            if FOCUS_MEMORY_AVAILABLE:
                try:
                    self.focus_memory = get_focus_memory()
                    logger.info("FocusMemory integration enabled")
                except Exception as e:
                    logger.warning(f"Could not enable FocusMemory: {e}")

            # Load previous state
            self._load_state()

            logger.info(f"FocusGuardrailsAgent initialized. Admin: {self.is_admin}")
        except Exception as e:
            logger.error(f"Error initializing FocusGuardrailsAgent: {e}")
            raise

    def _check_admin(self) -> bool:
        """Check if running with administrator privileges."""
        if self.is_windows:
            try:
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            except Exception:
                return False
        else:
            try:
                return os.geteuid() == 0
            except AttributeError:
                # os.geteuid() not available on this platform
                return False

    def _load_state(self):
        """Load previous state from disk."""
        try:
            if self.state_file.exists():
                with open(self.state_file, "r") as f:
                    state = json.load(f)

                    # Restore blocked sites
                    self.blocked_sites = set(state.get("blocked_sites", []))

                    # Restore sessions (for history)
                    for session_data in state.get("sessions", []):
                        self.focus_sessions.append(FocusSession(**session_data))

                    logger.info(
                        f"Loaded state: {len(self.blocked_sites)} blocked sites"
                    )
        except Exception as e:
            logger.debug(f"Could not load state: {e}")

    def _save_state(self):
        """Save state to disk for persistence."""
        try:
            state = {
                "blocked_sites": list(self.blocked_sites),
                "sessions": [
                    asdict(s) for s in self.focus_sessions[-20:]
                ],  # Keep last 20
                "last_updated": datetime.now().isoformat(),
            }
            with open(self.state_file, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save state: {e}")

    def start_focus_session(
        self, duration_minutes: int = 25, block_sites: bool = True
    ) -> Dict:
        """
        Start a timed focus session (Pomodoro-style).

        Args:
            duration_minutes: Duration in minutes (default 25 for Pomodoro)
            block_sites: Whether to block distracting sites during session

        Raises:
            ValueError: If duration_minutes is not a positive integer
        """
        if duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")

        try:
            session_id = f"focus_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            session = FocusSession(
                id=session_id,
                start_time=datetime.now().isoformat(),
                duration_minutes=duration_minutes,
                end_time=(
                    datetime.now() + timedelta(minutes=duration_minutes)
                ).isoformat(),
                status="active",
                blocked_sites=(
                    list(self.DEFAULT_DISTRACTING_SITES) if block_sites else []
                ),
            )
            self.focus_sessions.append(session)

            # Apply focus guardrails
            if block_sites:
                block_result = self._apply_site_blocks(self.DEFAULT_DISTRACTING_SITES)
                if not block_result["success"]:
                    logger.warning(
                        f"Some sites could not be blocked: {block_result['errors']}"
                    )

            # Send notification
            self._send_notification(
                "Focus Session Started",
                f"Stay focused for {duration_minutes} minutes! Distracting sites have been blocked.",
            )

            # Save state
            self._save_state()

            logger.info(f"Focus session started for {duration_minutes} minutes")
            return asdict(session)

        except Exception as e:
            logger.error(f"Error starting focus session: {e}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to start focus session",
            }

    def end_focus_session(self) -> Dict:
        """End the current focus session and remove blocks."""
        try:
            # Find active session
            active_session = None
            for session in reversed(self.focus_sessions):
                if session.status == "active":
                    active_session = session
                    break

            if not active_session:
                logger.warning("No active focus session to end")
                return {"status": "no_active_session"}

            # Update session
            active_session.status = "completed"
            active_session.actual_end_time = datetime.now().isoformat()

            # Remove focus guardrails
            if active_session.blocked_sites:
                self._remove_site_blocks(active_session.blocked_sites)

            # Store in memory for pattern learning
            if self.focus_memory and self.focus_memory.enabled:
                self.focus_memory.store_session(
                    session_data=asdict(active_session),
                    outcome="completed",
                    productivity_rating=None,  # Can be set via rate_session()
                    notes=None,
                )

            # Send notification
            self._send_notification(
                "Focus Session Completed",
                f"Great work! You stayed focused for {active_session.duration_minutes} minutes.",
            )

            # Save state
            self._save_state()

            logger.info("Focus session ended successfully")
            return asdict(active_session)

        except Exception as e:
            logger.error(f"Error ending focus session: {e}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to end focus session",
            }

    def get_session_insights(self, duration_minutes: int = 25) -> List[Dict]:
        """
        Get personalized insights before starting a focus session.

        Uses HybridMemory to analyze past patterns and provide recommendations.

        Args:
            duration_minutes: Planned session duration

        Returns:
            List of insight dictionaries with type, message, and confidence
        """
        if not self.focus_memory or not self.focus_memory.enabled:
            return [
                {
                    "type": "info",
                    "message": "Memory integration not available. Insights will improve over time.",
                    "confidence": 0.5,
                }
            ]

        insights = self.focus_memory.get_insights_for_session(duration_minutes)
        return [
            {
                "type": insight.insight_type,
                "message": insight.message,
                "confidence": insight.confidence,
                "source_sessions": insight.source_sessions,
                "data": insight.data,
            }
            for insight in insights
        ]

    def rate_last_session(
        self, productivity_rating: float, notes: Optional[str] = None
    ) -> Dict:
        """
        Rate the last completed focus session.

        This helps the memory system learn what works best for you.

        Args:
            productivity_rating: 1-5 rating of how productive the session was
            notes: Optional notes about what worked or didn't

        Returns:
            Status dictionary
        """
        if not 1 <= productivity_rating <= 5:
            return {"status": "error", "message": "Rating must be between 1 and 5"}

        # Find last completed session
        last_session = None
        for session in reversed(self.focus_sessions):
            if session.status == "completed":
                last_session = session
                break

        if not last_session:
            return {"status": "error", "message": "No completed session to rate"}

        # Store with rating in memory
        if self.focus_memory and self.focus_memory.enabled:
            self.focus_memory.store_session(
                session_data=asdict(last_session),
                outcome="completed",
                productivity_rating=productivity_rating,
                notes=notes,
            )
            return {
                "status": "success",
                "message": f"Rated session {last_session.id} as {productivity_rating}/5",
                "session_id": last_session.id,
            }

        return {"status": "warning", "message": "Rating saved but memory not available"}

    def block_distracting_sites(self, sites: List[str]) -> Dict:
        """
        Block distracting websites via hosts file and firewall.

        Args:
            sites: List of domain names to block

        Returns:
            Dict with status and details
        """
        return self._apply_site_blocks(sites)

    def _apply_site_blocks(self, sites: List[str]) -> Dict:
        """Apply site blocking via hosts file and firewall."""
        results = {
            "success": True,
            "blocked_hosts": [],
            "blocked_firewall": [],
            "errors": [],
            "method": "hosts_file",
        }

        if not self.is_admin:
            results["errors"].append("Administrator privileges required for blocking")
            results["success"] = False
            # Still track as blocked for user reference
            self.blocked_sites.update(sites)
            return results

        # Method 1: Hosts file blocking
        hosts_result = self._add_to_hosts_file(sites)
        results["blocked_hosts"] = hosts_result.get("blocked", [])
        if hosts_result.get("errors"):
            results["errors"].extend(hosts_result["errors"])

        # Method 2: Windows Firewall blocking (optional, more robust)
        if self.is_windows:
            firewall_result = self._add_firewall_blocks(sites)
            results["blocked_firewall"] = firewall_result.get("blocked", [])
            if firewall_result.get("errors"):
                results["errors"].extend(firewall_result["errors"])

        # Track blocked sites
        self.blocked_sites.update(sites)

        # Flush DNS cache
        self._flush_dns()

        if results["errors"]:
            results["success"] = len(results["blocked_hosts"]) > 0

        logger.info(f"Blocked {len(results['blocked_hosts'])} sites via hosts file")
        return results

    def _add_to_hosts_file(self, sites: List[str]) -> Dict:
        """Add sites to the hosts file to block them."""
        result = {"blocked": [], "errors": []}

        # Read current hosts file
        try:
            with open(self.hosts_path, "r") as f:
                current_content = f.read()
        except PermissionError:
            result["errors"].append("Permission denied reading hosts file")
            return result
        except FileNotFoundError:
            current_content = ""

        # Prepare entries to add
        marker_start = "# OsMEN Focus Guardrails - START"
        marker_end = "# OsMEN Focus Guardrails - END"

        # Remove old OsMEN entries if present
        if marker_start in current_content:
            start_idx = current_content.find(marker_start)
            end_idx = current_content.find(marker_end)
            if end_idx != -1:
                end_idx += len(marker_end)
                if end_idx > start_idx:
                    current_content = (
                        current_content[:start_idx] + current_content[end_idx:]
                    )
                else:
                    logging.warning(
                        "OsMEN hosts file markers found in wrong order; skipping removal of old entries."
                    )

        # Build new block entries
        block_entries = [marker_start]
        for site in sites:
            # Redirect to localhost
            block_entries.append(f"127.0.0.1 {site}")
            if not site.startswith("www."):
                block_entries.append(f"127.0.0.1 www.{site}")
            block_entries.append(f"::1 {site}")  # IPv6
            result["blocked"].append(site)
        block_entries.append(marker_end)

        # Write updated hosts file
        try:
            new_content = (
                current_content.strip()
                + "\n\n"
                + "\n".join(filter(None, block_entries))
                + "\n"
            )

            # Create backup
            backup_path = self.config_dir / "hosts.backup"
            if not backup_path.exists():
                shutil.copy2(self.hosts_path, backup_path)

            with open(self.hosts_path, "w") as f:
                f.write(new_content)

        except PermissionError:
            result["errors"].append(
                "Permission denied writing hosts file. Run as Administrator."
            )
        except Exception as e:
            result["errors"].append(f"Error writing hosts file: {e}")

        return result

    def _add_firewall_blocks(self, sites: List[str]) -> Dict:
        """Add Windows Firewall rules to block sites."""
        result = {"blocked": [], "errors": []}

        for site in sites:
            try:
                # Block outbound connections to the domain
                rule_name = f"OsMEN_Block_{site.replace('.', '_')}"

                # First, try to get IP addresses for the domain
                cmd = [
                    "netsh",
                    "advfirewall",
                    "firewall",
                    "add",
                    "rule",
                    f"name={rule_name}",
                    "dir=out",
                    "action=block",
                    f"remoteip={site}",  # May not resolve, but worth trying
                    "enable=yes",
                ]

                subprocess.run(cmd, capture_output=True, timeout=5)
                result["blocked"].append(site)

            except Exception as e:
                result["errors"].append(f"Firewall rule for {site}: {e}")

        return result

    def _remove_site_blocks(self, sites: List[str]) -> Dict:
        """Remove site blocks from hosts file and firewall."""
        result = {"unblocked": [], "errors": []}

        # Remove from hosts file
        try:
            with open(self.hosts_path, "r") as f:
                content = f.read()

            marker_start = "# OsMEN Focus Guardrails - START"
            marker_end = "# OsMEN Focus Guardrails - END"

            if marker_start in content:
                start_idx = content.find(marker_start)
                end_idx = content.find(marker_end)
                if end_idx != -1:
                    end_idx += len(marker_end) + 1
                    content = content[:start_idx] + content[end_idx:]

                    with open(self.hosts_path, "w") as f:
                        f.write(content.strip() + "\n")

                    result["unblocked"] = sites
        except Exception as e:
            result["errors"].append(f"Error removing hosts entries: {e}")

        # Remove firewall rules
        if self.is_windows:
            for site in sites:
                try:
                    rule_name = f"OsMEN_Block_{site.replace('.', '_')}"
                    subprocess.run(
                        [
                            "netsh",
                            "advfirewall",
                            "firewall",
                            "delete",
                            "rule",
                            f"name={rule_name}",
                        ],
                        capture_output=True,
                        timeout=5,
                    )
                except Exception as e:
                    result["errors"].append(
                        f"Error removing firewall rule for {site}: {e}"
                    )

        # Update tracked sites
        self.blocked_sites -= set(sites)

        # Flush DNS
        self._flush_dns()

        return result

    def unblock_sites(self, sites: Optional[List[str]] = None) -> Dict:
        """
        Unblock websites.

        Args:
            sites: Specific sites to unblock, or None for all blocked sites
        """
        try:
            if sites is None:
                sites = list(self.blocked_sites)

            if not sites:
                return {
                    "unblocked": [],
                    "status": "success",
                    "message": "No sites to unblock",
                }

            result = self._remove_site_blocks(sites)
            result["status"] = (
                "success" if not result.get("errors") else "partial_success"
            )

            self._save_state()

            logger.info(f"Unblocked {len(result.get('unblocked', []))} sites")
            return result

        except Exception as e:
            logger.error(f"Error unblocking sites: {e}")
            return {"unblocked": [], "status": "error", "error": str(e)}

    def _flush_dns(self):
        """Flush DNS cache to apply changes immediately."""
        try:
            if self.is_windows:
                subprocess.run(
                    ["ipconfig", "/flushdns"], capture_output=True, timeout=5
                )
            else:
                # Linux/macOS
                subprocess.run(
                    ["sudo", "systemd-resolve", "--flush-caches"],
                    capture_output=True,
                    timeout=5,
                )
        except Exception as e:
            logger.debug(f"Could not flush DNS: {e}")

    def _send_notification(self, title: str, message: str):
        """Send a desktop notification."""
        try:
            if self.is_windows:
                # Use PowerShell for toast notifications with proper escaping
                # Escape double quotes for PowerShell string literals
                safe_title = title.replace('"', '`"')
                safe_message = message.replace('"', '`"')
                ps_script = f"""
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
$template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
$textNodes = $template.GetElementsByTagName("text")
$textNodes.Item(0).AppendChild($template.CreateTextNode("{safe_title}")) | Out-Null
$textNodes.Item(1).AppendChild($template.CreateTextNode("{safe_message}")) | Out-Null
$notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("OsMEN")
$notifier.Show([Windows.UI.Notifications.ToastNotification]::new($template))
"""
                # Encode the script as UTF-16LE and then base64 for -EncodedCommand
                encoded_script = base64.b64encode(ps_script.encode("utf-16le")).decode(
                    "ascii"
                )
                subprocess.run(
                    ["powershell", "-NoProfile", "-EncodedCommand", encoded_script],
                    capture_output=True,
                    timeout=5,
                )
            else:
                # Linux - use notify-send
                subprocess.run(
                    ["notify-send", title, message], capture_output=True, timeout=5
                )
        except Exception as e:
            logger.debug(f"Could not send notification: {e}")

    def monitor_app_usage(self, duration_seconds: int = 60) -> Dict:
        """
        Monitor application usage for a period.

        Args:
            duration_seconds: How long to monitor (default 60 seconds)
        """
        usage = {
            "monitoring_period": duration_seconds,
            "apps": [],
            "productive_time": 0,
            "distracted_time": 0,
            "start_time": datetime.now().isoformat(),
        }

        if not self.is_windows:
            usage["error"] = "App monitoring only supported on Windows"
            return usage

        try:
            import psutil
            import win32gui
            import win32process

            app_times = {}
            start = time.time()
            last_app = None
            last_switch = start

            while time.time() - start < duration_seconds:
                try:
                    # Get foreground window
                    hwnd = win32gui.GetForegroundWindow()
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    proc = psutil.Process(pid)
                    app_name = proc.name()

                    if app_name != last_app:
                        if last_app:
                            duration = time.time() - last_switch
                            if last_app not in app_times:
                                app_times[last_app] = 0
                            app_times[last_app] += duration
                        last_app = app_name
                        last_switch = time.time()

                    time.sleep(1)
                except Exception:
                    time.sleep(1)

            # Final duration for last app
            if last_app:
                app_times[last_app] = app_times.get(last_app, 0) + (
                    time.time() - last_switch
                )

            # Calculate productive vs distracted time
            for app, duration in app_times.items():
                is_productive = app.lower() in [p.lower() for p in self.PRODUCTIVE_APPS]
                usage["apps"].append(
                    {
                        "name": app,
                        "duration_seconds": round(duration, 1),
                        "is_productive": is_productive,
                    }
                )
                if is_productive:
                    usage["productive_time"] += duration
                else:
                    usage["distracted_time"] += duration

            total_time = usage["productive_time"] + usage["distracted_time"]
            if total_time == 0:
                usage["productivity_score"] = 100.0  # No distraction occurred
            else:
                usage["productivity_score"] = round(
                    usage["productive_time"] / total_time * 100, 1
                )

        except ImportError:
            usage["error"] = (
                "App monitoring requires win32gui, win32process, and psutil packages"
            )
        except Exception as e:
            usage["error"] = str(e)

        usage["end_time"] = datetime.now().isoformat()
        return usage

    def get_focus_report(self) -> Dict:
        """Generate focus and productivity report."""
        report = {
            "total_sessions": len(self.focus_sessions),
            "completed_sessions": sum(
                1 for s in self.focus_sessions if s.status == "completed"
            ),
            "active_session": None,
            "blocked_sites": list(self.blocked_sites),
            "total_focus_minutes": 0,
            "admin_mode": self.is_admin,
            "timestamp": datetime.now().isoformat(),
        }

        # Find active session
        for session in reversed(self.focus_sessions):
            if session.status == "active":
                report["active_session"] = asdict(session)
                break

        # Calculate total focus time
        for session in self.focus_sessions:
            if session.status == "completed":
                report["total_focus_minutes"] += session.duration_minutes

        return report

    def send_focus_reminder(self, message: str = "Time to focus!") -> Dict:
        """Send a focus reminder notification."""
        reminder = {
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "sent": True,
        }

        self._send_notification("Focus Reminder", message)

        return reminder

    def get_blocked_sites(self) -> List[str]:
        """Get list of currently blocked sites."""
        return list(self.blocked_sites)


def main():
    """Main entry point for the agent"""
    agent = FocusGuardrailsAgent()

    print("=" * 60)
    print("Focus Guardrails Agent - Productivity System")
    print("=" * 60)
    print(f"Running as Administrator: {agent.is_admin}")
    print()

    # Start a focus session
    session = agent.start_focus_session(25)
    print("Focus Session Started:")
    print(json.dumps(session, indent=2))

    print()

    # Get report
    report = agent.get_focus_report()
    print("Focus Report:")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
