# Setting Up the Kafka Connector for Flink

Flink needs a JAR file to talk to Kafka. The standard Maven URLs don't always work, so here's how to get it.

## Download the JAR

The easiest way is to download it directly:

```bash
# This one usually works
curl -L -o libs/flink-connector-kafka-1.18.0.jar \
  "https://repo1.maven.org/maven2/org/apache/flink/flink-connector-kafka_2.12/1.18.1/flink-connector-kafka_2.12-1.18.1.jar"

# Also need the Kafka client library
curl -L -o libs/kafka-clients.jar \
  "https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.5.0/kafka-clients-3.5.0.jar"
```

The Dockerfile will automatically copy these from `libs/` when you build. If the JARs are there, they'll be included in the image.

## Manual Copy (If Needed)

If you downloaded them after building:

```bash
docker cp libs/flink-connector-kafka-1.18.0.jar $(docker-compose ps -q flink-jobmanager):/opt/flink/lib/
docker cp libs/kafka-clients.jar $(docker-compose ps -q flink-jobmanager):/opt/flink/lib/
docker cp libs/flink-connector-kafka-1.18.0.jar $(docker-compose ps -q flink-taskmanager):/opt/flink/lib/
docker cp libs/kafka-clients.jar $(docker-compose ps -q flink-taskmanager):/opt/flink/lib/
```

## Verify It's There

```bash
docker-compose exec flink-jobmanager ls -lh /opt/flink/lib/flink-connector-kafka*
docker-compose exec flink-jobmanager ls -lh /opt/flink/lib/kafka-clients*
```

You should see both JARs listed.
