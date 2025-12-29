# Project Data Flow

## End-to-End Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA INGESTION LAYER                              │
└─────────────────────────────────────────────────────────────────────────────┘

    CSV File (sample_data.csv)
           │
           │ Read & Parse
           ▼
    ┌──────────────────────┐
    │  CSV Replay Producer │  • Reads CSV file
    │  (csv_replay.py)     │  • Simulates real-time stream
    │                      │  • Adds configurable delays/gaps
    └──────────────────────┘
           │
           │ JSON Events
           │ {meter_id, timestamp, consumption_kwh}
           ▼
    ┌──────────────────────┐
    │  Kafka Producer      │  • Partitions by meter_id
    │  (kafka_producer.py) │  • Idempotent writes
    └──────────────────────┘
           │
           │ Produce to Topic
           ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │                         KAFKA BROKER                                 │
    │  Topic: smartmeter_raw (3 partitions, keyed by meter_id)             │
    └─────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                        STREAM PROCESSING LAYER                              │
└─────────────────────────────────────────────────────────────────────────────┘

           │
           │ Consume from smartmeter_raw
           ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │                    APACHE FLINK JOB                                  │
    │                    (flink_job/main.py)                               │
    └─────────────────────────────────────────────────────────────────────┘
           │
           │ Stream Processing Steps:
           │
           ├─► 1. Assign Event Time & Watermarks
           │      • Extract timestamp from event
           │      • Create bounded out-of-orderness watermarks (10s)
           │
           ├─► 2. Key by meter_id
           │      • Partition stream by meter for stateful processing
           │
           ├─► 3. Process Each Event (SmartMeterProcessingFunction)
           │      │
           │      ├─► Validate Event
           │      │     • Check required fields
           │      │     • Validate consumption values
           │      │     • Emit invalid_event metric if failed
           │      │
           │      ├─► Classify Event Timing
           │      │     • Compare event_time vs watermark
           │      │     • ON_TIME: Process normally
           │      │     • LATE: Process but mark as late
           │      │     • TOO_LATE: Route to late_events topic
           │      │
           │      ├─► Check for Gaps
           │      │     • Compare current_time vs last_seen
           │      │     • If gap detected → emit gap_alert
           │      │
           │      ├─► Update State (per meter_id)
           │      │     • last_seen = current event time
           │      │     • expected_next = last_seen + interval
           │      │     • gap_count, late_count counters
           │      │
           │      ├─► Register Event-Time Timer
           │      │     • Timer fires at: expected_next + grace_period
           │      │     • If timer fires → gap detected
           │      │
           │      └─► Emit Outputs
           │            • Validated reading (with status)
           │            • Gap alerts (if detected)
           │            • Late events (if too late)
           │            • Metrics (processing stats)
           │
           ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │                    OUTPUT STREAMS                                   │
    │  Split by type and route to different Kafka topics:                 │
    └─────────────────────────────────────────────────────────────────────┘
           │
           ├─► smartmeter_validated  → Validated readings (OK/LATE status)
           ├─► smartmeter_gap_alerts → Missing interval alerts
           ├─► smartmeter_late_events → Too-late events
           └─► smartmeter_metrics    → System & data quality metrics


┌─────────────────────────────────────────────────────────────────────────────┐
│                         PERSISTENCE LAYER                                   │
└─────────────────────────────────────────────────────────────────────────────┘

           │
           │ Consume from all output topics
           ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │              Kafka to Database Consumer                             │
    │              (consumer/kafka_to_db.py)                               │
    │                                                                      │
    │  • Runs 4 parallel consumer threads (one per topic)                 │
    │  • Deserializes JSON events                                         │
    │  • Writes to TimescaleDB using connection pool                      │
    └─────────────────────────────────────────────────────────────────────┘
           │
           │ INSERT statements
           ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │                    TIMESCALEDB                                     │
    │                    (PostgreSQL + TimescaleDB)                      │
    │                                                                      │
    │  Tables (Hypertables):                                              │
    │  • validated_readings  → Validated meter readings                   │
    │  • gap_alerts          → Missing interval records                   │
    │  • late_events         → Too-late event records                    │
    │  • metrics             → System metrics                             │
    │                                                                      │
    │  Continuous Aggregates:                                             │
    │  • gap_summary_hourly      → Hourly gap statistics                 │
    │  • late_events_summary_hourly → Hourly late event stats            │
    │  • metrics_summary_hourly  → Hourly metric aggregations            │
    └─────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                         VISUALIZATION LAYER                                │
