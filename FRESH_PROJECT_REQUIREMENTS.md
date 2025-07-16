# Tempo - Python Script Scheduler & Monitor

## Project Vision

**Tempo** is a web-based Python script scheduling and monitoring platform that solves the common problem of running Python scripts on a schedule while providing proper dependency isolation, real-time monitoring, and comprehensive logging.

## The Problem We're Solving

### Current Pain Points
- **Cron Jobs Are Limited** - Basic cron scheduling lacks monitoring, logging, and dependency management
- **Dependency Conflicts** - Scripts interfere with each other's Python packages
- **Poor Visibility** - No way to see what scripts are doing in real-time
- **Manual Management** - Editing crontab files and managing multiple scripts is tedious
- **Debugging Difficulties** - Hard to troubleshoot when scripts fail
- **No History** - Difficult to track execution patterns and success rates

### Our Solution
A **personal Python script scheduler** with a web interface that provides:
- **Easy Scheduling** - Visual interface for setting up CRON and interval schedules
- **Isolated Environments** - Each script runs in its own Python virtual environment
- **Real-time Monitoring** - Watch scripts execute live with instant output
- **Comprehensive Logging** - Complete execution history with success/failure tracking
- **Simple Management** - Web-based script creation, editing, and organization

## Target Users

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

## Script Creation Workflow

### Simple Creation Process
The script creation process should be **minimal and fast** to encourage users to create scripts:

1. **Create Script Dialog** - User clicks "New Script" button
   - **Script Name** - Enter display name (e.g., "Hello World", "Data Backup")
   - **Folder** - Optional folder selection for organization
   - **Create Button** - Creates script immediately

2. **Automatic Setup** - System automatically:
   - **Generates Safe Name** - Converts "Hello World" to "hello-world" for filesystem
   - **Creates Virtual Environment** - Sets up isolated Python environment
   - **Creates Directory Structure** - Organized file structure
   - **Opens Script Editor** - User can immediately start coding

3. **Script Configuration Page** - After creation, user can configure:
   - **Script Content** - Python code editor with syntax highlighting
   - **Requirements** - Pip packages needed (requirements.txt editor)
   - **Scheduling** - When to run the script (CRON, intervals, manual)
   - **Notifications** - Email settings for success/failure alerts
   - **Advanced Options** - Python version, resource limits, etc.

### Safe Name Generation Rules
- **Lowercase** - Convert to lowercase letters
- **Replace Spaces** - Spaces become hyphens (-)
- **Remove Special Characters** - Keep only letters, numbers, hyphens
- **Ensure Uniqueness** - Add suffix if name exists (hello-world-2)
- **Examples**:
  - "Hello World" → "hello-world"
  - "Data Backup Script!" → "data-backup-script"
  - "API Call #1" → "api-call-1"

## Core Features

### 1. Script Management
- **Simple Script Creation** - Quick dialog asking only for script name and optional folder
- **Safe Name Generation** - Convert script names to safe filesystem names (e.g., "Hello World" → "hello-world")
- **Web-based Code Editor** - Write and edit Python scripts in the browser after creation
- **Script Organization** - Simple folder structure for organizing multiple scripts
- **Script Templates** - Pre-built templates for common use cases
- **Version History** - Track changes to scripts over time
- **Import/Export** - Backup and restore scripts easily
- **Auto-save** - Automatic saving of script changes to prevent data loss

### 2. Dependency Management
- **Virtual Environments** - Each script gets its own isolated Python environment
- **Requirements Management** - Visual editor for pip requirements.txt files
- **Dependency Installation** - Automatic package installation with progress tracking
- **Python Version Selection** - Support for multiple Python versions (3.8-3.12)
- **Environment Health Checks** - Verify environments are working correctly

### 3. Scheduling System
- **Multiple Trigger Types**:
  - **Interval Scheduling** - Run every X seconds/minutes/hours
  - **CRON Expressions** - Full cron syntax with validation
  - **Manual Execution** - On-demand script running
  - **Startup Triggers** - Run scripts when the system starts
- **Visual CRON Builder** - Easy-to-use interface for creating CRON expressions
- **Schedule Preview** - See upcoming execution times
- **Timezone Support** - Proper handling of different timezones

