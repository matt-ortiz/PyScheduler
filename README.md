# PyScheduler

A web-based Python script scheduling and monitoring platform that solves the common problem of running Python scripts on a schedule while providing proper dependency isolation, real-time monitoring, and comprehensive logging.

[![Docker Pulls](https://img.shields.io/docker/pulls/mattortiz/pyscheduler)](https://hub.docker.com/r/mattortiz/pyscheduler)
[![GitHub](https://img.shields.io/github/license/matt-ortiz/PyScheduler)](https://github.com/matt-ortiz/PyScheduler/blob/main/LICENSE)

## 🚀 Quick Start

```bash
# Create a docker-compose.yml file
curl -O https://raw.githubusercontent.com/matt-ortiz/PyScheduler/main/docker-compose.yml

# Start PyScheduler
docker-compose up -d

# Access the web interface
open http://localhost:8000
```

**Default Login:**
- Username: `admin`
- Password: Check container logs for generated secure password
- Email: `admin@localhost`

```bash
# View the generated admin password
docker-compose logs pyscheduler | grep "Generated secure admin password"
```

## ✨ Key Features

- **🎯 Simple Script Creation** - Quick dialog asking only for script name and optional folder
- **🔒 Virtual Environment Isolation** - Each script runs in its own Python virtual environment
- **📊 Real-time Monitoring** - Live script execution monitoring via WebSocket
- **⏰ Multiple Scheduling Types** - CRON expressions, intervals, manual execution, and startup triggers
- **📁 Script Organization** - Simple folder structure for organizing multiple scripts
- **📧 Email Notifications** - Get notified when scripts succeed or fail
- **🔐 Secure API Access** - URL triggers with API key authentication and rate limiting
- **💾 Auto-save Functionality** - Real-time saving of script changes to prevent data loss
- **🛡️ Security Features** - Python syntax validation, resource limits, and input sanitization
- **🌐 Modern UI** - Dark/light themes, mobile-friendly, real-time updates

## 📖 Use Cases

- **Data Processing** - Regular ETL jobs and data transformations
- **System Maintenance** - Cleanup scripts, log rotation, and health checks
- **Development Workflows** - Automated testing, builds, and deployments
- **Personal Automation** - Any recurring Python task that needs scheduling
- **Monitoring & Alerts** - Scripts that check systems and send notifications

## 🐳 Docker Deployment

### Basic Setup

```yaml
services:
  pyscheduler:
    image: mattortiz/pyscheduler:latest
    ports:
      - "8000:8000"
    volumes:
      - pyscheduler_data:/data
      - pyscheduler_logs:/var/log
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

volumes:
  pyscheduler_data:
  pyscheduler_logs:
```

### Advanced Configuration

```yaml
services:
  pyscheduler:
    image: mattortiz/pyscheduler:latest
    ports:
      - "8000:8000"
    environment:
      # Core Settings
      - PYSCHED_DATA_PATH=/data
      - PYSCHED_SECRET_KEY=your-secret-key-change-me-in-production
      
      # Admin User Settings (customize for your deployment)
      - PYSCHED_ADMIN_USERNAME=admin
      - PYSCHED_ADMIN_PASSWORD=your-secure-password-here
      - PYSCHED_ADMIN_EMAIL=admin@yourdomain.com
      
      # Email Settings (Optional - only if not using database configuration)
      - SMTP_SERVER=mail.smtp2go.com
      - SMTP_PORT=2525
      - SMTP_USERNAME=your-username
      - SMTP_PASSWORD=your-password
      - FROM_EMAIL=pyscheduler@yourdomain.com
    volumes:
      - pyscheduler_data:/data
      - pyscheduler_logs:/var/log
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

volumes:
  pyscheduler_data:
  pyscheduler_logs:
```

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PYSCHED_DATA_PATH` | `/data` | Data directory path |
| `PYSCHED_SECRET_KEY` | `your-secret-key-change-me-in-production` | JWT secret key |
| `PYSCHED_ADMIN_USERNAME` | `admin` | Initial admin username |
| `PYSCHED_ADMIN_PASSWORD` | *random generated* | Initial admin password |
| `PYSCHED_ADMIN_EMAIL` | `admin@localhost` | Initial admin email |
| `SMTP_SERVER` | - | SMTP server hostname |
| `SMTP_PORT` | `2525` | SMTP server port |
| `SMTP_USERNAME` | - | SMTP username |
| `SMTP_PASSWORD` | - | SMTP password |
| `FROM_EMAIL` | - | Email sender address |

### Volumes

| Volume | Description |
|--------|-------------|
| `/data` | SQLite database and script storage |
| `/var/log` | Application and service logs |

## 🔧 API Access

PyScheduler provides a REST API for automation:

```bash
# Execute a script via URL trigger
curl "http://localhost:8000/api/scripts/my-script/trigger?api_key=your-api-key"

# Get script execution history
curl "http://localhost:8000/api/logs/1" \
  -H "Authorization: Bearer your-jwt-token"
```

**API Documentation:** Available at `http://localhost:8000/docs`

## 🛡️ Security Features

- **Secure Defaults** - Auto-generated admin passwords, secure session management
- **Virtual Environment Isolation** - Each script runs in its own Python environment
- **Input Validation** - Comprehensive validation of all user inputs
- **Rate Limiting** - Protection against API abuse
- **Resource Limits** - Configurable timeout and memory limits per script
- **API Key Authentication** - Secure remote script execution

## 📊 Monitoring & Logging

- **Real-time Execution Monitoring** - Live script output streaming
- **Complete Execution History** - Search and filter past executions
- **Email Notifications** - Configurable alerts for script success/failure
- **Health Check Endpoint** - `/api/health` for monitoring systems
- **WebSocket Support** - Real-time updates without page refresh

## 🏗️ Architecture

- **Single Container** - All services in one container for simplicity
- **SQLite Database** - No external database dependencies
- **FastAPI Backend** - High-performance Python web framework
- **Vue.js Frontend** - Modern, responsive web interface
- **Celery + Redis** - Background task processing
- **Nginx** - Static file serving and reverse proxy

## 🔄 Backup & Recovery

```bash
# Backup your data
docker cp pyscheduler_pyscheduler_1:/data ./backup-$(date +%Y%m%d)

# Restore from backup
docker cp ./backup-20240101 pyscheduler_pyscheduler_1:/data
```

## 🐛 Troubleshooting

### Common Issues

**Container won't start:**
```bash
# Check logs
docker-compose logs pyscheduler

# Verify health
curl http://localhost:8000/api/health
```

**Can't find admin password:**
```bash
# Look for generated password in logs
docker-compose logs pyscheduler | grep "Generated secure admin password"
```

**Scripts fail to execute:**
- Check script syntax in the editor
- Verify Python requirements are properly specified
- Review execution logs in the web interface

### Support

- **Documentation:** Full documentation available in the web interface
- **Issues:** Report bugs and feature requests on GitHub
- **API Reference:** Interactive API docs at `/docs`

## 🚀 Development

### Local Development Setup

```bash
# Clone repository
git clone https://github.com/matt-ortiz/PyScheduler.git
cd PyScheduler

# Install dependencies
pip install -r requirements.txt
cd frontend && npm install && cd ..

# Start development environment
./scripts/dev-all.sh
```

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

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

**Made with ❤️ for Python automation**