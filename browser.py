"""
Playwright browser manager.
Handles persistent browser context so the user only logs in once.
Zero credential storage — session lives in the browser profile directory.
"""

import logging
from pathlib import Path

from playwright.async_api import (
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)

import config
import dom_selectors as sel

log = logging.getLogger("cww.browser")


class BrowserManager:
    def __init__(
        self,
        headless: bool = config.HEADLESS,
        user_data_dir: str = config.USER_DATA_DIR,
    ):
        self.headless = headless
        self.user_data_dir = user_data_dir
        self._playwright: Playwright | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    async def start(self) -> Page:
        """Launch browser with persistent context and navigate to claude.ai."""
        # Ensure user data directory exists
        Path(self.user_data_dir).mkdir(parents=True, exist_ok=True)

        log.info("[NAV] Launching Chromium (headless=%s)", self.headless)
        log.info("[NAV] User data dir: %s", self.user_data_dir)

        self._playwright = await async_playwright().start()

        self._context = await self._playwright.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            headless=self.headless,
            viewport=config.BROWSER_VIEWPORT,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ],
            ignore_default_args=["--enable-automation"],
        )

        # Use existing page or create new one
        if self._context.pages:
            self._page = self._context.pages[0]
        else:
            self._page = await self._context.new_page()

        # Wire up console and error logging
        self._page.on("console", self._on_console)
        self._page.on("pageerror", self._on_page_error)

        # Navigate to claude.ai
        await self._navigate_to_claude()

        return self._page

    async def _navigate_to_claude(self):
        """Navigate to claude.ai/new and wait for the chat input to be ready."""
        log.info("[NAV] Navigating to %s", config.CLAUDE_NEW_CHAT_URL)
        await self._page.goto(
            config.CLAUDE_NEW_CHAT_URL,
            wait_until="domcontentloaded",
            timeout=config.PAGE_LOAD_TIMEOUT_MS,
        )

        # Wait for the chat input to appear (page ready signal)
        log.info("[NAV] Waiting for chat input to appear...")
        await self._page.wait_for_selector(
            sel.CHAT_INPUT,
            state="visible",
            timeout=config.PAGE_LOAD_TIMEOUT_MS,
        )
        log.info("[NAV] Page ready — chat input visible")

    @property
    def page(self) -> Page:
        if self._page is None:
            raise RuntimeError("Browser not started. Call start() first.")
        return self._page

    @property
    def context(self) -> BrowserContext:
        if self._context is None:
            raise RuntimeError("Browser not started. Call start() first.")
        return self._context

    async def is_logged_in(self) -> bool:
        """Check if user is logged in by looking for the chat input."""
        try:
            elem = await self._page.query_selector(sel.CHAT_INPUT)
            return elem is not None
        except Exception:
            return False

    async def close(self):
        """Shut down browser and playwright."""
        log.info("[NAV] Shutting down browser")
        if self._context:
            await self._context.close()
            self._context = None
            self._page = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    @staticmethod
    def _on_console(msg):
        """Forward browser console messages to terminal."""
        level = msg.type
        if level in ("error", "warning"):
            log.debug("[CONSOLE:%s] %s", level.upper(), msg.text)

    @staticmethod
    def _on_page_error(error):
        """Log uncaught page errors."""
        log.warning("[PAGE_ERROR] %s", error)
