# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**PyScheduler** is a web-based Python script scheduling and monitoring platform that solves the common problem of running Python scripts on a schedule while providing proper dependency isolation, real-time monitoring, and comprehensive logging.

### Key Features
- **Simple Script Creation** - Quick dialog asking only for script name and optional folder
- **Safe Name Generation** - Convert script names to safe filesystem names (e.g., "Hello World" → "hello-world")
- **Virtual Environment Isolation** - Each script runs in its own Python virtual environment
- **Real-time Monitoring** - Live script execution monitoring via WebSocket
- **Multiple Scheduling Types** - CRON expressions, intervals, manual execution, and startup triggers
- **Script Organization** - Simple folder structure for organizing multiple scripts
- **Email Notifications** - Get notified when scripts succeed or fail
- **Secure API Access** - URL triggers with API key authentication and rate limiting
- **Auto-save Functionality** - Real-time saving of script changes to prevent data loss
- **Security Features** - Python syntax validation, resource limits, and input sanitization
- **Environment Variables** - Per-script custom environment variables
- **Advanced Logging** - Complete execution history with search and filtering capabilities
- **Modern UI** - Dark/light themes, mobile-friendly, real-time updates, keyboard shortcuts

## Architecture

The system uses a **single-container architecture** with the following components:

### Backend (Python)
- **FastAPI** - REST API and WebSocket server with automatic documentation
- **SQLite** - Database for metadata (scripts, schedules, logs)
- **Celery + Redis** - Background task queue for script execution
- **Virtual Environment Management** - Isolated Python environments per script
- **SlowAPI** - Rate limiting middleware for API protection

### Frontend (JavaScript)
- **Vue.js 3** - Modern web interface
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **TypeScript** - Type safety for better code quality
- **WebSocket** - Real-time updates
- **Pinia** - State management

### Database Schema
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
    environment_variables TEXT DEFAULT '{}',  -- JSON object of env vars
    
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
    
    -- Auto-save functionality
    auto_save BOOLEAN DEFAULT true,
    
    UNIQUE(name, folder_id),
    UNIQUE(safe_name, folder_id)
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
    config TEXT NOT NULL,       -- JSON configuration
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
    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    duration_ms INTEGER,
    status TEXT NOT NULL, -- 'running', 'success', 'failed', 'timeout'
    exit_code INTEGER,
    stdout TEXT,
    stderr TEXT,
    max_memory_mb INTEGER,
    max_cpu_percent DECIMAL(5,2),
    triggered_by TEXT, -- 'schedule', 'manual', 'startup', 'url'
    INDEX(script_id, started_at DESC),
    INDEX(status, started_at DESC)
);

-- Users table - Basic authentication
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    theme TEXT DEFAULT 'dark',
    timezone TEXT DEFAULT 'UTC',
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

## Development Commands

Since this is a fresh project setup, the following commands will be needed once implementation begins:

### Backend Development
```bash
# Install Python dependencies
pip install -r requirements.txt

# Run FastAPI development server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Run Celery worker
celery -A backend.tasks worker --loglevel=info

# Run Celery beat scheduler
celery -A backend.tasks beat --loglevel=info

# Run Redis server (for development)
redis-server
```

### Frontend Development
```bash
# Install Node.js dependencies
npm install

# Run Vite development server
npm run dev

# Build for production
npm run build

# Run tests
npm test

# Run linting
npm run lint

# Run type checking
npm run type-check
```

### Database Management
```bash
# Initialize database
python -c "from backend.database import init_database; init_database()"

# Run database migrations (if implemented)
python backend/migrate.py

# Backup database
cp /data/pyscheduler.db /data/backups/pyscheduler-$(date +%Y%m%d).db
```

### Testing
```bash
# Run Python tests
pytest backend/tests/

# Run Python tests with coverage
pytest --cov=backend backend/tests/

# Run frontend tests
npm test

# Run end-to-end tests
npm run test:e2e
```

## File Structure

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
│   │   │   ├── weather-api.py
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

## Important Implementation Details

### Script Creation Workflow
The script creation process is **minimal and fast** to encourage users to create scripts:

1. **Create Script Dialog** - User clicks "New Script" button
   - **Script Name** - Enter display name (e.g., "Hello World", "Data Backup")
   - **Folder** - Optional folder selection for organization
   - **Create Button** - Creates script immediately

2. **Automatic Setup** - System automatically:
   - **Generates Safe Name** - Converts "Hello World" to "hello-world" for filesystem
   - **Creates Virtual Environment** - Sets up isolated Python environment
   - **Creates Directory Structure** - Organized file structure
   - **Opens Script Editor** - User can immediately start coding

### Script Name Management
- **Display Names**: User-friendly names (e.g., "Hello World", "Data Backup")
- **Safe Names**: Filesystem-safe names (e.g., "hello-world", "data-backup")
- **Safe Name Generation Rules**:
  - Convert to lowercase letters
  - Replace spaces with hyphens (-)
  - Remove special characters - keep only letters, numbers, hyphens
  - Ensure uniqueness - add suffix if name exists (hello-world-2)
- **Examples**:
  - "Hello World" → "hello-world"
  - "Data Backup Script!" → "data-backup-script"
  - "API Call #1" → "api-call-1"

### Security Features
- **Script Validation** - Python syntax checking and basic security scanning
- **Resource Limits** - Configurable timeout, memory, and CPU limits per script
- **Execution Isolation** - Scripts run in sandboxed virtual environments
- **Input Sanitization** - Comprehensive validation of all user inputs
- **Rate Limiting** - Protection against abuse and overload
- **API Key Management** - Secure remote access with mandatory authentication
- **Secure Auto-save** - Real-time saving with security validation

### Virtual Environment Management
- Each script gets its own isolated Python environment
- Automatic pip requirements installation with progress tracking
- Support for different Python versions (3.8-3.12)
- Environment health checks and cleanup
- Custom environment variables per script

### Real-time Features
- WebSocket connection for live script execution monitoring
- Auto-save functionality for script editing
- Live output streaming during execution
- Real-time execution status updates
- Live updates without page refreshes

### Scheduling System
- **Multiple Trigger Types**:
  - **Interval Scheduling** - Run every X seconds/minutes/hours
  - **CRON Expressions** - Full cron syntax with validation
  - **Manual Execution** - On-demand script running
  - **Startup Triggers** - Run scripts when the system starts
- **Visual CRON Builder** - Easy-to-use interface for creating CRON expressions
- **Schedule Preview** - See upcoming execution times
- **Timezone Support** - Proper handling of different timezones

## Configuration

The application uses environment variables for configuration:

```bash
# Basic Configuration
PYSCHED_DATA_PATH=/data
PYSCHED_SECRET_KEY=your-secret-key
PYSCHED_DEBUG=false

# Security Settings
PYSCHED_DEFAULT_API_KEY=your-default-api-key
PYSCHED_RATE_LIMIT_ENABLED=true
PYSCHED_DEFAULT_SCRIPT_TIMEOUT=300
PYSCHED_DEFAULT_MEMORY_LIMIT=512

# Email Notifications (Optional)
SMTP_SERVER=mail.smtp2go.com
SMTP_PORT=2525
SMTP_USERNAME=your-username
SMTP_PASSWORD=your-password
FROM_EMAIL=pysched@yourcompany.com
```

### Docker Deployment
```yaml
services:
  pyscheduler:
    image: pyscheduler:latest
    ports:
      - "8000:8000"
    environment:
      - PYSCHED_DATA_PATH=/data
      - PYSCHED_SECRET_KEY=your-secret-key
      - PYSCHED_DEFAULT_API_KEY=your-api-key
      - PYSCHED_RATE_LIMIT_ENABLED=true
    volumes:
      - pysched_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  pysched_data:
```

## Deployment

The application is designed for **single-container deployment** using Docker:

```bash
# Build and run with Docker Compose
docker-compose up -d

# Access application
http://localhost:8000
```

## API Endpoints

Key API endpoints for script management:

### Script Management
- `GET /api/scripts` - List all scripts with folder information
- `POST /api/scripts` - Create new script with validation
- `PUT /api/scripts/{id}` - Update script with environment variables
- `DELETE /api/scripts/{id}` - Delete script and cleanup
- `POST /api/scripts/{safe_name}/execute` - Execute script manually (authenticated)
- `GET /api/scripts/{safe_name}/trigger` - URL trigger execution (API key required)
- `PATCH /api/scripts/{safe_name}/auto-save` - Auto-save content (real-time)

