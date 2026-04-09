"""
Playwright browser manager.
Handles persistent browser context so the user only logs in once.
Zero credential storage — session lives in the browser profile directory.

IMPORTANT: Runs HEADED (not headless) but minimized. Cloudflare blocks
headless browsers. LMArenaBridge uses the same approach — headed mode
with the window hidden/minimized to bypass bot detection.
"""

import asyncio
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

# Cloudflare Turnstile selectors
CF_TURNSTILE_SELECTORS = [
    'iframe[src*="challenges.cloudflare.com"]',
    'iframe[title*="Cloudflare"]',
    "#turnstile-wrapper iframe",
    'iframe[src*="turnstile"]',
]

CF_CHECKBOX_SELECTORS = [
    'input[type="checkbox"]',
    ".ctp-checkbox-label",
    "#challenge-stage",
]


class BrowserManager:
    def __init__(
        self,
        login_mode: bool = False,
        user_data_dir: str = config.USER_DATA_DIR,
    ):
        # login_mode = True: visible window for user to log in
        # login_mode = False: headed but minimized (bypasses Cloudflare)
        self.login_mode = login_mode
        self.user_data_dir = user_data_dir
        self._playwright: Playwright | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    async def start(self) -> Page:
        """Launch browser with persistent context and navigate to claude.ai."""
        Path(self.user_data_dir).mkdir(parents=True, exist_ok=True)

        mode = "LOGIN (visible)" if self.login_mode else "BACKGROUND (headed-minimized)"
        log.info("[NAV] Launching Chromium — %s", mode)
        log.info("[NAV] User data dir: %s", self.user_data_dir)

        self._playwright = await async_playwright().start()

        # Always headed — Cloudflare blocks headless browsers.
        # In normal mode we start minimized via --start-minimized.
        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--disable-infobars",
            "--disable-extensions",
            "--disable-popup-blocking",
        ]

        if not self.login_mode:
            # Background mode: start window minimized (still headed)
            launch_args.append("--start-minimized")

        self._context = await self._playwright.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            headless=False,  # ALWAYS headed — Cloudflare kills headless
            viewport=config.BROWSER_VIEWPORT,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            args=launch_args,
            ignore_default_args=["--enable-automation"],
        )

        # Remove navigator.webdriver flag (bot detection bypass)
        await self._context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            // Hide Playwright/automation indicators
            delete window.__playwright;
            delete window.__pw_manual;
        """)

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
        """Navigate to claude.ai/new, handle Cloudflare, wait for page ready."""
        log.info("[NAV] Navigating to %s", config.CLAUDE_NEW_CHAT_URL)
        await self._page.goto(
            config.CLAUDE_NEW_CHAT_URL,
            wait_until="domcontentloaded",
            timeout=config.PAGE_LOAD_TIMEOUT_MS,
        )

        # Check for Cloudflare challenge and attempt to solve it
        await self._handle_cloudflare()

        # Wait for the chat input to appear (page ready signal)
        log.info("[NAV] Waiting for chat input to appear...")
        try:
            await self._page.wait_for_selector(
                sel.CHAT_INPUT,
                state="visible",
                timeout=config.PAGE_LOAD_TIMEOUT_MS,
            )
            log.info("[NAV] Page ready — chat input visible")
        except Exception:
            # Might be on login page or still on Cloudflare
            current_url = self._page.url
            log.warning("[NAV] Chat input not found. Current URL: %s", current_url)
            if "challenges.cloudflare.com" in current_url or "challenge" in current_url:
                log.warning("[NAV] Still on Cloudflare challenge page")
            elif "/login" in current_url:
                log.warning("[NAV] On login page — need to log in")
            else:
                log.warning("[NAV] Unknown state — page may need manual intervention")

    async def _handle_cloudflare(self):
        """Detect and attempt to auto-solve Cloudflare Turnstile challenges."""
        await asyncio.sleep(2)  # Let the page settle

        for attempt in range(3):
            # Check if we're past Cloudflare already
            if sel.CHAT_INPUT:
                chat_input = await self._page.query_selector(sel.CHAT_INPUT)
                if chat_input:
                    return  # Already through

            # Look for Turnstile iframe
            turnstile_frame = None
            for cf_sel in CF_TURNSTILE_SELECTORS:
                iframe_el = await self._page.query_selector(cf_sel)
                if iframe_el:
                    log.info("[CF] Found Cloudflare Turnstile widget (attempt %d)", attempt + 1)
                    try:
                        turnstile_frame = await iframe_el.content_frame()
                    except Exception:
                        pass
                    break

            if turnstile_frame:
                # Try to click the checkbox inside the iframe
                for cb_sel in CF_CHECKBOX_SELECTORS:
                    try:
                        cb = await turnstile_frame.query_selector(cb_sel)
                        if cb:
                            log.info("[CF] Clicking Turnstile checkbox")
                            await cb.click()
                            await asyncio.sleep(3)
                            break
                    except Exception:
                        continue

                # Fallback: click center of the iframe element
                try:
                    box = await iframe_el.bounding_box()
                    if box:
                        log.info("[CF] Clicking Turnstile iframe center")
                        await self._page.mouse.click(
                            box["x"] + box["width"] / 2,
                            box["y"] + box["height"] / 2,
                        )
                        await asyncio.sleep(3)
                except Exception:
                    pass
            else:
                # No Turnstile found — might already be through
                if attempt == 0:
                    log.info("[CF] No Cloudflare challenge detected")
                return

            await asyncio.sleep(2)

        log.warning("[CF] Could not auto-solve Cloudflare after 3 attempts")

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
