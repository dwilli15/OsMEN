---
type: briefing_script
date: "{{date}}"
generated_at: "{{time}}"
tags: [briefing, daily, audio]
---

# Daily Briefing Script | {{date}}

> 90-second personalized audio briefing generated from check-in data

## Context Used

| Source | Status | Data Points |
|--------|--------|-------------|
| Today's AM Check-in | {{am_status}} | Energy, Priorities, ADHD state |
| Yesterday's PM Check-in | {{pm_status}} | Carryover, Tomorrow prep |
| 3-Day History | {{history_count}} check-ins | Energy trends, Patterns |
| Syllabus | Week {{course_week}} | Readings, Deadlines |
| Progress Tracker | {{readings_status}} | Behind/On track |

---

## Script (Target: 90 seconds, ~225 words)

### Opening (10 sec / ~25 words)

Good morning. It's {{day_name}}, {{date_formatted}}. Here's your 90-second focus briefing.

### Energy & Trend (15 sec / ~40 words)

{{energy_section}}

### Carryover & Priorities (20 sec / ~50 words)

{{carryover_section}}

{{priority_section}}

### ADHD Strategy (15 sec / ~35 words)

{{adhd_tip}}

### Course Update (15 sec / ~35 words)

{{course_section}}

### Practice Reminder (10 sec / ~25 words)

{{meditation_section}}

### Boundary Reflection (10 sec / ~25 words)

{{boundary_reminder}}

### Closing (5 sec / ~15 words)

You've got this. Check in tonight to close the loop. Have a focused day.

---

## Audio Generation

- **Target duration**: 90 seconds
- **Word count**: ~225 words
- **Speaking rate**: 2.5 words/second (conversational)
- **Tone**: Warm, grounded, encouraging
- **Voice**: {{voice_profile}}
- **Output format**: MP3 (128kbps)
- **Background**: None (speech only)

## Data Sources

```yaml
am_checkin: "{{am_checkin_path}}"
pm_checkin: "{{pm_checkin_path}}"
briefings_referenced: {{briefings_count}}
syllabus: "course_data.json"
progress: "goals/hb411_progress.md"
adhd_dashboard: "goals/adhd_dashboard.md"
```

## Generation Metadata

- Generator version: 2.0 (production)
- Context window: 3 days
- Carryover items: {{carryover_count}}
- Pending tasks: {{pending_count}}
- Energy trend: {{energy_trend}}
