#!/bin/bash

# Docker Container Rebuild Script
# This script rebuilds your Docker container with a clean cache

set -e  # Exit on any error

echo "🔄 Starting Docker container rebuild process..."
echo "=============================================="

# Step 1: Stop Container
echo "📦 Step 1: Stopping Docker containers..."
docker-compose down
echo "✅ Containers stopped"

# Step 2: Clear Frontend Build
echo "🗑️  Step 2: Clearing frontend build directory..."
rm -rf dist/*
echo "✅ Frontend build cleared"

# Step 3: Rebuild Frontend
echo "🔨 Step 3: Rebuilding frontend..."
cd frontend && npm run build
echo "✅ Frontend rebuilt"

# Step 4: Rebuild Docker with No Cache
echo "🐳 Step 4: Rebuilding Docker images (no cache)..."
docker-compose build --no-cache
echo "✅ Docker images rebuilt"

# Step 5: Start Container
echo "🚀 Step 5: Starting containers..."
docker-compose up -d
echo "✅ Containers started"

echo "=============================================="
echo "🎉 Rebuild process completed successfully!"
echo "Your containers are now running with fresh builds."

# Optional: Show running containers
echo ""
echo "📋 Currently running containers:"
docker-compose ps