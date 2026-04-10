from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import os
import subprocess
import json
import time
import logging
from datetime import datetime, timedelta
from account_manager import validate_token, start_account_process, stop_account_process, sync_account_statuses
from crypto import encrypt_token, decrypt_token, is_encrypted

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "development_secret_key")

# Database configuration — fix Render's postgres:// prefix (SQLAlchemy 2.x needs postgresql://)
_db_url = os.environ.get("DATABASE_URL", "sqlite:///bot_data.db")
if _db_url.startswith("postgres://"):
    _db_url = _db_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = _db_url

# Initialize database
from models import db, BotConfiguration, AuthorizedUser, CommandLog, BotAnalytics, TargetUser, AFKStatus, BotSession, HostedAccount
from models import get_bot_setting, set_bot_setting, log_command_execution, record_analytics

db.init_app(app)

# Create tables and run migrations
with app.app_context():
    db.create_all()
    # Add new columns if they don't exist (migration)
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
    except Exception as _e:
        pass
    # Migrate any existing plaintext tokens to encrypted form
    try:
        accounts = HostedAccount.query.all()
        migrated = 0
        for acc in accounts:
            if acc.token and not is_encrypted(acc.token):
                acc.token = encrypt_token(acc.token)
                migrated += 1
        if migrated:
            db.session.commit()
            app.logger.info(f"Migrated {migrated} plaintext token(s) to encrypted form.")
    except Exception as _me:
        pass
    # Set default configuration values
    if not BotConfiguration.query.filter_by(setting_name='anti_ban_enabled').first():
        set_bot_setting('anti_ban_enabled', True, 'bool', 'Enable anti-ban protection features')
    if not BotConfiguration.query.filter_by(setting_name='response_delay_min').first():
        set_bot_setting('response_delay_min', 0.3, 'float', 'Minimum response delay in seconds')
    if not BotConfiguration.query.filter_by(setting_name='response_delay_max').first():
        set_bot_setting('response_delay_max', 0.8, 'float', 'Maximum response delay in seconds')

# Simple status tracking
BOT_STATUS = {
    "is_running": False,
    "last_started": None,
    "last_command": None,
    "command_result": None,
    "keep_alive_enabled": True  # New flag for 24/7 operation
}

@app.route('/')
def index():
    return redirect(url_for('accounts'))

@app.route('/start_bot', methods=['POST'])
def start_bot():
    try:
        # Import and use the auto-recovery system
        from auto_recovery import start_recovery, get_recovery_status
        
        # Start the bot with auto-recovery
        start_recovery()
        
        # Update status
        BOT_STATUS["is_running"] = True
        BOT_STATUS["keep_alive_enabled"] = True
        BOT_STATUS["last_started"] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        flash("Discord selfbot started successfully with 24/7 keep-alive and auto-recovery enabled!", "success")
        app.logger.info("Bot started with auto-recovery system")
    except Exception as e:
        flash(f"Error starting bot: {e}", "danger")
        app.logger.error(f"Error starting bot: {e}")
    
    return redirect(url_for('index'))

@app.route('/stop_bot', methods=['POST'])
def stop_bot():
    try:
        # Use the auto-recovery system to stop the bot properly
        from auto_recovery import stop_recovery
        
        # Stop the bot and recovery system
        stop_recovery()
        
        # Also use pkill as a backup method
        subprocess.run(["pkill", "-f", "python main.py"])
        
        BOT_STATUS["is_running"] = False
        flash("Discord selfbot stopped successfully!", "success")
    except Exception as e:
        flash(f"Error stopping bot: {e}", "danger")
        app.logger.error(f"Error stopping bot: {e}")
    
    return redirect(url_for('index'))

@app.route('/bot_status')
def bot_status():
    """API endpoint to get detailed bot status information"""
    try:
        # Import the recovery system and get status
        from auto_recovery import get_recovery_status
        recovery_status = get_recovery_status()
        
        # Update our status tracking based on recovery system
        BOT_STATUS["is_running"] = recovery_status["bot_running"]
        
        # Get analytics from database
        recent_commands = CommandLog.query.filter(
            CommandLog.created_at >= datetime.utcnow() - timedelta(hours=24)
        ).count()
        
        active_session = BotSession.query.filter_by(status='active').first()
        
        # Return combined status information
        return json.dumps({
            "bot_status": BOT_STATUS,
            "recovery_status": recovery_status,
            "analytics": {
                "commands_24h": recent_commands,
                "current_session_id": active_session.session_id if active_session else None,
                "session_start": active_session.started_at.isoformat() if active_session else None
            }
        })
    except Exception as e:
        app.logger.error(f"Error getting bot status: {e}")
        return json.dumps({
            "error": str(e),
            "bot_status": BOT_STATUS
        })

