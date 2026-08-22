"""Database management for tracking tweets and vouchers."""
import sqlite3
import logging
from datetime import datetime
from typing import Optional, List, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class ChowdeckDatabase:
    """SQLite database for tracking processed tweets and vouchers."""
    
    def __init__(self, db_path: str = "chowdeck_monitor.db"):
        """Initialize database connection.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Processed tweets table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processed_tweets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tweet_id TEXT UNIQUE NOT NULL,
                    tweet_text TEXT NOT NULL,
                    tweet_url TEXT NOT NULL,
                    author TEXT NOT NULL,
                    discovered_at TIMESTAMP NOT NULL,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pending'  -- pending, voucher_found, no_voucher, error
                )
            """)
            
            # Vouchers table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vouchers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    tweet_id TEXT NOT NULL,
                    discovered_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notification_sent BOOLEAN DEFAULT 0,
                    notification_sent_at TIMESTAMP,
                    redeemed BOOLEAN DEFAULT 0,
                    redeemed_at TIMESTAMP,
                    FOREIGN KEY (tweet_id) REFERENCES processed_tweets(tweet_id)
                )
            """)
            
            # Notifications table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    voucher_code TEXT NOT NULL,
                    telegram_message_id TEXT,
                    status TEXT DEFAULT 'pending',  -- pending, sent, failed
                    sent_at TIMESTAMP,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (voucher_code) REFERENCES vouchers(code)
                )
            """)
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweet_id ON processed_tweets(tweet_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_voucher_code ON vouchers(code)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_notification_status ON notifications(status)")
            
            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")
    
    def tweet_exists(self, tweet_id: str) -> bool:
        """Check if a tweet has already been processed.
        
        Args:
            tweet_id: The X/Twitter tweet ID
            
        Returns:
            True if tweet exists in database
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM processed_tweets WHERE tweet_id = ?", (tweet_id,))
            return cursor.fetchone() is not None
    
    def voucher_exists(self, code: str) -> bool:
        """Check if a voucher code has already been processed.
        
        Args:
            code: The voucher code
            
        Returns:
            True if voucher exists in database
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM vouchers WHERE code = ?", (code,))
            return cursor.fetchone() is not None
    
    def add_tweet(
        self,
        tweet_id: str,
        tweet_text: str,
        tweet_url: str,
        author: str,
        discovered_at: datetime,
    ) -> bool:
        """Add a processed tweet to the database.
        
        Args:
            tweet_id: The X/Twitter tweet ID
            tweet_text: Full tweet text
            tweet_url: URL to the tweet
            author: Tweet author (should be @lordbinary_)
            discovered_at: When the tweet was discovered
            
        Returns:
            True if insertion was successful
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO processed_tweets 
                    (tweet_id, tweet_text, tweet_url, author, discovered_at, status)
                    VALUES (?, ?, ?, ?, ?, 'pending')
                    """,
                    (tweet_id, tweet_text, tweet_url, author, discovered_at),
                )
                conn.commit()
                logger.info(f"Added tweet {tweet_id} to database")
                return True
        except sqlite3.IntegrityError:
            logger.warning(f"Tweet {tweet_id} already exists in database")
            return False
    
    def add_voucher(
        self,
        code: str,
        tweet_id: str,
        discovered_at: datetime,
    ) -> bool:
        """Add a voucher code to the database.
        
        Args:
            code: The voucher code
            tweet_id: Associated tweet ID
            discovered_at: When the voucher was discovered
            
        Returns:
            True if insertion was successful
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO vouchers 
                    (code, tweet_id, discovered_at, notification_sent)
                    VALUES (?, ?, ?, 0)
                    """,
                    (code, tweet_id, discovered_at),
                )
                conn.commit()
                logger.info(f"Added voucher {code} to database")
                return True
        except sqlite3.IntegrityError:
            logger.warning(f"Voucher {code} already exists in database")
            return False
    
    def add_notification(
        self,
        voucher_code: str,
        status: str = "pending",
        message_id: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> int:
        """Add a notification record.
        
        Args:
            voucher_code: Associated voucher code
            status: Notification status (pending, sent, failed)
            message_id: Telegram message ID if sent
            error_message: Error details if failed
            
        Returns:
            Notification record ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO notifications 
                (voucher_code, status, telegram_message_id, error_message)
                VALUES (?, ?, ?, ?)
                """,
                (voucher_code, status, message_id, error_message),
            )
            conn.commit()
            notification_id = cursor.lastrowid
            logger.info(f"Added notification record {notification_id} for voucher {voucher_code}")
            return notification_id
    
    def mark_notification_sent(
        self,
        notification_id: int,
        message_id: Optional[str] = None,
    ):
        """Mark a notification as sent.
        
        Args:
            notification_id: The notification record ID
            message_id: Telegram message ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE notifications
                SET status = 'sent', sent_at = CURRENT_TIMESTAMP, 
                    telegram_message_id = ?
                WHERE id = ?
                """,
                (message_id, notification_id),
            )
            conn.commit()
            logger.info(f"Marked notification {notification_id} as sent")
    
    def mark_notification_failed(
        self,
        notification_id: int,
        error_message: str,
    ):
        """Mark a notification as failed.
        
        Args:
            notification_id: The notification record ID
            error_message: Error details
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE notifications
                SET status = 'failed', sent_at = CURRENT_TIMESTAMP, 
                    error_message = ?
                WHERE id = ?
                """,
                (error_message, notification_id),
            )
            conn.commit()
            logger.warning(f"Marked notification {notification_id} as failed: {error_message}")
    
    def get_pending_notifications(self) -> List[Tuple]:
        """Get all pending notifications.
        
        Returns:
            List of (notification_id, voucher_code) tuples
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, voucher_code FROM notifications WHERE status = 'pending'"
            )
            return cursor.fetchall()
    
    def get_unprocessed_tweets(self) -> List[Tuple]:
        """Get all unprocessed tweets.
        
        Returns:
            List of tweet data tuples
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT tweet_id, tweet_text, tweet_url, discovered_at FROM processed_tweets WHERE status = 'pending'"
            )
            return cursor.fetchall()
    
    def close(self):
        """Close database connection."""
        pass  # SQLite connections are managed per operation
