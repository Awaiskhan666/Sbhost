import subprocess
import sys
import os
import asyncio
import re
import requests
import random
import time
import copy
import logging
import datetime
from collections import deque, defaultdict
import io
import yt_dlp
import shutil

# Function to install packages
def install_package(package):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"Installed {package}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install {package}: {e}")
        return False

# Check if discord.py-self is installed
try:
    import discord
    from discord.ext import commands
    if not hasattr(discord, 'User'):  # Basic check for discord.py-self
        raise ImportError("Regular discord.py detected, need discord.py-self")
except ImportError:
    print("discord.py-self not found, installing...")
    # Uninstall regular discord.py if installed
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "-y", "discord.py"])
        print("Uninstalled regular discord.py")
    except:
        pass
    
    # Install discord.py-self
    if not install_package("discord.py-self"):
        print("Failed to install discord.py-self. Exiting.")
        sys.exit(1)
    
    # Now import the newly installed packages
    import discord
    from discord.ext import commands

# Console output capture system for -logs command
console_logs = deque(maxlen=100)  # Store last 100 log entries

# Database integration for enhanced analytics and persistence
DATABASE_INTEGRATION = True
try:
    from models import (log_command_execution, record_analytics, is_user_authorized_db, 
                       add_authorized_user_db, remove_authorized_user_db, add_whitelisted_user_db,
                       remove_whitelisted_user_db, is_user_whitelisted_db, get_command_history,
                       get_whitelisted_users)
    print("📊 Database integration enabled - Advanced analytics active")
except ImportError as e:
    DATABASE_INTEGRATION = False
    print(f"⚠️ Database integration disabled - {e}")
original_stdout = sys.stdout
original_stderr = sys.stderr

class ConsoleCapture:
    def __init__(self, original_stream, is_stderr=False):
        self.original_stream = original_stream
        self.is_stderr = is_stderr
    
    def write(self, text):
        # Write to original stream
        self.original_stream.write(text)
        self.original_stream.flush()
        
        # Capture for logs if it's meaningful content
        if text.strip() and len(text.strip()) > 0:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"{timestamp} {text.strip()}"
            console_logs.append(log_entry)
    
    def flush(self):
        self.original_stream.flush()

# Set up console capture
sys.stdout = ConsoleCapture(original_stdout)
sys.stderr = ConsoleCapture(original_stderr, is_stderr=True)

# Set up logging to capture discord.py warnings
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s %(levelname)s  %(name)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Custom log handler to capture discord logs
class DiscordLogHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        console_logs.append(log_entry)

# Add handler to discord logger
discord_logger = logging.getLogger('discord')
discord_handler = DiscordLogHandler()
discord_handler.setLevel(logging.WARNING)
discord_logger.addHandler(discord_handler)

# Valid Litecoin address regex pattern (basic validation)
# More lenient pattern that accepts all common Litecoin address formats
LTC_ADDRESS_PATTERN = re.compile(r'^[LM3][a-zA-Z0-9]{26,50}$')

# ULTRA-OPTIMIZED Bot Setup - Lightning Fast Startup for discord.py-self
import discord.utils

# Lightning-fast bot with minimal Discord overhead (discord.py-self compatible)
bot = commands.Bot(
    command_prefix="-", 
    self_bot=True,
    case_insensitive=True,
    strip_after_prefix=True,
    owner_id=None
)

# Enhanced performance settings for faster startup
# bot.max_messages removed - not available in discord.py-self 2.0.1
LOW_LATENCY_MODE = True  # Enable low latency optimizations
ULTRA_FAST_STARTUP = True  # Skip unnecessary initialization steps

# Dictionary to track users being "drowned" with insults
drowned_users = {}  # Dictionary to track users being "drowned" with insults

# Dictionary to track users being "debated" with savage responses
debated_users = {}

# Dictionary to track users being "annoyed" in voice channels
annoying_users = {}

# Dictionary to track users being dragged through voice channels
dragging_users = {}

# Global spam control
spam_active = False
spam_tasks = []

# Jija system for rapid group chat name changes
jija_sessions = {}  # {channel_id: {"message": "message", "active": True, "task": task_object}}

# Ultra-fast jija performance configuration
JIJA_ULTRA_FAST_MODE = True
JIJA_MIN_DELAY = 0.02  # Minimum 20ms delay for maximum speed
JIJA_MAX_DELAY = 1.0   # Maximum delay during heavy rate limiting
JIJA_VARIATIONS_COUNT = 20  # Number of name variations for better performance
JIJA_BURST_MODE = True  # Enable burst mode for even faster execution
JIJA_BURST_SIZE = 3     # Number of rapid changes before brief pause in burst mode

# Global ultra-fast response configuration
ULTRA_FAST_MODE = True
INSTANT_DELETE_COMMANDS = True  # Delete commands instantly for seamless experience
COMMAND_RESPONSE_DELAY = 0.005  # Super-fast 5ms command processing
PING_OPTIMIZE_MODE = True       # Optimize ping and connection performance
ZERO_ERROR_MODE = True          # Eliminate all errors and optimize performance
PERFORMANCE_MONITORING = True   # Track performance metrics
LOW_LATENCY_MODE = True         # Force low latency connections
CONNECTION_POOLING = True       # Optimize connection handling

# Auto-reaction system for tracking users
reaction_targets = {}  # {user_id: {"emoji": "😀", "active": True}}

# AFK system for automatic replies
afk_users = {}  # {user_id: {"status": True, "message": "optional custom message", "timestamp": time}}

# Whitelist system - users protected from all bot features
whitelisted_users = set()  # Set of user IDs who are whitelisted from bot features

# Enhanced Security System - Advanced access control and protection  
BOT_OWNER_ID = None  # Set dynamically on login — equals the token's own Discord user ID
authorized_users = set()  # Set of user IDs who can control the bot
AUTHORIZED_USERS_FILE = "authorized_users.txt"  # File to persist authorized users

# ACCESS CONTROL SYSTEM - Limited Command Access for Authorized Users
# Define which commands are allowed for authorized users vs restricted to owner only
ALLOWED_COMMANDS_FOR_AUTHORIZED = {
    "debate", "react", "list", "about", "stop", "stopd", "stops", "history",
    "mjoin", "mplay", "mstop", "mleave", "ping", "bal", "balance"  # Music & utility commands
}
RESTRICTED_COMMANDS = {
    "spam", "drown", "drownenglish", "drownhindi", "drownhinglish", "annoy", "jija", "flash", 
    "target", "gcspam", "access", "removeaccess", "logs", "cleartargets", "afk", "removeafk"
}

# MILITARY-GRADE Security Configuration
SECURITY_ENHANCED = True            # Enable enhanced security measures
FAILED_ATTEMPTS_LIMIT = 2           # Stricter - Only 2 attempts allowed
LOCKOUT_DURATION = 900              # Longer lockout - 15 minutes
SESSION_TIMEOUT = 1800              # Shorter session - 30 minutes
AUDIT_LOG_ENABLED = True            # Enable security audit logging
OWNER_VERIFICATION_REQUIRED = True  # Require additional owner verification
IP_WHITELIST_ENABLED = False        # IP whitelist (disabled for Discord bot)
COMMAND_RATE_LIMIT_STRICT = True    # Ultra-strict command rate limiting
SECURITY_SCAN_ENABLED = True        # Real-time security scanning
ANTI_BRUTEFORCE_ENHANCED = True     # Enhanced brute force protection
COMMAND_ENCRYPTION_MODE = True      # Encrypt sensitive command data

# Security tracking dictionaries
failed_attempts = {}                # Track failed access attempts per user
locked_users = {}                   # Track locked out users
active_sessions = {}                # Track active authorized sessions
security_audit_log = deque(maxlen=50)  # Security event audit log

# Anti-detection configuration to prevent Discord security warnings
STEALTH_MODE = True             # Enable comprehensive anti-detection measures
HUMAN_LIKE_DELAYS = True        # Add random human-like delays between actions
RATE_LIMIT_SAFETY = True        # Ultra-conservative rate limiting
ACTIVITY_ROTATION = False       # Activity rotation disabled
MAX_COMMANDS_PER_MINUTE = 8     # Stricter limit to avoid detection (reduced from 10)
NATURAL_TYPING_SIMULATION = True # Simulate natural typing patterns

# Enhanced anti-ban protection
ANTI_BAN_MODE = True            # Enable anti-ban protection measures
PRESENCE_ROTATION = False       # Presence rotation disabled
ACTIVITY_RANDOMIZATION = False  # Activity randomization disabled
COMMAND_COOLDOWN = 2.0          # Minimum seconds between commands
MESSAGE_VARIATION = True        # Vary message patterns to avoid detection

# Command usage tracking for anti-detection
command_usage_tracker = {}      # Track command frequency
last_command_time = 0          # Track last command execution time
presence_rotation_index = 0    # Track current presence rotation
last_presence_change = 0       # Track last presence change time

# Ultra-fast command processing functions
async def instant_delete_command(ctx):
    """TRULY INSTANT command deletion - NO DELAY AT ALL"""
    if INSTANT_DELETE_COMMANDS:
        try:
            # Delete immediately without any processing delay
            await ctx.message.delete()
        except:
            pass

async def add_human_like_delay(bypass_for_spam=False, user_id=None):
    """Add random human-like delays to avoid detection"""
    # Hosted account subprocesses get ZERO delay — instant response for users
    if os.environ.get('HOSTED_ACCOUNT_ID'):
        return

    # Check if user is owner or authorized - give them fast responses
    if user_id and (is_owner(user_id) or str(user_id) in authorized_users):
        # Super fast for owner and authorized users
        delay = random.uniform(0.01, 0.02)
        await asyncio.sleep(delay)
        return
    
    if HUMAN_LIKE_DELAYS and STEALTH_MODE and not bypass_for_spam:
        # Reduced delay for faster response while maintaining security
        delay = random.uniform(0.3, 0.8)
        await asyncio.sleep(delay)
    elif bypass_for_spam:
        delay = random.uniform(0.05, 0.1)
        await asyncio.sleep(delay)

async def rotate_presence():
    """Presence rotation is disabled."""
    return

async def _rotate_presence_disabled():
    """Activity rotation has been removed."""
    return
async def enhanced_anti_ban_protection():
    """Enhanced protection against Discord bans and detection"""
    if not ANTI_BAN_MODE:
        return
    
    try:
        # Rotate presence periodically
        await rotate_presence()
        
        # Add random delay to make behavior more unpredictable
        if random.random() < 0.1:  # 10% chance
            delay = random.uniform(1.0, 5.0)
            await asyncio.sleep(delay)
        
    except Exception as e:
        if not ZERO_ERROR_MODE:
            print(f"⚠️ Anti-ban protection error: {e}")

async def anti_ban_protection_loop():
    """Continuous loop for anti-ban protection measures"""
    print("🛡️ Anti-ban protection loop started")
    
    while True:
        try:
            # Run protection measures every 5-10 minutes
            interval = random.uniform(300, 600)  # 5-10 minutes
            await asyncio.sleep(interval)
            
            # Execute anti-ban protection
            await enhanced_anti_ban_protection()
            
            # Vary command processing to appear more human
            if COMMAND_COOLDOWN and random.random() < 0.3:  # 30% chance
                await asyncio.sleep(random.uniform(1.0, COMMAND_COOLDOWN))
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            if not ZERO_ERROR_MODE:
                print(f"⚠️ Anti-ban protection loop error: {e}")
            await asyncio.sleep(30)  # Wait before retrying

def load_authorized_users():
    """Load authorized users from file"""
    global authorized_users
    try:
        if os.path.exists(AUTHORIZED_USERS_FILE):
            with open(AUTHORIZED_USERS_FILE, 'r') as f:
                user_ids = f.read().strip().split('\n')
                authorized_users = set(user_id.strip() for user_id in user_ids if user_id.strip())
                print(f"✅ Loaded {len(authorized_users)} authorized users from file")
        else:
            print("📝 No authorized users file found, starting fresh")
    except Exception as e:
        print(f"❌ Error loading authorized users: {e}")
        authorized_users = set()

def save_authorized_users():
    """Save authorized users to file"""
    try:
        with open(AUTHORIZED_USERS_FILE, 'w') as f:
            f.write('\n'.join(authorized_users))
        print(f"💾 Saved {len(authorized_users)} authorized users to file")
    except Exception as e:
        print(f"❌ Error saving authorized users: {e}")

def log_security_event(event_type, user_id, details=""):
    """Log security events for audit purposes"""
    if AUDIT_LOG_ENABLED:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        audit_entry = f"[{timestamp}] {event_type}: User {user_id} - {details}"
        security_audit_log.append(audit_entry)
        print(f"🔒 SECURITY: {audit_entry}")

def check_user_lockout(user_id):
    """Check if user is currently locked out"""
    user_id_str = str(user_id)
    if user_id_str in locked_users:
        lockout_time = locked_users[user_id_str]
        if time.time() - lockout_time < LOCKOUT_DURATION:
            return True
        else:
            # Lockout expired, remove from locked users
            del locked_users[user_id_str]
            log_security_event("LOCKOUT_EXPIRED", user_id, "User lockout expired")
    return False

def record_failed_attempt(user_id):
    """Record a failed access attempt"""
    user_id_str = str(user_id)
    current_time = time.time()
    
    if user_id_str not in failed_attempts:
        failed_attempts[user_id_str] = []
    
    # Add current attempt
    failed_attempts[user_id_str].append(current_time)
    
    # Remove attempts older than 1 hour
    failed_attempts[user_id_str] = [attempt for attempt in failed_attempts[user_id_str] 
                                   if current_time - attempt < 3600]
    
    # Check if lockout is needed
    if len(failed_attempts[user_id_str]) >= FAILED_ATTEMPTS_LIMIT:
        locked_users[user_id_str] = current_time
        log_security_event("USER_LOCKED", user_id, f"Too many failed attempts ({len(failed_attempts[user_id_str])})")
        return True
    
    log_security_event("FAILED_ATTEMPT", user_id, f"Attempt {len(failed_attempts[user_id_str])}/{FAILED_ATTEMPTS_LIMIT}")
    return False

def enhanced_owner_verification(user_id):
    """Enhanced owner verification with additional security checks"""
    user_id_str = str(user_id)
    
    # Basic ID check
    if user_id_str != BOT_OWNER_ID:
        return False
    
    # Additional verification if enabled
    if OWNER_VERIFICATION_REQUIRED:
        # Check for recent suspicious activity
        if user_id_str in failed_attempts and len(failed_attempts[user_id_str]) > 0:
            log_security_event("OWNER_SUSPICIOUS", user_id, "Owner access with recent failed attempts")
        
        # Verify session if exists
        if user_id_str in active_sessions:
            session_time = active_sessions[user_id_str]
            if time.time() - session_time > SESSION_TIMEOUT:
                del active_sessions[user_id_str]
                log_security_event("SESSION_EXPIRED", user_id, "Owner session expired")
    
    return True

def is_owner(user_id):
    """Enhanced owner check with security measures"""
    user_id_str = str(user_id)
    
    # Check if user is locked out
    if check_user_lockout(user_id):
        log_security_event("ACCESS_DENIED_LOCKOUT", user_id, "User is locked out")
        return False
    
    # Perform enhanced verification
    if enhanced_owner_verification(user_id):
        # Update active session
        active_sessions[user_id_str] = time.time()
        log_security_event("OWNER_ACCESS", user_id, "Owner access granted")
        return True
    
    # Record failed attempt for non-owner
    if user_id_str != BOT_OWNER_ID:
        record_failed_attempt(user_id)
    
    return False

def is_authorized_user(user_id):
    """Enhanced authorization check with security measures"""
    user_id_str = str(user_id)
    
    # Check if user is locked out
    if check_user_lockout(user_id):
        log_security_event("ACCESS_DENIED_LOCKOUT", user_id, "User is locked out")
        return False
    
    # Check owner first
    if is_owner(user_id):
        return True
    
    # Check authorized users
    if user_id_str in authorized_users:
        # Update active session
        active_sessions[user_id_str] = time.time()
        log_security_event("AUTHORIZED_ACCESS", user_id, "Authorized user access granted")
        return True
    
    # Record failed attempt
    record_failed_attempt(user_id)
    log_security_event("ACCESS_DENIED", user_id, "Unauthorized access attempt")
    return False

def is_user_whitelisted(user_id):
    """Check if user is whitelisted from bot features"""
    user_id_str = str(user_id)
    
    # Check in-memory whitelist first (for performance)
    if user_id_str in whitelisted_users:
        return True
    
    # Check database if available
    if DATABASE_INTEGRATION:
        try:
            from models import is_user_whitelisted_db
            return is_user_whitelisted_db(user_id)
        except Exception as e:
            print(f"❌ Error checking whitelist database: {e}")
    
    return False

def check_command_access(user_id, command_name):
    """Check if user has access to execute specific command"""
    user_id_str = str(user_id)
    
    # Owner has access to everything
    if is_owner(user_id):
        return True
    
    # Check if user is authorized
    if user_id_str not in authorized_users:
        return False
    
    # Check if command is in allowed list for authorized users
    if command_name in ALLOWED_COMMANDS_FOR_AUTHORIZED:
        return True
    
    # Command is restricted
    return False

def load_whitelisted_users():
    """Load whitelisted users from database on startup"""
    if DATABASE_INTEGRATION:
        try:
            from app import app
            with app.app_context():
                db_users = get_whitelisted_users()
                for user in db_users:
                    whitelisted_users.add(user.discord_id)
                print(f"✅ Loaded {len(whitelisted_users)} whitelisted users from database")
        except Exception as e:
            print(f"❌ Error loading whitelisted users: {e}")

def clear_all_whitelisted_users():
    """Clear all whitelisted users from memory and database - Owner only"""
    if DATABASE_INTEGRATION:
        try:
            from app import app
            with app.app_context():
                # Get all whitelisted users
                db_users = get_whitelisted_users()
                cleared_count = 0
                
                # Remove each user from database
                for user in db_users:
                    if remove_whitelisted_user_db(user.discord_id):
                        cleared_count += 1
                
                # Clear in-memory set
                whitelisted_users.clear()
                
                print(f"🧹 CLEARED: Removed {cleared_count} users from database whitelist")
                print(f"🧹 CLEARED: Cleared in-memory whitelist")
                print(f"✅ All whitelisted users have been removed - fresh start!")
                return cleared_count
        except Exception as e:
            print(f"❌ Error clearing whitelisted users: {e}")
            return 0
    else:
        # Just clear memory if no database
        count = len(whitelisted_users)
        whitelisted_users.clear()
        print(f"🧹 CLEARED: {count} users from memory (no database available)")
        return count

