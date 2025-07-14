#!/bin/bash

# Start PyScheduler Celery Worker and Beat
echo "Starting PyScheduler Celery worker and beat..."

# Activate virtual environment
source venv/bin/activate

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Start Celery worker in background
echo "Starting Celery worker..."
celery -A backend.tasks worker --loglevel=info --concurrency=2 &
WORKER_PID=$!

# Start Celery beat in background
echo "Starting Celery beat..."
celery -A backend.tasks beat --loglevel=info &
BEAT_PID=$!

# Handle shutdown
trap 'kill $WORKER_PID $BEAT_PID' INT TERM

# Wait for processes
wait $WORKER_PID $BEAT_PID