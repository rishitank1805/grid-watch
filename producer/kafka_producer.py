"""
Kafka producer for smart meter events.
"""
import json
import logging
from typing import Dict, Any
from kafka import KafkaProducer
from kafka.errors import KafkaError


class SmartMeterProducer:
    """Produces smart meter events to Kafka."""
    
    def __init__(self, bootstrap_servers: str, topic: str, config: dict = None):
        """
        Initialize producer.
        
        Args:
            bootstrap_servers: Kafka broker address
            topic: Target topic name
            config: Additional producer configuration
        """
        producer_config = {
            'bootstrap_servers': bootstrap_servers,
            'value_serializer': lambda v: json.dumps(v).encode('utf-8'),
            'key_serializer': lambda k: k.encode('utf-8') if k else None,
            'acks': 'all',
            'retries': 3,
            'max_in_flight_requests_per_connection': 1,
            'enable_idempotence': True,
            'compression_type': 'snappy'  # Snappy compression for better performance
        }
        
        if config:
            producer_config.update(config)
        
        self.producer = KafkaProducer(**producer_config)
        self.topic = topic
        self.logger = logging.getLogger(__name__)
    
    def send_event(self, event: Dict[str, Any], meter_id: str = None):
        """
        Send event to Kafka.
        
        Args:
            event: Event dictionary
            meter_id: Optional meter_id for partitioning (extracted from event if not provided)
        """
        try:
            key = meter_id or event.get('meter_id', '')
            future = self.producer.send(self.topic, key=key, value=event)
            
            # Optional: wait for confirmation
            # record_metadata = future.get(timeout=10)
            # self.logger.debug(f"Sent to {record_metadata.topic}[{record_metadata.partition}]")
            
        except KafkaError as e:
            self.logger.error(f"Failed to send event: {e}")
            raise
    
    def flush(self):
        """Flush all pending messages."""
        self.producer.flush()
    
    def close(self):
        """Close the producer."""
        self.producer.close()

