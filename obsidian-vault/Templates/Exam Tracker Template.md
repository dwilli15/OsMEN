---
tags: [template, exams, tracking]
type: exam-tracker
---

# {{course_code}} Exams

## Overview

| Metric | Value |
|--------|-------|
| **Total Exams** | {{total_exams}} |
| **Completed** | {{completed}} |
| **Upcoming** | {{upcoming}} |
| **Average Score** | {{average_score}}% |

## Exam Schedule

| Status | Exam | Date | Time | Location | Weight | Score |
|--------|------|------|------|----------|--------|-------|
{{#each exams}}
| {{status_icon}} | {{title}} | {{date}} | {{time}} | {{location}} | {{weight}}% | {{score}} |
{{/each}}

### Status Legend
- ⬜ Upcoming
- 📖 Studying
- ✅ Completed

## Exam Details

{{#each exams}}
### {{title}}
- **Date**: {{date}}
- **Time**: {{time}}
- **Location**: {{location}}
- **Weight**: {{weight}}%
- **Format**: {{format}}
- **Duration**: {{duration}} minutes

**Topics Covered**:
{{#each topics}}
- [ ] {{this}}
{{/each}}

**Study Resources**:
- Lecture Notes: 
- Practice Problems: 
- Past Exams: 

**Study Plan**:
- [ ] Review lecture notes
- [ ] Complete practice problems
- [ ] Review homework solutions
- [ ] Take practice exam
- [ ] Create summary sheet

---
{{/each}}

## Study Timeline

### 2 Weeks Before
- [ ] Gather all materials
- [ ] Identify weak topics
- [ ] Create study schedule
- [ ] Form study group

### 1 Week Before
- [ ] Complete first review pass
- [ ] Practice problems daily
- [ ] Attend office hours
- [ ] Take practice exam

### 2-3 Days Before
- [ ] Focus on weak areas
- [ ] Review formula sheet
- [ ] Get questions answered
- [ ] Final practice problems

### Day Before
- [ ] Light review only
- [ ] Prepare materials (calculator, pencils, etc.)
- [ ] Get good sleep
- [ ] Check exam time/location

### Exam Day
- [ ] Eat breakfast
- [ ] Arrive early
- [ ] Stay calm, breathe
- [ ] Read all instructions

## Performance Tracking

| Exam | Predicted | Actual | Difference |
|------|-----------|--------|------------|
{{#each exams}}
| {{title}} | | {{score}}% | |
{{/each}}

## Post-Exam Review

### What Worked
- 

### What to Improve
- 

### Notes for Next Exam
- 

---
*Tracked by OsMEN Course Manager*
