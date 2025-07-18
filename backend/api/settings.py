from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import json
import secrets
from pathlib import Path

from ..email_service import EmailService, test_email_connection

router = APIRouter()

class EmailSettings(BaseModel):
    smtp_server: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    from_email: str

class AppSettings(BaseModel):
    default_script_timeout: int = 300
    default_memory_limit: int = 512
    rate_limit_enabled: bool = True
    log_retention_days: int = 30
    max_execution_logs: int = 1000
    api_key: str = "default-api-key-change-me"

# Settings file path
SETTINGS_FILE = Path(os.getenv("TEMPO_DATA_PATH", "/data")) / "settings.json"

def load_settings() -> Dict[str, Any]:
    """Load settings from file"""
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")
    
    # Return defaults
    return {
        "app_settings": {
            "default_script_timeout": 300,
            "default_memory_limit": 512,
            "rate_limit_enabled": True,
            "log_retention_days": 30,
            "max_execution_logs": 1000,
            "api_key": "default-api-key-change-me"
        },
        "email_settings": {
            "smtp_server": "",
            "smtp_port": 2525,
            "smtp_username": "",
            "smtp_password": "",
            "from_email": "tempo@example.com"
        }
    }

def save_settings(settings: Dict[str, Any]) -> bool:
    """Save settings to file"""
    try:
        # Ensure directory exists
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False

@router.get("/")
async def get_settings():
    """Get all settings"""
    return load_settings()

@router.put("/")
async def update_settings(settings: Dict[str, Any]):
    """Update all settings"""
    if save_settings(settings):
        return {"message": "Settings updated successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to save settings")

@router.get("/email")
async def get_email_settings():
    """Get email settings"""
    settings = load_settings()
    return settings.get("email_settings", {})

@router.put("/email")
async def update_email_settings(email_settings: EmailSettings):
    """Update email settings"""
    settings = load_settings()
    settings["email_settings"] = email_settings.dict()
    
    if save_settings(settings):
        return {"message": "Email settings updated successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to save email settings")

@router.post("/email/test")
async def test_email_settings(email_settings: EmailSettings):
    """Test email settings"""
    try:
        # Create a temporary email service with the provided settings
        test_service = EmailService()
        test_service.smtp_server = email_settings.smtp_server
        test_service.smtp_port = email_settings.smtp_port
        test_service.smtp_username = email_settings.smtp_username
        test_service.smtp_password = email_settings.smtp_password
        test_service.from_email = email_settings.from_email
        test_service.enabled = True
        
        # Test the connection
        result = test_service.test_connection()
        
        if result["success"]:
            return {"success": True, "message": "Email connection test successful"}
        else:
            return {"success": False, "error": result["error"]}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/app")
async def get_app_settings():
    """Get application settings"""
    settings = load_settings()
    return settings.get("app_settings", {})

@router.put("/app")
async def update_app_settings(app_settings: AppSettings):
    """Update application settings"""
    settings = load_settings()
    settings["app_settings"] = app_settings.dict()
    
    if save_settings(settings):
        return {"message": "Application settings updated successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to save application settings")

@router.post("/api-key/generate")
async def generate_api_key():
    """Generate a new API key"""
    # Generate a cryptographically secure random API key
    api_key = secrets.token_urlsafe(32)
    
    # Update the settings with the new API key
    settings = load_settings()
    if "app_settings" not in settings:
        settings["app_settings"] = {}
    settings["app_settings"]["api_key"] = api_key
    
    if save_settings(settings):
        return {"api_key": api_key, "message": "API key generated successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to save new API key")