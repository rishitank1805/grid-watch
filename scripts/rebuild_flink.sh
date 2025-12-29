#!/bin/bash
# Script to rebuild Flink containers with updated dependencies

set -e

echo "Rebuilding Flink containers..."
echo "This will install PyFlink and PyYAML in the containers."

# Stop existing containers
echo "Stopping Flink containers..."
docker-compose stop flink-jobmanager flink-taskmanager

# Remove old containers
echo "Removing old containers..."
docker-compose rm -f flink-jobmanager flink-taskmanager

# Rebuild the images
echo "Rebuilding Flink images (this may take a few minutes)..."
docker-compose build --no-cache flink-jobmanager flink-taskmanager

# Start the containers
echo "Starting Flink containers..."
docker-compose up -d flink-jobmanager flink-taskmanager

echo ""
echo "Flink containers rebuilt and started!"
echo "Wait about 30 seconds for them to be ready, then submit the job:"
echo "  ./scripts/submit_flink_job.sh"