### Folder Management
- `GET /api/folders` - List all folders
- `POST /api/folders` - Create new folder
- `PUT /api/folders/{id}` - Update folder
- `DELETE /api/folders/{id}` - Delete folder

### Execution & Monitoring
- `GET /api/logs/{script_id}` - Get execution history
- `GET /api/logs/{script_id}/{log_id}` - Get specific execution log
- `WebSocket /ws` - Real-time updates for script execution

### Authentication & Settings
- `POST /api/auth/login` - User authentication
- `POST /api/auth/logout` - User logout
- `GET /api/settings` - Get application settings
- `PUT /api/settings` - Update application settings

### Health & Monitoring
- `GET /api/health` - Health check endpoint
- `GET /api/stats` - System statistics
- `GET /api/version` - Application version info

## Target Users & Use Cases

### Primary Users
- **Individual Developers** - Personal automation scripts and development tasks
- **System Administrators** - Maintenance scripts, backups, and monitoring tasks  
- **Data Engineers** - ETL pipelines and data processing workflows
- **DevOps Engineers** - Build processes and deployment automation

### Use Cases
- **Data Processing** - Regular ETL jobs and data transformations
- **System Maintenance** - Cleanup scripts, log rotation, and health checks
- **Development Workflows** - Automated testing, builds, and deployments
- **Personal Automation** - Any recurring Python task that needs scheduling
- **Monitoring & Alerts** - Scripts that check systems and send notifications

## User Interface Features

### Modern Web Interface
- **Clean, responsive design** that works on all devices
- **Dark/Light Themes** - User preference for interface appearance
- **Real-time Updates** - Live updates without page refreshes
- **Mobile Friendly** - Works well on tablets and phones
- **Keyboard Shortcuts** - Efficient navigation for power users

### Script Editor Features
- **Syntax Highlighting** - Python code editor with proper syntax highlighting
- **Auto-completion** - Intelligent code completion for Python
- **Error Detection** - Real-time syntax error detection
- **Auto-save** - Automatic saving of script changes to prevent data loss
- **Version History** - Track changes to scripts over time

### Monitoring Dashboard
- **Script Status Overview** - See all scripts and their current status
- **Execution History** - Complete history of script runs with search
- **Real-time Logs** - Live streaming of script output during execution
- **Performance Metrics** - CPU, memory usage, and execution time tracking
- **Success/Failure Rates** - Monitor script reliability over time

## Performance Requirements

### Response Times
- **API responses** - Under 200ms for most operations
- **Page loads** - Sub-second initial load times
- **Script execution** - Minimal overhead for script startup
- **Real-time updates** - Instant WebSocket message delivery

### Resource Usage
- **Base system** - Uses less than 100MB RAM
- **Per script** - Configurable memory and CPU limits
- **Storage** - Efficient disk usage with automatic cleanup
- **Concurrent processing** - Handle multiple scripts running simultaneously

### Scalability
- **Support for 100+ Scripts** - Handle moderate script collections
- **10,000+ Execution Logs** - Efficient storage and retrieval of history
- **Multiple Concurrent Users** - Support for small teams
- **Resource Limits** - Configurable limits to prevent system overload

## Technology Stack

### Backend Stack
- **Python 3.12** - Modern Python with excellent performance
- **FastAPI** - High-performance web framework with automatic documentation
- **SQLite** - Simple, reliable database with no external dependencies
- **Celery + Redis** - Task queue for background script execution
- **WebSocket** - Real-time communication for live updates
- **SlowAPI** - Rate limiting middleware for API protection

### Frontend Stack
- **Vue.js 3** - Modern JavaScript framework with excellent performance
- **Vite** - Fast development and build tool
- **Tailwind CSS** - Utility-first CSS framework for rapid development
- **TypeScript** - Type safety for better code quality
- **Pinia** - State management for Vue.js
- **WebSocket** - Real-time communication with the backend

### Infrastructure
- **Docker** - Containerized deployment for easy setup
- **Single Container** - All services in one container for simplicity
- **File-based Storage** - Scripts and environments stored on disk
- **Nginx** - Static file serving and reverse proxy
- **Automatic Backup** - Built-in backup functionality

