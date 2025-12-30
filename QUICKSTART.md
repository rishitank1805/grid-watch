# Quick Start

Get this running in a few minutes.

## 1. Generate Some Data

```bash
python scripts/create_sample_data.py
```

Or use your own CSV file in `data/sample_data.csv`.

## 2. Start Everything

```bash
./scripts/setup.sh
```

Or do it manually:
```bash
docker-compose up -d
# Wait 30 seconds, then create topics (see README)
```

## 3. Send Data to Kafka

```bash
python -m producer.csv_replay
```

This reads your CSV and streams it to Kafka.

## 4. Run the Flink Job

```bash
./scripts/submit_flink_job.sh
```

This processes the stream and writes results back to Kafka.

## 5. Save to Database

In another terminal:
```bash
python -m consumer.kafka_to_db
```

This reads from Kafka and writes to TimescaleDB.

## 6. Check It Out

Open http://localhost:3000 (admin/admin) to see the dashboards.

## When Things Break

**Services not running?**
```bash
docker-compose ps
```

**Need logs?**
```bash
docker-compose logs -f kafka
docker-compose logs -f flink-jobmanager
```

**Check if Kafka has data:**
```bash
docker-compose exec kafka kafka-console-consumer --topic smartmeter_validated --bootstrap-server localhost:9092 --from-beginning
```

**Check database:**
```bash
docker-compose exec timescaledb psql -U gridwatch -d gridwatch -c "SELECT COUNT(*) FROM validated_readings;"
```
