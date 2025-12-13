#!/usr/bin/env python3
"""
Production Demo Runner - OsMEN Semester Start Pipeline
======================================================
Complete production workflow:
1. Ingest all available readings into ChromaDB
2. Generate weekly podcast scripts (for review BEFORE TTS)
3. Set up daily briefing template (TTS AFTER check-in)
4. Create Obsidian vault structure with proper templates

This is the production demo as it should have been from the start.
"""

import hashlib
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add OsMEN to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from integrations.logging_system import AgentLogger, agent_startup_check

# OsMEN imports
from integrations.memory import HybridMemory

# Paths
SEMESTER_ROOT = Path(r"D:\semester_start")
VAULT_ROOT = SEMESTER_ROOT / "vault"
OSMEN_ROOT = Path(r"D:\OsMEN")


class ProductionDemoRunner:
    """Runs the full production demo for semester_start."""

    def __init__(self):
        self.logger = AgentLogger("production-demo")
        self.memory = None
        self.readings_ingested = 0
        self.scripts_generated = 0

    def initialize_memory(self):
        """Initialize HybridMemory connection."""
        print("🧠 Initializing HybridMemory...")
        try:
            self.memory = HybridMemory()
            print("   ✅ HybridMemory connected")
            return True
        except Exception as e:
            print(f"   ⚠️ HybridMemory not available: {e}")
            print("   Using fallback mode (no vector storage)")
            return False

    def ingest_readings(self) -> dict:
        """Ingest all available reading materials into ChromaDB."""
        print("\n📚 PHASE 1: Ingesting Readings into ChromaDB")
        print("-" * 50)

        supported_formats = {".pdf", ".epub", ".txt"}
        results = {"success": [], "failed": [], "skipped": []}

        for file_path in SEMESTER_ROOT.iterdir():
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() not in supported_formats:
                continue

            print(f"   Processing: {file_path.name}")

            try:
                # Read content based on format
                content = self._extract_content(file_path)

                if not content or len(content) < 100:
                    results["skipped"].append(
                        {"file": file_path.name, "reason": "Too short or empty"}
                    )
                    continue

                # Generate document ID
                doc_id = hashlib.md5(file_path.name.encode()).hexdigest()[:16]

                # Store in memory if available
                if self.memory:
                    self.memory.remember(
                        content=content[:10000],  # Chunk large docs
                        source=f"reading:{file_path.name}",
                        context={
                            "type": "course_reading",
                            "course": "HB411",
                            "filename": file_path.name,
                            "format": file_path.suffix.lower(),
                            "ingested_at": datetime.now().isoformat(),
                        },
                    )

                results["success"].append(file_path.name)
                self.readings_ingested += 1
                print(f"      ✅ Ingested ({len(content)} chars)")

            except Exception as e:
                results["failed"].append({"file": file_path.name, "error": str(e)})
                print(f"      ❌ Failed: {e}")

        print(f"\n   📊 Ingest Summary:")
        print(f"      Success: {len(results['success'])}")
        print(f"      Failed: {len(results['failed'])}")
        print(f"      Skipped: {len(results['skipped'])}")

        return results

    def _extract_content(self, file_path: Path) -> str:
        """Extract text content from various file formats."""
        suffix = file_path.suffix.lower()

        if suffix == ".txt":
            return file_path.read_text(encoding="utf-8", errors="ignore")

        elif suffix == ".pdf":
            try:
                import pdfplumber

                text = ""
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages[:50]:  # Limit pages
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                return text
            except Exception as e:
                return f"[PDF extraction failed: {e}]"

        elif suffix == ".epub":
            try:
                import ebooklib
                from bs4 import BeautifulSoup
                from ebooklib import epub

                book = epub.read_epub(str(file_path))
                text = ""
                for item in book.get_items():
                    if item.get_type() == ebooklib.ITEM_DOCUMENT:
                        soup = BeautifulSoup(item.get_content(), "html.parser")
                        text += soup.get_text() + "\n"
                        if len(text) > 50000:  # Limit size
                            break
                return text
            except Exception as e:
                return f"[EPUB extraction failed: {e}]"

        return ""

    def generate_weekly_scripts(self) -> list:
        """Generate weekly podcast review scripts (for user review BEFORE TTS)."""
        print("\n🎙️ PHASE 2: Generating Weekly Podcast Scripts")
        print("-" * 50)
        print("   ⚠️ NOTE: These are for USER REVIEW before TTS generation")

        # Load syllabus analysis
        analysis_path = VAULT_ROOT / "courses" / "HB411" / "syllabus_analysis.json"
        if not analysis_path.exists():
            print("   ❌ Syllabus analysis not found. Run syllabus_analyzer.py first.")
            return []

        with open(analysis_path, "r") as f:
            syllabus = json.load(f)

        scripts_dir = VAULT_ROOT / "audio" / "weekly_scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)

        scripts = []

        # Generate 15 weeks of content
        for week in range(1, 16):
            script = self._generate_week_script(week, syllabus)

            # Save script for review
            script_path = scripts_dir / f"week_{week:02d}_script.md"
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(script)

            scripts.append(
                {
                    "week": week,
                    "path": str(script_path),
                    "status": "AWAITING_REVIEW",
                    "tts_generated": False,
                }
            )

            print(f"   📝 Week {week} script saved (awaiting review)")
            self.scripts_generated += 1

        # Create script index
        index_path = scripts_dir / "script_index.json"
        with open(index_path, "w") as f:
            json.dump(
                {
                    "generated_at": datetime.now().isoformat(),
                    "scripts": scripts,
                    "workflow": {
                        "step1": "Review and edit scripts in vault/audio/weekly_scripts/",
                        "step2": "Mark approved scripts in script_index.json",
                        "step3": "Run TTS generator on approved scripts only",
                    },
                },
                f,
                indent=2,
            )

        print(f"\n   📊 Generated {len(scripts)} weekly scripts")
        print(f"   📋 Index saved to: {index_path}")

        return scripts

    def _generate_week_script(self, week: int, syllabus: dict) -> str:
        """Generate a single week's podcast script."""
        # Get weekly topic if available
        weekly_data = syllabus.get("weekly_schedule", {}).get(str(week), {})
        topic = weekly_data.get("topic", f"Week {week} Content")
        readings = weekly_data.get("readings", "See syllabus for details")

        script = f"""---
title: "HB411 Weekly Review - Week {week}"
course: HB 411 Healthy Boundaries in Ministry
topic: "{topic}"
status: DRAFT - AWAITING REVIEW
generated: {datetime.now().isoformat()}
tts_ready: false
---

# Week {week} Audio Review Script

## Opening (30 seconds)
Welcome to your Week {week} audio review for Healthy Boundaries in Ministry.
This week we're focusing on: {topic}

## Key Concepts (3-4 minutes)

### Main Themes
[EDIT THIS SECTION with actual content from readings]

1. **Theme 1**: [Description from readings]
   - Key point A
   - Key point B

2. **Theme 2**: [Description from readings]
   - Key point A
   - Key point B

### Critical Vocabulary
- **Term 1**: Definition and context
- **Term 2**: Definition and context

## Reading Connections (2 minutes)
This week's readings include:
{readings}

How these connect to course themes:
[EDIT with specific connections]

## Reflection Questions (1 minute)
Consider these questions as you complete your readings:
1. How does this week's content challenge your assumptions about boundaries?
2. What practical applications can you identify for your ministry context?
3. Where do you see connections to previous weeks' material?

## Closing (30 seconds)
That's your Week {week} review. Remember to complete your readings and journal
reflections before class. See you in session!

---
## Review Notes (DELETE BEFORE TTS)
- [ ] Content accuracy verified
- [ ] Timing checked (~6-8 minutes total)
- [ ] Transitions smooth
- [ ] No copyrighted content quoted at length
- [ ] Ready for TTS generation
"""
        return script

    def setup_daily_briefing_templates(self):
        """Set up daily briefing templates (TTS AFTER check-in finalization)."""
        print("\n📅 PHASE 3: Setting Up Daily Briefing System")
        print("-" * 50)
        print("   ⚠️ NOTE: Daily TTS runs AFTER check-in is finalized")

        templates_dir = VAULT_ROOT / "templates"
        templates_dir.mkdir(parents=True, exist_ok=True)

        # AM Check-in template
        am_template = templates_dir / "AM Check-In.md"
        am_content = """---
type: daily-checkin
time: morning
status: template
---

# AM Check-In - {{date}}

## 🌅 Energy & Focus
- Current energy level (1-10): 
- Sleep quality last night: 
- Primary focus for today: 

## 📚 Academic
- Classes/meetings today: 
- Readings to complete: 
- Assignments due: 

## 🎯 Top 3 Priorities
1. 
2. 
3. 

## 💭 Morning Reflection
What do I need to succeed today?


## ⚡ Quick Notes


---
*Complete by 9:00 AM to trigger daily briefing generation*
"""
        with open(am_template, "w", encoding="utf-8") as f:
            f.write(am_content)
        print(f"   ✅ AM Check-In template created")

        # PM Check-in template
        pm_template = templates_dir / "PM Check-In.md"
        pm_content = """---
type: daily-checkin
time: evening
status: template
---

# PM Check-In - {{date}}

## 📊 Day Review
- Energy level now (1-10): 
- Productivity score: 
- Major accomplishment: 

## ✅ Completed
- [ ] Priority 1: 
- [ ] Priority 2: 
- [ ] Priority 3: 

## 🔄 Carried Forward
What needs to move to tomorrow?


## 💡 Insights
What did I learn today?


## 🙏 Gratitude
Three things I'm grateful for:
1. 
2. 
3. 

## 📝 Notes for Tomorrow


---
*Complete by 10:00 PM to feed next day's briefing context*
"""
        with open(pm_template, "w", encoding="utf-8") as f:
            f.write(pm_content)
        print(f"   ✅ PM Check-In template created")

        # Daily Briefing Script template
        briefing_template = templates_dir / "Daily Briefing Script.md"
        briefing_content = """---
type: daily-briefing
status: auto-generated
tts_trigger: after-checkin-finalization
---

# Daily Briefing - {{date}}

## 🎯 Today's Focus (30 seconds)
Based on your AM check-in, today's primary focus is: {{primary_focus}}

## 📚 Academic Review (60 seconds)
{{academic_summary}}

## 📅 Schedule Overview (30 seconds)
{{schedule_items}}

## 💡 Key Reminders (30 seconds)
{{reminders}}

## 🌟 Motivation
{{motivational_note}}

---
**Total runtime: ~90 seconds**
*TTS generated after AM check-in finalization*
"""
        with open(briefing_template, "w", encoding="utf-8") as f:
            f.write(briefing_content)
        print(f"   ✅ Daily Briefing Script template created")

        # Create workflow documentation
        workflow_doc = templates_dir / "TTS_WORKFLOW.md"
        workflow_content = """# TTS Workflow Documentation

## Overview
This document defines the correct timing for TTS (Text-to-Speech) generation.

## Weekly Podcast Scripts
- **Generation**: Scripts generated at start of semester
- **Review**: USER reviews and edits scripts before TTS
- **TTS**: Only after manual approval
- **Location**: `vault/audio/weekly_scripts/`

## Daily 90-Second Briefings
- **Trigger**: AM Check-In finalization
- **Generation**: Automatic after check-in is marked complete
- **TTS**: Immediate after generation (same day, same session)
- **Location**: `vault/audio/daily_briefings/`

## Workflow Diagram

```
[Weekly Scripts]
    ↓
Generate all scripts at semester start
    ↓
User reviews script for Week N  ←──────┐
    ↓                                  │
Approve/Edit                           │
    ↓                                  │
Run TTS for approved script            │
    ↓                                  │
Next week ─────────────────────────────┘


[Daily Briefings]
    ↓
User completes AM Check-In
    ↓
System detects completion
    ↓
Generate 90-second script from check-in data
    ↓
Run TTS immediately
    ↓
Audio ready for playback
```

## Important Rules

1. **NEVER** generate TTS for weekly scripts without user review
2. **ALWAYS** generate TTS for daily briefings after check-in finalization
3. Weekly scripts are for **preparation** (review before class)
4. Daily briefings are for **immediate use** (start of day)
"""
        with open(workflow_doc, "w", encoding="utf-8") as f:
            f.write(workflow_content)
        print(f"   ✅ TTS Workflow documentation created")

        return True

    def create_vault_structure(self):
        """Create complete Obsidian vault structure."""
        print("\n📁 PHASE 4: Creating Obsidian Vault Structure")
        print("-" * 50)

        # Create directory structure
        directories = [
            VAULT_ROOT / "courses" / "HB411" / "notes",
            VAULT_ROOT / "courses" / "HB411" / "assignments",
            VAULT_ROOT / "journal" / "daily",
            VAULT_ROOT / "journal" / "weekly",
            VAULT_ROOT / "readings" / "annotations",
            VAULT_ROOT / "readings" / "summaries",
            VAULT_ROOT / "audio" / "weekly_scripts",
            VAULT_ROOT / "audio" / "daily_briefings",
            VAULT_ROOT / "templates",
            VAULT_ROOT / ".obsidian",
        ]

        for dir_path in directories:
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"   📂 {dir_path.relative_to(VAULT_ROOT)}")

        # Create vault configuration
        self._create_obsidian_config()

        return True

    def _create_obsidian_config(self):
        """Create Obsidian configuration files."""
        obsidian_dir = VAULT_ROOT / ".obsidian"

        # App config
        app_config = {
            "alwaysUpdateLinks": True,
            "newFileLocation": "folder",
            "newFileFolderPath": "journal/daily",
            "attachmentFolderPath": "attachments",
            "showUnsupportedFiles": False,
        }
        with open(obsidian_dir / "app.json", "w") as f:
            json.dump(app_config, f, indent=2)

        # Core plugins
        core_plugins = {
            "file-explorer": True,
            "global-search": True,
            "switcher": True,
            "graph": True,
            "backlink": True,
            "tag-pane": True,
            "daily-notes": True,
            "templates": True,
            "command-palette": True,
            "markdown-importer": True,
            "outline": True,
        }
        with open(obsidian_dir / "core-plugins.json", "w") as f:
            json.dump(core_plugins, f, indent=2)

        # Daily notes config
        daily_notes = {
            "format": "YYYY-MM-DD",
            "folder": "journal/daily",
            "template": "templates/AM Check-In.md",
            "autorun": False,
        }
        with open(obsidian_dir / "daily-notes.json", "w") as f:
            json.dump(daily_notes, f, indent=2)

        # Templates config
        templates_config = {
            "folder": "templates",
            "dateFormat": "YYYY-MM-DD",
            "timeFormat": "HH:mm",
        }
        with open(obsidian_dir / "templates.json", "w") as f:
            json.dump(templates_config, f, indent=2)

        print("   ⚙️ Obsidian configuration created")

    def generate_summary_report(self) -> dict:
        """Generate final summary report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "status": "SUCCESS",
            "phases_completed": {
                "reading_ingest": self.readings_ingested > 0,
                "weekly_scripts": self.scripts_generated > 0,
                "daily_briefing_templates": True,
                "vault_structure": True,
            },
            "metrics": {
                "readings_ingested": self.readings_ingested,
                "scripts_generated": self.scripts_generated,
            },
            "locations": {
                "vault_root": str(VAULT_ROOT),
                "weekly_scripts": str(VAULT_ROOT / "audio" / "weekly_scripts"),
                "templates": str(VAULT_ROOT / "templates"),
                "course_materials": str(VAULT_ROOT / "courses" / "HB411"),
            },
            "next_steps": [
                "Open vault in Obsidian: File > Open Vault > " + str(VAULT_ROOT),
                "Review weekly scripts in audio/weekly_scripts/",
                "Complete AM Check-In to trigger daily briefing",
                "Run TTS on approved weekly scripts",
            ],
        }

        # Save report
        report_path = VAULT_ROOT / "production_demo_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        return report

    def run(self):
        """Execute full production demo."""
        print("=" * 70)
        print("🚀 OsMEN PRODUCTION DEMO - SEMESTER START")
        print("=" * 70)
        print(f"Target: {SEMESTER_ROOT}")
        print(f"Time: {datetime.now().isoformat()}")
        print("=" * 70)

        # Initialize memory
        self.initialize_memory()

        # Create vault structure first
        self.create_vault_structure()

        # Run phases
        self.ingest_readings()
        self.generate_weekly_scripts()
        self.setup_daily_briefing_templates()

        # Generate summary
        report = self.generate_summary_report()

        print("\n" + "=" * 70)
        print("✅ PRODUCTION DEMO COMPLETE")
        print("=" * 70)
        print(f"\n📊 SUMMARY:")
        print(f"   Readings Ingested: {self.readings_ingested}")
        print(f"   Weekly Scripts Generated: {self.scripts_generated}")
        print(f"   Vault Location: {VAULT_ROOT}")
        print(f"\n📋 NEXT STEPS:")
        for i, step in enumerate(report["next_steps"], 1):
            print(f"   {i}. {step}")
        print("\n" + "=" * 70)

        self.logger.log(
            action="production_demo_complete",
            inputs={"semester_root": str(SEMESTER_ROOT)},
            outputs=report,
            status="completed",
        )

        return report


def main():
    runner = ProductionDemoRunner()
    return runner.run()


if __name__ == "__main__":
    main()
