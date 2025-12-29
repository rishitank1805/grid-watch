# Flink Web UI Access

Apache Flink includes a built-in web UI for monitoring and managing Flink jobs.

## Access the Flink UI

The Flink Web UI is available at:

**http://localhost:8081**

## Features

The Flink Web UI provides:

1. **Job Overview**
   - List of all submitted jobs
   - Job status (Running, Finished, Failed, Cancelled)
   - Job submission time and duration

2. **Job Details**
   - Job execution plan (DAG visualization)
   - Task manager details
   - Checkpoint information
   - Metrics and statistics

3. **Task Manager**
   - List of all task managers
   - Resource usage (CPU, memory)
   - Network metrics

4. **Checkpoints**
   - Checkpoint history
   - Checkpoint size and duration
   - Latest checkpoint information

5. **Metrics**
   - System metrics
   - Job-specific metrics
   - Custom metrics from your application

## Using the Flink UI

### View Running Jobs

1. Open http://localhost:8081 in your browser
2. Click on "Running Jobs" or "Completed Jobs" in the sidebar
3. Click on a job to see detailed information

### Monitor Job Execution

- **Overview Tab**: See job status, start time, duration
- **Timeline Tab**: Visual timeline of job execution
- **Exceptions Tab**: View any errors or exceptions
- **Checkpoints Tab**: Monitor checkpoint status and history
- **Metrics Tab**: View real-time metrics

### Submit Jobs via UI

You can also submit jobs through the UI:
1. Go to "Submit New Job"
2. Upload your JAR file
3. Configure entry class and parameters
4. Submit the job

### Cancel Jobs

To cancel a running job:
1. Go to "Running Jobs"
2. Click on the job
3. Click "Cancel" button

## Troubleshooting

If the Flink UI is not accessible:

1. **Check if Flink is running:**
   ```bash
   docker-compose ps flink-jobmanager
   ```

2. **Check Flink logs:**
   ```bash
   docker-compose logs flink-jobmanager
   ```

3. **Verify port is exposed:**
   ```bash
   docker-compose ps | grep 8081
   ```

4. **Restart Flink if needed:**
   ```bash
   docker-compose restart flink-jobmanager
   ```

## Quick Links

- **Flink UI**: http://localhost:8081
- **Kafka UI**: http://localhost:8080
- **Grafana**: http://localhost:3000

## Example: Viewing Your Smart Meter Job

After submitting the Flink job with `./scripts/submit_flink_job.sh`:

1. Open http://localhost:8081
2. You should see "Smart Meter Data Quality Monitoring" in the jobs list
3. Click on it to see:
   - Execution plan showing Kafka sources and sinks
   - Task manager assignments
   - Checkpoint status
   - Throughput metrics (records/second)
   - Latency metrics

## Metrics to Monitor

For the smart meter monitoring job, watch these metrics:

- **numRecordsInPerSecond**: Input rate from Kafka
- **numRecordsOutPerSecond**: Output rate to Kafka topics
- **checkpointDuration**: Time taken for checkpoints
- **lastCheckpointSize**: Size of the latest checkpoint
- **backpressure**: Indicates if processing is keeping up

