"""
WSGI entry point for the Flask web application.
When deployed (single gunicorn process), auto-starts the Discord selfbot too.
"""

import os
import logging
import threading
import subprocess
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

from app import app as application

logging.info("SelfBot Host web interface starting via WSGI")

def _start_discord_bot():
    token = os.environ.get('TOKEN', '').strip()
    if not token:
        logging.warning("TOKEN not set — Discord bot will not start.")
        return

    logging.info("Launching Discord selfbot in background...")
    env = os.environ.copy()
    env['DISABLE_WEB_SERVER'] = '1'

    try:
        proc = subprocess.Popen(
            [sys.executable, 'main.py'],
            env=env,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        logging.info(f"Discord bot started (PID {proc.pid})")
        proc.wait()
        logging.warning(f"Discord bot exited (PID {proc.pid})")
    except Exception as e:
        logging.error(f"Failed to start Discord bot: {e}")


# Auto-start bot unless:
# - We're a hosted-account subprocess (has HOSTED_ACCOUNT_ID)
# - Or the main bot is already running separately (BOT_MANAGED_EXTERNALLY set)
_is_hosted_subprocess = bool(os.environ.get('HOSTED_ACCOUNT_ID'))
_externally_managed = bool(os.environ.get('BOT_MANAGED_EXTERNALLY'))

if not _is_hosted_subprocess and not _externally_managed:
    _bot_thread = threading.Thread(target=_start_discord_bot, daemon=True, name='discord-bot')
    _bot_thread.start()

__all__ = ['application']
