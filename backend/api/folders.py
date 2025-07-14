from fastapi import APIRouter, HTTPException, Depends
from typing import List

from ..database import get_db
from ..auth import get_current_user
from ..models import FolderCreate, FolderResponse

router = APIRouter()

@router.get("/", response_model=List[FolderResponse])
@router.get("", response_model=List[FolderResponse])
async def list_folders(current_user: dict = Depends(get_current_user)):
    """Get all folders"""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM folders ORDER BY name")
        folders = []
        for row in cursor.fetchall():
            folders.append(FolderResponse(
                id=row["id"],
                name=row["name"],
                parent_id=row["parent_id"],
                created_at=row["created_at"]
            ))
        return folders

@router.post("/", response_model=FolderResponse)
@router.post("", response_model=FolderResponse)
async def create_folder(
    folder: FolderCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new folder"""
    with get_db() as conn:
        # Check if folder name already exists in parent
        cursor = conn.execute(
            "SELECT id FROM folders WHERE name = ? AND parent_id = ?",
            (folder.name, folder.parent_id)
        )
        if cursor.fetchone():
            raise HTTPException(400, "Folder name already exists in parent folder")
        
        # Create folder
        cursor = conn.execute("""
            INSERT INTO folders (name, parent_id)
            VALUES (?, ?)
        """, (folder.name, folder.parent_id))
        
        folder_id = cursor.lastrowid
        
        # Return created folder
        cursor = conn.execute("SELECT * FROM folders WHERE id = ?", (folder_id,))
        created_folder = cursor.fetchone()
        
        return FolderResponse(
            id=created_folder["id"],
            name=created_folder["name"],
            parent_id=created_folder["parent_id"],
            created_at=created_folder["created_at"]
        )

@router.get("/{folder_id}", response_model=FolderResponse)
async def get_folder(
    folder_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get folder by ID"""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM folders WHERE id = ?", (folder_id,))
        folder = cursor.fetchone()
        
        if not folder:
            raise HTTPException(404, "Folder not found")
        
        return FolderResponse(
            id=folder["id"],
            name=folder["name"],
            parent_id=folder["parent_id"],
            created_at=folder["created_at"]
        )

@router.put("/{folder_id}", response_model=FolderResponse)
async def update_folder(
    folder_id: int,
    folder: FolderCreate,
    current_user: dict = Depends(get_current_user)
):
    """Update folder"""
    with get_db() as conn:
        # Check if folder exists
        cursor = conn.execute("SELECT * FROM folders WHERE id = ?", (folder_id,))
        existing_folder = cursor.fetchone()
        
        if not existing_folder:
            raise HTTPException(404, "Folder not found")
        
        # Check if new name conflicts with existing folder in parent
        cursor = conn.execute(
            "SELECT id FROM folders WHERE name = ? AND parent_id = ? AND id != ?",
            (folder.name, folder.parent_id, folder_id)
        )
        if cursor.fetchone():
            raise HTTPException(400, "Folder name already exists in parent folder")
        
        # Update folder
        cursor = conn.execute("""
            UPDATE folders SET name = ?, parent_id = ?
            WHERE id = ?
        """, (folder.name, folder.parent_id, folder_id))
        
        # Return updated folder
        cursor = conn.execute("SELECT * FROM folders WHERE id = ?", (folder_id,))
        updated_folder = cursor.fetchone()
        
        return FolderResponse(
            id=updated_folder["id"],
            name=updated_folder["name"],
            parent_id=updated_folder["parent_id"],
            created_at=updated_folder["created_at"]
        )

@router.delete("/{folder_id}")
async def delete_folder(
    folder_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Delete folder"""
    with get_db() as conn:
        # Check if folder exists
        cursor = conn.execute("SELECT * FROM folders WHERE id = ?", (folder_id,))
        if not cursor.fetchone():
            raise HTTPException(404, "Folder not found")
        
        # Check if folder has scripts
        cursor = conn.execute("SELECT COUNT(*) FROM scripts WHERE folder_id = ?", (folder_id,))
        script_count = cursor.fetchone()[0]
        
        if script_count > 0:
            raise HTTPException(400, f"Cannot delete folder with {script_count} scripts")
        
        # Check if folder has subfolders
        cursor = conn.execute("SELECT COUNT(*) FROM folders WHERE parent_id = ?", (folder_id,))
        subfolder_count = cursor.fetchone()[0]
        
        if subfolder_count > 0:
            raise HTTPException(400, f"Cannot delete folder with {subfolder_count} subfolders")
        
        # Delete folder
        cursor = conn.execute("DELETE FROM folders WHERE id = ?", (folder_id,))
        
        return {"success": True, "message": "Folder deleted successfully"}