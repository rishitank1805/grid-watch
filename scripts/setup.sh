#!/bin/bash
# Setup script for grid-watch project

set -e

echo "Setting up Grid-Watch project..."

# Create data directory if it doesn't exist
mkdir -p data

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Start services
echo "Starting Docker services..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Create Kafka topics
echo "Creating Kafka topics..."
docker-compose exec -T kafka kafka-topics --create --topic smartmeter_raw --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 --if-not-exists || true
docker-compose exec -T kafka kafka-topics --create --topic smartmeter_validated --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 --if-not-exists || true
docker-compose exec -T kafka kafka-topics --create --topic smartmeter_gap_alerts --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 --if-not-exists || true
docker-compose exec -T kafka kafka-topics --create --topic smartmeter_late_events --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 --if-not-exists || true
docker-compose exec -T kafka kafka-topics --create --topic smartmeter_metrics --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 --if-not-exists || true

echo "Setup complete!"
echo ""
echo "Services:"
echo "  - Kafka: localhost:9092"
echo "  - TimescaleDB: localhost:5432"
echo "  - Grafana: http://localhost:3000 (admin/admin)"
echo "  - Flink UI: http://localhost:8081"
echo ""
echo "Next steps:"
echo "  1. Place your CSV data in data/sample_data.csv"
echo "  2. Run: python -m producer.csv_replay"
echo "  3. Submit Flink job (see README)"
echo "  4. Run: python -m consumer.kafka_to_db"

