---
type: briefing_script
date: {{date}}
duration_target: 90
word_count_target: 225
voice: af_nicole
generated: false
audio_path: ""
---

# 🎙️ Daily Briefing Script - {{date}}

## Source Data

### From AM Check-In

- Energy: {{am_energy}}/10
- Focus Capacity: {{am_focus}}
- Top Priorities: {{am_priorities}}
- ADHD Strategy: {{am_adhd_strategy}}

### From Previous PM Check-In

- Productivity Rate: {{pm_productivity}}%
- Mood Trend: {{pm_mood}}
- Carryover Tasks: {{pm_carryover}}
- Tomorrow Focus: {{pm_tomorrow_focus}}

### Course Context

- Week: {{course_week}}
- Topic: {{week_topic}}
- Readings Due: {{readings_due}}
- Days Until Class: {{days_to_class}}

---

## Script (90 Seconds / ~225 Words)

### Opening (10 sec)

Good morning. It's {{day_name}}, {{date_formatted}}. Here's your 90-second focus briefing.

### Energy Check (15 sec)

{{#if low_energy}}
Your energy is at {{am_energy}} today. Start with something energizing—movement, music, or a quick win. Protect your peak hours for priority work.
{{else}}
You're at {{am_energy}} energy today. Good foundation. Channel it into your top priority early.
{{/if}}

### Priority Focus (20 sec)

Your number one today: {{priority_1}}.
{{#if priority_2}}Second: {{priority_2}}.{{/if}}
Block focused time for these. Everything else can wait or be delegated.

### ADHD Strategy (15 sec)

{{adhd_tip}}

### Course Update (15 sec)

{{#if readings_behind}}
You're {{readings_behind}} readings behind for Week {{course_week}}. Consider audiobook during commute or chores.
{{else if readings_due_today}}
{{readings_due_today}} is due for class. Schedule reading time today.
{{else}}
On track with Week {{course_week}}: {{week_topic}}. Nice work.
{{/if}}

### Meditation Reminder (10 sec)

{{#if meditation_planned}}
{{meditation_type}} practice is planned. Protect that time. Your practice is your anchor.
{{else}}
Remember your practice commitments. Even 10 minutes of Trekchö shifts the day.
{{/if}}

### Boundary Reflection (10 sec)

{{boundary_reminder}}

### Closing (5 sec)

You've got this. Check in tonight. Have a focused day.

---

## Generation Notes

### Variables Required

```yaml
# User State (from check-ins)
am_energy: 7
am_focus: "medium"
am_priorities: ["Reading Response 3", "McBride Ch 5-6"]
am_adhd_strategy: "Body doubling for reading"
pm_productivity: 75
pm_mood: "stable"
pm_carryover: ["Email catch-up"]
pm_tomorrow_focus: "Deep reading block"

# Course State (from system)
course_week: 6
week_topic: "Boundaries & Self Systems II"
readings_due: ["Tawwab Ch 7-8", "McBride Ch 5-6"]
readings_behind: 0
days_to_class: 2

# Meditation State
meditation_planned: true
meditation_type: "Tummo"

# Generated Content
adhd_tip: "Use visual timer for reading blocks. Start with 15-minute sprints."
boundary_reminder: "Notice where you say yes when you mean no today."
```

### Audio Generation Command

```bash
python -m agents.audiobook_creator.tts_generator \
  --input "briefing_scripts/{{date}}.txt" \
  --output "daily_briefings/{{date}}_briefing.mp3" \
  --voice af_nicole \
  --speed 1.1
```

---

## Workflow Triggers

1. **Input**: AM Check-In completed
2. **Process**: Merge AM + previous PM + course state
3. **Generate**: Fill template variables
4. **Synthesize**: Generate audio via Kokoro TTS
5. **Notify**: Alert user briefing is ready
6. **Log**: Record generation in logs/audio_generations/

---

*Template version: 1.0*
*Last updated: 2025-12-10*
