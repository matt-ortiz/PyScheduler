#!/bin/bash

# Start PyScheduler Backend Development Server
echo "Starting PyScheduler backend development server..."

# Activate virtual environment
source venv/bin/activate

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Start FastAPI with hot reload
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload