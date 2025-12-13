# TTS Workflow Documentation

## Overview

Defines timing rules for TTS generation.

## Weekly Podcast Scripts

- Generation: scripts generated at semester start
- Review: user reviews/edits before TTS
- TTS: only after manual approval
- Location: `vault/audio/weekly_scripts/`

## Daily 90-Second Briefings

- Trigger: AM Check-In finalization
- Generation: automatic after check-in is marked complete
- TTS: immediate after generation
- Location: `vault/audio/daily_briefings/`

## Rules

1. Never generate TTS for weekly scripts without user review
2. Always generate TTS for daily briefings after check-in finalization
3. Weekly scripts are for preparation; daily briefings are for immediate use
