# How Data Flows Through the System

Here's what happens to your data from CSV to dashboard.

## The Pipeline

```
CSV → Producer → Kafka (raw) → Flink → Kafka (processed) → Consumer → TimescaleDB → Grafana
```

## Step by Step

### 1. Producer Reads CSV

The `csv_replay.py` script reads your CSV file and sends each row to Kafka. It can simulate delays and skip records to create gaps (useful for testing).

Sends to: `smartmeter_raw` topic

### 2. Flink Processes It

Flink reads from `smartmeter_raw` and does a bunch of stuff:

- **Validates** the event (required fields, reasonable values)
- **Checks timing** - is this event late? Too late?
- **Detects gaps** - did we miss an expected reading?
- **Updates state** - remembers what we last saw for each meter
- **Splits output** into different streams

Writes to 4 Kafka topics:
- `smartmeter_validated` - good readings (with status)
- `smartmeter_gap_alerts` - missing intervals
- `smartmeter_late_events` - events that arrived too late
- `smartmeter_metrics` - processing stats

### 3. Consumer Writes to Database

The `kafka_to_db.py` script runs 4 consumer threads (one per topic) and writes everything to TimescaleDB tables.

### 4. Grafana Shows It

Grafana queries TimescaleDB and displays dashboards that update every 10 seconds.

## How Gap Detection Works

When Flink sees an event for a meter:
1. It remembers when it last saw this meter
2. It calculates when the next reading should arrive (last_seen + interval)
3. It sets a timer for that time + grace period (15 min default)
4. If the timer fires before the next event arrives → gap detected

The timer is based on event time, not wall-clock time. So if events are delayed, the timer adjusts.

## How Late Events Work

Events get compared to the watermark (which tracks event time progress):
- **ON_TIME**: Arrived before watermark
- **LATE**: Arrived after watermark but within 1 hour window
- **TOO_LATE**: Missed the window entirely → goes to late_events topic

## State Management

Flink keeps state per meter (keyed by meter_id):
- When we last saw this meter
- When we expect the next reading
- How many gaps we've seen
- How many late events

This state gets checkpointed every 60 seconds, so if Flink crashes, it can recover.

## Example Flow

Say you have a reading at 10:00 AM:

1. CSV row gets read → sent to Kafka
2. Flink picks it up, validates it, marks it as ON_TIME
3. Updates state: last_seen = 10:00, expected_next = 10:30
4. Sets timer for 10:45 (10:30 + 15 min grace)
5. Emits to `smartmeter_validated` topic
6. Consumer writes to database
7. Grafana shows it on the dashboard

If no event arrives by 10:45:
- Timer fires
- Gap alert created: missing from 10:30 to 10:45
- Goes to `smartmeter_gap_alerts` topic
- Consumer writes to database
- Grafana shows the gap

## Why This Design?

**Event-time processing** - Uses actual meter timestamps, not when we process them. Handles out-of-order data correctly.

**Stateful processing** - Remembers context per meter. Can't detect gaps without remembering what we last saw.

**Exactly-once** - Checkpointing ensures we don't lose data or process duplicates.

**Multiple outputs** - Separates concerns. Validated data, alerts, and metrics go to different places.
