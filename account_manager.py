"""
Multi-Account Manager for Discord Selfbot Hosting Platform
Spawns and manages separate bot processes for each hosted account
"""

import os
import subprocess
import signal
import requests
import time
import logging
from datetime import datetime
from crypto import decrypt_token, is_encrypted

logger = logging.getLogger(__name__)

DISCORD_API = "https://discord.com/api/v9"


def validate_token(token: str) -> dict | None:
    """Validate a Discord token and return user info + ping, or None if invalid."""
    try:
        headers = {
            "Authorization": token,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        t0 = time.time()
        resp = requests.get(f"{DISCORD_API}/users/@me", headers=headers, timeout=10)
        ping_ms = int((time.time() - t0) * 1000)

        if resp.status_code == 200:
            data = resp.json()
            user_id = data.get("id")
            username = data.get("username", "Unknown")
            discriminator = data.get("discriminator", "0")
            avatar_hash = data.get("avatar")
            bio = data.get("bio", "")

            if avatar_hash:
                avatar_url = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.png?size=256"
            else:
                default_idx = (int(user_id) >> 22) % 6
                avatar_url = f"https://cdn.discordapp.com/embed/avatars/{default_idx}.png"

            return {
                "discord_id": user_id,
                "username": username,
                "discriminator": discriminator,
                "avatar_url": avatar_url,
                "bio": bio,
                "ping_ms": ping_ms,
            }
        return None
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        return None


def start_account_process(token: str, account_id: int) -> int | None:
    """Spawn an isolated bot process for the given token. Returns PID or None."""
    try:
        # Decrypt if stored as ciphertext
        plain_token = decrypt_token(token) if is_encrypted(token) else token

        env = os.environ.copy()
        env["TOKEN"] = plain_token
        env["HOSTED_ACCOUNT_ID"] = str(account_id)
        env["DISABLE_WEB_SERVER"] = "1"

        proc = subprocess.Popen(
            ["python", "main.py"],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        logger.info(f"Started bot PID {proc.pid} for account #{account_id}")
        return proc.pid
    except Exception as e:
        logger.error(f"Failed to start bot process: {e}")
        return None


def stop_account_process(pid: int) -> bool:
    """Gracefully stop a bot process."""
    if not pid:
        return False
    try:
        os.kill(pid, signal.SIGTERM)
        time.sleep(1)
        try:
            os.kill(pid, 0)        # still alive?
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        return True
    except ProcessLookupError:
        return True
    except Exception as e:
        logger.error(f"Error stopping process {pid}: {e}")
        return False


def is_process_running(pid: int) -> bool:
    """Return True if the process is still alive."""
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def measure_ping(token: str) -> int:
    """Quick ping measurement for an existing token."""
    try:
        headers = {
            "Authorization": token,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        t0 = time.time()
        resp = requests.get(f"{DISCORD_API}/users/@me", headers=headers, timeout=5)
        if resp.status_code == 200:
            return int((time.time() - t0) * 1000)
    except Exception:
        pass
    return 0


def sync_account_statuses(db, HostedAccount):
    """
    Sync every hosted account status:
    - If the process died → mark offline
    - If alive → refresh last_seen + ping
    Also auto-restart crashed instances.
    """
    try:
        accounts = HostedAccount.query.all()
        for acc in accounts:
            if not acc.is_active:
                continue

            running = is_process_running(acc.pid)
            if not running:
                # Decrypt token for auto-restart (start_account_process handles this too, but be explicit)
                new_pid = start_account_process(acc.token, acc.id)
                if new_pid:
                    acc.pid = new_pid
                    acc.status = "online"
                    acc.last_seen = datetime.utcnow()
                    acc.restart_count = (acc.restart_count or 0) + 1
                    if not acc.started_at:
                        acc.started_at = datetime.utcnow()
                else:
                    acc.status = "offline"
                    acc.is_active = False
                    acc.pid = None
            else:
                acc.status = "online"
                acc.last_seen = datetime.utcnow()

        db.session.commit()
    except Exception as e:
        logger.error(f"Error syncing statuses: {e}")
