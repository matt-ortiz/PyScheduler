# PyScheduler

A web-based Python script scheduling and monitoring platform that provides simple scheduling, dependency isolation, real-time monitoring, and comprehensive logging.

## Features

- **Easy Script Management** - Create, edit, and organize Python scripts through a web interface
- **Safe Name Generation** - Automatically converts script names to filesystem-safe names
- **Virtual Environment Isolation** - Each script runs in its own Python virtual environment
- **Flexible Scheduling** - Support for CRON expressions, intervals, and manual execution
- **Real-time Monitoring** - Watch scripts execute live with WebSocket updates
- **Comprehensive Logging** - Complete execution history with success/failure tracking
- **Email Notifications** - Get notified when scripts succeed or fail
- **Secure API Access** - URL triggers with API key authentication
- **Dark/Light Themes** - Modern, responsive web interface

## Quick Start

### Option 1: Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd PyScheduler
   ```

2. **Build and run with Docker Compose**
   ```bash
   # Build frontend and Docker image
   ./scripts/docker-build.sh
   
   # Start with Docker Compose
   docker-compose up -d
   ```

3. **Access the application**
   - Web Interface: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Option 2: Development Setup

1. **Prerequisites**
   - Python 3.12
   - Node.js 16+
   - Redis server

2. **Setup development environment**
   ```bash
   # Run setup script
   ./scripts/dev-setup.sh
   
   # Start Redis server
   redis-server
   
   # Start all services
   ./scripts/dev-all.sh
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Default Credentials

- **Username**: admin
- **Password**: admin

*Please change these credentials after first login*

## Environment Variables

### Basic Configuration
- `PYSCHED_DATA_PATH` - Data directory path (default: `/data`)
- `PYSCHED_SECRET_KEY` - JWT secret key (required in production)
- `PYSCHED_DEBUG` - Enable debug mode (default: `false`)

### Security Settings
- `PYSCHED_DEFAULT_API_KEY` - Default API key for URL triggers
- `PYSCHED_RATE_LIMIT_ENABLED` - Enable rate limiting (default: `true`)
- `PYSCHED_DEFAULT_SCRIPT_TIMEOUT` - Default script timeout in seconds (default: `300`)
- `PYSCHED_DEFAULT_MEMORY_LIMIT` - Default memory limit in MB (default: `512`)

### Email Settings (Optional)
- `SMTP_SERVER` - SMTP server hostname
- `SMTP_PORT` - SMTP server port (default: `2525`)
- `SMTP_USERNAME` - SMTP username
- `SMTP_PASSWORD` - SMTP password
- `FROM_EMAIL` - From email address

## Usage

### Creating Scripts

1. Click "New Script" on the dashboard
2. Enter script name and optional folder
3. The system automatically generates a safe filesystem name
4. Edit your Python code in the built-in editor
5. Configure requirements, environment variables, and notifications
6. Save and run your script

### Scheduling Scripts

Scripts can be executed in several ways:

- **Manual**: Click "Run" button in the interface
- **URL Trigger**: GET `/api/scripts/{script_id}/trigger?api_key=YOUR_API_KEY`
- **Intervals**: Set up recurring execution every X seconds/minutes/hours
- **CRON**: Use standard CRON expressions for complex scheduling

### Monitoring

- **Real-time Updates**: WebSocket connection provides live execution status
- **Execution History**: Complete log of all script runs with output
- **Success/Failure Tracking**: Monitor script reliability over time
- **Resource Usage**: Track CPU and memory usage during execution

## Architecture

### Backend (Python)
- **FastAPI** - REST API and WebSocket server
- **SQLite** - Database for metadata storage
- **Celery + Redis** - Background task queue for script execution
- **Virtual Environments** - Isolated Python environments per script

### Frontend (JavaScript)
- **Vue.js 3** - Modern reactive web interface
- **Vite** - Fast development and build tool
- **Tailwind CSS** - Utility-first styling
- **WebSocket** - Real-time updates

