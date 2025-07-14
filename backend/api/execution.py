from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import re

from ..database import get_db
from ..auth import get_current_user
from ..models import TriggerCreate, TriggerResponse

router = APIRouter()

def validate_cron_expression(expression: str) -> bool:
    """Validate CRON expression format"""
    # Basic CRON validation (minute hour day month weekday)
    parts = expression.split()
    if len(parts) != 5:
        return False
    
    # Define valid ranges for each field
    ranges = [
        (0, 59),   # minute
        (0, 23),   # hour
        (1, 31),   # day
        (1, 12),   # month
        (0, 6),    # weekday
    ]
    
    for i, part in enumerate(parts):
        if part == '*':
            continue
        
        # Handle ranges (e.g., "1-5")
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                if start < ranges[i][0] or end > ranges[i][1] or start > end:
                    return False
            except ValueError:
                return False
        # Handle step values (e.g., "*/5")
        elif '/' in part:
            try:
                base, step = part.split('/')
                if base != '*':
                    base_val = int(base)
                    if base_val < ranges[i][0] or base_val > ranges[i][1]:
                        return False
                step_val = int(step)
                if step_val <= 0:
                    return False
            except ValueError:
                return False
        # Handle lists (e.g., "1,3,5")
        elif ',' in part:
            try:
                values = [int(x) for x in part.split(',')]
                for val in values:
                    if val < ranges[i][0] or val > ranges[i][1]:
                        return False
            except ValueError:
                return False
        # Handle single values
        else:
            try:
                val = int(part)
                if val < ranges[i][0] or val > ranges[i][1]:
                    return False
            except ValueError:
                return False
    
    return True

def calculate_next_run_time(trigger_type: str, config: dict) -> Optional[datetime]:
    """Calculate the next run time for a trigger"""
    now = datetime.now()
    
    if trigger_type == "interval":
        seconds = config.get("seconds", 0)
        return now + timedelta(seconds=seconds)
    
    elif trigger_type == "cron":
        # For now, return a placeholder. In production, use croniter library
        # This is a simplified implementation
        return now + timedelta(hours=1)
    
    elif trigger_type == "startup":
        # Startup triggers run immediately when the system starts
        return now
    
    else:  # manual
        return None

@router.get("/status")
async def get_execution_status(current_user: dict = Depends(get_current_user)):
    """Get current execution status"""
    with get_db() as conn:
        # Get running executions
        cursor = conn.execute("""
            SELECT el.*, s.name as script_name
            FROM execution_logs el
            JOIN scripts s ON el.script_id = s.id
            WHERE el.status = 'running'
            ORDER BY el.started_at DESC
        """)
        
        running_executions = []
        for row in cursor.fetchall():
            running_executions.append({
                "id": row["id"],
                "script_id": row["script_id"],
                "script_name": row["script_name"],
                "started_at": row["started_at"],
                "duration_ms": int((datetime.now() - datetime.fromisoformat(row["started_at"])).total_seconds() * 1000)
            })
        
        # Get recent executions
        cursor = conn.execute("""
            SELECT el.*, s.name as script_name
            FROM execution_logs el
            JOIN scripts s ON el.script_id = s.id
            WHERE el.status != 'running'
            ORDER BY el.started_at DESC
            LIMIT 10
        """)
        
        recent_executions = []
        for row in cursor.fetchall():
            recent_executions.append({
                "id": row["id"],
                "script_id": row["script_id"],
                "script_name": row["script_name"],
                "started_at": row["started_at"],
                "finished_at": row["finished_at"],
                "duration_ms": row["duration_ms"],
                "status": row["status"],
                "exit_code": row["exit_code"]
            })
        
        return {
            "running_executions": running_executions,
            "recent_executions": recent_executions,
            "total_running": len(running_executions)
        }

