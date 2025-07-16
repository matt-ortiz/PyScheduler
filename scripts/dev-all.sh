#!/bin/bash

# Start all Tempo development services
echo "Starting all Tempo development services..."

# Check if Redis is running
if ! pgrep -x "redis-server" > /dev/null; then
    echo "Redis is not running. Please start Redis first:"
    echo "redis-server"
    exit 1
fi

# Start backend in background
echo "Starting backend..."
./scripts/dev-backend.sh &
BACKEND_PID=$!

# Start frontend in background
echo "Starting frontend..."
./scripts/dev-frontend.sh &
FRONTEND_PID=$!

# Start Celery in background
echo "Starting Celery..."
./scripts/dev-celery.sh &
CELERY_PID=$!

# Handle shutdown
trap 'kill $BACKEND_PID $FRONTEND_PID $CELERY_PID' INT TERM

echo "All services started!"
echo "- Backend: http://localhost:8000"
echo "- Frontend: http://localhost:3000"
echo "- API Documentation: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for all processes
wait $BACKEND_PID $FRONTEND_PID $CELERY_PID