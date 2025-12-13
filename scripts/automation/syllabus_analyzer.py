#!/usr/bin/env python3
"""
Syllabus Analyzer - OsMEN Production Pipeline
=============================================
Parses course syllabus PDF, extracts required readings, matches against available files,
and suggests auxiliary materials marked explicitly as "AUXILIARY - not in syllabus".

Part of the OsMEN orchestration layer.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import pdfplumber

# Configure paths - should match integrations/orchestration.py patterns
SEMESTER_ROOT = Path(r"D:\semester_start")
SYLLABUS_PATH = SEMESTER_ROOT / "F25 HB Syllabus_Final.pdf"
OUTPUT_DIR = SEMESTER_ROOT / "vault" / "courses" / "HB411"


def extract_syllabus_text(pdf_path: Path) -> str:
    """Extract all text from syllabus PDF."""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n\n"
    return text


def parse_readings_from_text(text: str) -> dict:
    """Parse syllabus text to extract readings and course structure."""
    result = {
        "course_title": "",
        "instructor": "",
        "semester": "",
        "required_texts": [],
        "weekly_readings": {},
        "all_readings": set(),
    }

    # Extract course info
    if "HB 411" in text or "Healthy Boundaries" in text:
        result["course_title"] = "HB 411: Healthy Boundaries in Ministry"

    if "Fall 2025" in text or "F25" in text:
        result["semester"] = "Fall 2025"

    # Find instructor
    instructor_match = re.search(
        r"(?:Professor|Instructor|Dr\.|Rev\.)\s*:?\s*([A-Z][a-z]+\s+[A-Z][a-z]+)", text
    )
    if instructor_match:
        result["instructor"] = instructor_match.group(1)

    # Find required texts section
    required_section = re.search(
        r"(?:Required\s+(?:Texts?|Readings?|Books?)|Textbooks?)\s*[:\-]?\s*(.*?)(?:(?:Recommended|Additional|Course\s+Schedule|Weekly|Week\s+\d)|$)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if required_section:
        req_text = required_section.group(1)
        # Extract book titles
        books = re.findall(r"([A-Z][^.!?\n]{10,100}(?:by|By|\-)[^.!?\n]+)", req_text)
        for book in books:
            result["required_texts"].append(book.strip())

    # Find weekly readings
    # Pattern: Week X: Topic / Readings: ...
    week_pattern = re.compile(
        r"Week\s*(\d+)[:\s]+([^\n]+)(?:.*?(?:Readings?|Read)[:\s]*([^\n]+(?:\n(?!\s*Week)[^\n]+)*))?",
        re.IGNORECASE | re.DOTALL,
    )

    for match in week_pattern.finditer(text):
        week_num = int(match.group(1))
        topic = match.group(2).strip() if match.group(2) else ""
        readings = match.group(3).strip() if match.group(3) else ""

        result["weekly_readings"][week_num] = {"topic": topic, "readings": readings}

        # Add to all readings
        if readings:
            result["all_readings"].add(readings)

    # Also look for any author-title patterns
    author_title_pattern = re.compile(
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*[,\-]\s*["\']?([^"\'\n,]{5,80})["\']?',
        re.MULTILINE,
    )
    for match in author_title_pattern.finditer(text):
        author = match.group(1)
        title = match.group(2)
        if len(title) > 10:  # Filter out short matches
            result["all_readings"].add(f"{author} - {title}")

    result["all_readings"] = list(result["all_readings"])
    return result


def scan_available_materials(directory: Path) -> list[dict]:
    """Scan directory for available reading materials."""
    materials = []
    supported_extensions = {".pdf", ".epub", ".txt", ".docx", ".mobi"}

    for file_path in directory.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
            materials.append(
                {
                    "filename": file_path.name,
                    "path": str(file_path),
                    "format": file_path.suffix.lower().replace(".", ""),
                    "size_kb": file_path.stat().st_size // 1024,
                }
            )

    return materials


def match_readings_to_files(parsed_readings: dict, available_files: list[dict]) -> dict:
    """Match syllabus readings to available files."""
    matches = {"matched": [], "unmatched_readings": [], "extra_files": []}

    # Create searchable index of filenames
    file_keywords = {}
    for f in available_files:
        # Extract keywords from filename
        name_lower = f["filename"].lower()
        keywords = set(re.findall(r"[a-z]{3,}", name_lower))
        file_keywords[f["filename"]] = keywords

    # Known title-to-file mappings for this course
    known_mappings = {
        "saying no to say yes": ["Saying No to Say Yes", "saynotosayyes"],
        "set boundaries": ["Set Boundaries, Find Peace", "setboundariesfindpeace"],
        "what it takes to heal": ["What It Takes to Heal", "Prentis Hemphill"],
        "sacred wounds": ["Sacred Wounds"],
        "anxious generation": ["Anxious Generation"],
        "safe congregation": ["safe_congregation"],
        "fiduciary duty": ["Fiduciary", "Stephens"],
        "healthy boundaries": ["FaithTrust", "HealthyBoundaries201"],
        "spiritual care": ["Spiritual_Care"],
        "black lives matter": ["BlackLivesMatter"],
        "professional ethics": ["Professional Sexual Ethics"],
        "code of ethics": ["Common-Code-of-Ethics"],
        "leader misconduct": ["Responding to Spiritual Leader Misconduct"],
        "shared wisdom": ["Shared_Wisdom"],
        "crossing borders": ["CrossingBorde", "McGarrah"],
    }

    matched_files = set()

    # Try to match each reading
    for reading in parsed_readings.get("all_readings", []):
        reading_lower = reading.lower()
        found = False

        for keyword, file_patterns in known_mappings.items():
            if keyword in reading_lower:
                for pattern in file_patterns:
                    for f in available_files:
                        if pattern.lower() in f["filename"].lower():
                            if f["filename"] not in matched_files:
                                matches["matched"].append(
                                    {"reading": reading, "file": f}
                                )
                                matched_files.add(f["filename"])
                                found = True
                                break
                    if found:
                        break
            if found:
                break

        if not found:
            matches["unmatched_readings"].append(reading)

    # Find files not matched to any reading
    for f in available_files:
        if f["filename"] not in matched_files:
            matches["extra_files"].append(f)

    return matches


def generate_auxiliary_suggestions(
    course_topic: str, existing_titles: list[str]
) -> list[dict]:
    """Generate 10 auxiliary reading suggestions marked as NOT in syllabus."""
    # These are curated suggestions for a Healthy Boundaries in Ministry course
    # In production, this could query a knowledge base or use LLM

    suggestions = [
        {
            "title": "Boundaries: When to Say Yes, How to Say No to Take Control of Your Life",
            "author": "Henry Cloud & John Townsend",
            "why": "Classic foundational text on boundary-setting from psychological perspective",
            "status": "AUXILIARY - not in syllabus",
        },
        {
            "title": "The Body Keeps the Score",
            "author": "Bessel van der Kolk",
            "why": "Understanding trauma's physical manifestations - critical for pastoral care",
            "status": "AUXILIARY - not in syllabus",
        },
        {
            "title": "When Helping Hurts: How to Alleviate Poverty Without Hurting the Poor... and Yourself",
            "author": "Steve Corbett & Brian Fikkert",
            "why": "Explores unintended consequences of well-meaning ministry interventions",
            "status": "AUXILIARY - not in syllabus",
        },
        {
            "title": "Burnout: The Secret to Unlocking the Stress Cycle",
            "author": "Emily Nagoski & Amelia Nagoski",
            "why": "Research-based approach to managing stress in helping professions",
            "status": "AUXILIARY - not in syllabus",
        },
        {
            "title": "Ministry Greenhouse: Cultivating Environments for Practical Learning",
            "author": "George M. Hillman Jr.",
            "why": "Practical frameworks for supervised ministry with boundary awareness",
            "status": "AUXILIARY - not in syllabus",
        },
        {
            "title": "Is Nothing Sacred? When Sex Invades the Pastoral Relationship",
            "author": "Marie M. Fortune",
            "why": "Seminal work on clergy sexual misconduct - deeper than typical ethics course",
            "status": "AUXILIARY - not in syllabus",
        },
        {
            "title": "Safe People: How to Find Relationships That Are Good for You",
            "author": "Henry Cloud & John Townsend",
            "why": "Practical guide for identifying healthy relationships - applicable to ministry",
            "status": "AUXILIARY - not in syllabus",
        },
        {
            "title": "Clergy Killers: Guidance for Pastors and Congregations Under Attack",
            "author": "G. Lloyd Rediger",
            "why": "Understanding toxic dynamics in faith communities",
            "status": "AUXILIARY - not in syllabus",
        },
        {
            "title": "Self-Care and the Helping Professions",
            "author": "Thomas M. Skovholt & Michelle Trotter-Mathison",
            "why": "Evidence-based self-care strategies for sustained ministry",
            "status": "AUXILIARY - not in syllabus",
        },
        {
            "title": "Restoring the Soul of a Church: Healing Congregations Wounded by Clergy Sexual Misconduct",
            "author": "Nancy Hopkins & Mark Laaser",
            "why": "Congregational recovery after boundary violations",
            "status": "AUXILIARY - not in syllabus",
        },
    ]

    return suggestions


def generate_analysis_report(
    syllabus_path: Path, parsed: dict, matches: dict, auxiliary: list[dict]
) -> dict:
    """Generate comprehensive analysis report."""

    report = {
        "metadata": {
            "generated": datetime.now().isoformat(),
            "syllabus_file": str(syllabus_path),
            "analyzer_version": "1.0.0",
        },
        "course_info": {
            "title": parsed.get("course_title", "Unknown"),
            "semester": parsed.get("semester", "Unknown"),
            "instructor": parsed.get("instructor", "Unknown"),
        },
        "reading_analysis": {
            "total_readings_identified": len(parsed.get("all_readings", [])),
            "files_matched": len(matches.get("matched", [])),
            "files_unmatched": len(matches.get("unmatched_readings", [])),
            "extra_available_files": len(matches.get("extra_files", [])),
        },
        "matched_readings": matches.get("matched", []),
        "needs_acquisition": matches.get("unmatched_readings", []),
        "available_extras": matches.get("extra_files", []),
        "auxiliary_suggestions": auxiliary,
        "weekly_schedule": parsed.get("weekly_readings", {}),
    }

    return report


def display_report(report: dict) -> str:
    """Format report for human-readable display."""
    lines = []
    lines.append("=" * 70)
    lines.append("SYLLABUS ANALYSIS REPORT")
    lines.append(f"Generated: {report['metadata']['generated']}")
    lines.append("=" * 70)
    lines.append("")

    # Course Info
    lines.append("📚 COURSE INFORMATION")
    lines.append("-" * 40)
    lines.append(f"  Title: {report['course_info']['title']}")
    lines.append(f"  Semester: {report['course_info']['semester']}")
    lines.append(f"  Instructor: {report['course_info']['instructor']}")
    lines.append("")

    # Summary Stats
    lines.append("📊 ANALYSIS SUMMARY")
    lines.append("-" * 40)
    analysis = report["reading_analysis"]
    lines.append(f"  Readings Identified: {analysis['total_readings_identified']}")
    lines.append(f"  Files Matched: {analysis['files_matched']}")
    lines.append(f"  Needs Acquisition: {analysis['files_unmatched']}")
    lines.append(f"  Extra Available: {analysis['extra_available_files']}")
    lines.append("")

    # Matched Readings
    lines.append("✅ MATCHED READINGS (Available)")
    lines.append("-" * 40)
    for item in report.get("matched_readings", []):
        lines.append(f"  • {item['file']['filename']}")
        lines.append(
            f"    Format: {item['file']['format'].upper()}, Size: {item['file']['size_kb']}KB"
        )
    lines.append("")

    # Unmatched (needs acquisition)
    if report.get("needs_acquisition"):
        lines.append("⚠️ NEEDS ACQUISITION")
        lines.append("-" * 40)
        for reading in report["needs_acquisition"]:
            lines.append(f"  • {reading}")
        lines.append("")

    # Available extras
    if report.get("available_extras"):
        lines.append("📁 ADDITIONAL AVAILABLE FILES")
        lines.append("-" * 40)
        for f in report["available_extras"]:
            lines.append(
                f"  • {f['filename']} ({f['format'].upper()}, {f['size_kb']}KB)"
            )
        lines.append("")

    # Auxiliary Suggestions
    lines.append("🔖 AUXILIARY SUGGESTIONS")
    lines.append("-" * 40)
    lines.append("  These are NOT in the syllabus but may enhance learning:")
    lines.append("")
    for i, aux in enumerate(report.get("auxiliary_suggestions", []), 1):
        lines.append(f"  {i}. {aux['title']}")
        lines.append(f"     Author: {aux['author']}")
        lines.append(f"     Why: {aux['why']}")
        lines.append(f"     ⚡ {aux['status']}")
        lines.append("")

    lines.append("=" * 70)
    lines.append("END OF REPORT")
    lines.append("=" * 70)

    return "\n".join(lines)


def main():
    """Main entry point for syllabus analyzer."""
    print("🔍 OsMEN Syllabus Analyzer")
    print("=" * 50)

    # Verify syllabus exists
    if not SYLLABUS_PATH.exists():
        print(f"❌ Syllabus not found: {SYLLABUS_PATH}")
        return None

    print(f"📄 Parsing syllabus: {SYLLABUS_PATH.name}")

    # Extract text
    syllabus_text = extract_syllabus_text(SYLLABUS_PATH)
    print(f"   Extracted {len(syllabus_text)} characters of text")

    # Parse readings
    parsed = parse_readings_from_text(syllabus_text)
    print(f"   Found {len(parsed['all_readings'])} reading references")

    # Scan available materials
    print(f"\n📁 Scanning available materials in {SEMESTER_ROOT}")
    available = scan_available_materials(SEMESTER_ROOT)
    print(f"   Found {len(available)} files")

    # Match readings to files
    print("\n🔗 Matching readings to available files...")
    matches = match_readings_to_files(parsed, available)
    print(f"   Matched: {len(matches['matched'])}")
    print(f"   Unmatched: {len(matches['unmatched_readings'])}")

    # Generate auxiliary suggestions
    print("\n💡 Generating auxiliary suggestions...")
    auxiliary = generate_auxiliary_suggestions(
        parsed.get("course_title", ""),
        [m["file"]["filename"] for m in matches["matched"]],
    )

    # Generate report
    report = generate_analysis_report(SYLLABUS_PATH, parsed, matches, auxiliary)

    # Display report
    print("\n" + display_report(report))

    # Save report
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = OUTPUT_DIR / "syllabus_analysis.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n💾 Report saved to: {report_path}")

    # Also save human-readable version
    readable_path = OUTPUT_DIR / "syllabus_analysis.md"
    with open(readable_path, "w", encoding="utf-8") as f:
        f.write(display_report(report))
    print(f"📝 Readable report saved to: {readable_path}")

    return report


if __name__ == "__main__":
    report = main()
