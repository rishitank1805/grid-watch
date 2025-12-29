"""
Schema definitions for smart meter events.
"""
from typing import Dict, Any
from datetime import datetime
import json


class SmartMeterEvent:
    """Raw smart meter reading event."""
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and validate raw event."""
        return {
            'meter_id': str(data['meter_id']),
            'timestamp': datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00')),
            'consumption_kwh': float(data['consumption_kwh'])
        }
    
    @staticmethod
    def to_json(data: Dict[str, Any]) -> str:
        """Serialize to JSON."""
        return json.dumps({
            'meter_id': data['meter_id'],
            'timestamp': data['timestamp'].isoformat(),
            'consumption_kwh': data['consumption_kwh']
        })


class ValidatedReading:
    """Validated meter reading with status."""
    
    @staticmethod
    def create(meter_id: str, timestamp: datetime, consumption_kwh: float, 
               status: str = "OK") -> Dict[str, Any]:
        """Create validated reading."""
        return {
            'meter_id': meter_id,
            'timestamp': timestamp,
            'consumption_kwh': consumption_kwh,
            'status': status
        }
    
    @staticmethod
    def to_json(data: Dict[str, Any]) -> str:
        """Serialize to JSON."""
        return json.dumps({
            'meter_id': data['meter_id'],
            'timestamp': data['timestamp'].isoformat(),
            'consumption_kwh': data['consumption_kwh'],
            'status': data['status']
        })


class GapAlert:
    """Alert for missing time intervals."""
    
    @staticmethod
    def create(meter_id: str, missing_from: datetime, missing_to: datetime,
               gap_minutes: int) -> Dict[str, Any]:
        """Create gap alert."""
        return {
            'meter_id': meter_id,
            'missing_from': missing_from,
            'missing_to': missing_to,
            'gap_minutes': gap_minutes
        }
    
    @staticmethod
    def to_json(data: Dict[str, Any]) -> str:
        """Serialize to JSON."""
        return json.dumps({
            'meter_id': data['meter_id'],
            'missing_from': data['missing_from'].isoformat(),
            'missing_to': data['missing_to'].isoformat(),
            'gap_minutes': data['gap_minutes']
        })


class LateEvent:
    """Late arriving event."""
    
    @staticmethod
    def create(meter_id: str, timestamp: datetime, consumption_kwh: float,
               delay_seconds: int) -> Dict[str, Any]:
        """Create late event record."""
        return {
            'meter_id': meter_id,
            'timestamp': timestamp,
            'consumption_kwh': consumption_kwh,
            'delay_seconds': delay_seconds
        }
    
    @staticmethod
    def to_json(data: Dict[str, Any]) -> str:
        """Serialize to JSON."""
        return json.dumps({
            'meter_id': data['meter_id'],
            'timestamp': data['timestamp'].isoformat(),
            'consumption_kwh': data['consumption_kwh'],
            'delay_seconds': data['delay_seconds']
        })


class MetricsEvent:
    """System and data quality metrics."""
    
    @staticmethod
    def create(metric_type: str, meter_id: str, timestamp: datetime,
               value: float, tags: Dict[str, str] = None) -> Dict[str, Any]:
        """Create metrics event."""
        return {
            'metric_type': metric_type,
            'meter_id': meter_id,
            'timestamp': timestamp,
            'value': value,
            'tags': tags or {}
        }
    
    @staticmethod
    def to_json(data: Dict[str, Any]) -> str:
        """Serialize to JSON."""
        return json.dumps({
            'metric_type': data['metric_type'],
            'meter_id': data['meter_id'],
            'timestamp': data['timestamp'].isoformat(),
            'value': data['value'],
            'tags': data.get('tags', {})
        })