### 4. Real-time Monitoring
- **Live Output Streaming** - Watch script execution in real-time
- **Execution Status** - Running, completed, failed, and queued indicators
- **Progress Tracking** - See how long scripts have been running
- **Resource Monitoring** - Track CPU and memory usage during execution
- **Multiple Concurrent Executions** - Handle multiple scripts running simultaneously

### 5. Logging & History
- **Execution Logs** - Complete stdout/stderr capture for every run
- **Execution History** - Track all script runs with timestamps and results
- **Success/Failure Tracking** - Monitor script reliability over time
- **Log Search** - Find specific log entries quickly
- **Log Retention** - Automatic cleanup of old logs with configurable retention

### 6. User Interface
- **Modern Web Interface** - Clean, responsive design that works on all devices
- **Dark/Light Themes** - User preference for interface appearance
- **Real-time Updates** - Live updates without page refreshes
- **Mobile Friendly** - Works well on tablets and phones
- **Keyboard Shortcuts** - Efficient navigation for power users

### 7. Remote Execution & API
- **Secure URL Triggers** - Execute scripts via authenticated GET/POST requests
- **API Key Management** - Secure remote access with mandatory authentication
- **Rate Limiting** - Protection against abuse and overload
- **RESTful API** - Full API access for automation and integration
- **Per-script URL Controls** - Individual scripts can enable/disable URL triggers

### 8. Security & Resource Management
- **Script Validation** - Python syntax checking and basic security scanning
- **Resource Limits** - Configurable timeout, memory, and CPU limits per script
- **Execution Isolation** - Scripts run in sandboxed virtual environments
- **Input Sanitization** - Comprehensive validation of all user inputs
- **Secure Auto-save** - Real-time saving with security validation

### 9. Notifications (Optional)
- **Email Notifications** - Get notified when scripts succeed or fail
- **Per-Script Configuration** - Choose which scripts send notifications
- **Custom Recipients** - Send notifications to multiple email addresses
- **SMTP2GO Integration** - Built-in support for SMTP2GO email service

## Technical Requirements

### Performance
- **Fast Response Times** - Sub-second page loads and API responses
- **Efficient Execution** - Minimal overhead for script execution
- **Concurrent Processing** - Handle multiple scripts running simultaneously
- **Resource Management** - Prevent scripts from consuming excessive resources

### Reliability
- **High Uptime** - System should be available 99%+ of the time
- **Error Recovery** - Graceful handling of failures and automatic recovery
- **Data Persistence** - Never lose scripts or execution history
- **Backup Support** - Easy backup and restore of all data

### Security
- **Isolated Execution** - Scripts run in sandboxed environments with resource limits
- **Strong Authentication** - Secure login system and API key management
- **Input Validation** - Comprehensive validation and sanitization
- **Rate Limiting** - Protection against abuse and DoS attacks
- **Secure Defaults** - Safe configuration out of the box

### Scalability
- **Support for 100+ Scripts** - Handle moderate script collections
- **10,000+ Execution Logs** - Efficient storage and retrieval of history
- **Multiple Concurrent Users** - Support for small teams
- **Resource Limits** - Configurable limits to prevent system overload

## Technology Stack

### Backend
- **Python 3.12** - Modern Python with excellent performance
- **FastAPI** - High-performance web framework with automatic documentation
- **SQLite** - Simple, reliable database with no external dependencies
- **Celery + Redis** - Task queue for background script execution
- **WebSocket** - Real-time communication for live updates
- **SlowAPI** - Rate limiting middleware for API protection

### Frontend
- **Vue.js 3** - Modern JavaScript framework with excellent performance
- **Vite** - Fast development and build tool
- **Tailwind CSS** - Utility-first CSS framework for rapid development
- **TypeScript** - Type safety for better code quality
- **WebSocket** - Real-time communication with the backend

### Infrastructure
- **Docker** - Containerized deployment for easy setup
- **Single Container** - All services in one container for simplicity
- **File-based Storage** - Scripts and environments stored on disk
- **Automatic Backup** - Built-in backup functionality

## Deployment Targets

### Primary Deployment
- **Home Servers** - UnRaid, Synology, and similar NAS systems
- **Docker Environment** - Single container with docker-compose
- **Local Development** - Quick setup for testing and development

### System Requirements
- **CPU** - 1+ cores (2+ recommended)
- **RAM** - 512MB minimum (1GB+ recommended)
- **Storage** - 1GB+ for application and scripts
- **Network** - Local network access for web interface

## Feature Priorities

