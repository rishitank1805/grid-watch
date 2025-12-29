"""
Detects missing time intervals using event-time timers.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


class GapDetector:
    """Detects gaps in time-series data."""
    
    def __init__(self, expected_interval_minutes: int = 30, 
                 grace_period_seconds: int = 900):
        self.expected_interval_minutes = expected_interval_minutes
        self.grace_period_seconds = grace_period_seconds
    
    def calculate_expected_next(self, current_time: datetime, 
                               interval_minutes: Optional[int] = None) -> datetime:
        """Calculate expected next event time."""
        interval = timedelta(minutes=interval_minutes or self.expected_interval_minutes)
        return current_time + interval
    
    def calculate_timer_time(self, expected_time: datetime) -> datetime:
        """Calculate when timer should fire (expected + grace period)."""
        grace = timedelta(seconds=self.grace_period_seconds)
        return expected_time + grace
    
    def detect_gap(self, current_time: datetime, last_seen: Optional[datetime],
                   interval_minutes: int) -> Optional[Dict[str, Any]]:
        """
        Detect if there's a gap between last_seen and current_time.
        
        Returns:
            Gap information dict if gap detected, None otherwise
        """
        if last_seen is None:
            return None
        
        expected_interval = timedelta(minutes=interval_minutes)
        actual_interval = current_time - last_seen
        
        # If actual interval is significantly larger than expected, there's a gap
        threshold = expected_interval * 1.5  # 50% tolerance
        
        if actual_interval > threshold:
            gap_minutes = int((actual_interval - expected_interval).total_seconds() / 60)
            if gap_minutes > 0:
                return {
                    'missing_from': last_seen + expected_interval,
                    'missing_to': current_time,
                    'gap_minutes': gap_minutes
                }
        
        return None
    
    def calculate_missing_intervals(self, from_time: datetime, to_time: datetime,
                                   interval_minutes: int) -> list[Dict[str, Any]]:
        """
        Calculate all missing intervals between from_time and to_time.
        
        Returns:
            List of gap dictionaries
        """
        gaps = []
        interval = timedelta(minutes=interval_minutes)
        current = from_time
        
        while current + interval < to_time:
            gap_start = current + interval
            gap_end = min(gap_start + interval, to_time)
            gap_minutes = int((gap_end - gap_start).total_seconds() / 60)
            
            if gap_minutes > 0:
                gaps.append({
                    'missing_from': gap_start,
                    'missing_to': gap_end,
                    'gap_minutes': gap_minutes
                })
            
            current = gap_end
        
        return gaps

