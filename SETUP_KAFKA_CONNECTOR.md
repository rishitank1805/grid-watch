# Setting Up Flink Kafka Connector

The Flink Kafka connector JAR is required for the PyFlink job to work. Since the standard Maven URLs are not working, please download it manually:

## Option 1: Download via Maven (Recommended)

Run this command to download the connector JAR:

```bash
# For Flink 1.18.1 (matches your Flink version)
curl -L -o libs/flink-connector-kafka-1.18.0.jar \
  "https://repo1.maven.org/maven2/org/apache/flink/flink-connector-kafka_2.12/1.18.1/flink-connector-kafka_2.12-1.18.1.jar"

# Or try the universal connector
curl -L -o libs/flink-connector-kafka-1.18.0.jar \
  "https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-kafka/1.18.1/flink-sql-connector-kafka-1.18.1.jar"
```

Then copy it to the Flink container:

```bash
docker cp libs/flink-connector-kafka-1.18.0.jar $(docker-compose ps -q flink-jobmanager):/opt/flink/lib/
docker cp libs/flink-connector-kafka-1.18.0.jar $(docker-compose ps -q flink-taskmanager):/opt/flink/lib/
```

## Option 2: Use Dockerfile

Add this to your Dockerfile.flink before the `USER flink` line:

```dockerfile
# Copy Kafka connector JAR if available
COPY libs/flink-connector-kafka-1.18.0.jar /opt/flink/lib/ 2>/dev/null || echo "JAR not found, will need to be added manually"
```

Then rebuild:

```bash
docker-compose build flink-jobmanager flink-taskmanager
```

## Option 3: Manual Download

1. Visit https://mvnrepository.com/artifact/org.apache.flink/flink-connector-kafka_2.12
2. Download version 1.18.1 or 1.18.0
3. Place it in `libs/flink-connector-kafka-1.18.0.jar`
4. Copy to containers as shown in Option 1

## Verification

After adding the JAR, verify it exists:

```bash
docker-compose exec flink-jobmanager ls -lh /opt/flink/lib/flink-connector-kafka*
```

You should see the JAR file listed.

