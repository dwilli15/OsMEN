#!/usr/bin/env python3
"""Copilot CLI Bridge.

Provides integration with GitHub Copilot CLI for command assistance.
"""

import logging
import os
import subprocess
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CopilotBridge:
    """
    Bridge to GitHub Copilot CLI

    Provides:
    - Command-line assistance
    - Shell command suggestions
    - Git workflow help
    - Context-aware code suggestions
    """

    def __init__(self, github_token: Optional[str] = None):
        """Initialize Copilot CLI Bridge.

        Args:
            github_token: Optional GitHub token used only for non-CLI fallback paths.
                The `gh copilot` CLI typically uses `gh auth login` (keyring) instead.
        """
        self.github_token = github_token
        self.cli_available = self._check_cli_availability()

        logger.info("CopilotBridge initialized")

    def _check_cli_availability(self) -> bool:
        """Check if GitHub Copilot CLI is available"""
        try:
            result = subprocess.run(
                ["gh", "copilot", "--version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False

    @staticmethod
    def _is_transient_error(stderr: str) -> bool:
        lowered = (stderr or "").lower()
        return (
            "internal server error" in lowered
            or "temporarily unavailable" in lowered
            or "try again" in lowered
        )

    def suggest_command(
        self,
        description: str,
        retries: int = 2,
        retry_sleep_s: float = 1.0,
    ) -> Dict[str, Any]:
        """Suggest a shell command based on description

        Args:
            description: Natural language description of desired command

        Returns:
            Dictionary with command suggestion
        """
        if not self.cli_available:
            logger.warning("Copilot CLI not available, using fallback")
            return self._fallback_suggest_command(description)

        last: Dict[str, Any] = {
            "success": False,
            "command": "",
            "description": description,
            "method": "gh_copilot",
        }

        # Non-interactive suggestion call. Target 'shell' for PowerShell/CMD-like output.
        # Note: gh-copilot's --shell-out flag expects a file path in newer versions;
        # we avoid it and parse stdout instead.
        cmd = ["gh", "copilot", "suggest", "-t", "shell", description]

        env = {
            **{
                k: v
                for k, v in os.environ.items()
                if k not in {"GITHUB_TOKEN", "GH_TOKEN"}
            },
            "GH_PROMPT": "disable",
            "GH_FORCE_TTY": "0",
        }

        for attempt in range(max(0, int(retries)) + 1):
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=90,
                    env=env,
                )

                stdout = (result.stdout or "").strip()
                stderr = (result.stderr or "").strip()
                last.update(
                    {
                        "returncode": result.returncode,
                        "stdout": stdout[-4000:] if stdout else "",
                        "stderr": stderr[-4000:] if stderr else "",
                        "attempt": attempt + 1,
                    }
                )

                if result.returncode == 0:
                    lines = [ln.strip() for ln in stdout.splitlines() if ln.strip()]
                    command = lines[-1] if lines else ""
                    last.update({"success": True, "command": command})
                    return last

                logger.error("Copilot CLI error (attempt %s): %s", attempt + 1, stderr)
                if attempt < retries and self._is_transient_error(stderr):
                    time.sleep(retry_sleep_s * (2**attempt))
                    continue
                break

            except Exception as e:
                logger.error(
                    "Failed to suggest command (attempt %s): %s", attempt + 1, e
                )
                last.update({"error": str(e)})
                if attempt < retries:
                    time.sleep(retry_sleep_s * (2**attempt))
                    continue
                break

        # Only fall back if a token was explicitly provided/configured.
        if self.github_token:
            fb = self._fallback_suggest_command(description)
            fb["method"] = fb.get("method", "api_fallback")
            fb["primary_error"] = last
            return fb

        last["error"] = last.get("error") or "Copilot CLI failed"
        return last

    def _fallback_suggest_command(self, description: str) -> Dict[str, Any]:
        """Fallback command suggestion using Copilot integration"""
        try:
            from tools.copilot_cli.copilot_integration import CopilotCLIIntegration

            integration = CopilotCLIIntegration(github_token=self.github_token)
            result = integration.suggest_command(description)

            return {
                "success": True,
                "command": result.get("suggestion", ""),
                "description": description,
                "method": "api_fallback",
            }
        except Exception as e:
            logger.error(f"Fallback command suggestion failed: {e}")
            return {"success": False, "error": str(e)}

    def explain_command(self, command: str) -> Dict[str, Any]:
        """Explain what a command does

        Args:
            command: Shell command to explain

        Returns:
            Dictionary with explanation
        """
        if not self.cli_available:
            return self._fallback_explain_command(command)

        try:
            cmd = ["gh", "copilot", "explain", command]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                return {
                    "success": True,
                    "explanation": result.stdout.strip(),
                    "command": command,
                }
            else:
                return self._fallback_explain_command(command)

        except Exception as e:
            logger.error(f"Failed to explain command: {e}")
            return {"success": False, "error": str(e)}

    def _fallback_explain_command(self, command: str) -> Dict[str, Any]:
        """Fallback command explanation"""
        try:
            from tools.copilot_cli.copilot_integration import CopilotCLIIntegration

            integration = CopilotCLIIntegration(github_token=self.github_token)
            result = integration.explain_command(command)

            return {
                "success": True,
                "explanation": result.get("explanation", ""),
                "command": command,
            }
        except Exception as e:
            logger.error(f"Fallback command explanation failed: {e}")
            return {"success": False, "error": str(e)}

    def get_git_help(self, task: str) -> Dict[str, Any]:
        """Get help with a git task

        Args:
            task: Description of git task

        Returns:
            Dictionary with git command suggestions
        """
        description = f"git: {task}"
        return self.suggest_command(description)

    def get_status(self) -> Dict[str, Any]:
        """Get status of Copilot CLI bridge

        Returns:
            Dictionary with status information
        """
        return {
            "cli_available": self.cli_available,
            "token_configured": bool(self.github_token),
            "operational": self.cli_available or bool(self.github_token),
        }


def main():
    """Test Copilot CLI Bridge"""
    bridge = CopilotBridge()

    print("\n" + "=" * 80)
    print("Copilot CLI Bridge Test")
    print("=" * 80)

    # Check status
    status = bridge.get_status()
    print(f"\nStatus:")
    print(f"  CLI Available: {status['cli_available']}")
    print(f"  Token Configured: {status['token_configured']}")
    print(f"  Operational: {status['operational']}")

    # Test command suggestion
    if status["operational"]:
        print("\nSuggesting command...")
        result = bridge.suggest_command("list all files in current directory")

        if result["success"]:
            print(f"Suggested command: {result['command']}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")

    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
if __name__ == "__main__":
    main()
