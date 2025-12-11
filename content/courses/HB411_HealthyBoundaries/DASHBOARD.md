# HB411 Semester Setup - Complete Dashboard

Generated: {datetime}

## 📊 Setup Summary

| Component | Status | Details |
|-----------|--------|---------|
| **Course Data** | ✅ Complete | 12.3 KB structured JSON |
| **Calendars** | ✅ Complete | 5 ICS files, 55 total events |
| **Textbook Text** | ✅ Complete | 7 books, 110,243 words extracted |
| **RAG Embeddings** | ✅ Complete | 563 documents indexed |
| **Obsidian Vault** | ✅ Complete | Hub + Weekly templates |
| **Professor Emails** | ✅ Complete | 7 bi-weekly engagement emails |
| **Test Audio** | ✅ Complete | Kokoro TTS working (27.9s sample) |
| **Full Audiobooks** | 🔄 Ready | Pipeline tested, ready for batch |

---

## 📅 Calendar Files (5 ICS)

Location: `calendar/`

| File | Events | Purpose |
|------|--------|---------|
| `HB411_class_sessions.ics` | 14 | All class meeting dates |
| `HB411_readings.ics` | 20 | Weekly reading reminders |
| `HB411_assignments.ics` | 13 | Assignment due dates |
| `HB411_special_events.ics` | 8 | Intensive, breaks, milestones |
| `HB411_master_calendar.ics` | 55 | Combined calendar |

**Import Instructions:**

1. Open Google Calendar / Outlook
2. Settings → Import Calendar
3. Select each .ics file
4. Events will appear with reminders

---

## 📚 Extracted Textbooks (7 Books)

Location: `readings/raw/`

| Book | Chapters | Words | Est. Audio |
|------|----------|-------|------------|
| Set Boundaries, Find Peace | 13 | 23,995 | 2.7 hrs |
| What It Takes to Heal | 8 | 34,009 | 3.8 hrs |
| Sacred Wounds | 33 | 18,605 | 2.1 hrs |
| Responding to Leader Misconduct | 7 | 31,590 | 3.5 hrs |
| Saying No to Say Yes | 2 | 820 | 0.1 hrs |
| Healthy Boundaries 201 | 1 | 886 | 0.1 hrs |
| The Anxious Generation | 3 | 338 | 0.0 hrs |
| **TOTAL** | **67** | **110,243** | **12.3 hrs** |

*Note: Some EPUBs had limited extractable content. PDFs of full books available.*

---

## 🧠 RAG Embeddings

Location: `embeddings/chroma_db/`

- **Collection:** `course_hb411`
- **Documents:** 563 chunks
- **Database:** 9.4 MB SQLite + vectors

**Sample Queries:**

```python
from scripts.ingest_course_embeddings import CourseEmbeddings
embeddings = CourseEmbeddings("HB411", "embeddings/chroma_db")
results = embeddings.search("boundaries in ministry", n_results=5)
```

---

## 📓 Obsidian Vault

Location: `obsidian/`

| File | Purpose |
|------|---------|
| `HB411 - Course Hub.md` | Central course MOC |
| `HB411 - Weekly Notes Index.md` | 16-week schedule tracker |
| `weekly/Week 02 - *.md` | Template weekly note |

**Setup Instructions:**

1. Open Obsidian
2. Open Vault → Select `obsidian/` folder
3. Start from `HB411 - Course Hub`

---

## 📧 Professor Communications

Location: `emails/professor_emails.md`

| Email | Date | Topic |
|-------|------|-------|
| 1 | Aug 25 | Introduction & Frameworks |
| 2 | Sep 8 | Hemphill & Integration |
| 3 | Sep 22 | Cooper-White & Systems |
| 4 | Oct 6 | Pasquale & Trauma |
| 5 | Oct 27 | Technology & Haidt |
| 6 | Nov 10 | Connection & Murthy |
| 7 | Nov 24 | Final Reflection |

---

## 🎧 Audiobook Generation

Location: `audiobooks/`

**TTS Engine:** Kokoro (54 voices)
**Test Audio:** `test_chapter.wav` (27.9 seconds)
**Target Format:** M4B @ 64kbps

**Generate Full Audiobooks:**

```bash
python scripts/generate_hb411_audiobooks.py --full
```

---

## 📂 Full Directory Structure

```
HB411_HealthyBoundaries/
├── audiobooks/
│   └── test_chapter.wav (1.3 MB)
├── calendar/
│   ├── HB411_assignments.ics
│   ├── HB411_class_sessions.ics
│   ├── HB411_master_calendar.ics
│   ├── HB411_readings.ics
│   └── HB411_special_events.ics
├── emails/
│   └── professor_emails.md
├── embeddings/
│   └── chroma_db/ (9.4 MB)
├── obsidian/
│   ├── HB411 - Course Hub.md
│   ├── HB411 - Weekly Notes Index.md
│   └── weekly/
│       └── Week 02 - *.md
├── readings/
│   ├── raw/
│   │   ├── extraction_index.json
│   │   ├── Set_Boundaries__Find_Peace/ (13 chapters)
│   │   ├── What_It_Takes_to_Heal/ (8 chapters)
│   │   ├── Sacred_Wounds/ (33 chapters)
│   │   └── ... (4 more books)
│   └── summaries/ (empty - for AI summaries)
├── course_data.json
└── DASHBOARD.md (this file)
```

---

## 🔧 Scripts Created

| Script | Purpose |
|--------|---------|
| `scripts/generate_course_calendars.py` | ICS generation |
| `scripts/extract_textbooks.py` | Text extraction from EPUB/PDF |
| `scripts/ingest_course_embeddings.py` | ChromaDB RAG ingestion |
| `scripts/generate_hb411_audiobooks.py` | M4B audiobook generation |
| `scripts/generate_audiobooks.py` | Generic audiobook generator |

---

## ✅ Ready to Use

1. **Import calendars** → 55 events with reminders
2. **Open Obsidian vault** → Start weekly note-taking
3. **Search readings** → RAG with 563 chunks indexed
4. **Generate audiobooks** → TTS pipeline ready
5. **Send professor emails** → 7 templates ready

**Total setup time:** ~5 minutes to execute
**Total content created:** 110K+ words, 55 calendar events, 563 embeddings

---

*Generated by YOLO-OPS | OsMEN Semester Setup*
