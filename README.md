# Job Bot

Lightweight job search automation for Android/Termux.

## What it does
1. Parses your resume (PDF or DOCX) and extracts skills.
2. Fetches remote jobs from RemoteOK API (no auth required).
3. Scores each job against your resume using:
   - Skill keyword Jaccard overlap
   - Cosine similarity of term frequency vectors
4. Filters by configurable score threshold, deduplicates via SQLite.
5. Sends Telegram notifications for matching jobs.

## Files
- `config.py` — Load config from `.env`
- `resume_parser.py` — Extract text/skills from resume
- `job_fetcher.py` — Pluggable backends: jobspy, remoteok, mock
- `matcher.py` — Lightweight scoring engine
- `database.py` — SQLite dedup + run logs
- `notifier.py` — Telegram alerts
- `main.py` — Full pipeline orchestrator
- `start_bot.py` — Entry point, supports `--once` or scheduled loop

## Quick Start

1. Copy `.env.example` to `.env` and fill in:
```bash
cp .env.example .env
nano .env
```

2. Set your resume path (PDF or DOCX):
```
RESUME_PATH=/path/to/your_resume.pdf
JOB_TITLE=Software Engineer
JOB_LOCATION=Remote
```

3. (Optional) Add Telegram bot token + chat ID for alerts.
4. Run once:
```bash
python3 start_bot.py --once --backend remoteok
```
5. Or loop every hour:
```bash
python3 start_bot.py --interval 3600 --backend remoteok
```

## Backends
- `remoteok` — Works on Termux/Android (default recommended)
- `jobspy` — Desktop Linux only (broken on Termux due to tls-client)
- `mock` — Offline test data
- `auto` — Tries jobspy, falls back to remoteok, then mock

## Limitations
- RemoteOK is *remote-only* — no location filtering.
- JobSpy (LinkedIn/Indeed/ZipRecruiter/Glassdoor) does not work on Android/Termux.
- Fair Use: do not auto-submit applications — notify only.