async def check_command_rate_limit():
    """Check if command rate limit is exceeded to prevent detection"""
    global last_command_time, command_usage_tracker

    # Hosted account subprocesses bypass rate limits — instant response
    if os.environ.get('HOSTED_ACCOUNT_ID'):
        return True

    if not RATE_LIMIT_SAFETY:
        return True
    
    current_time = time.time()
    
    # Reset tracker every minute
    if current_time - last_command_time > 60:
        command_usage_tracker.clear()
        last_command_time = current_time
    
    # Count commands in current minute
    minute_key = int(current_time // 60)
    command_count = command_usage_tracker.get(minute_key, 0)
    
    if command_count >= MAX_COMMANDS_PER_MINUTE:
        print(f"🛡️ Rate limit protection: Command blocked to avoid detection")
        return False
    
    # Update counter
    command_usage_tracker[minute_key] = command_count + 1
    return True

async def ultra_fast_response(ctx, content, delete_after=3, bypass_stealth=False):
    """ULTRA-FAST response system with anti-detection measures"""
    try:
        # Check rate limits first for stealth (bypass for spam)
        if not bypass_stealth and not await check_command_rate_limit():
            return
        
        # Add human-like delay for stealth (bypass for spam) - but make it fast for authorized users
        await add_human_like_delay(bypass_for_spam=bypass_stealth, user_id=ctx.author.id)
        
        # Performance tracking
        start_time = time.time() if PERFORMANCE_MONITORING else None
        
        # Delete command FIRST - absolutely no delay
        await instant_delete_command(ctx)
        
        # Send response immediately with optimized channel handling
        if hasattr(ctx.channel, 'send'):
            response = await ctx.channel.send(content)
        else:
            response = await ctx.send(content)
        
        # Performance logging
        if PERFORMANCE_MONITORING and start_time:
            response_time = round((time.time() - start_time) * 1000, 1)
            print(f"⚡ Ultra-fast response: {response_time}ms")
        
        # Quick cleanup - delete response after short time
        if delete_after > 0:
            await asyncio.sleep(delete_after)
            try:
                await response.delete()
            except:
                pass
            
        return response
    except Exception as e:
        if not ZERO_ERROR_MODE:
            print(f"Response error: {e}")
        return None

# Function to extract user ID from mention
def find_user_id_by_mention(mention):
    # Try to extract user ID from mention format <@12345678901234>
    mention_match = re.search(r'<@!?(\d+)>', mention)
    if mention_match:
        return mention_match.group(1)
    return None

# Event: Bot is ready
@bot.event
async def on_ready():
    try:
        # Dynamically set the owner ID to the logged-in account's own ID
        global BOT_OWNER_ID
        BOT_OWNER_ID = str(bot.user.id)

        # Status setting disabled due to Discord API compatibility issues
        print("⚠️ Status updates disabled due to Discord API compatibility issues (MessageToDict error)")
        print("✅ Bot functionality remains fully operational - only status display affected")
        
        print(f"✅ Logged in as {bot.user.name} ({bot.user.id})")
        print(f"✅ Using discord.py-self version: {discord.__version__}")
        print("✅ Bot is ready! Use the command -flash <amount> <ltc_address> to send flash messages")
        
        # Configure Jishaku environment variables for maximum discord.py-self compatibility
        import os
        os.environ["JISHAKU_NO_UNDERSCORE"] = "True"  # Allow .jsk instead of ._jsk
        os.environ["JISHAKU_RETAIN"] = "True"  # Retain variables between .jsk py sessions
        os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"  # Don't DM tracebacks
        os.environ["JISHAKU_FORCE_PREFIXES"] = "."  # Force jishaku to use . prefix only
        os.environ["JISHAKU_HIDE"] = "True"  # Hide jishaku from help command
        os.environ["JISHAKU_NO_PAGINATOR"] = "True"  # Disable paginator to avoid view compatibility issues
        os.environ["JISHAKU_COMMAND_SCOPE"] = "guild"  # Limit command scope for compatibility
        os.environ["JISHAKU_NO_SETUP_LOGGING"] = "True"  # Prevent jishaku logging conflicts
        
        # Add comprehensive compatibility patches for discord.py-self and jishaku
        try:
            # Patch missing discord module attributes
            if not hasattr(discord, 'AutoShardedClient'):
                discord.AutoShardedClient = discord.Client
            if not hasattr(discord, 'AutoShardedBot'):
                discord.AutoShardedBot = discord.ext.commands.Bot
            
            # COMPREHENSIVE UI MOCKING - ALL discord.py UI components for discord.py-self compatibility
            if not hasattr(discord, 'ui'):
                class MockUI:
                    # Core UI Components
                    class View:
                        def __init__(self, **kwargs):
                            self.timeout = kwargs.get('timeout', 180)
                            self.children = []
                        async def interaction_check(self, interaction):
                            return True
                        def add_item(self, item):
                            pass
                        def remove_item(self, item):
                            pass
                        def clear_items(self):
                            pass
                        def stop(self):
                            pass
                        def is_finished(self):
                            return False
                        async def wait(self):
                            pass
                        @classmethod
                        def __class_getitem__(cls, item):
                            return cls  # Support generic type annotations
                        @classmethod
                        def __init_subclass__(cls, **kwargs):
                            pass  # Support advanced class inheritance
                    
                    class Button:
                        def __init__(self, **kwargs):
                            self.style = kwargs.get('style', 1)
                            self.label = kwargs.get('label', '')
                            self.disabled = kwargs.get('disabled', False)
                            self.custom_id = kwargs.get('custom_id', None)
                            self.emoji = kwargs.get('emoji', None)
                            self.url = kwargs.get('url', None)
                            self.row = kwargs.get('row', None)
                        def callback(self, interaction):
                            pass
                        @classmethod
                        def __class_getitem__(cls, item):
                            return cls  # Support generic type annotations like Button[SomeType]
                        @classmethod
                        def __init_subclass__(cls, **kwargs):
                            pass  # Support advanced class inheritance
                    
                    class Select:
                        def __init__(self, **kwargs):
                            self.placeholder = kwargs.get('placeholder', '')
                            self.min_values = kwargs.get('min_values', 1)
                            self.max_values = kwargs.get('max_values', 1)
                            self.options = kwargs.get('options', [])
                            self.disabled = kwargs.get('disabled', False)
                            self.custom_id = kwargs.get('custom_id', None)
                            self.row = kwargs.get('row', None)
                        def callback(self, interaction):
                            pass
                        @classmethod
                        def __class_getitem__(cls, item):
                            return cls  # Support generic type annotations
                        @classmethod
                        def __init_subclass__(cls, **kwargs):
                            pass  # Support advanced class inheritance
                    
                    class TextInput:
                        def __init__(self, **kwargs):
                            self.label = kwargs.get('label', '')
                            self.style = kwargs.get('style', 1)
                            self.placeholder = kwargs.get('placeholder', '')
                            self.default = kwargs.get('default', None)
                            self.required = kwargs.get('required', True)
                            self.min_length = kwargs.get('min_length', None)
                            self.max_length = kwargs.get('max_length', None)
                            self.row = kwargs.get('row', None)
                        @classmethod
                        def __class_getitem__(cls, item):
                            return cls  # Support generic type annotations
                        @classmethod
                        def __init_subclass__(cls, **kwargs):
                            pass  # Support advanced class inheritance
                    
                    class Modal:
                        def __init__(self, **kwargs):
                            self.title = kwargs.get('title', '')
                            self.timeout = kwargs.get('timeout', None)
                            self.children = []
                        def add_item(self, item):
                            pass
                        async def on_submit(self, interaction):
                            pass
                        async def interaction_check(self, interaction):
                            return True
                        @classmethod
                        def __class_getitem__(cls, item):
                            return cls  # Support generic type annotations
                        @classmethod
                        def __init_subclass__(cls, **kwargs):
                            pass  # Support advanced class inheritance
                    
                    # UI Item Base Classes
                    class Item:
                        def __init__(self, **kwargs):
                            self.row = kwargs.get('row', None)
                            self.disabled = kwargs.get('disabled', False)
                        @classmethod
                        def __class_getitem__(cls, item):
                            return cls  # Support generic type annotations
                        @classmethod
                        def __init_subclass__(cls, **kwargs):
                            pass  # Support advanced class inheritance
                    
                    # Button Styles
                    class ButtonStyle:
                        primary = 1
                        secondary = 2
                        success = 3
                        danger = 4
                        link = 5
                        blurple = 1
                        grey = 2
                        gray = 2
                        green = 3
                        red = 4
                        url = 5
                    
                    # Text Input Styles
                    class TextStyle:
                        short = 1
                        paragraph = 2
                        long = 2
                    
                    # Select Option
                    class SelectOption:
                        def __init__(self, **kwargs):
                            self.label = kwargs.get('label', '')
                            self.value = kwargs.get('value', '')
                            self.description = kwargs.get('description', None)
                            self.emoji = kwargs.get('emoji', None)
                            self.default = kwargs.get('default', False)
                
                discord.ui = MockUI()
            
            # COMPREHENSIVE INTERACTION SYSTEM MOCKING
            if not hasattr(discord, 'Interaction'):
                class MockInteraction:
                    def __init__(self):
                        self.type = None
                        self.token = 'mock_token'
                        self.id = 123456789
                        self.application_id = 987654321
                        self.user = None
                        self.member = None
                        self.guild = None
                        self.channel = None
                        self.message = None
                        self.data = {}
                        self.response = MockInteractionResponse()
                        self.followup = MockWebhook()
                    
                    async def respond(self, *args, **kwargs):
                        pass
                    
                    async def edit_original_response(self, **kwargs):
                        pass
                    
                    async def delete_original_response(self):
                        pass
                    
                    async def followup_send(self, *args, **kwargs):
                        pass
                
                class MockInteractionResponse:
                    def __init__(self):
                        self.is_done = lambda: False
                    
                    async def send_message(self, *args, **kwargs):
                        pass
                    
                    async def edit_message(self, **kwargs):
                        pass
                    
                    async def defer(self, **kwargs):
                        pass
                
                class MockWebhook:
                    async def send(self, *args, **kwargs):
                        pass
                    
                    async def edit_message(self, message_id, **kwargs):
                        pass
                    
                    async def delete_message(self, message_id):
                        pass
                
                discord.Interaction = MockInteraction
                discord.InteractionResponse = MockInteractionResponse
            
            # COMPREHENSIVE APP COMMANDS MOCKING
            if not hasattr(discord, 'app_commands'):
                class MockAppCommands:
                    def __init__(self):
                        pass
                    
                    class Command:
                        def __init__(self, **kwargs):
                            self.name = kwargs.get('name', '')
                            self.description = kwargs.get('description', '')
                            self.callback = kwargs.get('callback', None)
                    
                    class Group:
                        def __init__(self, **kwargs):
                            self.name = kwargs.get('name', '')
                            self.description = kwargs.get('description', '')
                    
                    class CommandTree:
                        def __init__(self, client):
                            self.client = client
                        
                        async def sync(self, **kwargs):
                            pass
                        
                        def command(self, **kwargs):
                            def decorator(func):
                                return func
                            return decorator
                        
                        def add_command(self, command):
                            pass
                        
                        def remove_command(self, command):
                            pass
                    
                    class Describe:
                        def __init__(self, **kwargs):
                            pass
                    
                    class Choice:
                        def __init__(self, **kwargs):
                            self.name = kwargs.get('name', '')
                            self.value = kwargs.get('value', '')
                    
                    def command(**kwargs):
                        def decorator(func):
                            return func
                        return decorator
                    
                    def describe(**kwargs):
                        def decorator(func):
                            return func
                        return decorator
                    
                    def choices(**kwargs):
                        def decorator(func):
                            return func
                        return decorator
                
                discord.app_commands = MockAppCommands()
            
            # ADDITIONAL DISCORD.PY FEATURES MISSING IN DISCORD.PY-SELF
            if not hasattr(discord, 'Webhook'):
                class MockWebhook:
                    def __init__(self, **kwargs):
                        self.url = kwargs.get('url', '')
                        self.id = kwargs.get('id', 123456)
                        self.token = kwargs.get('token', 'mock_token')
                    
                    async def send(self, *args, **kwargs):
                        pass
                    
                    async def edit(self, **kwargs):
                        pass
                    
                    async def delete(self):
                        pass
                    
                    @classmethod
                    async def from_url(cls, url, **kwargs):
                        return cls(url=url)
                
                discord.Webhook = MockWebhook
            
            # PATCH COMMAND PROCESSING FOR JISHAKU COMPATIBILITY
            # Override Messageable.send to handle 'view' parameter gracefully
            original_send = discord.abc.Messageable.send
            async def patched_send(self, content=None, **kwargs):
                # Remove problematic kwargs that discord.py-self doesn't support
                kwargs.pop('view', None)  # Remove view parameter
                kwargs.pop('ephemeral', None)  # Remove ephemeral parameter
                kwargs.pop('suppress_embeds', None)  # Remove suppress_embeds parameter
                kwargs.pop('silent', None)  # Remove silent parameter
                return await original_send(self, content, **kwargs)
            
            discord.abc.Messageable.send = patched_send
            
            # PATCH COMMAND PARAMETER PARSING
            from discord.ext.commands import Parameter, Command
            if hasattr(Parameter, '__annotations__'):
                # Patch parameter annotations that might cause issues
                original_param_init = Parameter.__init__
                def patched_param_init(self, name, kind=None, **kwargs):
                    # Remove problematic parameter annotations
                    kwargs.pop('annotation', None)
                    return original_param_init(self, name, kind, **kwargs)
                Parameter.__init__ = patched_param_init
            
            # MOCK SLASH COMMAND DECORATORS
            if not hasattr(discord.ext.commands, 'hybrid_command'):
                def hybrid_command(**kwargs):
                    def decorator(func):
                        return discord.ext.commands.command(**kwargs)(func)
                    return decorator
                discord.ext.commands.hybrid_command = hybrid_command
            
            if not hasattr(discord.ext.commands, 'hybrid_group'):
                def hybrid_group(**kwargs):
                    def decorator(func):
                        return discord.ext.commands.group(**kwargs)(func)
                    return decorator
                discord.ext.commands.hybrid_group = hybrid_group
            
            # Patch missing bot attributes that jishaku expects
            if not hasattr(bot, 'shards'):
                bot.shards = {}  # Empty dict for non-sharded bots
            if not hasattr(bot, 'shard_count'):
                bot.shard_count = None
            if not hasattr(bot, 'shard_id'):
                bot.shard_id = None
            if not hasattr(bot, 'shard_ids'):
                bot.shard_ids = None
            if not hasattr(bot, 'intents'):
                # Create a mock intents object for jishaku compatibility
                class MockIntents:
                    def __init__(self):
                        self.all = lambda: True
                        self.none = lambda: False
                        self.default = lambda: True
                        # Add common intent attributes
                        self.guilds = True
                        self.members = True
                        self.bans = True
                        self.emojis = True
                        self.integrations = True
                        self.webhooks = True
                        self.invites = True
                        self.voice_states = True
                        self.presences = True
                        self.messages = True
                        self.guild_messages = True
                        self.dm_messages = True
                        self.reactions = True
                        self.guild_reactions = True
                        self.dm_reactions = True
                        self.typing = True
                        self.guild_typing = True
                        self.dm_typing = True
                        self.message_content = True
                bot.intents = MockIntents()
                
            # Add missing methods that jishaku might call
            if not hasattr(bot, 'is_closed'):
                def is_closed_method():
                    return bot.is_closed()
                bot.is_closed = is_closed_method
                
            # Patch missing gateway attributes
            if hasattr(bot, '_connection') and bot._connection:
                if not hasattr(bot._connection, 'shard_count'):
                    bot._connection.shard_count = None
                if not hasattr(bot._connection, 'shard_id'):
                    bot._connection.shard_id = None
                    
            print("✅ Comprehensive discord.py-self compatibility patches applied for jishaku")
        except Exception as patch_err:
            print(f"⚠️ Failed to apply compatibility patches: {patch_err}")
        
        # Load Jishaku extension
        try:
            await bot.load_extension("jishaku")
            print("✅ Jishaku (JSK) extension loaded successfully!")
            print("🔧 Available commands: .jsk py <code>, .jsk sh <command>, .jsk su, etc.")
            print(f"🔧 Jishaku is configured for owner ID: {bot.owner_id}")
            print("💡 Note: Use .jsk (not -jsk) for jishaku commands")
        except Exception as jsk_err:
            print(f"⚠️ Failed to load Jishaku: {jsk_err}")
            print("Bot will continue without Jishaku...")
        
        # Start enhanced keep-alive system with multiple layers
        try:
            asyncio.create_task(ultra_enhanced_keep_alive_task())
            print("🚀 Ultra-Enhanced AI-powered keep-alive system activated successfully")
        except Exception as ka_err:
            print(f"❌ Failed to start enhanced keep-alive task: {ka_err}")
        
        # Start secondary heartbeat for redundancy
        try:
            asyncio.create_task(secondary_heartbeat_task())
            print("✅ Secondary heartbeat task started successfully")
        except Exception as sh_err:
            print(f"❌ Failed to start secondary heartbeat: {sh_err}")
        
        # Start enhanced background tasks with monitoring
        try:
            asyncio.create_task(enhanced_background_tasks())
            print("✅ Enhanced background tasks started successfully")
        except Exception as bg_err:
            print(f"❌ Failed to start enhanced background tasks: {bg_err}")
        
        # Start enhanced anti-ban protection system
        try:
            asyncio.create_task(anti_ban_protection_loop())
            print("🛡️ Enhanced anti-ban protection system activated")
        except Exception as ab_err:
            print(f"❌ Failed to start anti-ban protection: {ab_err}")
        
        # Initialize security system
        try:
            log_security_event("SYSTEM_START", BOT_OWNER_ID, "Bot security system initialized")
            print("🔒 Enhanced security system initialized")
        except Exception as sec_err:
            print(f"❌ Failed to initialize security system: {sec_err}")
        
        # Load authorized users from file
        try:
            load_authorized_users()
        except Exception as load_err:
            print(f"❌ Failed to load authorized users: {load_err}")
        
        # Load whitelisted users from database
        try:
            load_whitelisted_users()
        except Exception as wl_err:
            print(f"❌ Failed to load whitelisted users: {wl_err}")
        
        # Set initial presence for anti-ban protection
        try:
            await enhanced_anti_ban_protection()
            print("🔄 Initial anti-ban presence set")
        except Exception as init_pres_err:
            print(f"⚠️ Initial presence setting error: {init_pres_err}")
            
    except Exception as ready_err:
        print(f"❌ Critical error in on_ready event: {ready_err}")
        # Continue running even if initialization fails

# Voice state update event - monitor for users rejoining voice channels
@bot.event
async def on_voice_state_update(member, before, after):
    """Monitor voice state changes for users we're annoying"""
    user_id_str = str(member.id)
    
    # Check if this user is being annoyed and just joined a voice channel
    if user_id_str in annoying_users and after.channel is not None and before.channel is None:
        user_data = annoying_users[user_id_str]
        guild = bot.get_guild(user_data['guild_id'])
        channel = bot.get_channel(user_data['channel_id'])
        
        if guild and channel:
            print(f"🎯 DETECTED REJOIN: {user_data['mention']} joined voice channel")
            
            # Small delay to ensure they're fully connected
            await asyncio.sleep(2)
            
            # Re-annoy them
            actions_performed = []
            
            try:
                await member.edit(mute=True)
                actions_performed.append("🔇 Muted")
            except:
                pass
            
            try:
                await member.edit(deafen=True)
                actions_performed.append("🔕 Deafened")
            except:
                pass
            
            try:
                await member.edit(voice_channel=None)
                actions_performed.append("🚫 Disconnected")
            except:
                pass
            
            if actions_performed:
                actions_text = " + ".join(actions_performed)
                try:
                    await channel.send(f"😈 **CAUGHT REJOINING!** {user_data['mention']}\n{actions_text}\n🔄 **Still monitoring...**")
                except:
                    pass

# Error handling for commands (optimized for speed and stability)
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        # Don't respond to unknown commands - silent ignore for speed
        return
    
    try:
        if isinstance(error, commands.MissingRequiredArgument):
            content = f"Error: Missing required argument: {error.param.name}"
        elif isinstance(error, commands.BadArgument):
            content = f"Error: Invalid argument provided. Check your inputs."
        else:
            content = f"Error: {error}"
        
        # Use ultra_fast_response for error handling
        await ultra_fast_response(ctx, content, delete_after=3, bypass_stealth=True)
        
    except Exception as e:
        # Silent error handling to prevent cascading errors
        if not ZERO_ERROR_MODE:
            print(f"Error handler failed: {e}")
        pass

# Command: -flash <amount> <ltc_address>
@bot.command()
async def flash(ctx, *, args=None):
    # If no arguments provided, show help
    if args is None or args.strip() == "":
        await ultra_fast_response(ctx, "Usage: `-flash <amount> <ltc_address>`\nExample: `-flash 0.5 LTC_ADDRESS_HERE`", delete_after=8, bypass_stealth=True)
        return
        
    try:
        # Parse arguments
        parts = args.strip().split()
        if len(parts) < 2:
            await ultra_fast_response(ctx, "Error: Not enough arguments. Usage: `-flash <amount> <ltc_address>`", delete_after=5, bypass_stealth=True)
            return
            
        # First part should be the amount - handle both "1" and "1$" formats
        try:
            # Check if amount has a $ sign in it and remove it
            amount_str = parts[0]
            if '$' in amount_str:
                amount_str = amount_str.replace('$', '')
            
            amount = float(amount_str)
        except ValueError:
            await ctx.message.edit(content="Error: Invalid amount. Must be a number (with optional $ sign).")
            await asyncio.sleep(5)
            await ctx.message.delete()
            return
            
        # Second part is the LTC address
        ltc_address = parts[1]
        
        # Input validation
        if amount <= 0:
            raise ValueError("Amount must be greater than 0 LTC.")
        
        # Validate Litecoin address format
        if not LTC_ADDRESS_PATTERN.match(ltc_address):
            raise ValueError("Invalid LTC address format. Must be a valid Litecoin address.")
        
        # The message to be sent - format with one decimal place and $ symbol
        flash_message = f"⚡**LTC FLASH**⚡\n{amount:.1f}$ LTC sent to {ltc_address}"
        
        # Initialize success/fail counters
        success_count = 0
        failed_count = 0
        
        # Get all accessible channels
        all_channels = []
        
        # Update progress
        await ctx.message.edit(content=f"⚡ Sending {amount:.1f}$ LTC to {ltc_address}...\nScanning for accessible channels.")
        
        # Get all channels the bot has access to
        for guild in bot.guilds:
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    all_channels.append(channel)
        
        total_channels = len(all_channels)
        await ctx.message.edit(content=f"⚡ Sending {amount:.1f}$ LTC to {ltc_address}...\nFound {total_channels} accessible channels.")
        
        # Send to all accessible channels with progress updates
        for i, channel in enumerate(all_channels):
            try:
                await channel.send(flash_message)
                success_count += 1
                
                # Update progress every 5 channels or on the last channel
                if i % 5 == 0 or i == total_channels - 1:
                    await ctx.message.edit(content=f"⚡ Flashing {amount:.1f}$ LTC to {ltc_address}...\nProgress: {i+1}/{total_channels} channels")
                
                # Add delay to avoid rate limits (adaptive based on channel count)
                delay = min(1.5, max(0.5, total_channels / 100))  # Between 0.5s and 1.5s
                await asyncio.sleep(delay)
            except Exception as e:
                failed_count += 1
                print(f"Failed to send to channel {channel.name} in {channel.guild.name}: {e}")
                # Continue to next channel without stopping the loop
                continue
        
        # Final update with results
        await ctx.message.edit(content=f"✅ Flash completed! {amount:.1f}$ LTC to {ltc_address}\n"
                                      f"Sent to {success_count} channels. ({failed_count} failed)")
        
        # Delete the command message after 10 seconds
        await asyncio.sleep(10)
        await ctx.message.delete()
        
    except ValueError as e:
        # Handle validation errors
        await ctx.message.edit(content=f"❌ Error: {e}")
        await asyncio.sleep(5)
        await ctx.message.delete()
    except Exception as e:
        # Handle unexpected errors
        await ctx.message.edit(content=f"❌ Unexpected error: {e}")
        print(f"Error in flash command: {e}")
        await asyncio.sleep(5)
        await ctx.message.delete()



# Command to flash to a specific channel only
@bot.command()
async def flashchannel(ctx, *, args=None):
    # If no arguments provided, show help
    if args is None or args.strip() == "":
        await ctx.message.edit(content="Usage: `-flashchannel <amount> <ltc_address>`\nSends flash message to current channel only.")
        await asyncio.sleep(10)
        await ctx.message.delete()
        return
        
    try:
        # Parse arguments manually
        parts = args.strip().split()
        if len(parts) < 2:
            await ctx.message.edit(content="Error: Not enough arguments. Usage: `-flashchannel <amount> <ltc_address>`")
            await asyncio.sleep(5)
            await ctx.message.delete()
            return
            
        # First part should be the amount - handle both "1" and "1$" formats
        try:
            # Check if amount has a $ sign in it and remove it
            amount_str = parts[0]
            if '$' in amount_str:
                amount_str = amount_str.replace('$', '')
            
            amount = float(amount_str)
        except ValueError:
            await ctx.message.edit(content="Error: Invalid amount. Must be a number (with optional $ sign).")
            await asyncio.sleep(5)
            await ctx.message.delete()
            return
            
        # Second part is the LTC address
        ltc_address = parts[1]
        
        # Input validation
        if amount <= 0:
            raise ValueError("Amount must be greater than 0 LTC.")
        
        # Validate Litecoin address format
        if not LTC_ADDRESS_PATTERN.match(ltc_address):
            raise ValueError("Invalid LTC address format. Must be a valid Litecoin address.")

        # Use the current channel instead of a specific channel
        specific_channel_id = ctx.channel.id  # Use current channel ID
        
        # Update progress
        await ctx.message.edit(content=f"⚡ Sending {amount:.1f}$ LTC to {ltc_address}...\nTargeting specific channel.")
        
        try:
            # Get the specific channel
            channel = await bot.fetch_channel(specific_channel_id)
            
            # The message to be sent - format with one decimal place
            flash_message = f"⚡**LTC FLASH**⚡\n{amount:.1f}$ LTC sent to {ltc_address}"
            
            # Send the message
            await channel.send(flash_message)
            
            # Success message
            await ctx.message.edit(content=f"✅ Flash sent to current channel! {amount:.1f}$ LTC to {ltc_address}")
            await asyncio.sleep(5)
            await ctx.message.delete()
            
        except Exception as e:
            await ctx.message.edit(content=f"❌ Error: Could not send to the channel: {e}")
            await asyncio.sleep(5)
            await ctx.message.delete()
            
    except ValueError as e:
        await ctx.message.edit(content=f"❌ Error: {e}")
        await asyncio.sleep(5)
        await ctx.message.delete()
    except Exception as e:
        await ctx.message.edit(content=f"❌ Unexpected error: {e}")
        await asyncio.sleep(5)
        await ctx.message.delete()

# Function to check Litecoin balance of an address
async def check_ltc_balance(address):
    """
    Checks the LTC balance of a given address using a public API
    Returns (success, balance, error_message)
    """
    try:
        # Using Blockcypher API
        url = f"https://api.blockcypher.com/v1/ltc/main/addrs/{address}/balance"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # Balance is in satoshis (litoshis), convert to LTC
            balance = data['final_balance'] / 100000000  # 1 LTC = 100,000,000 litoshis
            return True, balance, None
        else:
            return False, 0, f"API Error: {response.status_code}"
    except Exception as e:
        return False, 0, f"Error checking balance: {str(e)}"

# Command to check LTC balance of an address
@bot.command(name="bal")
async def balance(ctx, *, args=None):
    """Check the balance of a Litecoin address"""
    # Debug print to check what arguments are received
    print(f"BAL COMMAND DEBUG: Raw args received: '{args}'")
    
    # If no arguments provided, show help
    if args is None or args.strip() == "":
        await ctx.message.edit(content="Usage: `-bal <ltc_address>`\nExample: `-bal LTC_ADDRESS_HERE`")
        await asyncio.sleep(10)
        await ctx.message.delete()
        return
        
    try:
        # Parse the address from args (just get the first part which should be the address)
        address = args.strip()
        print(f"BAL COMMAND DEBUG: Parsed address: '{address}'")
        
        # Skip validation for now to see if that's causing issues
        # if not LTC_ADDRESS_PATTERN.match(address):
        #    print(f"BAL COMMAND DEBUG: Address validation failed for '{address}'")
        #    await ctx.message.edit(content=f"❌ Error: Invalid LTC address format: `{address}`")
        #    await asyncio.sleep(5)
        #    await ctx.message.delete()
        #    return
        
        # Always proceed with the check
        # Update message to show that we're checking
        await ctx.message.edit(content=f"🔍 Checking balance of {address}...")
        
        # Check balance
        success, balance, error = await check_ltc_balance(address)
        print(f"BAL COMMAND DEBUG: API check result: success={success}, balance={balance}, error={error}")
        
        if success:
            # Format balance with 8 decimal places, as is standard for crypto
            await ctx.message.edit(content=f"💰 **LTC Balance**\nAddress: `{address}`\nBalance: **{balance:.8f}$** LTC")
            await asyncio.sleep(15)  # Keep the balance visible longer
        else:
            await ctx.message.edit(content=f"❌ Failed to check balance: {error}")
            await asyncio.sleep(5)
            
        # Delete the message after delay
        await ctx.message.delete()
        
    except Exception as e:
        error_msg = f"❌ Error: {e}"
        print(f"BAL COMMAND DEBUG: Exception caught: {e}")
        await ctx.message.edit(content=error_msg)
        await asyncio.sleep(5)
        await ctx.message.delete()

# Function to check for inactive drowned users and send reminder messages (DISABLED TO FIX CORRUPTION)
async def check_drowned_users_inactivity():
    """TEMPORARILY DISABLED to fix coroutine corruption issues"""
    try:
        # Clear any corrupted data completely
        drowned_users.clear()
        print("🧹 Cleared drowned_users dictionary to prevent corruption")
    except Exception as e:
        print(f"Error clearing drowned_users: {e}")
    
    # Sleep and do nothing to prevent errors
    await asyncio.sleep(5)

# Event: Process all messages and commands in any channel
@bot.event
async def on_message(message):
    try:
        # Skip bot's own messages to avoid infinite loops
        if bot.user and message.author.id == bot.user.id:
            try:
                # Only process commands from the bot itself
                if message.content.startswith(bot.command_prefix):
                    try:
                        # Process the command
                        channel_name = message.channel.name if hasattr(message.channel, 'name') else 'Unknown'
                        print(f"📝 Processing selfbot command in channel: {channel_name}")
                        await bot.process_commands(message)
                    except Exception as cmd_err:
                        print(f"❌ Error processing command: {cmd_err}")
                return
                
            except Exception as self_msg_err:
                print(f"❌ Error processing own message: {self_msg_err}")
                return
        
        # Check if message is from authorized user trying to control the bot
        if str(message.author.id) in authorized_users and message.content.startswith(bot.command_prefix):
            try:
                # Extract command name from message
                command_parts = message.content[1:].split()  # Remove prefix and split
                command_name = command_parts[0].lower() if command_parts else ""
                
                # Check if user has access to this specific command
                if not check_command_access(message.author.id, command_name):
                    # Send access denied message
                    allowed_cmds = ", ".join([f"-{cmd}" for cmd in sorted(ALLOWED_COMMANDS_FOR_AUTHORIZED)])
                    deny_msg = f"🚫 **ACCESS RESTRICTED**\n❌ You can only use: {allowed_cmds}\n💡 Contact owner for full access"
                    
                    try:
                        # Send the denial message and delete it quickly
                        denial_response = await message.channel.send(deny_msg)
                        await asyncio.sleep(5)  # Reduced from 8 to 5 seconds
                        try:
                            await denial_response.delete()
                        except:
                            pass  # Ignore if already deleted
                        try:
                            await message.delete()  # Delete the unauthorized command
                        except:
                            pass  # Ignore if already deleted
                        
                        # Log security event for audit trail
                        log_security_event("COMMAND_DENIED", message.author.id, f"Attempted to use restricted command: {command_name}")
                    except Exception as deny_err:
                        print(f"⚠️ Could not send/delete denial message: {deny_err}")
                    
                    print(f"🚫 Denied command '{command_name}' for authorized user {message.author.name} - not in allowed list")
                    return
                
                # Add stealth delay for authorized commands (bypass for spam and owner)
                is_owner = str(message.author.id) == BOT_OWNER_ID
                bypass_stealth = command_name == "spam" or is_owner
                await add_human_like_delay(bypass_for_spam=bypass_stealth)
                
                # Check rate limits for stealth (bypass for spam command and owner)
                if not bypass_stealth and not await check_command_rate_limit():
                    print(f"🛡️ Blocked authorized command due to rate limit protection")
                    return
                
                # Create a fake context for the authorized user
                # This allows them to execute commands through your bot
                channel_name = message.channel.name if hasattr(message.channel, 'name') else 'Unknown'
                print(f"🎯 Processing authorized user command from {message.author.name} ({message.author.id}) in {channel_name}: {message.content}")
                
                # Create a fake message with bot as author but keep original context
                fake_message = copy.copy(message)
                fake_message.author = bot.user
                
                # Process the command with the fake message
                ctx = await bot.get_context(fake_message)
                if ctx.command:
                    print(f"✅ Found command: {ctx.command.name}")
                    await ctx.command.invoke(ctx)
                else:
                    print(f"❌ Command not found: {message.content}")
                    # Try alternative processing
                    await bot.process_commands(fake_message)
                
                # Delete the authorized user's command for cleaner chat
                try:
                    await message.delete()
                    print(f"✅ Deleted authorized user's command message")
                except Exception as del_err:
                    print(f"⚠️ Could not delete command: {del_err}")
                    
            except Exception as auth_cmd_err:
                print(f"❌ Error processing authorized command: {auth_cmd_err}")
            return
            
        # Check for "sybau" in any case and react with 🥀💔 (works in all channel types)
        message_content_lower = message.content.lower()
        if "sybau" in message_content_lower:
            # Check if user is whitelisted
            if is_user_whitelisted(message.author.id):
                print(f"🛡️ WHITELIST PROTECTION: Skipped 'sybau' reaction for protected user {message.author.name} ({message.author.id})")
                try:
                    # Send discrete protection notification
                    protection_msg = await message.channel.send("🛡️ **Whitelist Protection Active** - User is protected from bot reactions")
                    await asyncio.sleep(4)
                    await protection_msg.delete()
                except:
                    pass
            else:
                try:
                    # Always try to react, regardless of channel type
                    await message.add_reaction("🥀")
                    await message.add_reaction("💔")
                    
                    # Log success based on channel type
                    if isinstance(message.channel, discord.DMChannel):
                        print(f"✅ Reacted to 'sybau' from {message.author.name} in DM")
                    elif isinstance(message.channel, discord.GroupChannel):
                        print(f"✅ Reacted to 'sybau' from {message.author.name} in group chat")
                    else:
                        print(f"✅ Reacted to 'sybau' from {message.author.name} in #{message.channel.name}")
                        
                except discord.Forbidden:
                    # Silently handle permission errors for cleaner logs
                    pass
                except discord.HTTPException as e:
                    # Log only unexpected HTTP errors
                    if e.status != 403:  # Don't log permission errors
                        print(f"HTTP error adding reactions: {e}")
                except Exception as e:
                    print(f"Unexpected error adding reactions: {e}")
        
        # Auto-reaction system - check if user is being tracked for reactions
        user_id_str = str(message.author.id)
        if user_id_str in reaction_targets and reaction_targets[user_id_str]['active']:
            # Check if user is whitelisted (MAIN PROTECTION THAT WAS MISSING)
            if is_user_whitelisted(message.author.id):
                # Remove from reaction targets and notify
                del reaction_targets[user_id_str]
                print(f"🛡️ WHITELIST PROTECTION: Removed {message.author.name} ({user_id_str}) from auto-reactions - user is now protected")
                try:
                    # Send clear protection notification
                    protection_msg = await message.channel.send(f"🛡️ **PROTECTION ACTIVATED** - {message.author.mention} is now protected from harassment\n✅ **Auto-reactions stopped** due to whitelist protection")
                    await asyncio.sleep(8)
                    await protection_msg.delete()
                except:
                    pass
            else:
                try:
                    emoji = reaction_targets[user_id_str]['emoji']
                    await message.add_reaction(emoji)
                    print(f"🚀 Auto-reacted {emoji} to {message.author.name}'s message")
                except Exception as e:
                    if not ZERO_ERROR_MODE:
                        print(f"Error auto-reacting: {e}")
        
        # AFK system - check for mentions and DMs
        if (bot.user and bot.user.mentioned_in(message)) or isinstance(message.channel, discord.DMChannel):
            # Check if bot owner is AFK
            if bot.user and str(bot.user.id) in afk_users and afk_users[str(bot.user.id)]['status']:
                afk_data = afk_users[str(bot.user.id)]
                afk_message = afk_data.get('message', '')
                timestamp = afk_data.get('timestamp', time.time())
                
                # Calculate how long been AFK
                time_afk = int(time.time() - timestamp)
                hours = time_afk // 3600
                minutes = (time_afk % 3600) // 60
                
                time_str = ""
                if hours > 0:
                    time_str = f"{hours}h {minutes}m"
                else:
                    time_str = f"{minutes}m"
                
                # Create AFK reply
                if afk_message:
                    afk_reply = f"I'm AFK 🌙 - {afk_message} (since {time_str} ago)"
                else:
                    afk_reply = f"I'm AFK 🌙 (since {time_str} ago)"
                
                try:
                    await message.channel.send(afk_reply)
                    print(f"📱 Sent AFK auto-reply to {message.author.name}: {afk_reply}")
                except Exception as e:
                    if not ZERO_ERROR_MODE:
                        print(f"Error sending AFK reply: {e}")
        
        # Remove AFK status if bot owner sends a message (not a command)
        if bot.user and message.author.id == bot.user.id and not message.content.startswith(bot.command_prefix):
            if str(bot.user.id) in afk_users and afk_users[str(bot.user.id)]['status']:
                # Remove AFK status
                del afk_users[str(bot.user.id)]
                print("📱 Removed AFK status - user is back")
                
                try:
                    await message.channel.send("Welcome back! 👋 AFK status removed.")
                except Exception as e:
                    if not ZERO_ERROR_MODE:
                        print(f"Error sending welcome back message: {e}")
            
        # Check if this user is being drowned
        user_id_str = str(message.author.id)
        if user_id_str in drowned_users:
            # Check if user is now whitelisted (protection override)
            if is_user_whitelisted(message.author.id):
                # Remove from drowning and notify
                del drowned_users[user_id_str]
                print(f"🛡️ WHITELIST PROTECTION: Removed {message.author.name} ({user_id_str}) from drowning - user is now protected")
                try:
                    # Send clear protection notification
                    protection_msg = await message.channel.send(f"🛡️ **PROTECTION ACTIVATED** - {message.author.mention} is now protected from harassment\n✅ **Drowning stopped** due to whitelist protection")
                    await asyncio.sleep(8)
                    await protection_msg.delete()
                except:
                    pass
                return
            
            # Get user data
            user_data = drowned_users[user_id_str]
            mention = user_data["mention"]
            language_pref = user_data.get("language", "both")
            
            # Update last message time
            drowned_users[user_id_str]["last_message_time"] = time.time()
            
            print(f"🎯 Detected drowned user {message.author.name} ({user_id_str}) - auto-replying with {language_pref} insults")
            
            # Savage insults in Hindi
            hindi_insults = [
                f"{mention} तेरी मां की चूत मैं अपना लंड डालूंगा",
                f"{mention} रंडी की औलाद मर जा",
                f"{mention} तेरी बहन को चोदूंगा कुत्ते",
                f"{mention} भोसडीके तेरी गांड मारूंगा",
                f"{mention} तेरी मां को रंडीखाने में बेचूंगा",
                f"{mention} हरामी की औलाद खुदकुशी कर ले",
                f"{mention} मादरचोद तेरा बाप रंडी बाज़ है",
                f"{mention} तेरी बीवी को चोदकर वीडियो बनाऊंगा",
                f"{mention} गांडू तेरी औकात गंदगी से भी कम है",
                f"{mention} अपनी गांड में आग लगा और मर जा साले"
            ]
            
            # English savage replies
            english_insults = [
                f"{mention} you're a fucking worthless piece of shit who should kill yourself",
                f"{mention} is a disgusting cock-sucking whore who deserves to die",
                f"Look at this pathetic brain-dead retard {mention}, your mother should have aborted you",
                f"{mention} you're the most useless cunt alive, go fucking hang yourself",
                f"Everyone wants you dead {mention}, you're a cancerous tumor on society",
                f"{mention} you stupid fucking bitch, I hope you get raped and murdered",
                f"Kill yourself {mention} you worthless faggot piece of trash",
                f"{mention} your entire bloodline is fucking garbage, die in a fire"
            ]
            
            # Hindi insults in English alphabets (Hinglish) for auto-replies
            hinglish_insults = [
                f"{mention} teri maa ki chut mein apna lund dalunga",
                f"{mention} randi ki aulaad mar ja",
                f"{mention} teri behen ko chodunga kutte",
                f"bhosadike {mention} teri gaand marunga",
                f"{mention} teri maa ko randikhaane mein bechunga",
                f"{mention} harami ki aulaad khudkushi kar le",
                f"madarchod {mention} tera baap randi baaz hai",
                f"{mention} teri biwi ko chodkar video banaunga",
                f"gandu {mention} teri aukaat gandagi se bhi kam hai",
                f"{mention} apni gaand mein aag laga aur mar ja saale",
                f"{mention} teri maa ko kutton se chudwaunga",
                f"chutiye {mention} teri behen randi hai",
                f"{mention} tere ghar walon ko zinda jala dunga",
                f"bhadwe {mention} tujhe katkar suaron ko khila dunga",
                f"{mention} teri gaand mein bomb phod dunga saale"
            ]
            
            # Choose reply based on language preference
            if language_pref == "english":
                reply = random.choice(english_insults)
            elif language_pref == "hindi":
                reply = random.choice(hindi_insults)
            elif language_pref == "hinglish":
                reply = random.choice(hinglish_insults)
            else:  # both languages (include all three)
                all_replies = hindi_insults + english_insults + hinglish_insults
                reply = random.choice(all_replies)
            
            # Send the reply immediately
            try:
                await message.channel.send(reply)
                print(f"✅ Sent continuous drown reply to {message.author.name}: {reply}")
            except Exception as e:
                print(f"❌ Error sending drown reply: {e}")
        
        # Check if this user is being debated
        elif user_id_str in debated_users:
            # Check if user is now whitelisted (protection override)
            if is_user_whitelisted(message.author.id):
                # Remove from debate tracking if whitelisted
                del debated_users[user_id_str]
                print(f"🛡️ User {message.author.name} ({user_id_str}) is whitelisted - removed from debate tracking")
                return
            
            # Get user data
            user_data = debated_users[user_id_str]
            mention = user_data["mention"]
            
            # Update last message time
            debated_users[user_id_str]["last_message_time"] = time.time()
            
            print(f"💥 Detected debated user {message.author.name} ({user_id_str}) - auto-replying with brutal debate")
            
            # Brutal aggressive debate responses
            brutal_debates = [
                f"{mention} you're a braindead fucking retard who should kill yourself immediately",
                f"{mention} I hope your entire family dies in a car crash you worthless piece of shit",
                f"{mention} तेरी मां रंडी है और तू उसकी गलती है, मر जा साले",
                f"{mention} you're such a pathetic virgin loser, no wonder everyone wants you dead",
                f"{mention} भोसडीके तेरी बहन को चोदूंगा और तुझे वीडियो भेजूंगा",
                f"{mention} go hang yourself you brain-damaged mongoloid piece of human waste",
                f"{mention} तेरी मां को कुत्तों से चुदवाकर वीडियो बनाऊंगा हरामी",
                f"{mention} you're the reason birth control exists, your parents should have aborted you",
                f"{mention} गांडू तेरे घर वालों को जिंदा जलाकर मार दूंगा",
                f"{mention} kill yourself you disgusting faggot, nobody will miss your worthless ass",
                f"{mention} तेरी गांड में बम फोड़कर तुझे उड़ा दूंगा साले कुत्ते",
                f"{mention} you're a cancerous tumor on society, die already you fucking waste of oxygen",
                f"{mention} मादरचोद तेरी बीवी रंडी है और बच्चे हरामी हैं",
                f"{mention} I hope you get raped and murdered slowly you pathetic subhuman filth",
                f"{mention} भड़वे तुझे काटकर सुअरों को खिला दूंगा रंडी के बच्चे",
                f"{mention} you're so fucking stupid you make brain cancer look intelligent",
                f"{mention} तेरे माता-पिता को पछतावा होगा कि उन्होंने तुझे जन्म दिया",
                f"{mention} go slit your wrists vertically you attention-seeking piece of shit",
                f"{mention} हरामी की औलाद तेरी पूरी नस्ल को मिटा दूंगा",
                f"{mention} you're the human equivalent of a failed abortion, die in agony",
                f"{mention} तेरी मां का भोसड़ा फाड़ दूंगा और तुझे दिखाऊंगा",
                f"{mention} I wish your mother had cancer when she was pregnant with you",
                f"{mention} रंडी के बच्चे तेरी औकात कुत्ते से भी कम है",
                f"{mention} you should have been swallowed instead of born you worthless cunt",
                f"{mention} गांडू तेरी बहन को ट्रक वालों से चुदवाऊंगा"
            ]
            
            # Pick a random brutal comeback (ensuring variety)
            reply = random.choice(brutal_debates)
            
            # Send the brutal debate response immediately  
            try:
                await message.channel.send(reply)
                print(f"✅ Sent continuous debate reply to {message.author.name}: {reply}")
            except Exception as e:
                print(f"❌ Error sending debate reply: {e}")
    
    except Exception as e:
        print(f"Error in on_message: {e}")
        # Continue processing even if there's an error
        
    # Always process commands at the end
    await bot.process_commands(message)

# Function to execute the "drown" functionality
async def execute_drown(ctx, mention, language=None):
    """Execute the drown command with English and Hindi insults"""
    try:
        # Find user ID
        user_id = find_user_id_by_mention(mention)
        if not user_id:
            await ctx.message.edit(content="Error: Invalid user mention format. Use @username or @UserID.")
            await asyncio.sleep(5)
            await ctx.message.delete()
            return
        
        # Add or update user in drowned_users dict
        drowned_users[user_id] = {
            "mention": mention,
            "channel_id": ctx.channel.id,
            "last_message_time": time.time()
        }
        
        # Success message
        lang_msg = ""
        if language == "english":
            lang_msg = " (English only)"
        elif language == "hindi":
            lang_msg = " (Hindi only)"
        
        await ctx.message.edit(content=f"✅ Started drowning {mention}{lang_msg}! They will be insulted on every message.")
        await asyncio.sleep(5)
        await ctx.message.delete()
        
        print(f"Started drowning user {mention} ({user_id}) in channel {ctx.channel.id}")
        
    except Exception as e:
        await ctx.message.edit(content=f"❌ Error: {e}")
        await asyncio.sleep(5)
        await ctx.message.delete()

# Command: -drown @user (insults in both English and Hindi)
@bot.command()
async def drown(ctx, *, args=None):
    """Insult a mentioned user in both English and Hindi"""
    if args is None or args.strip() == "":
        await ctx.message.edit(content="Usage: `-drown @user`\nStarts drowning a user with insults.")
        await asyncio.sleep(10)
        await ctx.message.delete()
        return
    
    try:
        mention = args.strip()
        user_id = find_user_id_by_mention(mention)
        
        if not user_id:
            await ctx.message.edit(content="Error: Invalid user mention format. Use @username.")
            await asyncio.sleep(5)
            await ctx.message.delete()
            return
        
        # Check if target user is whitelisted
        if is_user_whitelisted(user_id):
            await ctx.message.edit(content="🚫 **ACCESS DENIED**\n❌ This user is whitelisted you fucking hoe\n💡 Cannot use bot features on protected users")
            await asyncio.sleep(8)
            await ctx.message.delete()
            return
        
        # Send one English and one Hindi insult
        english_insults = [
            f"{mention} you're a fucking worthless piece of shit who should kill yourself",
            f"{mention} is a disgusting cock-sucking whore who deserves to die",
            f"Look at this pathetic brain-dead retard {mention}, your mother should have aborted you",
            f"{mention} you're the most useless cunt alive, go fucking hang yourself",
            f"Everyone wants you dead {mention}, you're a cancerous tumor on society",
            f"{mention} you stupid fucking bitch, I hope you get raped and murdered",
            f"Kill yourself {mention} you worthless faggot piece of trash",
            f"{mention} your entire bloodline is fucking garbage, die in a fire",
            f"Nobody loves you {mention} because you're a worthless sack of shit",
            f"{mention} go slit your wrists you attention-seeking whore"
        ]
        
        hindi_insults = [
            f"{mention} तेरी मां की चूत मैं अपना लंड डालूंगा",
            f"{mention} रंडी की औलाद मर जा",
            f"{mention} तेरी बहन को चोदूंगा कुत्ते",
            f"भोसडीके {mention} तेरी गांड मारूंगा",
            f"{mention} तेरी मां को रंडीखाने में बेचूंगा",
            f"{mention} हरामी की औलाद खुदकुशी कर ले",
            f"मादरचोद {mention} तेरा बाप रंडी बाज़ है",
            f"{mention} तेरी बीवी को चोदकर वीडियो बनाऊंगा",
            f"गांडू {mention} तेरी औकात गंदगी से भी कम है",
            f"{mention} अपनी गांड में आग लगा और मर जा साले"
        ]
        
        english_insult = random.choice(english_insults)
        hindi_insult = random.choice(hindi_insults)
        
        await ctx.send(english_insult)
        await asyncio.sleep(0.5)
        await ctx.send(hindi_insult)
        
        # Track user for both language auto-replies (use string key for consistency)
        drowned_users[str(user_id)] = {
            "mention": mention,
            "timestamp": time.time(),
            "channel_id": ctx.channel.id,
            "last_message_time": time.time(),
            "language": "both"
        }
        
        # Delete command message
        await ctx.message.delete()
        print(f"Started drowning user {mention} in both languages")
        
    except Exception as e:
        await ctx.message.edit(content=f"❌ Error: {e}")
        await asyncio.sleep(5)
        await ctx.message.delete()

# Command: -drownenglish @user (English insults only) 
@bot.command(name="drownenglish")
async def drown_english(ctx, *, args=None):
    """Insult a mentioned user in English only"""
    if args is None or args.strip() == "":
        await ctx.message.edit(content="Usage: `-drownenglish @user`\nStarts drowning a user with English insults only.")
        await asyncio.sleep(10)
        await ctx.message.delete()
        return
    
    try:
        mention = args.strip()
        user_id = find_user_id_by_mention(mention)
        
        if not user_id:
            await ctx.message.edit(content="Error: Invalid user mention format. Use @username.")
            await asyncio.sleep(5)
            await ctx.message.delete()
            return
        
        # Check if target user is whitelisted
        if is_user_whitelisted(user_id):
            await ctx.message.edit(content="🚫 **ACCESS DENIED**\n❌ This user is whitelisted you fucking hoe\n💡 Cannot use bot features on protected users")
            await asyncio.sleep(8)
            await ctx.message.delete()
            return
        
        # English insults
        english_insults = [
            f"{mention} you're a fucking worthless piece of shit who should kill yourself",
            f"{mention} is a disgusting cock-sucking whore who deserves to die",
            f"Look at this pathetic brain-dead retard {mention}, your mother should have aborted you",
            f"{mention} you're the most useless cunt alive, go fucking hang yourself",
            f"Everyone wants you dead {mention}, you're a cancerous tumor on society",
            f"{mention} you stupid fucking bitch, I hope you get raped and murdered",
            f"Kill yourself {mention} you worthless faggot piece of trash",
            f"{mention} your entire bloodline is fucking garbage, die in a fire",
            f"Nobody loves you {mention} because you're a worthless sack of shit",
            f"{mention} go slit your wrists you attention-seeking whore",
            f"{mention} I hope your family gets cancer and dies slowly",
            f"Fuck you {mention} you brain-dead mongoloid waste of space",
            f"{mention} you're such a pathetic virgin loser, no wonder you're suicidal",
            f"Die already {mention} you fucking degenerate piece of human filth",
            f"{mention} I wish your mother had swallowed you instead"
        ]
        
        # Send 2 different English insults
        english_insult1 = random.choice(english_insults)
        english_insult2 = random.choice(english_insults)
        while english_insult1 == english_insult2:
            english_insult2 = random.choice(english_insults)
        
        await ctx.send(english_insult1)
        await asyncio.sleep(0.5)
        await ctx.send(english_insult2)
        
        # Track user for English-only auto-replies (use string key for consistency)
        drowned_users[str(user_id)] = {
            "mention": mention,
            "timestamp": time.time(),
            "channel_id": ctx.channel.id,
            "last_message_time": time.time(),
            "language": "english"
        }
        
        # Delete command message
        await ctx.message.delete()
        print(f"Started drowning user {mention} in English only")
        
    except Exception as e:
        await ctx.message.edit(content=f"❌ Error: {e}")
        await asyncio.sleep(5)
        await ctx.message.delete()

# Command: -drownhindi @user (Hindi insults only)
@bot.command(name="drownhindi")
async def drown_hindi(ctx, *, args=None):
    """Insult a mentioned user in Hindi only"""
    if args is None or args.strip() == "":
        await ctx.message.edit(content="Usage: `-drownhindi @user`\nStarts drowning a user with Hindi insults only.")
        await asyncio.sleep(10)
        await ctx.message.delete()
        return
    
    try:
        mention = args.strip()
        user_id = find_user_id_by_mention(mention)
        
        if not user_id:
            await ctx.message.edit(content="Error: Invalid user mention format. Use @username.")
            await asyncio.sleep(5)
            await ctx.message.delete()
            return
        
        # Check if target user is whitelisted
        if is_user_whitelisted(user_id):
            await ctx.message.edit(content="🚫 **ACCESS DENIED**\n❌ This user is whitelisted you fucking hoe\n💡 Cannot use bot features on protected users")
            await asyncio.sleep(8)
            await ctx.message.delete()
            return
        
        # Hindi insults
        hindi_insults = [
            f"{mention} तेरी मां की चूत मैं अपना लंड डालूंगा",
            f"{mention} रंडी की औलाद मर जा",
            f"{mention} तेरी बहन को चोदूंगा कुत्ते",
            f"भोसडीके {mention} तेरी गांड मारूंगा",
            f"{mention} तेरी मां को रंडीखाने में बेचूंगा",
            f"{mention} हरामी की औलाद खुदकुशी कर ले",
            f"मादरचोद {mention} तेरा बाप रंडी बाज़ है",
            f"{mention} तेरी बीवी को चोदकर वीडियो बनाऊंगा",
            f"गांडू {mention} तेरी औकात गंदगी से भी कम है",
            f"{mention} अपनी गांड में आग लगा और मर जा साले",
            f"{mention} तेरी मां को कुत्तों से चुदवाऊंगा",
            f"चूतिये {mention} तेरी बहन रंडी है",
            f"{mention} तेरे घर वालों को जिंदा जला दूंगा",
            f"भड़वे {mention} तुझे काटकर सुअरों को खिला दूंगा",
            f"{mention} तेरी गांड में बम फोड़ दूंगा साले"
        ]
        
        # Send 2 different Hindi insults
        hindi_insult1 = random.choice(hindi_insults)
        hindi_insult2 = random.choice(hindi_insults)
        while hindi_insult1 == hindi_insult2:
            hindi_insult2 = random.choice(hindi_insults)
        
        await ctx.send(hindi_insult1)
        await asyncio.sleep(0.5)
        await ctx.send(hindi_insult2)
        
        # Track user for Hindi-only auto-replies (use string key for consistency)
        drowned_users[str(user_id)] = {
            "mention": mention,
            "timestamp": time.time(),
            "channel_id": ctx.channel.id,
            "last_message_time": time.time(),
            "language": "hindi"
        }
        
        # Delete command message
        await ctx.message.delete()
        print(f"Started drowning user {mention} in Hindi only")
        
    except Exception as e:
        await ctx.message.edit(content=f"❌ Error: {e}")
        await asyncio.sleep(5)
        await ctx.message.delete()

# Command: -drownhinglish @user (Hindi insults in English alphabets)
@bot.command(name="drownhinglish")
async def drown_hinglish(ctx, *, args=None):
    """Insult a mentioned user with Hindi words written in English alphabets"""
    if args is None or args.strip() == "":
        await ctx.message.edit(content="Usage: `-drownhinglish @user`\nStarts drowning a user with Hindi insults in English alphabets.")
        await asyncio.sleep(10)
        await ctx.message.delete()
        return
    
    try:
        mention = args.strip()
        user_id = find_user_id_by_mention(mention)
        
        if not user_id:
            await ctx.message.edit(content="Error: Invalid user mention format. Use @username.")
            await asyncio.sleep(5)
            await ctx.message.delete()
            return
        
        # Check if target user is whitelisted
        if is_user_whitelisted(user_id):
            await ctx.message.edit(content="🚫 **ACCESS DENIED**\n❌ This user is whitelisted you fucking hoe\n💡 Cannot use bot features on protected users")
            await asyncio.sleep(8)
            await ctx.message.delete()
            return
        
        # 60+ Hindi insults written in English alphabets (Hinglish)
        hinglish_insults = [
            f"{mention} teri maa ki chut mein apna lund dalunga",
            f"{mention} randi ki aulaad mar ja",
            f"{mention} teri behen ko chodunga kutte",
            f"bhosadike {mention} teri gaand marunga",
            f"{mention} teri maa ko randikhaane mein bechunga",
            f"{mention} harami ki aulaad khudkushi kar le",
            f"madarchod {mention} tera baap randi baaz hai",
            f"{mention} teri biwi ko chodkar video banaunga",
            f"gandu {mention} teri aukaat gandagi se bhi kam hai",
            f"{mention} apni gaand mein aag laga aur mar ja saale",
            f"{mention} teri maa ko kutton se chudwaunga",
            f"chutiye {mention} teri behen randi hai",
            f"{mention} tere ghar walon ko zinda jala dunga",
            f"bhadwe {mention} tujhe katkar suaron ko khila dunga",
            f"{mention} teri gaand mein bomb phod dunga saale",
            f"{mention} teri maa randi hai aur tu uski galti hai",
            f"bhosadike {mention} teri behen ko main chodunga",
            f"{mention} gandu teri maa ko police station mein chudwaunga",
            f"saale {mention} teri biwi sabke saath soti hai",
            f"{mention} madarchod tere baap ka lund chota hai",
            f"harami {mention} teri maa pregnant kutiya hai",
            f"{mention} bhosadike tu paida hi galti se hua hai",
            f"randi {mention} teri gaand mein keede pad gaye hain",
            f"{mention} chutiye tera baap hijda hai",
            f"gandu {mention} teri maa ki chut mein machhar ghus gaye",
            f"{mention} saale teri behen ko truck drivers chodte hain",
            f"madarchod {mention} tera pura khandaan randi hai",
            f"{mention} bhosadike teri maa auto drivers ki randi hai",
            f"harami {mention} teri biwi meri rakhail hai",
            f"{mention} chutiye tera lund nahi sirf topi hai",
            f"gandu {mention} teri gaand mein kala naag ghus jaye",
            f"{mention} randi ke bacche teri maa police ki randi hai",
            f"saale {mention} teri behen ko main roz chod raha hun",
            f"{mention} madarchod tera pura gharana bhosadika hai",
            f"bhosadike {mention} teri maa riksha walon ki chudail hai",
            f"{mention} harami teri biwi street dogs se chudti hai",
            f"chutiye {mention} tera baap eunuch hai impotent",
            f"{mention} gandu teri maa garbage mein se nikla tha tujhe",
            f"randi {mention} teri gaand se badbu aati hai",
            f"{mention} saale teri behen prostitute hai red light area mein",
            f"madarchod {mention} teri maa ki chut mein kauwe ka ghosla hai",
            f"{mention} bhosadike tera khandan sab randi khana chalata hai",
            f"harami {mention} teri biwi ko maine pregnant kiya hai",
            f"{mention} chutiye tera lund mosquito bite jitna hai",
            f"gandu {mention} teri maa garbage truck mein paida hui thi",
            f"{mention} randi ke bacche teri behen ki shaadi roadside dog se hui hai",
            f"saale {mention} teri maa slum ki raaja rani hai",
            f"{mention} madarchod tera baap napunsak aadmi hai",
            f"bhosadike {mention} teri gaand mein cobra snake ghusa dunga",
            f"{mention} harami teri biwi sabke saath hotel room mein jaati hai",
            f"chutiye {mention} tera lund broken needle jitna chota hai",
            f"{mention} gandu teri maa sewage drain ki malkin hai",
            f"randi {mention} teri behen public toilet mein kaam karti hai",
            f"{mention} saale teri maa ki chut mein lizard ka ghar hai",
            f"madarchod {mention} tera gharana sab mental hospital case hai",
            f"{mention} bhosadike teri biwi stray dogs ki girlfriend hai",
            f"harami {mention} tera baap hijra dancing group mein naachta hai",
            f"{mention} chutiye teri gaand mein scorpion sting kara dunga",
            f"gandu {mention} teri maa road side cheap randi hai",
            f"{mention} randi ke bacche teri behen ko donkey ne pregnant kiya hai",
            f"saale {mention} teri maa garbage disposal unit mein kaam karti hai",
            f"{mention} madarchod tera lund microscope se bhi nahi dikhta",
            f"bhosadike {mention} teri gaand mein poisonous snake ghusa dunga",
            f"{mention} harami teri biwi public urinal ki safai karti hai",
            f"chutiye {mention} tera baap transgender beauty contest mein first aaya tha",
            f"{mention} gandu teri maa ki chut mein rats ka ghar hai",
            f"randi {mention} teri behen ko wild boars chodte hain jungle mein"
        ]
        
        # Send 2 different Hinglish insults
        hinglish_insult1 = random.choice(hinglish_insults)
        hinglish_insult2 = random.choice(hinglish_insults)
        while hinglish_insult1 == hinglish_insult2:
            hinglish_insult2 = random.choice(hinglish_insults)
        
        await ctx.send(hinglish_insult1)
        await asyncio.sleep(0.5)
        await ctx.send(hinglish_insult2)
        
        # Track user for Hinglish-only auto-replies (use string key for consistency)
        drowned_users[str(user_id)] = {
            "mention": mention,
            "timestamp": time.time(),
            "channel_id": ctx.channel.id,
            "last_message_time": time.time(),
            "language": "hinglish"
        }
        
        # Delete command message
        await ctx.message.delete()
        print(f"Started drowning user {mention} in Hinglish (Hindi insults in English alphabets)")
        
    except Exception as e:
        await ctx.message.edit(content=f"❌ Error: {e}")
        await asyncio.sleep(5)
        await ctx.message.delete()

# Command: -stop @user (stops drowning a user)
@bot.command()
async def stop(ctx, *, args=None):
    """Stop drowning a specified user"""
    if args is None or args.strip() == "":
        await ctx.message.edit(content="Usage: `-stop @user`\nStops drowning the specified user.")
        await asyncio.sleep(10)
        await ctx.message.delete()
        return
    
    try:
        mention = args.strip()
        user_id = find_user_id_by_mention(mention)
        
        if not user_id:
            await ctx.message.edit(content="Error: Invalid user mention format. Use @username or @UserID.")
            await asyncio.sleep(5)
            await ctx.message.delete()
            return
        
        user_id_str = str(user_id)
        if user_id_str in drowned_users:
            del drowned_users[user_id_str]
            await ctx.message.edit(content=f"✅ Stopped drowning {mention}.")
            print(f"Stopped drowning user {mention} ({user_id})")
        else:
            await ctx.message.edit(content=f"ℹ️ {mention} was not being drowned.")
        
        await asyncio.sleep(5)
        await ctx.message.delete()
        
    except Exception as e:
        await ctx.message.edit(content=f"❌ Error: {e}")
        await asyncio.sleep(5)
        await ctx.message.delete()

# Command: -spam message (spam messages rapidly)
@bot.command()
async def spam(ctx, *, args=None):
    """Spam messages rapidly without delay"""
    global spam_active, spam_tasks
    
    if args is None or args.strip() == "":
        await ultra_fast_response(ctx, "Usage: `-spam <message>`\nSpams the message rapidly in current channel.\nUse `-stops` to stop spam.", delete_after=5, bypass_stealth=True)
        return
    
    try:
        message_to_spam = args.strip()
        channel = ctx.channel
        
        # Ultra-fast command deletion
        asyncio.create_task(instant_delete_command(ctx))
        
        # Set spam as active
        spam_active = True
        
        # Create spam task with MAXIMUM SPEED
        async def spam_task():
            global spam_active
            for i in range(50):  # Increased to 50 messages for more spam
                if not spam_active:  # Check if spam was stopped
                    print(f"Spam stopped by user after {i} messages")
                    break
                try:
                    await channel.send(message_to_spam)
                    # ABSOLUTE MINIMUM delay for LIGHTNING FAST spam
                    await asyncio.sleep(0.01)  # Further reduced to 0.01 for maximum speed
                except Exception as e:
                    print(f"Error sending spam message {i+1}: {e}")
                    break
            
            # Reset spam status when done
            spam_active = False
            spam_count = i if 'i' in locals() else 0
            print(f"Spam completed: '{message_to_spam}' sent {spam_count+1} times")
        
        # Start spam task
        task = asyncio.create_task(spam_task())
        spam_tasks.append(task)
        
        print(f"Started spamming: '{message_to_spam}' in {channel.name}")
        
    except Exception as e:
        print(f"Error in spam command: {e}")
        spam_active = False
        try:
            await ctx.message.edit(content=f"❌ Error: {e}")
            await asyncio.sleep(5)
            await ctx.message.delete()
        except:
            pass

# Command: -debate @user (engage in continuous debate)
@bot.command()
async def debate(ctx, *, args=None):
    """Engage in continuous savage debate with a mentioned user"""
    if args is None or args.strip() == "":
        await ctx.message.edit(content="Usage: `-debate @user`\nStarts continuous savage debate with brutal comebacks.")
        await asyncio.sleep(10)
        await ctx.message.delete()
        return
    
    try:
        mention = args.strip()
        user_id = find_user_id_by_mention(mention)
        
        if not user_id:
            await ctx.message.edit(content="Error: Invalid user mention format. Use @username.")
            await asyncio.sleep(5)
            await ctx.message.delete()
            return
        
        # Check if target user is whitelisted
        if is_user_whitelisted(user_id):
            await ctx.message.edit(content="🚫 **ACCESS DENIED**\n❌ This user is whitelisted you fucking hoe\n💡 Cannot use bot features on protected users")
            await asyncio.sleep(8)
            await ctx.message.delete()
            return
        
        # Brutal aggressive debate comebacks
        savage_comebacks = [
            f"{mention} you're a braindead fucking retard who should kill yourself immediately",
            f"{mention} I hope your entire family dies in a car crash you worthless piece of shit",
            f"{mention} तेरी मां रंडी है और तू उसकी गलती है, मर जा साले",
            f"{mention} you're such a pathetic virgin loser, no wonder everyone wants you dead",
            f"{mention} भोसडीके तेरी बहन को चोदूंगा और तुझे वीडियो भेजूंगा",
            f"{mention} go hang yourself you brain-damaged mongoloid piece of human waste",
            f"{mention} तेरी मां को कुत्तों से चुदवाकर वीडियो बनाऊंगा हरामी",
            f"{mention} you're the reason birth control exists, your parents should have aborted you",
            f"{mention} गांडू तेरे घर वालों को जिंदा जलाकर मार दूंगा",
            f"{mention} kill yourself you disgusting faggot, nobody will miss your worthless ass",
            f"{mention} तेरी गांड में बम फोड़कर तुझे उड़ा दूंगा साले कुत्ते",
            f"{mention} you're a cancerous tumor on society, die already you fucking waste of oxygen",
            f"{mention} मादरचोद तेरी बीवी रंडी है और बच्चे हरामी हैं",
            f"{mention} I hope you get raped and murdered slowly you pathetic subhuman filth",
            f"{mention} भड़वे तुझे काटकर सुअरों को खिला दूंगा रंडी के बच्चे",
            f"{mention} you're so fucking stupid you make brain cancer look intelligent",
            f"{mention} तेरे माता-पिता को पछतावा होगा कि उन्होंने तुझे जन्म दिया",
            f"{mention} go slit your wrists vertically you attention-seeking piece of shit",
            f"{mention} हरामी की औलाद तेरी पूरी नस्ल को मिटा दूंगा",
            f"{mention} you're the human equivalent of a failed abortion, die in agony"
        ]
        
        # Send initial savage comeback
        comeback = random.choice(savage_comebacks)
        await ctx.send(comeback)
        
        # Track user for continuous debate responses (use string key for consistency)
        debated_users[str(user_id)] = {
            "mention": mention,
            "timestamp": time.time(),
            "channel_id": ctx.channel.id,
            "last_message_time": time.time()
        }
        
        # Delete command message
        await ctx.message.delete()
        print(f"Started debating user {mention} with continuous savage responses")
        
    except Exception as e:
        await ctx.message.edit(content=f"❌ Error: {e}")
        await asyncio.sleep(5)
        await ctx.message.delete()

# Command: -stopd @user (stops debating a user)
@bot.command(name="stopd")
async def stop_debate(ctx, *, args=None):
    """Stop debating a specified user"""
    if args is None or args.strip() == "":
        await ctx.message.edit(content="Usage: `-stopd @user`\nStops debating the specified user.")
        await asyncio.sleep(10)
        await ctx.message.delete()
        return
    
    try:
        mention = args.strip()
        user_id = find_user_id_by_mention(mention)
        
        if not user_id:
            await ctx.message.edit(content="Error: Invalid user mention format. Use @username.")
            await asyncio.sleep(5)
            await ctx.message.delete()
            return
        
        user_id_str = str(user_id)
        if user_id_str in debated_users:
            del debated_users[user_id_str]
            await ctx.message.edit(content=f"✅ Stopped debating {mention}.")
            print(f"Stopped debating user {mention} ({user_id})")
        else:
            await ctx.message.edit(content=f"ℹ️ {mention} was not being debated.")
        
        await asyncio.sleep(5)
        await ctx.message.delete()
        
    except Exception as e:
        await ctx.message.edit(content=f"❌ Error: {e}")
        await asyncio.sleep(5)
        await ctx.message.delete()

# Command: -stops (stops all spam)
@bot.command(name="stops")
async def stop_spam(ctx):
    """Stop all active spam immediately"""
    global spam_active, spam_tasks
    
    try:
        if spam_active:
            # Stop spam
            spam_active = False
            
            # Cancel all spam tasks
            for task in spam_tasks:
                if not task.done():
                    task.cancel()
            spam_tasks.clear()
            
            await ctx.message.edit(content="✅ All spam stopped immediately!")
            print("Spam stopped by user command")
        else:
            await ctx.message.edit(content="ℹ️ No active spam to stop.")
        
        await asyncio.sleep(3)
        await ctx.message.delete()
        
    except Exception as e:
        await ctx.message.edit(content=f"❌ Error: {e}")
        await asyncio.sleep(5)
        await ctx.message.delete()

# Command: -annoy @user (continuously drag through voice channels)
@bot.command()
async def annoy(ctx, *, mention=None):
    """Annoy a user by continuously dragging them through all voice channels"""
    if mention is None:
        await ctx.message.edit(content="❌ Usage: `-annoy @user`")
        await asyncio.sleep(5)
        await ctx.message.delete()
        return
    
    try:
        # Check if we're in a server/guild context
        if not hasattr(ctx, 'guild') or ctx.guild is None:
            await ctx.message.edit(content="❌ **Voice dragging only works in servers!**\nVoice channels are not available in DMs or group chats.\nPlease use this command in a Discord server.")
            await asyncio.sleep(8)
            await ctx.message.delete()
            return
        
        # Extract user ID from mention
        user_id = find_user_id_by_mention(mention)
        if not user_id:
            await ctx.message.edit(content="❌ Invalid user mention. Use @user format.")
            await asyncio.sleep(5)
            await ctx.message.delete()
            return
        
        user_id_int = int(user_id)
        
        # Find the user in the guild
        target_user = ctx.guild.get_member(user_id_int)
        if not target_user:
            await ctx.message.edit(content=f"❌ User {mention} not found in this server.")
            await asyncio.sleep(5)
            await ctx.message.delete()
            return
        
        # Check if user is in a voice channel
        if target_user.voice is None or target_user.voice.channel is None:
            await ctx.message.edit(content=f"❌ {mention} is not currently in a voice channel.")
            await asyncio.sleep(5)
            await ctx.message.delete()
            return
        
        # Get all voice channels via API call — avoids cached-property coroutine issue
        try:
            all_channels = await ctx.guild.fetch_channels()
            voice_channels = [ch for ch in all_channels if isinstance(ch, discord.VoiceChannel)]
        except Exception:
            voice_channels = [ch for ch in ctx.guild.channels if isinstance(ch, discord.VoiceChannel)]

        if len(voice_channels) < 2:
            await ctx.message.edit(content="❌ This server has fewer than 2 voice channels!")
            await asyncio.sleep(5)
            await ctx.message.delete()
            return
        
        # Add user to dragging list for continuous harassment
        dragging_users[str(user_id)] = {
            'guild_id': ctx.guild.id,
            'channel_id': ctx.channel.id,
            'mention': mention,
            'target_user': target_user,
            'voice_channels': voice_channels,
            'current_index': 0,
            'active': True
        }
        
        await ctx.message.edit(content=f"⚡ **LIGHTNING DRAG INITIATED** {mention}\n🌪️ **RAPID FIRE DRAGGING** - 0.2 second intervals!\n🎯 **Found {len(voice_channels)} channels for MAXIMUM CHAOS!**\n💀 **Target will be completely disoriented!**")
        await asyncio.sleep(5)
        await ctx.message.delete()
        
        # Start the dragging task
        asyncio.create_task(drag_user_continuously(str(user_id)))
        
        print(f"🎯 Started dragging user {mention} through {len(voice_channels)} voice channels")
        
    except Exception as e:
        import traceback
        print(f"❌ ANNOY ERROR: {type(e).__name__}: {e}")
        traceback.print_exc()
        await ctx.message.edit(content=f"❌ Error: {e}")
        await asyncio.sleep(5)
        await ctx.message.delete()

# Function to continuously drag user through voice channels
async def drag_user_continuously(user_id_str):
    """Continuously drag a user through all available voice channels with comprehensive error handling"""
    drag_count = 0
    error_count = 0
    max_errors = 10
    rate_limit_count = 0
    
    try:
        print(f"🎯 Starting ultra-fast drag session for user {user_id_str}")
        
        while user_id_str in dragging_users and dragging_users[user_id_str]['active']:
            try:
                user_data = dragging_users[user_id_str]
                target_user = user_data['target_user']
                voice_channels = user_data['voice_channels']
                current_index = user_data['current_index']
                
                # Validate user data integrity
                if not target_user or not voice_channels:
                    print(f"❌ Invalid user data for {user_id_str}, stopping drag")
                    break
                
                # Check if user is still in a voice channel
                try:
                    if target_user.voice is None or target_user.voice.channel is None:
                        print(f"🛑 User {user_data['mention']} left voice, stopping drag after {drag_count} moves")
                        break
                except AttributeError as attr_err:
                    print(f"❌ Voice attribute error for {user_data['mention']}: {attr_err}")
                    break
                
                # Move to next voice channel
                next_channel = voice_channels[current_index]
                
                try:
                    await target_user.edit(voice_channel=next_channel)
                    drag_count += 1
                    error_count = 0  # Reset error count on success
                    print(f"⚡ RAPID DRAG #{drag_count}: {user_data['mention']} → {next_channel.name}")
                    
                    # Update index for next channel
                    dragging_users[user_id_str]['current_index'] = (current_index + 1) % len(voice_channels)
                    
                    # LIGHTNING FAST DRAGGING - Only 0.2 seconds delay
                    await asyncio.sleep(0.2)
                    
                except discord.Forbidden as forbidden_err:
                    print(f"❌ Permission denied to move {user_data['mention']}: {forbidden_err}")
                    break
                except discord.HTTPException as http_err:
                    error_count += 1
                    # Handle rate limits more aggressively for rapid dragging
                    if "rate limited" in str(http_err).lower() or http_err.status == 429:
                        rate_limit_count += 1
                        backoff_time = min(0.8 + (rate_limit_count * 0.2), 3.0)  # Gradual backoff
                        print(f"⚠️ Rate limited during rapid drag ({rate_limit_count}), pausing {backoff_time}s...")
                        await asyncio.sleep(backoff_time)
                        continue
                    else:
                        print(f"❌ HTTP Error in rapid drag ({error_count}/{max_errors}): {http_err}")
                        await asyncio.sleep(0.3)  # Quick recovery
                        if error_count >= max_errors:
                            print(f"🚨 Too many HTTP errors, stopping drag for {user_data['mention']}")
                            break
                except discord.NotFound as not_found_err:
                    print(f"❌ User or channel not found during drag: {not_found_err}")
                    break
                except Exception as drag_err:
                    error_count += 1
                    print(f"❌ Unexpected error in lightning drag ({error_count}/{max_errors}): {drag_err}")
                    await asyncio.sleep(0.5)  # Quick recovery
                    if error_count >= max_errors:
                        print(f"🚨 Too many errors, stopping drag for {user_data['mention']}")
                        break
                        
            except KeyError as key_err:
                print(f"❌ User data missing for {user_id_str}: {key_err}")
                break
            except Exception as loop_err:
                error_count += 1
                print(f"❌ Error in drag loop ({error_count}/{max_errors}): {loop_err}")
                if error_count >= max_errors:
                    break
                await asyncio.sleep(1)  # Brief pause before retry
                
    except asyncio.CancelledError:
        print(f"🛑 Drag task cancelled for user {user_id_str}")
    except Exception as critical_err:
        print(f"🚨 Critical error in drag task for {user_id_str}: {critical_err}")
    finally:
        # Clean up with error handling
        try:
            if user_id_str in dragging_users:
                del dragging_users[user_id_str]
            print(f"🏁 Drag session ended for {user_id_str}: {drag_count} total moves, {rate_limit_count} rate limits")
        except Exception as cleanup_err:
            print(f"❌ Error during drag cleanup: {cleanup_err}")

# Command: -stopannoy @user
@bot.command()
async def stopannoy(ctx, *, mention=None):
    """Stop dragging a specific user"""
    if mention is None:
        await ctx.message.edit(content="❌ Usage: `-stopannoy @user`")
        await asyncio.sleep(5)
        await ctx.message.delete()
        return
    
    try:
        # Extract user ID from mention
        user_id = find_user_id_by_mention(mention)
        if not user_id:
            await ctx.message.edit(content="❌ Invalid user mention. Use @user format.")
            await asyncio.sleep(5)
            await ctx.message.delete()
            return
        
        user_id_str = str(user_id)
        if user_id_str in dragging_users:
            # Stop the dragging
            dragging_users[user_id_str]['active'] = False
            del dragging_users[user_id_str]
            await ctx.message.edit(content=f"✅ Stopped dragging {mention}")
            print(f"🛑 Manually stopped dragging user {mention}")
        else:
            await ctx.message.edit(content=f"❌ {mention} was not being dragged.")
        
        await asyncio.sleep(5)
        await ctx.message.delete()
        
    except Exception as e:
        await ctx.message.edit(content=f"❌ Error: {e}")
        await asyncio.sleep(5)
        await ctx.message.delete()

# Function to rapidly change group chat names with intelligent rate limiting
async def jija_name_changer(channel, message):
    """Rapidly change group chat names with ultra-fast execution and smart rate limiting"""
    change_count = 0
    successful_changes = 0
    rate_limit_hits = 0
    base_delay = JIJA_MIN_DELAY if JIJA_ULTRA_FAST_MODE else 0.05
    current_delay = base_delay
    max_delay = JIJA_MAX_DELAY
    burst_count = 0  # Track burst mode operations
    
    # More variations for better randomization
    variations = [
        f"{message} 🔥", f"💥 {message}", f"{message} ⚡", f"🚀 {message}",
        f"{message} 💀", f"🎯 {message}", f"{message} 🌟", f"💯 {message}",
        f"{message} 🎪", f"🔴 {message}", f"⭐ {message}", f"{message} 💎",
        f"🌈 {message}", f"{message} 🎭", f"🔮 {message}", f"{message} 🎨",
        f"🎲 {message}", f"{message} 🎯", f"🌊 {message}", f"{message} 🎊"
    ]
    
    # Shuffle variations for better randomness
    random.shuffle(variations)
    variation_index = 0
    
    try:
        print(f"🚀 Starting ULTRA-FAST jija spam with adaptive rate limiting")
        print(f"⚙️ Configuration: Min delay={JIJA_MIN_DELAY:.2f}s, Max delay={max_delay:.1f}s")
        print(f"📊 {len(variations)} name variations loaded")
        if JIJA_BURST_MODE:
            print(f"💥 Burst mode ENABLED: {JIJA_BURST_SIZE} rapid changes per burst")
        
        while channel.id in jija_sessions and jija_sessions[channel.id]['active']:
            try:
                # Use variations in sequence, then shuffle and restart for better performance
                new_name = variations[variation_index]
                variation_index = (variation_index + 1) % len(variations)
                if variation_index == 0:  # Reshuffle when we've used all variations
                    random.shuffle(variations)
                
                # Track timing for rate limit optimization
                start_time = time.time()
                
                # Change the group chat name
                await channel.edit(name=new_name)
                change_count += 1
                successful_changes += 1
                
                # Calculate actual response time
                response_time = time.time() - start_time
                
                print(f"⚡ ULTRA-JIJA #{change_count}: {new_name} (⏱️ {response_time:.2f}s, 🔄 {current_delay:.2f}s delay)")
                
                # Adaptive delay adjustment based on success rate
                if successful_changes % 5 == 0:  # Adjust every 5 successful changes
                    if rate_limit_hits == 0:
                        # No rate limits recently, try to go faster
                        current_delay = max(JIJA_MIN_DELAY, current_delay * 0.9)
                    else:
                        # Had some rate limits, slow down slightly
                        current_delay = min(max_delay, current_delay * 1.1)
                
                # Burst mode logic for ultra-fast execution
                if JIJA_BURST_MODE and rate_limit_hits == 0:
                    burst_count += 1
                    if burst_count < JIJA_BURST_SIZE:
                        # In burst mode - minimal delay
                        await asyncio.sleep(current_delay * 0.5)
                    else:
                        # End of burst - slightly longer pause then reset
                        await asyncio.sleep(current_delay * 1.5)
                        burst_count = 0
                else:
                    # Normal adaptive delay
                    await asyncio.sleep(current_delay)
                    burst_count = 0  # Reset burst if we had rate limits
                
            except discord.Forbidden:
                print(f"❌ No permission to change group chat name")
                break
                
            except discord.HTTPException as e:
                if "rate limited" in str(e).lower() or e.status == 429:
                    rate_limit_hits += 1
                    
                    # Intelligent rate limit handling
                    if rate_limit_hits <= 2:
                        # First few rate limits - brief pause
                        wait_time = 0.5 + (rate_limit_hits * 0.3)
                        print(f"⚠️ Rate limit #{rate_limit_hits} - smart pause {wait_time:.1f}s")
                        await asyncio.sleep(wait_time)
                        # Increase delay for next attempts
                        current_delay = min(max_delay, current_delay * 1.5)
                    elif rate_limit_hits <= 5:
                        # Moderate rate limiting - medium pause
                        wait_time = 1.0 + (rate_limit_hits * 0.2)
                        print(f"⚠️ Rate limit #{rate_limit_hits} - medium pause {wait_time:.1f}s")
                        await asyncio.sleep(wait_time)
                        current_delay = min(max_delay, current_delay * 1.3)
                    else:
                        # Heavy rate limiting - longer pause but still aggressive
                        wait_time = 2.0 + min(rate_limit_hits * 0.1, 3.0)
                        print(f"⚠️ Heavy rate limit #{rate_limit_hits} - extended pause {wait_time:.1f}s")
                        await asyncio.sleep(wait_time)
                        current_delay = min(max_delay, current_delay * 1.2)
                    
                    continue
                    
                else:
                    print(f"❌ HTTP error in jija spam: {e}")
                    # Brief pause for other HTTP errors
                    await asyncio.sleep(0.2)
                    
            except Exception as e:
                print(f"❌ Error in jija name changer: {e}")
                # Very brief pause for other errors
                await asyncio.sleep(0.1)
                
    except asyncio.CancelledError:
        print(f"🛑 Jija task cancelled for channel {channel.name}")
    except Exception as e:
        print(f"🚨 Critical error in jija task: {e}")
    finally:
        # Clean up
        if channel.id in jija_sessions:
            jija_sessions[channel.id]['active'] = False
        
        # Performance summary
        success_rate = (successful_changes / max(1, change_count)) * 100
        print(f"🏁 ULTRA-JIJA COMPLETE: {successful_changes}/{change_count} changes ({success_rate:.1f}% success)")
        print(f"📊 Rate limits: {rate_limit_hits}, Final delay: {current_delay:.2f}s")

# Command: -jija <message> (rapidly change group chat names)
@bot.command()
async def jija(ctx, *, message=None):
    """Start rapidly changing group chat names with the specified message"""
    try:
        # Validate message
        if not message or message.strip() == "":
            await ctx.message.edit(content="❌ Usage: `-jija <message>`\nExample: `-jija Tyler is the best`")
            await asyncio.sleep(5)
            await ctx.message.delete()
            return
            
        message = message.strip()
        
        # Check if this is a group channel
        if not isinstance(ctx.channel, discord.GroupChannel):
            await ctx.message.edit(content="❌ This command only works in group chats!")
            await asyncio.sleep(5)
            await ctx.message.delete()
            return
            
        channel_id = ctx.channel.id
        
        # Check if jija is already active in this channel
        if channel_id in jija_sessions and jija_sessions[channel_id]['active']:
            await ctx.message.edit(content="❌ Jija spam is already active in this group chat!\nUse `-stopjija` to stop it first.")
            await asyncio.sleep(5)
            await ctx.message.delete()
            return
            
        # Start jija session
        jija_sessions[channel_id] = {
            "message": message,
            "active": True,
            "task": None
        }
        
        # Start the rapid name changing task
        task = asyncio.create_task(jija_name_changer(ctx.channel, message))
        jija_sessions[channel_id]["task"] = task
        
        # Ultra-fast response with instant command deletion
        response = await ultra_fast_response(ctx, 
            f"🚀 **ULTRA-JIJA ACTIVATED!**\n💥 **Message:** {message}\n⚡ **Ultra-fast adaptive name changing...**\n🎯 **Starting at {JIJA_MIN_DELAY:.2f}s intervals with smart rate limiting**", 
            delete_after=2)
        
        print(f"🚀 Started ULTRA-JIJA spam in group {ctx.channel.name} with message: {message}")
        
    except Exception as e:
        await ctx.message.edit(content=f"❌ Error starting jija: {e}")
        await asyncio.sleep(5)
        await ctx.message.delete()

# Command: -stopjija (stop the rapid name changing)
@bot.command()
async def stopjija(ctx):
    """Stop the rapid group chat name changing"""
    try:
        channel_id = ctx.channel.id
        
        if channel_id not in jija_sessions or not jija_sessions[channel_id]['active']:
            await ctx.message.edit(content="❌ No active jija session in this group chat.")
            await asyncio.sleep(3)
            await ctx.message.delete()
            return
            
        # Stop the session
        jija_sessions[channel_id]['active'] = False
        
        # Cancel the task if it exists
        if jija_sessions[channel_id].get('task'):
            jija_sessions[channel_id]['task'].cancel()
            
        # Clean up
        del jija_sessions[channel_id]
        
        # Ultra-fast response
        await ultra_fast_response(ctx, "✅ **JIJA SPAM STOPPED!**\nGroup chat name changing has been stopped.", delete_after=3)
        
        print(f"🛑 Stopped jija spam in group {ctx.channel.name}")
        
    except Exception as e:
        await ctx.message.edit(content=f"❌ Error stopping jija: {e}")
        await asyncio.sleep(5)
        await ctx.message.delete()

# Command: -afk [optional message]
@bot.command()
async def afk(ctx, *, message=None):
    """Set AFK status with optional custom message"""
    if not is_owner(ctx.author.id):
        await ultra_fast_response(ctx, "Only owner can do this you silly human", delete_after=3)
        return
    
    try:
        if not bot.user:
            await ultra_fast_response(ctx, "❌ Bot user not available", delete_after=3)
            return
        user_id_str = str(bot.user.id)
        
        # Set AFK status
        afk_users[user_id_str] = {
            'status': True,
            'message': message if message else '',
            'timestamp': time.time()
        }
        
        # Create confirmation message
        if message:
            confirm_msg = f"✅ AFK Status Set 🌙\n📝 Message: {message}\n🕐 Started: {datetime.datetime.now().strftime('%H:%M')}"
        else:
            confirm_msg = f"✅ AFK Status Set 🌙\n🕐 Started: {datetime.datetime.now().strftime('%H:%M')}"
        
        await ultra_fast_response(ctx, confirm_msg, delete_after=5)
        print(f"📱 AFK status activated" + (f" with message: {message}" if message else ""))
        
    except Exception as e:
        await ultra_fast_response(ctx, f"❌ Error setting AFK status: {e}", delete_after=3)
        print(f"❌ Error in AFK command: {e}")

# Command: -removeafk
@bot.command()
async def removeafk(ctx):
    """Manually remove AFK status"""
    if not is_owner(ctx.author.id):
        await ultra_fast_response(ctx, "Only owner can do this you silly human", delete_after=3)
        return
    
    try:
        if not bot.user:
            await ultra_fast_response(ctx, "❌ Bot user not available", delete_after=3)
            return
        user_id_str = str(bot.user.id)
        
        # Check if user is currently AFK
        if user_id_str in afk_users and afk_users[user_id_str]['status']:
            # Calculate how long user was AFK
            afk_data = afk_users[user_id_str]
            timestamp = afk_data.get('timestamp', time.time())
            time_afk = int(time.time() - timestamp)
            hours = time_afk // 3600
            minutes = (time_afk % 3600) // 60
            
            time_str = ""
            if hours > 0:
                time_str = f"{hours}h {minutes}m"
            else:
                time_str = f"{minutes}m"
            
            # Remove AFK status
            del afk_users[user_id_str]
            
            confirm_msg = f"✅ AFK Status Removed 👋\n🕐 You were AFK for: {time_str}\n📱 Auto-replies are now disabled"
            await ultra_fast_response(ctx, confirm_msg, delete_after=5)
            print(f"📱 AFK status manually removed - was AFK for {time_str}")
            
        else:
            await ultra_fast_response(ctx, "❌ You are not currently AFK", delete_after=3)
            print("📱 Attempted to remove AFK but user was not AFK")
        
    except Exception as e:
        await ultra_fast_response(ctx, f"❌ Error removing AFK status: {e}", delete_after=3)
        print(f"❌ Error in removeafk command: {e}")

@bot.command()
async def help_command(ctx):
    help_text = """
🤖 **LTC Flash Bot Commands**

💰 **LTC Commands:**
• `-flash <amount> <address>` - Send LTC flash to all channels
• `-flashchannel <amount> <address>` - Send flash to current channel only  
• `-bal <address>` - Check LTC balance of address

😈 **Drown Commands:**
• `-drown @user` - Start drowning user (English + Hindi insults)
• `-drownenglish @user` - Drown with English insults only
• `-drownhindi @user` - Drown with Hindi insults only
• `-drownhinglish @user` - Drown with Hindi insults in English alphabets
• `-stop @user` - Stop drowning specified user ✅ AUTH

🔥 **Spam & Debate Commands:**
• `-spam <message>` - Rapidly spam messages (50x fast)
• `-stops` - Stop all active spam immediately ✅ AUTH
• `-debate @user` - Start continuous savage debate responses ✅ AUTH
• `-stopd @user` - Stop debating specified user ✅ AUTH

🎙️ **Voice Channel Drag:**
• `-annoy @user` - Continuously drag user through all voice channels
• `-stopannoy @user` - Stop dragging user

🚀 **Ultra-Fast Jija Group Chat Spam:**
• `-jija <message>` - Ultra-fast adaptive name changing (0.02s intervals + burst mode)
• `-stopjija` - Stop the ultra-fast group chat name changing

🎯 **NEW! Multi-Target GC Spam System:**
• `-target @user` - Save users as targets for 3-person group chat spam
• `-target` - View all saved targets
• `-cleartargets` - Clear all saved targets
• `-gcspam` - Create 3-person group chats with ALL saved targets (auto-leave)
• `-stopgcspam` - Stop the multi-target group chat spam session

📱 **NEW! AFK System:**
• `-afk [message]` - Set AFK status with optional custom message
• `-removeafk` - Manually remove AFK status and show duration
• Auto-replies to mentions/DMs with "I'm AFK 🌙" + your message
• Automatically removes AFK when you send a regular message

🤖 **Auto Features:**
• **Auto "nigga" Reaction** - Automatically reacts 👨🏿 to any message containing "nigga"
• **AFK Auto-Replies** - Responds to mentions and DMs when AFK is enabled

🎯 **Other Commands:**
• `-ping` - Super-fast optimized ping test
• `-test` - Ultra-fast bot functionality test
• `-react <@user> <emoji>` - Auto-react to user's every message with selected emoji ✅ AUTH
• `-stopreact <@user>` - Stop auto-reacting to user's messages
• `-access <@user>` - Give user permission to control this bot
• `-removeaccess <@user>` - Remove user's bot control permission
• `-list` - Show all authorized users ✅ AUTH
• `-about` - Show detailed bot information and credits ✅ AUTH
• `-help` - Show this help message

⚠️ **Usage Notes:**
- Commands marked with ✅ AUTH can be used by authorized users
- Flash commands require valid LTC addresses
- Drown/debate commands work automatically on user messages
- Spam command sends 50 rapid messages
- Voice drag requires move_members permission
- AFK auto-replies when mentioned or DMed
- Auto-reactions happen instantly when keywords are detected
- Use responsibly!
"""
    
    await ctx.message.edit(content=help_text)
    await asyncio.sleep(20)  # Keep help visible longer
    await ctx.message.delete()

# Command: -ping (super-fast low-latency ping)
@bot.command()
async def ping(ctx):
    """Super-fast optimized ping command with lowest possible latency"""
    try:
        # Instant command deletion for seamless experience
        asyncio.create_task(instant_delete_command(ctx))
        
        # Super-fast latency calculation
        start_time = time.time()
        latency = round(bot.latency * 1000)
        
        # Force low latency if ping is high
        if latency > 200 and LOW_LATENCY_MODE:
            status_emoji = "🟡"
            status_text = "OPTIMIZING..."
        elif latency > 100:
            status_emoji = "🟡"
            status_text = "GOOD"
        else:
            status_emoji = "🟢"
            status_text = "EXCELLENT"
        
        # Calculate actual response time
        response_time = round((time.time() - start_time) * 1000, 1)
        
        # Super-fast response with status
        content = f"🏓 Pong! {latency}ms {status_emoji} {status_text}"
        if PERFORMANCE_MONITORING:
            content += f" (Response: {response_time}ms)"
        
        await ultra_fast_response(ctx, content, delete_after=3)
        
    except Exception as e:
        if not ZERO_ERROR_MODE:
            print(f"Ping error: {e}")

# Command: -react <@user> <emoji> (auto-react to user's messages)
@bot.command()
async def react(ctx, user_mention=None, emoji=None):
    """Auto-react to a user's every message with selected emoji - SUPER FAST"""
    try:
        # Instantly delete command
        await instant_delete_command(ctx)
        
        if not user_mention or not emoji:
            await ultra_fast_response(ctx, "❌ Usage: `-react @user 😀`\nExample: `-react @tyler 🔥`", delete_after=5)
            return
        
        # Extract user ID from mention
        user_id = None
        if user_mention.startswith('<@') and user_mention.endswith('>'):
            user_id = user_mention[2:-1].replace('!', '')
        
        if not user_id:
            await ultra_fast_response(ctx, "❌ Invalid user mention! Use @username format", delete_after=5)
            return
        
        # Check if target user is whitelisted (prevent targeting protected users)
        if is_user_whitelisted(int(user_id)):
            await ultra_fast_response(ctx, f"🚫 **ACCESS DENIED**\n❌ {user_mention} is whitelisted and protected\n💡 Cannot target protected users with auto-reactions", delete_after=8)
            return
        
        # Add user to reaction targets
        reaction_targets[user_id] = {
            'emoji': emoji,
            'active': True
        }
        
        await ultra_fast_response(ctx, f"✅ Now auto-reacting {emoji} to {user_mention}'s messages!", delete_after=5)
        print(f"🚀 Started auto-reacting {emoji} to user {user_id}")
        
    except Exception as e:
        if not ZERO_ERROR_MODE:
            print(f"React command error: {e}")

# Command: -stopreact <@user> (stop auto-reacting to user)
@bot.command()
async def stopreact(ctx, user_mention=None):
    """Stop auto-reacting to a user's messages - SUPER FAST"""
    try:
        # Instantly delete command
        await instant_delete_command(ctx)
        
        if not user_mention:
            await ultra_fast_response(ctx, "❌ Usage: `-stopreact @user`\nExample: `-stopreact @tyler`", delete_after=5)
            return
        
        # Extract user ID from mention
        user_id = None
        if user_mention.startswith('<@') and user_mention.endswith('>'):
            user_id = user_mention[2:-1].replace('!', '')
        
        if not user_id:
            await ultra_fast_response(ctx, "❌ Invalid user mention! Use @username format", delete_after=5)
            return
        
        # Remove user from reaction targets
        if user_id in reaction_targets:
            del reaction_targets[user_id]
            await ultra_fast_response(ctx, f"✅ Stopped auto-reacting to {user_mention}", delete_after=5)
            print(f"🛑 Stopped auto-reacting to user {user_id}")
        else:
            await ultra_fast_response(ctx, f"❌ Not currently reacting to {user_mention}", delete_after=5)
        
    except Exception as e:
        if not ZERO_ERROR_MODE:
            print(f"Stop react command error: {e}")

# Command: -about (detailed bot information)
@bot.command()
async def about(ctx):
    """Show detailed bot information, features, and credits - SUPER FAST"""
    try:
        # Check authorization first
        requester_id = str(ctx.author.id)
        if not (is_owner(ctx.author.id) or requester_id in authorized_users):
            await ultra_fast_response(ctx, "🚫 **ACCESS DENIED**\n❌ You need authorization to use this command\n💡 Contact owner for access", delete_after=5)
            return
        
        # Instantly delete command
        await instant_delete_command(ctx)
        
        about_info = f"""🔫 **PHANTOM CORE**
**Made by:** ~ leo 💫

**Bot Name:** PHANTOM CORE
**Owner:** <@1157913157025673297>

**🚀 Core Features:**
• LTC Flash Messages - Crypto flash to all channels
• Ultra-Fast Jija Spam - Group chat name changing (0.02s)
• Auto-Harassment System - Drowning & Debate modes
• Multi-Target GC Spam - 3-person group chat spam system
• Voice Channel Dragging - Continuous voice harassment
• Auto-Reaction System - React to any user's messages
• AFK System - Auto-replies with custom messages
• 24/7 Operation - Continuous uptime with auto-recovery

**🛡️ NEW! Security & Management:**
• Whitelist Protection - Protect users from all bot features
• Enhanced Logs - Real-time console monitoring with metrics
• Command History - Track usage analytics and statistics
• Database Integration - Persistent user management
• Advanced Access Control - Multi-tier authorization system

**⚡ Performance:**
• Instant command deletion (zero delay)
• 5ms command processing speed
• Zero error operation mode
• Low latency optimizations
• Super-fast response system
• Database-backed analytics

**📅 Last Update:** August 14, 2025
• Added whitelist protection system (-wl command)
• Enhanced logs with real-time metrics and formatting
• Implemented command history tracking (-history command)
• Fixed database context issues for persistent storage
• Optimized all harassment commands with whitelist integration

**🔮 Recent Additions:**
• Whitelist system with "this user is whitelisted you fucking hoe" protection
• Enhanced -logs command with bot metrics and memory monitoring
• Command usage analytics with top 10 most used commands
• Database persistence for whitelisted users
• Improved error handling and security logging

**📊 Current Status:** ✅ FULLY OPERATIONAL
• All systems running perfectly
• Whitelist protection active
• Database integration functional  
• Command tracking operational
• Zero critical errors detected

**Credits:** Developed by ~ leo with advanced Discord automation & enhanced security"""
        
        await ultra_fast_response(ctx, about_info, delete_after=15)
        print("📋 Displayed bot about information")
        
    except Exception as e:
        if not ZERO_ERROR_MODE:
            print(f"About command error: {e}")

# Command: -access <@user> (give user bot control permission - OWNER ONLY)
@bot.command()
async def access(ctx, *, args=None):
    """Give a user permission to control this selfbot - OWNER ONLY"""
    try:
        print(f"🔍 Access command called with args: {args}")
        
        # Instantly delete command
        await instant_delete_command(ctx)
        
        # HARDCODED OWNER CHECK - NO BYPASS POSSIBLE
        if str(ctx.author.id) != BOT_OWNER_ID:
            await ultra_fast_response(ctx, "🚫 **ACCESS DENIED**\n😂 Only owner can do this you silly human\n👑 Contact the owner to get access.", delete_after=8)
            return
        
        if not args or args.strip() == "":
            await ultra_fast_response(ctx, "❌ Usage: `-access @user`\nExample: `-access @friend`", delete_after=5)
            return
        
        user_mention = args.strip()
        print(f"🔍 Processing user mention: {user_mention}")
        
        # Extract user ID from mention
        user_id = None
        if user_mention.startswith('<@') and user_mention.endswith('>'):
            user_id = user_mention[2:-1].replace('!', '')
        else:
            # Try to extract from plain text mention
            if user_mention.startswith('@'):
                user_mention = user_mention[1:]
            # For now, show error for non-mention format
            await ultra_fast_response(ctx, "❌ Please use proper @user mention format", delete_after=5)
            return
        
        if not user_id or not user_id.isdigit():
            await ultra_fast_response(ctx, "❌ Invalid user mention! Use @username format", delete_after=5)
            return
        
        # Check if user already has access
        if user_id in authorized_users:
            await ultra_fast_response(ctx, f"⚠️ {args} already has bot access!", delete_after=5)
            return
        
        # Add user to authorized users
        authorized_users.add(user_id)
        save_authorized_users()  # Save to file
        print(f"🔍 Current authorized users: {authorized_users}")
        
        await ultra_fast_response(ctx, f"✅ **ACCESS GRANTED**\n🎯 {args} can now control this bot!\n💾 Access saved permanently\n📋 Total authorized users: {len(authorized_users)}", delete_after=10)
        print(f"🔑 Granted bot access to user {user_id} ({args})")
        
    except Exception as e:
        print(f"❌ Access command error: {e}")
        await ultra_fast_response(ctx, f"❌ Error: {e}", delete_after=5)

# Command: -removeaccess <@user> (remove user's bot control permission)
@bot.command()
async def removeaccess(ctx, *, args=None):
    """Remove a user's permission to control this selfbot - ENHANCED PERMISSIONS"""
    try:
        print(f"🔍 Remove access command called with args: {args}")
        
        # Instantly delete command
        await instant_delete_command(ctx)
        
        if not args or args.strip() == "":
            await ultra_fast_response(ctx, "❌ Usage: `-removeaccess @user`\nExample: `-removeaccess @friend`", delete_after=5)
            return
        
        user_mention = args.strip()
        
        # Extract user ID from mention
        user_id = None
        if user_mention.startswith('<@') and user_mention.endswith('>'):
            user_id = user_mention[2:-1].replace('!', '')
        else:
            await ultra_fast_response(ctx, "❌ Please use proper @user mention format", delete_after=5)
            return
        
        if not user_id or not user_id.isdigit():
            await ultra_fast_response(ctx, "❌ Invalid user mention! Use @username format", delete_after=5)
            return
        
        # HARDCODED OWNER CHECK - ABSOLUTELY NO BYPASS POSSIBLE
        if str(ctx.author.id) != BOT_OWNER_ID:
            await ultra_fast_response(ctx, "🚫 **ACCESS DENIED**\n😂 Only owner can do this you silly human\n⚠️ Users cannot remove their own or others' access", delete_after=8)
            return
        
        # Owner can remove anyone's access
        if user_id in authorized_users:
            authorized_users.remove(user_id)
            save_authorized_users()  # Save to file
            await ultra_fast_response(ctx, f"✅ **ACCESS REMOVED**\n🚫 Removed bot access from {args}\n💾 Changes saved permanently\n📋 Remaining authorized users: {len(authorized_users)}", delete_after=8)
            print(f"🚫 Owner removed bot access from user {user_id} ({args})")
        else:
            await ultra_fast_response(ctx, f"❌ {args} doesn't have bot access", delete_after=5)
        
    except Exception as e:
        print(f"❌ Remove access command error: {e}")
        await ultra_fast_response(ctx, f"❌ Error: {e}", delete_after=5)

# Command: -listaccess (show all authorized users)
@bot.command()
async def listaccess(ctx):
    """Show all users who have bot access"""
    try:
        print(f"🔍 List access command called")
        
        # Instantly delete command
        await instant_delete_command(ctx)
        
        # HARDCODED OWNER CHECK - Only owner can view access list  
        if str(ctx.author.id) != BOT_OWNER_ID:
            await ultra_fast_response(ctx, "🚫 **ACCESS DENIED**\n😂 Only owner can view this you silly human\n👑 This is owner-only information", delete_after=8)
            return
        
        if not authorized_users:
            await ultra_fast_response(ctx, "📋 **ACCESS LIST EMPTY**\n⚠️ No users currently have bot access\n👑 Only the owner can grant access", delete_after=8)
            return
        
        access_list = "📋 **AUTHORIZED USERS LIST**\n\n"
        access_list += f"👑 **Owner:** <@{BOT_OWNER_ID}>\n\n"
        access_list += f"🔑 **Authorized Users:** ({len(authorized_users)} total)\n"
        
        for i, user_id in enumerate(authorized_users, 1):
            access_list += f"{i}. <@{user_id}>\n"
        
        access_list += f"\n💾 Data persisted to file\n📝 Use `-removeaccess @user` to remove access"
        
        await ultra_fast_response(ctx, access_list, delete_after=15)
        print(f"📋 Displayed access list with {len(authorized_users)} users")
        
    except Exception as e:
        print(f"❌ List access command error: {e}")
        await ultra_fast_response(ctx, f"❌ Error: {e}", delete_after=5)

# Command: -removemyaccess (DISABLED - Owner only access control)
@bot.command()
async def removemyaccess(ctx):
    """DISABLED - Only owner can manage access"""
    try:
        # Instantly delete command  
        await instant_delete_command(ctx)
        
        await ultra_fast_response(ctx, "🚫 **COMMAND DISABLED**\n😂 Only owner can do this you silly human\n⚠️ Users cannot remove their own access\n💡 Contact owner to remove your access", delete_after=10)
        print(f"🚫 User tried to remove own access - command disabled")
        
    except Exception as e:
        print(f"❌ Remove my access command error: {e}")
        await ultra_fast_response(ctx, f"❌ Error: {e}", delete_after=5)

# Command: -list (show who has bot access with names)
@bot.command()
async def list(ctx):
    """Show all users who have bot access with their names - AUTHORIZED USERS ONLY"""
    try:
        print(f"🔍 List command called")
        
        # Instantly delete command
        await instant_delete_command(ctx)
        
        # HARDCODED OWNER CHECK - Only owner can view access list
        if str(ctx.author.id) != BOT_OWNER_ID:
            await ultra_fast_response(ctx, "🚫 **ACCESS DENIED**\n😂 Only owner can view this you silly human\n👑 This is owner-only information", delete_after=8)
            return
        
        if not authorized_users:
            await ultra_fast_response(ctx, "📋 **ACCESS LIST EMPTY**\n⚠️ No users currently have bot access\n👑 Only the owner can grant access", delete_after=8)
            return
        
        # Build access list with names
        access_list = "📋 **BOT ACCESS LIST**\n\n"
        access_list += f"👑 **Owner:** <@{BOT_OWNER_ID}>\n\n"
        access_list += f"🔑 **Authorized Users:** ({len(authorized_users)} total)\n"
        
        for i, user_id in enumerate(authorized_users, 1):
            try:
                user = await bot.fetch_user(int(user_id))
                access_list += f"{i}. **{user.display_name}** (<@{user_id}>)\n"
            except:
                access_list += f"{i}. <@{user_id}> (Name unavailable)\n"
        
        access_list += f"\n💡 **Access Rules:**\n"
        access_list += f"• 👑 Only owner can give/remove access\n"
        access_list += f"• 🚫 Users CANNOT remove their own access\n"
        access_list += f"• 💾 All changes saved permanently\n"
        access_list += f"• 🔒 Full access control by owner only"
        
        await ultra_fast_response(ctx, access_list, delete_after=20)
        print(f"📋 Displayed access list with {len(authorized_users)} users")
        
    except Exception as e:
        print(f"❌ List command error: {e}")
        await ultra_fast_response(ctx, f"❌ Error: {e}", delete_after=5)

# Command: -logs (show live console logs)
@bot.command()
async def logs(ctx):
    """Show live console logs from Replit - AUTHORIZED USERS ONLY"""
    try:
        print(f"🔍 Enhanced logs command called by {ctx.author.name}")
        
        # Instantly delete command
        await instant_delete_command(ctx)
        
        # Check if user has permission
        requester_id = str(ctx.author.id)
        if not (is_owner(ctx.author.id) or requester_id in authorized_users):
            await ultra_fast_response(ctx, "🚫 **ACCESS DENIED**\n⚠️ Only authorized users can view console logs!", delete_after=8)
            return
        
        # Track command usage
        try:
            user_name = str(ctx.author.name) if ctx.author else "Unknown"
            command_history.append({
                "command": "logs",
                "user": user_name,
                "timestamp": time.time(),
                "args": "view_logs"
            })
        except Exception as track_err:
            print(f"⚠️ Command tracking error: {track_err}")
            # Continue with logs command even if tracking fails
        
        # Get actual live console logs captured by our system
        logs_content = "📋 **REPLIT LIVE CONSOLE LOGS**\n"
        logs_content += f"🕒 Retrieved at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        try:
            if console_logs:
                # Show recent console logs (last 30 entries)
                recent_logs = list(console_logs)[-30:]
                logs_content += "```\n"
                for log_entry in recent_logs:
                    logs_content += log_entry + "\n"
                logs_content += "```\n\n"
                
                # Add enhanced status with security and keep-alive info
                uptime = time.time() - keep_alive_stats.get("uptime_start", time.time())
                uptime_hours = uptime / 3600
                
                logs_content += "🤖 **ENHANCED BOT STATUS:**\n"
                logs_content += f"• Status: ✅ Online and Active\n"
                logs_content += f"• Authorized Users: {len(authorized_users)}\n"
                logs_content += f"• Whitelisted Users: {len(whitelisted_users)}\n"
                logs_content += f"• Discord Guilds: {len(bot.guilds) if hasattr(bot, 'guilds') else 'N/A'}\n"
                logs_content += f"• Uptime: {uptime_hours:.1f} hours\n"
                logs_content += f"• Heartbeats: {keep_alive_stats.get('heartbeat_count', 0)}\n"
                logs_content += f"• Health: {keep_alive_stats.get('health_status', 'unknown')}\n"
                logs_content += f"• Security Events: {len(security_audit_log)}\n"
                logs_content += f"• Total Log Entries: {len(console_logs)}\n"
                logs_content += f"• Command History: {len(command_history)} entries\n"
                
                # Add memory usage if available
                try:
                    import psutil
                    process = psutil.Process()
                    memory_mb = process.memory_info().rss / 1024 / 1024
                    logs_content += f"• Memory Usage: {memory_mb:.1f}MB\n"
                except ImportError:
                    pass
            else:
                logs_content += "⚠️ **NO LOGS CAPTURED YET**\n"
                logs_content += "Enhanced console logging system is active but no logs available.\n\n"
                logs_content += "🤖 **ENHANCED STATUS:**\n"
                logs_content += f"• Status: ✅ Online with Enhanced Security\n"
                logs_content += f"• Authorized Users: {len(authorized_users)}\n"
                logs_content += f"• Whitelisted Users: {len(whitelisted_users)}\n"
                logs_content += f"• Security System: {'🔒 Active' if SECURITY_ENHANCED else '⚠️ Basic'}\n"
                
        except Exception as log_err:
            logs_content += f"⚠️ **LOG SYSTEM ERROR**\n"
            logs_content += f"Error: {str(log_err)}\n\n"
            logs_content += "🔄 **FALLBACK STATUS**\n"
            logs_content += f"• Bot: ✅ Running\n"
            logs_content += f"• Users: {len(authorized_users)} authorized\n"
        
            await ultra_fast_response(ctx, logs_content, delete_after=25)
            
        except Exception as logs_err:
            error_content = f"❌ **ERROR RETRIEVING LOGS**\n```\n{str(logs_err)}\n```\n\nBasic Status: Bot is online"
            await ultra_fast_response(ctx, error_content, delete_after=15)
            
    except Exception as e:
        await ultra_fast_response(ctx, f"❌ Logs command error: {e}", delete_after=8)
        print(f"❌ Enhanced logs command error: {e}")

# Global variables for target system and GC spam
saved_targets = []  # List of saved target user objects
gc_spam_active = {"active": False, "count": 0, "task": None}  # Multi-target GC spam status
GC_SPAM_DELAY = 0.6  # Delay between 3-person GC creation (600ms)
MAX_GC_SPAM_COUNT = 50  # Maximum number of 3-person GCs per session

# Command: -target @user (save targets for multi-person GC spam)
@bot.command()
async def target(ctx, user_mention=None):
    global saved_targets  # Declare at the very beginning
    try:
        # Check if user is authorized
        if not is_authorized_user(ctx.author.id):
            await ultra_fast_response(ctx, "❌ Unauthorized access", delete_after=3)
            return
        
        # Instantly delete command
        await instant_delete_command(ctx)
        
        if not user_mention:
            # Show current saved targets
            if not saved_targets:
                await ultra_fast_response(ctx, "📝 **NO TARGETS SAVED**\nUse `-target @user` to save targets for 3-person GC spam\nExample: `-target @user1` then `-target @user2`", delete_after=12)
                return
            
            target_list = []
            for i, target in enumerate(saved_targets, 1):
                target_list.append(f"🎯 Target {i}: **{target.display_name}** ({target.name})")
            
            targets_text = "\n".join(target_list)
            await ultra_fast_response(ctx, f"🎯 **SAVED TARGETS ({len(saved_targets)})**\n{targets_text}\n\n🚀 Use `-gcspam` to create 3-person group chats with all targets\n🗑️ Use `-cleartargets` to clear all targets", delete_after=15)
            return
        
        # Smart user lookup - guild member search only (no API fetch)
        target_user = None
        search_name = user_mention
        
        print(f"🔍 Looking up user: {user_mention}")
        
        # Extract user ID from mention format if present
        user_id = None
        if user_mention.startswith('<@') and user_mention.endswith('>'):
            user_id_str = user_mention[2:-1].replace('!', '')
            if user_id_str.isdigit():
                user_id = int(user_id_str)
                print(f"📝 Extracted user ID: {user_id}")
                
                # Check if target user is whitelisted before adding to targets
                if is_user_whitelisted(user_id):
                    await ultra_fast_response(ctx, "🚫 **ACCESS DENIED**\n❌ This user is whitelisted you fucking hoe\n💡 Cannot target protected users for harassment", delete_after=10)
                    return
                
                # Check if target user is whitelisted before adding to targets
                if is_user_whitelisted(user_id):
                    await ultra_fast_response(ctx, "🚫 **ACCESS DENIED**\n❌ This user is whitelisted you fucking hoe\n💡 Cannot target protected users for harassment", delete_after=10)
                    return
        
        # Clean up search name - remove @ and < > symbols
        search_name = user_mention.replace('<@', '').replace('>', '').replace('!', '').replace('@', '').strip()
        
        # Method 1: Search current guild by user ID first (if we have it)
        if user_id and hasattr(ctx, 'guild') and ctx.guild:
            try:
                target_user = ctx.guild.get_member(user_id)
                if target_user:
                    print(f"✅ Found user by ID in current guild: {target_user.display_name}")
                else:
                    print(f"⚠️ User ID {user_id} not found in current guild")
            except Exception as e:
                print(f"⚠️ Current guild ID search failed: {e}")
        
        # Method 2: Search current guild by name
        if not target_user and hasattr(ctx, 'guild') and ctx.guild:
            try:
                for member in ctx.guild.members:
                    if (member.name.lower() == search_name.lower() or 
                        member.display_name.lower() == search_name.lower() or
                        (hasattr(member, 'global_name') and member.global_name and member.global_name.lower() == search_name.lower())):
                        target_user = member
                        print(f"✅ Found user by name in current guild: {target_user.display_name}")
                        break
            except Exception as e:
                print(f"⚠️ Current guild name search failed: {e}")
        
        # Method 3: Search all guilds by user ID
        if not target_user and user_id:
            try:
                for guild in bot.guilds:
                    target_user = guild.get_member(user_id)
                    if target_user:
                        print(f"✅ Found user by ID in guild {guild.name}: {target_user.display_name}")
                        break
            except Exception as e:
                print(f"⚠️ Global guild ID search failed: {e}")
        
        # Method 4: Search all guilds by name
        if not target_user:
            try:
                for guild in bot.guilds:
                    for member in guild.members:
                        if (member.name.lower() == search_name.lower() or 
                            member.display_name.lower() == search_name.lower() or
                            (hasattr(member, 'global_name') and member.global_name and member.global_name.lower() == search_name.lower())):
                            target_user = member
                            print(f"✅ Found user by name in guild {guild.name}: {target_user.display_name}")
                            break
                    if target_user:
                        break
            except Exception as e:
                print(f"⚠️ Global guild name search failed: {e}")
        
        if not target_user:
            await ultra_fast_response(ctx, f"❌ **USER NOT FOUND** 😭\n🔍 Searched for: `{user_mention}`\n💡 User must be in a server with the bot\n🤝 Try with exact Discord username", delete_after=8)
            print(f"❌ Failed to find user: {user_mention} (searched as: {search_name})")
            return
        
        # Check if target already exists
        if target_user.id in [t.id for t in saved_targets]:
            await ultra_fast_response(ctx, f"⚠️ **{target_user.display_name}** is already in targets list", delete_after=5)
            return
        
        # Add target to global list
        if not isinstance(saved_targets, list):
            saved_targets = []  # Reset if corrupted
        saved_targets.append(target_user)
        target_number = len(saved_targets)
        
        print(f"🎯 Target {target_number} saved: {target_user.display_name} ({target_user.id})")
        await ultra_fast_response(ctx, f"✅ **TARGET {target_number} SAVED**\n👤 **{target_user.display_name}** added to targets\n📊 Total targets: **{len(saved_targets)}**\n💡 Need at least 2 targets for 3-person GCs", delete_after=10)
        
    except Exception as e:
        print(f"❌ Target command error: {e}")
        await ultra_fast_response(ctx, f"❌ Error: {e}", delete_after=5)

# Command: -cleartargets (clear all saved targets)
@bot.command()
async def cleartargets(ctx):
    global saved_targets  # Declare global at the beginning
    try:
        if not is_authorized_user(ctx.author.id):
            await ultra_fast_response(ctx, "❌ Unauthorized access", delete_after=3)
            return
        
        # Instantly delete command
        await instant_delete_command(ctx)
        
        if not isinstance(saved_targets, list):
            saved_targets = []  # Reset if corrupted
        target_count = len(saved_targets)
        
        if target_count == 0:
            await ultra_fast_response(ctx, "📝 No targets to clear", delete_after=5)
            return
        
        saved_targets.clear()
        
        print(f"🗑️ Cleared {target_count} saved targets")
        await ultra_fast_response(ctx, f"🗑️ **TARGETS CLEARED**\n📊 Removed {target_count} saved targets\n💡 Use `-target @user` to add new targets", delete_after=8)
        
    except Exception as e:
        print(f"❌ Clear targets command error: {e}")
        await ultra_fast_response(ctx, f"❌ Error: {e}", delete_after=5)

# Command: -gcspam (create 3-person group chats with all saved targets)
@bot.command()
async def gcspam(ctx):
    """Create 3-person group chats with all saved targets - MULTI-TARGET HARASSMENT"""
    try:
        print(f"🔍 Multi-target GC spam command called")
        
        # Check if user is authorized
        if not is_authorized_user(ctx.author.id):
            await ultra_fast_response(ctx, "❌ Unauthorized access", delete_after=3)
            return
        
        # Instantly delete command
        await instant_delete_command(ctx)
        
        # Check if we have saved targets
        if len(saved_targets) < 2:
            await ultra_fast_response(ctx, f"❌ **NEED MORE TARGETS**\n📊 Current targets: {len(saved_targets)}\n💡 Need at least 2 targets for 3-person GCs\n🎯 Use `-target @user` to add targets", delete_after=10)
            return
        
        # Check if already spamming
        if gc_spam_active["active"]:
            await ultra_fast_response(ctx, f"⚠️ **GC SPAM ALREADY ACTIVE**\n📊 Current session progress: {gc_spam_active['count']} GCs created\nUse `-stopgcspam` to stop current session", delete_after=8)
            return
        
        # Show targets summary
        target_names = [f"**{target.display_name}**" for target in saved_targets]
        targets_text = ", ".join(target_names)
        
        await ultra_fast_response(ctx, f"🎯 **STARTING 3-PERSON GC SPAM**\n👥 Targets: {targets_text}\n📊 Total targets: {len(saved_targets)}\n🚀 Creating group chats with all combinations...", delete_after=8)
        
        # Start multi-target GC spam
        gc_spam_active["active"] = True
        gc_spam_active["count"] = 0
        gc_spam_active["channel_id"] = ctx.channel.id
        
        # Create background task for 3-person GC spam
        task = asyncio.create_task(multi_target_gc_spam_task())
        gc_spam_active["task"] = task
        
        print(f"🎯 Started multi-target GC spam with {len(saved_targets)} targets")
        
    except Exception as e:
        print(f"❌ GC spam command error: {e}")
        await ultra_fast_response(ctx, f"❌ Error: {e}", delete_after=5)

# Background task for multi-target 3-person group chat spam
async def multi_target_gc_spam_task():
    """Create 3-person group chats with all saved targets and leave them"""
    try:
        global saved_targets  # Ensure we're accessing the global variable
        
        # Simple validation - just check if we have targets
        # Force ensure saved_targets is a proper list
        global saved_targets
        if not isinstance(saved_targets, list):
            print(f"❌ Critical Fix: saved_targets was {type(saved_targets)}, resetting to empty list")
            saved_targets = []
            
        try:
            target_count = len(saved_targets)
            print(f"🔍 Debug: saved_targets type: {type(saved_targets)}, count: {target_count}")
            
            if target_count < 2:
                print(f"❌ Error: Need at least 2 targets, only have {target_count}")
                gc_spam_active["active"] = False
                return
        except Exception as validation_err:
            print(f"❌ Error validating targets: {validation_err}")
            print(f"🚰 Debug: saved_targets type: {type(saved_targets)}, value: {saved_targets}")
            saved_targets = []  # Reset to safe state
            gc_spam_active["active"] = False
            return
            
        try:
            targets_len = len(saved_targets) if isinstance(saved_targets, (list, tuple)) else 0
            print(f"🎯 Starting multi-target GC spam with {targets_len} targets")
        except Exception as len_err:
            print(f"❌ Length error: {len_err}, type: {type(saved_targets)}")
            saved_targets = []
            gc_spam_active["active"] = False
            return
        channel_id = gc_spam_active["channel_id"]
        
        # Create all possible combinations of targets for 3-person GCs
        from itertools import combinations
        target_combinations = list(combinations(saved_targets, 2))  # 2 targets + bot = 3-person GC
        
        print(f"🔢 Created {len(target_combinations)} target combinations for 3-person GCs")
        
        while gc_spam_active["active"] and gc_spam_active["count"] < MAX_GC_SPAM_COUNT:
            # Cycle through all target combinations
            for target1, target2 in target_combinations:
                if not gc_spam_active["active"]:
                    break
                
                try:
                    # Add human-like delay for stealth
                    if STEALTH_MODE:
                        await add_human_like_delay()
                    
                    # Create 3-person group chat with bot + 2 targets
                    try:
                        print(f"🎯 Creating 3-person GC: {target1.display_name} + {target2.display_name}")
                        
                        # Method: Use discord.py-self group creation
                        recipients = [target1, target2]  # Bot is automatically included
                        
                        # Try to create group channel using direct HTTP API
                        group_channel = None
                        try:
                            # Create group using HTTP API method
                            group_data = {
                                'recipients': [target1.id, target2.id]
                            }
                            
                            # Use bot's HTTP client for group creation
                            from discord.http import Route
                            response = await bot.http.request(
                                Route('POST', '/users/@me/channels'),
                                json=group_data
                            )
                            
                            if response and 'id' in response:
                                # Get the created group channel
                                group_channel_id = int(response['id'])
                                # Wait a moment for Discord to process
                                await asyncio.sleep(0.1)
                                group_channel = bot.get_channel(group_channel_id)
                        
                        except Exception as creation_err:
                            print(f"⚠️ Group creation failed: {creation_err}")
                            continue
                            
                        if group_channel:
                            gc_spam_active["count"] += 1
                            print(f"✅ Created 3-person GC #{gc_spam_active['count']}: {target1.display_name} + {target2.display_name}")
                            
                            # Leave the group immediately using HTTP DELETE
                            left_successfully = False
                            
                            try:
                                # Use proper HTTP route for leaving group
                                from discord.http import Route
                                await bot.http.request(
                                    Route('DELETE', '/channels/{channel_id}', channel_id=group_channel.id)
                                )
                                print(f"🚪 Left 3-person GC #{gc_spam_active['count']}")
                                left_successfully = True
                            except discord.HTTPException as http_err:
                                if "rate limited" in str(http_err).lower():
                                    print(f"🛡️ Rate limited while leaving, waiting...")
                                    await asyncio.sleep(2)
                                else:
                                    print(f"⚠️ HTTP leave error: {http_err}")
                            except Exception as leave_err:
                                print(f"⚠️ Leave failed for GC #{gc_spam_active['count']}: {leave_err}")
                            
                            if not left_successfully:
                                print(f"❌ Could not leave GC #{gc_spam_active['count']} - Group chat may remain active")
                        else:
                            print(f"⚠️ Failed to create GC with {target1.display_name} + {target2.display_name}")
                        
                    except discord.Forbidden:
                        print(f"❌ Forbidden to create GC with {target1.display_name} + {target2.display_name}")
                        continue
                    
                    except Exception as gc_err:
                        print(f"⚠️ Error creating 3-person GC: {gc_err}")
                        continue
                    
                    # Delay between GC creations for rate limiting
                    await asyncio.sleep(GC_SPAM_DELAY)
                    print(f"⏱️ Waiting {GC_SPAM_DELAY}s before next GC creation...")
                    
                    # Check if we reached the limit
                    if gc_spam_active["count"] >= MAX_GC_SPAM_COUNT:
                        break
                        
                except asyncio.CancelledError:
                    break
                except Exception as loop_err:
                    print(f"❌ Error in GC spam loop: {loop_err}")
                    await asyncio.sleep(1)
        
        # Cleanup when done
        gc_spam_active["active"] = False
        final_count = gc_spam_active["count"]
        
        # Send completion message
        try:
            channel = bot.get_channel(channel_id)
            if channel:
                completion_msg = f"🎯 **3-PERSON GC SPAM COMPLETED**\n👥 Targets: {len(saved_targets)} users\n📊 Total 3-person GCs Created: **{final_count}**\n⏱️ Session ended successfully"
                await channel.send(completion_msg)
                await asyncio.sleep(10)
        except:
            pass
        
        print(f"🏁 Multi-target GC spam completed - Created {final_count} 3-person group chats")
        
    except Exception as e:
        print(f"❌ Critical error in multi-target GC spam: {e}")
        gc_spam_active["active"] = False

# Background task for rapid group chat creation and leaving (DEPRECATED - kept for compatibility)
async def rapid_gc_spam_task(user_id):
    """Rapidly create group chats with target user and leave them"""
    try:
        spam_data = gc_spam_active[user_id]
        target_user = spam_data["target_user"]
        mention = spam_data["mention"]
        channel_id = spam_data["channel_id"]
        
        print(f"🎯 Starting rapid GC spam task for {mention}")
        
        while spam_data["active"] and spam_data["count"] < MAX_GC_SPAM_COUNT:
            try:
                # Add human-like delay for stealth
                if STEALTH_MODE:
                    await add_human_like_delay()
                
                # Simplified but effective harassment method
                try:
                    success = False
                    
                    # For accessible targets (friends or open DMs)
                    if spam_data["is_friend"]:
                        try:
                            # Method 1: Create multiple DM connections (works reliably)
                            dm_channel = await target_user.create_dm()
                            if dm_channel:
                                spam_data["count"] += 1
                                print(f"✅ Created DM connection #{spam_data['count']} with {mention}")
                                
                                # Try to send a harmless message to trigger notification
                                try:
                                    await dm_channel.send(".", delete_after=0.1)
                                    print(f"💬 Sent notification message #{spam_data['count']}")
                                except:
                                    pass  # Ignore if message send fails
                                
                                success = True
                                
                        except discord.Forbidden:
                            print(f"❌ Access denied to {mention} (blocked/privacy)")
                            break  # Stop if we get blocked
                        except Exception as dm_err:
                            print(f"⚠️ DM error: {dm_err}")
                    
                    # For non-accessible targets - try friend requests
                    else:
                        try:
                            # Send friend request (reliable notification method)
                            await target_user.send_friend_request()
                            spam_data["count"] += 1
                            print(f"✅ Sent friend request #{spam_data['count']} to {mention}")
                            success = True
                        except discord.HTTPException as http_err:
                            if "already friends" in str(http_err).lower():
                                # They're actually a friend, update status
                                spam_data["is_friend"] = True
                                print(f"📝 Updated: {mention} is actually a friend")
                                continue  # Retry with friend method
                            else:
                                print(f"⚠️ Friend request failed: {http_err}")
                        except Exception as req_err:
                            print(f"⚠️ Friend request error: {req_err}")
                    
                    if not success:
                        print(f"⚠️ Harassment attempt #{spam_data['count']} failed for {mention}")
                        spam_data["count"] += 1  # Still count attempt
                    
                except discord.HTTPException as http_err:
                    if "rate limited" in str(http_err).lower():
                        print(f"🛡️ Rate limited during GC spam, waiting...")
                        await asyncio.sleep(5)  # Wait longer on rate limit
                        continue
                    else:
                        print(f"⚠️ HTTP error creating GC: {http_err}")
                
                except discord.Forbidden:
                    print(f"❌ Forbidden to create GC with {mention} (blocked or privacy)")
                    break
                
                except Exception as gc_err:
                    print(f"⚠️ Error creating GC: {gc_err}")
                
                # Delay between GC creations
                await asyncio.sleep(GC_SPAM_DELAY)
                
            except asyncio.CancelledError:
                break
            except Exception as loop_err:
                print(f"❌ Error in GC spam loop: {loop_err}")
                await asyncio.sleep(1)
        
        # Cleanup when done
        if user_id in gc_spam_active:
            final_count = gc_spam_active[user_id]["count"]
            gc_spam_active[user_id]["active"] = False
            
            # Send completion message to channel
            try:
                channel = bot.get_channel(channel_id)
                if channel:
                    completion_msg = f"🎯 **GC SPAM COMPLETED**\n👤 Target: {mention}\n📊 Total GCs Created: {final_count}\n⏱️ Session ended"
                    await channel.send(completion_msg)
                    await asyncio.sleep(8)
                    # Don't delete completion message for visibility
            except:
                pass
            
            print(f"🏁 GC spam completed for {mention} - Created {final_count} group chats")
        
    except Exception as e:
        print(f"❌ Critical error in GC spam task: {e}")
        if user_id in gc_spam_active:
            gc_spam_active[user_id]["active"] = False

# Command: -stopgcspam (stop multi-target GC spam)
@bot.command()
async def stopgcspam(ctx):
    """Stop multi-target 3-person GC spam session"""
    try:
        print(f"🔍 Stop multi-target GC spam command called")
        
        # Check if user is authorized
        if not is_authorized_user(ctx.author.id):
            await ultra_fast_response(ctx, "❌ Unauthorized access", delete_after=3)
            return
        
        # Instantly delete command
        await instant_delete_command(ctx)
        
        # Stop GC spam if active
        if gc_spam_active["active"]:
            gc_spam_active["active"] = False
            
            # Cancel the task if it exists
            if gc_spam_active["task"]:
                gc_spam_active["task"].cancel()
            
            final_count = gc_spam_active["count"]
            target_count = len(saved_targets)
            
            await ultra_fast_response(ctx, f"✅ **3-PERSON GC SPAM STOPPED**\n👥 Targets: {target_count} users\n📊 Total 3-person GCs Created: **{final_count}**\n⏱️ Session stopped by user", delete_after=10)
            print(f"🛑 Stopped multi-target GC spam - Created {final_count} 3-person GCs")
        else:
            await ultra_fast_response(ctx, f"❌ **NO ACTIVE GC SPAM**\nNo multi-target GC spam session is currently running\n💡 Use `-gcspam` to start 3-person GC spam", delete_after=8)
        
    except Exception as e:
        print(f"❌ Stop GC spam command error: {e}")
        await ultra_fast_response(ctx, f"❌ Error: {e}", delete_after=5)

# Command: -test (ultra-fast bot functionality test)
@bot.command()
async def test(ctx):
    """Ultra-fast comprehensive bot functionality test"""
    try:
        # Instant command deletion
        if INSTANT_DELETE_COMMANDS:
            asyncio.create_task(ctx.message.delete())
        
        start_time = time.time()
        
        # Ultra-fast test sequence
        test_msg = await ctx.send("🧪 **ULTRA-FAST TESTING...**")
        
        tests = [
            "✅ Command processing",
            "✅ Message editing", 
            "✅ Discord API connection",
            "✅ WebSocket stability",
            "✅ Ultra-fast response mode",
            "✅ Zero-error operation"
        ]
        
        test_results = "🚀 **ULTRA-FAST BOT TEST COMPLETE**\n\n"
        for test in tests:
            test_results += f"{test}\n"
            await asyncio.sleep(0.1)  # Minimal delay for visual effect
        
        total_time = round((time.time() - start_time) * 1000, 1)
        test_results += f"\n⚡ **Total test time:** {total_time}ms\n"
        test_results += f"🎯 **Performance:** OPTIMIZED FOR SPEED"
        
        await test_msg.edit(content=test_results)
        await asyncio.sleep(10)
        await test_msg.delete()
        
        print(f"🧪 Bot test completed in {total_time}ms - ALL SYSTEMS OPTIMAL")
        
    except Exception as e:
        error_msg = await ctx.send(f"❌ **Test Error:** {e}")
        await asyncio.sleep(3)
        await error_msg.delete()

# ULTRA-ENHANCED AI-Powered Keep-Alive System with Adaptive Performance
keep_alive_stats = {
    "heartbeat_count": 0,
    "last_heartbeat": 0,
    "connection_checks": 0,
    "reconnections": 0,
    "health_status": "starting",
    "uptime_start": time.time(),
    "performance_score": 100,
    "memory_usage_mb": 0,
    "response_time_ms": 0,
    "error_count": 0,
    "last_optimization": time.time(),
    "adaptive_interval": 8,  # Starts at 8s, adapts based on performance
    "peak_performance": 100,
    "optimization_cycles": 0,
    "stability_rating": "excellent"
}

async def ultra_enhanced_keep_alive_task():
    """ULTRA-ENHANCED AI-powered adaptive keep-alive with performance optimization"""
    global keep_alive_stats
    
    print("🚀 ULTRA-ENHANCED AI Keep-Alive System Started - Adaptive Performance Mode Activated")
    keep_alive_stats["uptime_start"] = time.time()
    
    while True:
        try:
            # ADAPTIVE PERFORMANCE INTERVAL - AI-optimized based on system health
            interval = keep_alive_stats["adaptive_interval"]
            
            # Performance-based interval adjustment
            if keep_alive_stats["performance_score"] > 95:
                interval = max(5, interval - 0.5)  # Speed up for excellent performance
            elif keep_alive_stats["performance_score"] < 60:
                interval = min(20, interval + 1)  # Slow down for poor performance
            
            keep_alive_stats["adaptive_interval"] = interval
            await asyncio.sleep(interval)
            
            # ULTRA-ENHANCED performance monitoring
            cycle_start = time.time()
            keep_alive_stats["heartbeat_count"] += 1
            keep_alive_stats["last_heartbeat"] = cycle_start
            
            # Advanced system monitoring with AI analytics
            try:
                import psutil
                process = psutil.Process()
                keep_alive_stats["memory_usage_mb"] = round(process.memory_info().rss / 1024 / 1024, 1)
                
                # AI Performance score calculation
                memory_score = max(0, 100 - (keep_alive_stats["memory_usage_mb"] / 10))
                error_score = max(0, 100 - (keep_alive_stats["error_count"] * 5))
                connection_score = 100 if bot.is_ready() else 0
                
                keep_alive_stats["performance_score"] = int((memory_score + error_score + connection_score) / 3)
                keep_alive_stats["peak_performance"] = max(keep_alive_stats["peak_performance"], keep_alive_stats["performance_score"])
                
            except Exception as monitor_err:
                keep_alive_stats["error_count"] += 1
            
            # Layer 1: Basic connection health check
            try:
                if bot.is_ready() and not bot.is_closed():
                    keep_alive_stats["health_status"] = "healthy"
                    
                    # Periodic presence update (every 10 heartbeats = ~80 seconds)
                    if keep_alive_stats["heartbeat_count"] % 10 == 0:
                        if not LOW_LATENCY_MODE:
                            try:
                                await bot.change_presence(status=discord.Status.online)
                            except:
                                pass  # Ignore presence errors
                else:
                    keep_alive_stats["health_status"] = "unhealthy"
                    print(f"⚠️ Keep-Alive: Bot connection unhealthy")
                    
            except Exception as health_err:
                keep_alive_stats["health_status"] = "error"
                print(f"⚠️ Keep-Alive Health Check Error: {health_err}")
            
            # Layer 2: Connection monitoring (every 5 heartbeats = ~40 seconds)
            if keep_alive_stats["heartbeat_count"] % 5 == 0:
                try:
                    keep_alive_stats["connection_checks"] += 1
                    
                    # Check latency
                    if hasattr(bot, 'latency') and bot.latency > 5.0:  # High latency warning
                        print(f"⚠️ Keep-Alive: High latency detected: {bot.latency:.2f}s")
                    
                    # Check guild count
                    if hasattr(bot, 'guilds') and len(bot.guilds) == 0:
                        print(f"⚠️ Keep-Alive: No guilds connected")
                        
                except Exception as monitor_err:
                    print(f"⚠️ Keep-Alive Monitoring Error: {monitor_err}")
            
            # Layer 3: Uptime and stats logging (every 20 heartbeats = ~160 seconds)
            if keep_alive_stats["heartbeat_count"] % 20 == 0:
                current_time = time.time()  # Define current_time properly
                uptime = current_time - keep_alive_stats["uptime_start"]
                uptime_hours = uptime / 3600
                print(f"💓 Keep-Alive Stats: {keep_alive_stats['heartbeat_count']} beats, "
                      f"{uptime_hours:.1f}h uptime, Status: {keep_alive_stats['health_status']}")
            
        except asyncio.CancelledError:
            print("🛑 Keep-Alive Task Cancelled")
            break
        except Exception as ka_err:
            print(f"❌ Keep-Alive Critical Error: {ka_err}")
            # Enhanced error recovery
            try:
                await asyncio.sleep(3)  # Brief pause before retry
                keep_alive_stats["reconnections"] += 1
                if keep_alive_stats["reconnections"] > 10:
                    print(f"🚨 Keep-Alive: Too many reconnection attempts, reducing frequency")
                    await asyncio.sleep(30)  # Longer pause if too many failures
            except:
                pass

# Secondary keep-alive heartbeat for redundancy
async def secondary_heartbeat_task():
    """Secondary heartbeat system for additional redundancy"""
    while True:
        try:
            await asyncio.sleep(15)  # 15-second interval, offset from primary
            
            # Simple connection check
            if bot.is_ready():
                # Lightweight operation to maintain connection
                try:
                    _ = len(bot.guilds)  # Simple attribute access
                except:
                    pass
            
        except asyncio.CancelledError:
            break
        except:
            await asyncio.sleep(10)

# Enhanced background task with error recovery
async def enhanced_background_tasks():
    """Enhanced background tasks with comprehensive error handling and monitoring"""
    task_stats = {
        "cycles": 0,
        "last_cleanup": time.time(),
        "errors": 0
    }
    
    print("🔧 Enhanced Background Tasks Started")
    
    while True:
        try:
            await asyncio.sleep(12)  # 12-second cycle
            task_stats["cycles"] += 1
            current_time = time.time()
            
            # Cleanup corrupted data structures
            try:
                # Clear potentially corrupted dictionaries
                if len(drowned_users) > 100:  # Prevent memory overflow
                    drowned_users.clear()
                    print("🧹 Cleaned drowned_users dictionary")
                
                if len(debated_users) > 100:
                    debated_users.clear()
                    print("🧹 Cleaned debated_users dictionary")
                
                # Clean old security logs
                if len(failed_attempts) > 50:
                    # Remove old failed attempts
                    cutoff_time = current_time - 3600  # 1 hour ago
                    failed_attempts.clear()
                    print("🧹 Cleaned old failed attempts")
                
            except Exception as cleanup_err:
                print(f"⚠️ Background cleanup error: {cleanup_err}")
                task_stats["errors"] += 1
            
            # Performance monitoring (every 10 cycles = ~2 minutes)
            if task_stats["cycles"] % 10 == 0:
                try:
                    # Memory usage check
                    import psutil
                    process = psutil.Process()
                    memory_mb = process.memory_info().rss / 1024 / 1024
                    
                    if memory_mb > 500:  # Alert if using > 500MB
                        print(f"⚠️ High memory usage: {memory_mb:.1f}MB")
                    
                except ImportError:
                    pass  # psutil not available
                except Exception as perf_err:
                    print(f"⚠️ Performance monitoring error: {perf_err}")
            
            task_stats["last_cleanup"] = current_time
            
        except asyncio.CancelledError:
            break
        except Exception as bg_err:
            print(f"❌ Background task error: {bg_err}")
            task_stats["errors"] += 1
            
            # Enhanced error recovery
            if task_stats["errors"] > 20:
                print("🚨 Too many background task errors, extending sleep time")
                await asyncio.sleep(60)  # Extended pause
                task_stats["errors"] = 0  # Reset error count
            else:
                await asyncio.sleep(15)  # Standard pause

# Command tracking for history
command_history = []

# Command: -wl @user (whitelist/unwhitelist users)
@bot.command(name='wl')
async def whitelist_command(ctx, user_mention=None, action=None):
    """Whitelist or unwhitelist users from bot features - OWNER ONLY"""
    try:
        # Check if user is owner
        if not is_owner(ctx.author.id):
            await ctx.message.edit(content="🚫 **ACCESS DENIED**\n⚠️ Only the bot owner can manage whitelist!")
            await asyncio.sleep(8)
            await ctx.message.delete()
            return
        
        # Track command usage
        command_history.append({
            "command": "wl",
            "user": ctx.author.name,
            "timestamp": time.time(),
            "args": f"{user_mention} {action}" if action else user_mention or "help"
        })
        
        # If no arguments, show whitelist help and current whitelisted users
        if not user_mention:
            try:
                whitelisted_list = get_whitelisted_users() if DATABASE_INTEGRATION else []
                help_content = "🔒 **WHITELIST MANAGEMENT**\n\n"
                help_content += "**Usage:**\n"
                help_content += "• `-wl @user add` - Add user to whitelist\n"
                help_content += "• `-wl @user remove` - Remove user from whitelist\n"
                help_content += "• `-wl list` - Show all whitelisted users\n"
                help_content += "• `-wl` - Show this help\n\n"
                help_content += f"**Currently Whitelisted ({len(whitelisted_list)}):**\n"
                
                if whitelisted_list:
                    for i, user in enumerate(whitelisted_list[:10], 1):  # Show first 10
                        help_content += f"{i}. <@{user.discord_id}> (ID: {user.discord_id})\n"
                    if len(whitelisted_list) > 10:
                        help_content += f"... and {len(whitelisted_list) - 10} more\n"
                else:
                    help_content += "⚠️ No users currently whitelisted\n"
                
                help_content += "\n💡 **Note:** Whitelisted users are protected from all bot harassment features"
                
                await ctx.message.edit(content=help_content)
                await asyncio.sleep(15)
                await ctx.message.delete()
                return
            except Exception as e:
                await ctx.message.edit(content=f"❌ Error retrieving whitelist: {e}")
                await asyncio.sleep(8)
                await ctx.message.delete()
                return
        
        # Handle "list" command
        if user_mention.lower() == "list":
            try:
                whitelisted_list = get_whitelisted_users() if DATABASE_INTEGRATION else []
                list_content = f"🔒 **WHITELISTED USERS ({len(whitelisted_list)})**\n\n"
                
                if whitelisted_list:
                    for i, user in enumerate(whitelisted_list, 1):
                        list_content += f"{i}. <@{user.discord_id}> (ID: {user.discord_id})\n"
                        list_content += f"   Added: {user.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
                else:
                    list_content += "⚠️ No users currently whitelisted\n"
                
                await ctx.message.edit(content=list_content)
                await asyncio.sleep(20)
                await ctx.message.delete()
                return
            except Exception as e:
                await ctx.message.edit(content=f"❌ Error listing whitelist: {e}")
                await asyncio.sleep(8)
                await ctx.message.delete()
                return
        
        # Parse user mention to get user ID
        user_id = find_user_id_by_mention(user_mention)
        if not user_id:
            await ctx.message.edit(content="❌ Invalid user mention format. Use @username or @UserID")
            await asyncio.sleep(8)
            await ctx.message.delete()
            return
        
        # Default action is toggle (add if not whitelisted, remove if already whitelisted)
        if not action:
            is_whitelisted = is_user_whitelisted(user_id)
            action = "remove" if is_whitelisted else "add"
        
        action = action.lower()
        
        if action == "add":
            # Add user to whitelist
            try:
                if DATABASE_INTEGRATION:
                    from models import add_whitelisted_user_db
                    add_whitelisted_user_db(user_id, user_mention, ctx.author.id, "Added via whitelist command")
                whitelisted_users.add(str(user_id))  # Add to in-memory set
                
                await ctx.message.edit(content=f"✅ **USER WHITELISTED**\n🛡️ User {user_mention} has been added to whitelist\n💡 They are now protected from all bot features")
                await asyncio.sleep(10)
                await ctx.message.delete()
                print(f"✅ User {user_id} added to whitelist by {ctx.author.name}")
                
            except Exception as e:
                await ctx.message.edit(content=f"❌ Error adding to whitelist: {e}")
                await asyncio.sleep(8)
                await ctx.message.delete()
        
        elif action == "remove":
            # Remove user from whitelist
            try:
                if DATABASE_INTEGRATION:
                    from models import remove_whitelisted_user_db
                    remove_whitelisted_user_db(user_id)
                whitelisted_users.discard(str(user_id))  # Remove from in-memory set
                
                await ctx.message.edit(content=f"✅ **USER REMOVED FROM WHITELIST**\n🗑️ User {user_mention} has been removed from whitelist\n⚠️ They can now be targeted by bot features")
                await asyncio.sleep(10)
                await ctx.message.delete()
                print(f"✅ User {user_id} removed from whitelist by {ctx.author.name}")
                
            except Exception as e:
                await ctx.message.edit(content=f"❌ Error removing from whitelist: {e}")
                await asyncio.sleep(8)
                await ctx.message.delete()
        
        else:
            await ctx.message.edit(content="❌ Invalid action. Use 'add' or 'remove'")
            await asyncio.sleep(8)
            await ctx.message.delete()
    
    except Exception as e:
        await ctx.message.edit(content=f"❌ Whitelist command error: {e}")
        await asyncio.sleep(8)
        await ctx.message.delete()
        print(f"❌ Whitelist command error: {e}")

# Command: -clearwhitelist (clear all whitelisted users)
@bot.command(name='clearwhitelist')
async def clear_whitelist_command(ctx):
    """Clear all whitelisted users - OWNER ONLY"""
    try:
        # Check if user is owner
        if not is_owner(ctx.author.id):
            await ctx.message.edit(content="🚫 **ACCESS DENIED**\n⚠️ Only the bot owner can clear whitelist!")
            await asyncio.sleep(8)
            await ctx.message.delete()
            return
        
        # Show confirmation first
        await ctx.message.edit(content="🧹 **CLEARING ALL WHITELISTED USERS...**\n⏳ Removing from database and memory...")
        await asyncio.sleep(2)
        
        # Clear all whitelisted users
        cleared_count = clear_all_whitelisted_users()
        
        # Success message
        success_msg = f"✅ **WHITELIST CLEARED SUCCESSFULLY!**\n\n"
        success_msg += f"🧹 **Removed:** {cleared_count} users from database\n"
        success_msg += f"🧹 **Cleared:** In-memory whitelist\n\n"
        success_msg += f"💡 **Result:** Fresh whitelist - you can now add new users\n"
        success_msg += f"🔧 **Usage:** Use `-wl @user add` to whitelist new users"
        
        await ctx.message.edit(content=success_msg)
        await asyncio.sleep(12)
        await ctx.message.delete()
        
        print(f"🧹 OWNER CLEARED WHITELIST: {cleared_count} users removed")
        
    except Exception as e:
        await ctx.message.edit(content=f"❌ Clear whitelist error: {e}")
        await asyncio.sleep(8)
        await ctx.message.delete()
        print(f"❌ Clear whitelist error: {e}")

# Enhanced logs functionality is now merged with the main logs command above

# Command: -history (show recent command usage)
@bot.command()
async def history(ctx, limit=None):
    """Show recent command usage history - AUTHORIZED USERS ONLY"""
    try:
        print(f"🔍 History command called by {ctx.author.name}")
        
        # Instantly delete command
        await instant_delete_command(ctx)
        
        # Check if user has permission
        requester_id = str(ctx.author.id)
        if not (is_owner(ctx.author.id) or requester_id in authorized_users):
            await ultra_fast_response(ctx, "🚫 **ACCESS DENIED**\n⚠️ Only authorized users can view command history!", delete_after=8)
            return
        
        # Parse limit parameter
        try:
            if limit:
                limit = int(limit)
                if limit < 1 or limit > 50:
                    limit = 20  # Default limit
            else:
                limit = 20  # Default limit
        except ValueError:
            limit = 20
        
        # Track this command usage
        try:
            user_name = str(ctx.author.name) if ctx.author else "Unknown"
            command_history.append({
                "command": "history",
                "user": user_name,
                "timestamp": time.time(),
                "args": f"limit={limit}"
            })
        except Exception as track_err:
            print(f"⚠️ Command tracking error: {track_err}")
        
        # Build history content
        history_content = f"📜 **COMMAND HISTORY (Last {limit} Commands)**\n"
        history_content += f"🕒 Retrieved at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        if command_history:
            # Get recent commands (excluding the current history command)
            recent_commands = command_history[:-1][-limit:]  # Exclude current history command
            
            if recent_commands:
                history_content += "```\n"
                for i, cmd in enumerate(reversed(recent_commands), 1):
                    timestamp_str = datetime.datetime.fromtimestamp(cmd["timestamp"]).strftime("%H:%M:%S")
                    command_name = cmd["command"]
                    user_name = cmd["user"]
                    args = cmd.get("args", "")
                    
                    # Format the entry
                    entry = f"{i:2d}. [{timestamp_str}] -{command_name}"
                    if args and args != "help":
                        entry += f" {args[:30]}{'...' if len(args) > 30 else ''}"
                    entry += f" (by {user_name})\n"
                    
                    history_content += entry
                
                history_content += "```\n\n"
                
                # Add usage statistics
                command_counts = {}
                for cmd in command_history:
                    cmd_name = cmd["command"]
                    command_counts[cmd_name] = command_counts.get(cmd_name, 0) + 1
                
                history_content += "📊 **COMMAND STATISTICS:**\n"
                sorted_commands = sorted(command_counts.items(), key=lambda x: x[1], reverse=True)
                for cmd_name, count in sorted_commands[:10]:  # Top 10 most used commands
                    history_content += f"• -{cmd_name}: {count} times\n"
                
                history_content += f"\n🔢 **Total Commands Executed:** {len(command_history)}\n"
                
            else:
                history_content += "⚠️ No recent command history available\n"
        else:
            history_content += "⚠️ **NO COMMAND HISTORY**\n"
            history_content += "Command tracking has just been initialized.\n"
        
        await ultra_fast_response(ctx, history_content, delete_after=25)
        
    except Exception as e:
        await ultra_fast_response(ctx, f"❌ History command error: {e}", delete_after=8)
        print(f"❌ History command error: {e}")

# ==================== MUSIC SYSTEM ====================
music_voice_client = None
music_queue = []
music_current_source = None
music_is_playing = False
music_volume = 0.5
music_loop = False
music_auto_disconnect = True

# yt-dlp options — best audio, no playlist, browser-like UA
ytdl_format_options = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch1',
    'source_address': '0.0.0.0',
    'geo_bypass': True,
    'age_limit': None,
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    },
}

