from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..auth import get_current_user
from ..models import ExecutionLogResponse

router = APIRouter()

@router.get("/", response_model=List[ExecutionLogResponse])
async def list_execution_logs(
    script_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """Get execution logs with optional filtering"""
    with get_db() as conn:
        query = """
            SELECT el.*, s.name as script_name
            FROM execution_logs el
            JOIN scripts s ON el.script_id = s.id
            WHERE 1=1
        """
        params = []
        
        if script_id:
            query += " AND el.script_id = ?"
            params.append(script_id)
        
        if status:
            query += " AND el.status = ?"
            params.append(status)
        
        query += " ORDER BY el.started_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor = conn.execute(query, params)
        logs = []
        for row in cursor.fetchall():
            log_dict = dict(row)
            log_dict.pop('script_name', None)  # Remove join field
            logs.append(ExecutionLogResponse(**log_dict))
        
        return logs

@router.get("/{log_id}", response_model=ExecutionLogResponse)
async def get_execution_log(
    log_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get specific execution log"""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM execution_logs WHERE id = ?", (log_id,))
        log = cursor.fetchone()
        
        if not log:
            raise HTTPException(404, "Execution log not found")
        
        return ExecutionLogResponse(**dict(log))

@router.get("/script/{safe_name}", response_model=List[ExecutionLogResponse])
async def get_script_execution_logs(
    safe_name: str,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """Get execution logs for a specific script"""
    with get_db() as conn:
        # Check if script exists and get script_id
        cursor = conn.execute("SELECT id FROM scripts WHERE safe_name = ?", (safe_name,))
        script = cursor.fetchone()
        if not script:
            raise HTTPException(404, "Script not found")
        
        script_id = script["id"]
        
        # Get logs
        cursor = conn.execute("""
            SELECT * FROM execution_logs 
            WHERE script_id = ? 
            ORDER BY started_at DESC 
            LIMIT ? OFFSET ?
        """, (script_id, limit, offset))
        
        logs = []
        for row in cursor.fetchall():
            logs.append(ExecutionLogResponse(**dict(row)))
        
        return logs

@router.delete("/{log_id}")
async def delete_execution_log(
    log_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Delete specific execution log"""
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM execution_logs WHERE id = ?", (log_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(404, "Execution log not found")
        
        return {"success": True, "message": "Execution log deleted successfully"}

@router.delete("/script/{safe_name}")
async def delete_script_execution_logs(
    safe_name: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete all execution logs for a script"""
    with get_db() as conn:
        # Check if script exists and get script_id
        cursor = conn.execute("SELECT id FROM scripts WHERE safe_name = ?", (safe_name,))
        script = cursor.fetchone()
        if not script:
            raise HTTPException(404, "Script not found")
        
        script_id = script["id"]
        
        # Delete logs
        cursor = conn.execute("DELETE FROM execution_logs WHERE script_id = ?", (script_id,))
        
        return {
            "success": True,
            "message": f"Deleted {cursor.rowcount} execution logs for script"
        }

@router.post("/cleanup")
async def cleanup_old_logs(
    days: int = 30,
    current_user: dict = Depends(get_current_user)
):
    """Clean up old execution logs"""
    if not current_user.get("is_admin"):
        raise HTTPException(403, "Admin access required")
    
    with get_db() as conn:
        # Delete logs older than specified days
        cursor = conn.execute("""
            DELETE FROM execution_logs 
            WHERE started_at < datetime('now', '-{} days')
        """.format(days))
        
        deleted_count = cursor.rowcount
        
        return {
            "success": True,
            "message": f"Cleaned up {deleted_count} old execution logs"
        }

@router.get("/stats/summary")
async def get_execution_stats(
    script_id: Optional[int] = None,
    days: int = 30,
    current_user: dict = Depends(get_current_user)
):
    """Get execution statistics"""
    with get_db() as conn:
        query = """
            SELECT 
                COUNT(*) as total_executions,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_executions,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_executions,
                AVG(duration_ms) as avg_duration_ms,
                MIN(started_at) as first_execution,
                MAX(started_at) as last_execution
            FROM execution_logs
            WHERE started_at > datetime('now', '-{} days')
        """.format(days)
        
        params = []
        if script_id:
            query += " AND script_id = ?"
            params.append(script_id)
        
        cursor = conn.execute(query, params)
        stats = cursor.fetchone()
        
        return {
            "total_executions": stats["total_executions"] or 0,
            "successful_executions": stats["successful_executions"] or 0,
            "failed_executions": stats["failed_executions"] or 0,
            "success_rate": (stats["successful_executions"] or 0) / max(stats["total_executions"] or 1, 1) * 100,
            "avg_duration_ms": stats["avg_duration_ms"] or 0,
            "first_execution": stats["first_execution"],
            "last_execution": stats["last_execution"],
            "days": days
        }