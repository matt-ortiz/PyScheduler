import re
from typing import Optional
from .database import get_db

def generate_safe_name(display_name: str) -> str:
    """Convert display name to filesystem-safe name"""
    # Convert to lowercase
    safe = display_name.lower()
    # Replace spaces with hyphens
    safe = re.sub(r'\s+', '-', safe)
    # Remove special characters, keep only letters, numbers, hyphens
    safe = re.sub(r'[^a-z0-9-]', '', safe)
    # Remove multiple consecutive hyphens
    safe = re.sub(r'-+', '-', safe)
    # Remove leading/trailing hyphens
    safe = safe.strip('-')
    # Ensure it's not empty
    if not safe:
        safe = 'script'
    return safe

def ensure_unique_safe_name(safe_name: str, folder_id: Optional[int] = None, exclude_id: Optional[int] = None) -> str:
    """Ensure safe name is unique within folder"""
    with get_db() as conn:
        base_name = safe_name
        counter = 1
        
        while True:
            # Check if name exists (excluding current script if updating)
            query = "SELECT id FROM scripts WHERE safe_name = ? AND folder_id = ?"
            params = [safe_name, folder_id]
            
            if exclude_id:
                query += " AND id != ?"
                params.append(exclude_id)
            
            cursor = conn.execute(query, params)
            if not cursor.fetchone():
                return safe_name
            
            counter += 1
            safe_name = f"{base_name}-{counter}"

def get_folder_path(folder_id: Optional[int]) -> str:
    """Get folder path for filesystem organization"""
    if not folder_id:
        return ""
    
    with get_db() as conn:
        cursor = conn.execute("SELECT name FROM folders WHERE id = ?", (folder_id,))
        folder = cursor.fetchone()
        if folder:
            return folder["name"]
        return ""

def validate_python_version(version: str) -> bool:
    """Validate Python version format"""
    return re.match(r"^3\.(8|9|10|11|12)$", version) is not None

def validate_cron_expression(expression: str) -> bool:
    """Basic CRON expression validation"""
    # Simple validation - 5 fields separated by spaces
    fields = expression.split()
    if len(fields) != 5:
        return False
    
    # Each field should contain valid characters
    for field in fields:
        if not re.match(r'^[0-9,\-\*/]+$', field):
            return False
    
    return True

def format_duration(duration_ms: int) -> str:
    """Format duration in milliseconds to human readable format"""
    if duration_ms < 1000:
        return f"{duration_ms}ms"
    elif duration_ms < 60000:
        return f"{duration_ms / 1000:.1f}s"
    elif duration_ms < 3600000:
        return f"{duration_ms / 60000:.1f}m"
    else:
        return f"{duration_ms / 3600000:.1f}h"

def truncate_text(text: str, max_length: int = 1000) -> str:
    """Truncate text to maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."