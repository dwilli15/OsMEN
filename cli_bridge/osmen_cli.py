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
import json
import os
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

# Add OsMEN root to path
OSMEN_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(OSMEN_ROOT))

from integrations.logging_system import (
    AgentLogger,
    CheckInTracker,
    agent_startup_check,
    get_recent_context,
)
from integrations.orchestration import (
    Agents,
    OsMEN,
    Paths,
    Pipelines,
    Services,
    execute_pipeline,
    get_pipeline,
    get_state,
)


def cmd_checkin(args):
    """Handle check-in commands"""
    tracker = CheckInTracker()

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

        # Create today's AM check-in file from template
        today = date.today().isoformat()
        template_path = Paths.VAULT_TEMPLATES / "AM Check-In Template.md"
        output_path = Paths.VAULT_JOURNAL / "daily" / f"{today}-AM.md"

        if output_path.exists():
            print(f"  Check-in already exists: {output_path}")
            print("  Opening in default editor...")
        else:
            # Copy template
            output_path.parent.mkdir(parents=True, exist_ok=True)
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
        except:
            print(f"  Please open manually: {output_path}")

        print("\n  After completing the check-in, run: osmen briefing generate")
        return 0

    elif args.action == "pm":
        print("\n🌙 Starting PM Check-In...")

        today = date.today().isoformat()
        template_path = Paths.VAULT_TEMPLATES / "PM Check-In Template.md"
        output_path = Paths.VAULT_JOURNAL / "daily" / f"{today}-PM.md"

        if output_path.exists():
            print(f"  Check-in already exists: {output_path}")
        else:
            output_path.parent.mkdir(parents=True, exist_ok=True)
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
        except:
            print(f"  Please open manually: {output_path}")

        return 0

    return 1


def cmd_briefing(args):
    """Handle briefing commands"""

    if args.action == "generate":
        print("\n🎙️ Generating Daily Briefing...")
        result = execute_pipeline("daily_briefing")

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
        audio_file = Paths.HB411_BRIEFINGS / f"{today}_briefing.mp3"

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

    if args.tracker == "hb411":
        progress_file = Paths.VAULT_GOALS / "hb411_progress.md"
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
        dashboard_file = Paths.VAULT_GOALS / "adhd_dashboard.md"
        print(f"\n🧠 ADHD Executive Functioning Dashboard")
        print("=" * 40)

        if dashboard_file.exists():
            print(f"  File: {dashboard_file}")
            print("  (Open in Obsidian for full details)")
        else:
            print("  ❌ Dashboard file not found")

        return 0

    elif args.tracker == "meditation":
        log_file = Paths.VAULT_GOALS / "meditation_log.md"
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

    if args.action == "generate":
        print("\n🎙️ Generating Weekly Podcast...")
        result = execute_pipeline("weekly_podcast")

        if "error" in result:
            print(f"  ❌ Error: {result['error']}")
            return 1

        print(f"  ✅ Complete")
        return 0

    return 1


def cmd_status(args):
    """Show system status"""
    print("\n" + "=" * 60)
    print("🔥 OSMEN SYSTEM STATUS")
    print("=" * 60)

    state = get_state()

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
    print("\n🔧 Initializing OsMEN...")

    OsMEN.initialize()

    print("  ✅ Paths created")
    print("  ✅ State loaded")

    # Verify key files
    key_files = [
        (Paths.VAULT_INSTRUCTIONS, "Vault Instructions"),
        (Paths.VAULT_TEMPLATES / "AM Check-In Template.md", "AM Check-In Template"),
        (Paths.VAULT_TEMPLATES / "PM Check-In Template.md", "PM Check-In Template"),
        (Paths.VAULT_GOALS / "adhd_dashboard.md", "ADHD Dashboard"),
        (Paths.VAULT_GOALS / "meditation_log.md", "Meditation Log"),
        (Paths.VAULT_GOALS / "hb411_progress.md", "Course Progress"),
    ]

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
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
