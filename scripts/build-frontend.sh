#!/bin/bash

# Build PyScheduler Frontend for Production
echo "Building PyScheduler frontend for production..."

# Change to frontend directory
cd frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
fi

# Build frontend
echo "Building frontend..."
npm run build

# Check if build was successful
if [ -d "dist" ]; then
    echo "Frontend build completed successfully!"
    echo "Output directory: frontend/dist"
else
    echo "Frontend build failed!"
    exit 1
fi