import os
from pathlib import Path

def load_config():
    """Load configuration from environment or .env file."""
    # Try to load .env if python-dotenv available, else rely on env vars
    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parent / '.env')
    except Exception:
        pass

    return {
        'telegram_bot_token': os.getenv('TELEGRAM_BOT_TOKEN', ''),
        'telegram_chat_id': os.getenv('TELEGRAM_CHAT_ID', ''),
        'resume_path': os.getenv('RESUME_PATH', './resume.pdf'),
        'job_title': os.getenv('JOB_TITLE', ''),
        'job_location': os.getenv('JOB_LOCATION', 'Remote'),
        'countries': [c.strip() for c in os.getenv('COUNTRIES', 'USA').split(',')],
        'score_threshold': float(os.getenv('SCORE_THRESHOLD', '0.35')),
        'max_daily_jobs': int(os.getenv('MAX_DAILY_JOBS', '20')),
        'dry_run': os.getenv('DRY_RUN', 'true').lower() in ('1', 'true', 'yes'),
        'db_path': os.getenv('DB_PATH', './job_bot.db'),
    }
