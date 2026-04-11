"""
Helper Utilities for EchoQuest Pro
Provides various helper functions for data processing, formatting,
validation, and general utility operations
"""

import re
import json
import random
import string
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, List, Any, Optional, Tuple
import hashlib

# ==================== STRING HELPERS ====================

def clean_text(text: str, max_length: int = 500) -> str:
    """Clean and sanitize text"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters (keep basic punctuation)
    text = re.sub(r'[^\w\s\?\.\!\,\:\;\"\'\-\/\(\)]', '', text)
    
    # Trim length
    if len(text) > max_length:
        text = text[:max_length] + "..."
    
    return text.strip()

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length"""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length].rsplit(' ', 1)[0] + suffix

def slugify(text: str) -> str:
    """Convert text to URL-friendly slug"""
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Replace spaces with hyphens
    text = re.sub(r'\s+', '-', text)
    
    # Remove special characters
    text = re.sub(r'[^\w\-]', '', text)
    
    # Remove multiple hyphens
    text = re.sub(r'-+', '-', text)
    
    return text.strip('-')

def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """Extract important keywords from text"""
    if not text:
        return []
    
    # Remove common words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                  'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being'}
    
    # Tokenize
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    
    # Count frequency
    word_count = {}
    for word in words:
        if word not in stop_words:
            word_count[word] = word_count.get(word, 0) + 1
    
    # Sort by frequency
    sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
    
    return [word for word, count in sorted_words[:max_keywords]]

# ==================== DATE & TIME HELPERS ====================

def format_datetime(dt: datetime, format_type: str = 'full') -> str:
    """Format datetime in various formats"""
    if not dt:
        return ""
    
    formats = {
        'full': '%Y-%m-%d %H:%M:%S',
        'date': '%Y-%m-%d',
        'time': '%H:%M:%S',
        'readable': '%B %d, %Y at %I:%M %p',
        'short': '%m/%d/%y %H:%M',
        'filename': '%Y%m%d_%H%M%S'
    }
    
    return dt.strftime(formats.get(format_type, formats['full']))