## System Requirements

### Minimum Requirements
- **CPU** - 1+ cores (2+ recommended)
- **RAM** - 512MB minimum (1GB+ recommended)
- **Storage** - 1GB+ for application and scripts
- **Network** - Local network access for web interface

### Supported Python Versions
- **Python 3.8** - Minimum supported version
- **Python 3.9** - Supported
- **Python 3.10** - Supported
- **Python 3.11** - Supported
- **Python 3.12** - Default and recommended version

## Development Notes

- The project emphasizes **simplicity and ease of deployment**
- All services run in a single container for easy home server deployment
- SQLite is used to avoid external database dependencies
- File-based storage enables simple backup and restore
- Virtual environments provide script isolation without complex containerization per script
- The UI prioritizes **quick script creation** (name + optional folder) over complex configuration
- **Security-first approach** with comprehensive input validation and resource limits
- **Real-time monitoring** is a core feature, not an add-on
- **Mobile-first design** ensures usability on all devices

## Current Project Status

### Project Location
- **Working Directory**: `/Users/matt/PycharmProjects/PyScheduler`
- **Git Repository**: Not initialized (local development only)
- **Environment**: macOS (Darwin 24.5.0)

### Implementation Status ✅
- **Core Backend**: Fully implemented and functional
  - FastAPI server with all API endpoints
  - SQLite database with complete schema
  - Virtual environment management
  - Script execution with proper isolation
  - CRON validation and scheduling logic
  - WebSocket support for real-time updates
  
- **Frontend**: Fully implemented and functional
  - Vue.js 3 with Composition API
  - Complete trigger management system
  - CRON builder with visual interface
  - Interval scheduler with presets
  - Script creation and editing
  - Real-time log viewing
  - Responsive design with dark/light themes

- **Docker Deployment**: Ready and tested
  - Single container architecture
  - Nginx for static file serving
  - Redis for task queue
  - Supervisor for process management
  - Health checks implemented

### Recent Fixes & Improvements
- **URL Trigger System**: Fixed script referencing to use `safe_name` instead of `script_id`
- **Security**: Replaced dangerous `eval()` usage with `json.loads()`
- **Frontend Build**: Updated and optimized for production
- **Docker Integration**: Container rebuilt and redeployed successfully

### Development Commands (Tested)

#### Frontend Development
```bash
# Build for production (tested ✅)
npm run build

# Install dependencies
npm install

# Development server
npm run dev
```

#### Docker Operations (Tested)
```bash
# Build container with no cache (tested ✅)
docker-compose build --no-cache

# Start services (tested ✅)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

#### Backend Development
```bash
# Install Python dependencies
pip install -r requirements.txt

# Run FastAPI development server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Current Service URLs
- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health
- **WebSocket**: ws://localhost:8000/ws

### Key Files & Directories
```
/Users/matt/PycharmProjects/PyScheduler/
├── backend/                 # Python FastAPI backend
├── frontend/               # Vue.js 3 frontend
├── docker/                 # Docker configuration files
├── data/                   # SQLite database and script storage
├── docker-compose.yml      # Container orchestration
├── Dockerfile             # Container definition
└── CLAUDE.md              # This documentation file
```

### Testing Status
- **Manual Testing**: All core features tested and working
- **URL Triggers**: Tested with safe_name format
- **Script Creation**: Simplified modal working correctly
- **Trigger Management**: CRON and interval triggers functional
- **Docker Deployment**: Successfully rebuilt and running

### Known Working Features
- ✅ Script creation with safe name generation
- ✅ Virtual environment isolation
- ✅ CRON expression validation and scheduling
- ✅ Interval scheduling with time unit selection
- ✅ Manual script execution
- ✅ URL-based script triggering with API keys
- ✅ Real-time WebSocket communication
- ✅ Responsive UI with dark/light theme support
- ✅ Container deployment with health checks

### Next Development Phase
Currently focused on **Phase 2: Enhanced logging and monitoring features**
- Real-time log streaming improvements
- Advanced search and filtering capabilities
- Resource monitoring (CPU, memory usage)
- Enhanced error reporting and notifications