from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import os
import subprocess
import json
import time
import logging
import secrets as _secrets
import requests as _requests
from datetime import datetime, timedelta
from account_manager import validate_token, start_account_process, stop_account_process, sync_account_statuses
from crypto import encrypt_token, decrypt_token, is_encrypted

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "development_secret_key")

# Fix Render's postgres:// prefix — SQLAlchemy 2.x requires postgresql://
_db_url = os.environ.get("DATABASE_URL", "sqlite:///bot_data.db")
if _db_url.startswith("postgres://"):
    _db_url = _db_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = _db_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

from models import db, BotConfiguration, AuthorizedUser, CommandLog, BotAnalytics, TargetUser, AFKStatus, BotSession, HostedAccount
from models import get_bot_setting, set_bot_setting, log_command_execution, record_analytics

db.init_app(app)

def init_db():
    """Initialize database — called lazily so startup never crashes."""
    try:
        db.create_all()
    except Exception as e:
        app.logger.error(f"db.create_all failed: {e}")
        return

    try:
        from sqlalchemy import text
        migration_stmts = [
            "ALTER TABLE hosted_accounts ADD COLUMN IF NOT EXISTS started_at TIMESTAMP",
            "ALTER TABLE hosted_accounts ADD COLUMN IF NOT EXISTS ping_ms INTEGER DEFAULT 0",
            "ALTER TABLE hosted_accounts ADD COLUMN IF NOT EXISTS restart_count INTEGER DEFAULT 0",
            "ALTER TABLE hosted_accounts ADD COLUMN IF NOT EXISTS owner_discord_id VARCHAR(20)",
        ]
        for stmt in migration_stmts:
            try:
                with db.engine.begin() as conn:
                    conn.execute(text(stmt))
            except Exception:
                pass
    except Exception:
        pass

    try:
        accounts = HostedAccount.query.all()
        migrated = 0
        for acc in accounts:
            if acc.token and not is_encrypted(acc.token):
                acc.token = encrypt_token(acc.token)
                migrated += 1
        if migrated:
            db.session.commit()
    except Exception:
        pass

    try:
        if not BotConfiguration.query.filter_by(setting_name='anti_ban_enabled').first():
            set_bot_setting('anti_ban_enabled', True, 'bool', 'Enable anti-ban protection features')
        if not BotConfiguration.query.filter_by(setting_name='response_delay_min').first():
            set_bot_setting('response_delay_min', 0.3, 'float', 'Minimum response delay in seconds')
        if not BotConfiguration.query.filter_by(setting_name='response_delay_max').first():
            set_bot_setting('response_delay_max', 0.8, 'float', 'Maximum response delay in seconds')
    except Exception:
        pass


with app.app_context():
    init_db()

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin1234")
DISCORD_CLIENT_ID = os.environ.get("DISCORD_CLIENT_ID", "")
DISCORD_CLIENT_SECRET = os.environ.get("DISCORD_CLIENT_SECRET", "")
MAX_SLOTS = 5


def get_logged_in_user():
    return session.get('discord_user')


def login_required_redirect():
    session['next'] = request.url
    flash('Please login with Discord first.', 'warning')
    return redirect(url_for('auth_discord'))


def _get_redirect_uri():
    custom = os.environ.get("DISCORD_REDIRECT_URI")
    if custom:
        return custom
    base = request.host_url.rstrip('/')
    return f"{base}/auth/callback"


# ── Main routes ──────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return redirect(url_for('accounts'))


# ── Discord OAuth Routes ─────────────────────────────────────────────────────

@app.route('/auth/discord')
def auth_discord():
    if not DISCORD_CLIENT_ID:
        flash('Discord OAuth not configured. Set DISCORD_CLIENT_ID and DISCORD_CLIENT_SECRET.', 'danger')
        return redirect(url_for('accounts'))
    state = _secrets.token_urlsafe(16)
    session['oauth_state'] = state
    redirect_uri = _get_redirect_uri()
    params = (
        f"client_id={DISCORD_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope=identify"
        f"&state={state}"
    )
    return redirect(f"https://discord.com/api/oauth2/authorize?{params}")


