"""
State management utilities for Flink keyed state.
"""
from typing import Optional
from datetime import datetime, timedelta
from pyflink.datastream.state import ValueStateDescriptor, ValueState
from pyflink.common.typeinfo import Types
from pyflink.datastream import RuntimeContext


class MeterState:
    """State maintained per meter."""
    
    def __init__(self, last_seen: Optional[datetime] = None,
                 expected_next: Optional[datetime] = None,
                 interval_minutes: int = 30,
                 gap_count: int = 0,
                 late_count: int = 0):
        self.last_seen = last_seen
        self.expected_next = expected_next
        self.interval_minutes = interval_minutes
        self.gap_count = gap_count
        self.late_count = late_count
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'expected_next': self.expected_next.isoformat() if self.expected_next else None,
            'interval_minutes': self.interval_minutes,
            'gap_count': self.gap_count,
            'late_count': self.late_count
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MeterState':
        """Deserialize from dictionary."""
        return cls(
            last_seen=datetime.fromisoformat(data['last_seen']) if data.get('last_seen') else None,
            expected_next=datetime.fromisoformat(data['expected_next']) if data.get('expected_next') else None,
            interval_minutes=data.get('interval_minutes', 30),
            gap_count=data.get('gap_count', 0),
            late_count=data.get('late_count', 0)
        )


class StateManager:
    """Manages keyed state for meters."""
    
    def __init__(self, runtime_context: RuntimeContext, interval_minutes: int = 30):
        self.interval_minutes = interval_minutes
        self.state_descriptor = ValueStateDescriptor(
            "meter_state",
            Types.PICKLED_BYTE_ARRAY()
        )
        self.state: ValueState = runtime_context.get_state(self.state_descriptor)
    
    def get_state(self) -> Optional[MeterState]:
        """Get current state for the key."""
        state_bytes = self.state.value()
        if state_bytes is None:
            return None
        import pickle
        state_dict = pickle.loads(state_bytes)
        return MeterState.from_dict(state_dict)
    
    def update_state(self, meter_state: MeterState):
        """Update state for the key."""
        import pickle
        state_bytes = pickle.dumps(meter_state.to_dict())
        self.state.update(state_bytes)
    
    def update_with_event(self, event_time: datetime, interval_minutes: Optional[int] = None):
        """Update state with a new event."""
        current_state = self.get_state() or MeterState(interval_minutes=self.interval_minutes)
        
        if interval_minutes:
            current_state.interval_minutes = interval_minutes
        
        # Calculate expected next time
        if current_state.last_seen:
            interval = timedelta(minutes=current_state.interval_minutes)
            current_state.expected_next = current_state.last_seen + interval
        else:
            # First event for this meter
            interval = timedelta(minutes=current_state.interval_minutes)
            current_state.expected_next = event_time + interval
        
        current_state.last_seen = event_time
        self.update_state(current_state)
        return current_state
    
    def increment_gap_count(self):
        """Increment gap counter."""
        state = self.get_state() or MeterState(interval_minutes=self.interval_minutes)
        state.gap_count += 1
        self.update_state(state)
    
    def increment_late_count(self):
        """Increment late event counter."""
        state = self.get_state() or MeterState(interval_minutes=self.interval_minutes)
        state.late_count += 1
        self.update_state(state)