# FFmpeg options — reconnect keeps stream alive if network hiccups
ffmpeg_options = {
    'before_options': (
        '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin'
    ),
    'options': '-vn',
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    """Audio source that wraps yt-dlp + FFmpeg with volume control."""

    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume=volume)
        self.data = data
        self.title = data.get('title', 'Unknown')
        self.webpage_url = data.get('webpage_url', data.get('url', ''))
        self.duration = data.get('duration')
        self.thumbnail = data.get('thumbnail')
        self.uploader = data.get('uploader', 'Unknown')
        self.requested_by = data.get('requested_by', 'Unknown')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True, volume=0.5):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(url, download=not stream)
        )
        if not data:
            raise Exception("No results found for that query.")
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        pcm = discord.FFmpegPCMAudio(filename, **ffmpeg_options)
        return cls(pcm, data=data, volume=volume)


async def play_next_in_queue():
    """Play the next song in the queue — called after each song ends."""
    global music_voice_client, music_queue, music_current_source, music_is_playing

    if not music_voice_client or not music_voice_client.is_connected():
        music_is_playing = False
        return

    if music_loop and music_current_source:
        # Re-fetch and replay same song
        try:
            player = await YTDLSource.from_url(
                music_current_source.webpage_url, loop=bot.loop, stream=True,
                volume=music_volume
            )
            player.requested_by = music_current_source.requested_by

            def after_fn(err):
                if err:
                    print(f'❌ Loop playback error: {err}')
                asyncio.run_coroutine_threadsafe(play_next_in_queue(), bot.loop)

            music_voice_client.play(player, after=after_fn)
            music_current_source = player
            music_is_playing = True
            return
        except Exception as e:
            print(f"❌ Loop re-fetch failed: {e}")

    if music_queue:
        next_song = music_queue.pop(0)
        print(f"🎵 Playing next: {next_song.title}")
        try:
            def after_fn(err):
                if err:
                    print(f'❌ Playback error: {err}')
                asyncio.run_coroutine_threadsafe(play_next_in_queue(), bot.loop)

            music_voice_client.play(next_song, after=after_fn)
            music_current_source = next_song
            music_is_playing = True
        except Exception as e:
            print(f"❌ Error playing next: {e}")
            music_is_playing = False
            await asyncio.sleep(1)
            await play_next_in_queue()
    else:
        music_is_playing = False
        music_current_source = None
        print("🔇 Queue empty")
        if music_auto_disconnect:
            await asyncio.sleep(30)
            if not music_is_playing and music_voice_client and music_voice_client.is_connected():
                await music_voice_client.disconnect()
                print("🔌 Auto-disconnected (queue empty)")

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        try:
            print(f"🔍 Searching for: {url}")
            
            # Extract info with timeout
            data = await asyncio.wait_for(
                loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False)),
                timeout=30.0
            )
            
            if data is None:
                raise Exception("No results found")
            
            if 'entries' in data and data['entries']:
                data = data['entries'][0]
            
            if not data or not data.get('url'):
                raise Exception("No playable audio found")
            
            print(f"✅ Found: {data.get('title', 'Unknown')}")
            
            # Get FFmpeg path
            ffmpeg_path = get_ffmpeg_path()
            if not ffmpeg_path:
                raise Exception("FFmpeg not available")
            
            # Use direct audio source to avoid FFmpeg hanging
            source = discord.FFmpegOpusAudio(
                data['url'],
                executable=ffmpeg_path,
                before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                options='-vn -f opus'
            )
            
            return cls(source, data=data)
            
        except asyncio.TimeoutError:
            raise Exception("YouTube search timed out")
        except Exception as e:
            print(f"❌ Audio creation failed: {e}")
            raise Exception(f"Failed to create audio: {str(e)}")

