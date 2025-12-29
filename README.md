# Real-Time Smart Meter Data Quality Monitoring

A production-style real-time streaming system that ingests smart electricity meter readings, validates time-series integrity, detects missing time steps, late arrivals, and irregular sampling, and exposes live data quality and system metrics through Grafana dashboards.

## Architecture

```
CSV Replay Producer → Kafka → Apache Flink → Kafka Topics → Database Consumer → TimescaleDB → Grafana
```

### Components

1. **CSV Replay Producer**: Simulates live smart meter data stream with configurable delays and gaps
2. **Kafka**: Message broker with topics for raw data, validated readings, gap alerts, late events, and metrics
3. **Apache Flink**: Event-time driven processing with stateful gap detection and late event handling
4. **TimescaleDB**: Time-series database for storing validated data, alerts, and metrics
5. **Grafana**: Real-time dashboards for data quality monitoring

## Features

- ✅ **Event-Time Semantics**: Uses meter timestamps as event time with bounded out-of-orderness watermarks
- ✅ **Stateful Processing**: Maintains per-meter state for gap detection and late event tracking
- ✅ **Gap Detection**: Uses event-time timers to detect missing intervals
- ✅ **Late Event Handling**: Classifies events as on-time, late, or too-late
- ✅ **Exactly-Once Processing**: Enabled with periodic checkpointing
- ✅ **Real-Time Dashboards**: Three Grafana dashboards for monitoring
- ✅ **Modular Python Code**: Clean, maintainable, and well-organized

## Prerequisites

- Docker and Docker Compose
- Python 3.8+
- Access to a smart meter dataset (see Data Sources below)

**Note**: The Flink job uses PyFlink which requires Java 11+. The Docker image includes Java, but if running Flink locally, ensure Java is installed.

## Quick Start

### 1. Clone and Setup

```bash
cd grid-watch
pip install -r requirements.txt
```

### 2. Prepare Data

You can either:

**Option A: Generate Sample Data**
```bash
python scripts/create_sample_data.py --meters 10 --days 7
```

**Option B: Use Real Data**

Download a smart meter dataset and place it in `data/sample_data.csv`. The CSV should have columns:
- `meter_id` (or `meterId`, `id`)
- `timestamp` (ISO format or `YYYY-MM-DD HH:MM:SS`)
- `consumption_kwh` (or `consumption`, `kwh`)

