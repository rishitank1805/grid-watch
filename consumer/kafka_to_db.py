"""
Kafka consumer that writes validated data, alerts, and metrics to TimescaleDB.
"""
import json
import logging
import signal
import sys
from typing import Dict, Any
from kafka import KafkaConsumer
from kafka.errors import KafkaError

from database.connection import DatabaseConnection


class KafkaToDatabaseConsumer:
    """Consumes from Kafka topics and writes to database."""
    
    def __init__(self, kafka_config: dict, db_config: dict):
        """
        Initialize consumer.
        
        Args:
            kafka_config: Kafka configuration
            db_config: Database configuration
        """
        self.kafka_config = kafka_config
        self.db_config = db_config
        self.logger = logging.getLogger(__name__)
        self.running = True
        
        # Initialize database connection
        self.db = DatabaseConnection(db_config)
        self.db.connect()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info("Received shutdown signal")
        self.running = False
    
    def create_consumer(self, topic: str) -> KafkaConsumer:
        """Create Kafka consumer for a topic."""
        return KafkaConsumer(
            topic,
            bootstrap_servers=self.kafka_config['bootstrap_servers'],
            group_id=f"{self.kafka_config['consumer_group']}-{topic}",
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            consumer_timeout_ms=1000
        )
    
    def process_validated_readings(self):
        """Process validated readings topic."""
        consumer = self.create_consumer(self.kafka_config['topics']['validated'])
        self.logger.info(f"Started consuming from {self.kafka_config['topics']['validated']}")
        
        try:
            while self.running:
                message_pack = consumer.poll(timeout_ms=1000)
                
                for topic_partition, messages in message_pack.items():
                    for message in messages:
                        try:
                            reading = message.value
                            # Convert timestamp string to datetime if needed
                            if isinstance(reading.get('timestamp'), str):
                                from datetime import datetime
                                reading['timestamp'] = datetime.fromisoformat(
                                    reading['timestamp'].replace('Z', '+00:00')
                                )
                            self.db.insert_validated_reading(reading)
                        except Exception as e:
                            self.logger.error(f"Error processing validated reading: {e}")
        
        finally:
            consumer.close()
    
    def process_gap_alerts(self):
        """Process gap alerts topic."""
        consumer = self.create_consumer(self.kafka_config['topics']['gap_alerts'])
        self.logger.info(f"Started consuming from {self.kafka_config['topics']['gap_alerts']}")
        
        try:
            while self.running:
                message_pack = consumer.poll(timeout_ms=1000)
                
                for topic_partition, messages in message_pack.items():
                    for message in messages:
                        try:
                            alert = message.value
                            # Convert timestamp strings to datetime if needed
                            if isinstance(alert.get('missing_from'), str):
                                from datetime import datetime
                                alert['missing_from'] = datetime.fromisoformat(
                                    alert['missing_from'].replace('Z', '+00:00')
                                )
                            if isinstance(alert.get('missing_to'), str):
                                alert['missing_to'] = datetime.fromisoformat(
                                    alert['missing_to'].replace('Z', '+00:00')
                                )
                            self.db.insert_gap_alert(alert)
                        except Exception as e:
                            self.logger.error(f"Error processing gap alert: {e}")
        
        finally:
            consumer.close()
    
    def process_late_events(self):
        """Process late events topic."""
        consumer = self.create_consumer(self.kafka_config['topics']['late_events'])
        self.logger.info(f"Started consuming from {self.kafka_config['topics']['late_events']}")
        
        try:
            while self.running:
                message_pack = consumer.poll(timeout_ms=1000)
                
                for topic_partition, messages in message_pack.items():
                    for message in messages:
                        try:
                            event = message.value
                            # Convert timestamp string to datetime if needed
                            if isinstance(event.get('timestamp'), str):
                                from datetime import datetime
                                event['timestamp'] = datetime.fromisoformat(
                                    event['timestamp'].replace('Z', '+00:00')
                                )
                            self.db.insert_late_event(event)
                        except Exception as e:
                            self.logger.error(f"Error processing late event: {e}")
        
        finally:
            consumer.close()
    
    def process_metrics(self):
        """Process metrics topic."""
        consumer = self.create_consumer(self.kafka_config['topics']['metrics'])
        self.logger.info(f"Started consuming from {self.kafka_config['topics']['metrics']}")
        
        try:
            while self.running:
                message_pack = consumer.poll(timeout_ms=1000)
                
                for topic_partition, messages in message_pack.items():
                    for message in messages:
                        try:
                            metric = message.value
                            # Convert timestamp string to datetime if needed
                            if isinstance(metric.get('timestamp'), str):
                                from datetime import datetime
                                metric['timestamp'] = datetime.fromisoformat(
                                    metric['timestamp'].replace('Z', '+00:00')
                                )
                            self.db.insert_metric(metric)
                        except Exception as e:
                            self.logger.error(f"Error processing metric: {e}")
        
        finally:
            consumer.close()
    
    def run_all(self):
        """Run all consumers in separate threads."""
        import threading
        
        threads = [
            threading.Thread(target=self.process_validated_readings, daemon=True),
            threading.Thread(target=self.process_gap_alerts, daemon=True),
            threading.Thread(target=self.process_late_events, daemon=True),
            threading.Thread(target=self.process_metrics, daemon=True)
        ]
        
        for thread in threads:
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
    
    def close(self):
        """Close database connection."""
        self.db.close()


def main():
    """Main entry point."""
    import yaml
    import argparse
    
    parser = argparse.ArgumentParser(description='Kafka to Database Consumer')
    parser.add_argument('--config', default='config/config.yaml', help='Config file path')
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load config
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)
    
    # Create consumer
    consumer = KafkaToDatabaseConsumer(
        kafka_config=config['kafka'],
        db_config=config['database']
    )
    
    try:
        consumer.run_all()
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()


if __name__ == "__main__":
    main()