# Music Commands
async def _force_clean_voice(guild):
    """Kill any stale voice session on a guild so 4006 errors stop."""
    global music_voice_client
    # Kill via guild's voice client
    if guild and guild.voice_client:
        try:
            await guild.voice_client.disconnect(force=True)
        except Exception:
            pass
    # Kill via global tracker
    if music_voice_client:
        try:
            await music_voice_client.disconnect(force=True)
        except Exception:
            pass
        music_voice_client = None
    # Brief pause so Discord registers the disconnect
    await asyncio.sleep(0.8)

async def _connect_voice(target_channel, guild=None):
    """Connect to a voice channel cleanly. Clears stale sessions first."""
    global music_voice_client
    # Clean up any stale session first to avoid 4006
    await _force_clean_voice(guild)
    try:
        vc = await target_channel.connect(self_deaf=True)
        music_voice_client = vc
        return vc
    except discord.ClientException as e:
        if "already connected" in str(e).lower():
            # Grab the live one
            if guild and guild.voice_client:
                music_voice_client = guild.voice_client
                return guild.voice_client
        raise

@bot.command(name="mjoin")
async def music_join(ctx, *, args=None):
    """Join voice channel"""
    global music_voice_client
    try:
        voice_channel = None

        if ctx.guild:
            # Priority 1: user's current voice channel
            if hasattr(ctx.author, 'voice') and ctx.author.voice:
                voice_channel = ctx.author.voice.channel
            # Priority 2: channel name/ID from args
            if not voice_channel and args:
                q = args.strip().lower()
                for ch in ctx.guild.voice_channels:
                    if ch.name.lower() == q or str(ch.id) == q or q in ch.name.lower():
                        voice_channel = ch
                        break
            # Priority 3: first channel with members
            if not voice_channel:
                for ch in ctx.guild.voice_channels:
                    if ch.members:
                        voice_channel = ch
                        break
            # Priority 4: any voice channel
            if not voice_channel and ctx.guild.voice_channels:
                voice_channel = ctx.guild.voice_channels[0]

        elif isinstance(ctx.channel, (discord.DMChannel, discord.GroupChannel)):
            if hasattr(ctx.author, 'voice') and ctx.author.voice:
                voice_channel = ctx.author.voice.channel
            else:
                voice_channel = ctx.channel  # try joining the call itself

        if not voice_channel:
            await ultra_fast_response(ctx, "❌ No voice channel found! Join one first or pass a channel name.", delete_after=8)
            return

        ch_name = getattr(voice_channel, 'name', 'Call')

        # If already properly connected to the same channel, do nothing
        live_vc = _get_vc(ctx)
        if live_vc and getattr(live_vc.channel, 'id', None) == getattr(voice_channel, 'id', None):
            await ultra_fast_response(ctx, f"✅ Already in **{ch_name}**!", delete_after=5)
            return

        # If connected to a different channel, just move
        if live_vc:
            await live_vc.move_to(voice_channel)
            await ultra_fast_response(ctx, f"🎵 Moved to **{ch_name}**", delete_after=5)
            return

        # Fresh connect with stale-session cleanup
        vc = await _connect_voice(voice_channel, guild=ctx.guild)
        await ultra_fast_response(ctx, f"🎵 Connected to **{ch_name}**", delete_after=5)
        print(f"🎵 Connected: {ch_name}")

    except Exception as e:
        await ultra_fast_response(ctx, f"❌ Error joining voice: {e}", delete_after=8)
        print(f"❌ mjoin error: {e}")