└─────────────────────────────────────────────────────────────────────────────┘

           │
           │ SQL Queries
           ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │                         GRAFANA                                     │
    │                    (http://localhost:3000)                           │
    │                                                                      │
    │  Dashboards:                                                         │
    │  • Data Quality Overview                                             │
    │    - Active meters count                                             │
    │    - Events per minute                                              │
    │    - Missing intervals per hour                                      │
    │    - Percentage of late events                                      │
    │    - Top 10 meters by gap frequency                                  │
    │                                                                      │
    │  • Meter Drill-Down                                                  │
    │    - Per-meter consumption time-series                              │
    │    - Missing intervals visualization                               │
    │    - Late event markers                                             │
    │    - Meter statistics                                               │
    │                                                                      │
    │  • System & Stream Health                                            │
    │    - Processing metrics                                             │
    │    - Error rates                                                    │
    │    - Gap detection rates                                            │
    │    - Late event rates                                               │
    └─────────────────────────────────────────────────────────────────────┘
```

## Detailed Component Flow

### 1. Data Ingestion (Producer)

**File**: `producer/csv_replay.py`

```
CSV File → Parse Row → Create Event → Add Delays/Gaps → Send to Kafka
```

- Reads CSV file line by line
- Parses: `meter_id`, `timestamp`, `consumption_kwh`
- Simulates realistic streaming:
  - Configurable replay rate (1x, 2x, 0.5x speed)
  - Random delays (10% probability, max 5 minutes)
  - Random gaps (5% probability - skips records)
- Sends to `smartmeter_raw` topic, partitioned by `meter_id`

### 2. Stream Processing (Flink)

**File**: `flink_job/main.py`

```
Kafka Consumer → Watermarks → Key by meter_id → Process → Split → Kafka Producers
```

**Processing Logic** (`SmartMeterProcessingFunction`):

1. **Event Validation** (`processors/validator.py`)
   - Checks required fields
   - Validates data types and ranges
   - Rejects invalid events

2. **Late Event Classification** (`processors/late_event_handler.py`)
   - Compares event timestamp vs watermark
   - **ON_TIME**: Event arrives before watermark
   - **LATE**: Event arrives after watermark but within allowed lateness (1 hour)
   - **TOO_LATE**: Event arrives beyond allowed lateness → routed to `late_events` topic

3. **Gap Detection** (`processors/gap_detector.py`)
   - **Immediate Gap Detection**: When event arrives, check if gap exists since last event
   - **Timer-Based Gap Detection**: Register event-time timer at `expected_next + grace_period`
     - If timer fires before next event → gap detected
     - Emit gap alert with `missing_from` and `missing_to` timestamps

4. **State Management** (`utils/state_management.py`)
   - Per-meter state (keyed by `meter_id`):
     - `last_seen`: Timestamp of last event
     - `expected_next`: Expected timestamp of next event
     - `interval_minutes`: Expected interval (30 min default)
     - `gap_count`: Number of gaps detected
     - `late_count`: Number of late events
   - State TTL: 7 days (cleanup inactive meters)

5. **Output Generation**
   - **Validated Reading**: Original event + status (OK/LATE)
   - **Gap Alert**: Meter ID, missing time range, gap duration
   - **Late Event**: Meter ID, timestamp, delay seconds
   - **Metrics**: Processing statistics, error counts, etc.

### 3. Data Persistence (Consumer)

**File**: `consumer/kafka_to_db.py`

```
Kafka Topics → Consumer Threads → Deserialize → Database Connection Pool → INSERT
```

- Runs 4 parallel consumer threads:
  - `smartmeter_validated` → `validated_readings` table
  - `smartmeter_gap_alerts` → `gap_alerts` table
  - `smartmeter_late_events` → `late_events` table
  - `smartmeter_metrics` → `metrics` table
- Uses connection pooling for efficiency
- Handles JSON deserialization and timestamp conversion

### 4. Visualization (Grafana)

**Files**: `grafana/dashboards/*.json`

- Auto-provisioned dashboards query TimescaleDB
- Real-time refresh (10 seconds)
- Uses TimescaleDB continuous aggregates for performance
- Time-range queries with `$__timeFilter` macro

## Key Concepts

### Event-Time Processing

- **Event Time**: Uses the timestamp from the meter reading (not processing time)
- **Watermarks**: Indicate progress of event time
  - Bounded out-of-orderness: 10 seconds
  - Events within 10 seconds of watermark are considered on-time
- **Allowed Lateness**: 1 hour window for late events
- **Grace Period**: 15 minutes after expected time before declaring gap

### Stateful Processing

- **Keyed State**: Each `meter_id` maintains its own state
- **Event-Time Timers**: Fire based on event time (not wall-clock time)
- **State Recovery**: Flink checkpoints state every 60 seconds
- **Exactly-Once**: Guaranteed with checkpointing and idempotent sinks

### Gap Detection Strategy

1. **Proactive**: Register timer when event arrives
2. **Reactive**: Check for gaps when new event arrives
3. **Cascading**: Handle multiple consecutive gaps
4. **Resilient**: Timers can be cancelled if late event arrives

## Execution Order

1. **Start Infrastructure**: `docker-compose up -d`
   - Kafka, TimescaleDB, Grafana, Flink

2. **Create Topics**: Kafka topics for all streams

3. **Start Producer**: `python -m producer.csv_replay`
   - Begins streaming data to Kafka

4. **Submit Flink Job**: Submit to Flink cluster
   - Processes stream in real-time
   - Outputs to multiple Kafka topics

5. **Start Consumer**: `python -m consumer.kafka_to_db`
   - Persists all outputs to database

6. **View Dashboards**: Open Grafana
   - Real-time monitoring of data quality

## Data Flow Example

**Example Event Journey**:

```
1. CSV Row: "METER_0001,2024-01-01T10:00:00,2.5"
   ↓
2. Producer: Creates JSON, adds 30s delay, sends to Kafka
   ↓
3. Kafka: Stores in smartmeter_raw topic, partition 0 (meter_id hash)
   ↓
4. Flink: 
   - Assigns event time: 2024-01-01T10:00:00
   - Watermark: 2024-01-01T09:59:50 (10s behind)
   - Key by meter_id: METER_0001
   - Validates: ✓ Valid
   - Checks timing: ON_TIME
   - Updates state: last_seen = 10:00:00, expected_next = 10:30:00
   - Registers timer: 10:30:00 + 15min grace = 10:45:00
   - Emits: validated reading (status: OK)
   ↓
5. Kafka: smartmeter_validated topic receives event
   ↓
6. Consumer: Reads from topic, inserts into validated_readings table
   ↓
7. TimescaleDB: Stores with time = 10:00:00, meter_id = METER_0001
   ↓
8. Grafana: Queries table, displays on dashboard
```

**Gap Detection Example**:

```
1. Event at 10:00:00 → Timer registered for 10:45:00
2. No event arrives by 10:45:00
3. Timer fires → Gap detected
4. Flink emits gap_alert: missing_from=10:30:00, missing_to=10:45:00
5. Consumer writes to gap_alerts table
6. Grafana shows gap on meter drill-down dashboard
```

This architecture ensures **correctness**, **fault tolerance**, and **real-time observability** for smart meter data quality monitoring.

