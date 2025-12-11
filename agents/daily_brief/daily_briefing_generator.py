"""
Daily Briefing Generator - Production Ready
============================================

Generates 90-second personalized audio briefings with FULL CONTEXT:

Context Sources:
1. Today's AM check-in (energy, priorities, ADHD state, meditation)
2. Previous 3 days of check-ins (AM + PM) for continuity
3. Previous 3 days of briefing scripts (what was emphasized)
4. Current week's syllabus (readings, assignments, class schedule)
5. Course progress tracker (readings behind, next deadline)
6. ADHD patterns (energy trends, working strategies)
7. Carryover tasks from yesterday's PM check-in
8. Pending to-do items aggregated from all sources

Briefing Structure (90 seconds):
- Opening: Day, date, greeting
- Energy check: Today's energy + 3-day trend context
- Priority focus: Top priorities with carryover awareness
- ADHD strategy: Contextual tip based on patterns
- Course update: Readings, deadlines, class status
- Meditation reminder: Practice continuity
- Boundary reflection: Week-appropriate reminder
- Closing: Encouragement + evening check-in reminder

Integration:
- Registered in: integrations/orchestration.py as Pipelines.DAILY_BRIEFING
- CLI: python cli_bridge/osmen_cli.py briefing generate
- n8n: checkin_triggered_briefing.json
- Langflow: daily_brief_specialist.json
"""

import json
import os
import random
import re
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

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