@app.route('/analytics')
def analytics():
    """Display bot analytics and statistics"""
    try:
        # Get command statistics
        total_commands = CommandLog.query.count()
        commands_today = CommandLog.query.filter(
            CommandLog.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
        
        # Get most used commands
        from sqlalchemy import func
        popular_commands = db.session.query(
            CommandLog.command,
            func.count(CommandLog.command).label('count')
        ).group_by(CommandLog.command).order_by(func.count(CommandLog.command).desc()).limit(10).all()
        
        # Get authorized users count
        auth_users = AuthorizedUser.query.filter_by(is_active=True).count()
        
        # Get AFK statistics
        afk_sessions = AFKStatus.query.filter(AFKStatus.ended_at.isnot(None)).count()
        
        return render_template('analytics.html', 
                             total_commands=total_commands,
                             commands_today=commands_today,
                             popular_commands=popular_commands,
                             auth_users=auth_users,
                             afk_sessions=afk_sessions)
    except Exception as e:
        app.logger.error(f"Error getting analytics: {e}")
        flash(f"Error loading analytics: {e}", "danger")
        return redirect(url_for('index'))

@app.route('/api/command_logs')
def api_command_logs():
    """API endpoint for recent command logs"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        logs = CommandLog.query.order_by(CommandLog.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            "logs": [{
                "id": log.id,
                "username": log.username,
                "command": log.command,
                "arguments": log.arguments,
                "success": log.success,
                "error_message": log.error_message,
                "execution_time": log.execution_time,
                "created_at": log.created_at.isoformat()
            } for log in logs.items],
            "total": logs.total,
            "pages": logs.pages,
            "current_page": page
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/dashboard')
def dashboard():
    """Real-time dashboard for bot monitoring"""
    return render_template('dashboard.html')

@app.route('/api/dashboard_data')
def api_dashboard_data():
    """API endpoint for real-time dashboard data"""
    try:
        # Get current bot status
        from auto_recovery import get_recovery_status
        recovery_status = get_recovery_status()
        
        # Calculate performance metrics
        recent_commands = CommandLog.query.filter(
            CommandLog.created_at >= datetime.utcnow() - timedelta(minutes=5)
        ).count()
        
        avg_response_time = db.session.query(
            db.func.avg(CommandLog.execution_time)
        ).filter(
            CommandLog.execution_time.isnot(None),
            CommandLog.created_at >= datetime.utcnow() - timedelta(hours=1)
        ).scalar() or 0
        
        commands_today = CommandLog.query.filter(
            CommandLog.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
        
        # Get recent command logs for display
        recent_logs = CommandLog.query.order_by(CommandLog.created_at.desc()).limit(10).all()
        
        return jsonify({
            "bot_online": recovery_status.get("bot_running", False),
            "commands_today": commands_today,
            "avg_response_time": round((avg_response_time or 0) * 1000, 1),  # Convert to ms
            "active_users": AuthorizedUser.query.filter_by(is_active=True).count(),
            "uptime": recovery_status.get("uptime", "0h"),
            "memory_usage": 75,  # Placeholder - could integrate with psutil
            "recent_commands": [{
                "timestamp": log.created_at.isoformat(),
                "user": log.username or "Unknown",
                "command": log.command,
                "success": log.success
            } for log in recent_logs],
            "performance_data": {
                "response_time": round((avg_response_time or 0) * 1000, 1),
                "commands_per_minute": recent_commands
            },
            "status": {
                "process": recovery_status.get("bot_running", False),
                "database": True,  # Could add actual DB health check
                "web_server": True,
                "anti_ban": True,
                "keep_alive": recovery_status.get("keep_alive_active", False),
                "security": True
            }
        })
    except Exception as e:
        app.logger.error(f"Error getting dashboard data: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/export_logs')
def api_export_logs():
    """Export command logs as JSON"""
    try:
        logs = CommandLog.query.order_by(CommandLog.created_at.desc()).limit(1000).all()
        export_data = [{
            "id": log.id,
            "user_id": log.user_id,
            "username": log.username,
            "command": log.command,
            "arguments": log.arguments,
            "success": log.success,
            "error_message": log.error_message,
            "execution_time": log.execution_time,
            "created_at": log.created_at.isoformat()
        } for log in logs]
        
        response = jsonify(export_data)
        response.headers["Content-Disposition"] = f"attachment; filename=bot_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/emergency_stop', methods=['POST'])
def api_emergency_stop():
    """Emergency stop endpoint"""
    try:
        from auto_recovery import stop_recovery
        stop_recovery()
        subprocess.run(["pkill", "-f", "python main.py"])
        return jsonify({"success": True, "message": "Emergency stop executed"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/check_token')
def check_token():
    token = os.environ.get('TOKEN')
    if token:
        # More secure way to verify token without exposing any part of it
        import hashlib
        token_hash = hashlib.sha256(token.encode()).hexdigest()[:10]
        return json.dumps({
            "status": "available", 
            "secured": True,
            "verified": True,
            "token_hash": token_hash
        })
    else:
        return json.dumps({"status": "missing", "secured": False})

@app.route('/setup-24-7')
def setup_24_7():
    """Display instructions for setting up 24/7 operation"""
    # Get the current Replit URL
    replit_url = os.environ.get('REPL_SLUG', 'your-repl-name')
    replit_owner = os.environ.get('REPL_OWNER', 'your-username')
    
    # Construct the URL to be monitored
    monitor_url = f"https://{replit_url}.{replit_owner}.repl.co"
    
    return render_template('setup_24_7.html', monitor_url=monitor_url)

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin1234")
DISCORD_CLIENT_ID = os.environ.get("DISCORD_CLIENT_ID", "")
DISCORD_CLIENT_SECRET = os.environ.get("DISCORD_CLIENT_SECRET", "")
MAX_SLOTS = 5  # Max hosted accounts per user

import secrets as _secrets
import requests as _requests

def get_logged_in_user():
    """Return dict with discord_id, username, avatar from session, or None."""
    return session.get('discord_user')

def login_required_redirect():
    session['next'] = request.url
    flash('Please login with Discord first.', 'warning')
    return redirect(url_for('auth_discord'))

# ── Discord OAuth Routes ────────────────────────────────────────────────────

@app.route('/auth/discord')
def auth_discord():
    if not DISCORD_CLIENT_ID:
        flash('Discord OAuth not configured yet. Ask the admin to set DISCORD_CLIENT_ID and DISCORD_CLIENT_SECRET.', 'danger')
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
        flash(f'Discord login cancelled.', 'warning')
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
    #1
    def _get_redirect_uri():
    custom = os.environ.get("DISCORD_REDIRECT_URI")
    if custom:
        return custom
    base = request.host_url.rstrip('/')
    return f"{base}/auth/callback"
# ── Public accounts page (shows ALL hosted bots) ────────────────────────────

@app.route('/accounts')
def accounts():
    sync_account_statuses(db, HostedAccount)
    all_accounts = HostedAccount.query.order_by(HostedAccount.added_at.desc()).all()
    online_count = sum(1 for a in all_accounts if a.status == 'online')
    user = get_logged_in_user()
    return render_template('accounts.html', accounts=all_accounts,
                           online_count=online_count, total_count=len(all_accounts),
                           current_user=user)

# ── Private dashboard — user's own accounts ─────────────────────────────────

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

# ── Add account (requires login) ────────────────────────────────────────────

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

        # Enforce 5-slot limit
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

# ── Remove account (owner only) ─────────────────────────────────────────────

@app.route('/accounts/remove/<int:account_id>', methods=['POST'])
def remove_account(account_id):
    user = get_logged_in_user()
    account = HostedAccount.query.get_or_404(account_id)

    # Allow removal if owner of the account OR admin password provided
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

# ── Toggle account (owner only) ─────────────────────────────────────────────

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

# ── API ─────────────────────────────────────────────────────────────────────

@app.route('/api/accounts')
def api_accounts():
    sync_account_statuses(db, HostedAccount)
    accounts = HostedAccount.query.order_by(HostedAccount.added_at.desc()).all()
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
    } for a in accounts])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
