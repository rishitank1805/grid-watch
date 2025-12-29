"""
Database connection and utilities for TimescaleDB.
"""
import logging
from typing import Dict, Any, Optional
import psycopg
import json

# Try to import pool - psycopg3 uses psycopg_pool as a separate package
try:
    from psycopg_pool import ConnectionPool
except ImportError:
    try:
        from psycopg.pool import ConnectionPool
    except ImportError:
        raise ImportError(
            "psycopg pool not available. Install with: pip install 'psycopg[binary,pool]'"
        )


class DatabaseConnection:
    """Manages database connections and operations."""
    
    def __init__(self, config: dict):
        """
        Initialize database connection pool.
        
        Args:
            config: Database configuration dictionary
        """
        self.config = config
        self.pool: Optional[ConnectionPool] = None
        self.logger = logging.getLogger(__name__)
    
    def connect(self):
        """Create connection pool."""
        try:
            conninfo = f"host={self.config['host']} port={self.config['port']} dbname={self.config['database']} user={self.config['user']} password={self.config['password']}"
            self.pool = ConnectionPool(
                conninfo=conninfo,
                min_size=1,
                max_size=self.config.get('pool_size', 10)
            )
            self.logger.info("Database connection pool created")
        except Exception as e:
            self.logger.error(f"Failed to create connection pool: {e}")
            raise
    
    def close(self):
        """Close all connections in pool."""
        if self.pool:
            self.pool.close()
            self.logger.info("Database connection pool closed")
    
    def insert_validated_reading(self, reading: Dict[str, Any]):
        """Insert validated reading."""
        if self.pool is None:
            self.connect()
        try:
            with self.pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO validated_readings (time, meter_id, consumption_kwh, status)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (time, meter_id) DO UPDATE
                        SET consumption_kwh = EXCLUDED.consumption_kwh,
                            status = EXCLUDED.status
                        """,
                        (
                            reading['timestamp'],
                            reading['meter_id'],
                            reading['consumption_kwh'],
                            reading['status']
                        )
                    )
                    conn.commit()
        except Exception as e:
            self.logger.error(f"Error inserting validated reading: {e}")
            raise
    
    def insert_gap_alert(self, alert: Dict[str, Any]):
        """Insert gap alert."""
        if self.pool is None:
            self.connect()
        try:
            with self.pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO gap_alerts (time, meter_id, missing_from, missing_to, gap_minutes)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (time, meter_id, missing_from) DO NOTHING
                        """,
                        (
                            alert.get('timestamp') or alert.get('missing_from'),
                            alert['meter_id'],
                            alert['missing_from'],
                            alert['missing_to'],
                            alert['gap_minutes']
                        )
                    )
                    conn.commit()
        except Exception as e:
            self.logger.error(f"Error inserting gap alert: {e}")
            raise
    
    def insert_late_event(self, event: Dict[str, Any]):
        """Insert late event."""
        if self.pool is None:
            self.connect()
        try:
            with self.pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO late_events (time, meter_id, event_timestamp, consumption_kwh, delay_seconds)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (time, meter_id, event_timestamp) DO NOTHING
                        """,
                        (
                            event.get('timestamp') or event.get('event_timestamp'),
                            event['meter_id'],
                            event['timestamp'],
                            event['consumption_kwh'],
                            event['delay_seconds']
                        )
                    )
                    conn.commit()
        except Exception as e:
            self.logger.error(f"Error inserting late event: {e}")
            raise
    
    def insert_metric(self, metric: Dict[str, Any]):
        """Insert metric."""
        if self.pool is None:
            self.connect()
        try:
            with self.pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO metrics (time, metric_type, meter_id, value, tags)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            metric['timestamp'],
                            metric['metric_type'],
                            metric.get('meter_id'),
                            metric['value'],
                            json.dumps(metric.get('tags', {}))
                        )
                    )
                    conn.commit()
        except Exception as e:
            self.logger.error(f"Error inserting metric: {e}")
            raise

