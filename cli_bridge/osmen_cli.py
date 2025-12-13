#!/usr/bin/env python3
"""
OsMEN CLI - Unified command-line interface
==========================================

Entry point for all OsMEN operations. Provides consistent access to all pipelines.

Usage:
    osmen checkin am          # Start AM check-in
    osmen checkin pm          # Start PM check-in
    osmen checkin status      # Show today's status

    osmen briefing generate   # Generate today's briefing
    osmen briefing play       # Play today's briefing

    osmen progress hb411      # Show course progress
    osmen progress adhd       # Show ADHD dashboard
    osmen progress meditation # Show practice log

    osmen podcast generate    # Generate weekly podcast

    osmen status              # Show system status
    osmen init                # Initialize/verify system
"""
import argparse
import os
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

from loguru import logger

# Fix Windows console encoding for emojis
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add OsMEN root to path
OSMEN_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(OSMEN_ROOT))


_CTX = None


def cmd_nl(args):
    """Handle natural-language commands via GitHub Copilot CLI.

    This mode intentionally runs WITHOUT an allowlist (per user preference).
    Use --dry-run to preview without executing.
    """

    prompt = (args.prompt or "").strip()
    if not prompt:
        print("❌ Missing prompt")
        return 2

    # Lazy import to avoid extra deps for users not using nl.
    from cli_bridge.copilot_bridge import CopilotBridge

    bridge = CopilotBridge(github_token=os.getenv("GITHUB_TOKEN"))
    if not bridge.cli_available:
        print("❌ GitHub Copilot CLI is not available.")
        print("   Install GitHub CLI + Copilot extension:")
        print("   - https://cli.github.com/")
        print("   - gh extension install github/gh-copilot")
        print("   - gh auth login")
        return 3

    # Force the model to return an executable Windows-first command.
    # We avoid an allowlist, but we do constrain the *format* to improve reliability.
    context = (
        "You are running on Windows PowerShell. "
        "Return EXACTLY ONE PowerShell command (no markdown, no explanation). "
        "If multiple steps are needed, chain them with ';'. "
        "Prefer using OsMEN CLI (python cli_bridge/osmen_cli.py ...) when relevant. "
    )
    full_prompt = f"{context}\nTask: {prompt}".strip()

    suggestion = bridge.suggest_command(full_prompt)
    cmd = (suggestion.get("command") or suggestion.get("suggestion") or "").strip()

    if not cmd:
        print("❌ Copilot returned an empty command")
        return 4

    print(f"\n🧠 NL prompt: {prompt}")
    print(f"\n⚡ Command: {cmd}\n")

    # Always log (audit trail)
    log_dir = OSMEN_ROOT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logger.add(
        str(log_dir / "copilot_cli_nl.log"), rotation="5 MB", retention="10 files"
    )
    logger.info("NL prompt: {prompt}", prompt=prompt)
    logger.info("NL command: {cmd}", cmd=cmd)

    if args.dry_run:
        print("(dry-run) Not executing.")
        return 0

    try:
        # Execute using PowerShell for Windows-first behavior.
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                cmd,
            ],
            cwd=args.cwd or str(OSMEN_ROOT),
            text=True,
            capture_output=not args.no_capture,
            timeout=args.timeout,
        )

        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        logger.info("NL exit_code: {code}", code=result.returncode)
        if result.stdout:
            logger.info("NL stdout: {out}", out=result.stdout[-4000:])
        if result.stderr:
            logger.warning("NL stderr: {err}", err=result.stderr[-4000:])

        return int(result.returncode)
    except subprocess.TimeoutExpired:
        print(f"❌ Command timed out after {args.timeout}s")
        logger.error("NL command timed out after {t}s", t=args.timeout)
        return 124
    except Exception as e:
        print(f"❌ Failed to execute command: {e}")
        logger.exception("NL execution failure")
        return 1


def _bootstrap(workspace: str | None):
    """Initialize runtime context.

    We intentionally delay importing orchestration/paths until after we can set
    `OSMEN_SEMESTER_WORKSPACE`, so vault/template paths resolve correctly.
    """
    global _CTX
    if _CTX is not None:
        return _CTX

    if workspace:
        os.environ["OSMEN_SEMESTER_WORKSPACE"] = workspace

    from integrations.logging_system import CheckInTracker
    from integrations.orchestration import OsMEN, execute_pipeline, get_state
    from integrations.paths import (
        PRODUCT_TEMPLATES_ROOT,
        TEMPLATE_AM_CHECKIN,
        TEMPLATE_PM_CHECKIN,
        WorkspaceNotConfiguredError,
        get_vault_root,
    )

    _CTX = {
        "CheckInTracker": CheckInTracker,
        "OsMEN": OsMEN,
        "execute_pipeline": execute_pipeline,
        "get_state": get_state,
        "get_vault_root": get_vault_root,
        "WorkspaceNotConfiguredError": WorkspaceNotConfiguredError,
        "TEMPLATE_AM_CHECKIN": TEMPLATE_AM_CHECKIN,
        "TEMPLATE_PM_CHECKIN": TEMPLATE_PM_CHECKIN,
        "PRODUCT_TEMPLATES_ROOT": PRODUCT_TEMPLATES_ROOT,
        "repo_root": OSMEN_ROOT,
    }
    return _CTX