@app.route('/auth/callback')
def auth_callback():
    error = request.args.get('error')
    if error:
        flash('Discord login cancelled.', 'warning')
        return redirect(url_for('accounts'))

    state = request.args.get('state', '')
    if state != session.pop('oauth_state', None):
        flash('Invalid OAuth state. Try again.', 'danger')
        return redirect(url_for('accounts'))

    code = request.args.get('code', '')
    redirect_uri = _get_redirect_uri()

    try:
        token_resp = _requests.post('https://discord.com/api/oauth2/token', data={
            'client_id': DISCORD_CLIENT_ID,
            'client_secret': DISCORD_CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
        }, headers={'Content-Type': 'application/x-www-form-urlencoded'}, timeout=10)
        token_data = token_resp.json()
        access_token = token_data.get('access_token')
        if not access_token:
            flash('Failed to get Discord access token. Try again.', 'danger')
            return redirect(url_for('accounts'))

        user_resp = _requests.get('https://discord.com/api/v10/users/@me',
                                  headers={'Authorization': f'Bearer {access_token}'}, timeout=10)
        user_data = user_resp.json()

        avatar_hash = user_data.get('avatar')
        discord_id = user_data['id']
        avatar_url = (
            f"https://cdn.discordapp.com/avatars/{discord_id}/{avatar_hash}.png"
            if avatar_hash else
            f"https://cdn.discordapp.com/embed/avatars/{int(discord_id) % 5}.png"
        )
        session['discord_user'] = {
            'discord_id': discord_id,
            'username': user_data.get('global_name') or user_data.get('username', 'Unknown'),
            'avatar_url': avatar_url,
        }
        session.permanent = True
    except Exception as e:
        app.logger.error(f"OAuth error: {e}")
        flash('Discord login failed. Try again.', 'danger')
        return redirect(url_for('accounts'))

    next_url = session.pop('next', None)
    return redirect(next_url or url_for('my_accounts'))


@app.route('/auth/logout')
def auth_logout():
    session.pop('discord_user', None)
    flash('Logged out.', 'success')
    return redirect(url_for('accounts'))


# ── Public accounts page ─────────────────────────────────────────────────────

@app.route('/accounts')
def accounts():
    sync_account_statuses(db, HostedAccount)
    all_accounts = HostedAccount.query.order_by(HostedAccount.added_at.desc()).all()
    online_count = sum(1 for a in all_accounts if a.status == 'online')
    user = get_logged_in_user()
    return render_template('accounts.html', accounts=all_accounts,
                           online_count=online_count, total_count=len(all_accounts),
                           current_user=user)


# ── My accounts (logged-in user) ─────────────────────────────────────────────

@app.route('/my-accounts')
def my_accounts():
    user = get_logged_in_user()
    if not user:
        return login_required_redirect()

    sync_account_statuses(db, HostedAccount)
    my_accs = HostedAccount.query.filter_by(owner_discord_id=user['discord_id']).order_by(HostedAccount.added_at.desc()).all()
    slots_used = len(my_accs)
    slots_left = max(0, MAX_SLOTS - slots_used)
    return render_template('my_accounts.html', accounts=my_accs,
                           slots_used=slots_used, slots_left=slots_left,
                           current_user=user, max_slots=MAX_SLOTS)


# ── Add account ──────────────────────────────────────────────────────────────

