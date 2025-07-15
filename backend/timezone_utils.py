from datetime import datetime
from typing import Optional, List
import pytz

# Common timezone choices for the frontend
TIMEZONE_CHOICES = [
    ('UTC', 'UTC'),
    ('US/Eastern', 'Eastern Time'),
    ('US/Central', 'Central Time'),
    ('US/Mountain', 'Mountain Time'),
    ('US/Pacific', 'Pacific Time'),
    ('America/New_York', 'New York'),
    ('America/Chicago', 'Chicago'),
    ('America/Denver', 'Denver'),
    ('America/Los_Angeles', 'Los Angeles'),
    ('Europe/London', 'London'),
    ('Europe/Paris', 'Paris'),
    ('Europe/Berlin', 'Berlin'),
    ('Asia/Tokyo', 'Tokyo'),
    ('Asia/Shanghai', 'Shanghai'),
    ('Australia/Sydney', 'Sydney'),
]

def get_timezone_list() -> List[dict]:
    """Get a list of common timezones for frontend dropdown"""
    return [
        {"value": tz_key, "label": tz_label}
        for tz_key, tz_label in TIMEZONE_CHOICES
    ]

def format_datetime_for_api(dt: datetime) -> str:
    """Format datetime for API response with proper UTC indicator"""
    if dt is None:
        return None
    
    # Ensure datetime is in UTC
    if dt.tzinfo is None:
        # Assume naive datetime is UTC
        dt = pytz.UTC.localize(dt)
    elif dt.tzinfo != pytz.UTC:
        # Convert to UTC
        dt = dt.astimezone(pytz.UTC)
    
    # Return ISO format with Z suffix for UTC
    return dt.isoformat().replace('+00:00', 'Z')

def convert_to_user_timezone(dt: datetime, user_timezone: str) -> datetime:
    """Convert UTC datetime to user's timezone"""
    if dt is None:
        return None
    
    # Ensure datetime is in UTC
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    
    # Convert to user's timezone
    try:
        user_tz = pytz.timezone(user_timezone)
        return dt.astimezone(user_tz)
    except Exception:
        # Fall back to UTC if timezone is invalid
        return dt

def validate_timezone(timezone_str: str) -> bool:
    """Validate if timezone string is valid"""
    try:
        pytz.timezone(timezone_str)
        return True
    except Exception:
        return False