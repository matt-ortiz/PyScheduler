#!/bin/bash
set -e

echo "Starting PyScheduler (Simple Mode)..."

# Create necessary directories
mkdir -p /data/scripts /data/logs /data/backups
mkdir -p /var/log/nginx /var/lib/nginx
mkdir -p /var/log/supervisor

# Set proper permissions
chown -R www-data:www-data /data
chmod -R 755 /data

# Initialize database
echo "Initializing database..."
cd /app
export PYTHONPATH="/app"
python -c "from backend.database import init_database; init_database()"

# Start Redis in background
echo "Starting Redis..."
redis-server --daemonize yes --bind 127.0.0.1

# Wait for Redis to start
echo "Waiting for Redis to start..."
sleep 3

# Start FastAPI directly on port 8000
echo "Starting FastAPI..."
exec python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload