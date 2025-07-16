# Tempo - Technical Architecture

## Overview

This document defines the technical architecture for **Tempo**, a web-based Python script scheduling and monitoring platform. The architecture prioritizes simplicity, reliability, and ease of deployment while providing all necessary functionality for script management and execution.

## Design Principles

### Core Principles
- **Simplicity First** - Choose simple solutions over complex ones
- **Single Container** - All services in one container for easy deployment
- **File-based Storage** - Use SQLite and filesystem for data persistence
- **Real-time Updates** - WebSocket for live monitoring capabilities
- **Resource Efficient** - Minimal memory and CPU usage
- **Easy Backup** - Simple file-based backup and restore

### Architecture Goals
- **Fast Development** - Get a working system quickly
- **Easy Deployment** - One-command setup on home servers
- **Low Maintenance** - Minimal ongoing administration
- **Reliable Operation** - Handle failures gracefully
- **Clear Debugging** - Easy to troubleshoot when issues arise

## System Architecture

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Browser   │    │   Tempo   │    │   File System   │
│                 │    │   Container     │    │                 │
│  - Vue.js App   │◄──►│                 │◄──►│  - SQLite DB    │
│  - WebSocket    │    │  - FastAPI      │    │  - Scripts      │
│  - Real-time UI │    │  - Celery       │    │  - Venvs        │
└─────────────────┘    │  - Redis        │    │  - Logs         │
                       │  - Nginx        │    └─────────────────┘
                       └─────────────────┘
```

### Component Overview
- **FastAPI Backend** - REST API and WebSocket server
- **Vue.js Frontend** - Modern web interface with real-time updates
- **Celery Worker** - Background task execution for scripts
- **Redis** - Task queue and caching
- **SQLite Database** - Metadata storage (scripts, schedules, logs)
- **File System** - Script storage and virtual environments
- **Nginx** - Static file serving and reverse proxy

## Database Design

### SQLite Schema
```sql
-- Scripts table - Core script metadata
CREATE TABLE scripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,              -- Display name (e.g., "Hello World")
    safe_name TEXT NOT NULL,         -- Filesystem name (e.g., "hello-world")
    description TEXT DEFAULT '',
    content TEXT NOT NULL,
    folder_id INTEGER REFERENCES folders(id),
    
    -- Environment settings
    python_version TEXT DEFAULT '3.12',
    requirements TEXT DEFAULT '',
    
    -- Status and statistics
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_executed_at TIMESTAMP,
    execution_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    
    -- Email notifications
    email_notifications BOOLEAN DEFAULT false,
    email_recipients TEXT DEFAULT '',
    
    -- Environment variables and auto-save
    environment_variables TEXT DEFAULT '{}',  -- JSON object of env vars
    auto_save BOOLEAN DEFAULT true,
    
    UNIQUE(name, folder_id),
    UNIQUE(safe_name, folder_id)     -- Ensure safe names are unique within folders
);

-- Folders table - Simple organization
CREATE TABLE folders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    parent_id INTEGER REFERENCES folders(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(name, parent_id)
);

-- Triggers table - Scheduling configuration
CREATE TABLE triggers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    script_id INTEGER REFERENCES scripts(id) ON DELETE CASCADE,
    trigger_type TEXT NOT NULL, -- 'interval', 'cron', 'manual', 'startup'
    
    -- JSON configuration for trigger parameters
    config TEXT NOT NULL,
    -- Examples:
    -- Interval: {"seconds": 3600}
    -- CRON: {"expression": "0 */6 * * *", "timezone": "UTC"}
    
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_triggered_at TIMESTAMP,
    next_run_at TIMESTAMP
);

-- Execution logs table - History and monitoring
CREATE TABLE execution_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    script_id INTEGER REFERENCES scripts(id) ON DELETE CASCADE,
    trigger_id INTEGER REFERENCES triggers(id) ON DELETE SET NULL,
    
    -- Execution timing
    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    duration_ms INTEGER,
    
    -- Execution results
    status TEXT NOT NULL, -- 'running', 'success', 'failed', 'timeout'
    exit_code INTEGER,
    stdout TEXT,
    stderr TEXT,
    
    -- Resource usage
    max_memory_mb INTEGER,
    max_cpu_percent DECIMAL(5,2),
    
    -- Metadata
    triggered_by TEXT, -- 'schedule', 'manual', 'startup'
    
    INDEX(script_id, started_at DESC),
    INDEX(status, started_at DESC)
);