### Database Schema
- `scripts` - Script metadata with display and safe names
- `folders` - Simple organization structure
- `triggers` - Scheduling configuration
- `execution_logs` - Complete execution history
- `users` - Basic authentication
- `settings` - Application configuration

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `GET /api/auth/me` - Current user info

### Scripts
- `GET /api/scripts` - List all scripts
- `POST /api/scripts` - Create new script
- `GET /api/scripts/{id}` - Get script details
- `PUT /api/scripts/{id}` - Update script
- `DELETE /api/scripts/{id}` - Delete script
- `POST /api/scripts/{id}/execute` - Execute script manually
- `GET /api/scripts/{id}/trigger` - URL trigger execution

### Logs
- `GET /api/logs` - List execution logs
- `GET /api/logs/{id}` - Get specific log
- `GET /api/logs/script/{script_id}` - Get logs for script

### Folders
- `GET /api/folders` - List folders
- `POST /api/folders` - Create folder
- `PUT /api/folders/{id}` - Update folder
- `DELETE /api/folders/{id}` - Delete folder

## Development

### Project Structure
```
PyScheduler/
├── backend/              # Python FastAPI backend
│   ├── api/             # API endpoints
│   ├── models.py        # Pydantic models
│   ├── database.py      # SQLite database
│   ├── auth.py          # Authentication
│   ├── tasks.py         # Celery tasks
│   └── main.py          # FastAPI app
├── frontend/            # Vue.js frontend
│   ├── src/
│   │   ├── components/  # Vue components
│   │   ├── views/       # Page views
│   │   ├── stores/      # Pinia stores
│   │   └── router/      # Vue Router
│   └── package.json
├── docker/              # Docker configuration
├── scripts/             # Development scripts
└── data/               # Runtime data
```

### Development Commands

```bash
# Setup development environment
./scripts/dev-setup.sh

# Start individual services
./scripts/dev-backend.sh    # FastAPI backend
./scripts/dev-frontend.sh   # Vue.js frontend
./scripts/dev-celery.sh     # Celery worker

# Start all services
./scripts/dev-all.sh

# Build frontend for production
./scripts/build-frontend.sh

# Build Docker image
./scripts/docker-build.sh
```

### Testing

```bash
# Run backend tests
source venv/bin/activate
python -m pytest

# Run frontend tests
cd frontend
npm test
```

## Security Features

- **Input Validation** - Comprehensive validation of all user inputs
- **Python Syntax Checking** - Validates Python code before execution
- **Resource Limits** - Configurable timeout, memory, and CPU limits
- **Rate Limiting** - Protection against API abuse
- **Authentication** - JWT-based user authentication
- **Isolated Execution** - Scripts run in sandboxed virtual environments

## Deployment

### Docker Compose (Recommended)
```bash
# Clone repository
git clone <repository-url>
cd PyScheduler

# Configure environment variables
cp .env.example .env
# Edit .env with your settings

# Build and start
./scripts/docker-build.sh
docker-compose up -d
```

### Manual Installation
1. Install Python 3.12, Node.js, and Redis
2. Run setup script: `./scripts/dev-setup.sh`
3. Configure environment variables
4. Start all services: `./scripts/dev-all.sh`

## Backup and Restore

The application stores all data in the `/data` directory:
- `pyscheduler.db` - SQLite database
- `scripts/` - Script files and virtual environments
- `logs/` - Application logs

To backup: `tar -czf pyscheduler-backup.tar.gz /data`
To restore: `tar -xzf pyscheduler-backup.tar.gz`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- GitHub Issues: [Create an issue]
- Documentation: Check the `/docs` endpoint when running
- API Documentation: Available at `/docs` when running

## Roadmap

- [ ] Advanced scheduling with dependencies
- [ ] Multi-user support with roles
- [ ] Script templates and sharing
- [ ] Performance analytics dashboard
- [ ] Integration with external services
- [ ] Advanced monitoring and alerting