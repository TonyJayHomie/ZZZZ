import os
from pathlib import Path

# Server
PORT = int(os.environ.get("CWW_PORT", 3967))
HOST = os.environ.get("CWW_HOST", "127.0.0.1")

# Browser
HEADLESS = os.environ.get("CWW_HEADLESS", "true").lower() == "true"
USER_DATA_DIR = os.environ.get(
    "CWW_USER_DATA_DIR",
    str(Path.home() / ".claude-wrapper" / "browser-data"),
)
BROWSER_VIEWPORT = {"width": 1280, "height": 900}

# Automation timing
POLL_INTERVAL_MS = 100  # How often to poll for streaming content
IDLE_TIMEOUT_S = 5.0  # Max seconds of no new content before assuming done
PAGE_LOAD_TIMEOUT_MS = 30000  # Max wait for page navigation
ELEMENT_TIMEOUT_MS = 10000  # Max wait for element to appear
SEND_BUTTON_TIMEOUT_MS = 5000  # Max wait for send button after typing

# Claude.ai
CLAUDE_BASE_URL = "https://claude.ai"
CLAUDE_NEW_CHAT_URL = f"{CLAUDE_BASE_URL}/new"

# Logging
VERBOSE = os.environ.get("CWW_VERBOSE", "true").lower() == "true"