-- Users table - Simple authentication
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    
    -- User preferences
    theme TEXT DEFAULT 'dark',
    timezone TEXT DEFAULT 'UTC',
    
    -- Status
    is_admin BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
);

-- Settings table - Application configuration
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    description TEXT
);
```

## Backend Implementation

### FastAPI Application Structure
```python
# main.py - Application entry point
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from api import scripts, folders, auth, logs, execution
from websocket_manager import WebSocketManager
from database import init_database

app = FastAPI(
    title="Tempo",
    description="Python Script Scheduler & Monitor",
    version="1.0.0"
)

# Initialize database
init_database()

# WebSocket manager for real-time updates
ws_manager = WebSocketManager()

# API routes
app.include_router(scripts.router, prefix="/api/scripts", tags=["scripts"])
app.include_router(folders.router, prefix="/api/folders", tags=["folders"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(logs.router, prefix="/api/logs", tags=["logs"])
app.include_router(execution.router, prefix="/api/execution", tags=["execution"])

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)

# Serve frontend static files
app.mount("/", StaticFiles(directory="dist", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Database Connection
```python
# database.py - Simple SQLite management
import sqlite3
import os
from contextlib import contextmanager
from pathlib import Path

DATABASE_PATH = Path(os.getenv("PYSCHED_DATA_PATH", "/data")) / "pyscheduler.db"

@contextmanager
def get_db():
    """Database connection context manager"""
    conn = sqlite3.connect(str(DATABASE_PATH), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_database():
    """Initialize database with schema"""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with get_db() as conn:
        conn.executescript("""
            -- Create all tables as defined in schema above
            -- (Full schema creation script)
        """)
        
        # Create default admin user if none exists
        cursor = conn.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            from auth import hash_password
            conn.execute("""
                INSERT INTO users (username, email, password_hash, is_admin)
                VALUES ('admin', 'admin@localhost', ?, true)
            """, (hash_password("admin"),))
```

### Script Management API
```python
# api/scripts.py - Script management endpoints
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
import json

from database import get_db
from auth import get_current_user
from virtual_env import VirtualEnvironmentManager
from utils import generate_safe_name, get_folder_path

router = APIRouter()

def generate_safe_name(display_name: str) -> str:
    """Convert display name to filesystem-safe name"""
    import re
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

def ensure_unique_safe_name(safe_name: str, folder_id: int = None) -> str:
    """Ensure safe name is unique within folder"""
    with get_db() as conn:
        base_name = safe_name
        counter = 1
        
        while True:
            cursor = conn.execute(
                "SELECT id FROM scripts WHERE safe_name = ? AND folder_id = ?",
                (safe_name, folder_id)
            )
            if not cursor.fetchone():
                return safe_name
            
            counter += 1
            safe_name = f"{base_name}-{counter}"

class ScriptCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field("", max_length=500)
    content: str = Field(..., min_length=1)
    folder_id: Optional[int] = None
    python_version: str = Field("3.12", regex=r"^3\.(8|9|10|11|12)$")
    requirements: str = Field("", max_length=10000)
    email_notifications: bool = False
    email_recipients: str = Field("", max_length=500)
    environment_variables: str = Field("", max_length=5000)  # JSON string of env vars
    auto_save: bool = True
    
    @validator('content')
    def validate_python_syntax(cls, v):
        """Validate Python syntax and check for dangerous patterns"""
        if not v.strip():
            raise ValueError('Script content cannot be empty')
        
        # Basic Python syntax validation
        try:
            compile(v, '<script>', 'exec')
        except SyntaxError as e:
            raise ValueError(f'Invalid Python syntax: {e}')
        
        # Check for potentially dangerous patterns
        dangerous_patterns = [
            'import os',
            'import subprocess',
            'import sys',
            '__import__',
            'exec(',
            'eval(',
            'open(',
            'file(',
        ]
        
        # Warning only - don't block, but log
        for pattern in dangerous_patterns:
            if pattern in v:
                print(f"Warning: Script contains potentially dangerous pattern: {pattern}")
        
        return v
    
    @validator('requirements')
    def validate_requirements(cls, v):
        """Validate pip requirements format"""
        if not v.strip():
            return v
        
        # Basic requirements.txt validation
        lines = v.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                # Basic package name validation
                if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-_\.]*', line.split('==')[0].split('>=')[0].split('<=')[0]):
                    raise ValueError(f'Invalid package name in requirements: {line}')
        
        return v
    
    @validator('environment_variables')
    def validate_env_vars(cls, v):
        """Validate environment variables JSON"""
        if not v.strip():
            return '{}'
        
        try:
            env_dict = json.loads(v)
            if not isinstance(env_dict, dict):
                raise ValueError('Environment variables must be a JSON object')
            
            # Validate variable names and values
            for key, value in env_dict.items():
                if not isinstance(key, str) or not isinstance(value, str):
                    raise ValueError('Environment variable names and values must be strings')
                if not re.match(r'^[A-Z_][A-Z0-9_]*$', key):
                    raise ValueError(f'Invalid environment variable name: {key}')
            
            return v
        except json.JSONDecodeError:
            raise ValueError('Environment variables must be valid JSON')

class ScriptResponse(BaseModel):
    id: int
    name: str                        # Display name
    safe_name: str                   # Filesystem name
    description: str
    content: str
    folder_id: Optional[int]
    python_version: str
    requirements: str
    enabled: bool
    created_at: str
    updated_at: str
    last_executed_at: Optional[str]
    execution_count: int
    success_count: int
    email_notifications: bool
    email_recipients: str

@router.get("/", response_model=List[ScriptResponse])
async def list_scripts(user=Depends(get_current_user)):
    """Get all scripts with folder information"""
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT s.*, f.name as folder_name 
            FROM scripts s 
            LEFT JOIN folders f ON s.folder_id = f.id
            ORDER BY f.name NULLS FIRST, s.name
        """)
        scripts = []
        for row in cursor.fetchall():
            script = dict(row)
            script.pop('folder_name', None)  # Remove join field
            scripts.append(ScriptResponse(**script))
        return scripts

@router.post("/", response_model=ScriptResponse)
async def create_script(script: ScriptCreate, user=Depends(get_current_user)):
    """Create new script with virtual environment"""
    # Generate safe name and ensure uniqueness
    safe_name = generate_safe_name(script.name)
    safe_name = ensure_unique_safe_name(safe_name, script.folder_id)
    
    with get_db() as conn:
        # Check for display name conflicts
        cursor = conn.execute(
            "SELECT id FROM scripts WHERE name = ? AND folder_id = ?",
            (script.name, script.folder_id)
        )
        if cursor.fetchone():
            raise HTTPException(400, "Script name already exists in this folder")
        
        # Create script record
        cursor = conn.execute("""
            INSERT INTO scripts (
                name, safe_name, description, content, folder_id, python_version,
                requirements, email_notifications, email_recipients
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            script.name, safe_name, script.description, script.content, script.folder_id,
            script.python_version, script.requirements,
            script.email_notifications, script.email_recipients
        ))
        
        script_id = cursor.lastrowid
        
        # Get folder path for virtual environment creation
        folder_path = ""
        if script.folder_id:
            folder_cursor = conn.execute("SELECT name FROM folders WHERE id = ?", (script.folder_id,))
            folder_row = folder_cursor.fetchone()
            if folder_row:
                folder_path = folder_row["name"]
        
        # Create virtual environment asynchronously
        from tasks import create_virtual_environment
        create_virtual_environment.delay(safe_name, folder_path)
        
        # Return created script
        cursor = conn.execute("SELECT * FROM scripts WHERE id = ?", (script_id,))
        return ScriptResponse(**dict(cursor.fetchone()))

@router.put("/{script_id}")
async def update_script(script_id: int, script: ScriptCreate, user=Depends(get_current_user)):
    """Update existing script"""
    with get_db() as conn:
        cursor = conn.execute("""
            UPDATE scripts SET 
                name = ?, description = ?, content = ?, folder_id = ?,
                python_version = ?, requirements = ?, 
                email_notifications = ?, email_recipients = ?,
                environment_variables = ?, auto_save = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            script.name, script.description, script.content, script.folder_id,
            script.python_version, script.requirements,
            script.email_notifications, script.email_recipients,
            script.environment_variables, script.auto_save, script_id
        ))
        
        if cursor.rowcount == 0:
            raise HTTPException(404, "Script not found")
        
        # Update virtual environment if requirements changed
        from tasks import update_virtual_environment
        update_virtual_environment.delay(script_id)
        
        return {"success": True}

@router.patch("/{script_safe_name}/auto-save")
async def auto_save_script(script_safe_name: str, content: str, user=Depends(get_current_user)):
    """Auto-save script content (for real-time saving)"""
    with get_db() as conn:
        cursor = conn.execute("""
            UPDATE scripts SET 
                content = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE safe_name = ? AND auto_save = true
        """, (content, script_safe_name))
        
        if cursor.rowcount == 0:
            raise HTTPException(404, "Script not found or auto-save disabled")
        
        return {"success": True, "saved_at": datetime.now().isoformat()}

@router.post("/{script_safe_name}/execute")
async def execute_script(script_safe_name: str, user=Depends(get_current_user)):
    """Execute script manually via authenticated API"""
    with get_db() as conn:
        cursor = conn.execute("SELECT id, safe_name FROM scripts WHERE safe_name = ? AND enabled = true", (script_safe_name,))
        script = cursor.fetchone()
        if not script:
            raise HTTPException(404, "Script not found or disabled")
    
    # Queue script execution
    from tasks import execute_script_task
    task = execute_script_task.delay(script["safe_name"], triggered_by="manual")
    
    return {"task_id": task.id, "status": "queued"}

@router.get("/{script_safe_name}/trigger")
async def trigger_script_via_url(script_safe_name: str, api_key: str = None):
    """Execute script via simple URL (with optional API key)"""
    # Check API key if provided
    if api_key:
        with get_db() as conn:
            cursor = conn.execute("SELECT value FROM settings WHERE key = 'api_key'")
            stored_key = cursor.fetchone()
            if not stored_key or stored_key["value"] != api_key:
                raise HTTPException(401, "Invalid API key")
    
    # Find and execute script
    with get_db() as conn:
        cursor = conn.execute("SELECT id, safe_name FROM scripts WHERE safe_name = ? AND enabled = true", (script_safe_name,))
        script = cursor.fetchone()
        if not script:
            raise HTTPException(404, "Script not found or disabled")
    
    # Queue script execution
    from tasks import execute_script_task
    task = execute_script_task.delay(script["safe_name"], triggered_by="url")
    
    return {
        "success": True,
        "script": script_safe_name,
        "task_id": task.id,
        "message": f"Script '{script_safe_name}' execution queued"
    }
```

### Virtual Environment Management
```python
# virtual_env.py - Virtual environment management
import os
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Any

class VirtualEnvironmentManager:
    def __init__(self, safe_name: str, folder_path: str = ""):
        self.safe_name = safe_name
        self.data_path = Path(os.getenv("PYSCHED_DATA_PATH", "/data"))
        
        # Build script path using safe name and folder structure
        if folder_path:
            self.script_path = self.data_path / "scripts" / folder_path / safe_name
        else:
            self.script_path = self.data_path / "scripts" / safe_name
            
        self.venv_path = self.script_path / ".venv"
        self.script_file = self.script_path / f"{safe_name}.py"
        self.requirements_file = self.script_path / "requirements.txt"
    
    async def create_environment(self, python_version: str = "3.12") -> Dict[str, Any]:
        """Create virtual environment"""
        try:
            # Create directory structure
            self.script_path.mkdir(parents=True, exist_ok=True)
            
            # Create virtual environment
            process = await asyncio.create_subprocess_exec(
                f"python{python_version}", "-m", "venv", str(self.venv_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                return {
                    "success": False,
                    "error": f"Failed to create venv: {stderr.decode()}"
                }
            
            # Upgrade pip
            pip_path = self.venv_path / "bin" / "pip"
            process = await asyncio.create_subprocess_exec(
                str(pip_path), "install", "--upgrade", "pip",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            return {"success": True, "message": "Virtual environment created"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def install_requirements(self, requirements: str) -> Dict[str, Any]:
        """Install requirements in virtual environment"""
        if not requirements.strip():
            return {"success": True, "message": "No requirements to install"}
        
        try:
            # Write requirements file
            self.requirements_file.write_text(requirements)
            
            # Install requirements
            pip_path = self.venv_path / "bin" / "pip"
            process = await asyncio.create_subprocess_exec(
                str(pip_path), "install", "-r", str(self.requirements_file),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            return {
                "success": process.returncode == 0,
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
                "exit_code": process.returncode
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def execute_script(self, content: str, environment_variables: str = "{}") -> Dict[str, Any]:
        """Execute script in virtual environment with custom env vars"""
        try:
            # Write script file
            self.script_file.write_text(content)
            
            # Prepare environment variables
            env = os.environ.copy()
            try:
                custom_env = json.loads(environment_variables)
                env.update(custom_env)
            except (json.JSONDecodeError, TypeError):
                pass  # Use default environment if JSON is invalid
            
            # Execute script
            python_path = self.venv_path / "bin" / "python"
            start_time = asyncio.get_event_loop().time()
            
            process = await asyncio.create_subprocess_exec(
                str(python_path), str(self.script_file),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.script_path),
                env=env
            )
            
            stdout, stderr = await process.communicate()
            end_time = asyncio.get_event_loop().time()
            
            return {
                "exit_code": process.returncode,
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
                "duration_ms": int((end_time - start_time) * 1000)
            }
            
        except Exception as e:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "duration_ms": 0
            }
    
    def cleanup(self):
        """Remove virtual environment and files"""
        import shutil
        if self.script_path.exists():
            shutil.rmtree(self.script_path)
```

### Task Queue System
```python
# tasks.py - Celery background tasks
from celery import Celery
from celery.schedules import crontab
import asyncio
import json
from datetime import datetime

from database import get_db
from virtual_env import VirtualEnvironmentManager
from email_service import send_script_notification
from websocket_manager import broadcast_event

# Celery configuration
celery_app = Celery(
    'pyscheduler',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

@celery_app.task(bind=True)
def execute_script_task(self, safe_name: str, trigger_id: int = None, triggered_by: str = "schedule"):
    """Execute a script and log results"""
    execution_log_id = None
    
    try:
        # Get script details
        with get_db() as conn:
            cursor = conn.execute("""
                SELECT * FROM scripts WHERE safe_name = ? AND enabled = true
            """, (safe_name,))
            script = cursor.fetchone()
            
            if not script:
                return {"error": "Script not found or disabled"}
            
            script_id = script["id"]
        
        # Create execution log
        with get_db() as conn:
            cursor = conn.execute("""
                INSERT INTO execution_logs (
                    script_id, trigger_id, started_at, status, triggered_by
                ) VALUES (?, ?, ?, 'running', ?)
            """, (script_id, trigger_id, datetime.now().isoformat(), triggered_by))
            execution_log_id = cursor.lastrowid
        
        # Broadcast execution start
        asyncio.run(broadcast_event("script_execution_started", {
            "script_id": script_id,
            "execution_log_id": execution_log_id
        }))
        
        # Get folder path for script execution
        folder_path = ""
        if script["folder_id"]:
            with get_db() as conn:
                folder_cursor = conn.execute("SELECT name FROM folders WHERE id = ?", (script["folder_id"],))
                folder_row = folder_cursor.fetchone()
                if folder_row:
                    folder_path = folder_row["name"]
        
        # Execute script with environment variables
        manager = VirtualEnvironmentManager(safe_name, folder_path)
        result = asyncio.run(manager.execute_script(
            script["content"], 
            script.get("environment_variables", "{}")
        ))
        
        # Update execution log
        status = "success" if result["exit_code"] == 0 else "failed"
        with get_db() as conn:
            conn.execute("""
                UPDATE execution_logs SET
                    finished_at = ?,
                    duration_ms = ?,
                    status = ?,
                    exit_code = ?,
                    stdout = ?,
                    stderr = ?
                WHERE id = ?
            """, (
                datetime.now().isoformat(),
                result["duration_ms"],
                status,
                result["exit_code"],
                result["stdout"],
                result["stderr"],
                execution_log_id
            ))
            
            # Update script statistics
            conn.execute("""
                UPDATE scripts SET
                    last_executed_at = ?,
                    execution_count = execution_count + 1,
                    success_count = success_count + ?
                WHERE id = ?
            """, (
                datetime.now().isoformat(),
                1 if status == "success" else 0,
                script_id
            ))
        
        # Send email notification if enabled
        if script["email_notifications"] and script["email_recipients"]:
            send_script_notification(
                script["name"],
                status,
                result["stdout"] + "\n" + result["stderr"],
                script["email_recipients"]
            )
        
        # Broadcast execution completion
        asyncio.run(broadcast_event("script_execution_completed", {
            "script_id": script_id,
            "execution_log_id": execution_log_id,
            "status": status
        }))
        
        return {"success": True, "status": status}
        
    except Exception as exc:
        # Log error
        if execution_log_id:
            with get_db() as conn:
                conn.execute("""
                    UPDATE execution_logs SET
                        finished_at = ?,
                        status = 'failed',
                        stderr = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), str(exc), execution_log_id))
        
        # Retry logic
        if self.request.retries < 3:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {"error": str(exc)}

@celery_app.task
def create_virtual_environment(script_id: int):
    """Create virtual environment for script"""
    try:
        with get_db() as conn:
            cursor = conn.execute(
                "SELECT python_version FROM scripts WHERE id = ?", 
                (script_id,)
            )
            script = cursor.fetchone()
            
            if not script:
                return {"error": "Script not found"}
        
        manager = VirtualEnvironmentManager(script_id)
        result = asyncio.run(manager.create_environment(script["python_version"]))
        
        # Broadcast environment ready
        asyncio.run(broadcast_event("script_environment_ready", {
            "script_id": script_id,
            "success": result["success"]
        }))
        
        return result
        
    except Exception as e:
        return {"error": str(e)}

@celery_app.task
def update_virtual_environment(script_id: int):
    """Update virtual environment requirements"""
    try:
        with get_db() as conn:
            cursor = conn.execute(
                "SELECT requirements FROM scripts WHERE id = ?",
                (script_id,)
            )
            script = cursor.fetchone()
            
            if not script:
                return {"error": "Script not found"}
        
        manager = VirtualEnvironmentManager(script_id)
        result = asyncio.run(manager.install_requirements(script["requirements"]))
        
        return result
        
    except Exception as e:
        return {"error": str(e)}

# Periodic tasks
@celery_app.task
def cleanup_old_logs():
    """Clean up old execution logs"""
    with get_db() as conn:
        # Keep last 100 logs per script
        conn.execute("""
            DELETE FROM execution_logs 
            WHERE id NOT IN (
                SELECT id FROM execution_logs el1
                WHERE (
                    SELECT COUNT(*) FROM execution_logs el2 
                    WHERE el2.script_id = el1.script_id 
                    AND el2.started_at >= el1.started_at
                ) <= 100
            )
        """)
        
        # Delete logs older than 30 days
        conn.execute("""
            DELETE FROM execution_logs 
            WHERE started_at < datetime('now', '-30 days')
        """)

# Celery beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    'cleanup-logs': {
        'task': 'tasks.cleanup_old_logs',
        'schedule': crontab(hour=2, minute=0),  # Run daily at 2 AM
    },
}
```

### WebSocket Manager
```python
# websocket_manager.py - Real-time communication
from fastapi import WebSocket
from typing import List, Dict, Any
import json
import asyncio

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        try:
            while True:
                # Keep connection alive
                await websocket.receive_text()
        except:
            # Connection closed
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
    
    async def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return
        
        message_text = json.dumps(message)
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_text)
            except:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.active_connections.remove(connection)

# Global WebSocket manager
ws_manager = WebSocketManager()

async def broadcast_event(event_type: str, data: Dict[str, Any]):
    """Broadcast event to all connected clients"""
    await ws_manager.broadcast({
        "type": event_type,
        "timestamp": datetime.now().isoformat(),
        "data": data
    })
```

### Email Service
```python
# email_service.py - SMTP2GO email notifications
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "mail.smtp2go.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "2525"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL", "pyscheduler@example.com")
    
    def send_script_notification(self, script_name: str, status: str, output: str, recipients: str):
        """Send email notification for script execution"""
        if not self.smtp_server or not self.smtp_username or not recipients:
            return
        
        subject = f"Tempo: {script_name} - {status.title()}"
        
        # Create email body
        body = f"""
Script: {script_name}
Status: {status.title()}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Output:
{output}

---
Tempo Notification
        """
        
        # Send to each recipient
        for recipient in recipients.split(","):
            recipient = recipient.strip()
            if recipient:
                try:
                    self._send_email(recipient, subject, body)
                except Exception as e:
                    print(f"Failed to send email to {recipient}: {e}")
    
    def _send_email(self, to: str, subject: str, body: str):
        """Send email via SMTP"""
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = self.from_email
        msg['To'] = to
        
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)

# Global email service
email_service = EmailService()

def send_script_notification(script_name: str, status: str, output: str, recipients: str):
    """Send script notification email"""
    email_service.send_script_notification(script_name, status, output, recipients)
```

## Frontend Implementation

### Vue.js Application Structure
```javascript
// main.js - Vue application entry point
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './style.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
```

### Pinia Store for State Management
```javascript
// stores/scripts.js - Script management store
import { defineStore } from 'pinia'
import axios from 'axios'

export const useScriptStore = defineStore('scripts', {
  state: () => ({
    scripts: [],
    folders: [],
    currentScript: null,
    executionLogs: [],
    loading: false,
    error: null
  }),
  
  getters: {
    getScriptById: (state) => (id) => {
      return state.scripts.find(script => script.id === id)
    },
    
    getScriptsByFolder: (state) => (folderId) => {
      return state.scripts.filter(script => script.folder_id === folderId)
    }
  },
  
  actions: {
    async fetchScripts() {
      this.loading = true
      try {
        const response = await axios.get('/api/scripts')
        this.scripts = response.data
      } catch (error) {
        this.error = error.message
      } finally {
        this.loading = false
      }
    },
    
    async createScript(scriptData) {
      try {
        const response = await axios.post('/api/scripts', scriptData)
        this.scripts.push(response.data)
        return response.data
      } catch (error) {
        throw new Error(error.response?.data?.detail || 'Failed to create script')
      }
    },
    
    async updateScript(scriptId, scriptData) {
      try {
        await axios.put(`/api/scripts/${scriptId}`, scriptData)
        const index = this.scripts.findIndex(s => s.id === scriptId)
        if (index !== -1) {
          this.scripts[index] = { ...this.scripts[index], ...scriptData }
        }
      } catch (error) {
        throw new Error(error.response?.data?.detail || 'Failed to update script')
      }
    },
    
    async executeScript(scriptId) {
      try {
        const response = await axios.post(`/api/scripts/${scriptId}/execute`)
        return response.data
      } catch (error) {
        throw new Error(error.response?.data?.detail || 'Failed to execute script')
      }
    },
    
    async deleteScript(scriptId) {
      try {
        await axios.delete(`/api/scripts/${scriptId}`)
        this.scripts = this.scripts.filter(s => s.id !== scriptId)
      } catch (error) {
        throw new Error(error.response?.data?.detail || 'Failed to delete script')
      }
    }
  }
})
```

### WebSocket Integration
```javascript
// composables/useWebSocket.js - WebSocket composable
import { ref, onMounted, onUnmounted } from 'vue'

export function useWebSocket() {
  const connected = ref(false)
  const messages = ref([])
  const socket = ref(null)
  
  const connect = () => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws`
    
    socket.value = new WebSocket(wsUrl)
    
    socket.value.onopen = () => {
      connected.value = true
      console.log('WebSocket connected')
    }
    
    socket.value.onmessage = (event) => {
      const message = JSON.parse(event.data)
      messages.value.push(message)
      
      // Emit custom events for different message types
      const customEvent = new CustomEvent(`ws-${message.type}`, {
        detail: message.data
      })
      window.dispatchEvent(customEvent)
    }
    
    socket.value.onclose = () => {
      connected.value = false
      console.log('WebSocket disconnected')
      
      // Reconnect after 5 seconds
      setTimeout(connect, 5000)
    }
    
    socket.value.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
  }
  
  const disconnect = () => {
    if (socket.value) {
      socket.value.close()
    }
  }
  
  onMounted(() => {
    connect()
  })
  
  onUnmounted(() => {
    disconnect()
  })
  
  return {
    connected,
    messages,
    connect,
    disconnect
  }
}
```

## File System Organization

### Directory Structure
```
/data/pyscheduler/
├── pyscheduler.db              # SQLite database
├── scripts/                    # Script storage (organized by safe names)
│   ├── hello-world/            # Script: "Hello World" 
│   │   ├── hello-world.py      # Script content
│   │   ├── requirements.txt    # Dependencies
│   │   └── .venv/             # Virtual environment
│   ├── data-backup/            # Script: "Data Backup"
│   │   ├── data-backup.py
│   │   ├── requirements.txt
│   │   └── .venv/
│   ├── api-calls/              # Folder for API-related scripts
│   │   ├── weather-api/        # Script: "Weather API"
│   │   │   ├── api-calls.py
│   │   │   ├── requirements.txt
│   │   │   └── .venv/
│   │   └── news-api/           # Script: "News API"
│   │       ├── news-api.py
│   │       ├── requirements.txt
│   │       └── .venv/
│   └── maintenance/            # Folder for maintenance scripts
│       └── log-cleanup/        # Script: "Log Cleanup"
│           ├── log-cleanup.py
│           ├── requirements.txt
│           └── .venv/
├── backups/                    # Database backups
│   ├── daily/
│   └── weekly/
├── logs/                       # Application logs
│   ├── pyscheduler.log
│   └── celery.log
└── config/                     # Configuration files
    └── settings.json
```

## Deployment Configuration

### Dockerfile
```dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    nginx \
    redis-server \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY frontend/dist/ ./frontend/

# Copy configuration files
COPY docker/nginx.conf /etc/nginx/sites-available/default
COPY docker/supervisord.conf /etc/supervisor/conf.d/pyscheduler.conf
COPY docker/start.sh /start.sh

RUN chmod +x /start.sh

# Create data directory
RUN mkdir -p /data && chown -R www-data:www-data /data

# Expose port
EXPOSE 80

# Start supervisor
CMD ["/start.sh"]
```

### Docker Compose
```yaml
services:
  pyscheduler:
    build: .
    ports:
      - "8000:80"
    environment:
      - PYSCHED_DATA_PATH=/data
      - PYSCHED_SECRET_KEY=${PYSCHED_SECRET_KEY:-change-me-in-production}
      - SMTP_SERVER=${SMTP_SERVER:-mail.smtp2go.com}
      - SMTP_PORT=${SMTP_PORT:-2525}
      - SMTP_USERNAME=${SMTP_USERNAME:-}
      - SMTP_PASSWORD=${SMTP_PASSWORD:-}
      - FROM_EMAIL=${FROM_EMAIL:-pyscheduler@example.com}
    volumes:
      - pyscheduler_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  pyscheduler_data:
```

### Supervisor Configuration
```ini
[supervisord]
nodaemon=true
user=root

[program:nginx]
command=/usr/sbin/nginx -g "daemon off;"
autostart=true
autorestart=true

[program:redis]
command=/usr/bin/redis-server
autostart=true
autorestart=true

[program:fastapi]
command=python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
directory=/app
autostart=true
autorestart=true

[program:celery_worker]
command=python -m celery -A backend.tasks worker --loglevel=info
directory=/app
autostart=true
autorestart=true

[program:celery_beat]
command=python -m celery -A backend.tasks beat --loglevel=info
directory=/app
autostart=true
autorestart=true
```

## Conclusion

This architecture provides a robust foundation for Tempo while maintaining simplicity and ease of deployment. The key strengths are:

### Technical Benefits
- **Single Container Deployment** - Easy to install and manage
- **SQLite Database** - No external dependencies
- **Real-time Updates** - WebSocket for live monitoring
- **Isolated Execution** - Virtual environments with resource limits
- **Comprehensive API** - Full REST API with security features

The architecture is designed to be **simple enough for individual developers** while being **secure and robust enough for production use** on home servers and small deployments.

---

**Document Version**: 1.1  
**Created**: 2025-01-11  
**Updated**: 2025-01-14  
**Purpose**: Enhanced technical architecture for Tempo with security and resource management improvements external dependencies
- **Real-time Updates** - WebSocket for live monitoring
- **Isolated Execution** - Virtual environments prevent conflicts
- **Comprehensive Logging** - Full execution history and debugging

### Operational Benefits
- **Easy Backup** - Simple file-based backup strategy
- **Low Resource Usage** - Efficient memory and CPU utilization
- **Quick Development** - Modern tools for rapid iteration
- **Clear Architecture** - Easy to understand and extend

The architecture is designed to be **simple enough for individual developers** while being **robust enough for production use** on home servers and small deployments.

---

**Document Version**: 1.0  
**Created**: 2025-01-11  
**Purpose**: Complete technical architecture for Tempo