def time_ago(dt: datetime) -> str:
    """Get human-readable time difference"""
    if not dt:
        return ""
    
    now = datetime.now()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 604800:
        days = int(seconds // 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif seconds < 2592000:
        weeks = int(seconds // 604800)
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    elif seconds < 31536000:
        months = int(seconds // 2592000)
        return f"{months} month{'s' if months != 1 else ''} ago"
    else:
        years = int(seconds // 31536000)
        return f"{years} year{'s' if years != 1 else ''} ago"

def get_date_range(range_type: str = 'week') -> Tuple[datetime, datetime]:
    """Get date range for filtering"""
    now = datetime.now()
    
    if range_type == 'day':
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif range_type == 'week':
        start = now - timedelta(days=7)
        end = now
    elif range_type == 'month':
        start = now - timedelta(days=30)
        end = now
    elif range_type == 'year':
        start = now - timedelta(days=365)
        end = now
    else:
        start = datetime(2020, 1, 1)
        end = now
    
    return start, end

# ==================== NUMBER HELPERS ====================

def format_number(num: int, style: str = 'decimal') -> str:
    """Format numbers with suffixes"""
    if not num:
        return "0"
    
    if style == 'decimal':
        return f"{num:,}"
    elif style == 'abbreviate':
        if num >= 1_000_000:
            return f"{num/1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num/1_000:.1f}K"
        else:
            return str(num)
    elif style == 'ordinal':
        if 10 <= num % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(num % 10, 'th')
        return f"{num}{suffix}"
    
    return str(num)

def calculate_percentage(part: float, total: float, decimals: int = 1) -> float:
    """Calculate percentage"""
    if total == 0:
        return 0.0
    
    return round((part / total) * 100, decimals)

def get_grade(percentage: float) -> Dict[str, Any]:
    """Get grade based on percentage"""
    if percentage >= 90:
        return {'grade': 'A+', 'text': 'Excellent', 'color': '#4CAF50', 'icon': '🏆'}
    elif percentage >= 80:
        return {'grade': 'A', 'text': 'Very Good', 'color': '#8BC34A', 'icon': '⭐'}
    elif percentage >= 70:
        return {'grade': 'B', 'text': 'Good', 'color': '#FFC107', 'icon': '👍'}
    elif percentage >= 60:
        return {'grade': 'C', 'text': 'Average', 'color': '#FF9800', 'icon': '📚'}
    elif percentage >= 50:
        return {'grade': 'D', 'text': 'Below Average', 'color': '#F44336', 'icon': '⚠️'}
    else:
        return {'grade': 'F', 'text': 'Needs Improvement', 'color': '#9E9E9E', 'icon': '💪'}

# ==================== JSON HELPERS ====================

def safe_json_loads(json_string: str, default: Any = None) -> Any:
    """Safely parse JSON string"""
    if not json_string:
        return default
    
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return default

def safe_json_dumps(data: Any, default: str = '{}') -> str:
    """Safely convert to JSON string"""
    try:
        return json.dumps(data, ensure_ascii=False)
    except (TypeError, ValueError):
        return default

# ==================== VALIDATION HELPERS ====================

def is_valid_url(url: str) -> bool:
    """Check if string is a valid URL"""
    if not url:
        return False
    
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return bool(url_pattern.match(url))

def is_valid_email(email: str) -> bool:
    """Validate email format"""
    if not email:
        return False
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))

def is_valid_phone(phone: str) -> bool:
    """Validate phone number format"""
    if not phone:
        return False
    
    # Remove common separators
    cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)
    
    # Check if contains only digits and is reasonable length
    return cleaned.isdigit() and 7 <= len(cleaned) <= 15

# ==================== RANDOM GENERATORS ====================

def generate_random_string(length: int = 10, include_digits: bool = True) -> str:
    """Generate random string"""
    chars = string.ascii_letters
    if include_digits:
        chars += string.digits
    
    return ''.join(random.choice(chars) for _ in range(length))

def generate_quiz_id() -> str:
    """Generate unique quiz ID"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_part = generate_random_string(6, True)
    return f"quiz_{timestamp}_{random_part}"

def get_random_items(items: List[Any], count: int = 1) -> List[Any]:
    """Get random items from list"""
    if not items:
        return []
    
    count = min(count, len(items))
    return random.sample(items, count)

# ==================== DATA PROCESSING ====================

def group_by_key(data: List[Dict], key: str) -> Dict:
    """Group list of dicts by a key"""
    result = {}
    
    for item in data:
        group_key = item.get(key)
        if group_key not in result:
            result[group_key] = []
        result[group_key].append(item)
    
    return result

def sort_by_key(data: List[Dict], key: str, reverse: bool = False) -> List[Dict]:
    """Sort list of dicts by a key"""
    return sorted(data, key=lambda x: x.get(key, 0), reverse=reverse)

def unique_list(items: List[Any], preserve_order: bool = True) -> List[Any]:
    """Get unique items from list"""
    if not preserve_order:
        return list(set(items))
    
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    
    return result

# ==================== CACHE HELPERS ====================

class SimpleCache:
    """Simple in-memory cache"""
    
    def __init__(self, default_ttl: int = 300):
        self.cache = {}
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Any:
        """Get item from cache"""
        if key in self.cache:
            value, expiry = self.cache[key]
            if datetime.now() < expiry:
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> None:
        """Set item in cache"""
        if ttl is None:
            ttl = self.default_ttl
        
        expiry = datetime.now() + timedelta(seconds=ttl)
        self.cache[key] = (value, expiry)
    
    def delete(self, key: str) -> None:
        """Delete item from cache"""
        if key in self.cache:
            del self.cache[key]
    
    def clear(self) -> None:
        """Clear all cache"""
        self.cache.clear()

# ==================== DECORATORS ====================

def timing_decorator(func):
    """Decorator to measure function execution time"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = datetime.now()
        result = func(*args, **kwargs)
        end = datetime.now()
        duration = (end - start).total_seconds()
        print(f"{func.__name__} took {duration:.3f} seconds")
        return result
    return wrapper

def retry_decorator(max_attempts: int = 3, delay: int = 1):
    """Decorator to retry function on failure"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise e
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

# ==================== QUIZ SPECIFIC HELPERS ====================

def calculate_quiz_score(correct_count: int, total_questions: int, time_bonus: int = 0) -> int:
    """Calculate quiz score with bonuses"""
    base_score = correct_count * 10
    return base_score + time_bonus

def get_difficulty_from_score(correct_count: int, total_answered: int) -> str:
    """Determine next question difficulty based on performance"""
    if total_answered == 0:
        return 'medium'
    
    accuracy = correct_count / total_answered
    
    if accuracy > 0.7:
        return 'hard'
    elif accuracy < 0.4:
        return 'easy'
    else:
        return 'medium'

def calculate_time_bonus(time_taken: int, max_time: int = 20) -> int:
    """Calculate time bonus for quick answers"""
    if time_taken <= 5:
        return 5
    elif time_taken <= 10:
        return 2
    else:
        return 0

# ==================== BROWSER DETECTION ====================

def parse_user_agent(user_agent: str) -> Dict[str, str]:
    """Parse user agent string"""
    result = {
        'browser': 'Unknown',
        'os': 'Unknown',
        'device': 'Desktop'
    }
    
    if not user_agent:
        return result
    
    # Simple browser detection
    if 'Chrome' in user_agent and 'Edg' not in user_agent:
        result['browser'] = 'Chrome'
    elif 'Firefox' in user_agent:
        result['browser'] = 'Firefox'
    elif 'Safari' in user_agent and 'Chrome' not in user_agent:
        result['browser'] = 'Safari'
    elif 'Edg' in user_agent:
        result['browser'] = 'Edge'
    
    # OS detection
    if 'Windows' in user_agent:
        result['os'] = 'Windows'
    elif 'Mac' in user_agent:
        result['os'] = 'macOS'
    elif 'Linux' in user_agent:
        result['os'] = 'Linux'
    elif 'Android' in user_agent:
        result['os'] = 'Android'
        result['device'] = 'Mobile'
    elif 'iPhone' in user_agent or 'iPad' in user_agent:
        result['os'] = 'iOS'
        result['device'] = 'Mobile'
    
    return result

# ==================== EXPORT ALL ====================

__all__ = [
    'clean_text',
    'truncate_text', 
    'slugify',
    'extract_keywords',
    'format_datetime',
    'time_ago',
    'get_date_range',
    'format_number',
    'calculate_percentage',
    'get_grade',
    'safe_json_loads',
    'safe_json_dumps',
    'is_valid_url',
    'is_valid_email',
    'is_valid_phone',
    'generate_random_string',
    'generate_quiz_id',
    'get_random_items',
    'group_by_key',
    'sort_by_key',
    'unique_list',
    'SimpleCache',
    'timing_decorator',
    'retry_decorator',
    'calculate_quiz_score',
    'get_difficulty_from_score',
    'calculate_time_bonus',
    'parse_user_agent'
]