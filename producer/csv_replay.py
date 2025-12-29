"""
CSV replay producer that simulates live smart meter data stream.
"""
import csv
import time
import random
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

from producer.kafka_producer import SmartMeterProducer


class CSVReplayProducer:
    """Replays CSV data as a live stream with configurable delays and gaps."""
    
    def __init__(self, csv_file: str, producer: SmartMeterProducer, config: dict):
        """
        Initialize CSV replay producer.
        
        Args:
            csv_file: Path to CSV file
            producer: Kafka producer instance
            config: Configuration dictionary
        """
        self.csv_file = Path(csv_file)
        self.producer = producer
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Replay settings
        self.replay_rate = config.get('replay_rate', 1.0)
        self.delay_probability = config.get('delay_probability', 0.1)
        self.max_delay_seconds = config.get('max_delay_seconds', 300)
        self.gap_probability = config.get('gap_probability', 0.05)
        
        # Track last timestamp per meter for realistic replay
        self.last_timestamps: Dict[str, datetime] = {}
    
    def parse_csv_row(self, row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse CSV row into event format.
        
        Expected CSV columns:
        - meter_id (or similar)
        - timestamp (ISO format or parseable)
        - consumption_kwh (or similar)
        """
        try:
            # Try common column name variations
            meter_id = row.get('meter_id') or row.get('meterId') or row.get('id')
            timestamp_str = row.get('timestamp') or row.get('time') or row.get('datetime')
            consumption = row.get('consumption_kwh') or row.get('consumption') or row.get('kwh')
            
            if not all([meter_id, timestamp_str, consumption]):
                self.logger.warning(f"Skipping incomplete row: {row}")
                return None
            
            # Parse timestamp
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except:
                # Try other formats
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            
            return {
                'meter_id': str(meter_id),
                'timestamp': timestamp.isoformat(),
                'consumption_kwh': float(consumption)
            }
        except Exception as e:
            self.logger.error(f"Error parsing row {row}: {e}")
            return None
    
    def should_add_delay(self) -> float:
        """Determine if delay should be added and how much."""
        if random.random() < self.delay_probability:
            return random.uniform(0, self.max_delay_seconds)
        return 0.0
    
    def should_skip_for_gap(self) -> bool:
        """Determine if this record should be skipped to simulate a gap."""
        return random.random() < self.gap_probability
    
    def calculate_sleep_time(self, current_time: datetime, next_time: datetime,
                            last_sent_time: Optional[datetime] = None) -> float:
        """
        Calculate sleep time between events based on replay rate.
        
        Args:
            current_time: Timestamp of current event
            next_time: Timestamp of next event
            last_sent_time: When we last sent an event
        """
        if last_sent_time is None:
            return 0.0
        
        # Calculate real time difference
        real_diff = (next_time - current_time).total_seconds()
        
        # Adjust for replay rate
        sleep_time = real_diff / self.replay_rate
        
        # Ensure non-negative
        return max(0.0, sleep_time)
    
    def replay(self):
        """Replay CSV file as a stream."""
        if not self.csv_file.exists():
            raise FileNotFoundError(f"CSV file not found: {self.csv_file}")
        
        self.logger.info(f"Starting replay of {self.csv_file}")
        self.logger.info(f"Replay rate: {self.replay_rate}x")
        
        events = []
        
        # Read all events first and sort by timestamp
        with open(self.csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                event = self.parse_csv_row(row)
                if event:
                    events.append(event)
        
        # Sort by timestamp
        events.sort(key=lambda x: x['timestamp'])
        
        self.logger.info(f"Loaded {len(events)} events")
        
        last_sent_time = None
        sent_count = 0
        skipped_count = 0
        
        for i, event in enumerate(events):
            # Check if we should skip this event (simulate gap)
            if self.should_skip_for_gap():
                self.logger.debug(f"Skipping event to simulate gap: {event['meter_id']} at {event['timestamp']}")
                skipped_count += 1
                continue
            
            # Calculate sleep time
            if last_sent_time and i > 0:
                current_timestamp = datetime.fromisoformat(event['timestamp'])
                prev_timestamp = datetime.fromisoformat(events[i-1]['timestamp'])
                sleep_time = self.calculate_sleep_time(
                    prev_timestamp,
                    current_timestamp,
                    last_sent_time
                )
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
            
            # Add random delay if configured
            delay = self.should_add_delay()
            if delay > 0:
                self.logger.debug(f"Adding {delay:.2f}s delay to event")
                time.sleep(delay)
            
            # Send event
            try:
                self.producer.send_event(event)
                sent_count += 1
                last_sent_time = datetime.now()
                
                if sent_count % 100 == 0:
                    self.logger.info(f"Sent {sent_count} events, skipped {skipped_count}")
            
            except Exception as e:
                self.logger.error(f"Error sending event: {e}")
        
        # Flush remaining messages
        self.producer.flush()
        
        self.logger.info(f"Replay complete. Sent: {sent_count}, Skipped: {skipped_count}")


def main():
    """Main entry point for CSV replay."""
    import yaml
    import argparse
    
    parser = argparse.ArgumentParser(description='Replay CSV data to Kafka')
    parser.add_argument('--config', default='config/config.yaml', help='Config file path')
    parser.add_argument('--csv', help='CSV file path (overrides config)')
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load config
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)
    
    # Create producer
    producer = SmartMeterProducer(
        bootstrap_servers=config['kafka']['bootstrap_servers'],
        topic=config['kafka']['topics']['raw'],
        config=config['kafka']['producer_config']
    )
    
    # Create replay producer
    csv_file = args.csv or config['producer']['csv_file']
    replay_producer = CSVReplayProducer(
        csv_file=csv_file,
        producer=producer,
        config=config['producer']
    )
    
    try:
        replay_producer.replay()
    finally:
        producer.close()


if __name__ == "__main__":
    main()

