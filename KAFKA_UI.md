# Kafka UI

There's a web UI for Kafka at **http://localhost:8080**. No login needed, just open it.

## What It's Good For

**Browse Topics** - See all your topics, message counts, partition info.

**Read Messages** - Click a topic, go to Messages tab, see what's actually in there. Super useful for debugging.

**Consumer Groups** - See which consumers are running, how far behind they are (lag).

**Send Test Messages** - There's a "Produce Message" button. Handy for testing.

## Quick Commands (If You Prefer CLI)

```bash
# See what's in a topic
docker-compose exec kafka kafka-console-consumer \
  --topic smartmeter_raw \
  --bootstrap-server localhost:9092 \
  --from-beginning

# List all topics
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Topic details
docker-compose exec kafka kafka-topics --describe --topic smartmeter_raw --bootstrap-server localhost:9092
```

## Troubleshooting

If the UI won't connect:
- Make sure Kafka is up: `docker-compose ps kafka`
- Check logs: `docker-compose logs kafka-ui`
- Verify Kafka works: `docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092`
