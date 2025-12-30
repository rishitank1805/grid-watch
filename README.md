# Smart Meter Data Quality Monitoring

Real-time streaming pipeline for monitoring smart electricity meter data. Detects gaps, late arrivals, and data quality issues as they happen.

## What This Does

Takes smart meter readings from CSV files, streams them through Kafka, processes with Flink to detect problems (missing data, late events), and stores everything in TimescaleDB. Grafana dashboards show what's happening in real-time.

## Architecture

```
CSV → Kafka → Flink → Kafka (processed) → TimescaleDB → Grafana
```

- **Producer**: Reads CSV and sends to Kafka (simulates live stream)
- **Kafka**: Message broker with 5 topics (raw, validated, gaps, late events, metrics)
- **Flink**: Does the heavy lifting - validates, detects gaps, handles late events
- **TimescaleDB**: Stores everything for querying later
- **Grafana**: Pretty dashboards to see what's going on

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.8+ (3.13 works too)
- Some smart meter data (or we'll generate sample data)

### Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Get some data:**

   Either generate sample data:
   ```bash
   python scripts/create_sample_data.py --meters 10 --days 7
   ```

   Or use your own CSV. Put it in `data/sample_data.csv` with columns:
   - `meter_id` (or `meterId`, `id` - we'll figure it out)
   - `timestamp` (ISO format or `YYYY-MM-DD HH:MM:SS`)
   - `consumption_kwh` (or `consumption`, `kwh`)

   Good datasets:
   - [UK Smart Meter Data on Kaggle](https://www.kaggle.com/datasets/jeanmidev/smart-meters-in-london)
   - [UCI Electricity Load Diagrams](https://archive.ics.uci.edu/ml/datasets/ElectricityLoadDiagrams20112014)

3. **Start everything:**
   ```bash
   docker-compose up -d
   ```

   Wait about 30 seconds for services to start, then create Kafka topics:
   ```bash
   docker-compose exec kafka kafka-topics --create --topic smartmeter_raw --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 --if-not-exists
   docker-compose exec kafka kafka-topics --create --topic smartmeter_validated --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 --if-not-exists
   docker-compose exec kafka kafka-topics --create --topic smartmeter_gap_alerts --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 --if-not-exists
   docker-compose exec kafka kafka-topics --create --topic smartmeter_late_events --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 --if-not-exists
   docker-compose exec kafka kafka-topics --create --topic smartmeter_metrics --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 --if-not-exists
   ```

4. **Send data to Kafka:**
   ```bash
   python -m producer.csv_replay
   ```

5. **Start the Flink job:**
   ```bash
   ./scripts/submit_flink_job.sh
   ```

6. **Write to database (separate terminal):**
   ```bash
   python -m consumer.kafka_to_db
   ```

7. **Check it out:**
   - Grafana: http://localhost:3000 (admin/admin)
   - Flink UI: http://localhost:8081
   - Kafka UI: http://localhost:8080

## How It Works

### Event-Time Processing

Uses the actual meter timestamps, not when we process them. Handles out-of-order events with watermarks. Events can arrive up to an hour late and still get processed.

### Gap Detection

If a meter is supposed to send data every 30 minutes and we don't see it, we fire a timer after a grace period (15 min default). Detects cascading gaps too.

### Late Events

Events get classified as:
- **ON_TIME**: Arrived when expected
- **LATE**: Arrived late but still within the allowed window
- **TOO_LATE**: Missed the window, goes to a separate topic

### State Management

Keeps track of each meter separately. Remembers when we last saw it, when we expect the next reading, and the interval between readings. Cleans up after 7 days of inactivity.

## Configuration

Edit `config/config.yaml` to tweak:
- Kafka connection details
- Flink parallelism and checkpoint settings
- Database connection
- How the producer simulates delays/gaps
- Grafana credentials

## Project Structure

```
grid-watch/
├── config/              # Config files
├── producer/            # CSV replay and Kafka producer
├── flink_job/          # The main processing logic
│   ├── processors/     # Validator, gap detector, late event handler
│   └── utils/          # Schemas and state management
├── consumer/           # Kafka to database writer
├── database/           # TimescaleDB schema and connection
├── grafana/            # Dashboard configs
└── scripts/            # Helper scripts
```

## Monitoring

### Flink UI (http://localhost:8081)

See your job running, check throughput, monitor checkpoints. Pretty useful when things go wrong.

### Grafana Dashboards

Three dashboards:
1. **Data Quality Overview** - Big picture stuff
2. **Meter Drill-Down** - Individual meter details
3. **System Health** - Processing metrics

## Common Issues

**Flink job won't start:**
- Check logs: `docker-compose logs flink-jobmanager`
- Make sure Kafka is reachable from Flink
- Verify the Kafka connector JAR is in `libs/` (see SETUP_KAFKA_CONNECTOR.md)

**No data in Grafana:**
- Is the database consumer running?
- Check Kafka has data: `docker-compose exec kafka kafka-console-consumer --topic smartmeter_validated --bootstrap-server localhost:9092 --from-beginning`
- Verify Grafana can connect to TimescaleDB

**Gaps not being detected:**
- Check the grace period in config
- Make sure the expected interval matches your data
- Look at Flink metrics to see if timers are firing

## Development

Want to add a new processor? Drop it in `flink_job/processors/` and wire it up in `main.py`.

Dashboard changes? Edit the JSON files in `grafana/dashboards/` or use the Grafana UI (changes save to the volume).

## License

MIT
