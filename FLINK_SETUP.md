# Setting Up Flink

If you're getting errors about PyFlink not being found, here's what's going on.

## The Problem

The standard Flink Docker image doesn't include PyFlink. We built a custom image that does.

## What We Did

Created `Dockerfile.flink` that:
- Starts with the standard Flink image
- Installs Python 3 and pip
- Installs PyFlink 1.18.0
- Sets up JDK headers (needed for PyFlink's native bits)
- Copies the Kafka connector JARs

The docker-compose.yml builds this image automatically.

## Getting It Running

1. **Build the image** (first time only, takes a few minutes):
   ```bash
   docker-compose build flink-jobmanager flink-taskmanager
   ```

2. **Start Flink**:
   ```bash
   docker-compose up -d flink-jobmanager flink-taskmanager
   ```

3. **Submit your job**:
   ```bash
   ./scripts/submit_flink_job.sh
   ```

## Verify PyFlink Works

```bash
docker-compose exec flink-jobmanager python3 -c "import pyflink; print('PyFlink is installed')"
```

## Common Issues

**Job won't submit:**
- Check logs: `docker-compose logs flink-jobmanager`
- Make sure volumes are mounted: `docker-compose exec flink-jobmanager ls -la /opt/flink/usrlib/flink_job`

**Kafka connection fails:**
- Flink containers use `kafka:29092` (internal port)
- Your producer uses `localhost:9092` (external port)
- Check `config/config.flink.yaml` has the right bootstrap servers

**Missing Kafka connector:**
- See SETUP_KAFKA_CONNECTOR.md
- JARs should be in `libs/` directory
