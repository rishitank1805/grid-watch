"""
Handles late arriving events.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


class LateEventHandler:
    """Classifies and handles late events."""
    
    def __init__(self, allowed_lateness_seconds: int = 3600):
        self.allowed_lateness_seconds = allowed_lateness_seconds
    
    def classify_event(self, event_time: datetime, watermark: datetime) -> str:
        """
        Classify event timing.
        
        Returns:
            "ON_TIME", "LATE", or "TOO_LATE"
        """
        if watermark is None:
            return "ON_TIME"
        
        delay_seconds = (watermark - event_time).total_seconds()
        
        if delay_seconds <= 0:
            return "ON_TIME"
        elif delay_seconds <= self.allowed_lateness_seconds:
            return "LATE"
        else:
            return "TOO_LATE"
    
    def calculate_delay(self, event_time: datetime, watermark: datetime) -> Optional[int]:
        """Calculate delay in seconds."""
        if watermark is None:
            return None
        delay = (watermark - event_time).total_seconds()
        return int(delay) if delay > 0 else None