### Phase 1: Core Functionality (Must Have)
- ✅ Simple script creation workflow (name + folder only)
- ✅ Safe name generation and filesystem organization
- ✅ Script editing and content management
- ✅ Virtual environment management
- ✅ Basic scheduling (intervals and CRON)
- ✅ Script execution with logging
- ✅ Web interface for management
- ✅ Real-time output streaming
- ✅ Security enhancements (validation, rate limiting, resource limits)

### Phase 2: Enhanced Features (Should Have)
- ✅ Script organization (folders)
- ✅ Better code editor with syntax highlighting
- ✅ Email notifications
- ✅ Execution statistics and history
- ✅ CRON expression builder
- ✅ Import/export functionality
- ✅ Secure API access with URL triggers
- ✅ Auto-save functionality

### Phase 3: Polish Features (Nice to Have)
- ✅ Dark/light theme toggle
- ✅ Advanced log search and filtering
- ✅ Mobile-optimized interface
- ✅ Keyboard shortcuts
- ✅ Performance monitoring
- ✅ API key management interface

## Success Criteria

### User Experience
- **Quick Setup** - Users can create and schedule their first script within 5 minutes
- **Intuitive Interface** - New users can navigate without documentation
- **Reliable Execution** - Scripts run on schedule 99%+ of the time
- **Fast Debugging** - Users can quickly identify and fix script issues

### Technical Metrics
- **Response Time** - API responses under 200ms
- **Memory Usage** - Base system uses less than 100MB RAM
- **Startup Time** - Container starts in under 30 seconds
- **Storage Efficiency** - Minimal disk space usage for the application

### Adoption Goals
- **Easy Installation** - One-command deployment on UnRaid/Synology
- **Active Usage** - Users schedule multiple scripts and use regularly
- **Community Feedback** - Positive user reviews and feature requests
- **Reliability** - Zero data loss or corruption reports

## What We're NOT Building

### Excluded Features
- ❌ Complex user management with roles and permissions
- ❌ Advanced analytics and reporting dashboards
- ❌ Multi-tenancy or SaaS features
- ❌ Complex workflow management with dependencies
- ❌ Advanced integrations with external services
- ❌ Horizontal scaling and clustering
- ❌ Advanced security features (MFA, SSO, etc.)
- ❌ Support for non-Python scripting languages

### Why These Are Excluded
- **Complexity** - They significantly increase development and maintenance effort
- **Target Audience** - Our users don't need enterprise-level features
- **Simplicity Goal** - We want to keep the system easy to understand and use
- **Resource Constraints** - Focus on core value rather than feature breadth

## Development Timeline

### Phase 1: Foundation (4 weeks)
- **Week 1**: Project setup, database schema, basic FastAPI backend
- **Week 2**: Script management API, virtual environment handling
- **Week 3**: Vue.js frontend, basic script management interface
- **Week 4**: Scheduling system, task queue integration

### Phase 2: Core Features (4 weeks)
- **Week 5**: Real-time execution monitoring, WebSocket integration
- **Week 6**: Logging system, execution history, basic UI polish
- **Week 7**: Email notifications, script organization (folders)
- **Week 8**: Security enhancements, API features, testing, documentation

### Total Timeline: 8 weeks

## Deployment Strategy

### Development
- **Local Development** - Docker Compose setup with hot reload
- **Testing Environment** - Automated testing with sample scripts
- **Documentation** - User guide and API documentation

### Production
- **Docker Image** - Single container with all dependencies
- **UnRaid Template** - Community Applications template
- **Synology Package** - Container Manager configuration
- **Documentation** - Installation and configuration guides

## Configuration

### Environment Variables
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

volumes:
  pysched_data:
```

## Conclusion

Tempo addresses a real need for individual developers and small teams who want to schedule Python scripts without the complexity of enterprise workflow systems. By focusing on simplicity, reliability, and ease of use, we can create a tool that solves the specific problem of Python script scheduling while providing modern conveniences like real-time monitoring and proper dependency management.

The key to success is maintaining focus on the core value proposition: **making it easy to schedule and monitor Python scripts securely and reliably**. Every feature should directly support this goal without adding unnecessary complexity.

---

**Document Version**: 1.1  
**Created**: 2025-01-11  
**Updated**: 2025-01-14  
**Purpose**: Enhanced project requirements for Tempo with security and resource management improvements