"""
Validates incoming smart meter events.
"""
from typing import Dict, Any
from datetime import datetime


class EventValidator:
    """Validates smart meter events."""
    
    @staticmethod
    def validate(event: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate event structure and values.
        
        Returns:
            (is_valid, error_message)
        """
        required_fields = ['meter_id', 'timestamp', 'consumption_kwh']
        
        for field in required_fields:
            if field not in event:
                return False, f"Missing required field: {field}"
        
        # Validate meter_id
        if not event['meter_id'] or not isinstance(event['meter_id'], str):
            return False, "Invalid meter_id"
        
        # Validate timestamp
        if not isinstance(event['timestamp'], datetime):
            return False, "Invalid timestamp type"
        
        # Validate consumption
        try:
            consumption = float(event['consumption_kwh'])
            if consumption < 0:
                return False, "Consumption cannot be negative"
            if consumption > 100000:  # Reasonable upper bound
                return False, "Consumption value too large"
        except (ValueError, TypeError):
            return False, "Invalid consumption_kwh value"
        
        return True, "OK"

