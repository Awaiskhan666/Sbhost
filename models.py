"""
Database Models for LTC Flash Discord Selfbot
Provides persistent storage for bot configurations, user data, and analytics
"""

import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, JSON

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class BotConfiguration(db.Model):
    """Store bot configuration settings"""
    __tablename__ = 'bot_configurations'
    
    id = db.Column(db.Integer, primary_key=True)
    setting_name = db.Column(db.String(100), unique=True, nullable=False)
    setting_value = db.Column(db.Text)
    setting_type = db.Column(db.String(20), default='string')  # string, int, bool, json
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AuthorizedUser(db.Model):
    """Store authorized users for the bot"""
    __tablename__ = 'authorized_users'
    
    id = db.Column(db.Integer, primary_key=True)
    discord_id = db.Column(db.String(20), unique=True, nullable=False)
    username = db.Column(db.String(100), nullable=False)
    permissions = db.Column(db.JSON, default=lambda: ['basic'])  # ['basic', 'admin', 'owner']
    is_active = db.Column(db.Boolean, default=True)
    added_by = db.Column(db.String(20))  # Discord ID of who added them
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CommandLog(db.Model):
    """Log all commands executed by the bot"""
    __tablename__ = 'command_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), nullable=False)
    username = db.Column(db.String(100))
    command = db.Column(db.String(50), nullable=False)
    arguments = db.Column(db.Text)
    channel_id = db.Column(db.String(20))
    guild_id = db.Column(db.String(20))
    success = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.Text)
    execution_time = db.Column(db.Float)  # Time in seconds
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class BotAnalytics(db.Model):
    """Store bot performance and usage analytics"""
    __tablename__ = 'bot_analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    metric_name = db.Column(db.String(50), nullable=False)
    metric_value = db.Column(db.Float, nullable=False)
    metric_data = db.Column(db.JSON)  # Additional context data
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

class TargetUser(db.Model):
    """Store target users for various bot operations"""
    __tablename__ = 'target_users'
    
    id = db.Column(db.Integer, primary_key=True)
    discord_id = db.Column(db.String(20), nullable=False)
    username = db.Column(db.String(100))
    target_type = db.Column(db.String(20), default='general')  # general, drown, debate, etc.
    is_active = db.Column(db.Boolean, default=True)
    added_by = db.Column(db.String(20))  # Discord ID of who added them
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AFKStatus(db.Model):
    """Store AFK status history and statistics"""
    __tablename__ = 'afk_status'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), nullable=False)
    afk_message = db.Column(db.Text)
    started_at = db.Column(db.DateTime, nullable=False)
    ended_at = db.Column(db.DateTime)
    duration_seconds = db.Column(db.Integer)
    auto_replies_sent = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)

class BotSession(db.Model):
    """Track bot session information"""
    __tablename__ = 'bot_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(50), unique=True, nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)
    uptime_seconds = db.Column(db.Integer)
    commands_executed = db.Column(db.Integer, default=0)
    errors_encountered = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='active')  # active, stopped, crashed

class WhitelistedUser(db.Model):
    """Store whitelisted users who are immune to bot features"""
    __tablename__ = 'whitelisted_users'
    
    id = db.Column(db.Integer, primary_key=True)
    discord_id = db.Column(db.String(20), unique=True, nullable=False)
    username = db.Column(db.String(100))
    whitelisted_by = db.Column(db.String(20))  # Discord ID of who whitelisted them
    reason = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Utility functions for database operations
def get_bot_setting(setting_name, default_value=None):
    """Get a bot configuration setting"""
    setting = BotConfiguration.query.filter_by(setting_name=setting_name).first()
    if setting:
        if setting.setting_type == 'int':
            return int(setting.setting_value)
        elif setting.setting_type == 'bool':
            return setting.setting_value.lower() == 'true'
        elif setting.setting_type == 'json':
            import json
            return json.loads(setting.setting_value)
        else:
            return setting.setting_value
    return default_value

def set_bot_setting(setting_name, setting_value, setting_type='string', description=None):
    """Set a bot configuration setting"""
    setting = BotConfiguration.query.filter_by(setting_name=setting_name).first()
    if not setting:
        setting = BotConfiguration(setting_name=setting_name)
        db.session.add(setting)
    
    if setting_type == 'json':
        import json
        setting.setting_value = json.dumps(setting_value)
    else:
        setting.setting_value = str(setting_value)
    
    setting.setting_type = setting_type
    if description:
        setting.description = description
    setting.updated_at = datetime.utcnow()
    
    db.session.commit()
    return setting

