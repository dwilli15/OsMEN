"""
Daily Briefing Generator
Generates 90-second personalized audio briefings from check-in data

Workflow:
1. AM Check-in completed → triggers this generator
2. Reads AM check-in + previous PM check-in + course progress
3. Generates script from template
4. Synthesizes audio via Kokoro TTS
5. Saves to daily_briefings/ and logs the generation

Integration:
- Registered in: integrations/orchestration.py as Pipelines.DAILY_BRIEFING
- CLI: python cli_bridge/osmen_cli.py briefing generate
- n8n: checkin_triggered_briefing.json
- Langflow: daily_brief_specialist.json
"""

import json
import os
import re
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

# Add OsMEN root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from integrations.logging_system import (
    AgentLogger,
    AudioGenerationLog,
    CheckInTracker,
    agent_startup_check,
)

# Import from unified orchestration layer (SOURCE OF TRUTH)
from integrations.orchestration import OsMEN, Paths, Pipelines

# Use paths from orchestration layer (NEVER hardcode)
OBSIDIAN_ROOT = Paths.HB411_OBSIDIAN
TEMPLATES_DIR = Paths.VAULT_TEMPLATES
JOURNAL_DIR = Paths.VAULT_JOURNAL / "daily"
GOALS_DIR = Paths.VAULT_GOALS
SCRIPTS_DIR = Paths.HB411_BRIEFING_SCRIPTS
OUTPUT_DIR = Paths.HB411_BRIEFINGS
OSMEN_ROOT = Paths.OSMEN_ROOT

# Ensure directories exist
Paths.ensure_all()


