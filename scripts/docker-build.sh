#!/bin/bash

# Build and run PyScheduler with Docker
echo "Building and running PyScheduler with Docker..."

# Build frontend first
echo "Building frontend..."
./scripts/build-frontend.sh

# Build Docker image
echo "Building Docker image..."
docker build -t pyscheduler:latest .

# Check if image was built successfully
if [ $? -eq 0 ]; then
    echo "Docker image built successfully!"
    echo "To run with Docker Compose: docker-compose up -d"
    echo "To run directly: docker run -p 8000:8000 -v pyscheduler_data:/data pyscheduler:latest"
else
    echo "Docker image build failed!"
    exit 1
fi