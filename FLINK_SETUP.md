# Flink Job Submission Guide

## Understanding the Error

The error you saw:
```
java.nio.file.NoSuchFileException: /tmp/pyflink/.../main.py
```

This happens because:
1. Flink tries to copy Python files to a temporary directory for execution
2. The standard `flink:1.18-scala_2.12` image may not have PyFlink properly configured
3. The file path resolution might be incorrect

## Solution

I've created a custom Dockerfile (`Dockerfile.flink`) that extends the standard Flink image with PyFlink:
- Base image: `flink:1.18-scala_2.12`
- Adds: Python 3, pip, and PyFlink 1.18.0

The docker-compose.yml now builds this custom image instead of using a pre-built one.

## Steps to Fix

1. **Build the custom Flink image** (this will take a few minutes the first time):
   ```bash
   docker-compose build flink-jobmanager flink-taskmanager
   ```

2. **Start the Flink containers**:
   ```bash
   docker-compose up -d flink-jobmanager flink-taskmanager
   ```

2. **Wait for containers to be ready** (about 30 seconds)

3. **Submit the job**:
   ```bash
   ./scripts/submit_flink_job.sh
   ```

   Or manually:
   ```bash
   docker-compose exec flink-jobmanager flink run -py /opt/flink/usrlib/flink_job/main.py
   ```

## Alternative: If PyFlink Image Doesn't Work

If the PyFlink image has issues, you can:

1. **Use the standard image and install PyFlink**:
   ```bash
   docker-compose exec flink-jobmanager pip install apache-flink
   ```

2. **Or create a custom Dockerfile** that extends the Flink image with PyFlink

## Verifying PyFlink is Available

Check if PyFlink is installed:
```bash
docker-compose exec flink-jobmanager python3 -c "import pyflink; print(pyflink.__version__)"
```

## Troubleshooting

- **If job submission fails**: Check Flink logs:
  ```bash
  docker-compose logs flink-jobmanager
  ```

- **If Python modules not found**: Ensure the volume mount is correct:
  ```bash
  docker-compose exec flink-jobmanager ls -la /opt/flink/usrlib/flink_job
  ```

- **If Kafka connection fails**: Update `config/config.yaml` to use `kafka:9092` instead of `localhost:9092` (container networking)

