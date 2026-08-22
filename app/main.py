"""Main application entry point for Chowdeck Voucher Agent."""
import asyncio
import logging
import sys
from datetime import datetime
from typing import Optional

from app.config import get_settings
from app.database import ChowdeckDatabase
from app.notifications import TelegramNotifier
from app.scheduler import MonitorScheduler
from app.voucher_extractor import VoucherExtractor
from app.x_monitor import XMonitor
from app.chowdeck import ChowdeckBrowser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ChowdeckVoucherAgent:
    """Main agent for monitoring X and detecting Chowdeck vouchers."""

    def __init__(self):
        """Initialize the agent."""
        self.settings = get_settings()
        
        # Validate required configuration
        if not self.settings.validate_required_secrets():
            logger.error("Missing required configuration. Please check .env file.")
            sys.exit(1)
        
        # Initialize components
        self.db = ChowdeckDatabase(self.settings.database_path)
        self.x_monitor = XMonitor(self.settings.x_bearer_token)
        self.voucher_extractor = VoucherExtractor(
            min_length=self.settings.voucher_min_length,
            max_length=self.settings.voucher_max_length,
            pattern=self.settings.voucher_pattern,
        )
        self.notifier = TelegramNotifier(
            self.settings.telegram_bot_token,
            self.settings.telegram_chat_id,
        )
        self.scheduler = MonitorScheduler(
            timezone=self.settings.monitor_timezone,
            start_time=self.settings.monitor_start,
            end_time=self.settings.monitor_end,
            interval_seconds=self.settings.monitor_interval_seconds,
        )
        self.browser = ChowdeckBrowser(
            profile_path=self.settings.chowdeck_profile_path,
            headless=self.settings.chowdeck_browser_headless,
            timeout_ms=self.settings.chowdeck_timeout_ms,
        )
        
        self.running = False
        self.user_id: Optional[str] = None

    async def initialize(self):
        """Initialize agent components."""
        logger.info("Initializing Chowdeck Voucher Agent...")
        
        # Get user ID for @lordbinary_
        self.user_id = self.x_monitor.get_user_id(self.settings.x_username)
        if not self.user_id:
            logger.error(f"Could not find user ID for @{self.settings.x_username}")
            sys.exit(1)
        
        logger.info(f"Agent initialized. Monitoring @{self.settings.x_username}")

    async def monitor_once(self) -> bool:
        """Perform one monitoring cycle.
        
        Returns:
            True if monitoring completed successfully
        """
        try:
            if not self.user_id:
                logger.error("User ID not set")
                return False
            
            logger.info(f"Fetching recent tweets from @{self.settings.x_username}...")
            tweets = self.x_monitor.get_recent_tweets(self.user_id)
            
            if not tweets:
                logger.info("No new tweets found")
                return True
            
            logger.info(f"Processing {len(tweets)} tweets...")
            
            for tweet in tweets:
                await self._process_tweet(tweet)
            
            return True
            
        except Exception as e:
            logger.error(f"Error during monitoring cycle: {e}")
            return False

    async def _process_tweet(self, tweet: dict):
        """Process a single tweet.
        
        Args:
            tweet: Tweet data dictionary
        """
        try:
            tweet_id = tweet.get("id")
            tweet_text = tweet.get("text", "")
            
            if not tweet_id:
                logger.warning("Tweet has no ID")
                return
            
            # Check if we've already processed this tweet
            if self.db.tweet_exists(tweet_id):
                logger.debug(f"Tweet {tweet_id} already processed")
                return
            
            # Build tweet URL
            tweet_url = self.x_monitor.build_tweet_url(
                self.settings.x_username,
                tweet_id,
            )
            
            # Add tweet to database
            self.db.add_tweet(
                tweet_id=tweet_id,
                tweet_text=tweet_text,
                tweet_url=tweet_url,
                author=self.settings.x_username,
                discovered_at=datetime.now(),
            )
            
            # Extract vouchers from tweet
            vouchers = self.voucher_extractor.extract(tweet_text)
            
            if vouchers:
                logger.info(f"Found {len(vouchers)} potential voucher(s) in tweet {tweet_id}")
                
                for voucher_code in vouchers:
                    await self._process_voucher(
                        voucher_code,
                        tweet_id,
                        tweet_text,
                        tweet_url,
                    )
            else:
                logger.debug(f"No vouchers found in tweet {tweet_id}")
                
        except Exception as e:
            logger.error(f"Error processing tweet: {e}")

    async def _process_voucher(
        self,
        code: str,
        tweet_id: str,
        tweet_text: str,
        tweet_url: str,
    ):
        """Process a discovered voucher code.
        
        Args:
            code: Voucher code
            tweet_id: Source tweet ID
            tweet_text: Tweet text
            tweet_url: Tweet URL
        """
        try:
            # Check if voucher already processed
            if self.db.voucher_exists(code):
                logger.info(f"Voucher {code} already processed")
                return
            
            # Add voucher to database
            self.db.add_voucher(
                code=code,
                tweet_id=tweet_id,
                discovered_at=datetime.now(),
            )
            
            # Create notification record
            notification_id = self.db.add_notification(code, status="pending")
            
            # Send Telegram notification
            logger.info(f"Sending Telegram notification for voucher {code}...")
            message_id = self.notifier.send_voucher_notification(
                voucher_code=code,
                tweet_text=tweet_text,
                tweet_url=tweet_url,
                detected_time=datetime.now(),
            )
            
            if message_id:
                self.db.mark_notification_sent(notification_id, message_id)
                logger.info(f"Notification sent for voucher {code}")
            else:
                self.db.mark_notification_failed(
                    notification_id,
                    "Failed to send Telegram message",
                )
                logger.error(f"Failed to send notification for voucher {code}")
                
        except Exception as e:
            logger.error(f"Error processing voucher {code}: {e}")

    async def run(self):
        """Run the monitoring loop."""
        await self.initialize()
        self.running = True
        
        logger.info("Starting monitoring loop...")
        self.scheduler.log_schedule_status()
        
        try:
            while self.running:
                # Check if we're in the monitoring window
                if self.scheduler.is_monitoring_time():
                    await self.monitor_once()
                    
                    # Wait before next poll
                    logger.debug(
                        f"Waiting {self.settings.monitor_interval_seconds}s before next poll"
                    )
                    await asyncio.sleep(self.settings.monitor_interval_seconds)
                else:
                    # Not in monitoring window, wait until it starts
                    seconds_until = self.scheduler.get_seconds_until_monitoring()
                    logger.info(
                        f"Outside monitoring window. Sleeping for {seconds_until}s "
                        f"until {self.settings.monitor_start}"
                    )
                    
                    # Sleep in smaller chunks so we can check for shutdown
                    for _ in range(min(seconds_until, 300)):  # Max 5 min sleep at a time
                        if not self.running:
                            break
                        await asyncio.sleep(1)
                        
        except KeyboardInterrupt:
            logger.info("Monitoring interrupted by user")
        except Exception as e:
            logger.error(f"Fatal error in monitoring loop: {e}")
            raise
        finally:
            await self.shutdown()

    async def shutdown(self):
        """Clean up resources."""
        logger.info("Shutting down agent...")
        self.running = False
        
        try:
            await self.browser.close()
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
        
        try:
            self.db.close()
        except Exception as e:
            logger.error(f"Error closing database: {e}")
        
        logger.info("Agent shutdown complete")


async def main():
    """Main entry point."""
    agent = ChowdeckVoucherAgent()
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