def log_command_execution(user_id, username, command, arguments=None, channel_id=None, 
                         guild_id=None, success=True, error_message=None, execution_time=None):
    """Log a command execution"""
    log_entry = CommandLog(
        user_id=user_id,
        username=username,
        command=command,
        arguments=arguments,
        channel_id=channel_id,
        guild_id=guild_id,
        success=success,
        error_message=error_message,
        execution_time=execution_time
    )
    db.session.add(log_entry)
    db.session.commit()
    return log_entry

def record_analytics(metric_name, metric_value, metric_data=None):
    """Record analytics data"""
    analytics = BotAnalytics(
        metric_name=metric_name,
        metric_value=metric_value,
        metric_data=metric_data
    )
    db.session.add(analytics)
    db.session.commit()
    return analytics

def is_user_authorized_db(discord_id):
    """Check if user is authorized using database"""
    user = AuthorizedUser.query.filter_by(discord_id=str(discord_id), is_active=True).first()
    return user is not None

def add_authorized_user_db(discord_id, username, permissions=['basic'], added_by=None):
    """Add authorized user to database"""
    existing = AuthorizedUser.query.filter_by(discord_id=str(discord_id)).first()
    if existing:
        existing.is_active = True
        existing.username = username
        existing.permissions = permissions
        existing.updated_at = datetime.utcnow()
    else:
        user = AuthorizedUser(
            discord_id=str(discord_id),
            username=username,
            permissions=permissions,
            added_by=str(added_by) if added_by else None
        )
        db.session.add(user)
    
    db.session.commit()
    return existing if existing else user

def remove_authorized_user_db(discord_id):
    """Remove authorized user from database"""
    user = AuthorizedUser.query.filter_by(discord_id=str(discord_id)).first()
    if user:
        user.is_active = False
        user.updated_at = datetime.utcnow()
        db.session.commit()
        return True
    return False

def add_whitelisted_user_db(discord_id, username, whitelisted_by=None, reason=None):
    """Add whitelisted user to database"""
    try:
        from app import app
        with app.app_context():
            existing = WhitelistedUser.query.filter_by(discord_id=str(discord_id)).first()
            if existing:
                existing.is_active = True
                existing.username = username
                existing.whitelisted_by = str(whitelisted_by) if whitelisted_by else None
                existing.reason = reason
                existing.updated_at = datetime.utcnow()
            else:
                user = WhitelistedUser(
                    discord_id=str(discord_id),
                    username=username,
                    whitelisted_by=str(whitelisted_by) if whitelisted_by else None,
                    reason=reason
                )
                db.session.add(user)
            
            db.session.commit()
            return existing if existing else user
    except Exception as e:
        print(f"❌ Database error adding to whitelist: {e}")
        return None

def remove_whitelisted_user_db(discord_id):
    """Remove whitelisted user from database"""
    try:
        from app import app
        with app.app_context():
            user = WhitelistedUser.query.filter_by(discord_id=str(discord_id)).first()
            if user:
                user.is_active = False
                user.updated_at = datetime.utcnow()
                db.session.commit()
                return True
    except Exception as e:
        print(f"❌ Database error removing from whitelist: {e}")
    return False

def is_user_whitelisted_db(discord_id):
    """Check if user is whitelisted using database"""
    try:
        from app import app
        with app.app_context():
            user = WhitelistedUser.query.filter_by(discord_id=str(discord_id), is_active=True).first()
            return user is not None
    except Exception as e:
        print(f"❌ Database context error in whitelist check: {e}")
        return False

class HostedAccount(db.Model):
    """Store hosted Discord accounts for multi-account selfbot hosting"""
    __tablename__ = 'hosted_accounts'

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.Text, nullable=False, unique=True)
    discord_id = db.Column(db.String(20))
    username = db.Column(db.String(100))
    discriminator = db.Column(db.String(10))
    avatar_url = db.Column(db.Text)
    bio = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)
    pid = db.Column(db.Integer)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    last_seen = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='offline')
    ping_ms = db.Column(db.Integer, default=0)
    restart_count = db.Column(db.Integer, default=0)
    owner_discord_id = db.Column(db.String(20))  # OAuth login Discord ID of the person who added this

def get_command_history(limit=20):
    """Get recent command history"""
    commands = CommandLog.query.order_by(CommandLog.created_at.desc()).limit(limit).all()
    return commands

def get_whitelisted_users():
    """Get all active whitelisted users"""
    try:
        from app import app
        with app.app_context():
            users = WhitelistedUser.query.filter_by(is_active=True).all()
            return users
    except Exception as e:
        print(f"❌ Database error getting whitelisted users: {e}")
        return []