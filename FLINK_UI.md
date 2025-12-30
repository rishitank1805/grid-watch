# Using the Flink Web UI

Flink comes with a web UI that's actually pretty useful. It's at **http://localhost:8081**.

## What You Can See

**Job List** - All your jobs, running or finished. Click one to see details.

**Execution Plan** - Visual DAG showing how data flows through your job. Nice for debugging.

**Checkpoints** - See if checkpoints are working, how long they take, when the last one happened.

**Metrics** - Throughput, latency, backpressure. All the good stuff.

**Task Managers** - CPU, memory usage, which tasks are running where.

## Quick Tour

1. Open http://localhost:8081
2. Click "Running Jobs" in the sidebar
3. Find "Smart Meter Data Quality Monitoring" (or whatever you named it)
4. Click it to see:
   - The execution graph (Kafka sources → processing → Kafka sinks)
   - Throughput numbers (records/second in and out)
   - Checkpoint status
   - Any exceptions

## Useful Things

**Checkpoint Tab** - Shows checkpoint history. If these are failing, your job might have issues.

**Metrics Tab** - Real-time metrics. Watch `numRecordsInPerSecond` to see if data is flowing.

**Exceptions Tab** - If something breaks, it's here.

**Timeline Tab** - See when operators started, when checkpoints happened, etc.

## Submitting Jobs via UI

You can upload JARs and submit jobs through the UI if you want. We're using Python though, so the script is easier.

## Canceling Jobs

Click the job, then hit "Cancel". Useful when you need to stop something quickly.

## If It's Not Working

```bash
# Is Flink running?
docker-compose ps flink-jobmanager

# Check logs
docker-compose logs flink-jobmanager

# Restart if needed
docker-compose restart flink-jobmanager
```

## Other UIs

- Kafka UI: http://localhost:8080
- Grafana: http://localhost:3000
