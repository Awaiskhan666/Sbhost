"""
Enhanced Security Module for Discord Selfbot
Provides advanced anti-detection, behavioral mimicking, and security monitoring
"""

import random
import time
import asyncio
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

class EnhancedSecurity:
    def __init__(self, bot):
        self.bot = bot
        self.failed_attempts = {}  # Track failed access attempts
        self.session_tokens = {}   # Secure session management
        self.presence_rotation = PresenceManager()
        self.behavior_mimicker = BehaviorMimicker()
        self.anti_detection = AntiDetectionSystem()
        
    def generate_session_token(self, user_id: str) -> str:
        """Generate secure session token for user"""
        token = secrets.token_urlsafe(32)
        expiry = datetime.utcnow() + timedelta(minutes=30)
        
        self.session_tokens[user_id] = {
            'token': token,
            'expires': expiry,
            'created': datetime.utcnow()
        }
        return token
    
    def validate_session(self, user_id: str, token: str) -> bool:
        """Validate user session token"""
        if user_id not in self.session_tokens:
            return False
            
        session = self.session_tokens[user_id]
        if datetime.utcnow() > session['expires']:
            del self.session_tokens[user_id]
            return False
            
        return session['token'] == token
    
    def log_failed_attempt(self, user_id: str, command: str, reason: str):
        """Log failed access attempts for security monitoring"""
        if user_id not in self.failed_attempts:
            self.failed_attempts[user_id] = []
            
        self.failed_attempts[user_id].append({
            'command': command,
            'reason': reason,
            'timestamp': datetime.utcnow(),
            'ip_hash': hashlib.md5(str(user_id).encode()).hexdigest()[:8]
        })
        
        # Clean old attempts (older than 1 hour)
        cutoff = datetime.utcnow() - timedelta(hours=1)
        self.failed_attempts[user_id] = [
            attempt for attempt in self.failed_attempts[user_id]
            if attempt['timestamp'] > cutoff
        ]
        
        # Check for suspicious activity
        if len(self.failed_attempts[user_id]) > 5:
            print(f"🚨 SECURITY ALERT: Multiple failed attempts from user {user_id}")
    
    def is_rate_limited(self, user_id: str) -> bool:
        """Check if user is rate limited"""
        if user_id not in self.failed_attempts:
            return False
            
        recent_attempts = len([
            attempt for attempt in self.failed_attempts[user_id]
            if attempt['timestamp'] > datetime.utcnow() - timedelta(minutes=5)
        ])
        
        return recent_attempts >= 3

class PresenceManager:
    def __init__(self):
        self.activities = [
            {"name": "🌙 Sleeping", "type": "playing"},
            {"name": "💤 Dreaming", "type": "playing"},
            {"name": "🎮 Gaming", "type": "playing"},
            {"name": "📱 Phone", "type": "playing"},
            {"name": "💻 Coding", "type": "playing"},
            {"name": "🎵 Music", "type": "listening"},
            {"name": "📺 YouTube", "type": "watching"},
            {"name": "🍕 Food", "type": "playing"},
        ]
        self.last_rotation = datetime.utcnow()
        self.current_activity = None
    
    def get_random_activity(self) -> Dict:
        """Get a random human-like activity"""
        return random.choice(self.activities)
    
    def should_rotate(self) -> bool:
        """Check if presence should be rotated"""
        return datetime.utcnow() - self.last_rotation > timedelta(minutes=random.randint(10, 15))
    
    async def rotate_presence(self, bot):
        """Rotate bot presence to mimic human behavior"""
        if not self.should_rotate():
            return
            
        try:
            activity = self.get_random_activity()
            
            # Temporarily disabled due to Discord API compatibility
            # This prevents MessageToDict errors while maintaining functionality
            print(f"🔄 Would rotate presence to: {activity['name']} (disabled for stability)")
            
            self.current_activity = activity
            self.last_rotation = datetime.utcnow()
            
        except Exception as e:
            print(f"⚠️ Presence rotation skipped: {e}")

class BehaviorMimicker:
    def __init__(self):
        self.typing_delays = (0.5, 2.0)  # Realistic typing speeds
        self.response_delays = (0.3, 0.8)  # Human-like response times
        self.last_command_time = {}
        
    def get_human_delay(self, command_type: str = "normal") -> float:
        """Get human-like delay based on command type"""
        if command_type == "typing":
            return random.uniform(*self.typing_delays)
        elif command_type == "fast":
            return random.uniform(0.1, 0.3)
        else:
            return random.uniform(*self.response_delays)
    
    def should_add_typing(self, channel) -> bool:
        """Determine if typing indicator should be shown"""
        return random.random() < 0.3  # 30% chance for natural feel
    
    async def mimic_typing(self, channel, duration: float = None):
        """Show typing indicator for realistic duration"""
        if duration is None:
            duration = self.get_human_delay("typing")
            
        try:
            async with channel.typing():
                await asyncio.sleep(duration)
        except Exception:
            pass  # Ignore typing errors

class AntiDetectionSystem:
    def __init__(self):
        self.command_intervals = {}  # Track command timing
        self.daily_limits = {
            "spam": 50,
            "drown": 30,
            "debate": 25,
            "flash": 100
        }
        self.daily_usage = {}
        self.last_reset = datetime.utcnow().date()
        
    def check_daily_limits(self, command: str) -> bool:
        """Check if command is within daily limits"""
        today = datetime.utcnow().date()
        
        # Reset daily counters if new day
        if today != self.last_reset:
            self.daily_usage = {}
            self.last_reset = today
            
        # Check limit
        if command in self.daily_limits:
            current_usage = self.daily_usage.get(command, 0)
            if current_usage >= self.daily_limits[command]:
                return False
            
            self.daily_usage[command] = current_usage + 1
            
        return True
    
    def get_safe_interval(self, command: str) -> float:
        """Get safe interval between commands"""
        base_intervals = {
            "spam": 2.0,
            "drown": 3.0,
            "debate": 2.5,
            "flash": 1.0,
            "normal": 0.5
        }
        
        base = base_intervals.get(command, base_intervals["normal"])
        # Add randomization for natural behavior
        return base + random.uniform(0.1, 0.5)
    
    def log_command_usage(self, command: str, user_id: str):
        """Log command usage for pattern analysis"""
        now = datetime.utcnow()
        
        if user_id not in self.command_intervals:
            self.command_intervals[user_id] = {}
            
        if command not in self.command_intervals[user_id]:
            self.command_intervals[user_id][command] = []
            
        # Keep only last 10 command times
        self.command_intervals[user_id][command].append(now)
        self.command_intervals[user_id][command] = self.command_intervals[user_id][command][-10:]

# Global security instance
security_manager = None

def initialize_security(bot):
    """Initialize the security system"""
    global security_manager
    security_manager = EnhancedSecurity(bot)
    return security_manager

def get_security_manager():
    """Get the global security manager instance"""
    return security_manager

# Enhanced command wrapper with security features
def secure_command(original_command):
    """Decorator to add security features to commands"""
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            # Add anti-detection delay
            if security_manager:
                delay = security_manager.anti_detection.get_safe_interval("normal")
                await asyncio.sleep(delay)
            
            # Execute original command
            result = await original_command(*args, **kwargs)
            
            # Log successful execution time
            execution_time = time.time() - start_time
            print(f"⚡ Command executed in {execution_time:.3f}s")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"❌ Command failed after {execution_time:.3f}s: {e}")
            raise
            
    return wrapper