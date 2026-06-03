#!/data/data/com.termux/files/usr/bin/env python3
"""Entry point for the job bot — run once or in a scheduled loop."""
import argparse
import sys
import time
from datetime import datetime

from config import load_config
from main import run_pipeline


def main():
    parser = argparse.ArgumentParser(description='Job Search Bot')
    parser.add_argument('--once', action='store_true', help='Run a single pass and exit')
    parser.add_argument('--interval', type=int, default=3600, help='Loop interval in seconds (default 3600)')
    parser.add_argument('--backend', type=str, default='auto', choices=['auto','jobspy','remoteok','mock'])
    args = parser.parse_args()

    cfg = load_config()
    if not cfg.get('resume_path'):
        print("ERROR: Set RESUME_PATH in .env")
        sys.exit(1)

    run_count = 0
    while True:
        run_count += 1
        print(f"\n=== Run #{run_count} at {datetime.utcnow().isoformat()}Z ===")
        try:
            run_pipeline(cfg)
        except Exception as e:
            print(f"Run failed: {e}")
            import traceback
            traceback.print_exc()

        if args.once:
            print("Single run complete. Exiting.")
            break

        print(f"Sleeping {args.interval}s...")
        time.sleep(args.interval)


if __name__ == '__main__':
    main()
