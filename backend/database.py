import sqlite3
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator
import hashlib

DATABASE_PATH = Path(os.getenv("PYSCHED_DATA_PATH", "./data")) / "pyscheduler.db"

@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Database connection context manager"""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
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

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def migrate_database(conn):
    """Run database migrations"""
    # Migration 1: Add email_trigger_type field to scripts table
    try:
        cursor = conn.execute("SELECT email_trigger_type FROM scripts LIMIT 1")
        cursor.fetchone()  # If this succeeds, the field exists
    except Exception:
        # Field doesn't exist, add it
        conn.execute("ALTER TABLE scripts ADD COLUMN email_trigger_type TEXT DEFAULT 'all'")
        print("Added email_trigger_type field to scripts table")

def init_database():
    """Initialize database with schema"""
    with get_db() as conn:
        conn.executescript("""
            -- Scripts table - Core script metadata
            CREATE TABLE IF NOT EXISTS scripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                safe_name TEXT NOT NULL,
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
                email_trigger_type TEXT DEFAULT 'all', -- 'all', 'success', 'failure'
                
                -- Environment variables and auto-save
                environment_variables TEXT DEFAULT '{}',
                auto_save BOOLEAN DEFAULT true,
                
                UNIQUE(name, folder_id),
                UNIQUE(safe_name, folder_id)
            );

            -- Folders table - Simple organization
            CREATE TABLE IF NOT EXISTS folders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                parent_id INTEGER REFERENCES folders(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(name, parent_id)
            );

            -- Triggers table - Scheduling configuration
            CREATE TABLE IF NOT EXISTS triggers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                script_id INTEGER REFERENCES scripts(id) ON DELETE CASCADE,
                trigger_type TEXT NOT NULL,
                config TEXT NOT NULL,
                enabled BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_triggered_at TIMESTAMP,
                next_run_at TIMESTAMP
            );

            -- Execution logs table - History and monitoring
            CREATE TABLE IF NOT EXISTS execution_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                script_id INTEGER REFERENCES scripts(id) ON DELETE CASCADE,
                trigger_id INTEGER REFERENCES triggers(id) ON DELETE SET NULL,
                
                -- Execution timing
                started_at TIMESTAMP NOT NULL,
                finished_at TIMESTAMP,
                duration_ms INTEGER,
                
                -- Execution results
                status TEXT NOT NULL,
                exit_code INTEGER,
                stdout TEXT,
                stderr TEXT,
                
                -- Resource usage
                max_memory_mb INTEGER,
                max_cpu_percent DECIMAL(5,2),
                
                -- Metadata
                triggered_by TEXT
            );

            -- Users table - Simple authentication
            CREATE TABLE IF NOT EXISTS users (
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
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                description TEXT
            );

            -- Create indexes
            CREATE INDEX IF NOT EXISTS idx_execution_logs_script_id ON execution_logs(script_id, started_at DESC);
            CREATE INDEX IF NOT EXISTS idx_execution_logs_status ON execution_logs(status, started_at DESC);
            CREATE INDEX IF NOT EXISTS idx_scripts_folder_id ON scripts(folder_id);
            CREATE INDEX IF NOT EXISTS idx_triggers_script_id ON triggers(script_id);
        """)
        
        # Run migrations
        migrate_database(conn)
        
        # Create default admin user if none exists
        cursor = conn.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            admin_username = os.getenv("PYSCHED_ADMIN_USERNAME", "admin")
            admin_password = os.getenv("PYSCHED_ADMIN_PASSWORD")
            admin_email = os.getenv("PYSCHED_ADMIN_EMAIL", "admin@localhost")
            
            # Generate secure random password if not provided
            if not admin_password:
                import secrets
                import string
                # Generate 16-character secure password
                alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
                admin_password = ''.join(secrets.choice(alphabet) for _ in range(16))
                print(f"Generated secure admin password: {admin_password}")
                print("IMPORTANT: Please save this password and change it after first login!")
            
            conn.execute("""
                INSERT INTO users (username, email, password_hash, is_admin)
                VALUES (?, ?, ?, true)
            """, (admin_username, admin_email, hash_password(admin_password)))
        
        # Create default settings
        settings = [
            ('api_key', 'default-api-key-change-me', 'Default API key for URL triggers'),
            ('rate_limit_enabled', 'true', 'Enable rate limiting'),
            ('default_script_timeout', '300', 'Default script timeout in seconds'),
            ('default_memory_limit', '512', 'Default memory limit in MB'),
            ('max_execution_logs', '1000', 'Maximum execution logs to keep per script'),
            ('log_retention_days', '30', 'Days to keep execution logs'),
        ]
        
        for key, value, description in settings:
            conn.execute("""
                INSERT OR IGNORE INTO settings (key, value, description)
                VALUES (?, ?, ?)
            """, (key, value, description))

if __name__ == "__main__":
    init_database()
    print("Database initialized successfully")