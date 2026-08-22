"""Scheduling logic for monitoring within configured time windows."""
import logging
from datetime import datetime, time
from typing import Callable, Optional
import pytz
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)


class MonitorScheduler:
    """Manages monitoring schedule with timezone-aware time windows."""
    
    def __init__(
        self,
        timezone: str = "Africa/Lagos",
        start_time: str = "18:00",
        end_time: str = "23:00",
        interval_seconds: int = 60,
    ):
        """Initialize the scheduler.
        
        Args:
            timezone: Timezone string (e.g., 'Africa/Lagos')
            start_time: Start time in HH:MM format
            end_time: End time in HH:MM format
            interval_seconds: Polling interval in seconds
        """
        self.timezone = ZoneInfo(timezone)
        self.interval_seconds = interval_seconds
        
        try:
            start_parts = start_time.split(":")
            end_parts = end_time.split(":")
            
            self.start_time = time(
                hour=int(start_parts[0]),
                minute=int(start_parts[1]) if len(start_parts) > 1 else 0,
            )
            self.end_time = time(
                hour=int(end_parts[0]),
                minute=int(end_parts[1]) if len(end_parts) > 1 else 0,
            )
        except (ValueError, IndexError) as e:
            logger.error(f"Invalid time format: {e}")
            raise
        
        logger.info(
            f"Scheduler initialized: {start_time}-{end_time} {timezone}, "
            f"polling every {interval_seconds}s"
        )
    
    def is_monitoring_time(self, dt: Optional[datetime] = None) -> bool:
        """Check if current time falls within monitoring window.
        
        Args:
            dt: Datetime to check (uses current time if None)
            
        Returns:
            True if within monitoring window
        """
        if dt is None:
            dt = datetime.now(self.timezone)
        else:
            # Convert to target timezone if naive
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=self.timezone)
            else:
                dt = dt.astimezone(self.timezone)
        
        current_time = dt.time()
        
        # Handle case where end_time is before start_time (spans midnight)
        if self.start_time <= self.end_time:
            is_within = self.start_time <= current_time < self.end_time
        else:
            is_within = current_time >= self.start_time or current_time < self.end_time
        
        return is_within
    
    def get_seconds_until_monitoring(self, dt: Optional[datetime] = None) -> int:
        """Get seconds until monitoring window starts.
        
        Args:
            dt: Datetime to calculate from (uses current time if None)
            
        Returns:
            Seconds until monitoring starts, or 0 if monitoring is active
        """
        if dt is None:
            dt = datetime.now(self.timezone)
        else:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=self.timezone)
            else:
                dt = dt.astimezone(self.timezone)
        
        if self.is_monitoring_time(dt):
            return 0
        
        current_time = dt.time()
        current_datetime = dt
        
        # Create a datetime for start_time today
        start_datetime = current_datetime.replace(
            hour=self.start_time.hour,
            minute=self.start_time.minute,
            second=0,
            microsecond=0,
        )
        
        if start_datetime > current_datetime:
            # Start time is later today
            delta = start_datetime - current_datetime
        else:
            # Start time is tomorrow
            from datetime import timedelta
            start_datetime = start_datetime + timedelta(days=1)
            delta = start_datetime - current_datetime
        
        return int(delta.total_seconds())
    
    def log_schedule_status(self):
        """Log the current schedule status."""
        now = datetime.now(self.timezone)
        is_monitoring = self.is_monitoring_time(now)
        seconds_until = self.get_seconds_until_monitoring(now)
        
        status = "ACTIVE" if is_monitoring else "INACTIVE"
        logger.info(
            f"Schedule Status: {status} | Current time: {now.strftime('%Y-%m-%d %H:%M:%S %Z')} | "
            f"Monitoring window: {self.start_time}-{self.end_time} | "
            f"Seconds until monitoring: {seconds_until if not is_monitoring else 'monitoring active'}"
        )
