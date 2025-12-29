# Kafka UI Guide

## Accessing Kafka UI

I've added **Kafka UI** to your docker-compose.yml. This provides a web interface to view Kafka topics, messages, and consumer groups.

### Start Kafka UI

```bash
docker-compose up -d kafka-ui
```

### Access the UI

Open your browser and go to:
**http://localhost:8080**

No login required - it's ready to use immediately!

## What You Can Do in Kafka UI

### 1. View Topics
- See all Kafka topics (smartmeter_raw, smartmeter_validated, etc.)
- View topic configuration (partitions, replication, etc.)
- See message counts and sizes

### 2. Browse Messages
- Click on any topic (e.g., `smartmeter_raw`)
- Click "Messages" tab
- View messages in real-time
- See message keys, values, timestamps, and partitions

### 3. Monitor Consumer Groups
- View consumer group status
- See consumer lag
- Monitor offset positions

### 4. Send Test Messages
- Use the "Produce Message" feature to send test messages
- Useful for testing your Flink job

## Quick Commands

### View messages in a topic via command line:
```bash
# View messages in smartmeter_raw topic
docker-compose exec kafka kafka-console-consumer \
  --topic smartmeter_raw \
  --bootstrap-server localhost:9092 \
  --from-beginning

# View only new messages (tail)
docker-compose exec kafka kafka-console-consumer \
  --topic smartmeter_raw \
  --bootstrap-server localhost:9092
```

### List all topics:
```bash
docker-compose exec kafka kafka-topics \
  --list \
  --bootstrap-server localhost:9092
```

### Check topic details:
```bash
docker-compose exec kafka kafka-topics \
  --describe \
  --topic smartmeter_raw \
  --bootstrap-server localhost:9092
```

## Troubleshooting

If Kafka UI doesn't connect:
1. Make sure Kafka is running: `docker-compose ps kafka`
2. Check Kafka UI logs: `docker-compose logs kafka-ui`
3. Verify Kafka is accessible: `docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092`

