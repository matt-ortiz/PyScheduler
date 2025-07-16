from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
import json

from ..database import get_db
from ..auth import get_current_user
from ..models import ScriptCreate, ScriptUpdate, ScriptResponse, AutoSaveRequest
from ..utils import generate_safe_name, ensure_unique_safe_name, get_folder_path
from ..virtual_env import VirtualEnvironmentManager
from ..timezone_utils import format_datetime_for_api

def load_script_content_from_file(script_dict: dict) -> dict:
    """Load script content from file (source of truth) and update database if needed"""
    try:
        folder_path = get_folder_path(script_dict.get("folder_id"))
        manager = VirtualEnvironmentManager(script_dict["safe_name"], folder_path)
        
        # If script file exists, use it as source of truth
        if manager.script_file.exists():
            file_content = manager.script_file.read_text()
            
            # If file content differs from database, update database
            if file_content != script_dict.get("content", ""):
                with get_db() as conn:
                    conn.execute(
                        "UPDATE scripts SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (file_content, script_dict["id"])
                    )
                script_dict["content"] = file_content
        
        return script_dict
    except Exception as e:
        print(f"Error loading script content from file: {e}")
        return script_dict

router = APIRouter()

@router.get("/", response_model=List[ScriptResponse])
@router.get("", response_model=List[ScriptResponse])
async def list_scripts(current_user: dict = Depends(get_current_user)):
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
            script_dict = dict(row)
            script_dict.pop('folder_name', None)  # Remove join field
            
            # Load content from file (source of truth)
            script_dict = load_script_content_from_file(script_dict)
            
            # Format datetime fields for API response
            datetime_fields = ['created_at', 'updated_at', 'last_executed_at']
            for field in datetime_fields:
                if script_dict.get(field):
                    # Parse SQLite datetime string and format for API
                    dt = datetime.fromisoformat(script_dict[field].replace('Z', '+00:00'))
                    script_dict[field] = format_datetime_for_api(dt)
            
            scripts.append(ScriptResponse(**script_dict))
        return scripts

@router.post("/", response_model=ScriptResponse)
@router.post("", response_model=ScriptResponse)
async def create_script(
    script: ScriptCreate,
    current_user: dict = Depends(get_current_user)
):
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
                requirements, email_notifications, email_recipients, email_trigger_type,
                environment_variables, auto_save
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            script.name, safe_name, script.description, script.content, script.folder_id,
            script.python_version, script.requirements,
            script.email_notifications, script.email_recipients, script.email_trigger_type,
            script.environment_variables, script.auto_save
        ))
        
        script_id = cursor.lastrowid
        
        # Create script file immediately (source of truth)
        try:
            folder_path = get_folder_path(script.folder_id)
            manager = VirtualEnvironmentManager(safe_name, folder_path)
            
            # Create directory and script file first
            manager.script_path.mkdir(parents=True, exist_ok=True)
            manager.script_file.write_text(script.content)
            
            # Create virtual environment in background (don't wait for it)
            # This prevents the UI from hanging
            async def create_venv_background():
                try:
                    await manager.create_environment(script.python_version)
                    if script.requirements:
                        await manager.install_requirements(script.requirements)
                except Exception as e:
                    print(f"Background venv creation failed: {e}")
            
            import asyncio
            asyncio.create_task(create_venv_background())
            
        except Exception as e:
            print(f"Error creating script file: {e}")
            raise HTTPException(500, f"Failed to create script file: {str(e)}")
        
        # Return created script with file content
        cursor = conn.execute("SELECT * FROM scripts WHERE id = ?", (script_id,))
        created_script = cursor.fetchone()
        script_dict = load_script_content_from_file(dict(created_script))
        return ScriptResponse(**script_dict)

@router.get("/{safe_name}", response_model=ScriptResponse)
async def get_script(
    safe_name: str,
    current_user: dict = Depends(get_current_user)
):
    """Get script by safe name"""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM scripts WHERE safe_name = ?", (safe_name,))
        script = cursor.fetchone()
        
        if not script:
            raise HTTPException(404, "Script not found")
        
        # Load content from file (source of truth)
        script_dict = load_script_content_from_file(dict(script))
        
        return ScriptResponse(**script_dict)

