"""Telegram notifications module."""
import logging
from typing import Optional
from datetime import datetime
import requests

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Send notifications via Telegram Bot API."""
    
    API_URL = "https://api.telegram.org/bot{token}/sendMessage"
    
    def __init__(self, bot_token: str, chat_id: str):
        """Initialize Telegram notifier.
        
        Args:
            bot_token: Telegram bot token
            chat_id: Target chat ID for notifications
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = self.API_URL.format(token=bot_token)
    
    def send_voucher_notification(
        self,
        voucher_code: str,
        tweet_text: str,
        tweet_url: str,
        detected_time: datetime,
    ) -> Optional[str]:
        """Send a voucher discovery notification.
        
        Args:
            voucher_code: The discovered voucher code
            tweet_text: Full text of the tweet
            tweet_url: URL to the tweet
            detected_time: When the voucher was detected
            
        Returns:
            Telegram message ID if sent successfully, None otherwise
        """
        message = self._format_voucher_message(
            voucher_code,
            tweet_text,
            tweet_url,
            detected_time,
        )
        
        return self._send_message(message)
    
    def _format_voucher_message(
        self,
        voucher_code: str,
        tweet_text: str,
        tweet_url: str,
        detected_time: datetime,
    ) -> str:
        """Format a voucher notification message.
        
        Args:
            voucher_code: The voucher code
            tweet_text: Tweet content
            tweet_url: Tweet URL
            detected_time: Detection timestamp
            
        Returns:
            Formatted message string
        """
        timestamp = detected_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Truncate tweet text if too long
        max_text_len = 300
        display_text = tweet_text[:max_text_len]
        if len(tweet_text) > max_text_len:
            display_text += "..."
        
        message = (
            f"🚨 NEW POSSIBLE CHOWDECK VOUCHER\n\n"
            f"💰 Code: `{voucher_code}`\n\n"
            f"📝 Tweet:\n{display_text}\n\n"
            f"🔗 URL:\n{tweet_url}\n\n"
            f"⏰ Detected:\n{timestamp}"
        )
        
        return message
    
    def _send_message(self, text: str) -> Optional[str]:
        """Send a message via Telegram.
        
        Args:
            text: Message text
            
        Returns:
            Telegram message ID if successful, None otherwise
        """
        try:
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "Markdown",
            }
            
            response = requests.post(self.api_url, json=payload, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get("ok") and "result" in data:
                message_id = data["result"].get("message_id")
                logger.info(f"Telegram notification sent successfully (message_id: {message_id})")
                return str(message_id)
            else:
                logger.error(f"Telegram API error: {data.get('description', 'Unknown')}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending Telegram notification: {e}")
            return None
    
    def send_error_notification(self, error_message: str) -> Optional[str]:
        """Send an error notification.
        
        Args:
            error_message: Error details
            
        Returns:
            Telegram message ID if sent successfully
        """
        message = (
            f"⚠️ CHOWDECK AGENT ERROR\n\n"
            f"{error_message}\n\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        return self._send_message(message)