@router.post("/triggers", response_model=TriggerResponse)
async def create_trigger(
    trigger: TriggerCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new trigger for a script"""
    with get_db() as conn:
        # Check if script exists
        cursor = conn.execute("SELECT id FROM scripts WHERE id = ?", (trigger.script_id,))
        if not cursor.fetchone():
            raise HTTPException(404, "Script not found")
        
        # Validate trigger configuration
        if trigger.trigger_type == "cron":
            if "expression" not in trigger.config:
                raise HTTPException(400, "CRON trigger requires 'expression' in config")
            if not validate_cron_expression(trigger.config["expression"]):
                raise HTTPException(400, "Invalid CRON expression")
        elif trigger.trigger_type == "interval":
            if "seconds" not in trigger.config:
                raise HTTPException(400, "Interval trigger requires 'seconds' in config")
            if not isinstance(trigger.config["seconds"], int) or trigger.config["seconds"] <= 0:
                raise HTTPException(400, "Interval seconds must be a positive integer")
        
        # Calculate next run time
        next_run_at = calculate_next_run_time(trigger.trigger_type, trigger.config)
        
        # Create trigger
        cursor = conn.execute("""
            INSERT INTO triggers (script_id, trigger_type, config, enabled, next_run_at)
            VALUES (?, ?, ?, ?, ?)
        """, (trigger.script_id, trigger.trigger_type, json.dumps(trigger.config), trigger.enabled, 
              next_run_at.isoformat() if next_run_at else None))
        
        trigger_id = cursor.lastrowid
        
        # Return created trigger
        cursor = conn.execute("SELECT * FROM triggers WHERE id = ?", (trigger_id,))
        created_trigger = cursor.fetchone()
        
        return TriggerResponse(
            id=created_trigger["id"],
            script_id=created_trigger["script_id"],
            trigger_type=created_trigger["trigger_type"],
            config=json.loads(created_trigger["config"]),
            enabled=created_trigger["enabled"],
            created_at=created_trigger["created_at"],
            last_triggered_at=created_trigger["last_triggered_at"],
            next_run_at=created_trigger["next_run_at"]
        )

@router.get("/triggers", response_model=List[TriggerResponse])
async def list_triggers(
    script_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """List all triggers or triggers for a specific script"""
    with get_db() as conn:
        query = "SELECT * FROM triggers"
        params = []
        
        if script_id:
            query += " WHERE script_id = ?"
            params.append(script_id)
        
        query += " ORDER BY created_at DESC"
        
        cursor = conn.execute(query, params)
        triggers = []
        for row in cursor.fetchall():
            triggers.append(TriggerResponse(
                id=row["id"],
                script_id=row["script_id"],
                trigger_type=row["trigger_type"],
                config=json.loads(row["config"]),
                enabled=row["enabled"],
                created_at=row["created_at"],
                last_triggered_at=row["last_triggered_at"],
                next_run_at=row["next_run_at"]
            ))
        
        return triggers

@router.get("/triggers/{trigger_id}", response_model=TriggerResponse)
async def get_trigger(
    trigger_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get specific trigger"""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM triggers WHERE id = ?", (trigger_id,))
        trigger = cursor.fetchone()
        
        if not trigger:
            raise HTTPException(404, "Trigger not found")
        
        return TriggerResponse(
            id=trigger["id"],
            script_id=trigger["script_id"],
            trigger_type=trigger["trigger_type"],
            config=json.loads(trigger["config"]),
            enabled=trigger["enabled"],
            created_at=trigger["created_at"],
            last_triggered_at=trigger["last_triggered_at"],
            next_run_at=trigger["next_run_at"]
        )

@router.put("/triggers/{trigger_id}")
async def update_trigger(
    trigger_id: int,
    trigger: TriggerCreate,
    current_user: dict = Depends(get_current_user)
):
    """Update trigger"""
    with get_db() as conn:
        cursor = conn.execute("""
            UPDATE triggers SET
                trigger_type = ?,
                config = ?,
                enabled = ?
            WHERE id = ?
        """, (trigger.trigger_type, json.dumps(trigger.config), trigger.enabled, trigger_id))
        
        if cursor.rowcount == 0:
            raise HTTPException(404, "Trigger not found")
        
        return {"success": True, "message": "Trigger updated successfully"}

@router.delete("/triggers/{trigger_id}")
async def delete_trigger(
    trigger_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Delete trigger"""
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM triggers WHERE id = ?", (trigger_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(404, "Trigger not found")
        
        return {"success": True, "message": "Trigger deleted successfully"}

@router.post("/triggers/{trigger_id}/toggle")
async def toggle_trigger(
    trigger_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Toggle trigger enabled/disabled"""
    with get_db() as conn:
        cursor = conn.execute("""
            UPDATE triggers SET enabled = NOT enabled WHERE id = ?
        """, (trigger_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(404, "Trigger not found")
        
        # Get updated trigger
        cursor = conn.execute("SELECT enabled FROM triggers WHERE id = ?", (trigger_id,))
        trigger = cursor.fetchone()
        
        return {
            "success": True,
            "enabled": trigger["enabled"],
            "message": f"Trigger {'enabled' if trigger['enabled'] else 'disabled'}"
        }

@router.get("/queue")
async def get_execution_queue(current_user: dict = Depends(get_current_user)):
    """Get execution queue status (placeholder for Celery integration)"""
    # This would integrate with Celery to show queued tasks
    return {
        "queued_tasks": [],
        "active_tasks": [],
        "total_queued": 0,
        "total_active": 0
    }

@router.post("/validate-cron")
async def validate_cron(
    expression: str,
    current_user: dict = Depends(get_current_user)
):
    """Validate CRON expression and return next run times"""
    if not validate_cron_expression(expression):
        raise HTTPException(400, "Invalid CRON expression")
    
    # Calculate next few run times (simplified)
    next_runs = []
    base_time = datetime.now()
    
    # For demo purposes, show next 5 theoretical runs
    for i in range(5):
        next_time = base_time + timedelta(hours=i+1)  # Simplified calculation
        next_runs.append({
            "time": next_time.isoformat(),
            "description": next_time.strftime("%Y-%m-%d %H:%M:%S")
        })
    
    return {
        "valid": True,
        "next_runs": next_runs,
        "description": f"CRON expression: {expression}"
    }

@router.get("/triggers/upcoming")
async def get_upcoming_triggers(
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """Get upcoming trigger executions"""
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT t.*, s.name as script_name
            FROM triggers t
            JOIN scripts s ON t.script_id = s.id
            WHERE t.enabled = true 
            AND t.next_run_at IS NOT NULL
            ORDER BY t.next_run_at ASC
            LIMIT ?
        """, (limit,))
        
        upcoming = []
        for row in cursor.fetchall():
            upcoming.append({
                "id": row["id"],
                "script_id": row["script_id"],
                "script_name": row["script_name"],
                "trigger_type": row["trigger_type"],
                "config": json.loads(row["config"]),
                "next_run_at": row["next_run_at"],
                "next_run_description": datetime.fromisoformat(row["next_run_at"]).strftime("%Y-%m-%d %H:%M:%S") if row["next_run_at"] else None
            })
        
        return upcoming