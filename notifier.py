"""Telegram notifier — sends job alerts."""
import asyncio
from typing import Dict

try:
    from telegram import Bot
except ImportError:
    Bot = None


def _escape_md(text: str) -> str:
    """Basic MarkdownV2 escaping for Telegram."""
    chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for c in chars:
        text = text.replace(c, f'\\{c}')
    return text


def format_job_message(job: dict, score_info: dict) -> str:
    title = _escape_md(job.get('title', 'Unknown'))
    company = _escape_md(job.get('company', 'Unknown'))
    location = _escape_md(job.get('location', 'Remote'))
    url = job.get('job_url', job.get('url', ''))
    score = score_info.get('score', 0)
    skills = score_info.get('matched_skills', [])
    skills_str = _escape_md(', '.join(skills[:8]) if skills else 'None')

    msg = (
        f"📋 *{title}*\n"
        f"🏢 {company} | \U0001f4cd {location}\n"
        f"⭐ Score: `{score}`\n"
        f"🎯 Skills: {skills_str}\n"
    )
    if url:
        msg += f"🔗 {url}\n"
    return msg


async def send_message_async(token: str, chat_id: str, text: str):
    if Bot is None:
        raise RuntimeError("python-telegram-bot not installed")
    bot = Bot(token)
    await bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode='MarkdownV2',
        disable_web_page_preview=False
    )


def send_message(token: str, chat_id: str, text: str):
    """Synchronous wrapper."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        asyncio.create_task(send_message_async(token, chat_id, text))
    else:
        asyncio.run(send_message_async(token, chat_id, text))


def notify_jobs(token: str, chat_id: str, jobs_with_scores: list):
    """Send multiple job notifications."""
    if not token or not chat_id:
        print("Telegram credentials missing, skipping notification.")
        return
    for job, score_info in jobs_with_scores:
        text = format_job_message(job, score_info)
        try:
            send_message(token, chat_id, text)
        except Exception as e:
            print(f"Failed to send message: {e}")


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 4:
        print("Usage: python notifier.py <token> <chat_id> <message>")
        sys.exit(1)
    send_message(sys.argv[1], sys.argv[2], sys.argv[3])
