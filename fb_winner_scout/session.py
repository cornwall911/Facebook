import json
import time
from typing import Optional, List
from patchright.sync_api import sync_playwright, BrowserContext, Page, Browser
from fb_winner_scout.config import ScoutConfig

class FacebookSession:
    def __init__(self, config: ScoutConfig):
        self.config = config
        self._playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None

    def start(self) -> BrowserContext:
        self._playwright = sync_playwright().start()
        
        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
        ]

        launch_kwargs = {
            "headless": self.config.headless,
            "args": launch_args,
        }

        if self.config.proxy_url:
            launch_kwargs["proxy"] = {"server": self.config.proxy_url}

        self.browser = self._playwright.chromium.launch(**launch_kwargs)

        # Realistic desktop context
        self.context = self.browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            locale="en-US",
            timezone_id="America/New_York",
        )

        # Inject cookies
        cookies = self.config.load_cookies()
        if cookies:
            print(f"[Session] Loaded {len(cookies)} cookies into session.")
            self.context.add_cookies(cookies)
        else:
            print("[Warning] No cookies provided! Facebook private groups will not be accessible without login.")

        return self.context

    def verify_login(self, page: Page) -> bool:
        """Checks if the injected session is currently logged into Facebook."""
        try:
            page.goto("https://www.facebook.com/", wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)
            # Check if login form is displayed or feed/home
            url = page.url
            if "login" in url or "checkpoint" in url:
                print(f"[Session Error] Not logged in. Redirected to: {url}")
                return False

            # Check for common logged-in elements
            has_feed = page.locator("div[role='feed'], div[role='main'], div[aria-label='Facebook']").count() > 0
            if has_feed:
                print("[Session] Successfully verified Facebook logged-in session!")
                return True

            # If page doesn't have login inputs, we might be logged in
            is_login_page = page.locator("input[name='email'], input#email").count() > 0
            if not is_login_page:
                print("[Session] Logged-in session appears active.")
                return True

            return False
        except Exception as e:
            print(f"[Session] Verification check error: {e}")
            return False

    def close(self):
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self._playwright:
            self._playwright.stop()