@app.route('/accounts/add', methods=['GET', 'POST'])
def add_account():
    user = get_logged_in_user()
    if not user:
        return login_required_redirect()

    if request.method == 'POST':
        token = request.form.get('token', '').strip()
        if not token:
            flash('Please provide a Discord token.', 'danger')
            return redirect(url_for('add_account'))

        my_count = HostedAccount.query.filter_by(owner_discord_id=user['discord_id']).count()
        if my_count >= MAX_SLOTS:
            flash(f'You have reached the maximum of {MAX_SLOTS} hosted accounts.', 'warning')
            return redirect(url_for('my_accounts'))

        user_info = validate_token(token)
        if not user_info:
            flash('Invalid token. Please check and try again.', 'danger')
            return redirect(url_for('add_account'))

        existing = HostedAccount.query.filter_by(discord_id=user_info['discord_id']).first()
        if existing:
            flash('This Discord account is already hosted.', 'warning')
            return redirect(url_for('my_accounts'))

        encrypted = encrypt_token(token)
        account = HostedAccount(
            token=encrypted,
            discord_id=user_info['discord_id'],
            username=user_info['username'],
            discriminator=user_info['discriminator'],
            avatar_url=user_info['avatar_url'],
            bio=user_info.get('bio', ''),
            is_verified=True,
            status='offline',
            owner_discord_id=user['discord_id'],
        )
        db.session.add(account)
        db.session.commit()

        pid = start_account_process(token, account.id)
        if pid:
            account.pid = pid
            account.is_active = True
            account.status = 'online'
            account.started_at = datetime.utcnow()
            account.last_seen = datetime.utcnow()
            account.ping_ms = user_info.get('ping_ms', 0)
            db.session.commit()
            flash(f'Account {user_info["username"]} is now hosted and running!', 'success')
        else:
            flash(f'Account {user_info["username"]} added but failed to start.', 'warning')

        return redirect(url_for('my_accounts'))

    my_count = HostedAccount.query.filter_by(owner_discord_id=user['discord_id']).count()
    if my_count >= MAX_SLOTS:
        flash(f'You have reached the maximum of {MAX_SLOTS} hosted accounts.', 'warning')
        return redirect(url_for('my_accounts'))

    return render_template('add_account.html', current_user=user)


# ── Remove account ───────────────────────────────────────────────────────────

@app.route('/accounts/remove/<int:account_id>', methods=['POST'])
def remove_account(account_id):
    user = get_logged_in_user()
    account = HostedAccount.query.get_or_404(account_id)

    password = request.form.get('password', '')
    is_admin = password == ADMIN_PASSWORD
    is_owner = user and account.owner_discord_id == user['discord_id']

    if not is_admin and not is_owner:
        flash('You do not have permission to remove this account.', 'danger')
        return redirect(url_for('my_accounts') if user else url_for('accounts'))

    if account.pid:
        stop_account_process(account.pid)
    db.session.delete(account)
    db.session.commit()
    flash('Account removed successfully.', 'success')
    return redirect(url_for('my_accounts') if user else url_for('accounts'))


# ── Toggle account ───────────────────────────────────────────────────────────

@app.route('/accounts/toggle/<int:account_id>', methods=['POST'])
def toggle_account(account_id):
    user = get_logged_in_user()
    account = HostedAccount.query.get_or_404(account_id)

    password = request.form.get('password', '')
    is_admin = password == ADMIN_PASSWORD
    is_owner = user and account.owner_discord_id == user['discord_id']

    if not is_admin and not is_owner:
        return jsonify({'error': 'Permission denied'}), 403

    if account.is_active and account.pid:
        stop_account_process(account.pid)
        account.is_active = False
        account.status = 'offline'
        account.pid = None
        account.started_at = None
    else:
        pid = start_account_process(account.token, account.id)
        if pid:
            account.pid = pid
            account.is_active = True
            account.status = 'online'
            account.started_at = datetime.utcnow()
            account.last_seen = datetime.utcnow()

    db.session.commit()
    return jsonify({'status': account.status, 'is_active': account.is_active})


# ── API ──────────────────────────────────────────────────────────────────────

@app.route('/api/accounts')
def api_accounts():
    sync_account_statuses(db, HostedAccount)
    all_accs = HostedAccount.query.order_by(HostedAccount.added_at.desc()).all()
    return jsonify([{
        'id': a.id,
        'username': a.username,
        'discriminator': a.discriminator,
        'discord_id': a.discord_id,
        'avatar_url': a.avatar_url,
        'status': a.status,
        'is_active': a.is_active,
        'ping_ms': a.ping_ms or 0,
        'restart_count': a.restart_count or 0,
        'added_at': a.added_at.isoformat() if a.added_at else None,
        'started_at': a.started_at.isoformat() if a.started_at else None,
        'last_seen': a.last_seen.isoformat() if a.last_seen else None,
    } for a in all_accs])


@app.route('/api/status')
def api_status():
    try:
        total = HostedAccount.query.count()
        online = HostedAccount.query.filter_by(status='online').count()
        return jsonify({'online': online, 'total': total, 'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
