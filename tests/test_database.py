"""Tests for database module."""
import pytest
import sqlite3
from pathlib import Path
from datetime import datetime
from app.database import ChowdeckDatabase


class TestChowdeckDatabase:
    """Test database operations."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create a temporary test database."""
        db_path = str(tmp_path / "test.db")
        database = ChowdeckDatabase(db_path)
        yield database
        # Cleanup
        try:
            Path(db_path).unlink()
        except:
            pass

    def test_database_initialization(self, db):
        """Test that database initializes with correct tables."""
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        # Check tables exist
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = [row[0] for row in cursor.fetchall()]
        
        assert "processed_tweets" in tables
        assert "vouchers" in tables
        assert "notifications" in tables
        
        conn.close()

    def test_add_tweet(self, db):
        """Test adding a tweet to the database."""
        success = db.add_tweet(
            tweet_id="12345",
            tweet_text="Check out this voucher code PROMO50",
            tweet_url="https://twitter.com/user/status/12345",
            author="@lordbinary_",
            discovered_at=datetime.now(),
        )
        
        assert success is True

    def test_tweet_exists(self, db):
        """Test checking if a tweet exists."""
        tweet_id = "12345"
        
        # Initially should not exist
        assert db.tweet_exists(tweet_id) is False
        
        # Add tweet
        db.add_tweet(
            tweet_id=tweet_id,
            tweet_text="Test",
            tweet_url="https://twitter.com/user/status/12345",
            author="@lordbinary_",
            discovered_at=datetime.now(),
        )
        
        # Now should exist
        assert db.tweet_exists(tweet_id) is True

    def test_duplicate_tweet_not_added(self, db):
        """Test that duplicate tweets are not added."""
        tweet_id = "12345"
        now = datetime.now()
        
        # Add first time
        success1 = db.add_tweet(
            tweet_id=tweet_id,
            tweet_text="Test",
            tweet_url="https://twitter.com/user/status/12345",
            author="@lordbinary_",
            discovered_at=now,
        )
        assert success1 is True
        
        # Try to add duplicate
        success2 = db.add_tweet(
            tweet_id=tweet_id,
            tweet_text="Test",
            tweet_url="https://twitter.com/user/status/12345",
            author="@lordbinary_",
            discovered_at=now,
        )
        assert success2 is False

    def test_add_voucher(self, db):
        """Test adding a voucher to the database."""
        now = datetime.now()
        success = db.add_voucher(
            code="PROMO50",
            tweet_id="12345",
            discovered_at=now,
        )
        
        assert success is True

    def test_voucher_exists(self, db):
        """Test checking if a voucher exists."""
        voucher_code = "PROMO50"
        now = datetime.now()
        
        # Initially should not exist
        assert db.voucher_exists(voucher_code) is False
        
        # Add voucher
        db.add_voucher(
            code=voucher_code,
            tweet_id="12345",
            discovered_at=now,
        )
        
        # Now should exist
        assert db.voucher_exists(voucher_code) is True

    def test_duplicate_voucher_not_added(self, db):
        """Test that duplicate vouchers are not added."""
        code = "PROMO50"
        now = datetime.now()
        
        # Add first time
        success1 = db.add_voucher(
            code=code,
            tweet_id="12345",
            discovered_at=now,
        )
        assert success1 is True
        
        # Try to add duplicate
        success2 = db.add_voucher(
            code=code,
            tweet_id="12346",
            discovered_at=now,
        )
        assert success2 is False

    def test_add_notification(self, db):
        """Test adding a notification."""
        notification_id = db.add_notification(
            voucher_code="PROMO50",
            status="pending",
        )
        
        assert isinstance(notification_id, int)
        assert notification_id > 0

    def test_mark_notification_sent(self, db):
        """Test marking a notification as sent."""
        notification_id = db.add_notification(
            voucher_code="PROMO50",
            status="pending",
        )
        
        db.mark_notification_sent(notification_id, message_id="67890")
        
        # Verify it's marked as sent
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT status, telegram_message_id FROM notifications WHERE id = ?",
            (notification_id,),
        )
        row = cursor.fetchone()
        conn.close()
        
        assert row[0] == "sent"
        assert row[1] == "67890"

    def test_mark_notification_failed(self, db):
        """Test marking a notification as failed."""
        notification_id = db.add_notification(
            voucher_code="PROMO50",
            status="pending",
        )
        
        error_msg = "Test error"
        db.mark_notification_failed(notification_id, error_msg)
        
        # Verify it's marked as failed
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT status, error_message FROM notifications WHERE id = ?",
            (notification_id,),
        )
        row = cursor.fetchone()
        conn.close()
        
        assert row[0] == "failed"
        assert row[1] == error_msg

    def test_get_pending_notifications(self, db):
        """Test retrieving pending notifications."""
        # Add some notifications
        id1 = db.add_notification("CODE1", status="pending")
        id2 = db.add_notification("CODE2", status="pending")
        id3 = db.add_notification("CODE3", status="sent")
        
        pending = db.get_pending_notifications()
        
        # Should only get pending ones
        assert len(pending) >= 2
        codes = [p[1] for p in pending]
        assert "CODE1" in codes
        assert "CODE2" in codes
        assert "CODE3" not in codes
