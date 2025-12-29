# Quick Start Guide

## 1. Generate Sample Data

```bash
python scripts/create_sample_data.py
```

## 2. Setup and Start Services

```bash
./scripts/setup.sh
```

Or manually:
```bash
docker-compose up -d
# Wait 30 seconds, then create topics (see README)
```

## 3. Start Data Replay

```bash
python -m producer.csv_replay
```

## 4. Submit Flink Job

```bash
# Copy files to Flink container
docker cp flink_job flink-jobmanager:/opt/flink/usrlib/
docker cp config flink-jobmanager:/opt/flink/usrlib/

# Submit job
docker-compose exec flink-jobmanager flink run -py /opt/flink/usrlib/flink_job/main.py
```

## 5. Start Database Consumer

In a new terminal:
```bash
python -m consumer.kafka_to_db
```

## 6. View Dashboards

Open http://localhost:3000
- Username: `admin`
- Password: `admin`

## Troubleshooting

### Check Service Status
```bash
docker-compose ps
```

### View Logs
```bash
docker-compose logs -f kafka
docker-compose logs -f flink-jobmanager
docker-compose logs -f timescaledb
```

### Check Kafka Topics
```bash
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092
```

### Check Data in Kafka
```bash
docker-compose exec kafka kafka-console-consumer --topic smartmeter_validated --bootstrap-server localhost:9092 --from-beginning
```

### Check Database
```bash
docker-compose exec timescaledb psql -U gridwatch -d gridwatch -c "SELECT COUNT(*) FROM validated_readings;"
```

