#!/data/data/com.termux/files/usr/bin/sh
# Auto-commit script for job-search-bot
# Usage: ./auto_commit.sh [commit_message]

PROJECT_DIR="/data/data/com.termux/files/home/job_bot"
TOKEN_FILE="/data/data/com.termux/files/home/.github_token"
REPO="https://github.com/Yous-f78/job-search-bot"

cd "$PROJECT_DIR" || exit 1

# Check for changes
if git diff --quiet && git diff --cached --quiet; then
    echo "No changes to commit."
    exit 0
fi

MSG="${1:-Update $(date -Iseconds)}"

# Stage, commit, push with token
git add -A
git commit -m "$MSG"
git push "https://$(cat "$TOKEN_FILE")@github.com/Yous-f78/job-search-bot.git" main

echo "Pushed: $MSG"