def cmd_checkin(args):
    """Handle check-in commands"""
    ctx = _bootstrap(getattr(args, "workspace", None))
    tracker = ctx["CheckInTracker"]()

    if args.action == "status":
        status = tracker.get_status()
        print(f"\n📋 Check-In Status for {status['date']}")
        print("=" * 40)
        print(
            f"  AM Check-In: {'✅ Done' if status['am_completed'] else '❌ Not done'}"
        )
        if status["am_time"]:
            print(f"    Completed at: {status['am_time']}")
        print(
            f"  PM Check-In: {'✅ Done' if status['pm_completed'] else '❌ Not done'}"
        )
        if status["pm_time"]:
            print(f"    Completed at: {status['pm_time']}")
        print(
            f"  Briefing: {'✅ Generated' if status['briefing_generated'] else '⏳ Pending'}"
        )
        return 0

    elif args.action == "am":
        print("\n☀️ Starting AM Check-In...")

        try:
            vault_root = ctx["get_vault_root"](required=True)
        except ctx["WorkspaceNotConfiguredError"] as e:
            print(f"\n❌ {e}")
            print(
                "Provide a workspace path with `--workspace` (must be outside the repo)."
            )
            return 2

        # Create today's AM check-in file from template
        today = date.today().isoformat()
        template_path = ctx["TEMPLATE_AM_CHECKIN"]
        fallback_template = ctx["PRODUCT_TEMPLATES_ROOT"] / "AM Check-In.md"
        if not template_path.exists() and fallback_template.exists():
            template_path = fallback_template

        output_path = vault_root / "journal" / "daily" / f"{today}-AM.md"

        if output_path.exists():
            print(f"  Check-in already exists: {output_path}")
            print("  Opening in default editor...")
        else:
            # Copy template
            output_path.parent.mkdir(parents=True, exist_ok=True)
            if not template_path.exists():
                print(f"  ❌ Template not found: {template_path}")
                print(
                    "  Add templates under <workspace>\\vault\\templates or repo templates/."
                )
                return 1

            template_content = template_path.read_text(encoding="utf-8")

            # Replace template variables
            now = datetime.now()
            content = template_content.replace("{{date}}", today)
            content = content.replace("{{time}}", now.strftime("%H:%M"))

            output_path.write_text(content, encoding="utf-8")
            print(f"  Created: {output_path}")

        # Open in default editor (or Obsidian if available)
        try:
            if sys.platform == "win32":
                os.startfile(str(output_path))
            else:
                subprocess.run(["open", str(output_path)])
        except OSError:
            print(f"  Please open manually: {output_path}")

        print("\n  After completing the check-in, run: osmen briefing generate")
        return 0

    elif args.action == "pm":
        print("\n🌙 Starting PM Check-In...")

        try:
            vault_root = ctx["get_vault_root"](required=True)
        except ctx["WorkspaceNotConfiguredError"] as e:
            print(f"\n❌ {e}")
            print(
                "Provide a workspace path with `--workspace` (must be outside the repo)."
            )
            return 2

        today = date.today().isoformat()
        template_path = ctx["TEMPLATE_PM_CHECKIN"]
        fallback_template = ctx["PRODUCT_TEMPLATES_ROOT"] / "PM Check-In.md"
        if not template_path.exists() and fallback_template.exists():
            template_path = fallback_template

        output_path = vault_root / "journal" / "daily" / f"{today}-PM.md"

        if output_path.exists():
            print(f"  Check-in already exists: {output_path}")
        else:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            if not template_path.exists():
                print(f"  ❌ Template not found: {template_path}")
                print(
                    "  Add templates under <workspace>\\vault\\templates or repo templates/."
                )
                return 1

            template_content = template_path.read_text(encoding="utf-8")

            now = datetime.now()
            content = template_content.replace("{{date}}", today)
            content = content.replace("{{time}}", now.strftime("%H:%M"))

            output_path.write_text(content, encoding="utf-8")
            print(f"  Created: {output_path}")

        try:
            if sys.platform == "win32":
                os.startfile(str(output_path))
            else:
                subprocess.run(["open", str(output_path)])
        except OSError:
            print(f"  Please open manually: {output_path}")

        return 0

    return 1


