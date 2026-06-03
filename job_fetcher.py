"""Job fetcher — pluggable backends: jobspy, remoteok, mock."""
import json
from typing import List, Dict, Any
import requests

SITE_MAP = {
    'linkedin': 'linkedin',
    'indeed': 'indeed',
    'glassdoor': 'glassdoor',
    'google': 'google',
    'ziprecruiter': 'zip_recruiter',
}

DEFAULT_SITES = ['linkedin', 'indeed', 'ziprecruiter', 'google']


def _fix_encoding(text: str) -> str:
    """Fix mojibake from Latin-1 -> UTF-8 double-encoding."""
    if not text:
        return ''
    try:
        return text.encode('latin1').decode('utf-8')
    except (UnicodeError, AttributeError):
        return text


def _strip_html(text: str) -> str:
    """Basic HTML tag stripping."""
    import re
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    return text


def _normalize_remoteok(job: dict) -> dict:
    """Convert RemoteOK job dict to our standard schema."""
    desc_raw = job.get('description', '')
    desc_fixed = _fix_encoding(desc_raw)
    desc_clean = _strip_html(desc_fixed)
    return {
        'id': f"remoteok-{job.get('id', '')}",
        'title': _fix_encoding(job.get('position', '')),
        'company': _fix_encoding(job.get('company', '')),
        'location': 'Remote',
        'description': desc_clean,
        'job_url': job.get('url', ''),
        'site': 'remoteok',
        'date_posted': '',
        'job_type': job.get('tags', []),
        'job_function': '',
        'job_level': '',
    }


def fetch_remoteok(search_term: str = '', limit: int = 20) -> List[Dict[str, Any]]:
    """Fetch from RemoteOK public API (no auth, works on Termux)."""
    url = 'https://remoteok.com/api'
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        'Accept': 'application/json',
    }
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    # First item is often meta, skip if not a job dict
    jobs = [j for j in data if isinstance(j, dict) and j.get('position')]

    # Simple keyword filter if search_term provided
    term = search_term.lower()
    if term:
        jobs = [j for j in jobs if term in j.get('position', '').lower() or term in j.get('description', '').lower()]

    return [_normalize_remoteok(j) for j in jobs[:limit]]


def fetch_with_jobspy(
    search_term: str,
    location: str = 'Remote',
    results_wanted: int = 20,
    hours_old: int = 72,
    country_indeed: str = 'USA',
    **kwargs
) -> List[Dict[str, Any]]:
    """Desktop Linux backend via python-jobspy."""
    try:
        from jobspy import scrape_jobs
    except Exception as e:
        raise RuntimeError(f"jobspy unavailable: {e}")

    df = scrape_jobs(
        site_name=[SITE_MAP.get(s, s) for s in DEFAULT_SITES],
        search_term=search_term,
        location=location,
        results_wanted=results_wanted,
        hours_old=hours_old,
        country_indeed=country_indeed,
        **kwargs
    )
    records = df.fillna('').to_dict(orient='records')
    return records


def fetch_mock(search_term: str = '', limit: int = 5) -> List[Dict[str, Any]]:
    """Return mock jobs for offline testing."""
    return [
        {
            'id': f'mock-{i}',
            'title': f'{search_term or "Software Engineer"} (Mock)',
            'company': f'Acme Corp {i}',
            'location': 'Remote',
            'description': f'We are looking for a talented engineer with python, react, and aws experience.',
            'job_url': 'https://example.com/job',
            'site': 'mock',
        }
        for i in range(limit)
    ]


def fetch_jobs(
    search_term: str,
    location: str = 'Remote',
    backend: str = 'auto',
    results_wanted: int = 20,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Fetch jobs using the best available backend.
    backend: 'auto' | 'jobspy' | 'remoteok' | 'mock'
    """
    if backend == 'mock':
        return fetch_mock(search_term, results_wanted)

    if backend == 'jobspy':
        return fetch_with_jobspy(search_term, location, results_wanted, **kwargs)

    if backend == 'remoteok':
        return fetch_remoteok(search_term, results_wanted)

    # auto: try jobspy, then remoteok, then mock
    if backend == 'auto':
        try:
            return fetch_with_jobspy(search_term, location, results_wanted, **kwargs)
        except Exception as e:
            print(f"jobspy failed ({e}), falling back to remoteok...")
            try:
                return fetch_remoteok(search_term, results_wanted)
            except Exception as e2:
                print(f"remoteok failed ({e2}), falling back to mock...")
                return fetch_mock(search_term, results_wanted)

    raise ValueError(f"Unknown backend: {backend}")


def job_to_text(job: dict) -> str:
    """Flatten a job dict into a single string for matching."""
    parts = [
        job.get('title', ''),
        job.get('description', ''),
        job.get('company', ''),
        job.get('job_type', ''),
        job.get('job_function', ''),
        job.get('job_level', ''),
    ]
    return ' '.join(str(p) for p in parts if p)


if __name__ == '__main__':
    import sys
    term = sys.argv[1] if len(sys.argv) > 1 else 'Software Engineer'
    be = sys.argv[2] if len(sys.argv) > 2 else 'auto'
    jobs = fetch_jobs(term, backend=be, results_wanted=10)
    print(f"Fetched {len(jobs)} jobs via {be}.")
    for j in jobs[:3]:
        print(f"- {j.get('title')} @ {j.get('company')} ({j.get('site')})")
