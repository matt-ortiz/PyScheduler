from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from typing import List, Optional
from pydantic import BaseModel

from ..database import get_db, hash_password
from ..auth import create_access_token, verify_password, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
from ..models import UserCreate, UserResponse, LoginRequest, LoginResponse
from ..timezone_utils import get_timezone_list, validate_timezone

router = APIRouter()

@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """Authenticate user and return access token"""
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM users WHERE username = ?", 
            (login_data.username,)
        )
        user = cursor.fetchone()
        
        if not user or not verify_password(login_data.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Update last login
        conn.execute(
            "UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id = ?",
            (user["id"],)
        )
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["username"]}, expires_delta=access_token_expires
        )
        
        user_response = UserResponse(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            theme=user["theme"],
            timezone=user["timezone"],
            is_admin=user["is_admin"],
            created_at=user["created_at"],
            last_login_at=user["last_login_at"]
        )
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    """Register a new user"""
    with get_db() as conn:
        # Check if username already exists
        cursor = conn.execute("SELECT id FROM users WHERE username = ?", (user_data.username,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        
        # Check if email already exists
        cursor = conn.execute("SELECT id FROM users WHERE email = ?", (user_data.email,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        
        # Create user
        hashed_password = hash_password(user_data.password)
        cursor = conn.execute("""
            INSERT INTO users (username, email, password_hash, is_admin)
            VALUES (?, ?, ?, ?)
        """, (user_data.username, user_data.email, hashed_password, False))
        
        user_id = cursor.lastrowid
        
        # Get created user
        cursor = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        return UserResponse(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            theme=user["theme"],
            timezone=user["timezone"],
            is_admin=user["is_admin"],
            created_at=user["created_at"],
            last_login_at=user["last_login_at"]
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=current_user["id"],
        username=current_user["username"],
        email=current_user["email"],
        theme=current_user["theme"],
        timezone=current_user["timezone"],
        is_admin=current_user["is_admin"],
        created_at=current_user["created_at"],
        last_login_at=current_user["last_login_at"]
    )

class UserUpdateRequest(BaseModel):
    theme: Optional[str] = None
    timezone: Optional[str] = None

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    update_data: UserUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update current user preferences"""
    with get_db() as conn:
        updates = []
        params = []
        
        if update_data.theme is not None:
            updates.append("theme = ?")
            params.append(update_data.theme)
        
        if update_data.timezone is not None:
            if not validate_timezone(update_data.timezone):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid timezone"
                )
            updates.append("timezone = ?")
            params.append(update_data.timezone)
        
        if updates:
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            params.append(current_user["id"])
            conn.execute(query, params)
        
        # Get updated user
        cursor = conn.execute("SELECT * FROM users WHERE id = ?", (current_user["id"],))
        user = cursor.fetchone()
        
        return UserResponse(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            theme=user["theme"],
            timezone=user["timezone"],
            is_admin=user["is_admin"],
            created_at=user["created_at"],
            last_login_at=user["last_login_at"]
        )

@router.get("/users", response_model=List[UserResponse])
async def list_users(current_user: dict = Depends(get_current_user)):
    """List all users (admin only)"""
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM users ORDER BY created_at DESC")
        users = []
        for row in cursor.fetchall():
            users.append(UserResponse(
                id=row["id"],
                username=row["username"],
                email=row["email"],
                theme=row["theme"],
                timezone=row["timezone"],
                is_admin=row["is_admin"],
                created_at=row["created_at"],
                last_login_at=row["last_login_at"]
            ))
        return users

@router.get("/timezones")
async def get_timezones():
    """Get list of available timezones"""
    return get_timezone_list()