def cmd_briefing(args):
    """Handle briefing commands"""
    ctx = _bootstrap(getattr(args, "workspace", None))

    if args.action == "generate":
        print("\n🎙️ Generating Daily Briefing...")
        result = ctx["execute_pipeline"]("daily_briefing")

        if "error" in result:
            print(f"  ❌ Error: {result['error']}")
            return 1

        print(f"  ✅ Script: {result.get('script_file', 'N/A')}")
        if result.get("audio_file"):
            print(f"  ✅ Audio: {result['audio_file']}")
        else:
            print("  ⚠️ Audio generation skipped (TTS not available)")

        return 0

    elif args.action == "play":
        today = date.today().isoformat()
        try:
            vault_root = ctx["get_vault_root"](required=True)
        except ctx["WorkspaceNotConfiguredError"] as e:
            print(f"\n❌ {e}")
            print(
                "Provide a workspace path with `--workspace` (must be outside the repo)."
            )
            return 2

        audio_file = vault_root / "audio" / "daily_briefings" / f"{today}_briefing.mp3"

        if not audio_file.exists():
            print(f"  ❌ No briefing found for today")
            print(f"  Run: osmen briefing generate")
            return 1

        print(f"  ▶️ Playing: {audio_file}")
        try:
            if sys.platform == "win32":
                os.startfile(str(audio_file))
            else:
                subprocess.run(["open", str(audio_file)])
        except Exception as e:
            print(f"  Error playing: {e}")
            return 1

        return 0

    return 1


def cmd_progress(args):
    """Handle progress commands"""
    ctx = _bootstrap(getattr(args, "workspace", None))

    try:
        vault_root = ctx["get_vault_root"](required=True)
    except ctx["WorkspaceNotConfiguredError"] as e:
        print(f"\n❌ {e}")
        print("Provide a workspace path with `--workspace` (must be outside the repo).")
        return 2

    if args.tracker == "hb411":
        progress_file = vault_root / "journal" / "weekly" / "hb411_progress.md"
        print(f"\n📚 HB411 Course Progress")
        print("=" * 40)

        if progress_file.exists():
            content = progress_file.read_text(encoding="utf-8")
            # Extract key stats from the file
            print(f"  File: {progress_file}")
            print("  (Open in Obsidian for full details)")
        else:
            print("  ❌ Progress file not found")

        return 0

    elif args.tracker == "adhd":
        dashboard_file = vault_root / "journal" / "weekly" / "adhd_dashboard.md"
        print(f"\n🧠 ADHD Executive Functioning Dashboard")
        print("=" * 40)

        if dashboard_file.exists():
            print(f"  File: {dashboard_file}")
            print("  (Open in Obsidian for full details)")
        else:
            print("  ❌ Dashboard file not found")

        return 0

    elif args.tracker == "meditation":
        log_file = vault_root / "journal" / "weekly" / "meditation_log.md"
        print(f"\n🧘 Meditation Practice Log")
        print("=" * 40)

        if log_file.exists():
            print(f"  File: {log_file}")
            print("  (Open in Obsidian for full details)")
        else:
            print("  ❌ Log file not found")

        return 0

    return 1


def cmd_podcast(args):
    """Handle podcast commands"""
    ctx = _bootstrap(getattr(args, "workspace", None))

    if args.action == "generate":
        print("\n🎙️ Generating Weekly Podcast...")
        result = ctx["execute_pipeline"]("weekly_podcast")

        if "error" in result:
            print(f"  ❌ Error: {result['error']}")
            return 1

        print(f"  ✅ Complete")
        return 0

    return 1


def cmd_status(args):
    """Show system status"""
    ctx = _bootstrap(getattr(args, "workspace", None))
    print("\n" + "=" * 60)
    print("🔥 OSMEN SYSTEM STATUS")
    print("=" * 60)

    state = ctx["get_state"]()

    print(f"\n📅 Date: {state['date']}")
    print(f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}")

    print(f"\n📋 Check-In Status:")
    cs = state["checkin_status"]
    print(f"  AM: {'✅' if cs['am_completed'] else '❌'}")
    print(f"  PM: {'✅' if cs['pm_completed'] else '❌'}")
    print(f"  Briefing: {'✅' if cs['briefing_generated'] else '⏳'}")

    print(f"\n🤖 Agents:")
    for name, status in state["agents"].items():
        icon = "✅" if status == "operational" else "🚧"
        print(f"  {icon} {name}: {status}")

    print(f"\n📊 Recent Activity:")
    ctx = state["recent_context"]
    print(f"  Sessions: {len(ctx['recent_sessions'])}")
    print(f"  Check-ins: {len(ctx['recent_checkins'])}")
    print(f"  Audio generations: {len(ctx['recent_audio'])}")

    print("\n" + "=" * 60)
    return 0