@router.put("/{safe_name}", response_model=ScriptResponse)
async def update_script(
    safe_name: str,
    script: ScriptUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update existing script"""
    with get_db() as conn:
        # Get existing script
        cursor = conn.execute("SELECT * FROM scripts WHERE safe_name = ?", (safe_name,))
        existing_script = cursor.fetchone()
        
        if not existing_script:
            raise HTTPException(404, "Script not found")
        
        # Build update query
        updates = []
        params = []
        
        # Handle name change - update safe_name if needed
        if script.name is not None and script.name != existing_script["name"]:
            new_safe_name = generate_safe_name(script.name)
            new_safe_name = ensure_unique_safe_name(new_safe_name, existing_script["folder_id"], existing_script["id"])
            updates.extend(["name = ?", "safe_name = ?"])
            params.extend([script.name, new_safe_name])
        
        # Add other fields
        if script.description is not None:
            updates.append("description = ?")
            params.append(script.description)
        
        if script.content is not None:
            updates.append("content = ?")
            params.append(script.content)
        
        if script.folder_id is not None:
            updates.append("folder_id = ?")
            params.append(script.folder_id)
        
        if script.python_version is not None:
            updates.append("python_version = ?")
            params.append(script.python_version)
        
        if script.requirements is not None:
            updates.append("requirements = ?")
            params.append(script.requirements)
        
        if script.email_notifications is not None:
            updates.append("email_notifications = ?")
            params.append(script.email_notifications)
        
        if script.email_recipients is not None:
            updates.append("email_recipients = ?")
            params.append(script.email_recipients)
        
        if script.email_trigger_type is not None:
            updates.append("email_trigger_type = ?")
            params.append(script.email_trigger_type)
        
        if script.environment_variables is not None:
            updates.append("environment_variables = ?")
            params.append(script.environment_variables)
        
        if script.auto_save is not None:
            updates.append("auto_save = ?")
            params.append(script.auto_save)
        
        if script.enabled is not None:
            updates.append("enabled = ?")
            params.append(script.enabled)
        
        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            query = f"UPDATE scripts SET {', '.join(updates)} WHERE id = ?"
            params.append(existing_script["id"])
            conn.execute(query, params)
        
        # Update script file and virtual environment if needed
        folder_path = get_folder_path(existing_script["folder_id"])
        manager = VirtualEnvironmentManager(existing_script["safe_name"], folder_path)
        
        try:
            # Update script file if content changed
            if script.content is not None:
                manager.script_file.write_text(script.content)
            
            # Update virtual environment if requirements changed
            if script.requirements is not None and script.requirements:
                await manager.install_requirements(script.requirements)
        except Exception as e:
            print(f"Error updating script file or virtual environment: {e}")
        
        # Return updated script
        cursor = conn.execute("SELECT * FROM scripts WHERE id = ?", (existing_script["id"],))
        updated_script = cursor.fetchone()
        return ScriptResponse(**dict(updated_script))

@router.patch("/{safe_name}/auto-save")
async def auto_save_script(
    safe_name: str,
    auto_save_data: AutoSaveRequest,
    current_user: dict = Depends(get_current_user)
):
    """Auto-save script content (for real-time saving)"""
    with get_db() as conn:
        # Get script info first
        cursor = conn.execute("SELECT * FROM scripts WHERE safe_name = ? AND auto_save = true", (safe_name,))
        script = cursor.fetchone()
        
        if not script:
            raise HTTPException(404, "Script not found or auto-save disabled")
        
        # Update database
        cursor = conn.execute("""
            UPDATE scripts SET 
                content = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE safe_name = ? AND auto_save = true
        """, (auto_save_data.content, safe_name))
        
        # Update script file
        try:
            folder_path = get_folder_path(script["folder_id"])
            manager = VirtualEnvironmentManager(safe_name, folder_path)
            manager.script_file.write_text(auto_save_data.content)
        except Exception as e:
            print(f"Error updating script file during auto-save: {e}")
        
        return {"success": True, "saved_at": format_datetime_for_api(datetime.now())}

@router.post("/{safe_name}/execute")
async def execute_script(
    safe_name: str,
    current_user: dict = Depends(get_current_user)
):
    """Execute script manually"""
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT * FROM scripts WHERE safe_name = ? AND enabled = true
        """, (safe_name,))
        script = cursor.fetchone()
        
        if not script:
            raise HTTPException(404, "Script not found or disabled")
        
        # Queue script execution through Celery and wait for result
        from ..tasks import execute_script_task
        task = execute_script_task.delay(script["id"], None, "manual")
        
        # Wait for task completion (with timeout)
        try:
            result = task.get(timeout=60)  # Wait up to 60 seconds
            
            if "error" in result:
                return {
                    "success": False,
                    "error": result["error"],
                    "exit_code": -1,
                    "duration_ms": 0,
                    "stdout": "",
                    "stderr": result["error"]
                }
            
            # Return the task result directly (now includes stdout/stderr)
            return {
                "success": result["status"] == "success",
                "status": result["status"],
                "exit_code": result["exit_code"],
                "duration_ms": result["duration_ms"],
                "stdout": result.get("stdout", ""),
                "stderr": result.get("stderr", "")
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Execution timeout or error: {str(e)}",
                "exit_code": -1,
                "duration_ms": 0,
                "stdout": "",
                "stderr": str(e)
            }

