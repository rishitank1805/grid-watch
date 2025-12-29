#!/bin/bash
# Script to submit Flink job

set -e

echo "Checking Flink container status..."

# Check if containers are running
if ! docker-compose ps | grep -q "flink-jobmanager.*Up"; then
    echo "Error: Flink containers are not running."
    echo "Please start them with: docker-compose up -d"
    exit 1
fi

# Get the actual container name (Docker Compose may prefix with project name)
CONTAINER_NAME=$(docker-compose ps -q flink-jobmanager)

if [ -z "$CONTAINER_NAME" ]; then
    echo "Error: Could not find flink-jobmanager container"
    echo "Available containers:"
    docker-compose ps
    exit 1
fi

echo "Found Flink container: $CONTAINER_NAME"

# Note: flink_job is already mounted as volume, so we only need to copy config
echo "Copying config directory to Flink container..."
docker cp config "$CONTAINER_NAME:/opt/flink/usrlib/"

echo "Submitting Flink job..."
# Verify volumes are mounted
if ! docker-compose exec flink-jobmanager test -d /opt/flink/usrlib/flink_job; then
    echo "ERROR: flink_job directory not found at /opt/flink/usrlib/flink_job"
    echo "Checking volume mounts..."
    docker-compose exec flink-jobmanager ls -la /opt/flink/usrlib/ 2>&1 || true
    exit 1
fi

# Submit PyFlink job with Kafka connector and client JARs
# -pyfs: Python filesystem (includes Python modules) - use absolute path
# -py: Python main file
# -j: JAR files for Kafka connector and client (use multiple -j flags)
if docker-compose exec flink-jobmanager test -f /opt/flink/lib/flink-connector-kafka-1.18.0.jar && \
   docker-compose exec flink-jobmanager test -f /opt/flink/lib/kafka-clients.jar; then
    # Use -pyfs with the full path to the directory containing the Python files
    docker-compose exec flink-jobmanager flink run \
      -j /opt/flink/lib/flink-connector-kafka-1.18.0.jar \
      -j /opt/flink/lib/kafka-clients.jar \
      -pyfs file:///opt/flink/usrlib/flink_job \
      -py /opt/flink/usrlib/flink_job/main.py
else
    echo "ERROR: Required Kafka JARs not found."
    echo "Please ensure both JARs are in libs/ directory and rebuild the Flink image:"
    echo "  - flink-connector-kafka-1.18.0.jar"
    echo "  - kafka-clients.jar"
    echo "See SETUP_KAFKA_CONNECTOR.md for instructions."
    exit 1
fi

echo "Job submitted! Check Flink UI at http://localhost:8081"