class DailyBriefingGenerator:
    """Generate personalized 90-second daily briefings"""

    def __init__(self):
        self.logger, self.prompt = agent_startup_check("daily-briefing-generator")
        self.today = date.today()
        self.today_str = self.today.isoformat()
        self.yesterday = (self.today - timedelta(days=1)).isoformat()

    def gather_context(self) -> Dict[str, Any]:
        """Gather all context needed for briefing generation"""
        context = {
            "date": self.today_str,
            "day_name": self.today.strftime("%A"),
            "date_formatted": self.today.strftime("%B %d, %Y"),
        }

        # Read AM check-in
        am_checkin = self._read_checkin("am", self.today_str)
        if am_checkin:
            context.update(
                {
                    "am_energy": am_checkin.get("energy", 5),
                    "am_focus": am_checkin.get("focus_capacity", "medium"),
                    "am_priorities": am_checkin.get("priorities", []),
                    "am_adhd_strategy": am_checkin.get("adhd_strategy", ""),
                    "meditation_planned": am_checkin.get("meditation_planned", False),
                    "meditation_type": am_checkin.get("meditation_type", ""),
                }
            )

        # Read previous PM check-in
        pm_checkin = self._read_checkin("pm", self.yesterday)
        if pm_checkin:
            context.update(
                {
                    "pm_productivity": pm_checkin.get("productivity_rate", 70),
                    "pm_mood": pm_checkin.get("mood_trend", "stable"),
                    "pm_carryover": pm_checkin.get("carryover_tasks", []),
                    "pm_tomorrow_focus": pm_checkin.get("tomorrow_focus", ""),
                }
            )

        # Read course progress
        course = self._read_course_progress()
        context.update(course)

        # Generate ADHD tip based on context
        context["adhd_tip"] = self._generate_adhd_tip(context)

        # Generate boundary reminder from course content
        context["boundary_reminder"] = self._get_boundary_reminder(
            context.get("course_week", 1)
        )

        self.logger.log(
            action="gather_context",
            inputs={"date": self.today_str},
            outputs={"context_keys": list(context.keys())},
            status="completed",
        )

        return context

    def _read_checkin(self, period: str, date_str: str) -> Optional[Dict]:
        """Read a check-in file and extract key data"""
        # Try to read from check-in log first
        log_file = OSMEN_ROOT / "logs" / "check_ins" / f"{date_str}_checkin.json"
        if log_file.exists():
            with open(log_file) as f:
                data = json.load(f)
                if period == "am" and data.get("am_completed"):
                    return data.get("am_data", {})
                if period == "pm" and data.get("pm_completed"):
                    return data.get("pm_data", {})

        # Fallback: parse markdown file
        md_file = JOURNAL_DIR / f"{date_str}-{period.upper()}.md"
        if md_file.exists():
            return self._parse_checkin_md(md_file)

        return None

    def _parse_checkin_md(self, filepath: Path) -> Dict:
        """Parse a check-in markdown file for key values"""
        # Simplified parser - in production, use proper YAML frontmatter parsing
        data = {}
        try:
            content = filepath.read_text(encoding="utf-8")

            # Extract energy level
            energy_match = re.search(r"Energy Level[:\s]*(\d+)/10", content)
            if energy_match:
                data["energy"] = int(energy_match.group(1))

            # Extract priorities
            priorities = re.findall(r"^\d+\.\s+(.+)$", content, re.MULTILINE)
            if priorities:
                data["priorities"] = priorities[:3]

            # Check meditation planned
            data["meditation_planned"] = (
                "session planned" in content.lower() or "[x]" in content.lower()
            )

        except Exception as e:
            self.logger.log(
                action="parse_checkin_error",
                inputs={"file": str(filepath)},
                outputs={"error": str(e)},
                status="error",
                level="warning",
            )

        return data

    def _read_course_progress(self) -> Dict:
        """Read course progress from tracker"""
        progress_file = GOALS_DIR / "hb411_progress.md"

        # Default values
        data = {
            "course_week": 1,
            "week_topic": "Introduction to Boundaries",
            "readings_due": [],
            "readings_behind": 0,
            "days_to_class": 7,
        }

        if progress_file.exists():
            try:
                content = progress_file.read_text(encoding="utf-8")

                # Extract current week
                week_match = re.search(r"Current Week[:\s]*(\d+)", content)
                if week_match:
                    data["course_week"] = int(week_match.group(1))

            except Exception:
                pass

        return data

    def _generate_adhd_tip(self, context: Dict) -> str:
        """Generate context-aware ADHD tip"""
        energy = context.get("am_energy", 5)
        focus = context.get("am_focus", "medium")

        tips = {
            "low_energy": [
                "Start with a 10-minute walk or movement. Get your body activated before tackling cognitive work.",
                "Use body doubling or a virtual co-working session to help initiate focus.",
                "Break your first task into 5-minute chunks. Lower the activation energy to start.",
            ],
            "medium_energy": [
                "Use a visual timer for 25-minute focus blocks. The external structure helps.",
                "Do your hardest task in the next 2 hours while energy peaks.",
                "Keep your phone in another room during deep work blocks.",
            ],
            "high_energy": [
                "Capitalize on this energy! Tackle your most challenging task right now.",
                "Set ambitious goals for the morning but have a low-energy backup plan for afternoon.",
                "Document what's working today so you can replicate these conditions.",
            ],
        }

        if energy <= 4:
            import random

            return random.choice(tips["low_energy"])
        elif energy <= 7:
            import random

            return random.choice(tips["medium_energy"])
        else:
            import random

            return random.choice(tips["high_energy"])

    def _get_boundary_reminder(self, week: int) -> str:
        """Get a boundary reminder relevant to current course week"""
        reminders = {
            1: "Boundaries define where you end and others begin. Notice your edges today.",
            2: "Your boundaries were shaped in childhood. Understanding them is the first step to changing them.",
            3: "Which boundary problem shows up for you? Compliant, avoidant, controller, or nonresponsive?",
            4: "Remember: You are responsible TO others, not FOR others. Where can you release responsibility today?",
            5: "Boundary myths keep us stuck. What belief about boundaries might be limiting you?",
            6: "Self-boundaries are about self-control, not controlling others. What do you need to say no to within yourself?",
            7: "Healing from narcissistic patterns takes time. Be patient with your process.",
            8: "Family boundaries require the most courage. Small steps count.",
            9: "Ministry and work boundaries protect your calling. Burnout serves no one.",
            10: "Recovery is not linear. Some days are harder. That's part of the journey.",
            11: "The damage was real, but so is healing. You are already on the path.",
            12: "Integration means living your boundaries, not just knowing about them.",
            13: "Your spiritual boundaries matter too. Guilt is not from God.",
            14: "Digital boundaries are boundaries too. Your attention is sacred.",
            15: "You've learned so much. Trust your growth. You know what you need.",
        }
        return reminders.get(week, reminders[1])

    def generate_script(self, context: Dict) -> str:
        """Generate the 90-second briefing script"""

        priority_1 = (
            context.get("am_priorities", ["your top priority"])[0]
            if context.get("am_priorities")
            else "your top priority"
        )
        priority_2 = (
            context.get("am_priorities", [None, None])[1]
            if len(context.get("am_priorities", [])) > 1
            else None
        )

        energy = context.get("am_energy", 5)
        energy_section = ""
        if energy <= 4:
            energy_section = f"Your energy is at {energy} today. Start with something energizing—movement, music, or a quick win. Protect your peak hours for priority work."
        else:
            energy_section = f"You're at {energy} energy today. Good foundation. Channel it into your top priority early."

        script_parts = [
            # Opening (10 sec)
            f"Good morning. It's {context['day_name']}, {context['date_formatted']}. Here's your 90-second focus briefing.",
            # Energy Check (15 sec)
            energy_section,
            # Priority Focus (20 sec)
            f"Your number one today: {priority_1}.",
        ]

        if priority_2:
            script_parts.append(f"Second: {priority_2}.")

        script_parts.append(
            "Block focused time for these. Everything else can wait or be delegated."
        )

        # ADHD Strategy (15 sec)
        script_parts.append(
            context.get(
                "adhd_tip", "Use a timer and take breaks. Your brain needs rhythm."
            )
        )

        # Course Update (15 sec)
        readings_behind = context.get("readings_behind", 0)
        if readings_behind > 0:
            script_parts.append(
                f"You're {readings_behind} readings behind for Week {context.get('course_week', 1)}. Consider audiobook during commute or chores."
            )
        else:
            script_parts.append(
                f"On track with Week {context.get('course_week', 1)}: {context.get('week_topic', 'course content')}. Nice work."
            )

        # Meditation Reminder (10 sec)
        if context.get("meditation_planned"):
            script_parts.append(
                f"{context.get('meditation_type', 'Your')} practice is planned. Protect that time. Your practice is your anchor."
            )
        else:
            script_parts.append(
                "Remember your practice commitments. Even 10 minutes of Trekchö shifts the day."
            )

        # Boundary Reflection (10 sec)
        script_parts.append(
            context.get(
                "boundary_reminder", "Notice where you say yes when you mean no today."
            )
        )

        # Closing (5 sec)
        script_parts.append("You've got this. Check in tonight. Have a focused day.")

        script = " ".join(script_parts)

        self.logger.log(
            action="generate_script",
            inputs={"context_keys": list(context.keys())},
            outputs={"script_length": len(script), "word_count": len(script.split())},
            status="completed",
        )

        return script

    def synthesize_audio(self, script: str) -> Optional[Path]:
        """Generate audio from script using Kokoro TTS"""

        # Save script to file
        script_file = SCRIPTS_DIR / f"{self.today_str}.txt"
        script_file.write_text(script, encoding="utf-8")

        output_file = OUTPUT_DIR / f"{self.today_str}_briefing.mp3"

        try:
            # Use the TTS system - simplified call
            # In production, this would call the Kokoro TTS directly
            from agents.audiobook_creator.tts_generator import generate_speech

            generate_speech(
                text=script, output_path=str(output_file), voice="af_nicole", speed=1.1
            )

            self.logger.log(
                action="synthesize_audio",
                inputs={"script_file": str(script_file)},
                outputs={"audio_file": str(output_file)},
                status="completed",
            )

            return output_file

        except ImportError:
            # Fallback: just save the script, audio generation needs setup
            self.logger.log(
                action="synthesize_audio",
                inputs={"script_file": str(script_file)},
                outputs={"error": "TTS module not available"},
                status="skipped",
                level="warning",
            )
            print(f"⚠️ TTS not available. Script saved to: {script_file}")
            return None

        except Exception as e:
            self.logger.log(
                action="synthesize_audio_error",
                inputs={"script_file": str(script_file)},
                outputs={"error": str(e)},
                status="error",
                level="error",
            )
            return None

    def run(self) -> Dict:
        """Run the full briefing generation pipeline"""
        print(f"🎙️ Daily Briefing Generator - {self.today_str}")
        print("=" * 50)

        # Check if AM check-in exists
        tracker = CheckInTracker()
        if self.prompt:
            print(f"\n⚠️ {self.prompt}")
            print("Proceeding with available data...\n")

        # Gather context
        print("📊 Gathering context...")
        context = self.gather_context()

        # Generate script
        print("📝 Generating script...")
        script = self.generate_script(context)
        word_count = len(script.split())
        print(f"   Word count: {word_count} (~{word_count * 0.4:.0f} seconds)")

        # Synthesize audio
        print("🔊 Synthesizing audio...")
        audio_file = self.synthesize_audio(script)

        # Log the generation
        AudioGenerationLog.log_generation(
            audio_type="briefing",
            script_file=str(SCRIPTS_DIR / f"{self.today_str}.txt"),
            audio_file=str(audio_file) if audio_file else "",
            duration_sec=90,
            voice="af_nicole",
            source_data={"am_checkin": self.today_str, "pm_checkin": self.yesterday},
        )

        # Update check-in tracker
        tracker.update_status(
            {
                "briefing_generated": True,
                "briefing_file": str(audio_file) if audio_file else None,
                "briefing_script": str(SCRIPTS_DIR / f"{self.today_str}.txt"),
            }
        )

        # End session
        self.logger.end_session(f"Generated briefing for {self.today_str}")

        result = {
            "date": self.today_str,
            "script_file": str(SCRIPTS_DIR / f"{self.today_str}.txt"),
            "audio_file": str(audio_file) if audio_file else None,
            "word_count": word_count,
            "script_preview": script[:200] + "...",
        }

        print("\n" + "=" * 50)
        print("✅ Briefing generation complete!")
        print(f"   Script: {result['script_file']}")
        if audio_file:
            print(f"   Audio: {result['audio_file']}")

        return result


def main():
    generator = DailyBriefingGenerator()
    result = generator.run()
    return result


if __name__ == "__main__":
    main()
