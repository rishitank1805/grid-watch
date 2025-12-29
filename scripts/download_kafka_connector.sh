#!/bin/bash
# Script to download Flink Kafka connector JAR

set -e

JAR_PATH="/opt/flink/lib/flink-connector-kafka-1.18.0.jar"
# Try 1.18.1 first (matches Flink version), then 1.18.0
JAR_URL="https://repo1.maven.org/maven2/org/apache/flink/flink-connector-kafka_2.12/1.18.1/flink-connector-kafka_2.12-1.18.1.jar"

if [ ! -f "$JAR_PATH" ]; then
    echo "Downloading Flink Kafka connector JAR..."
    mkdir -p /opt/flink/lib
    curl -L -f -o "$JAR_PATH" "$JAR_URL" || {
        echo "Failed to download 1.18.1, trying 1.18.0..."
        curl -L -f -o "$JAR_PATH" "https://repo1.maven.org/maven2/org/apache/flink/flink-connector-kafka_2.12/1.18.0/flink-connector-kafka_2.12-1.18.0.jar" || {
            echo "Failed to download 1.18.0, trying universal connector..."
            curl -L -f -o "$JAR_PATH" "https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-kafka/1.18.1/flink-sql-connector-kafka-1.18.1.jar" || {
                echo "ERROR: Could not download Kafka connector JAR from any source"
                exit 1
            }
        }
    }
    chmod 644 "$JAR_PATH"
    echo "Kafka connector JAR downloaded successfully: $JAR_PATH"
    ls -lh "$JAR_PATH"
else
    echo "Kafka connector JAR already exists: $JAR_PATH"
fi