Example datasets:
- [UK Smart Meter Energy Consumption (Kaggle)](https://www.kaggle.com/datasets/jeanmidev/smart-meters-in-london)
- [UCI Electricity Load Diagrams](https://archive.ics.uci.edu/ml/datasets/ElectricityLoadDiagrams20112014)

### 3. Start Services

**Quick Setup (Recommended)**
```bash
./scripts/setup.sh
```

**Manual Setup**

```bash
# Start services
docker-compose up -d

# Wait for services to be healthy (about 30-60 seconds)
sleep 30

# Create Kafka topics
docker-compose exec kafka kafka-topics --create --topic smartmeter_raw --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 --if-not-exists
docker-compose exec kafka kafka-topics --create --topic smartmeter_validated --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 --if-not-exists
docker-compose exec kafka kafka-topics --create --topic smartmeter_gap_alerts --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 --if-not-exists
docker-compose exec kafka kafka-topics --create --topic smartmeter_late_events --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 --if-not-exists
docker-compose exec kafka kafka-topics --create --topic smartmeter_metrics --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 --if-not-exists
```

This starts:
- Zookeeper (port 2181)
- Kafka (port 9092)
- TimescaleDB (port 5432)
- Grafana (port 3000)
- Flink JobManager (port 8081)
- Flink TaskManager

### 5. Start Data Replay

```bash
python -m producer.csv_replay
```

This will replay your CSV data to Kafka with configurable delays and gaps.

### 6. Submit Flink Job

```bash
# Copy job files to Flink
docker cp flink_job flink-jobmanager:/opt/flink/usrlib/
docker cp config flink-jobmanager:/opt/flink/usrlib/

# Submit job
docker-compose exec flink-jobmanager flink run -py /opt/flink/usrlib/flink_job/main.py
```

### 7. Start Database Consumer

In a separate terminal:

```bash
python -m consumer.kafka_to_db
```

This consumes from Kafka topics and writes to TimescaleDB.

### 8. Access Grafana

Open http://localhost:3000 and login with:
- Username: `admin`
- Password: `admin`

The dashboards should be automatically provisioned:
- **Data Quality Overview**: Active meters, events per minute, missing intervals, late events
- **Meter Drill-Down**: Per-meter consumption, gaps, and late events
- **System & Stream Health**: Processing metrics, error rates, gap detection rates

## Configuration

Edit `config/config.yaml` to customize:

- **Kafka**: Bootstrap servers, topics, consumer groups
- **Flink**: Parallelism, checkpoint interval, allowed lateness, grace period
- **Database**: Connection details
- **Producer**: Replay rate, delay probability, gap probability
- **Grafana**: URL and credentials

## Project Structure

```
grid-watch/
├── config/
│   └── config.yaml              # Configuration file
├── producer/
│   ├── csv_replay.py            # CSV replay producer
│   └── kafka_producer.py        # Kafka producer wrapper
├── flink_job/
│   ├── main.py                  # Main Flink job
│   ├── processors/
│   │   ├── validator.py         # Event validation
│   │   ├── gap_detector.py      # Gap detection logic
│   │   └── late_event_handler.py # Late event classification
│   └── utils/
│       ├── schemas.py           # Event schemas
│       └── state_management.py  # State management
├── consumer/
│   └── kafka_to_db.py           # Kafka to database consumer
├── database/
│   ├── schema.sql               # TimescaleDB schema
│   └── connection.py            # Database connection
├── grafana/
│   ├── dashboards/              # Grafana dashboard JSON files
│   └── provisioning/            # Grafana provisioning configs
├── docker-compose.yml           # Docker Compose configuration
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Key Design Decisions

### Event-Time Processing

- Uses meter timestamps as event time (not processing time)
- Bounded out-of-orderness watermarks (10 seconds)
- Allowed lateness window (1 hour by default)
- Grace period for gap detection (15 minutes)

### Gap Detection

- Event-time timers fire when expected events don't arrive
- Timers are registered at `expected_time + grace_period`
- Cascading gaps are handled by updating expected next time
- State is maintained per meter using Flink keyed state

### Late Event Handling

- Events are classified as: ON_TIME, LATE, TOO_LATE
- Too-late events are routed to a separate topic
- Late events within allowed lateness are processed but marked

### State Management

- Keyed state per meter_id
- TTL for inactive meters (7 days default)
- State includes: last_seen, expected_next, interval, counters

## Monitoring

### Flink Web UI

Access at http://localhost:8081 to monitor:
- Job status and metrics
- Checkpoint status
- Operator throughput
- Watermark delay

### Grafana Dashboards

Three dashboards provide comprehensive monitoring:
1. **Data Quality Overview**: System-wide metrics
2. **Meter Drill-Down**: Per-meter analysis
3. **System Health**: Stream processing metrics

## Troubleshooting

### Flink Job Not Starting

- Check Flink logs: `docker-compose logs flink-jobmanager`
- Ensure Kafka is accessible from Flink containers
- Verify Python dependencies are installed in Flink image

### No Data in Grafana

- Verify database consumer is running
- Check Kafka topics have data: `docker-compose exec kafka kafka-console-consumer --topic smartmeter_validated --bootstrap-server localhost:9092`
- Verify database connection in Grafana datasource

### Gaps Not Detected

- Check grace period configuration
- Verify event-time timers are working (check Flink metrics)
- Ensure expected interval matches actual data interval

## Development

### Running Tests

```bash
# Add tests as needed
pytest tests/
```

### Adding New Processors

1. Create processor in `flink_job/processors/`
2. Import and use in `flink_job/main.py`
3. Update schemas if needed

### Modifying Dashboards

1. Edit JSON files in `grafana/dashboards/`
2. Or use Grafana UI (changes persist in volume)
3. Export and commit dashboard JSON

## License

MIT

## Contributing

Contributions welcome! Please open an issue or submit a pull request.