def cmd_init(args):
    """Initialize/verify system"""
    ctx = _bootstrap(getattr(args, "workspace", None))
    print("\n🔧 Initializing OsMEN...")

    ctx["OsMEN"].initialize()

    print("  ✅ Paths created")
    print("  ✅ State loaded")

    # Verify key files
    key_files = []
    try:
        vault_root = ctx["get_vault_root"](required=True)
        key_files.extend(
            [
                (vault_root / "templates" / "AM Check-In.md", "AM Check-In Template"),
                (vault_root / "templates" / "PM Check-In.md", "PM Check-In Template"),
                (
                    vault_root / "journal" / "weekly" / "adhd_dashboard.md",
                    "ADHD Dashboard",
                ),
                (
                    vault_root / "journal" / "weekly" / "meditation_log.md",
                    "Meditation Log",
                ),
                (
                    vault_root / "journal" / "weekly" / "hb411_progress.md",
                    "Course Progress",
                ),
            ]
        )
    except Exception:
        # Workspace not configured: fall back to product templates only.
        key_files.extend(
            [
                (
                    ctx["PRODUCT_TEMPLATES_ROOT"] / "AM Check-In.md",
                    "AM Check-In Template (product)",
                ),
                (
                    ctx["PRODUCT_TEMPLATES_ROOT"] / "PM Check-In.md",
                    "PM Check-In Template (product)",
                ),
            ]
        )

    print("\n📁 Key Files:")
    for path, name in key_files:
        exists = path.exists()
        print(f"  {'✅' if exists else '❌'} {name}")

    print("\n✅ OsMEN initialized!")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="OsMEN CLI - Unified command-line interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  osmen checkin am          Start morning check-in
  osmen checkin status      Show check-in status
  osmen briefing generate   Generate daily briefing
  osmen progress hb411      Show course progress
  osmen status              Show system status
        """,
    )

    parser.add_argument(
        "--workspace",
        default=os.getenv("OSMEN_SEMESTER_WORKSPACE"),
        help=(
            "External semester workspace directory (must be outside the repo). "
            "Also configurable via OSMEN_SEMESTER_WORKSPACE."
        ),
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # checkin command
    checkin_parser = subparsers.add_parser("checkin", help="Check-in management")
    checkin_parser.add_argument(
        "action", choices=["am", "pm", "status"], help="Check-in action"
    )

    # briefing command
    briefing_parser = subparsers.add_parser("briefing", help="Daily briefing")
    briefing_parser.add_argument(
        "action", choices=["generate", "play"], help="Briefing action"
    )

    # progress command
    progress_parser = subparsers.add_parser("progress", help="Progress tracking")
    progress_parser.add_argument(
        "tracker", choices=["hb411", "adhd", "meditation"], help="Which tracker to view"
    )

    # podcast command
    podcast_parser = subparsers.add_parser("podcast", help="Podcast generation")
    podcast_parser.add_argument("action", choices=["generate"], help="Podcast action")

    # status command
    subparsers.add_parser("status", help="Show system status")

    # init command
    subparsers.add_parser("init", help="Initialize/verify system")

    # nl command
    nl_parser = subparsers.add_parser(
        "nl",
        help="Natural language → Copilot CLI → execute (no allowlist)",
    )
    nl_parser.add_argument(
        "prompt",
        nargs="+",
        help="Natural language prompt",
    )
    nl_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print command but do not execute",
    )
    nl_parser.add_argument(
        "--cwd",
        default=None,
        help="Working directory for execution (defaults to repo root)",
    )
    nl_parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Timeout seconds for the executed command",
    )
    nl_parser.add_argument(
        "--no-capture",
        action="store_true",
        help="Do not capture stdout/stderr (stream to console)",
    )

    args = parser.parse_args()

    if args.command == "checkin":
        return cmd_checkin(args)
    elif args.command == "briefing":
        return cmd_briefing(args)
    elif args.command == "progress":
        return cmd_progress(args)
    elif args.command == "podcast":
        return cmd_podcast(args)
    elif args.command == "status":
        return cmd_status(args)
    elif args.command == "init":
        return cmd_init(args)
    elif args.command == "nl":
        args.prompt = " ".join(args.prompt or []).strip()
        return cmd_nl(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