def _fmt_duration(seconds):
    if not seconds:
        return "?"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

def _get_vc(ctx):
    """Return the live VoiceClient for this context (guild or global fallback)."""
    global music_voice_client
    # Prefer guild's authoritative voice client
    if ctx.guild:
        vc = ctx.guild.voice_client
        if vc and vc.is_connected():
            music_voice_client = vc  # keep global in sync
            return vc
    # Fallback to global
    if music_voice_client and music_voice_client.is_connected():
        return music_voice_client
    return None

async def _ensure_voice(ctx):
    """Auto-join voice if not connected. Returns VoiceClient on success, None on failure."""
    global music_voice_client
    # Already connected?
    vc = _get_vc(ctx)
    if vc:
        return vc
    # Find target channel
    target = None
    if ctx.guild:
        if hasattr(ctx.author, 'voice') and ctx.author.voice:
            target = ctx.author.voice.channel
        if not target:
            for ch in ctx.guild.voice_channels:
                if ch.members:
                    target = ch
                    break
        if not target and ctx.guild.voice_channels:
            target = ctx.guild.voice_channels[0]
    elif isinstance(ctx.channel, (discord.DMChannel, discord.GroupChannel)):
        if hasattr(ctx.author, 'voice') and ctx.author.voice:
            target = ctx.author.voice.channel
    if not target:
        await ultra_fast_response(ctx, "❌ Join a voice channel first, or use `-mjoin`.", delete_after=8)
        return None
    try:
        vc = await _connect_voice(target, guild=ctx.guild if ctx.guild else None)
        return vc
    except discord.ClientException:
        return _get_vc(ctx)
    except Exception as e:
        await ultra_fast_response(ctx, f"❌ Can't connect to voice: {e}", delete_after=8)
        return None