@router.get("/{safe_name}/trigger")
async def trigger_script_via_url(
    safe_name: str,
    api_key: Optional[str] = None
):
    """Execute script via URL trigger (with optional API key)"""
    # Check API key if provided
    if api_key:
        from .settings import load_settings
        settings = load_settings()
        stored_key = settings.get("app_settings", {}).get("api_key")
        if not stored_key or stored_key != api_key:
            raise HTTPException(401, "Invalid API key")
    
    # Find and execute script
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT * FROM scripts WHERE safe_name = ? AND enabled = true
        """, (safe_name,))
        script = cursor.fetchone()
        
        if not script:
            raise HTTPException(404, "Script not found or disabled")
        
        # Queue script execution through Celery
        from ..tasks import execute_script_task
        task = execute_script_task.delay(script["id"], None, "url")
        
        return {
            "success": True,
            "task_id": task.id,
            "script": script["name"],
            "message": f"Script '{script['name']}' queued for execution"
        }

@router.delete("/{safe_name}")
async def delete_script(
    safe_name: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete script and clean up virtual environment"""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM scripts WHERE safe_name = ?", (safe_name,))
        script = cursor.fetchone()
        
        if not script:
            raise HTTPException(404, "Script not found")
        
        # Clean up virtual environment
        folder_path = get_folder_path(script["folder_id"])
        manager = VirtualEnvironmentManager(script["safe_name"], folder_path)
        
        try:
            manager.cleanup()
        except Exception as e:
            print(f"Error cleaning up virtual environment: {e}")
        
        # Delete script from database
        cursor = conn.execute("DELETE FROM scripts WHERE id = ?", (script["id"],))
        
        return {"success": True, "message": "Script deleted successfully"}

@router.get("/{safe_name}/venv-info")
async def get_venv_info(
    safe_name: str,
    current_user: dict = Depends(get_current_user)
):
    """Get virtual environment information for a script"""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM scripts WHERE safe_name = ?", (safe_name,))
        script = cursor.fetchone()
        
        if not script:
            raise HTTPException(404, "Script not found")
        
        # Get virtual environment manager
        folder_path = get_folder_path(script["folder_id"])
        manager = VirtualEnvironmentManager(script["safe_name"], folder_path)
        
        try:
            # Check if venv exists
            venv_exists = manager.exists()
            
            if not venv_exists:
                return {
                    "venv_exists": False,
                    "packages": [],
                    "python_version": None,
                    "venv_path": str(manager.get_venv_path()),
                    "message": "Virtual environment not created"
                }
            
            # Get installed packages
            import asyncio
            from concurrent.futures import ThreadPoolExecutor
            
            def get_pip_list():
                import subprocess
                pip_path = manager.get_venv_path() / "bin" / "pip"
                if not pip_path.exists():
                    pip_path = manager.get_venv_path() / "Scripts" / "pip.exe"  # Windows
                
                if not pip_path.exists():
                    return []
                
                try:
                    result = subprocess.run(
                        [str(pip_path), "list", "--format=json"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        import json
                        return json.loads(result.stdout)
                    return []
                except Exception as e:
                    print(f"Error getting pip list: {e}")
                    return []
            
            def get_python_version():
                import subprocess
                python_path = manager.get_venv_path() / "bin" / "python"
                if not python_path.exists():
                    python_path = manager.get_venv_path() / "Scripts" / "python.exe"  # Windows
                
                if not python_path.exists():
                    return "Unknown"
                
                try:
                    result = subprocess.run(
                        [str(python_path), "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        return result.stdout.strip()
                    return "Unknown"
                except Exception as e:
                    print(f"Error getting Python version: {e}")
                    return "Unknown"
            
            # Run in thread pool to avoid blocking
            with ThreadPoolExecutor() as executor:
                packages_future = executor.submit(get_pip_list)
                version_future = executor.submit(get_python_version)
                
                packages = packages_future.result()
                python_version = version_future.result()
            
            return {
                "venv_exists": True,
                "packages": packages,
                "python_version": python_version,
                "venv_path": str(manager.get_venv_path()),
                "package_count": len(packages),
                "message": "Virtual environment is ready"
            }
            
        except Exception as e:
            return {
                "venv_exists": venv_exists,
                "packages": [],
                "python_version": None,
                "venv_path": str(manager.get_venv_path()),
                "error": str(e),
                "message": "Error getting virtual environment info"
            }