"""X API monitor for tracking tweets from @lordbinary_."""
import logging
from typing import Optional, List, Dict
from datetime import datetime
import requests

logger = logging.getLogger(__name__)


class XMonitor:
    """Monitor X (Twitter) API for tweets from specific users."""
    
    # X API v2 endpoints
    SEARCH_ENDPOINT = "https://api.twitter.com/2/tweets/search/recent"
    USER_ENDPOINT = "https://api.twitter.com/2/users/by/username/{username}"
    TIMELINE_ENDPOINT = "https://api.twitter.com/2/users/{user_id}/tweets"
    
    def __init__(self, bearer_token: str):
        """Initialize X API monitor.
        
        Args:
            bearer_token: X API Bearer token for authentication
        """
        self.bearer_token = bearer_token
        self.headers = {
            "Authorization": f"Bearer {bearer_token}",
            "User-Agent": "ChowdeckVoucherAgent/0.1.0",
        }
    
    def get_user_id(self, username: str) -> Optional[str]:
        """Get the user ID for a given username.
        
        Args:
            username: Twitter username (without @)
            
        Returns:
            User ID or None if not found
        """
        try:
            url = self.USER_ENDPOINT.format(username=username)
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if "data" in data and "id" in data["data"]:
                user_id = data["data"]["id"]
                logger.info(f"Found user ID for @{username}: {user_id}")
                return user_id
            else:
                logger.warning(f"Could not find user ID for @{username}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching user ID for @{username}: {e}")
            return None
    
    def get_recent_tweets(
        self,
        user_id: str,
        max_results: int = 100,
    ) -> List[Dict]:
        """Get recent tweets from a user.
        
        Args:
            user_id: X user ID
            max_results: Maximum tweets to fetch (10-100)
            
        Returns:
            List of tweet data dictionaries
        """
        try:
            url = self.TIMELINE_ENDPOINT.format(user_id=user_id)
            params = {
                "max_results": min(max(max_results, 10), 100),
                "tweet.fields": "created_at,public_metrics,author_id",
                "expansions": "author_id",
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            tweets = data.get("data", [])
            logger.info(f"Fetched {len(tweets)} recent tweets from user {user_id}")
            return tweets
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching tweets from user {user_id}: {e}")
            return []
    
    def search_tweets(self, query: str, max_results: int = 100) -> List[Dict]:
        """Search for tweets using a query.
        
        Args:
            query: Search query
            max_results: Maximum tweets to fetch
            
        Returns:
            List of tweet data dictionaries
        """
        try:
            params = {
                "query": query,
                "max_results": min(max(max_results, 10), 100),
                "tweet.fields": "created_at,public_metrics,author_id",
            }
            
            response = requests.get(self.SEARCH_ENDPOINT, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            tweets = data.get("data", [])
            logger.info(f"Search query '{query}' returned {len(tweets)} tweets")
            return tweets
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching tweets with query '{query}': {e}")
            return []
    
    def build_tweet_url(self, username: str, tweet_id: str) -> str:
        """Build the URL for a tweet.
        
        Args:
            username: Tweet author username
            tweet_id: Tweet ID
            
        Returns:
            Full URL to the tweet
        """
        return f"https://twitter.com/{username}/status/{tweet_id}"
