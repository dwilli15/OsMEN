---
tags: [template, assignments, tracking]
type: assignment-tracker
---

# {{course_code}} Assignments

## Overview

| Metric | Value |
|--------|-------|
| **Total Assignments** | {{total_assignments}} |
| **Completed** | {{completed}} |
| **Pending** | {{pending}} |
| **Average Grade** | {{average_grade}}% |

## Assignment Tracker

| Status | # | Assignment | Due Date | Weight | Grade |
|--------|---|-----------|----------|--------|-------|
{{#each assignments}}
| {{status_icon}} | {{number}} | {{title}} | {{due_date}} | {{weight}}% | {{grade}} |
{{/each}}

### Status Legend
- ⬜ Not Started
- 🔄 In Progress
- ✅ Submitted
- ✔️ Graded

## Upcoming Deadlines

### This Week
{{#each this_week}}
- [ ] **{{due_date}}** - {{title}}
{{/each}}

### Next Week
{{#each next_week}}
- [ ] **{{due_date}}** - {{title}}
{{/each}}

## Assignment Details

{{#each assignments}}
### {{number}}. {{title}}
- **Due**: {{due_date}}
- **Weight**: {{weight}}%
- **Status**: {{status}}

**Description**:
> {{description}}

**Notes**:


---
{{/each}}

## Submission Checklist

For each assignment:
- [ ] Read requirements carefully
- [ ] Create outline/plan
- [ ] Complete first draft
- [ ] Review and edit
- [ ] Check formatting
- [ ] Submit before deadline
- [ ] Verify submission received

## Resources

### Assignment Help
- Office Hours: 
- TA Sessions: 
- Study Groups: 

### Templates & Examples
- 

---
*Tracked by OsMEN Course Manager*
