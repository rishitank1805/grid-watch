"""
Main Flink job for smart meter data quality monitoring.

This job processes smart meter readings with event-time semantics,
detects gaps, handles late events, and emits metrics.
"""
import json
import sys
import os
from datetime import datetime, timedelta
from typing import Any

# Add the parent directory to Python path so we can import flink_job modules
# When running in Flink, the script is at /opt/flink/usrlib/flink_job/main.py
# We need to add /opt/flink/usrlib to the path
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.functions import KeyedProcessFunction, RuntimeContext
from pyflink.datastream.state import ValueStateDescriptor, ValueState
from pyflink.common.typeinfo import Types
from pyflink.common.serialization import SimpleStringSchema
from pyflink.datastream.connectors import FlinkKafkaConsumer, FlinkKafkaProducer

# Import our modules
from flink_job.utils.schemas import (
    SmartMeterEvent, ValidatedReading, GapAlert, LateEvent, MetricsEvent
)
from flink_job.utils.state_management import StateManager, MeterState
from flink_job.processors.validator import EventValidator
from flink_job.processors.late_event_handler import LateEventHandler
from flink_job.processors.gap_detector import GapDetector


class SmartMeterProcessingFunction(KeyedProcessFunction):
    """
    Main processing function that handles:
    - Event validation
    - Gap detection using event-time timers
    - Late event classification
    - State management
    - Metrics emission
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.validator = EventValidator()
        self.late_handler = LateEventHandler(
            allowed_lateness_seconds=config['flink']['allowed_lateness_seconds']
        )
        self.gap_detector = GapDetector(
            expected_interval_minutes=config['flink']['expected_interval_minutes'],
            grace_period_seconds=config['flink']['grace_period_seconds']
        )
        self.state_manager: StateManager = None
    
    def open(self, runtime_context: RuntimeContext):
        """Initialize state and collectors."""
        self.state_manager = StateManager(
            runtime_context,
            interval_minutes=self.config['flink']['expected_interval_minutes']
        )
    
    def process_element(self, value: str, ctx: 'KeyedProcessFunction.Context', out):
        """
        Process each incoming event.
        
        Args:
            value: JSON string of the event
            ctx: Process context with timer service
            out: Collector for outputs
        """
        try:
            # Parse event
            event_dict = json.loads(value)
            event = SmartMeterEvent.from_dict(event_dict)
            meter_id = event['meter_id']
            event_time = event['timestamp']
            
            # Validate event
            is_valid, error_msg = self.validator.validate(event)
            if not is_valid:
                # Emit metric for invalid events
                metric = MetricsEvent.create(
                    "invalid_event",
                    meter_id,
                    datetime.utcnow(),
                    1.0,
                    {"error": error_msg}
                )
                out.collect(("metrics", MetricsEvent.to_json(metric)))
                return
            
            # Get current watermark
            watermark = ctx.timer_service().current_watermark()
            if watermark is not None:
                watermark_dt = datetime.fromtimestamp(watermark / 1000.0)
            else:
                watermark_dt = None
            
            # Classify event timing
            timing_class = self.late_handler.classify_event(event_time, watermark_dt)
            
            # Handle too-late events
            if timing_class == "TOO_LATE":
                delay = self.late_handler.calculate_delay(event_time, watermark_dt)
                late_event = LateEvent.create(
                    meter_id,
                    event_time,
                    event['consumption_kwh'],
                    delay or 0
                )
                out.collect(("late_events", LateEvent.to_json(late_event)))
                
                # Update metrics
                self.state_manager.increment_late_count()
                metric = MetricsEvent.create(
                    "too_late_event",
                    meter_id,
                    datetime.utcnow(),
                    1.0
                )
                out.collect(("metrics", MetricsEvent.to_json(metric)))
                return
            
            # Get current state
            current_state = self.state_manager.get_state()
            
            # Detect gaps before this event
            if current_state and current_state.last_seen:
                gap_info = self.gap_detector.detect_gap(
                    event_time,
                    current_state.last_seen,
                    current_state.interval_minutes
                )
                
                if gap_info:
                    # Emit gap alert
                    gap_alert = GapAlert.create(
                        meter_id,
                        gap_info['missing_from'],
                        gap_info['missing_to'],
                        gap_info['gap_minutes']
                    )
                    out.collect(("gap_alerts", GapAlert.to_json(gap_alert)))
                    
                    # Update state
                    self.state_manager.increment_gap_count()
                    
                    # Emit metric
                    metric = MetricsEvent.create(
                        "gap_detected",
                        meter_id,
                        datetime.utcnow(),
                        gap_info['gap_minutes']
                    )
                    out.collect(("metrics", MetricsEvent.to_json(metric)))
            
            # Update state with new event
            updated_state = self.state_manager.update_with_event(
                event_time,
                self.config['flink']['expected_interval_minutes']
            )
            
            # Register timer for next expected event
            if updated_state.expected_next:
                timer_time = self.gap_detector.calculate_timer_time(
                    updated_state.expected_next
                )
                timer_timestamp = int(timer_time.timestamp() * 1000)
                ctx.timer_service().register_event_time_timer(timer_timestamp)
            
            # Emit validated reading
            status = "LATE" if timing_class == "LATE" else "OK"
            validated = ValidatedReading.create(
                meter_id,
                event_time,
                event['consumption_kwh'],
                status
            )
            out.collect(("validated", ValidatedReading.to_json(validated)))
            
            # Emit processing metrics
            metric = MetricsEvent.create(
                "event_processed",
                meter_id,
                datetime.utcnow(),
                1.0,
                {"status": status}
            )
            out.collect(("metrics", MetricsEvent.to_json(metric)))
            
        except Exception as e:
            # Emit error metric
            metric = MetricsEvent.create(
                "processing_error",
                "unknown",
                datetime.utcnow(),
                1.0,
                {"error": str(e)}
            )
            out.collect(("metrics", MetricsEvent.to_json(metric)))
    
    def on_timer(self, timestamp: int, ctx: 'KeyedProcessFunction.OnTimerContext', out):
        """
        Called when an event-time timer fires.
        This indicates a missing event.
        """
        timer_time = datetime.fromtimestamp(timestamp / 1000.0)
        current_state = self.state_manager.get_state()
        
        if current_state and current_state.expected_next:
            # Check if event arrived after timer was set but before it fired
            if current_state.last_seen and current_state.last_seen >= current_state.expected_next:
                # Event arrived, no gap
                return
            
            # Timer fired without event - gap detected
            meter_id = ctx.get_current_key()
            
            # Calculate gap
            gap_start = current_state.expected_next
            gap_end = timer_time - timedelta(seconds=self.config['flink']['grace_period_seconds'])
            
            if gap_end > gap_start:
                gap_minutes = int((gap_end - gap_start).total_seconds() / 60)
                
                gap_alert = GapAlert.create(
                    meter_id,
                    gap_start,
                    gap_end,
                    gap_minutes
                )
                out.collect(("gap_alerts", GapAlert.to_json(gap_alert)))
                
                # Update state
                self.state_manager.increment_gap_count()
                
                # Update expected next to after the gap
                interval = timedelta(minutes=current_state.interval_minutes)
                new_expected = gap_end + interval
                current_state.expected_next = new_expected
                self.state_manager.update_state(current_state)
                
                # Register new timer
                next_timer_time = self.gap_detector.calculate_timer_time(new_expected)
                next_timer_ts = int(next_timer_time.timestamp() * 1000)
                ctx.timer_service().register_event_time_timer(next_timer_ts)
                
                # Emit metric
                metric = MetricsEvent.create(
                    "gap_detected_timer",
                    meter_id,
                    datetime.utcnow(),
                    gap_minutes
                )
                out.collect(("metrics", MetricsEvent.to_json(metric)))


def create_flink_job(config: dict):
    """Create and configure the Flink job."""
    env = StreamExecutionEnvironment.get_execution_environment()
    
    # Set parallelism
    env.set_parallelism(config['flink']['parallelism'])
    
    # Enable checkpointing
    # In PyFlink 1.18, exactly-once is the default when checkpointing is enabled
    # The mode is configured via Flink properties in docker-compose.yml
    env.enable_checkpointing(config['flink']['checkpoint_interval_ms'])
    
    # Get checkpoint config and ensure exactly-once mode
    checkpoint_config = env.get_checkpoint_config()
    # The mode is already set to EXACTLY_ONCE via docker-compose environment
    # But we can verify it's enabled
    checkpoint_config.set_min_pause_between_checkpoints(500)
    checkpoint_config.set_checkpoint_timeout(600000)
    checkpoint_config.set_max_concurrent_checkpoints(1)
    
    # Configure Kafka consumer
    kafka_consumer = FlinkKafkaConsumer(
        topics=config['kafka']['topics']['raw'],
        deserialization_schema=SimpleStringSchema(),
        properties={
            'bootstrap.servers': config['kafka']['bootstrap_servers'],
            'group.id': config['kafka']['consumer_group'],
            'auto.offset.reset': 'earliest'
        }
    )
    
    # Create stream from Kafka
    # Note: PyFlink 1.18 DataStream API has limited watermark support
    # We'll process events and extract timestamps in the processing function
    stream = env.add_source(kafka_consumer)
    
    # Key by meter_id and process
    keyed_stream = stream.key_by(lambda x: json.loads(x)['meter_id'])
    
    # Process with our function
    processed_stream = keyed_stream.process(
        SmartMeterProcessingFunction(config)
    )
    
    # Split stream by output type
    validated_stream = processed_stream.filter(lambda x: x[0] == "validated")
    gap_alerts_stream = processed_stream.filter(lambda x: x[0] == "gap_alerts")
    late_events_stream = processed_stream.filter(lambda x: x[0] == "late_events")
    metrics_stream = processed_stream.filter(lambda x: x[0] == "metrics")
    
    # Create Kafka producers
    validated_producer = FlinkKafkaProducer(
        topic=config['kafka']['topics']['validated'],
        serialization_schema=SimpleStringSchema(),
        producer_config={
            'bootstrap.servers': config['kafka']['bootstrap_servers']
        }
    )
    
    gap_alerts_producer = FlinkKafkaProducer(
        topic=config['kafka']['topics']['gap_alerts'],
        serialization_schema=SimpleStringSchema(),
        producer_config={
            'bootstrap.servers': config['kafka']['bootstrap_servers']
        }
    )
    
    late_events_producer = FlinkKafkaProducer(
        topic=config['kafka']['topics']['late_events'],
        serialization_schema=SimpleStringSchema(),
        producer_config={
            'bootstrap.servers': config['kafka']['bootstrap_servers']
        }
    )
    
    metrics_producer = FlinkKafkaProducer(
        topic=config['kafka']['topics']['metrics'],
        serialization_schema=SimpleStringSchema(),
        producer_config={
            'bootstrap.servers': config['kafka']['bootstrap_servers']
        }
    )
    
    # Sink to Kafka
    validated_stream.map(lambda x: x[1]).add_sink(validated_producer)
    gap_alerts_stream.map(lambda x: x[1]).add_sink(gap_alerts_producer)
    late_events_stream.map(lambda x: x[1]).add_sink(late_events_producer)
    metrics_stream.map(lambda x: x[1]).add_sink(metrics_producer)
    
    return env


if __name__ == "__main__":
    import yaml
    
    # Load config - try Flink-specific config first, fall back to regular config
    import os
    config_path = '/opt/flink/usrlib/config/config.flink.yaml'
    if not os.path.exists(config_path):
        config_path = '/opt/flink/usrlib/config/config.yaml'
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Create and execute job
    env = create_flink_job(config)
    env.execute("Smart Meter Data Quality Monitoring")

