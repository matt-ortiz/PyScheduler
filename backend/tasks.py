from celery import Celery
from celery.schedules import crontab
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any

from .database import get_db
from .virtual_env import VirtualEnvironmentManager
from .websocket_manager import broadcast_event
from .email_service import send_script_notification

# Celery configuration
celery_app = Celery(
    'pyscheduler',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

@celery_app.task(bind=True)
def execute_script_task(self, script_id: int, trigger_id: int = None, triggered_by: str = "schedule"):
    """Execute a script and log results"""
    execution_log_id = None
    
    try:
        # Get script details
        with get_db() as conn:
            cursor = conn.execute("""
                SELECT s.*, f.name as folder_name FROM scripts s
                LEFT JOIN folders f ON s.folder_id = f.id
                WHERE s.id = ? AND s.enabled = true
            """, (script_id,))
            script = cursor.fetchone()
            
            if not script:
                return {"error": "Script not found or disabled"}
        
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
            "execution_log_id": execution_log_id,
            "script_name": script["name"]
        }))
        
        # Get folder path for script execution
        folder_path = script["folder_name"] or ""
        
        # Execute script
        manager = VirtualEnvironmentManager(script["safe_name"], folder_path)
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
                    last_executed_at = CURRENT_TIMESTAMP,
                    execution_count = execution_count + 1,
                    success_count = success_count + ?
                WHERE id = ?
            """, (1 if status == "success" else 0, script_id))
        
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
            "status": status,
            "script_name": script["name"]
        }))
        
        return {
            "success": True,
            "status": status,
            "exit_code": result["exit_code"],
            "duration_ms": result["duration_ms"]
        }
        
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
        
        # Broadcast error
        asyncio.run(broadcast_event("script_execution_error", {
            "script_id": script_id,
            "execution_log_id": execution_log_id,
            "error": str(exc)
        }))
        
        # Retry logic
        if self.request.retries < 3:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {"error": str(exc)}

@celery_app.task
def create_virtual_environment(script_id: int):
    """Create virtual environment for script"""
    try:
        with get_db() as conn:
            cursor = conn.execute("""
                SELECT s.*, f.name as folder_name FROM scripts s
                LEFT JOIN folders f ON s.folder_id = f.id
                WHERE s.id = ?
            """, (script_id,))
            script = cursor.fetchone()
            
            if not script:
                return {"error": "Script not found"}
        
        folder_path = script["folder_name"] or ""
        manager = VirtualEnvironmentManager(script["safe_name"], folder_path)
        result = asyncio.run(manager.create_environment(script["python_version"]))
        
        # Install requirements if provided
        if result["success"] and script["requirements"]:
            install_result = asyncio.run(manager.install_requirements(script["requirements"]))
            if not install_result["success"]:
                result["warning"] = f"Environment created but requirements failed: {install_result.get('error', 'Unknown error')}"
        
        # Broadcast environment ready
        asyncio.run(broadcast_event("script_environment_ready", {
            "script_id": script_id,
            "success": result["success"],
            "script_name": script["name"]
        }))
        
        return result
        
    except Exception as e:
        return {"error": str(e)}

@celery_app.task
def update_virtual_environment(script_id: int):
    """Update virtual environment requirements"""
    try:
        with get_db() as conn:
            cursor = conn.execute("""
                SELECT s.*, f.name as folder_name FROM scripts s
                LEFT JOIN folders f ON s.folder_id = f.id
                WHERE s.id = ?
            """, (script_id,))
            script = cursor.fetchone()
            
            if not script:
                return {"error": "Script not found"}
        
        folder_path = script["folder_name"] or ""
        manager = VirtualEnvironmentManager(script["safe_name"], folder_path)
        result = asyncio.run(manager.install_requirements(script["requirements"]))
        
        return result
        
    except Exception as e:
        return {"error": str(e)}

@celery_app.task
def cleanup_old_logs():
    """Clean up old execution logs"""
    try:
        with get_db() as conn:
            # Get cleanup settings or use defaults
            cursor = conn.execute("SELECT value FROM settings WHERE key = 'max_execution_logs'")
            result = cursor.fetchone()
            max_logs = int(result["value"]) if result else 100
            
            cursor = conn.execute("SELECT value FROM settings WHERE key = 'log_retention_days'")
            result = cursor.fetchone()
            retention_days = int(result["value"]) if result else 30
            
            # Keep only the most recent logs per script
            conn.execute("""
                DELETE FROM execution_logs 
                WHERE id NOT IN (
                    SELECT id FROM (
                        SELECT id, ROW_NUMBER() OVER (PARTITION BY script_id ORDER BY started_at DESC) as rn
                        FROM execution_logs
                    ) ranked
                    WHERE rn <= ?
                )
            """, (max_logs,))
            
            # Delete logs older than retention period
            cursor = conn.execute("""
                DELETE FROM execution_logs 
                WHERE started_at < datetime('now', '-{} days')
            """.format(retention_days))
            
            deleted_count = cursor.rowcount
            
            return {"success": True, "deleted_count": deleted_count}
            
    except Exception as e:
        return {"error": str(e)}

@celery_app.task
def process_scheduled_triggers():
    """Process scheduled triggers (cron and interval)"""
    try:
        with get_db() as conn:
            # Get all enabled triggers
            cursor = conn.execute("""
                SELECT t.*, s.name as script_name 
                FROM triggers t
                JOIN scripts s ON t.script_id = s.id
                WHERE t.enabled = true AND s.enabled = true
            """)
            
            triggers = cursor.fetchall()
            processed = 0
            
            for trigger in triggers:
                trigger_config = json.loads(trigger["config"])
                should_execute = False
                
                if trigger["trigger_type"] == "interval":
                    # Check if enough time has passed for interval trigger
                    if trigger["last_triggered_at"]:
                        last_run = datetime.fromisoformat(trigger["last_triggered_at"])
                        interval_seconds = trigger_config.get("seconds", 3600)
                        
                        if (datetime.now() - last_run).total_seconds() >= interval_seconds:
                            should_execute = True
                    else:
                        should_execute = True
                
                elif trigger["trigger_type"] == "cron":
                    # Check if next run time has passed
                    if trigger["next_run_at"]:
                        next_run = datetime.fromisoformat(trigger["next_run_at"])
                        if datetime.now() >= next_run:
                            should_execute = True
                    else:
                        # If no next run time, calculate it
                        should_execute = True
                
                if should_execute:
                    # Queue script execution
                    execute_script_task.delay(trigger["script_id"], trigger["id"], "schedule")
                    
                    # Update trigger last run time and calculate next run
                    next_run_at = None
                    if trigger["trigger_type"] == "interval":
                        interval_seconds = trigger_config.get("seconds", 3600)
                        next_run_at = (datetime.now() + timedelta(seconds=interval_seconds)).isoformat()
                    elif trigger["trigger_type"] == "cron":
                        # For now, set next run to one hour from now (simplified)
                        # In production, use croniter library for proper CRON parsing
                        next_run_at = (datetime.now() + timedelta(hours=1)).isoformat()
                    
                    conn.execute("""
                        UPDATE triggers SET 
                            last_triggered_at = CURRENT_TIMESTAMP,
                            next_run_at = ?
                        WHERE id = ?
                    """, (next_run_at, trigger["id"]))
                    
                    processed += 1
            
            return {"success": True, "processed": processed}
            
    except Exception as e:
        return {"error": str(e)}

@celery_app.task
def execute_startup_triggers():
    """Execute all startup triggers"""
    try:
        with get_db() as conn:
            cursor = conn.execute("""
                SELECT t.*, s.name as script_name 
                FROM triggers t
                JOIN scripts s ON t.script_id = s.id
                WHERE t.enabled = true 
                AND s.enabled = true 
                AND t.trigger_type = 'startup'
            """)
            
            triggers = cursor.fetchall()
            processed = 0
            
            for trigger in triggers:
                # Queue script execution
                execute_script_task.delay(trigger["script_id"], trigger["id"], "startup")
                
                # Update trigger last run time
                conn.execute("""
                    UPDATE triggers SET last_triggered_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (trigger["id"],))
                
                processed += 1
            
            return {"success": True, "processed": processed}
            
    except Exception as e:
        return {"error": str(e)}

# Celery beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    'cleanup-logs': {
        'task': 'backend.tasks.cleanup_old_logs',
        'schedule': crontab(hour=2, minute=0),  # Run daily at 2 AM
    },
    'process-scheduled-triggers': {
        'task': 'backend.tasks.process_scheduled_triggers',
        'schedule': 60.0,  # Run every minute
    },
}

celery_app.conf.timezone = 'UTC'