#!/bin/bash

# PyScheduler Development Setup Script
echo "Setting up PyScheduler development environment..."

# Check if Python 3.12 is available
if ! command -v python3.12 &> /dev/null; then
    echo "Python 3.12 is required but not installed. Please install Python 3.12 first."
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "Node.js is required but not installed. Please install Node.js first."
    exit 1
fi

# Create virtual environment for backend
echo "Creating Python virtual environment..."
python3.12 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install Node.js dependencies for frontend
echo "Installing Node.js dependencies..."
cd frontend
npm install
cd ..

# Create data directories
echo "Creating data directories..."
mkdir -p data/scripts data/logs data/backups

# Initialize database
echo "Initializing database..."
python -c "from backend.database import init_database; init_database()"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << EOL
# PyScheduler Environment Variables
PYSCHED_DATA_PATH=./data
PYSCHED_SECRET_KEY=dev-secret-key-change-in-production
PYSCHED_DEBUG=true
PYSCHED_DEFAULT_API_KEY=dev-api-key-change-in-production
PYSCHED_RATE_LIMIT_ENABLED=false

# Email Settings (Optional)
SMTP_SERVER=
SMTP_PORT=2525
SMTP_USERNAME=
SMTP_PASSWORD=
FROM_EMAIL=pyscheduler@localhost

# Redis Settings
REDIS_URL=redis://localhost:6379/0
EOL
fi

echo "Development environment setup complete!"
echo ""
echo "To start development:"
echo "1. Start Redis server: redis-server"
echo "2. Start backend: ./scripts/dev-backend.sh"
echo "3. Start frontend: ./scripts/dev-frontend.sh"
echo "4. Start Celery worker: ./scripts/dev-celery.sh"
echo ""
echo "Or use: ./scripts/dev-all.sh to start all services"