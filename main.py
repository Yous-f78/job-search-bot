"""Main orchestrator — run the job search pipeline."""
import sys
import traceback
from pathlib import Path

from config import load_config
from resume_parser import parse_resume
from job_fetcher import fetch_jobs, job_to_text
from matcher import score_job
from database import init_db, is_new_job, record_job, log_run
from notifier import notify_jobs


def run_pipeline(cfg: dict):
    db_path = cfg.get('db_path', './job_bot.db')
    conn = init_db(db_path)

    # 1. Parse resume
    print(f"[1/5] Parsing resume: {cfg['resume_path']}")
    resume = parse_resume(cfg['resume_path'])
    print(f"      Found {resume['skill_count']} skills: {', '.join(s for s, _ in resume['top_skills'][:5])}...")

    # 2. Fetch jobs
    print(f"[2/5] Fetching jobs for '{cfg['job_title']}' in '{cfg['job_location']}'...")
    fetched = fetch_jobs(
        search_term=cfg['job_title'],
        location=cfg['job_location'],
        results_wanted=cfg['max_daily_jobs'],
        hours_old=72,
        countries=cfg.get('countries', ['USA']),
    )
    print(f"      Fetched {len(fetched)} jobs.")

    # 3. Score & filter
    print(f"[3/5] Scoring against resume (threshold={cfg['score_threshold']})...")
    scored = []
    for job in fetched:
        text = job_to_text(job)
        if not text.strip():
            continue
        info = score_job(resume, text)
        if info['score'] >= cfg['score_threshold']:
            scored.append((job, info))

    scored.sort(key=lambda x: x[1]['score'], reverse=True)
    print(f"      {len(scored)} jobs passed threshold.")

    # 4. Deduplicate
    print("[4/5] Deduplicating...")
    new_jobs = []
    for job, info in scored:
        if is_new_job(conn, job):
            new_jobs.append((job, info))
            record_job(conn, job, info['score'], info['matched_skills'])
    print(f"      {len(new_jobs)} new jobs.")

    # 5. Notify
    print("[5/5] Notifying...")
    if cfg['dry_run']:
        print("      DRY RUN — not sending Telegram messages.")
        for job, info in new_jobs[:5]:
            print(f"      Would send: {job.get('title')} @ {job.get('company')} (score={info['score']})")
    else:
        notify_jobs(cfg['telegram_bot_token'], cfg['telegram_chat_id'], new_jobs)
        print(f"      Sent {len(new_jobs)} notifications.")

    log_run(conn, len(fetched), len(new_jobs), len(new_jobs) if not cfg['dry_run'] else 0)
    conn.close()
    print("Done.")


if __name__ == '__main__':
    cfg = load_config()
    if not cfg.get('resume_path'):
        print("ERROR: Set RESUME_PATH in .env")
        sys.exit(1)
    try:
        run_pipeline(cfg)
    except Exception as e:
        print(f"Pipeline failed: {e}")
        traceback.print_exc()
        sys.exit(1)
