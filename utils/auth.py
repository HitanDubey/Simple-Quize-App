"""
Authentication Utilities for EchoQuest Pro
Handles user authentication, password management, session handling,
and security-related functions
"""

import re
import hashlib
import secrets
import string
from datetime import datetime, timedelta
from functools import wraps
from flask import session, flash, redirect, url_for, request
import sqlite3

# Password validation constants
MIN_PASSWORD_LENGTH = 6
MAX_PASSWORD_LENGTH = 128
MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 50

class PasswordValidator:
    """Password strength validation and management"""
    
    @staticmethod
    def validate_strength(password):
        """
        Validate password strength
        Returns: (is_valid, message, strength_score)
        """
        errors = []
        strength_score = 0
        
        # Length check
        if len(password) < MIN_PASSWORD_LENGTH:
            errors.append(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
        elif len(password) > MAX_PASSWORD_LENGTH:
            errors.append(f"Password must be less than {MAX_PASSWORD_LENGTH} characters")
        else:
            strength_score += 20
        
        # Uppercase check
        if re.search(r'[A-Z]', password):
            strength_score += 20
        else:
            errors.append("Password should contain at least one uppercase letter")
        
        # Lowercase check
        if re.search(r'[a-z]', password):
            strength_score += 20
        else:
            errors.append("Password should contain at least one lowercase letter")
        
        # Digit check
        if re.search(r'\d', password):
            strength_score += 20
        else:
            errors.append("Password should contain at least one number")
        
        # Special character check
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            strength_score += 20
        else:
            errors.append("Password should contain at least one special character")
        
        # Common password check
        common_passwords = [
            'password', '123456', 'qwerty', 'abc123', 'password123',
            'admin', 'letmein', 'welcome', 'monkey', 'dragon'
        ]
        if password.lower() in common_passwords:
            errors.append("Password is too common. Please choose a stronger password")
            strength_score = max(0, strength_score - 50)
        
        is_valid = len(errors) == 0
        strength_level = "Weak"
        if strength_score >= 80:
            strength_level = "Strong"
        elif strength_score >= 60:
            strength_level = "Good"
        elif strength_score >= 40:
            strength_level = "Fair"
        
        return is_valid, errors, strength_score, strength_level
    
    @staticmethod
    def generate_temp_password(length=12):
        """Generate a temporary secure password"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password
    
    @staticmethod
    def hash_password(password):
        """Hash password using SHA-256 with salt"""
        salt = secrets.token_hex(16)
        hash_obj = hashlib.sha256()
        hash_obj.update((password + salt).encode('utf-8'))
        hashed = hash_obj.hexdigest()
        return f"{salt}${hashed}"
    
    @staticmethod
    def verify_password(password, stored_hash):
        """Verify password against stored hash"""
        if '$' not in stored_hash:
            return False
        salt, hash_value = stored_hash.split('$')
        hash_obj = hashlib.sha256()
        hash_obj.update((password + salt).encode('utf-8'))
        return hash_obj.hexdigest() == hash_value

class UsernameValidator:
    """Username validation and sanitization"""
    
    @staticmethod
    def validate(username):
        """
        Validate username
        Returns: (is_valid, message)
        """
        if not username:
            return False, "Username is required"
        
        if len(username) < MIN_USERNAME_LENGTH:
            return False, f"Username must be at least {MIN_USERNAME_LENGTH} characters"
        
        if len(username) > MAX_USERNAME_LENGTH:
            return False, f"Username must be less than {MAX_USERNAME_LENGTH} characters"
        
        # Allowed characters: letters, numbers, underscore, dot
        if not re.match(r'^[a-zA-Z0-9_.]+$', username):
            return False, "Username can only contain letters, numbers, underscore, and dot"
        
        # Check for consecutive dots or underscores
        if re.search(r'[_.]{2,}', username):
            return False, "Username cannot contain consecutive dots or underscores"
        
        # Check if starts/ends with dot or underscore
        if username[0] in '_.' or username[-1] in '_.':
            return False, "Username cannot start or end with dot or underscore"
        
        # Check for reserved usernames
        reserved = ['admin', 'root', 'system', 'user', 'test', 'guest', 'anonymous']
        if username.lower() in reserved:
            return False, "This username is reserved"
        
        return True, "Valid username"
    
    @staticmethod
    def sanitize(username):
        """Sanitize username by removing special characters"""
        # Remove any special characters except allowed ones
        sanitized = re.sub(r'[^a-zA-Z0-9_.]', '', username)
        # Limit length
        sanitized = sanitized[:MAX_USERNAME_LENGTH]
        return sanitized

class EmailValidator:
    """Email validation utilities"""
    
    @staticmethod
    def validate(email):
        """
        Validate email format
        Returns: (is_valid, message)
        """
        if not email:
            return False, "Email is required"
        
        # Basic email regex
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return False, "Invalid email format"
        
        # Check for common typos in domain
        email_lower = email.lower()
        common_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
        domain = email_lower.split('@')[1] if '@' in email_lower else ''
        
        if domain and domain not in common_domains:
            # Not an error, just a warning
            pass
        
        return True, "Valid email"
    
    @staticmethod
    def normalize(email):
        """Normalize email (lowercase, remove dots from gmail)"""
        if not email:
            return email
        
        email = email.lower().strip()
        
        # Gmail-specific normalization (remove dots before @)
        if '@gmail.com' in email:
            local, domain = email.split('@')
            local = local.replace('.', '')
            email = f"{local}@{domain}"
        
        return email

class SessionManager:
    """Session management utilities"""
    
    @staticmethod
    def create_session(user_id, username, email):
        """Create a new user session"""
        session.clear()
        session['user_id'] = user_id
        session['username'] = username
        session['email'] = email
        session['login_time'] = datetime.now().isoformat()
        session['session_token'] = secrets.token_hex(32)
        session['is_authenticated'] = True
        
        return session['session_token']
    
    @staticmethod
    def validate_session():
        """Validate current session"""
        if not session.get('is_authenticated'):
            return False
        
        # Check session age (max 24 hours)
        login_time = session.get('login_time')
        if login_time:
            login_datetime = datetime.fromisoformat(login_time)
            if datetime.now() - login_datetime > timedelta(hours=24):
                session.clear()
                return False
        
        return True
    
    @staticmethod
    def destroy_session():
        """Destroy current session"""
        session.clear()
        return True
    
    @staticmethod
    def get_current_user():
        """Get current user from session"""
        if SessionManager.validate_session():
            return {
                'user_id': session.get('user_id'),
                'username': session.get('username'),
                'email': session.get('email')
            }
        return None

class RateLimiter:
    """Rate limiting for login attempts and API requests"""
    
    def __init__(self):
        self.attempts = {}
    
    def is_allowed(self, key, max_attempts=5, time_window=300):
        """
        Check if action is allowed
        key: identifier (IP, username, etc.)
        max_attempts: maximum attempts in time_window
        time_window: time window in seconds
        """
        now = datetime.now()
        
        if key not in self.attempts:
            self.attempts[key] = []
        
        # Clean old attempts
        self.attempts[key] = [
            attempt for attempt in self.attempts[key]
            if (now - attempt).total_seconds() < time_window
        ]
        
        if len(self.attempts[key]) >= max_attempts:
            return False, f"Too many attempts. Please wait {time_window} seconds"
        
        self.attempts[key].append(now)
        return True, "Allowed"
    
    def reset(self, key):
        """Reset attempts for a key"""
        if key in self.attempts:
            del self.attempts[key]

# Global rate limiter instance
login_rate_limiter = RateLimiter()

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_authenticated'):
            flash('Please login to access this page', 'warning')
            return redirect(url_for('login'))
        
        if not SessionManager.validate_session():
            flash('Session expired. Please login again', 'warning')
            return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_authenticated'):
            flash('Please login to access this page', 'warning')
            return redirect(url_for('login'))
        
        if not session.get('is_admin', False):
            flash('Admin access required', 'error')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def get_user_by_username(username):
    """Get user from database by username"""
    try:
        conn = sqlite3.connect('db.sqlite3')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None
    except Exception as e:
        print(f"Database error: {e}")
        return None

def get_user_by_email(email):
    """Get user from database by email"""
    try:
        conn = sqlite3.connect('db.sqlite3')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None
    except Exception as e:
        print(f"Database error: {e}")
        return None

def create_user(username, email, password):
    """Create a new user in database"""
    try:
        # Validate inputs
        is_valid, username_msg = UsernameValidator.validate(username)
        if not is_valid:
            return False, username_msg
        
        is_valid, email_msg = EmailValidator.validate(email)
        if not is_valid:
            return False, email_msg
        
        is_valid, password_errors, strength_score, strength_level = PasswordValidator.validate_strength(password)
        if not is_valid:
            return False, password_errors[0] if password_errors else "Invalid password"
        
        # Check if user exists
        if get_user_by_username(username):
            return False, "Username already exists"
        
        if get_user_by_email(email):
            return False, "Email already registered"
        
        # Hash password
        hashed_password = PasswordValidator.hash_password(password)
        
        # Insert user
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, email, password, total_score, quizzes_taken, level, xp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (username, email, hashed_password, 0, 0, 1, 0))
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return True, user_id
    except Exception as e:
        print(f"Error creating user: {e}")
        return False, "Database error"

def authenticate_user(username, password, ip_address=None):
    """Authenticate a user"""
    # Rate limiting
    if ip_address:
        allowed, message = login_rate_limiter.is_allowed(ip_address)
        if not allowed:
            return False, message
    
    # Get user
    user = get_user_by_username(username)
    if not user:
        # Also try email
        user = get_user_by_email(username)
    
    if not user:
        return False, "Invalid username/email or password"
    
    # Verify password
    if not PasswordValidator.verify_password(password, user['password']):
        return False, "Invalid username/email or password"
    
    # Reset rate limiter on success
    if ip_address:
        login_rate_limiter.reset(ip_address)
    
    return True, user

def update_user_password(user_id, new_password):
    """Update user password"""
    try:
        is_valid, errors, strength_score, strength_level = PasswordValidator.validate_strength(new_password)
        if not is_valid:
            return False, errors[0] if errors else "Invalid password"
        
        hashed_password = PasswordValidator.hash_password(new_password)
        
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_password, user_id))
        conn.commit()
        conn.close()
        
        return True, "Password updated successfully"
    except Exception as e:
        print(f"Error updating password: {e}")
        return False, "Database error"

def update_user_profile(user_id, **kwargs):
    """Update user profile fields"""
    try:
        allowed_fields = ['avatar', 'level', 'xp', 'total_score', 'quizzes_taken']
        updates = []
        values = []
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                updates.append(f"{field} = ?")
                values.append(value)
        
        if not updates:
            return False, "No valid fields to update"
        
        values.append(user_id)
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
        
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        cursor.execute(query, values)
        conn.commit()
        conn.close()
        
        return True, "Profile updated"
    except Exception as e:
        print(f"Error updating profile: {e}")
        return False, "Database error"

def get_user_stats(user_id):
    """Get user statistics"""
    try:
        conn = sqlite3.connect('db.sqlite3')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get user info
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        # Get quiz stats
        cursor.execute('''
            SELECT 
                COUNT(*) as total_quizzes,
                SUM(score) as total_score,
                AVG(score) as avg_score,
                MAX(score) as best_score
            FROM quiz_sessions 
            WHERE user_id = ? AND completed = 1
        ''', (user_id,))
        quiz_stats = cursor.fetchone()
        
        # Get topic stats
        cursor.execute('''
            SELECT topic, COUNT(*) as times_played, AVG(percentage) as avg_percentage
            FROM leaderboard 
            WHERE user_id = ? 
            GROUP BY topic 
            ORDER BY times_played DESC 
            LIMIT 5
        ''', (user_id,))
        top_topics = cursor.fetchall()
        
        conn.close()
        
        return {
            'user': dict(user) if user else None,
            'quiz_stats': dict(quiz_stats) if quiz_stats else None,
            'top_topics': [dict(t) for t in top_topics]
        }
    except Exception as e:
        print(f"Error getting user stats: {e}")
        return None

def generate_reset_token(email):
    """Generate password reset token"""
    token = secrets.token_urlsafe(32)
    expiry = datetime.now() + timedelta(hours=24)
    
    # Store token in database (you'd need a password_resets table)
    # For now, just return token
    return token, expiry

def verify_reset_token(token):
    """Verify password reset token"""
    # Check token in database
    # For now, just return True
    return True

def log_user_activity(user_id, action, details=None):
    """Log user activity for audit"""
    try:
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        
        # Create activity log table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT,
                details TEXT,
                ip_address TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            INSERT INTO user_activity (user_id, action, details)
            VALUES (?, ?, ?)
        ''', (user_id, action, details))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error logging activity: {e}")
        return False

# Security headers middleware
def add_security_headers(response):
    """Add security headers to response"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# CSRF protection
def generate_csrf_token():
    """Generate CSRF token"""
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']

def validate_csrf_token(token):
    """Validate CSRF token"""
    return token == session.get('csrf_token')

# Export all utilities
__all__ = [
    'PasswordValidator',
    'UsernameValidator', 
    'EmailValidator',
    'SessionManager',
    'RateLimiter',
    'login_required',
    'admin_required',
    'authenticate_user',
    'create_user',
    'get_user_by_username',
    'get_user_by_email',
    'update_user_password',
    'update_user_profile',
    'get_user_stats',
    'generate_reset_token',
    'verify_reset_token',
    'log_user_activity',
    'add_security_headers',
    'generate_csrf_token',
    'validate_csrf_token'
]