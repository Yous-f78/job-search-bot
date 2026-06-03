"""SQLite storage for job deduplication and history."""
import sqlite3
import json
from pathlib import Path
from datetime import datetime


def init_db(db_path: str = './job_bot.db') -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS jobs_seen (
            job_id TEXT PRIMARY KEY,
            title TEXT,
            company TEXT,
            site TEXT,
            url TEXT,
            score REAL,
            matched_skills TEXT,
            created_at TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS run_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_at TEXT,
            jobs_fetched INTEGER,
            jobs_new INTEGER,
            jobs_sent INTEGER
        )
    ''')
    conn.commit()
    return conn


def job_key(job: dict) -> str:
    """Stable dedup key from job data."""
    parts = [
        str(job.get('id', '')),
        str(job.get('title', '')),
        str(job.get('company', '')),
        str(job.get('site', '')),
    ]
    key = '|'.join(parts).strip()
    if not key or key == '|||':
        # fallback hash
        import hashlib
        key = hashlib.md5(json.dumps(job, sort_keys=True, default=str).encode()).hexdigest()
    return key


def is_new_job(conn: sqlite3.Connection, job: dict) -> bool:
    key = job_key(job)
    row = conn.execute('SELECT 1 FROM jobs_seen WHERE job_id = ?', (key,)).fetchone()
    return row is None


def record_job(conn: sqlite3.Connection, job: dict, score: float, matched_skills: list):
    key = job_key(job)
    conn.execute('''
        INSERT OR REPLACE INTO jobs_seen (job_id, title, company, site, url, score, matched_skills, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        key,
        job.get('title', '')[:200],
        job.get('company', '')[:200],
        job.get('site', ''),
        job.get('job_url', job.get('url', '')),
        score,
        json.dumps(matched_skills),
        datetime.utcnow().isoformat()
    ))
    conn.commit()


def log_run(conn: sqlite3.Connection, fetched: int, new_jobs: int, sent: int):
    conn.execute('''
        INSERT INTO run_log (run_at, jobs_fetched, jobs_new, jobs_sent)
        VALUES (?, ?, ?, ?)
    ''', (datetime.utcnow().isoformat(), fetched, new_jobs, sent))
    conn.commit()


if __name__ == '__main__':
    conn = init_db('./test_job_bot.db')
    print("DB initialized.")
    conn.close()