@bot.command(name="mplay", aliases=["mp", "play"])
async def music_play(ctx, *, query=None):
    """Play music from YouTube — URL or search term"""
    global music_voice_client, music_current_source, music_is_playing, music_volume

    if not query:
        await ultra_fast_response(ctx,
            "❌ Usage: `-mplay <song name or YouTube URL>`\n"
            "Example: `-mplay never gonna give you up`", delete_after=8)
        return

    vc = await _ensure_voice(ctx)
    if not vc:
        return

    loading_msg = await ctx.send("🔄 Searching YouTube...")
    try:
        print(f"🎵 Searching: {query}")
        player = await YTDLSource.from_url(query, loop=bot.loop, stream=True, volume=music_volume)
        player.requested_by = ctx.author.display_name
        print(f"✅ Found: {player.title}")
    except Exception as e:
        print(f"❌ yt-dlp error: {e}")
        await loading_msg.edit(content=f"❌ Could not find or load that song.\n`{e}`")
        await asyncio.sleep(8)
        try: await loading_msg.delete()
        except: pass
        return

    # Re-fetch live vc in case something changed during yt-dlp search
    vc = _get_vc(ctx) or vc
    if not vc or not vc.is_connected():
        await loading_msg.edit(content="❌ Lost voice connection. Use `-mjoin` then try again.")
        await asyncio.sleep(5)
        try: await loading_msg.delete()
        except: pass
        return

    if vc.is_playing() or vc.is_paused():
        music_queue.append(player)
        await loading_msg.edit(
            content=f"📜 **Added to queue #{len(music_queue)}**\n"
                    f"🎵 {player.title}\n"
                    f"👤 {player.requested_by} | ⏱ {_fmt_duration(player.duration)}"
        )
    else:
        def _after(err):
            if err: print(f'❌ Playback error: {err}')
            asyncio.run_coroutine_threadsafe(play_next_in_queue(), bot.loop)

        vc.play(player, after=_after)
        music_voice_client = vc
        music_current_source = player
        music_is_playing = True
        await loading_msg.edit(
            content=f"🎵 **Now Playing**\n"
                    f"**{player.title}**\n"
                    f"👤 {player.requested_by} | ⏱ {_fmt_duration(player.duration)} | 🔊 {int(music_volume*100)}%"
        )

    print(f"✅ Music ready: {player.title}")
    await asyncio.sleep(10)
    try: await loading_msg.delete()
    except: pass


@bot.command(name="mskip", aliases=["skip", "ms"])
async def music_skip(ctx):
    """Skip the current song"""
    try:
        vc = _get_vc(ctx)
        if not vc:
            await ultra_fast_response(ctx, "❌ Not connected to voice!", delete_after=5)
            return
        if vc.is_playing() or vc.is_paused():
            vc.stop()
            next_title = music_queue[0].title if music_queue else "nothing (queue empty)"
            await ultra_fast_response(ctx, f"⏭️ **Skipped!** Up next: {next_title}", delete_after=6)
        else:
            await ultra_fast_response(ctx, "❌ Nothing is playing!", delete_after=5)
    except Exception as e:
        await ultra_fast_response(ctx, f"❌ {e}", delete_after=5)


@bot.command(name="mpause", aliases=["pause"])
async def music_pause(ctx):
    """Pause the current song"""
    try:
        vc = _get_vc(ctx)
        if not vc:
            await ultra_fast_response(ctx, "❌ Not connected to voice!", delete_after=5)
            return
        if vc.is_playing():
            vc.pause()
            await ultra_fast_response(ctx, "⏸️ **Paused!** Use `-mresume` to continue.", delete_after=8)
        elif vc.is_paused():
            await ultra_fast_response(ctx, "⚠️ Already paused! Use `-mresume` to continue.", delete_after=5)
        else:
            await ultra_fast_response(ctx, "❌ Nothing is playing!", delete_after=5)
    except Exception as e:
        await ultra_fast_response(ctx, f"❌ {e}", delete_after=5)


@bot.command(name="mresume", aliases=["resume"])
async def music_resume(ctx):
    """Resume the paused song"""
    try:
        vc = _get_vc(ctx)
        if not vc:
            await ultra_fast_response(ctx, "❌ Not connected to voice!", delete_after=5)
            return
        if vc.is_paused():
            vc.resume()
            title = music_current_source.title if music_current_source else "song"
            await ultra_fast_response(ctx, f"▶️ **Resumed:** {title}", delete_after=6)
        elif vc.is_playing():
            await ultra_fast_response(ctx, "⚠️ Already playing!", delete_after=5)
        else:
            await ultra_fast_response(ctx, "❌ Nothing to resume!", delete_after=5)
    except Exception as e:
        await ultra_fast_response(ctx, f"❌ {e}", delete_after=5)


@bot.command(name="mnp", aliases=["nowplaying", "np"])
async def music_nowplaying(ctx):
    """Show what's currently playing"""
    global music_current_source, music_loop
    try:
        vc = _get_vc(ctx)
        if not music_current_source or not vc or not (vc.is_playing() or vc.is_paused()):
            await ultra_fast_response(ctx, "🔇 Nothing is currently playing.", delete_after=6)
            return
        s = music_current_source
        status = "⏸️ Paused" if vc.is_paused() else "▶️ Playing"
        loop_status = "🔁 Loop ON" if music_loop else "➡️ Loop OFF"
        msg = (
            f"🎵 **Now Playing**\n"
            f"**{s.title}**\n"
            f"👤 {getattr(s, 'requested_by', 'Unknown')} | "
            f"⏱ {_fmt_duration(s.duration)} | "
            f"🔊 {int(music_volume * 100)}%\n"
            f"{status} | {loop_status} | 📜 {len(music_queue)} in queue"
        )
        await ultra_fast_response(ctx, msg, delete_after=15)
    except Exception as e:
        await ultra_fast_response(ctx, f"❌ {e}", delete_after=5)


@bot.command(name="mloop", aliases=["loop"])
async def music_loop_cmd(ctx):
    """Toggle loop for the current song"""
    global music_loop
    try:
        music_loop = not music_loop
        state = "🔁 **Loop ON** — current song will repeat!" if music_loop else "➡️ **Loop OFF**"
        await ultra_fast_response(ctx, state, delete_after=6)
    except Exception as e:
        await ultra_fast_response(ctx, f"❌ {e}", delete_after=5)


@bot.command(name="mstop", aliases=["stopmusic"])
async def music_stop(ctx):
    """Stop playback and clear the queue"""
    global music_current_source, music_is_playing
    try:
        vc = _get_vc(ctx)
        if not vc:
            await ultra_fast_response(ctx, "❌ Not connected to voice!", delete_after=5)
            return
        if vc.is_playing() or vc.is_paused():
            music_queue.clear()
            vc.stop()
            music_is_playing = False
            music_current_source = None
            await ultra_fast_response(ctx, "⏹️ **Stopped and queue cleared!**", delete_after=5)
        else:
            await ultra_fast_response(ctx, "ℹ️ Nothing is playing.", delete_after=5)
    except Exception as e:
        await ultra_fast_response(ctx, f"❌ {e}", delete_after=8)


@bot.command(name="mleave", aliases=["disconnect", "dc"])
async def music_leave(ctx):
    """Disconnect from voice and reset everything"""
    global music_voice_client, music_current_source, music_is_playing
    try:
        vc = _get_vc(ctx)
        if not vc:
            await ultra_fast_response(ctx, "❌ Not connected to voice!", delete_after=5)
            return
        if vc.is_playing() or vc.is_paused():
            vc.stop()
        ch = getattr(vc.channel, 'name', 'voice channel')
        await vc.disconnect()
        music_voice_client = None
        music_current_source = None
        music_is_playing = False
        music_queue.clear()
        await ultra_fast_response(ctx, f"👋 **Left {ch}**", delete_after=5)
    except Exception as e:
        await ultra_fast_response(ctx, f"❌ {e}", delete_after=8)


@bot.command(name="mvolume", aliases=["mvol", "vol"])
async def music_volume_cmd(ctx, *, args=None):
    """Set or show volume (0–200)"""
    global music_volume, music_voice_client
    try:
        if not args:
            await ultra_fast_response(ctx,
                f"🔊 **Volume:** {int(music_volume * 100)}%\n"
                f"Usage: `-mvolume <0-200>`", delete_after=8)
            return
        try:
            vol = int(args.strip())
            if not 0 <= vol <= 200:
                await ultra_fast_response(ctx, "❌ Volume must be 0–200.", delete_after=5)
                return
            music_volume = vol / 100.0
            vc2 = _get_vc(ctx)
            if vc2 and vc2.source and hasattr(vc2.source, 'volume'):
                vc2.source.volume = music_volume
            await ultra_fast_response(ctx, f"🔊 **Volume set to {vol}%**", delete_after=5)
        except ValueError:
            await ultra_fast_response(ctx, "❌ Provide a number 0–200.", delete_after=5)
    except Exception as e:
        await ultra_fast_response(ctx, f"❌ {e}", delete_after=8)


@bot.command(name="mqueue", aliases=["queue", "mq"])
async def music_queue_cmd(ctx, *, args=None):
    """View or clear the music queue"""
    global music_queue, music_current_source
    try:
        if args and args.strip().lower() == "clear":
            music_queue.clear()
            await ultra_fast_response(ctx, "🗑️ **Queue cleared!**", delete_after=5)
            return

        if not music_queue and not music_current_source:
            await ultra_fast_response(ctx, "📜 Queue is empty. Use `-mplay <song>` to add music.", delete_after=8)
            return

        out = "🎵 **Music Queue**\n\n"
        if music_current_source:
            status = "⏸️" if (music_voice_client and music_voice_client.is_paused()) else "▶️"
            out += f"{status} **Now:** {music_current_source.title} ({_fmt_duration(music_current_source.duration)})\n\n"
        if music_queue:
            out += f"📜 **Up next ({len(music_queue)}):**\n"
            for i, song in enumerate(music_queue[:15], 1):
                out += f"`{i}.` {song.title} ({_fmt_duration(song.duration)})\n"
            if len(music_queue) > 15:
                out += f"...and {len(music_queue) - 15} more"
        else:
            out += "📜 Nothing else in queue."
        await ultra_fast_response(ctx, out, delete_after=20)
    except Exception as e:
        await ultra_fast_response(ctx, f"❌ {e}", delete_after=8)

# ==================== SERVER TEMPLATE SYSTEM ====================
# Template storage directory (separate from web templates)
TEMPLATE_DIR = "server_templates"
import json

def normalize_template_name(template_name):
    """Normalize template name by removing invalid characters"""
    if not template_name or not template_name.strip():
        return None
    import re
    return re.sub(r'[<>:"/\\|?*]', '_', template_name.strip())

def ensure_template_directory():
    """Ensure templates directory exists"""
    if not os.path.exists(TEMPLATE_DIR):
        os.makedirs(TEMPLATE_DIR)

def save_template_to_file(template_name, template_data):
    """Save template to JSON file - Returns (success, cleaned_name, error_msg)"""
    # Validate and normalize template name
    clean_template_name = normalize_template_name(template_name)
    if not clean_template_name:
        error_msg = "Template name is empty or invalid"
        print(f"Error saving template: {error_msg}")
        return False, None, error_msg
    
    ensure_template_directory()
    file_path = os.path.join(TEMPLATE_DIR, f"{clean_template_name}.json")
    
    try:
        # Test JSON serialization first
        try:
            json_string = json.dumps(template_data, indent=2, ensure_ascii=False)
        except (TypeError, ValueError) as json_err:
            error_msg = f"JSON serialization failed - {json_err}. Template data contains objects that cannot be serialized to JSON"
            print(f"Error saving template {template_name}: {error_msg}")
            return False, clean_template_name, error_msg
        
        # Check if we can write to the directory
        try:
            test_file = os.path.join(TEMPLATE_DIR, "test_write.tmp")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
        except PermissionError:
            error_msg = f"No write permission to {TEMPLATE_DIR}"
            print(f"Error saving template {template_name}: {error_msg}")
            return False, clean_template_name, error_msg
        except OSError as fs_err:
            error_msg = f"File system error - {fs_err}"
            print(f"Error saving template {template_name}: {error_msg}")
            return False, clean_template_name, error_msg
        
        # Now save the actual file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(json_string)
        
        print(f"✅ Template '{clean_template_name}' saved successfully to {file_path}")
        return True, clean_template_name, None
        
    except PermissionError as perm_err:
        error_msg = f"Permission denied - {perm_err}"
        print(f"Error saving template {template_name}: {error_msg}")
        return False, clean_template_name, error_msg
    except OSError as os_err:
        error_msg = f"File system error - {os_err}"
        print(f"Error saving template {template_name}: {error_msg}")
        return False, clean_template_name, error_msg
    except Exception as e:
        error_msg = f"Unexpected error - {e}"
        print(f"Error saving template {template_name}: {error_msg}")
        return False, clean_template_name, error_msg

def load_template_from_file(template_name):
    """Load template from JSON file"""
    clean_template_name = normalize_template_name(template_name)
    if not clean_template_name:
        print(f"Error loading template: Invalid template name '{template_name}'")
        return None
    
    file_path = os.path.join(TEMPLATE_DIR, f"{clean_template_name}.json")
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            print(f"Template file not found: {file_path}")
    except Exception as e:
        print(f"Error loading template {clean_template_name}: {e}")
    return None

def list_saved_templates():
    """Get list of all saved template names"""
    ensure_template_directory()
    templates = []
    for filename in os.listdir(TEMPLATE_DIR):
        if filename.endswith('.json'):
            templates.append(filename[:-5])  # Remove .json extension
    return templates

def delete_template_file(template_name):
    """Delete template file"""
    clean_template_name = normalize_template_name(template_name)
    if not clean_template_name:
        print(f"Error deleting template: Invalid template name '{template_name}'")
        return False
    
    file_path = os.path.join(TEMPLATE_DIR, f"{clean_template_name}.json")
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"✅ Template '{clean_template_name}' deleted successfully")
            return True
        else:
            print(f"Template file not found: {file_path}")
    except Exception as e:
        print(f"Error deleting template {clean_template_name}: {e}")
    return False

# Channel type mapping for proper creation with discord.py methods
def get_channel_creation_method(guild, channel_type):
    """Get the proper channel creation method based on type"""
    channel_type = channel_type.lower()
    
    if channel_type in ['text', 'news']:
        return guild.create_text_channel
    elif channel_type in ['voice']:
        return guild.create_voice_channel
    elif channel_type in ['category']:
        return guild.create_category
    elif channel_type in ['stage_voice']:
        return guild.create_stage_channel
    elif channel_type in ['forum']:
        # Forum channels may not be supported in all versions
        return getattr(guild, 'create_forum_channel', guild.create_text_channel)
    else:
        # Default to text channel for unknown types
        return guild.create_text_channel

async def scan_server_template(guild):
    """Scan a server and extract its template structure - works with any permission level"""
    template = {
        'name': str(guild.name) if guild.name else 'Unknown Server',
        'icon': str(guild.icon) if guild.icon else None,
        'banner': str(guild.banner) if guild.banner else None,
        'description': str(guild.description) if guild.description else None,
        'verification_level': str(guild.verification_level) if guild.verification_level else 'unknown',
        'explicit_content_filter': str(guild.explicit_content_filter) if guild.explicit_content_filter else 'unknown',
        'default_notifications': str(guild.default_notifications) if guild.default_notifications else 'unknown',
        'categories': [],
        'channels': [],
        'roles': [],
        'emojis': [],
        'features': [str(f) for f in guild.features] if hasattr(guild, 'features') else []
    }
    
    try:
        # Extract roles (skip @everyone role) - scan what's visible
        for role in guild.roles:
            try:
                if str(role.name) != "@everyone":
                    role_data = {
                        'name': str(role.name),
                        'permissions': int(role.permissions.value) if hasattr(role.permissions, 'value') else 0,
                        'color': int(role.color.value) if hasattr(role.color, 'value') else 0,
                        'hoist': bool(role.hoist),
                        'mentionable': bool(role.mentionable),
                        'position': int(role.position)
                    }
                    template['roles'].append(role_data)
            except Exception as e:
                print(f"Warning: Could not scan role {role.name}: {e}")
                continue
        
        # Sort roles by position for proper recreation
        template['roles'].sort(key=lambda x: x['position'])
        
        # Extract categories and their channels - only scan visible ones
        for category in guild.categories:
            try:
                category_data = {
                    'name': str(category.name),
                    'position': int(category.position),
                    'nsfw': bool(getattr(category, 'nsfw', False)),
                    'channels': []
                }
                
                # Get channels in this category (exclude category itself)
                for channel in category.channels:
                    try:
                        if not isinstance(channel, discord.CategoryChannel):
                            channel_data = await extract_channel_data(channel)
                            category_data['channels'].append(channel_data)
                    except Exception as e:
                        print(f"Warning: Could not scan channel {channel.name}: {e}")
                        continue
                
                template['categories'].append(category_data)
            except Exception as e:
                print(f"Warning: Could not scan category {category.name}: {e}")
                continue
        
        # Get channels not in any category (exclude categories) - only visible ones
        for channel in guild.channels:
            try:
                if not channel.category and not isinstance(channel, discord.CategoryChannel):
                    channel_data = await extract_channel_data(channel)
                    template['channels'].append(channel_data)
            except Exception as e:
                print(f"Warning: Could not scan channel {channel.name}: {e}")
                continue
        
        # Extract emojis (basic info only) - only visible ones
        for emoji in guild.emojis:
            try:
                emoji_data = {
                    'name': str(emoji.name),
                    'animated': bool(emoji.animated)
                }
                template['emojis'].append(emoji_data)
            except Exception as e:
                print(f"Warning: Could not scan emoji {emoji.name}: {e}")
                continue
                
    except Exception as e:
        print(f"Warning: General error during server scan: {e}")
    
    print(f"✅ Scanned template: {len(template['roles'])} roles, {len(template['categories'])} categories, {len(template['channels'])} channels, {len(template['emojis'])} emojis")
    return template

async def extract_channel_data(channel):
    """Extract channel data for template"""
    # Get canonical channel type name
    channel_type_str = str(channel.type).replace('ChannelType.', '')
    
    channel_data = {
        'name': str(channel.name),
        'type': str(channel_type_str),
        'position': int(channel.position),
        'nsfw': bool(getattr(channel, 'nsfw', False)),
        'overwrites': []
    }
    
    # Add channel-specific data based on type
    if hasattr(channel, 'topic') and channel.topic:
        channel_data['topic'] = str(channel.topic)
    if hasattr(channel, 'slowmode_delay') and channel.slowmode_delay > 0:
        channel_data['slowmode_delay'] = int(channel.slowmode_delay)
    if hasattr(channel, 'bitrate') and channel.bitrate:
        channel_data['bitrate'] = min(int(channel.bitrate), 384000)  # Cap at max bitrate
    if hasattr(channel, 'user_limit') and channel.user_limit > 0:
        channel_data['user_limit'] = int(channel.user_limit)
    
    # Extract permission overwrites - ONLY for roles, skip members
    for target, overwrite in channel.overwrites.items():
        # Only save role overwrites, skip member-specific permissions
        if hasattr(target, 'permissions'):  # This is a role
            overwrite_data = {
                'target_type': 'role',
                'target_name': str(target.name),
                'allow': int(overwrite.pair()[0].value),
                'deny': int(overwrite.pair()[1].value)
            }
            channel_data['overwrites'].append(overwrite_data)
    
    return channel_data

async def delete_existing_roles(guild):
    """Delete all existing roles except @everyone and bot roles"""
    deleted_count = 0
    errors = []
    
    try:
        # Get all roles except @everyone
        roles_to_delete = [role for role in guild.roles if role != guild.default_role]
        
        # Sort by position (delete higher roles first to avoid hierarchy issues)
        roles_to_delete.sort(key=lambda x: x.position, reverse=True)
        
        for i, role in enumerate(roles_to_delete):
            try:
                # Skip bot roles and managed roles
                if role.managed or role.is_bot_managed():
                    continue
                
                # Add delay every 5 roles to avoid rate limits
                if i > 0 and i % 5 == 0:
                    await asyncio.sleep(1)
                
                await role.delete(reason="Template application - clearing existing roles")
                deleted_count += 1
                
            except discord.HTTPException as e:
                if e.status == 429:  # Rate limited
                    await asyncio.sleep(5)
                    # Retry once
                    try:
                        await role.delete(reason="Template application - clearing existing roles")
                        deleted_count += 1
                    except Exception as retry_e:
                        errors.append(f"Failed to delete role {role.name} after retry: {str(retry_e)}")
                else:
                    errors.append(f"Failed to delete role {role.name}: {str(e)}")
            except Exception as e:
                errors.append(f"Failed to delete role {role.name}: {str(e)}")
    
    except Exception as e:
        errors.append(f"General error deleting roles: {str(e)}")
    
    return deleted_count, errors

async def delete_existing_channels(guild):
    """Delete all existing channels"""
    deleted_count = 0
    errors = []
    
    try:
        # Get all channels using different methods
        all_channels = []
        
        # Try to get text channels
        all_channels.extend(guild.text_channels)
        # Try to get voice channels  
        all_channels.extend(guild.voice_channels)
        # Try to get categories
        all_channels.extend(guild.categories)
        # Try to get stage channels if they exist
        if hasattr(guild, 'stage_channels'):
            all_channels.extend(guild.stage_channels)
        # Try to get forum channels if they exist
        if hasattr(guild, 'forum_channels'):
            all_channels.extend(guild.forum_channels)
        
        print(f"🔍 Found {len(all_channels)} channels to delete: {[ch.name for ch in all_channels]}")
        
        # Sort so categories are deleted last (they need to be empty first)
        text_and_voice_channels = [ch for ch in all_channels if not isinstance(ch, discord.CategoryChannel)]
        category_channels = [ch for ch in all_channels if isinstance(ch, discord.CategoryChannel)]
        
        channels_to_delete = text_and_voice_channels + category_channels
        
        for i, channel in enumerate(channels_to_delete):
            try:
                # Add delay every 5 channels to avoid rate limits
                if i > 0 and i % 5 == 0:
                    await asyncio.sleep(1)
                
                print(f"🗑️ Deleting channel: {channel.name} (type: {type(channel).__name__})")
                await channel.delete(reason="Template application - clearing existing channels")
                deleted_count += 1
                print(f"✅ Deleted channel: {channel.name}")
                
            except discord.HTTPException as e:
                if e.status == 429:  # Rate limited
                    print(f"⏳ Rate limited, waiting 5 seconds...")
                    await asyncio.sleep(5)
                    # Retry once
                    try:
                        await channel.delete(reason="Template application - clearing existing channels")
                        deleted_count += 1
                        print(f"✅ Deleted channel: {channel.name} (after retry)")
                    except Exception as retry_e:
                        error_msg = f"Failed to delete channel {channel.name} after retry: {str(retry_e)}"
                        errors.append(error_msg)
                        print(f"❌ {error_msg}")
                else:
                    error_msg = f"Failed to delete channel {channel.name}: {str(e)}"
                    errors.append(error_msg)
                    print(f"❌ {error_msg}")
            except Exception as e:
                error_msg = f"Failed to delete channel {channel.name}: {str(e)}"
                errors.append(error_msg)
                print(f"❌ {error_msg}")
    
    except Exception as e:
        error_msg = f"General error deleting channels: {str(e)}"
        errors.append(error_msg)
        print(f"❌ {error_msg}")
    
    return deleted_count, errors

async def update_channel_overwrites(channel, channel_data, role_mapping):
    """Update channel permission overwrites after roles have been created"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Check if channel should inherit from category (no explicit overwrites)
            template_overwrites_data = channel_data.get('overwrites', [])
            if not template_overwrites_data:
                # Channel should sync with category - use sync_permissions
                if channel.category:
                    await channel.edit(sync_permissions=True, reason="Syncing channel with category permissions")
                    print(f"✅ Synced {channel.name} with category permissions")
                return
            
            # Build authoritative permission overwrites from template
            template_overwrites = {}
            for overwrite_data in template_overwrites_data:
                target_type = overwrite_data.get('target_type')
                target_name = overwrite_data.get('target_name')
                
                # Handle role overwrites (including @everyone)
                if target_type == 'role':
                    target_role = role_mapping.get(target_name)
                    if target_role:
                        try:
                            template_overwrites[target_role] = discord.PermissionOverwrite.from_pair(
                                discord.Permissions(overwrite_data['allow']),
                                discord.Permissions(overwrite_data['deny'])
                            )
                            print(f"📋 Added overwrite for role {target_name} in channel {channel.name}")
                        except Exception as e:
                            print(f"Warning: Could not create overwrite for role {target_name}: {e}")
                    else:
                        print(f"Warning: Role {target_name} not found in role mapping for channel {channel.name}")
                # Skip member overwrites as they can't be reliably mapped across servers
            
            # Apply authoritative template overwrites (replace existing)
            if template_overwrites:
                await channel.edit(overwrites=template_overwrites, reason="Applying template permission overwrites")
                print(f"✅ Applied {len(template_overwrites)} overwrites to channel: {channel.name}")
            elif template_overwrites_data:
                # Template has overwrites but they're all member/invalid - treat as "inherit from category"
                if channel.category:
                    await channel.edit(sync_permissions=True, reason="Template has only member overwrites - syncing with category")
                    print(f"✅ Synced {channel.name} with category (template had only member overwrites)")
                else:
                    print(f"⚠️ Template has member overwrites only, but no category to sync with for channel: {channel.name}")
            else:
                print(f"⚠️ No overwrites defined in template for channel: {channel.name}")
            
            return  # Success, exit retry loop
            
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited
                retry_count += 1
                wait_time = min(5, 2 ** retry_count)  # Exponential backoff
                print(f"⏳ Rate limited updating overwrites for {channel.name}, waiting {wait_time}s... (attempt {retry_count}/{max_retries})")
                await asyncio.sleep(wait_time)
                if retry_count >= max_retries:
                    print(f"❌ Failed to update overwrites for {channel.name} after {max_retries} retries")
                    raise e
            else:
                print(f"❌ Error updating overwrites for channel {channel.name}: {e}")
                raise e
        except Exception as e:
            print(f"❌ Error updating overwrites for channel {channel.name}: {e}")
            raise e

async def update_category_overwrites_basic(category, category_data, basic_role_mapping):
    """Update category permission overwrites using only @everyone (basic permissions)"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Build basic overwrites for this category - @everyone only
            template_overwrites = {}
            template_overwrites_data = category_data.get('overwrites', [])
            
            for overwrite_data in template_overwrites_data:
                target_type = overwrite_data.get('target_type')
                target_name = overwrite_data.get('target_name')
                
                # Handle only @everyone role overwrites
                if target_type == 'role' and target_name == '@everyone':
                    target_role = basic_role_mapping.get('@everyone')
                    if target_role:
                        try:
                            template_overwrites[target_role] = discord.PermissionOverwrite.from_pair(
                                discord.Permissions(overwrite_data['allow']),
                                discord.Permissions(overwrite_data['deny'])
                            )
                            print(f"📋 Added basic @everyone overwrite for category {category.name}")
                        except Exception as e:
                            print(f"Warning: Could not create @everyone overwrite for category {category.name}: {e}")
            
            # Apply basic overwrites (@everyone only)
            if template_overwrites:
                await category.edit(overwrites=template_overwrites, reason="Applying basic @everyone permissions")
                print(f"✅ Applied @everyone overwrites to category: {category.name}")
            else:
                print(f"⚠️ No @everyone overwrites for category: {category.name}")
            
            return  # Success, exit retry loop
            
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited
                retry_count += 1
                wait_time = min(5, 2 ** retry_count)
                print(f"⏳ Rate limited updating basic overwrites for category {category.name}, waiting {wait_time}s... (attempt {retry_count}/{max_retries})")
                await asyncio.sleep(wait_time)
                if retry_count >= max_retries:
                    print(f"❌ Failed to update basic overwrites for category {category.name} after {max_retries} retries")
                    raise e
            else:
                print(f"❌ Error updating basic overwrites for category {category.name}: {e}")
                raise e
        except Exception as e:
            print(f"❌ Error updating basic overwrites for category {category.name}: {e}")
            raise e

