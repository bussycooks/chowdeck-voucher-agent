"""Tests for scheduler module."""
import pytest
from datetime import datetime, time
from zoneinfo import ZoneInfo
from app.scheduler import MonitorScheduler


class TestMonitorScheduler:
    """Test scheduling logic."""

    def test_scheduler_initialization(self):
        """Test scheduler initialization."""
        scheduler = MonitorScheduler(
            timezone="Africa/Lagos",
            start_time="18:00",
            end_time="23:00",
            interval_seconds=60,
        )
        
        assert scheduler.start_time == time(18, 0)
        assert scheduler.end_time == time(23, 0)
        assert scheduler.interval_seconds == 60

    def test_monitoring_time_within_window(self):
        """Test detection of monitoring time within window."""
        scheduler = MonitorScheduler(
            timezone="UTC",
            start_time="18:00",
            end_time="23:00",
        )
        
        # Create a datetime within the window
        tz = ZoneInfo("UTC")
        test_time = datetime(2024, 1, 1, 20, 30, tzinfo=tz)
        
        assert scheduler.is_monitoring_time(test_time) is True

    def test_monitoring_time_outside_window(self):
        """Test detection of monitoring time outside window."""
        scheduler = MonitorScheduler(
            timezone="UTC",
            start_time="18:00",
            end_time="23:00",
        )
        
        # Create a datetime outside the window
        tz = ZoneInfo("UTC")
        test_time = datetime(2024, 1, 1, 10, 30, tzinfo=tz)
        
        assert scheduler.is_monitoring_time(test_time) is False

    def test_monitoring_time_at_start(self):
        """Test monitoring time exactly at start."""
        scheduler = MonitorScheduler(
            timezone="UTC",
            start_time="18:00",
            end_time="23:00",
        )
        
        tz = ZoneInfo("UTC")
        test_time = datetime(2024, 1, 1, 18, 0, tzinfo=tz)
        
        assert scheduler.is_monitoring_time(test_time) is True

    def test_monitoring_time_just_before_end(self):
        """Test monitoring time just before end."""
        scheduler = MonitorScheduler(
            timezone="UTC",
            start_time="18:00",
            end_time="23:00",
        )
        
        tz = ZoneInfo("UTC")
        test_time = datetime(2024, 1, 1, 22, 59, tzinfo=tz)
        
        assert scheduler.is_monitoring_time(test_time) is True

    def test_monitoring_time_at_end(self):
        """Test monitoring time at end (should be outside)."""
        scheduler = MonitorScheduler(
            timezone="UTC",
            start_time="18:00",
            end_time="23:00",
        )
        
        tz = ZoneInfo("UTC")
        test_time = datetime(2024, 1, 1, 23, 0, tzinfo=tz)
        
        assert scheduler.is_monitoring_time(test_time) is False

    def test_monitoring_across_midnight(self):
        """Test monitoring window that spans midnight."""
        scheduler = MonitorScheduler(
            timezone="UTC",
            start_time="22:00",
            end_time="02:00",
        )
        
        tz = ZoneInfo("UTC")
        
        # Before midnight - should be in window
        test_time_1 = datetime(2024, 1, 1, 23, 0, tzinfo=tz)
        assert scheduler.is_monitoring_time(test_time_1) is True
        
        # After midnight - should be in window
        test_time_2 = datetime(2024, 1, 2, 1, 0, tzinfo=tz)
        assert scheduler.is_monitoring_time(test_time_2) is True
        
        # Middle of day - should be outside
        test_time_3 = datetime(2024, 1, 2, 12, 0, tzinfo=tz)
        assert scheduler.is_monitoring_time(test_time_3) is False

    def test_get_seconds_until_monitoring(self):
        """Test calculation of seconds until monitoring starts."""
        scheduler = MonitorScheduler(
            timezone="UTC",
            start_time="20:00",
            end_time="23:00",
        )
        
        tz = ZoneInfo("UTC")
        # At 10:00, next monitoring is at 20:00 (10 hours away)
        test_time = datetime(2024, 1, 1, 10, 0, tzinfo=tz)
        seconds_until = scheduler.get_seconds_until_monitoring(test_time)
        
        # Should be around 10 hours = 36000 seconds
        assert 35900 < seconds_until < 36100

    def test_get_seconds_until_monitoring_already_active(self):
        """Test seconds calculation when monitoring is active."""
        scheduler = MonitorScheduler(
            timezone="UTC",
            start_time="18:00",
            end_time="23:00",
        )
        
        tz = ZoneInfo("UTC")
        test_time = datetime(2024, 1, 1, 20, 0, tzinfo=tz)
        seconds_until = scheduler.get_seconds_until_monitoring(test_time)
        
        # Should be 0 when monitoring is active
        assert seconds_until == 0

    def test_invalid_start_time_format(self):
        """Test that invalid time format raises error."""
        with pytest.raises(ValueError):
            MonitorScheduler(
                timezone="UTC",
                start_time="invalid",
                end_time="23:00",
            )

    def test_timezone_conversion(self):
        """Test timezone conversion."""
        scheduler = MonitorScheduler(
            timezone="Africa/Lagos",
            start_time="18:00",
            end_time="23:00",
        )
        
        # Create UTC time
        tz_utc = ZoneInfo("UTC")
        tz_lagos = ZoneInfo("Africa/Lagos")
        
        # 18:00 Lagos time = 17:00 UTC
        test_time_utc = datetime(2024, 1, 1, 17, 30, tzinfo=tz_utc)
        
        # Should be within window when converted to Lagos time
        assert scheduler.is_monitoring_time(test_time_utc) is True
