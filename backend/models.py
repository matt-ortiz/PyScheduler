from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import re

class ScriptCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field("", max_length=500)
    content: str = Field(..., min_length=1)
    folder_id: Optional[int] = None
    python_version: str = Field("3.12", pattern=r"^3\.(8|9|10|11|12)$")
    requirements: str = Field("", max_length=10000)
    email_notifications: bool = False
    email_recipients: str = Field("", max_length=500)
    email_trigger_type: str = Field("all", pattern=r"^(all|success|failure)$")
    environment_variables: str = Field("{}", max_length=5000)
    auto_save: bool = True
    
    @validator('content')
    def validate_python_syntax(cls, v):
        """Validate Python syntax"""
        if not v.strip():
            raise ValueError('Script content cannot be empty')
        
        try:
            compile(v, '<script>', 'exec')
        except SyntaxError as e:
            raise ValueError(f'Invalid Python syntax: {e}')
        
        return v
    
    @validator('requirements')
    def validate_requirements(cls, v):
        """Validate pip requirements format"""
        if not v.strip():
            return v
        
        lines = v.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                # Basic package name validation
                package_name = line.split('==')[0].split('>=')[0].split('<=')[0].split('~=')[0].strip()
                if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-_\.]*$', package_name):
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
            
            for key, value in env_dict.items():
                if not isinstance(key, str) or not isinstance(value, str):
                    raise ValueError('Environment variable names and values must be strings')
                if not re.match(r'^[A-Z_][A-Z0-9_]*$', key):
                    raise ValueError(f'Invalid environment variable name: {key}')
            
            return v
        except json.JSONDecodeError:
            raise ValueError('Environment variables must be valid JSON')

class ScriptUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = Field(None, min_length=1)
    folder_id: Optional[int] = None
    python_version: Optional[str] = Field(None, pattern=r"^3\.(8|9|10|11|12)$")
    requirements: Optional[str] = Field(None, max_length=10000)
    email_notifications: Optional[bool] = None
    email_recipients: Optional[str] = Field(None, max_length=500)
    email_trigger_type: Optional[str] = Field(None, pattern=r"^(all|success|failure)$")
    environment_variables: Optional[str] = Field(None, max_length=5000)
    auto_save: Optional[bool] = None
    enabled: Optional[bool] = None

class ScriptResponse(BaseModel):
    id: int
    name: str
    safe_name: str
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
    email_trigger_type: str
    environment_variables: str
    auto_save: bool

class FolderCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    parent_id: Optional[int] = None

class FolderResponse(BaseModel):
    id: int
    name: str
    parent_id: Optional[int]
    created_at: str

class TriggerCreate(BaseModel):
    script_id: int
    trigger_type: str = Field(..., pattern=r"^(interval|cron|manual|startup)$")
    config: Dict[str, Any]
    enabled: bool = True

class TriggerResponse(BaseModel):
    id: int
    script_id: int
    trigger_type: str
    config: Dict[str, Any]
    enabled: bool
    created_at: str
    last_triggered_at: Optional[str]
    next_run_at: Optional[str]

class ExecutionLogResponse(BaseModel):
    id: int
    script_id: int
    trigger_id: Optional[int]
    started_at: str
    finished_at: Optional[str]
    duration_ms: Optional[int]
    status: str
    exit_code: Optional[int]
    stdout: Optional[str]
    stderr: Optional[str]
    max_memory_mb: Optional[int]
    max_cpu_percent: Optional[float]
    triggered_by: Optional[str]

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., max_length=100)
    password: str = Field(..., min_length=6)

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    theme: str
    timezone: str
    is_admin: bool
    created_at: str
    last_login_at: Optional[str]

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class AutoSaveRequest(BaseModel):
    content: str

class CronValidationRequest(BaseModel):
    expression: str = Field(..., min_length=1, max_length=100)