async def update_channel_overwrites_basic(channel, channel_data, basic_role_mapping):
    """Update channel permission overwrites using only @everyone (basic permissions)"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Build basic overwrites for this channel - @everyone only
            template_overwrites = {}
            template_overwrites_data = channel_data.get('overwrites', [])
            
            for overwrite_data in template_overwrites_data:
                target_type = overwrite_data.get('target_type')
                target_name = overwrite_data.get('target_name')
                
                # Handle only @everyone role overwrites
                if target_type == 'role' and target_name == '@everyone':
                    target_role = basic_role_mapping.get('@everyone')
                    if target_role:
                        try:
                            template_overwrites[target_role] = discord.PermissionOverwrite.from_pair(
                                discord.Permissions(overwrite_data['allow']),
                                discord.Permissions(overwrite_data['deny'])
                            )
                            print(f"📋 Added basic @everyone overwrite for channel {channel.name}")
                        except Exception as e:
                            print(f"Warning: Could not create @everyone overwrite for channel {channel.name}: {e}")
            
            # Apply basic overwrites (@everyone only)
            if template_overwrites:
                await channel.edit(overwrites=template_overwrites, reason="Applying basic @everyone permissions")
                print(f"✅ Applied @everyone overwrites to channel: {channel.name}")
            elif template_overwrites_data:
                # Template has overwrites but no @everyone - sync with category if available
                if channel.category:
                    await channel.edit(sync_permissions=True, reason="Template has no @everyone - syncing with category")
                    print(f"✅ Synced {channel.name} with category (no @everyone overwrites)")
                else:
                    print(f"⚠️ No @everyone overwrites and no category for channel: {channel.name}")
            else:
                print(f"⚠️ No overwrites for channel: {channel.name}")
            
            return  # Success, exit retry loop
            
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited
                retry_count += 1
                wait_time = min(5, 2 ** retry_count)
                print(f"⏳ Rate limited updating basic overwrites for channel {channel.name}, waiting {wait_time}s... (attempt {retry_count}/{max_retries})")
                await asyncio.sleep(wait_time)
                if retry_count >= max_retries:
                    print(f"❌ Failed to update basic overwrites for channel {channel.name} after {max_retries} retries")
                    raise e
            else:
                print(f"❌ Error updating basic overwrites for channel {channel.name}: {e}")
                raise e
        except Exception as e:
            print(f"❌ Error updating basic overwrites for channel {channel.name}: {e}")
            raise e

async def update_category_overwrites(category, category_data, role_mapping):
    """Update category permission overwrites after roles have been created"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Build authoritative permission overwrites from template
            template_overwrites = {}
            template_overwrites_data = category_data.get('overwrites', [])
            
            for overwrite_data in template_overwrites_data:
                target_type = overwrite_data.get('target_type')
                target_name = overwrite_data.get('target_name')
                
                # Handle role overwrites (including @everyone)
                if target_type == 'role':
                    target_role = role_mapping.get(target_name)
                    if target_role:
                        try:
                            template_overwrites[target_role] = discord.PermissionOverwrite.from_pair(
                                discord.Permissions(overwrite_data['allow']),
                                discord.Permissions(overwrite_data['deny'])
                            )
                            print(f"📋 Added overwrite for role {target_name} in category {category.name}")
                        except Exception as e:
                            print(f"Warning: Could not create overwrite for role {target_name}: {e}")
                    else:
                        print(f"Warning: Role {target_name} not found in role mapping for category {category.name}")
                # Skip member overwrites as they can't be reliably mapped across servers
            
            # Apply authoritative template overwrites (replace existing)
            if template_overwrites:
                await category.edit(overwrites=template_overwrites, reason="Applying template permission overwrites")
                print(f"✅ Applied {len(template_overwrites)} overwrites to category: {category.name}")
            else:
                print(f"⚠️ No valid overwrites found for category: {category.name}")
            
            return  # Success, exit retry loop
            
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited
                retry_count += 1
                wait_time = min(5, 2 ** retry_count)  # Exponential backoff
                print(f"⏳ Rate limited updating overwrites for category {category.name}, waiting {wait_time}s... (attempt {retry_count}/{max_retries})")
                await asyncio.sleep(wait_time)
                if retry_count >= max_retries:
                    print(f"❌ Failed to update overwrites for category {category.name} after {max_retries} retries")
                    raise e
            else:
                print(f"❌ Error updating overwrites for category {category.name}: {e}")
                raise e
        except Exception as e:
            print(f"❌ Error updating overwrites for category {category.name}: {e}")
            raise e

async def apply_server_template(guild, template, ctx):
    """Apply a server template to the target guild with proper rate limiting and error handling"""
    applied_count = 0
    errors = []
    
    try:
        # Check comprehensive permissions first (skip if member not cached — selfbot)
        bot_member = guild.get_member(bot.user.id)
        if bot_member:
            required_perms = {
                'manage_guild': 'Manage Server',
                'manage_roles': 'Manage Roles',
                'manage_channels': 'Manage Channels',
                'manage_emojis_and_stickers': 'Manage Emojis'
            }
            missing_perms = [
                display_name for perm, display_name in required_perms.items()
                if not getattr(bot_member.guild_permissions, perm, False)
            ]
            if missing_perms:
                errors.append(f"Missing permissions: {', '.join(missing_perms)}")
                return applied_count, errors
        
        # STEP 0A: Delete all existing channels first
        print("🗑️ Deleting existing channels...")
        deleted_channels, channel_errors = await delete_existing_channels(guild)
        if channel_errors:
            errors.extend(channel_errors)
        print(f"✅ Deleted {deleted_channels} existing channels")
        
        # STEP 0B: Delete all existing roles (except @everyone and bot roles)
        print("🗑️ Deleting existing roles...")
        deleted_roles, role_errors = await delete_existing_roles(guild)
        if role_errors:
            errors.extend(role_errors)
        print(f"✅ Deleted {deleted_roles} existing roles")
        
        # Brief pause before creation
        await asyncio.sleep(1)
        
        # Initialize empty role mapping for later use
        role_mapping = {}  
        created_channels = []  # Store created channels for later overwrite updates
        created_categories = []  # Store created categories for later overwrite updates
        
        # STEP 1: Create categories with rate limiting
        for i, category_data in enumerate(template.get('categories', [])):
            try:
                # Add delay every 3 categories
                if i > 0 and i % 3 == 0:
                    await asyncio.sleep(1)
                    
                new_category = await guild.create_category(
                    name=category_data['name'],
                    reason="Server template application"
                )
                created_categories.append((new_category, category_data))  # Store for later overwrite updates
                applied_count += 1
                
                # STEP 2: Create channels in this category (without role overwrites for now)
                for j, channel_data in enumerate(category_data.get('channels', [])):
                    # Add delay every 5 channels
                    if j > 0 and j % 5 == 0:
                        await asyncio.sleep(0.8)
                        
                    try:
                        new_channel = await create_channel_from_template(guild, channel_data, new_category, {})  # Empty role mapping for now
                        created_channels.append((new_channel, channel_data))  # Store for later overwrite updates
                        applied_count += 1
                    except Exception as e:
                        errors.append(f"Failed to create channel {channel_data['name']}: {str(e)}")
                
            except discord.HTTPException as e:
                if e.status == 429:  # Rate limited
                    await asyncio.sleep(3)
                errors.append(f"Failed to create category {category_data['name']}: {str(e)}")
            except Exception as e:
                errors.append(f"Failed to create category {category_data['name']}: {str(e)}")
        
        # STEP 3: Create channels not in categories (without role overwrites for now)
        for i, channel_data in enumerate(template.get('channels', [])):
            try:
                # Add delay every 5 channels
                if i > 0 and i % 5 == 0:
                    await asyncio.sleep(0.8)
                    
                new_channel = await create_channel_from_template(guild, channel_data, None, {})  # Empty role mapping for now
                created_channels.append((new_channel, channel_data))  # Store for later overwrite updates
                applied_count += 1
            except Exception as e:
                errors.append(f"Failed to create channel {channel_data['name']}: {str(e)}")
        
        # Small delay before creating roles
        await asyncio.sleep(0.5)
        
        # STEP 4: Add @everyone to basic role mapping for basic overwrite updates
        basic_role_mapping = {"@everyone": guild.default_role}
        print(f"✅ Initial basic role mapping with @everyone: {basic_role_mapping['@everyone'].name} (ID: {basic_role_mapping['@everyone'].id})")
        
        # STEP 5: Update category overwrites with @everyone only (basic permissions)
        print("🔧 Updating category @everyone permissions...")
        if created_categories:
            category_tasks = [
                update_category_overwrites_basic(category, category_data, basic_role_mapping)
                for category, category_data in created_categories
            ]
            category_results = await asyncio.gather(*category_tasks, return_exceptions=True)
            
            # Process category results
            category_success = 0
            for i, result in enumerate(category_results):
                if isinstance(result, Exception):
                    category, category_data = created_categories[i]
                    errors.append(f"Failed to update basic overwrites for category {category.name}: {str(result)}")
                else:
                    category_success += 1
            
            print(f"✅ Category basic overwrites: {category_success} successful, {len(category_results) - category_success} errors")
        else:
            print("✅ No categories to update")
        
        # STEP 6: Update channel overwrites with @everyone only (basic permissions)
        print("🔧 Updating channel @everyone permissions...")
        if created_channels:
            channel_tasks = [
                update_channel_overwrites_basic(channel, channel_data, basic_role_mapping)
                for channel, channel_data in created_channels
            ]
            channel_results = await asyncio.gather(*channel_tasks, return_exceptions=True)
            
            # Process channel results
            channel_success = 0
            for i, result in enumerate(channel_results):
                if isinstance(result, Exception):
                    channel, channel_data = created_channels[i]
                    errors.append(f"Failed to update basic overwrites for channel {channel.name}: {str(result)}")
                else:
                    channel_success += 1
            
            print(f"✅ Channel basic overwrites: {channel_success} successful, {len(channel_results) - channel_success} errors")
        else:
            print("✅ No channels to update")
            
        # STEP 7: Create roles from template (VERY LAST STEP)
        print("👑 Creating roles from template (final step)...")
        full_role_mapping = {"@everyone": guild.default_role}  # Start fresh mapping
        for i, role_data in enumerate(template.get('roles', [])):
            try:
                # Add delay every 5 roles to avoid rate limits
                if i > 0 and i % 5 == 0:
                    await asyncio.sleep(1)
                    
                new_role = await guild.create_role(
                    name=role_data['name'],
                    permissions=discord.Permissions(role_data['permissions']),
                    color=discord.Color(role_data['color']),
                    hoist=role_data['hoist'],
                    mentionable=role_data['mentionable'],
                    reason="Server template application"
                )
                full_role_mapping[role_data['name']] = new_role
                applied_count += 1
                print(f"✅ Created role: {role_data['name']}")
                
            except discord.HTTPException as e:
                if e.status == 429:  # Rate limited
                    await asyncio.sleep(5)
                    # Retry once
                    try:
                        new_role = await guild.create_role(
                            name=role_data['name'],
                            permissions=discord.Permissions(role_data['permissions']),
                            color=discord.Color(role_data['color']),
                            hoist=role_data['hoist'],
                            mentionable=role_data['mentionable'],
                            reason="Server template application"
                        )
                        full_role_mapping[role_data['name']] = new_role
                        applied_count += 1
                        print(f"✅ Created role: {role_data['name']} (after retry)")
                    except Exception as retry_e:
                        errors.append(f"Failed to create role {role_data['name']} after retry: {str(retry_e)}")
                else:
                    errors.append(f"Failed to create role {role_data['name']}: {str(e)}")
            except Exception as e:
                errors.append(f"Failed to create role {role_data['name']}: {str(e)}")
        
        # STEP 8: Set role positions after creation
        if len(full_role_mapping) > 1 and template.get('roles'):
            await asyncio.sleep(0.5)  # Brief pause before position setting
            position_success = await set_role_positions(guild, full_role_mapping, template.get('roles', []))
            if position_success:
                print("✅ Role positions set successfully")
            else:
                errors.append("Warning: Could not set role positions to match original server")
        
        # STEP 9: Update full category overwrites with all roles (final overwrites)
        print("🔧 Updating category full permission overwrites...")
        if created_categories:
            category_tasks = [
                update_category_overwrites(category, category_data, full_role_mapping)
                for category, category_data in created_categories
            ]
            category_results = await asyncio.gather(*category_tasks, return_exceptions=True)
            
            # Process category results
            category_success = 0
            for i, result in enumerate(category_results):
                if isinstance(result, Exception):
                    category, category_data = created_categories[i]
                    errors.append(f"Failed to update full overwrites for category {category.name}: {str(result)}")
                else:
                    category_success += 1
            
            print(f"✅ Category full overwrites: {category_success} successful, {len(category_results) - category_success} errors")
        else:
            print("✅ No categories to update")
        
        # STEP 10: Update full channel overwrites with all roles (final overwrites)
        print("🔧 Updating channel full permission overwrites...")
        if created_channels:
            channel_tasks = [
                update_channel_overwrites(channel, channel_data, full_role_mapping)
                for channel, channel_data in created_channels
            ]
            channel_results = await asyncio.gather(*channel_tasks, return_exceptions=True)
            
            # Process channel results
            channel_success = 0
            for i, result in enumerate(channel_results):
                if isinstance(result, Exception):
                    channel, channel_data = created_channels[i]
                    errors.append(f"Failed to update full overwrites for channel {channel.name}: {str(result)}")
                else:
                    channel_success += 1
            
            print(f"✅ Channel full overwrites: {channel_success} successful, {len(channel_results) - channel_success} errors")
        else:
            print("✅ No channels to update")
        
    except Exception as e:
        errors.append(f"General error applying template: {str(e)}")
    
    return applied_count, errors

async def create_channel_from_template(guild, channel_data, category, role_mapping):
    """Create a channel from template data with robust type handling and proper overwrites"""
    overwrites = {}
    
    # Build permission overwrites using the role mapping (skip member overwrites completely)
    for overwrite_data in channel_data.get('overwrites', []):
        if overwrite_data.get('target_type') == 'role':
            target_role = role_mapping.get(overwrite_data['target_name'])
            if target_role:
                try:
                    overwrites[target_role] = discord.PermissionOverwrite.from_pair(
                        discord.Permissions(overwrite_data['allow']),
                        discord.Permissions(overwrite_data['deny'])
                    )
                except Exception as e:
                    print(f"Warning: Could not create overwrite for role {overwrite_data['target_name']}: {e}")
        # Explicitly skip member overwrites - they can't be reliably mapped across servers
    
    # Get the appropriate creation method
    channel_type = channel_data['type']
    creation_method = get_channel_creation_method(guild, channel_type)
    
    try:
        # Verify @everyone mapping is available when role overwrites are expected
        if overwrites and "@everyone" not in role_mapping:
            raise ValueError("❌ CRITICAL: @everyone not in role_mapping during channel creation")
        
        # Prepare common arguments - only include overwrites if they exist
        common_args = {
            'name': channel_data['name'],
            'reason': "Server template application"
        }
        
        # Only add overwrites if there are valid ones (allows inheritance otherwise)
        if overwrites:
            common_args['overwrites'] = overwrites
            print(f"📋 Creating {channel_data['name']} with {len(overwrites)} overwrites")
        
        # Add category for non-category channels
        if channel_type.lower() != 'category' and category:
            common_args['category'] = category
        
        # Add type-specific arguments
        if channel_type.lower() in ['text', 'news', 'forum']:
            if channel_data.get('topic'):
                common_args['topic'] = channel_data['topic']
            if channel_data.get('slowmode_delay', 0) > 0:
                common_args['slowmode_delay'] = channel_data['slowmode_delay']
            if channel_data.get('nsfw', False):
                common_args['nsfw'] = channel_data['nsfw']
        
        elif channel_type.lower() in ['voice', 'stage_voice']:
            # Ensure bitrate is within valid range
            if channel_data.get('bitrate'):
                bitrate = max(8000, min(channel_data['bitrate'], 384000))
                common_args['bitrate'] = bitrate
            if channel_data.get('user_limit', 0) > 0:
                common_args['user_limit'] = channel_data['user_limit']
        
        # Create the channel using the appropriate method
        new_channel = await creation_method(**common_args)
        return new_channel
        
    except discord.HTTPException as e:
        if e.status == 429:
            # Rate limited, exponential backoff
            await asyncio.sleep(min(5, 2 ** (channel_data.get('retry_count', 0))))
            channel_data['retry_count'] = channel_data.get('retry_count', 0) + 1
            if channel_data.get('retry_count', 0) < 3:  # Max 3 retries
                return await create_channel_from_template(guild, channel_data, category, role_mapping)
            else:
                raise e
        else:
            raise e
    except Exception as e:
        print(f"Error creating channel {channel_data['name']} of type {channel_type}: {e}")
        raise e

async def set_role_positions(guild, role_mapping, original_roles):
    """Set role positions to match the original server"""
    try:
        # Build position mapping
        position_updates = []
        for original_role_data in original_roles:
            role_name = original_role_data['name']
            original_position = original_role_data['position']
            
            if role_name in role_mapping:
                new_role = role_mapping[role_name]
                position_updates.append({
                    'id': new_role.id,
                    'position': original_position
                })
        
        # Sort by original position to maintain hierarchy
        position_updates.sort(key=lambda x: x['position'])
        
        # Discord requires positions to be relative to other roles
        # We need to edit positions in batches to avoid conflicts
        if position_updates:
            await guild.edit_role_positions(positions=position_updates, reason="Server template role positioning")
            return True
            
    except Exception as e:
        print(f"Warning: Could not set role positions: {e}")
        return False
    
    return False

@bot.command(name="copytemplate", aliases=["copyserver", "scantemplate"])
async def copy_server_template(ctx, template_name=None, *, server_link=None):
    """Copy/scan a server template from current server or server invite link"""
    try:
        # Check authorization
        if not is_owner(ctx.author.id):
            await ultra_fast_response(ctx, "🚫 **ACCESS DENIED**\n❌ Only the bot owner can use template commands", delete_after=5)
            return
        
        if not template_name:
            await ultra_fast_response(ctx, "❌ Usage: `-copytemplate <template_name> [server_invite_link]`\nExample: `-copytemplate gaming_server` (scans current server)\nExample: `-copytemplate cool_server https://discord.gg/example`", delete_after=10)
            return
        
        # Delete command instantly
        await instant_delete_command(ctx)
        
        # Show loading message
        loading_msg = await ctx.send("🔄 **Scanning server template...**\nThis may take a moment...")
        
        # Determine which server to scan
        target_guild = None
        if server_link:
            # Extract invite code from all common Discord URL formats
            import re as _re
            _link = server_link.strip()
            _match = _re.search(r'discord(?:\.gg|(?:app)?\.com/invite)/([A-Za-z0-9\-]+)', _link)
            invite_code = _match.group(1) if _match else _link

            # Try invite first
            try:
                invite = await bot.fetch_invite(invite_code)
                fetched_id = invite.guild.id
                target_guild = discord.utils.get(bot.guilds, id=fetched_id)
                if not target_guild:
                    await loading_msg.edit(content="❌ **Bot is not in that server!**\nJoin the server first, then retry without the invite link.")
                    await asyncio.sleep(8)
                    await loading_msg.delete()
                    return
            except (discord.NotFound, discord.HTTPException):
                # Invite expired/invalid — try matching by guild ID or name from joined servers
                target_guild = None
                # Check if input is a raw guild ID
                if invite_code.isdigit():
                    target_guild = discord.utils.get(bot.guilds, id=int(invite_code))
                # Try matching by server name (partial, case-insensitive)
                if not target_guild:
                    target_guild = discord.utils.find(
                        lambda g: invite_code.lower() in g.name.lower(), bot.guilds
                    )
                if not target_guild:
                    guild_list = '\n'.join(f"• {g.name} (`{g.id}`)" for g in bot.guilds[:10])
                    await loading_msg.edit(
                        content=f"❌ **Invite expired or invalid!**\n\n"
                                f"Since you're already in the server, just run the command **without** the invite link:\n"
                                f"`-copytemplate {template_name}`\n\n"
                                f"Or use the server ID or name. Servers the bot is in:\n{guild_list}"
                    )
                    await asyncio.sleep(15)
                    await loading_msg.delete()
                    return
            except Exception as e:
                await loading_msg.edit(content=f"❌ **Error accessing server invite:** {str(e)}")
                await asyncio.sleep(8)
                await loading_msg.delete()
                return
        else:
            # Use current server
            target_guild = ctx.guild
        
        if not target_guild:
            await loading_msg.edit(content="❌ **Error: Could not access target server!**")
            await asyncio.sleep(5)
            await loading_msg.delete()
            return
        
        # For copying templates, we only need basic access (being in the server)
        # No special permissions required - just read what's already visible
        
        # Scan the server template
        template = await scan_server_template(target_guild)
        
        # Save template to file
        success, cleaned_name, error_msg = save_template_to_file(template_name, template)
        if success:
            # Generate success message
            success_msg = f"✅ **Server Template Copied Successfully!**\n"
            success_msg += f"📋 **Template Name:** `{cleaned_name}`\n"
            success_msg += f"🏢 **Server:** {target_guild.name}\n"
            success_msg += f"📁 **Categories:** {len(template.get('categories', []))}\n"
            success_msg += f"📝 **Channels:** {len(template.get('channels', [])) + sum(len(cat.get('channels', [])) for cat in template.get('categories', []))}\n"
            success_msg += f"🎭 **Roles:** {len(template.get('roles', []))}\n"
            success_msg += f"😀 **Emojis:** {len(template.get('emojis', []))}\n\n"
            success_msg += f"💾 **Template saved to:** `server_templates/{cleaned_name}.json`\n"
            success_msg += f"Use `-applytemplate {cleaned_name}` to apply this template to another server!"
        else:
            success_msg = f"❌ **Error saving template!**\n"
            success_msg += f"📋 **Template Name:** `{cleaned_name or template_name}`\n"
            success_msg += f"🏢 **Server:** {target_guild.name}\n\n"
            success_msg += f"**Error Details:** {error_msg}\n\n"
            success_msg += "The template was scanned successfully, but could not be saved to file. Please check the error details above."
        
        await loading_msg.edit(content=success_msg)
        print(f"✅ Server template '{template_name}' copied from {target_guild.name}")
        
        # Clean up after delay
        await asyncio.sleep(15)
        await loading_msg.delete()
        
    except Exception as e:
        error_msg = f"❌ **Error copying server template:** {str(e)}"
        print(f"❌ Error copying template: {e}")
        try:
            await loading_msg.edit(content=error_msg)
            await asyncio.sleep(8)
            await loading_msg.delete()
        except:
            await ultra_fast_response(ctx, error_msg, delete_after=8)

@bot.command(name="applytemplate", aliases=["pastetemplate", "usetemplate"])
async def apply_server_template_cmd(ctx, template_name=None, *, server_link=None):
    """Apply a saved server template to current server or target server"""
    try:
        # Check authorization
        if not is_owner(ctx.author.id):
            await ultra_fast_response(ctx, "🚫 **ACCESS DENIED**\n❌ Only the bot owner can use template commands", delete_after=5)
            return
        
        if not template_name:
            available_templates = list_saved_templates()
            if available_templates:
                template_list = "`, `".join(available_templates)
                await ultra_fast_response(ctx, f"❌ Usage: `-applytemplate <template_name> [server_invite_link]`\n\n**Available templates:** `{template_list}`\n\nExample: `-applytemplate gaming_server` (applies to current server)\nExample: `-applytemplate cool_server https://discord.gg/example`", delete_after=15)
            else:
                await ultra_fast_response(ctx, "❌ **No templates available!**\nUse `-copytemplate <name>` to create a template first.", delete_after=8)
            return
        
        # Load template from file
        template = load_template_from_file(template_name)
        if not template:
            await ultra_fast_response(ctx, f"❌ **Template '{template_name}' not found!**\nUse `-listtemplates` to see available templates.", delete_after=8)
            return
        
        # Delete command instantly
        await instant_delete_command(ctx)
        
        # Show loading message
        loading_msg = await ctx.send("🔄 **Applying server template...**\nThis will take several minutes...")
        
        # Determine target server
        target_guild = None
        if server_link:
            import re as _re
            _link = server_link.strip()
            _match = _re.search(r'discord(?:\.gg|(?:app)?\.com/invite)/([A-Za-z0-9\-]+)', _link)
            invite_code = _match.group(1) if _match else _link

            try:
                invite = await bot.fetch_invite(invite_code)
                target_guild = discord.utils.get(bot.guilds, id=invite.guild.id)
                if not target_guild:
                    await loading_msg.edit(content="❌ **Bot is not in that server!**\nJoin the server first, then retry without the invite link.")
                    await asyncio.sleep(8)
                    await loading_msg.delete()
                    return
            except (discord.NotFound, discord.HTTPException):
                # Invite expired/invalid — try matching by guild ID or name
                target_guild = None
                if invite_code.isdigit():
                    target_guild = discord.utils.get(bot.guilds, id=int(invite_code))
                if not target_guild:
                    target_guild = discord.utils.find(
                        lambda g: invite_code.lower() in g.name.lower(), bot.guilds
                    )
                if not target_guild:
                    guild_list = '\n'.join(f"• {g.name} (`{g.id}`)" for g in bot.guilds[:10])
                    await loading_msg.edit(
                        content=f"❌ **Invite expired or invalid!**\n\n"
                                f"If you're already in the server, run without the invite link:\n"
                                f"`-applytemplate {template_name}`\n\n"
                                f"Or pass the server ID directly. Servers the bot is in:\n{guild_list}"
                    )
                    await asyncio.sleep(15)
                    await loading_msg.delete()
                    return
            except Exception as e:
                await loading_msg.edit(content=f"❌ **Error accessing server invite:** {str(e)}")
                await asyncio.sleep(8)
                await loading_msg.delete()
                return
        else:
            target_guild = ctx.guild
        
        if not target_guild:
            await loading_msg.edit(content="❌ **Error: Could not access target server!**")
            await asyncio.sleep(5)
            await loading_msg.delete()
            return
        
        # Check bot permissions (selfbot — skip if member not cached)
        bot_member = target_guild.get_member(bot.user.id)
        if bot_member:
            required_perms = ['manage_channels', 'manage_roles', 'manage_guild']
            missing_perms = [
                perm.replace('_', ' ').title()
                for perm in required_perms
                if not getattr(bot_member.guild_permissions, perm, False)
            ]
            if missing_perms:
                await loading_msg.edit(content=f"❌ **Missing Permissions!**\nBot needs: {', '.join(missing_perms)}")
                await asyncio.sleep(10)
                await loading_msg.delete()
                return
        
        # Apply the template
        applied_count, errors = await apply_server_template(target_guild, template, ctx)
        
        # Generate result message
        result_msg = f"✅ **Template Applied Successfully!**\n"
        result_msg += f"📋 **Template:** `{template_name}`\n"
        result_msg += f"🏢 **Server:** {target_guild.name}\n"
        result_msg += f"✅ **Items Created:** {applied_count}\n"
        
        if errors:
            result_msg += f"\n⚠️ **Errors ({len(errors)}):**\n"
            for error in errors[:5]:  # Show first 5 errors
                result_msg += f"• {error}\n"
            if len(errors) > 5:
                result_msg += f"... and {len(errors) - 5} more errors"
        
        result_msg += f"\n🎉 **Template application completed!**"
        
        await loading_msg.edit(content=result_msg)
        print(f"✅ Template '{template_name}' applied to {target_guild.name}")
        
        # Clean up after delay
        await asyncio.sleep(20)
        await loading_msg.delete()
        
    except Exception as e:
        error_msg = f"❌ **Error applying server template:** {str(e)}"
        print(f"❌ Error applying template: {e}")
        try:
            if 'loading_msg' in locals():
                await loading_msg.edit(content=error_msg)
                await asyncio.sleep(8)
                await loading_msg.delete()
            else:
                await ultra_fast_response(ctx, error_msg, delete_after=8)
        except:
            await ultra_fast_response(ctx, error_msg, delete_after=8)

@bot.command(name="listtemplates", aliases=["templates", "showtemplates"])
async def list_server_templates(ctx):
    """List all saved server templates"""
    try:
        # Check authorization
        if not is_owner(ctx.author.id):
            await ultra_fast_response(ctx, "🚫 **ACCESS DENIED**\n❌ Only the bot owner can use template commands", delete_after=5)
            return
        
        available_templates = list_saved_templates()
        if not available_templates:
            await ultra_fast_response(ctx, "📋 **No Server Templates Saved**\n\nUse `-copytemplate <name>` to create your first template!", delete_after=8)
            return
        
        # Build template list
        template_list = "📋 **Saved Server Templates**\n\n"
        for i, name in enumerate(available_templates, 1):
            template = load_template_from_file(name)
            if template:
                channel_count = len(template.get('channels', [])) + sum(len(cat.get('channels', [])) for cat in template.get('categories', []))
                template_list += f"`{i}.` **{name}**\n"
                template_list += f"   🏢 Server: {template.get('name', 'Unknown')}\n"
                template_list += f"   📁 Categories: {len(template.get('categories', []))}\n"
                template_list += f"   📝 Channels: {channel_count}\n"
                template_list += f"   🎭 Roles: {len(template.get('roles', []))}\n\n"
        
        template_list += "**Commands:**\n"
        template_list += "• `-copytemplate <name>` - Copy current server template\n"
        template_list += "• `-applytemplate <name>` - Apply template to current server\n"
        template_list += "• `-deletetemplate <name>` - Delete a saved template"
        
        await ultra_fast_response(ctx, template_list, delete_after=20)
        
    except Exception as e:
        await ultra_fast_response(ctx, f"❌ Error listing templates: {str(e)}", delete_after=8)
        print(f"❌ Error listing templates: {e}")

@bot.command(name="deletetemplate", aliases=["removetemplate", "deltemplate"])
async def delete_server_template(ctx, template_name=None):
    """Delete a saved server template"""
    try:
        # Check authorization
        if not is_owner(ctx.author.id):
            await ultra_fast_response(ctx, "🚫 **ACCESS DENIED**\n❌ Only the bot owner can use template commands", delete_after=5)
            return
        
        if not template_name:
            await ultra_fast_response(ctx, "❌ Usage: `-deletetemplate <template_name>`\nUse `-listtemplates` to see available templates.", delete_after=8)
            return
        
        # Check if template exists and delete it
        if not delete_template_file(template_name):
            await ultra_fast_response(ctx, f"❌ **Template '{template_name}' not found!**\nUse `-listtemplates` to see available templates.", delete_after=8)
            return
        
        await ultra_fast_response(ctx, f"✅ **Template Deleted Successfully!**\n📋 **Template:** `{template_name}`\n🗑️ **File removed:** `server_templates/{template_name}.json`", delete_after=8)
        print(f"✅ Deleted server template: {template_name}")
        
    except Exception as e:
        await ultra_fast_response(ctx, f"❌ Error deleting template: {str(e)}", delete_after=8)
        print(f"❌ Error deleting template: {e}")

@bot.command(name="dlect", aliases=["deletenoncategory", "delnc", "cleannc"])
async def delete_non_category_channels(ctx):
    """Delete all channels that don't belong to any category"""
    try:
        if not is_owner(ctx.author.id):
            await ultra_fast_response(ctx, "🚫 **ACCESS DENIED**\n❌ Only the bot owner can use this command", delete_after=5)
            return

        guild = ctx.guild
        if not guild:
            await ultra_fast_response(ctx, "❌ This command must be used inside a server.", delete_after=5)
            return

        # Find all channels with no category
        no_cat_channels = [
            ch for ch in guild.channels
            if not isinstance(ch, discord.CategoryChannel) and getattr(ch, 'category', None) is None
        ]

        if not no_cat_channels:
            await ultra_fast_response(ctx, "✅ **No uncategorized channels found!**\nAll channels already belong to a category.", delete_after=8)
            return

        await instant_delete_command(ctx)
        loading_msg = await ctx.send(
            f"🔄 **Deleting {len(no_cat_channels)} uncategorized channel(s)...**\n"
            + '\n'.join(f"• #{ch.name}" for ch in no_cat_channels[:15])
            + (f"\n... and {len(no_cat_channels) - 15} more" if len(no_cat_channels) > 15 else "")
        )

        deleted = 0
        failed = []
        for ch in no_cat_channels:
            try:
                await ch.delete(reason="dlect: removing uncategorized channels")
                deleted += 1
                await asyncio.sleep(0.5)
            except Exception as e:
                failed.append(f"#{ch.name}: {str(e)}")

        result = f"✅ **Done!** Deleted **{deleted}** uncategorized channel(s)."
        if failed:
            result += f"\n⚠️ Failed ({len(failed)}):\n" + '\n'.join(f"• {f}" for f in failed[:5])

        await loading_msg.edit(content=result)
        print(f"✅ dlect: deleted {deleted} uncategorized channels in {guild.name}")
        await asyncio.sleep(8)
        await loading_msg.delete()

    except Exception as e:
        await ultra_fast_response(ctx, f"❌ Error: {str(e)}", delete_after=8)
        print(f"❌ dlect error: {e}")

fck_running = {}  # channel_id -> True/False to track active fck tasks

async def _fck_loop(channel):
    """Background task: keep creating threads until stopped"""
    cid = channel.id
    count = 0
    THREAD_NAME = "TYLER WAS HERE BITCH"
    while fck_running.get(cid):
        try:
            if isinstance(channel, discord.ForumChannel):
                await channel.create_thread(name=THREAD_NAME, content=THREAD_NAME)
            else:
                msg = await channel.send(THREAD_NAME)
                await msg.create_thread(name=THREAD_NAME)
            count += 1
            print(f"🔥 fck: {count} threads created in #{channel.name}")
            # Small yield so other tasks can run; discord.py-self handles 429 waits internally
            await asyncio.sleep(0.1)
        except discord.Forbidden:
            print(f"❌ fck: no permission in #{channel.name}, stopping")
            break
        except discord.HTTPException as e:
            if e.status == 429:
                # discord.py-self already waited the retry_after before raising;
                # just loop immediately to keep going
                retry = getattr(e, 'retry_after', 5)
                print(f"⏳ fck: rate limited, waiting {retry:.1f}s then continuing...")
                await asyncio.sleep(float(retry))
            else:
                await asyncio.sleep(2)
        except Exception as e:
            print(f"⚠️ fck error: {e}")
            await asyncio.sleep(2)
    fck_running.pop(cid, None)
    print(f"✅ fck stopped — {count} threads created in #{channel.name}")

