from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
import json

from ..database import get_db
from ..auth import get_current_user
from ..models import ScriptCreate, ScriptUpdate, ScriptResponse, AutoSaveRequest
from ..utils import generate_safe_name, ensure_unique_safe_name, get_folder_path
from ..virtual_env import VirtualEnvironmentManager

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
                requirements, email_notifications, email_recipients,
                environment_variables, auto_save
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            script.name, safe_name, script.description, script.content, script.folder_id,
            script.python_version, script.requirements,
            script.email_notifications, script.email_recipients,
            script.environment_variables, script.auto_save
        ))
        
        script_id = cursor.lastrowid
        
        # Create virtual environment asynchronously
        folder_path = get_folder_path(script.folder_id)
        manager = VirtualEnvironmentManager(safe_name, folder_path)
        
        # Create environment asynchronously
        try:
            result = await manager.create_environment(script.python_version)
            if result["success"] and script.requirements:
                await manager.install_requirements(script.requirements)
        except Exception as e:
            print(f"Error creating virtual environment: {e}")
            # Could raise an exception here, but for now just log the error
        
        # Return created script
        cursor = conn.execute("SELECT * FROM scripts WHERE id = ?", (script_id,))
        created_script = cursor.fetchone()
        return ScriptResponse(**dict(created_script))

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
        
        return ScriptResponse(**dict(script))

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
        
        # Update virtual environment if requirements changed
        if script.requirements is not None:
            folder_path = get_folder_path(existing_script["folder_id"])
            manager = VirtualEnvironmentManager(existing_script["safe_name"], folder_path)
            
            try:
                if script.requirements:
                    await manager.install_requirements(script.requirements)
            except Exception as e:
                print(f"Error updating virtual environment: {e}")
        
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
        cursor = conn.execute("""
            UPDATE scripts SET 
                content = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE safe_name = ? AND auto_save = true
        """, (auto_save_data.content, safe_name))
        
        if cursor.rowcount == 0:
            raise HTTPException(404, "Script not found or auto-save disabled")
        
        return {"success": True, "saved_at": datetime.now().isoformat()}

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
        
        # Execute script directly for now (should use Celery in production)
        folder_path = get_folder_path(script["folder_id"])
        manager = VirtualEnvironmentManager(script["safe_name"], folder_path)
        
        try:
            import asyncio
            from concurrent.futures import ThreadPoolExecutor
            
            # Create a new event loop for the thread
            def run_script():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(manager.execute_script(
                        script["content"], 
                        script["environment_variables"] or "{}"
                    ))
                finally:
                    loop.close()
            
            # Run in a thread pool to avoid event loop conflicts
            with ThreadPoolExecutor() as executor:
                future = executor.submit(run_script)
                result = future.result()
            
            # Log execution
            cursor = conn.execute("""
                INSERT INTO execution_logs (
                    script_id, started_at, finished_at, duration_ms, status,
                    exit_code, stdout, stderr, triggered_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                script["id"],
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                result["duration_ms"],
                "success" if result["exit_code"] == 0 else "failed",
                result["exit_code"],
                result["stdout"],
                result["stderr"],
                "manual"
            ))
            
            # Update script statistics
            conn.execute("""
                UPDATE scripts SET
                    last_executed_at = CURRENT_TIMESTAMP,
                    execution_count = execution_count + 1,
                    success_count = success_count + ?
                WHERE id = ?
            """, (1 if result["exit_code"] == 0 else 0, script["id"]))
            
            return {
                "success": True,
                "status": "success" if result["exit_code"] == 0 else "failed",
                "exit_code": result["exit_code"],
                "stdout": result["stdout"],
                "stderr": result["stderr"],
                "duration_ms": result["duration_ms"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

@router.get("/{safe_name}/trigger")
async def trigger_script_via_url(
    safe_name: str,
    api_key: Optional[str] = None
):
    """Execute script via URL trigger (with optional API key)"""
    # Check API key if provided
    if api_key:
        with get_db() as conn:
            cursor = conn.execute("SELECT value FROM settings WHERE key = 'api_key'")
            stored_key = cursor.fetchone()
            if not stored_key or stored_key["value"] != api_key:
                raise HTTPException(401, "Invalid API key")
    
    # Find and execute script
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT * FROM scripts WHERE safe_name = ? AND enabled = true
        """, (safe_name,))
        script = cursor.fetchone()
        
        if not script:
            raise HTTPException(404, "Script not found or disabled")
        
        # Execute script (simplified for now)
        folder_path = get_folder_path(script["folder_id"])
        manager = VirtualEnvironmentManager(script["safe_name"], folder_path)
        
        try:
            import asyncio
            from concurrent.futures import ThreadPoolExecutor
            
            # Create a new event loop for the thread
            def run_script():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(manager.execute_script(
                        script["content"], 
                        script["environment_variables"] or "{}"
                    ))
                finally:
                    loop.close()
            
            # Run in a thread pool to avoid event loop conflicts
            with ThreadPoolExecutor() as executor:
                future = executor.submit(run_script)
                result = future.result()
            
            # Log execution
            cursor = conn.execute("""
                INSERT INTO execution_logs (
                    script_id, started_at, finished_at, duration_ms, status,
                    exit_code, stdout, stderr, triggered_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                script["id"],
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                result["duration_ms"],
                "success" if result["exit_code"] == 0 else "failed",
                result["exit_code"],
                result["stdout"],
                result["stderr"],
                "url"
            ))
            
            return {
                "success": True,
                "script": script["name"],
                "status": "success" if result["exit_code"] == 0 else "failed",
                "message": f"Script '{script['name']}' executed successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
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