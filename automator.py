"""
DOM automation for claude.ai.
Handles sending messages, reading streaming responses, model selection,
and new chat creation. All interaction is pure DOM — zero API calls.
"""

import asyncio
import logging
import time
from typing import AsyncGenerator

from playwright.async_api import Page

import config
import selectors as sel

log = logging.getLogger("cww.automator")

# Threshold for switching from keyboard.type() to clipboard paste
LONG_MESSAGE_THRESHOLD = 500


class Automator:
    def __init__(self, page: Page):
        self.page = page

    # =========================================================================
    # Send Message
    # =========================================================================

    async def send_message(self, text: str) -> None:
        """Type a message into the chat input and click Send."""
        log.info("[DOM] Focusing chat input")

        # Click the input to focus it
        input_el = await self._wait_for(sel.CHAT_INPUT)
        await input_el.click()
        await asyncio.sleep(0.1)

        # Clear any existing content
        await self.page.keyboard.press("Control+a")
        await self.page.keyboard.press("Backspace")

        # Type the message — use clipboard paste for long messages (ProseMirror)
        if len(text) > LONG_MESSAGE_THRESHOLD:
            log.info("[DOM] Pasting %d chars via clipboard", len(text))
            await self.page.evaluate(
                "text => navigator.clipboard.writeText(text)", text
            )
            await self.page.keyboard.press("Control+v")
        else:
            log.info("[DOM] Typing %d chars", len(text))
            await self.page.keyboard.type(text, delay=5)

        # Wait a moment for the send button to appear (voice → send transition)
        await asyncio.sleep(0.3)

        # Wait for send button to become visible
        log.info("[DOM] Waiting for Send button")
        try:
            send_btn = await self.page.wait_for_selector(
                sel.SEND_BUTTON,
                state="visible",
                timeout=config.SEND_BUTTON_TIMEOUT_MS,
            )
        except Exception:
            # Fallback: try pressing Enter to send
            log.warning("[DOM] Send button not found, pressing Enter")
            await self.page.keyboard.press("Enter")
            return

        await send_btn.click()
        log.info("[DOM] Clicked Send")

    # =========================================================================
    # Stream Response
    # =========================================================================

    async def stream_response(self) -> AsyncGenerator[str, None]:
        """
        Yield text chunks as the AI response streams in.
        Uses data-is-streaming attribute for deterministic state detection.
        """
        log.info("[STREAM] Waiting for AI response to start streaming...")

        # Wait for a streaming element to appear
        try:
            await self.page.wait_for_selector(
                sel.AI_MESSAGE_STREAMING,
                state="attached",
                timeout=config.PAGE_LOAD_TIMEOUT_MS,
            )
        except Exception:
            log.error("[STREAM] No streaming element appeared — timeout")
            yield "[Error: No response received from Claude]"
            return

        log.info("[STREAM] Streaming started")
        start_time = time.time()

        previous_text = ""
        idle_count = 0

        while True:
            # Check if still streaming
            streaming_el = await self.page.query_selector(sel.AI_MESSAGE_STREAMING)

            if streaming_el:
                # Still streaming — get current text content
                current_text = await streaming_el.inner_text()
            else:
                # Streaming stopped — get the completed message
                complete_els = await self.page.query_selector_all(
                    sel.AI_MESSAGE_COMPLETE
                )
                if complete_els:
                    current_text = await complete_els[-1].inner_text()
                else:
                    current_text = previous_text

            # Yield delta (new text since last poll)
            if len(current_text) > len(previous_text):
                delta = current_text[len(previous_text):]
                previous_text = current_text
                idle_count = 0
                yield delta
            else:
                idle_count += 1

            # Check for completion
            if not streaming_el:
                # data-is-streaming changed to false — we're done
                # Yield any remaining text
                if current_text and len(current_text) > len(previous_text):
                    yield current_text[len(previous_text):]
                elapsed = time.time() - start_time
                log.info(
                    "[STREAM] Complete — %d chars in %.1fs",
                    len(current_text),
                    elapsed,
                )
                return

            # Idle timeout fallback (in case data-is-streaming gets stuck)
            if idle_count > (config.IDLE_TIMEOUT_S * 1000 / config.POLL_INTERVAL_MS):
                elapsed = time.time() - start_time
                log.warning(
                    "[STREAM] Idle timeout after %.1fs — assuming complete", elapsed
                )
                return

            await asyncio.sleep(config.POLL_INTERVAL_MS / 1000)

    async def get_full_response(self) -> str:
        """Wait for streaming to complete and return the full response text."""
        chunks = []
        async for chunk in self.stream_response():
            chunks.append(chunk)
        return "".join(chunks)

    # =========================================================================
    # New Chat
    # =========================================================================

    async def start_new_chat(self) -> None:
        """Navigate to a fresh chat page."""
        log.info("[NAV] Starting new chat → %s", config.CLAUDE_NEW_CHAT_URL)
        await self.page.goto(
            config.CLAUDE_NEW_CHAT_URL,
            wait_until="domcontentloaded",
            timeout=config.PAGE_LOAD_TIMEOUT_MS,
        )

        # Wait for the input to be ready
        await self._wait_for(sel.CHAT_INPUT)
        log.info("[NAV] New chat ready")

    # =========================================================================
    # Model Selection
    # =========================================================================

    async def select_model(self, model_name: str) -> bool:
        """
        Open the model dropdown and select a model by name.
        Returns True if successful, False if model not found.
        """
        display_name = sel.MODEL_NAME_MAP.get(model_name, model_name)
        log.info("[DOM] Selecting model: %s (display: %s)", model_name, display_name)

        # Check if already on the right model
        model_btn = await self._wait_for(sel.MODEL_SELECTOR)
        current_text = await model_btn.inner_text()
        if display_name.lower() in current_text.lower():
            log.info("[DOM] Already on model %s", display_name)
            return True

        # Click the model selector dropdown
        await model_btn.click()
        await asyncio.sleep(0.3)

        # Wait for the menu to open
        try:
            await self.page.wait_for_selector(
                f'{sel.MODEL_MENU}[data-state="open"]',
                timeout=3000,
            )
        except Exception:
            # Try alternative: just wait for any menu
            await self.page.wait_for_selector(
                sel.MODEL_MENU,
                state="visible",
                timeout=3000,
            )

        # Check if it's a legacy model (needs More models submenu)
        is_legacy = model_name in (
            "claude-opus-4-5", "claude-opus-3", "claude-sonnet-4-5",
            "opus-4-5", "opus-3", "sonnet-4-5",
        )

        if is_legacy:
            # Click "More models" first
            log.info("[DOM] Opening More models submenu")
            more_btn = await self.page.query_selector(sel.MORE_MODELS_TRIGGER)
            if more_btn:
                await more_btn.click()
                await asyncio.sleep(0.3)

        # Find and click the target model
        menu_items = await self.page.query_selector_all('div[role="menuitem"]')
        for item in menu_items:
            text = await item.inner_text()
            if display_name.lower() in text.lower():
                await item.click()
                log.info("[DOM] Selected model: %s", display_name)
                await asyncio.sleep(0.3)
                return True

        log.warning("[DOM] Model '%s' not found in dropdown", display_name)
        # Close the dropdown by pressing Escape
        await self.page.keyboard.press("Escape")
        return False

    # =========================================================================
    # Usage Limit Check
    # =========================================================================

    async def check_usage_limit(self) -> bool:
        """Check if the usage limit banner is showing."""
        banner = await self.page.query_selector(sel.USAGE_LIMIT_BANNER)
        if banner:
            text = await banner.inner_text()
            if "weekly limit" in text.lower() or "limit" in text.lower():
                log.warning("[LIMIT] Usage limit detected: %s", text.strip())
                return True
        return False

    # =========================================================================
    # Helpers
    # =========================================================================

    async def _wait_for(self, selector: str, timeout: int | None = None):
        """Wait for an element to be visible and return it."""
        timeout = timeout or config.ELEMENT_TIMEOUT_MS
        return await self.page.wait_for_selector(
            selector, state="visible", timeout=timeout
        )