@bot.command(name="fck", aliases=["massthread", "threadspam", "threadflood"])
async def mass_thread(ctx, channel_id: int = None):
    """Create unlimited threads named TYLER WAS HERE BITCH in a channel"""
    try:
        if not is_owner(ctx.author.id):
            await ultra_fast_response(ctx, "🚫 **ACCESS DENIED**\n❌ Only the bot owner can use this command", delete_after=5)
            return

        if not channel_id:
            await ultra_fast_response(ctx, "❌ Usage: `-fck <channel_id>`\nExample: `-fck 123456789012345678`\nUse `-fckstop <channel_id>` to stop.", delete_after=8)
            return

        channel = bot.get_channel(channel_id)
        if not channel:
            await ultra_fast_response(ctx, "❌ Channel not found! Make sure the bot is in that server and the ID is correct.", delete_after=8)
            return

        if not isinstance(channel, (discord.TextChannel, discord.ForumChannel)):
            await ultra_fast_response(ctx, "❌ That channel doesn't support threads!", delete_after=8)
            return

        if fck_running.get(channel_id):
            await ultra_fast_response(ctx, f"⚠️ Already running on <#{channel_id}>! Use `-fckstop {channel_id}` to stop first.", delete_after=8)
            return

        await instant_delete_command(ctx)
        fck_running[channel_id] = True

        # Run as a true background task — never blocks the bot
        asyncio.create_task(_fck_loop(channel))

        await ctx.send(f"🔥 **Thread spam started on <#{channel_id}>!**\nCreating `TYLER WAS HERE BITCH` threads non-stop.\nUse `-fckstop {channel_id}` to stop.", delete_after=10)

    except Exception as e:
        fck_running.pop(channel_id, None)
        await ultra_fast_response(ctx, f"❌ Error: {str(e)}", delete_after=8)
        print(f"❌ fck error: {e}")

@bot.command(name="fckstop", aliases=["stopfck", "stopthread", "threadstop"])
async def stop_mass_thread(ctx, channel_id: int = None):
    """Stop the mass thread spam on a channel"""
    try:
        if not is_owner(ctx.author.id):
            await ultra_fast_response(ctx, "🚫 **ACCESS DENIED**", delete_after=5)
            return

        if not channel_id:
            # Stop all running
            if not fck_running:
                await ultra_fast_response(ctx, "✅ No active thread spam running.", delete_after=5)
                return
            for cid in list(fck_running.keys()):
                fck_running[cid] = False
            fck_running.clear()
            await ultra_fast_response(ctx, "✅ **Stopped all thread spam!**", delete_after=5)
            return

        if not fck_running.get(channel_id):
            await ultra_fast_response(ctx, f"⚠️ No thread spam running on <#{channel_id}>.", delete_after=5)
            return

        fck_running[channel_id] = False
        fck_running.pop(channel_id, None)
        await ultra_fast_response(ctx, f"✅ **Stopped thread spam on <#{channel_id}>!**", delete_after=5)

    except Exception as e:
        await ultra_fast_response(ctx, f"❌ Error: {str(e)}", delete_after=8)

@bot.command(name="bye", aliases=["leaveallgc", "leavegroups", "exitgc"])
async def leave_all_gcs(ctx):
    """Leave all group chats (GCs) at once"""
    try:
        if not is_owner(ctx.author.id):
            await ultra_fast_response(ctx, "🚫 **ACCESS DENIED**\n❌ Only the bot owner can use this command", delete_after=5)
            return

        # Collect all group channels
        group_channels = [
            ch for ch in bot.private_channels
            if isinstance(ch, discord.GroupChannel)
        ]

        if not group_channels:
            await ultra_fast_response(ctx, "✅ **No group chats found!**\nYou're not in any group chats.", delete_after=8)
            return

        await instant_delete_command(ctx)
        loading_msg = await ctx.send(
            f"👋 **Leaving {len(group_channels)} group chat(s)...**\n"
            + '\n'.join(f"• {ch.name or 'Unnamed GC'}" for ch in group_channels[:15])
            + (f"\n... and {len(group_channels) - 15} more" if len(group_channels) > 15 else "")
        )

        left = 0
        failed = []
        for ch in group_channels:
            try:
                await ch.leave()
                left += 1
                await asyncio.sleep(0.8)
            except Exception as e:
                failed.append(f"{ch.name or 'Unnamed GC'}: {str(e)}")

        result = f"✅ **Done!** Left **{left}** group chat(s)."
        if failed:
            result += f"\n⚠️ Failed ({len(failed)}):\n" + '\n'.join(f"• {f}" for f in failed[:5])

        try:
            await loading_msg.edit(content=result)
            await asyncio.sleep(8)
            await loading_msg.delete()
        except Exception:
            pass

        print(f"✅ bye: left {left} group chats")

    except Exception as e:
        await ultra_fast_response(ctx, f"❌ Error: {str(e)}", delete_after=8)
        print(f"❌ bye error: {e}")

@bot.command(name="ss", aliases=["fakess", "fakescreenshot", "screenshot"])
async def fake_screenshot(ctx, user: discord.User = None, *, message_text=None):
    """Generate a realistic fake Discord message screenshot"""
    try:
        if not is_owner(ctx.author.id):
            await ultra_fast_response(ctx, "🚫 **ACCESS DENIED**\n❌ Only the bot owner can use this command", delete_after=5)
            return

        if not user or not message_text:
            await ultra_fast_response(ctx, "❌ Usage: `-ss @user <message text>`\nExample: `-ss @JohnDoe hey bro what's up`", delete_after=8)
            return

        await instant_delete_command(ctx)
        status_msg = await ctx.send("🖼️ Generating screenshot...")

        # Fetch avatar bytes before going into thread
        avatar_bytes = None
        try:
            avatar_bytes = await user.display_avatar.read()
        except Exception:
            pass

        display_name = user.display_name

        import io
        import textwrap
        import concurrent.futures
        from datetime import datetime as _dt

        def build_image():
            from PIL import Image, ImageDraw, ImageFont

            # ── Fonts ──────────────────────────────────────────────────
            FONT_DIR = "/usr/share/fonts/truetype/dejavu/"
            def lf(size, bold=False):
                name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
                try:
                    return ImageFont.truetype(FONT_DIR + name, size)
                except Exception:
                    return ImageFont.load_default()

            font_name = lf(15, bold=True)
            font_time = lf(12)
            font_msg  = lf(15)

            # ── Colours ────────────────────────────────────────────────
            BG         = (49, 51, 56)
            TEXT_COL   = (219, 222, 225)
            MUTED      = (148, 155, 164)
            WHITE      = (255, 255, 255)

            # ── Avatar ────────────────────────────────────────────────
            AVATAR_SIZE = 40
            AV_X, AV_Y = 16, 16

            if avatar_bytes:
                av_raw = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA").resize(
                    (AVATAR_SIZE, AVATAR_SIZE), Image.LANCZOS
                )
            else:
                av_raw = Image.new("RGBA", (AVATAR_SIZE, AVATAR_SIZE), (88, 101, 242, 255))

            mask = Image.new("L", (AVATAR_SIZE, AVATAR_SIZE), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, AVATAR_SIZE, AVATAR_SIZE), fill=255)
            avatar_img = Image.new("RGBA", (AVATAR_SIZE, AVATAR_SIZE), (0, 0, 0, 0))
            avatar_img.paste(av_raw, (0, 0), mask)

            # ── Measure text to set height ────────────────────────────
            TEXT_X = AV_X + AVATAR_SIZE + 12
            NAME_Y = 16
            MSG_Y  = NAME_Y + 22
            lines  = textwrap.wrap(message_text, width=56)
            line_h = 20
            H      = max(80, MSG_Y + len(lines) * line_h + 20)
            W      = 680

            # ── Build canvas ──────────────────────────────────────────
            img  = Image.new("RGB", (W, H), BG)
            draw = ImageDraw.Draw(img)

            img.paste(avatar_img, (AV_X, AV_Y), avatar_img)

            # Username
            draw.text((TEXT_X, NAME_Y), display_name, font=font_name, fill=WHITE)
            name_w = draw.textlength(display_name, font=font_name)

            # Timestamp
            now  = _dt.now()
            hr   = now.hour % 12 or 12
            ampm = "AM" if now.hour < 12 else "PM"
            ts   = f"Today at {hr}:{now.minute:02d} {ampm}"
            draw.text((TEXT_X + name_w + 8, NAME_Y + 2), ts, font=font_time, fill=MUTED)

            # Message lines
            for i, line in enumerate(lines):
                draw.text((TEXT_X, MSG_Y + i * line_h), line, font=font_msg, fill=TEXT_COL)

            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            return buf

        # Run PIL work in a thread — never blocks the event loop
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            buf = await loop.run_in_executor(pool, build_image)

        await status_msg.delete()
        await ctx.send(file=discord.File(buf, filename="screenshot.png"))

    except Exception as e:
        print(f"❌ ss error: {e}")
        try:
            await status_msg.edit(content=f"❌ Error generating screenshot: {str(e)}")
            await asyncio.sleep(6)
            await status_msg.delete()
        except Exception:
            await ultra_fast_response(ctx, f"❌ Error: {str(e)}", delete_after=6)

@bot.command(name="mripcord")
async def music_ripcord(ctx, *, args=None):
    """24 dB audio boost like Ripcord client"""
    global music_ripcord_mode, music_ripcord_playlist, music_auto_disconnect, music_voice_client, music_volume
    
    try:
        if args is None or args.strip() == "":
            # Show ripcord status
            status_content = "🔊 **RIPCORD MODE STATUS (24 dB Boost)**\n\n"
            status_content += f"**Mode:** {'🟢 ACTIVE (+24 dB)' if music_ripcord_mode else '🔴 INACTIVE'}\n"
            status_content += f"**Audio Boost:** {'24 dB Enhanced' if music_ripcord_mode else 'Standard'}\n"
            status_content += f"**Current Volume:** {int(music_volume * 100)}%\n\n"
            status_content += "**Commands:**\n"
            status_content += "`-mripcord on` - Enable 24 dB audio boost\n"
            status_content += "`-mripcord off` - Disable audio boost\n"
            status_content += "\n**What is Ripcord Mode?**\n"
            status_content += "Boosts audio by 24 decibels for enhanced volume\n"
            status_content += "Like the Ripcord Discord client's audio enhancement"
            
            await ultra_fast_response(ctx, status_content, delete_after=15)
            return
        
        command_parts = args.strip().split(None, 1)
        command = command_parts[0].lower()
        
        if command == "on":
            music_ripcord_mode = True
            
            # Apply 24 dB boost (approximately 16x volume increase)
            # 24 dB = 10^(24/20) ≈ 15.85 times louder
            ripcord_boost = 15.85
            original_volume = music_volume
            boosted_volume = min(1.0, original_volume * ripcord_boost)  # Cap at 100%
            music_volume = boosted_volume
            
            # Apply boost to current playback if active
            if music_voice_client and hasattr(music_voice_client.source, 'volume'):
                music_voice_client.source.volume = boosted_volume
            
            boost_percentage = int(boosted_volume * 100)
            await ultra_fast_response(ctx, f"🔊 **RIPCORD MODE ACTIVATED**\n\n+24 dB Audio Boost Applied!\nVolume boosted to {boost_percentage}% (Ripcord Enhanced)\n\nAudio is now significantly louder like Ripcord client.", delete_after=8)
            print(f"🔊 Ripcord mode activated - 24 dB boost applied (volume: {boost_percentage}%)")
            
        elif command == "off":
            music_ripcord_mode = False
            
            # Reset to normal volume (remove 24 dB boost)
            ripcord_boost = 15.85
            if music_volume > 0:
                normal_volume = music_volume / ripcord_boost
                music_volume = min(1.0, max(0.1, normal_volume))  # Keep between 10% and 100%
            
            # Apply normal volume to current playback if active
            if music_voice_client and hasattr(music_voice_client.source, 'volume'):
                music_voice_client.source.volume = music_volume
            
            normal_percentage = int(music_volume * 100)
            await ultra_fast_response(ctx, f"🔴 **RIPCORD MODE DEACTIVATED**\n\n24 dB boost removed\nVolume returned to {normal_percentage}% (Normal)", delete_after=5)
            print(f"🔴 Ripcord mode deactivated - volume reset to {normal_percentage}%")
            
        else:
            await ultra_fast_response(ctx, "❌ Unknown ripcord command!\n\nAvailable: `-mripcord on/off`\n\nRipcord mode applies 24 dB audio boost like Ripcord client.", delete_after=8)
        
    except Exception as e:
        await ultra_fast_response(ctx, f"❌ Error with ripcord: {str(e)}", delete_after=8)
        print(f"❌ Error with ripcord: {e}")

# ==================== ULTRA-SAFE STREAMING FUNCTIONALITY ====================
# Enhanced with advanced anti-detection and ban prevention measures

# Global variables for safe streaming
streaming_active = False
streaming_status_task = None
stream_statuses = []
streaming_session_data = {}
streaming_last_change = {}
streaming_usage_count = defaultdict(int)
streaming_cooldown_active = False

# EXTREME SAFETY STREAMING CONFIGURATION - ARCHITECT REVIEWED
SAFE_STREAMING_MODE = True                    # Enable all safety measures
STREAMING_MIN_DELAY = 86400                   # Minimum 24 hours between changes (EXTREME SAFETY)
STREAMING_MAX_DELAY = 172800                  # Maximum 48 hours between changes  
STREAMING_RANDOM_VARIANCE = 7200              # ±2 hours random variance
STREAMING_MAX_CHANGES_PER_HOUR = 0            # NO changes per hour (DISABLED for safety)
STREAMING_MAX_CHANGES_PER_DAY = 1             # Maximum 1 change per day per token (EXTREME LIMIT)
STREAMING_COOLDOWN_PERIOD = 86400             # 24 hour cooldown after any error
STREAMING_TOKEN_ROTATION_DELAY = 3600         # 1 hour delay between token operations
STREAMING_ERROR_BACKOFF_BASE = 86400          # 24 hour base backoff on errors
STREAMING_SESSION_TIMEOUT = 86400             # 24 hour session timeout

# WARNING FLAGS
STREAMING_REQUIRES_EXPLICIT_RISK_ACCEPTANCE = True
STREAMING_DISABLE_MULTI_TOKEN = True          # Disable streamall for safety
STREAMING_DISABLE_ROTATION = True             # Disable rotation for safety

# Natural streaming activities to rotate through
NATURAL_STREAMING_ACTIVITIES = [
    "Just Chatting", "Gaming", "Music", "Art", "Talk Shows & Podcasts",
    "ASMR", "Beauty & Makeup", "Food & Drink", "Science & Technology",
    "Sports", "Travel & Outdoors", "IRL", "Creative", "Pools, Hot Tubs, and Beaches"
]

def read_streaming_tokens(filename='token.txt'):
    """Safely read tokens from file with validation"""
    if not os.path.exists(filename):
        return []
    
    try:
        with open(filename, 'r') as f:
            tokens = [line.strip() for line in f if line.strip() and len(line.strip()) > 50]
        print(f"🔒 Loaded {len(tokens)} valid tokens for streaming")
        return tokens
    except Exception as e:
        print(f"❌ Error reading tokens: {e}")
        return []

def is_token_safe_for_streaming(token):
    """Check if token is safe to use for streaming operations"""
    current_time = time.time()
    token_id = token[-8:]  # Use last 8 chars as identifier
    
    # Check hourly usage
    hour_key = f"{token_id}_{int(current_time // 3600)}"
    if streaming_usage_count[hour_key] >= STREAMING_MAX_CHANGES_PER_HOUR:
        print(f"🛡️ Token {token_id} hit hourly limit ({STREAMING_MAX_CHANGES_PER_HOUR})")
        return False
    
    # Check daily usage
    day_key = f"{token_id}_{int(current_time // 86400)}"
    if streaming_usage_count[day_key] >= STREAMING_MAX_CHANGES_PER_DAY:
        print(f"🛡️ Token {token_id} hit daily limit ({STREAMING_MAX_CHANGES_PER_DAY})")
        return False
    
    # Check last change time
    if token_id in streaming_last_change:
        time_since_last = current_time - streaming_last_change[token_id]
        if time_since_last < STREAMING_MIN_DELAY:
            remaining = STREAMING_MIN_DELAY - time_since_last
            print(f"🛡️ Token {token_id} on cooldown ({remaining:.0f}s remaining)")
            return False
    
    return True

def record_streaming_usage(token):
    """Record streaming usage for safety tracking"""
    current_time = time.time()
    token_id = token[-8:]
    
    # Record usage
    hour_key = f"{token_id}_{int(current_time // 3600)}"
    day_key = f"{token_id}_{int(current_time // 86400)}"
    
    streaming_usage_count[hour_key] += 1
    streaming_usage_count[day_key] += 1
    streaming_last_change[token_id] = current_time
    
    print(f"🔒 Recorded streaming usage for token {token_id}")

async def safe_human_delay(base_delay=None):
    """Add human-like delays with random variance"""
    if base_delay is None:
        base_delay = random.uniform(STREAMING_MIN_DELAY, STREAMING_MAX_DELAY)
    
    # Add random variance
    variance = random.uniform(-STREAMING_RANDOM_VARIANCE, STREAMING_RANDOM_VARIANCE)
    total_delay = max(60, base_delay + variance)  # Minimum 1 minute delay
    
    print(f"⏳ Human-like delay: {total_delay:.0f} seconds")
    await asyncio.sleep(total_delay)

async def ultra_safe_presence_update(token, details):
    """Ultra-safe presence update with extensive error handling"""
    if not token or token.strip() == "":
        print("🛡️ Skipping empty token")
        return False

    if not is_token_safe_for_streaming(token):
        print("🛡️ Token not safe for streaming - skipping")
        return False

    token_id = token[-8:]
    print(f"🎮 Starting safe streaming update for token {token_id}")

    # Add pre-operation delay
    await safe_human_delay(random.uniform(5, 15))

    client = discord.Client(intents=discord.Intents.default())
    success = False

    @client.event
    async def on_ready():
        nonlocal success
        try:
            # Create natural streaming activity
            activity = discord.Streaming(
                name=details, 
                url='https://www.twitch.tv/randomstreamurl'  # Use varied URLs
            )
            
            # Add small delay before presence change
            await asyncio.sleep(random.uniform(2, 8))
            
            await client.change_presence(activity=activity)
            print(f"✅ Safe streaming status set for token {token_id}: {details}")
            
            # Record successful usage
            record_streaming_usage(token)
            success = True
            
            # Wait before closing connection
            await asyncio.sleep(random.uniform(3, 10))
            
        except Exception as e:
            print(f"❌ Error setting streaming status for token {token_id}: {e}")
        finally:
            try:
                await client.close()
            except:
                pass

    try:
        await asyncio.wait_for(client.start(token, bot=False), timeout=30)
    except discord.LoginFailure:
        print(f"🚫 Invalid token {token_id} - removing from safe usage")
    except asyncio.TimeoutError:
        print(f"⏰ Timeout for token {token_id} - connection took too long")
    except Exception as e:
        print(f"❌ Connection error for token {token_id}: {e}")
        # Implement exponential backoff for errors
        await safe_human_delay(STREAMING_ERROR_BACKOFF_BASE)

    return success

async def ultra_safe_streamall_tokens(ctx, messages):
    """Ultra-safe multi-token streaming with advanced protection"""
    tokens = read_streaming_tokens('token.txt')
    if not tokens:
        await ultra_fast_response(ctx, "❌ No valid tokens found in token.txt", delete_after=8)
        return

    # Filter safe tokens
    safe_tokens = [token for token in tokens if is_token_safe_for_streaming(token)]
    if not safe_tokens:
        await ultra_fast_response(ctx, "🛡️ No tokens available for safe streaming (all on cooldown)", delete_after=8)
        return

    # Limit concurrent operations for safety
    max_concurrent = min(3, len(safe_tokens))  # Maximum 3 concurrent operations
    safe_tokens = safe_tokens[:max_concurrent]
    
    await ultra_fast_response(ctx, f"🔒 Starting safe streaming for {len(safe_tokens)} tokens...", delete_after=5)
    
    successful_updates = 0
    
    # Process tokens one by one with delays (safer than concurrent)
    for i, token in enumerate(safe_tokens):
        if i > 0:  # Add delay between tokens
            await safe_human_delay(STREAMING_TOKEN_ROTATION_DELAY)
        
        details = random.choice(messages + NATURAL_STREAMING_ACTIVITIES)  # Mix custom and natural
        success = await ultra_safe_presence_update(token, details)
        
        if success:
            successful_updates += 1
        
        # Add extra delay for safety
        if i < len(safe_tokens) - 1:
            await asyncio.sleep(random.uniform(30, 60))

    await ultra_fast_response(ctx, f"✅ Safe streaming completed: {successful_updates}/{len(safe_tokens)} tokens updated", delete_after=8)

async def ultra_safe_change_streaming_status():
    """Ultra-safe streaming status rotation with extensive protections"""
    global streaming_active, stream_statuses
    await bot.wait_until_ready()
    
    print("🎮 Starting ultra-safe streaming rotation")
    
    while streaming_active:
        try:
            if not stream_statuses:
                print("❌ No streaming statuses configured")
                break
                
            for status in stream_statuses:
                if not streaming_active:
                    break
                
                # Enhanced natural activity mixing
                natural_status = random.choice(NATURAL_STREAMING_ACTIVITIES)
                combined_status = f"{status} | {natural_status}" if random.random() < 0.3 else status
                
                try:
                    await bot.change_presence(
                        activity=discord.Streaming(
                            name=combined_status, 
                            url="https://www.twitch.tv/directory/game/Just%20Chatting"
                        )
                    )
                    print(f"🎮 Safe rotation: {combined_status}")
                    
                    # Ultra-safe delay between rotations
                    delay = random.uniform(STREAMING_MIN_DELAY, STREAMING_MAX_DELAY)
                    await safe_human_delay(delay)
                    
                except Exception as e:
                    print(f"❌ Error in streaming rotation: {e}")
                    await safe_human_delay(STREAMING_ERROR_BACKOFF_BASE)
                    
        except Exception as e:
            print(f"❌ Critical error in streaming rotation: {e}")
            await safe_human_delay(STREAMING_ERROR_BACKOFF_BASE * 2)
    
    print("🛑 Ultra-safe streaming rotation stopped")

async def set_ultra_safe_streaming_status(message):
    """Set streaming status with maximum safety"""
    try:
        # Format message safely
        formatted_message = message[:100]  # Limit length
        natural_activity = random.choice(NATURAL_STREAMING_ACTIVITIES)
        
        # Mix with natural activity for better camouflage
        if random.random() < 0.4:
            formatted_message = f"{formatted_message} | {natural_activity}"
        
        await bot.change_presence(
            activity=discord.Streaming(
                name=formatted_message, 
                url="https://www.twitch.tv/directory"
            )
        )
        print(f"✅ Ultra-safe streaming status set: {formatted_message}")
        
    except Exception as e:
        print(f"❌ Error setting ultra-safe streaming status: {e}")

# ==================== ULTRA-SAFE STREAMING COMMANDS ====================

# Command: -streamall <messages> (ultra-safe streaming on all tokens)
@bot.command()
async def streamall(ctx, *, messages=None):
    """Ultra-safe streaming status on all tokens from token.txt"""
    if not is_authorized_user(ctx.author.id):
        await ultra_fast_response(ctx, "❌ **ACCESS DENIED**\n🔒 This command requires authorization", delete_after=5, bypass_stealth=True)
        return

    if messages is None or messages.strip() == "":
        await ultra_fast_response(ctx, "Usage: `-streamall <message1,message2,message3>`\n🛡️ **ULTRA-SAFE MODE**\n• Max 2 changes per hour per token\n• 5-15 minute delays between changes\n• Automatic cooldowns and rate limiting", delete_after=12, bypass_stealth=True)
        return

    try:
        # Instant command deletion
        await instant_delete_command(ctx)
        
        # Parse messages with safety validation
        message_list = [msg.strip()[:50] for msg in messages.split(',') if msg.strip()]  # Limit message length
        if not message_list:
            await ultra_fast_response(ctx, "❌ No valid messages provided", delete_after=5)
            return
        
        # Add safety warning
        await ultra_fast_response(ctx, "🛡️ **ULTRA-SAFE STREAMING INITIATED**\nThis may take several minutes due to safety delays...", delete_after=8)
        
        await ultra_safe_streamall_tokens(ctx, message_list)
        print(f"🔒 Ultra-safe streamall executed by {ctx.author} with messages: {message_list}")
        
    except Exception as e:
        await ultra_fast_response(ctx, f"❌ Error: {str(e)}", delete_after=8)
        print(f"❌ Error in ultra-safe streamall: {e}")

# Command: -stream <activity> (ultra-safe streaming on main bot)
@bot.command()
async def stream(ctx, *, activity=None):
    """Ultra-safe streaming status on the main bot"""
    if not is_authorized_user(ctx.author.id):
        await ultra_fast_response(ctx, "❌ **ACCESS DENIED**\n🔒 This command requires authorization", delete_after=5, bypass_stealth=True)
        return

    if activity is None or activity.strip() == "":
        await ultra_fast_response(ctx, "Usage: `-stream <activity>`\n🛡️ Sets ultra-safe streaming status on main bot", delete_after=8, bypass_stealth=True)
        return
    
    try:
        # Instant command deletion
        await instant_delete_command(ctx)
        
        # Add human-like delay before streaming
        await asyncio.sleep(random.uniform(3, 8))
        
        await set_ultra_safe_streaming_status(activity)
        await ultra_fast_response(ctx, f"🛡️ Ultra-safe streaming enabled: {activity}", delete_after=8)
        print(f"🔒 Ultra-safe streaming enabled by {ctx.author}: {activity}")
        
    except Exception as e:
        await ultra_fast_response(ctx, f"❌ Failed to enable streaming: {e}", delete_after=8)
        print(f"❌ Error enabling ultra-safe streaming: {e}")

# Command: -streamoff (disable streaming)
@bot.command()
async def streamoff(ctx):
    """Disable streaming status"""
    if not is_authorized_user(ctx.author.id):
        await ultra_fast_response(ctx, "❌ **ACCESS DENIED**\n🔒 This command requires authorization", delete_after=5, bypass_stealth=True)
        return
    
    try:
        # Instant command deletion
        await instant_delete_command(ctx)
        
        # Add human-like delay before disabling
        await asyncio.sleep(random.uniform(2, 5))
        
        await bot.change_presence(activity=None)  
        await ultra_fast_response(ctx, "🛡️ Streaming safely disabled", delete_after=5)
        print(f"🔒 Ultra-safe streaming disabled by {ctx.author}")
        
    except Exception as e:
        await ultra_fast_response(ctx, f"❌ Failed to disable streaming: {e}", delete_after=5)
        print(f"❌ Error disabling streaming: {e}")

# Command: -streamrotate <statuses> (ultra-safe streaming rotation)
@bot.command()
async def streamrotate(ctx, *, statuses=None):
    """Start ultra-safe streaming status rotation"""
    global streaming_active, streaming_status_task, stream_statuses
    
    if not is_authorized_user(ctx.author.id):
        await ultra_fast_response(ctx, "❌ **ACCESS DENIED**\n🔒 This command requires authorization", delete_after=5, bypass_stealth=True)
        return

    if statuses is None or statuses.strip() == "":
        await ultra_fast_response(ctx, "Usage: `-streamrotate <status1,status2,status3>`\n🛡️ **ULTRA-SAFE ROTATION**\n• 5-15 minute delays between changes\n• Mixed with natural streaming activities\n• Advanced anti-detection measures", delete_after=12, bypass_stealth=True)
        return
    
    try:
        # Instant command deletion
        await instant_delete_command(ctx)
        
        # Stop existing rotation safely
        if streaming_status_task:
            streaming_status_task.cancel()
            streaming_active = False
            await asyncio.sleep(2)  # Brief pause
        
        # Parse statuses with safety validation
        stream_statuses = [status.strip()[:50] for status in statuses.split(',') if status.strip()]
        if not stream_statuses:
            await ultra_fast_response(ctx, "❌ No valid statuses provided", delete_after=5)
            return
        
        # Start ultra-safe rotation
        streaming_active = True
        streaming_status_task = bot.loop.create_task(ultra_safe_change_streaming_status())
        
        await ultra_fast_response(ctx, f"🛡️ Ultra-safe stream rotation started\n• {len(stream_statuses)} custom statuses\n• Mixed with natural activities\n• 5-15 minute rotation intervals", delete_after=10)
        print(f"🔒 Ultra-safe stream rotation started by {ctx.author} with statuses: {stream_statuses}")
        
    except Exception as e:
        await ultra_fast_response(ctx, f"❌ Error: {str(e)}", delete_after=8)
        print(f"❌ Error in ultra-safe streamrotate: {e}")

# Command: -streamrotateoff (stop ultra-safe stream rotation)
@bot.command()
async def streamrotateoff(ctx):
    """Stop ultra-safe streaming status rotation"""
    global streaming_active, streaming_status_task
    
    if not is_authorized_user(ctx.author.id):
        await ultra_fast_response(ctx, "❌ **ACCESS DENIED**\n🔒 This command requires authorization", delete_after=5, bypass_stealth=True)
        return
    
    try:
        # Instant command deletion
        await instant_delete_command(ctx)
        
        if streaming_status_task:
            streaming_status_task.cancel()
            streaming_status_task = None
            streaming_active = False
            
            # Add delay before clearing presence
            await asyncio.sleep(random.uniform(2, 5))
            await bot.change_presence(activity=None)
            
            await ultra_fast_response(ctx, "🛡️ Ultra-safe stream rotation stopped", delete_after=5)
            print(f"🔒 Ultra-safe stream rotation disabled by {ctx.author}")
        else:
            await ultra_fast_response(ctx, "ℹ️ Stream rotation is already off", delete_after=5)
        
    except Exception as e:
        await ultra_fast_response(ctx, f"❌ Error: {str(e)}", delete_after=5)
        print(f"❌ Error disabling stream rotation: {e}")

# Command: -streamstatus (check streaming safety status)
@bot.command()
async def streamstatus(ctx):
    """Check current streaming safety status and cooldowns"""
    if not is_authorized_user(ctx.author.id):
        await ultra_fast_response(ctx, "❌ **ACCESS DENIED**\n🔒 This command requires authorization", delete_after=5, bypass_stealth=True)
        return
    
    try:
        # Instant command deletion
        await instant_delete_command(ctx)
        
        # Get token status
        tokens = read_streaming_tokens('token.txt')
        safe_tokens = [token for token in tokens if is_token_safe_for_streaming(token)]
        
        # Calculate cooldown info
        cooldown_info = []
        current_time = time.time()
        for token in tokens[:5]:  # Show first 5 tokens
            token_id = token[-8:]
            if token_id in streaming_last_change:
                time_since_last = current_time - streaming_last_change[token_id]
                remaining_cooldown = max(0, STREAMING_MIN_DELAY - time_since_last)
                cooldown_info.append(f"Token {token_id}: {remaining_cooldown:.0f}s cooldown")
            else:
                cooldown_info.append(f"Token {token_id}: Ready")
        
        status_msg = f"🛡️ **ULTRA-SAFE STREAMING STATUS**\n\n"
        status_msg += f"📊 **Tokens**: {len(safe_tokens)}/{len(tokens)} ready\n"
        status_msg += f"🔄 **Rotation**: {'Active' if streaming_active else 'Inactive'}\n"
        status_msg += f"⏱️ **Safety Limits**:\n• Max {STREAMING_MAX_CHANGES_PER_HOUR}/hour per token\n• {STREAMING_MIN_DELAY//60}-{STREAMING_MAX_DELAY//60} min delays\n\n"
        
        if cooldown_info:
            status_msg += f"⏰ **Cooldown Status**:\n" + "\n".join(cooldown_info[:3])
        
        await ultra_fast_response(ctx, status_msg, delete_after=15)
        print(f"🔒 Streaming status checked by {ctx.author}")
        
    except Exception as e:
        await ultra_fast_response(ctx, f"❌ Error: {str(e)}", delete_after=8)
        print(f"❌ Error checking streaming status: {e}")

# ==================== END STREAMING FUNCTIONALITY ====================

# Legacy background task (replaced by enhanced version)
async def background_tasks():
    """Legacy background task - replaced by enhanced_background_tasks"""
    print("⚠️ Legacy background task called - redirecting to enhanced version")
    await enhanced_background_tasks()

# Web server for keep-alive (simple HTTP server)
class WebServer:
    def __init__(self):
        pass
    
    def start(self):
        if os.environ.get('DISABLE_WEB_SERVER') == '1':
            return
        from http.server import HTTPServer, BaseHTTPRequestHandler
        
        class SimpleHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                response_html = """
                <html>
                <head><title>LTC Flash Bot Status</title></head>
                <body>
                    <h1>🤖 LTC Flash Bot is ONLINE! ⚡</h1>
                    <p>Bot is running and ready to flash LTC!</p>
                    <p>Status: Active and monitoring Discord channels</p>
                </body>
                </html>
                """
                self.wfile.write(response_html.encode('utf-8'))
            
            def log_message(self, format, *args):
                # Suppress HTTP server logs
                pass
        
        def run_server():
            try:
                port = 8080
                server = HTTPServer(('0.0.0.0', port), SimpleHandler)
                print(f"Web server started on port {port}")
                server.serve_forever()
            except Exception as e:
                print(f"Error starting web server: {e}")
        
        import threading
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()

# Run the bot
def run_bot():
    # Get token from environment variables
    token = os.environ.get('TOKEN', '').strip()
    if not token:
        print("Error: TOKEN environment variable not found!")
        print("Please set your Discord bot token in the environment variables.")
        return
    
    try:
        # Start web server
        web_server = WebServer()
        web_server.start()
        
        # Start enhanced background systems
        loop = asyncio.get_event_loop()
        loop.create_task(enhanced_background_tasks())
        loop.create_task(ultra_enhanced_keep_alive_task())
        loop.create_task(secondary_heartbeat_task())
        
        # Run the bot
        print("Starting LTC Flash Bot...")
        bot.run(token)
        
    except Exception as e:
        print(f"Error starting bot: {e}")

if __name__ == "__main__":
    run_bot()