# Import the production context aggregator
from agents.daily_brief.context_aggregator import (
    AggregatedContext,
    ContextAggregator,
    gather_context_for_briefing,
)

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
    """Generate personalized 90-second daily briefings with full context"""

    def __init__(self):
        self.logger, self.prompt = agent_startup_check("daily-briefing-generator")
        self.today = date.today()
        self.today_str = self.today.isoformat()
        self.yesterday = (self.today - timedelta(days=1)).isoformat()
        
        # Use production context aggregator
        self.aggregator = ContextAggregator()

    def gather_context(self) -> AggregatedContext:
        """Gather comprehensive context using the production aggregator"""
        context = self.aggregator.gather_full_context()
        
        self.logger.log(
            action="gather_context",
            inputs={"date": self.today_str},
            outputs={
                "checkins_found": len(context.checkins),
                "briefings_found": len(context.briefings),
                "pending_tasks": len(context.pending_tasks),
                "syllabus_week": context.syllabus.current_week if context.syllabus else 0,
            },
            status="completed",
        )

        return context

    def _generate_adhd_tip(self, context: AggregatedContext) -> str:
        """Generate context-aware ADHD tip based on patterns"""
        adhd = context.adhd
        am = context.today_am_checkin
        
        # Get current energy
        energy = am.energy if am else 5
        adhd_state = am.adhd_state if am else "moderate"
        
        # Tips organized by situation
        tips_by_situation = {
            "low_energy": [
                "Energy is low today. Start with a 10-minute walk or movement to wake up your system. Protect your limited focus for one priority only.",
                "At {energy} energy, your threshold to start is higher. Use body doubling or a virtual co-working session to lower activation energy.",
                "Low energy day - break your first task into 5-minute chunks. One tiny start is better than paralysis.",
            ],
            "struggling": [
                "Struggling to start is normal. Set a timer for just 5 minutes on your top priority. Permission to stop after, but you might not want to.",
                "When initiation is hard, externalize the task. Write the first three steps on paper. Make the path visible.",
                "Struggling state detected. Your working strategies have been {strategies}. Try one of those to get moving.",
            ],
            "foggy": [
                "Brain fog today. Stay hydrated, move your body, and give yourself 30 minutes before tackling complex work.",
                "Foggy start - consider pushing hard cognitive work to afternoon if possible. Use morning for routine tasks.",
                "When foggy, reduce choices. Pick ONE thing and commit to it for the first hour.",
            ],
            "improving_energy": [
                "Your energy has been improving over the past few days. Ride this momentum - tackle something you've been avoiding.",
                "Energy trending up. This is a good day to front-load difficult tasks while you have capacity.",
            ],
            "declining_energy": [
                "Energy has been declining. Consider whether you're overcommitting. Protect your recovery today.",
                "Your trend shows declining energy. Be realistic about what you can accomplish. Quality over quantity.",
            ],
            "high_energy": [
                "Energy is strong at {energy}. Capitalize on it now - your best work window is the next 2-3 hours.",
                "High energy day! Challenge yourself but set a clear stopping point. Don't let hyperfocus burn you out.",
            ],
            "default": [
                "Use a visual timer for {focus_length}-minute focus blocks. External structure helps.",
                "Remember: done is better than perfect. What's the minimum viable version of your top task?",
                "Your recommended focus block is {focus_length} minutes based on recent patterns. Set a timer.",
            ],
        }
        
        # Select appropriate tip category
        if energy <= 3:
            category = "low_energy"
        elif adhd_state == "struggling":
            category = "struggling"
        elif adhd_state == "foggy":
            category = "foggy"
        elif adhd and adhd.energy_trend == "improving":
            category = "improving_energy"
        elif adhd and adhd.energy_trend == "declining":
            category = "declining_energy"
        elif energy >= 8:
            category = "high_energy"
        else:
            category = "default"
        
        tips = tips_by_situation[category]
        tip = random.choice(tips)
        
        # Fill in template variables
        strategies = ", ".join(adhd.working_strategies[:2]) if adhd and adhd.working_strategies else "body doubling and timers"
        focus_length = adhd.recommended_focus_block_length if adhd else 25
        
        tip = tip.format(
            energy=energy,
            strategies=strategies,
            focus_length=focus_length,
        )
        
        return tip

    def _get_boundary_reminder(self, week: int) -> str:
        """Get a boundary reminder relevant to current course week"""
        reminders = {
            1: "Boundaries define where you end and others begin. Notice your edges today.",
            2: "Today's framework: boundaries are about 'what' not 'who'. What boundaries serve you?",
            3: "Your ethical commitments are your guardrails. Let them guide your nos and yeses today.",
            4: "Integration means living your values, not just knowing them. Where can you embody a boundary?",
            5: "Self and systems interact. Your boundaries affect others and theirs affect you. Notice the dance.",
            6: "Shared wisdom: your self-knowledge is a tool for service. What do your patterns tell you?",
            7: "Sharing your work today. Remember: feedback on boundaries work is itself a boundary practice.",
            8: "Trauma shapes our boundaries. Today, notice where old wounds inform current reactions.",
            9: "Async week. A boundary around your time. Use it wisely for what matters most.",
            10: "Break week. Rest is a boundary. You don't have to be productive to be worthy.",
            11: "Technology boundaries matter. Your attention is sacred. Guard it today.",
            12: "Conflict is where boundaries get tested. How you handle disagreement reveals your edges.",
            13: "Connection requires boundaries. True intimacy needs healthy separation first.",
            14: "Presenting your work. Own your learning. You know what you need.",
            15: "Final presentations. You've learned so much. Trust your growth.",
            16: "Course complete. Integration continues. You carry these boundaries forward.",
        }
        return reminders.get(week, reminders[1])

    def generate_script(self, context: AggregatedContext) -> str:
        """Generate the 90-second briefing script with full context"""
        
        # Extract key data with safe defaults
        am = context.today_am_checkin
        yesterday_pm = context.yesterday_pm_checkin
        syllabus = context.syllabus
        adhd = context.adhd
        progress = context.progress
        
        # Core data
        energy = am.energy if am else 5
        priorities = am.priorities if am else context.pending_tasks[:3]
        priority_1 = priorities[0] if priorities else "your most important task"
        priority_2 = priorities[1] if len(priorities) > 1 else None
        
        # Carryover awareness
        carryover = context.carryover_from_yesterday
        
        script_parts = []
        
        # ===== OPENING (10 sec) =====
        script_parts.append(
            f"Good morning. It's {context.day_name}, {context.date_formatted}. "
            f"Here's your 90-second focus briefing."
        )
        
        # ===== ENERGY CHECK WITH TREND (15 sec) =====
        energy_trend = adhd.energy_trend if adhd else "stable"
        avg_energy = adhd.avg_energy_3day if adhd else energy
        
        if energy <= 3:
            energy_section = (
                f"Your energy is at {energy} today. "
                f"Your 3-day average is {avg_energy:.0f}, so this is {'below your recent baseline' if energy < avg_energy else 'consistent'}. "
                f"Be gentle with yourself. Focus on one thing only."
            )
        elif energy <= 5:
            trend_note = ""
            if energy_trend == "declining":
                trend_note = "It's been declining—consider what's draining you. "
            elif energy_trend == "improving":
                trend_note = "You're on an upward trend. Build on that momentum. "
            energy_section = (
                f"Energy at {energy}, moderate capacity. {trend_note}"
                f"Good enough to get meaningful work done with the right structure."
            )
        else:
            energy_section = (
                f"You're at {energy} energy today—strong foundation. "
                f"{"Capitalize on this uptrend by front-loading hard work." if energy_trend == "improving" else "Channel it into your top priority early."}"
            )
        
        script_parts.append(energy_section)
        
        # ===== CARRYOVER & PRIORITIES (20 sec) =====
        if carryover:
            script_parts.append(
                f"Carried over from yesterday: {carryover[0]}. "
                f"Consider whether this is still your top priority or can be delegated."
            )
        
        script_parts.append(f"Your number one today: {priority_1}.")
        
        if priority_2:
            script_parts.append(f"Second: {priority_2}.")
        
        script_parts.append(
            "Block focused time for these. Everything else can wait or be delegated."
        )
        
        # ===== ADHD STRATEGY (15 sec) =====
        adhd_tip = self._generate_adhd_tip(context)
        script_parts.append(adhd_tip)
        
        # ===== COURSE UPDATE (15 sec) =====
        if syllabus:
            if syllabus.is_break_week:
                script_parts.append(
                    f"Week {syllabus.current_week} is a break week. "
                    f"No class, but use the time wisely for your final project."
                )
            elif syllabus.is_class_today:
                script_parts.append(
                    f"Class today at {syllabus.class_time}. "
                    f"Topic: {syllabus.week_topic}. Make sure you're prepared."
                )
            else:
                readings_behind = progress.readings_behind if progress else 0
                if readings_behind > 0:
                    script_parts.append(
                        f"You're about {readings_behind} readings behind for Week {syllabus.current_week}: {syllabus.week_topic}. "
                        f"Consider audiobook during commute or chores to catch up."
                    )
                else:
                    script_parts.append(
                        f"On track with Week {syllabus.current_week}: {syllabus.week_topic}. "
                        f"{'Class in ' + str(syllabus.days_until_class) + ' days.' if syllabus.days_until_class <= 3 else 'Keep the momentum.'}"
                    )
                
                # Next deadline reminder
                if syllabus.next_deadline and syllabus.next_deadline["days_until"] <= 7:
                    script_parts.append(
                        f"Reminder: {syllabus.next_deadline['name']} due in {syllabus.next_deadline['days_until']} days."
                    )
        
        # ===== MEDITATION REMINDER (10 sec) =====
        meditation_done = am.meditation_completed if am else False
        meditation_type = am.meditation_type if am else ""
        meditation_streak = progress.meditation_sessions_this_week if progress else 0
        
        if meditation_done:
            script_parts.append(
                f"{'Your ' + meditation_type + ' practice' if meditation_type else 'Morning practice'} complete. "
                f"{'That makes ' + str(meditation_streak) + ' sessions this week.' if meditation_streak > 1 else 'Your practice is your anchor.'}"
            )
        else:
            script_parts.append(
                "Remember your practice commitments. Even 10 minutes of sitting shifts the day. "
                "Don't let 'not enough time' become 'no time.'"
            )
        
        # ===== BOUNDARY REFLECTION (10 sec) =====
        week = syllabus.current_week if syllabus else 1
        boundary_reminder = self._get_boundary_reminder(week)
        script_parts.append(boundary_reminder)
        
        # ===== CLOSING (5 sec) =====
        script_parts.append(
            "You've got this. Check in tonight to close the loop. Have a focused day."
        )
        
        script = " ".join(script_parts)
        
        self.logger.log(
            action="generate_script",
            inputs={
                "energy": energy,
                "priorities_count": len(priorities),
                "carryover_count": len(carryover),
                "syllabus_week": syllabus.current_week if syllabus else 0,
            },
            outputs={"script_length": len(script), "word_count": len(script.split())},
            status="completed",
        )

        return script

    def synthesize_audio(self, script: str) -> Optional[Path]:
        """Generate audio from script using Kokoro TTS"""

        # Save script to file
        script_file = SCRIPTS_DIR / f"{self.today_str}.txt"
        script_file.parent.mkdir(parents=True, exist_ok=True)
        script_file.write_text(script, encoding="utf-8")

        output_file = OUTPUT_DIR / f"{self.today_str}_briefing.mp3"
        output_file.parent.mkdir(parents=True, exist_ok=True)

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
            print(f"[INFO] TTS not available. Script saved to: {script_file}")
            return None

        except Exception as e:
            self.logger.log(
                action="synthesize_audio_error",
                inputs={"script_file": str(script_file)},
                outputs={"error": str(e)},
                status="error",
                level="error",
            )
            print(f"[ERROR] Audio synthesis failed: {e}")
            return None

    def run(self) -> Dict:
        """Run the full briefing generation pipeline"""
        print(f"\n{'=' * 60}")
        print(f"  Daily Briefing Generator - {self.today_str}")
        print(f"{'=' * 60}")

        # Check if AM check-in exists
        tracker = CheckInTracker()
        if self.prompt:
            print(f"\n[WARN] {self.prompt}")
            print("Proceeding with available data...\n")

        # Gather comprehensive context
        print("[1/4] Gathering context...")
        context = self.gather_context()
        
        print(f"      - Check-ins found: {len(context.checkins)}")
        print(f"      - Previous briefings: {len(context.briefings)}")
        print(f"      - Pending tasks: {len(context.pending_tasks)}")
        if context.syllabus:
            print(f"      - Course week: {context.syllabus.current_week}")
            print(f"      - Topic: {context.syllabus.week_topic[:50]}...")

        # Generate script
        print("\n[2/4] Generating script...")
        script = self.generate_script(context)
        word_count = len(script.split())
        duration_est = word_count * 0.4  # ~2.5 words per second at normal pace
        print(f"      - Words: {word_count}")
        print(f"      - Est. duration: {duration_est:.0f} seconds")

        # Synthesize audio
        print("\n[3/4] Synthesizing audio...")
        audio_file = self.synthesize_audio(script)

        # Log the generation
        print("\n[4/4] Logging generation...")
        AudioGenerationLog.log_generation(
            audio_type="briefing",
            script_file=str(SCRIPTS_DIR / f"{self.today_str}.txt"),
            audio_file=str(audio_file) if audio_file else "",
            duration_sec=int(duration_est),
            voice="af_nicole",
            source_data={
                "checkins_used": len(context.checkins),
                "briefings_referenced": len(context.briefings),
                "pending_tasks": len(context.pending_tasks),
                "syllabus_week": context.syllabus.current_week if context.syllabus else 0,
            },
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
            "duration_seconds": int(duration_est),
            "context_summary": {
                "checkins": len(context.checkins),
                "briefings": len(context.briefings),
                "pending_tasks": len(context.pending_tasks),
                "syllabus_week": context.syllabus.current_week if context.syllabus else 0,
            },
            "script_preview": script[:300] + "..." if len(script) > 300 else script,
        }

        print(f"\n{'=' * 60}")
        print("  BRIEFING GENERATION COMPLETE")
        print(f"{'=' * 60}")
        print(f"  Script: {result['script_file']}")
        if audio_file:
            print(f"  Audio:  {result['audio_file']}")
        else:
            print("  Audio:  [Skipped - TTS not configured]")
        print(f"  Words:  {word_count} (~{duration_est:.0f} sec)")
        print(f"{'=' * 60}\n")

        return result


def main():
    generator = DailyBriefingGenerator()
    result = generator.run()
    return result


if __name__ == "__main__":
    main()
