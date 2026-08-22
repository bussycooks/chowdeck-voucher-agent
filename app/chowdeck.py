"""Chowdeck browser automation using Playwright.

This module handles:
1. Persistent browser profile authentication
2. Manual login flow with OTP verification
3. Voucher page navigation
4. Voucher verification (without redemption)

Never:
- Stores passwords or OTPs
- Bypasses authentication or CAPTCHA
- Performs financial transactions
- Accesses private user data
"""
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime
from playwright.async_api import async_playwright, Browser, Page

logger = logging.getLogger(__name__)


class ChowdeckBrowser:
    """Manage Chowdeck browser automation with persistent profiles."""
    
    CHOWDECK_URL = "https://chowdeck.com"
    VOUCHERS_PAGE = "https://chowdeck.com/store/vouchers"
    
    def __init__(
        self,
        profile_path: str = "./browser_profiles/chowdeck",
        headless: bool = False,
        timeout_ms: int = 30000,
    ):
        """Initialize Chowdeck browser manager.
        
        Args:
            profile_path: Path to persistent browser profile
            headless: Whether to run browser in headless mode
            timeout_ms: Navigation timeout in milliseconds
        """
        self.profile_path = Path(profile_path)
        self.profile_path.mkdir(parents=True, exist_ok=True)
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
    
    async def initialize(self):
        """Initialize Playwright and browser."""
        try:
            self.playwright = await async_playwright().start()
            logger.info("Playwright started")
        except Exception as e:
            logger.error(f"Failed to start Playwright: {e}")
            raise
    
    async def launch_browser(self) -> Browser:
        """Launch browser with persistent profile.
        
        Returns:
            Browser instance
        """
        try:
            if not self.playwright:
                await self.initialize()
            
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
            )
            logger.info(f"Browser launched (headless={self.headless})")
            return self.browser
            
        except Exception as e:
            logger.error(f"Failed to launch browser: {e}")
            raise
    
    async def create_context_with_profile(self):
        """Create browser context with persistent profile.
        
        Returns:
            Browser context
        """
        if not self.browser:
            await self.launch_browser()
        
        try:
            context = await self.browser.new_context(
                storage_state=str(self.profile_path / "auth.json"),
            )
            logger.info(f"Browser context created with profile: {self.profile_path}")
            return context
            
        except Exception as e:
            logger.warning(f"Could not load profile (may be first run): {e}")
            # Create fresh context for first-time auth
            context = await self.browser.new_context()
            return context
    
    async def require_authentication(self) -> bool:
        """Check if authentication is needed and prompt for manual login.
        
        This opens a visible browser for manual login and OTP verification.
        The session is saved to the persistent profile.
        
        Returns:
            True if authentication completed successfully
        """
        try:
            context = await self.create_context_with_profile()
            self.page = await context.new_page()
            self.page.set_default_timeout(self.timeout_ms)
            
            logger.info("Opening Chowdeck for authentication...")
            await self.page.goto(self.CHOWDECK_URL)
            
            # Check if login is required
            try:
                # Wait for either login button or logged-in state
                await self.page.wait_for_selector(
                    "[data-testid='login-button'], [data-testid='account-menu'], button:has-text('Sign in')",
                    timeout=5000,
                )
                
                login_button = await self.page.query_selector(
                    "[data-testid='login-button'], button:has-text('Sign in')"
                )
                
                if login_button:
                    await login_button.click()
                    logger.info("Clicked login button. Please complete authentication manually.")
                    logger.info("Browser will remain open for manual OTP entry.")
                    logger.info("Close the browser window after successful login.")
                    
                    # Wait for navigation to indicate successful login
                    try:
                        await self.page.wait_for_navigation(timeout=300000)  # 5 minutes
                    except Exception:
                        pass  # User may not trigger a navigation
                
                # Save authentication state
                auth_file = self.profile_path / "auth.json"
                await context.storage_state(path=str(auth_file))
                logger.info(f"Authentication state saved to {auth_file}")
                
                await context.close()
                return True
                
            except Exception as e:
                logger.error(f"Authentication check failed: {e}")
                await context.close()
                return False
                
        except Exception as e:
            logger.error(f"Error during authentication: {e}")
            return False
    
    async def check_voucher_exists(self, voucher_code: str) -> bool:
        """Check if a voucher code exists and is valid.
        
        Args:
            voucher_code: Code to verify
            
        Returns:
            True if voucher appears valid
        """
        try:
            context = await self.create_context_with_profile()
            page = await context.new_page()
            page.set_default_timeout(self.timeout_ms)
            
            logger.info(f"Checking voucher {voucher_code} on Chowdeck...")
            await page.goto(self.VOUCHERS_PAGE)
            
            # Look for the voucher code on the page
            # This is a simple check - adjust selector based on Chowdeck's actual HTML
            try:
                voucher_element = await page.query_selector(
                    f"text='{voucher_code}'"
                )
                
                if voucher_element:
                    logger.info(f"Voucher {voucher_code} found on Chowdeck vouchers page")
                    await page.close()
                    await context.close()
                    return True
                else:
                    logger.info(f"Voucher {voucher_code} not found on current page")
                    
            except Exception as e:
                logger.warning(f"Could not verify voucher on page: {e}")
            
            await page.close()
            await context.close()
            return False
            
        except Exception as e:
            logger.error(f"Error checking voucher: {e}")
            return False
    
    async def get_voucher_details(self, voucher_code: str) -> Optional[dict]:
        """Get details about a voucher without attempting to redeem.
        
        Args:
            voucher_code: Code to look up
            
        Returns:
            Dictionary with voucher details or None
        """
        try:
            context = await self.create_context_with_profile()
            page = await context.new_page()
            page.set_default_timeout(self.timeout_ms)
            
            await page.goto(self.VOUCHERS_PAGE)
            
            # Search for voucher (implementation depends on Chowdeck's UI)
            details = {
                "code": voucher_code,
                "exists": False,
                "checked_at": datetime.now().isoformat(),
            }
            
            # Try to find the voucher on the page
            try:
                voucher_text = await page.locator(f"text='{voucher_code}'").count()
                if voucher_text > 0:
                    details["exists"] = True
                    logger.info(f"Voucher details retrieved for {voucher_code}")
            except Exception as e:
                logger.debug(f"Could not retrieve voucher details: {e}")
            
            await page.close()
            await context.close()
            
            return details
            
        except Exception as e:
            logger.error(f"Error getting voucher details: {e}")
            return None
    
    async def close(self):
        """Clean up browser resources."""
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("Browser closed")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
