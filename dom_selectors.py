"""
Complete verified DOM selectors for claude.ai
Merged from two independent DevTools extraction sessions.
All selectors verified against live claude.ai as of April 2026.

Framework: React + Radix UI + TipTap (ProseMirror) + Tailwind CSS
Stable selectors: data-testid > aria-label > role > id > semantic HTML
Avoid: Tailwind utility classes (not stable across deployments)
"""


# =============================================================================
# CHAT INPUT (Compose Area)
# =============================================================================

# Main text input — TipTap ProseMirror contenteditable div
# IMPORTANT: Use keyboard.type() or keyboard.insert_text(), NOT fill()
CHAT_INPUT = '[data-testid="chat-input"]'
CHAT_INPUT_BACKUP = 'div.ProseMirror[role="textbox"][aria-label="Write your prompt to Claude"]'
CHAT_INPUT_TIPTAP = "div.tiptap.ProseMirror[contenteditable='true']"

# Placeholder paragraphs inside the input (state detection)
PLACEHOLDER_NEW_CHAT = 'p[data-placeholder="How can I help you today?"]'
PLACEHOLDER_REPLY = 'p[data-placeholder="Reply..."]'

# Input area sticky wrapper
INPUT_AREA_WRAPPER = "div.sticky.bottom-0"


# =============================================================================
# SEND / VOICE / STOP BUTTONS
# =============================================================================

# Send button — only visible when text is typed in the input
SEND_BUTTON = 'button[aria-label="Send message"]'

# Voice mode button — visible when input is empty, transforms to Send when text present
VOICE_BUTTON = 'button[aria-label="Use voice mode"]'

# Incognito button — only on /new page
INCOGNITO_BUTTON = 'button[aria-label="Use incognito"]'

# Stop generation button — appears during streaming
STOP_BUTTON = "button#claude-agent-stop-button"  # text="Stop Claude"

# Streaming animation border
GLOW_BORDER = "div#claude-agent-glow-border"

# Stop button container
STOP_CONTAINER = "div#claude-agent-stop-container"

# Animation styles (injected during streaming)
ANIMATION_STYLES = "style#claude-agent-animation-styles"


# =============================================================================
# FILE UPLOAD
# =============================================================================

FILE_UPLOAD_INPUT = 'input[data-testid="file-upload"][type="file"]'
FILE_UPLOAD_INPUT_BY_ID = "input#chat-input-file-upload-bottom"
FILE_UPLOAD_INPUT_BY_ARIA = 'input[aria-label="Upload files"]'

# Add files menu trigger
ADD_FILES_BUTTON = 'button[aria-label="Add files, connectors, and more"]'

# Add files dropdown menu items (div[role="menuitem"] or div[role="menuitemcheckbox"])
ADD_FILES_MENU = {
    "add_files": 'div[role="menuitem"]:has-text("Add files or photos")',
    "screenshot": 'div[role="menuitem"]:has-text("Take a screenshot")',
    "add_to_project": 'div[role="menuitem"]:has-text("Add to project")',
    "add_from_github": 'div[role="menuitem"]:has-text("Add from GitHub")',
    "add_connectors": 'div[role="menuitem"]:has-text("Add connectors")',
    "research": 'div[role="menuitemcheckbox"]:has-text("Research")',
    "web_search": 'div[role="menuitemcheckbox"]:has-text("Web search")',
    "use_style": 'div[role="menuitem"]:has-text("Use style")',
}

# Use style submenu items (role="menuitemcheckbox")
STYLE_MENU = {
    "normal": 'div[role="menuitemcheckbox"]:has-text("Normal")',
    "learning": 'div[role="menuitemcheckbox"]:has-text("Learning")',
    "concise": 'div[role="menuitemcheckbox"]:has-text("Concise")',
    "explanatory": 'div[role="menuitemcheckbox"]:has-text("Explanatory")',
    "formal": 'div[role="menuitemcheckbox"]:has-text("Formal")',
    "create_edit": 'div[role="menuitem"]:has-text("Create & edit styles")',
}


# =============================================================================
# MODEL SELECTOR
# =============================================================================

# Dropdown trigger button
MODEL_SELECTOR = '[data-testid="model-selector-dropdown"]'

# Model menu container (opens below trigger)
MODEL_MENU = 'div[role="menu"]'

# Individual model items (div[role="menuitem"])
MODEL_ITEMS = {
    "opus-4-6": 'div[role="menuitem"]:has-text("Opus 4.6")',
    "sonnet-4-6": 'div[role="menuitem"]:has-text("Sonnet 4.6")',
    "haiku-4-5": 'div[role="menuitem"]:has-text("Haiku 4.5")',
}

# Extended thinking toggle (inside model dropdown)
EXTENDED_THINKING_TOGGLE = 'input[role="switch"][aria-label="Extended thinking"]'

# More models submenu trigger
MORE_MODELS_TRIGGER = 'div[role="menuitem"]:has-text("More models")'

# Legacy model items (in More models submenu)
LEGACY_MODEL_ITEMS = {
    "opus-4-5": 'div[role="menuitem"]:has-text("Opus 4.5")',
    "opus-3": 'div[role="menuitem"]:has-text("Opus 3")',
    "sonnet-4-5": 'div[role="menuitem"]:has-text("Sonnet 4.5")',
}

# Map from OpenAI-style model names to display text for matching
MODEL_NAME_MAP = {
    "claude-opus-4-6": "Opus 4.6",
    "claude-sonnet-4-6": "Sonnet 4.6",
    "claude-haiku-4-5": "Haiku 4.5",
    "claude-opus-4-5": "Opus 4.5",
    "claude-opus-3": "Opus 3",
    "claude-sonnet-4-5": "Sonnet 4.5",
    # Short aliases
    "opus-4-6": "Opus 4.6",
    "sonnet-4-6": "Sonnet 4.6",
    "haiku-4-5": "Haiku 4.5",
    "opus": "Opus 4.6",
    "sonnet": "Sonnet 4.6",
    "haiku": "Haiku 4.5",
}


# =============================================================================
# MESSAGES — Reading AI Responses
# =============================================================================

# User message container
USER_MESSAGE = '[data-testid="user-message"]'

# AI message — use data-is-streaming for state detection
AI_MESSAGE_STREAMING = 'div[data-is-streaming="true"]'
AI_MESSAGE_COMPLETE = 'div[data-is-streaming="false"]'

# File thumbnail in messages
FILE_THUMBNAIL = '[data-testid="file-thumbnail"]'

# Message action bar (wraps buttons on each message)
MESSAGE_ACTIONS = 'div[role="group"][aria-label="Message actions"]'

# AI message action buttons
ACTION_COPY = '[data-testid="action-bar-copy"]'
ACTION_RETRY = '[data-testid="action-bar-retry"]'
ACTION_THUMBS_UP = 'button[aria-label="Give positive feedback"]'
ACTION_THUMBS_DOWN = 'button[aria-label="Give negative feedback"]'

# User message action buttons
ACTION_EDIT = 'button[aria-label="Edit"]'
ACTION_USER_RETRY = 'button[aria-label="Retry"]'

# Web search status indicator
WEB_SEARCH_STATUS = 'span[role="status"][aria-live="polite"]'

# Usage limit banner
USAGE_LIMIT_BANNER = 'div[role="status"][aria-live="polite"][aria-atomic="true"]'


# =============================================================================
# PAGE HEADER (in-conversation)
# =============================================================================

PAGE_HEADER = '[data-testid="page-header"]'
CHAT_TITLE_BUTTON = '[data-testid="chat-title-button"]'
CHAT_MENU_TRIGGER = '[data-testid="chat-menu-trigger"]'
CHAT_ACTIONS = '[data-testid="chat-actions"]'

# Chat title dropdown menu items
CHAT_MENU_ITEMS = {
    "star": '[data-testid="star-chat-trigger"]',
    "rename": '[data-testid="rename-chat-trigger"]',
    "add_to_project": '[data-testid="move-to-project-trigger"]',
    "delete": '[data-testid="delete-chat-trigger"]',
}


# =============================================================================
# SIDEBAR NAVIGATION
# =============================================================================

SIDEBAR = 'nav[aria-label="Sidebar"]'
SIDEBAR_TOGGLE = '[data-testid="pin-sidebar-toggle"]'

# Navigation links
NAV_HOME = 'a[aria-label="Home"]'
NAV_NEW_CHAT = 'a[aria-label="New chat"]'
NAV_SEARCH = 'a[aria-label="Search"]'
NAV_CUSTOMIZE = 'a[aria-label="Customize"]'
NAV_CHATS = 'a[aria-label="Chats"]'
NAV_PROJECTS = 'a[aria-label="Projects"]'
NAV_ARTIFACTS = 'a[aria-label="Artifacts"]'
NAV_CODE = 'a[aria-label="Code"]'

# Chat history items
CHAT_HISTORY_ITEM = 'a[href^="/chat/"]'
ALL_CHATS_LINK = 'a[href="/recents"]'

# Scroll to bottom (appears when scrolled up)
SCROLL_TO_BOTTOM = 'button[aria-label="Scroll to bottom"]'


# =============================================================================
# USER MENU
# =============================================================================

USER_MENU_BUTTON = '[data-testid="user-menu-button"]'
USER_MENU_SETTINGS = '[data-testid="user-menu-settings"]'
GET_APPS_LINK = 'a[aria-label="Get apps and extensions"]'

# User menu items (by href or text)
USER_MENU_ITEMS = {
    "settings": 'a[href="/settings/general"]',
    "plans": 'a[href="/upgrade"]',
    "downloads": 'a[href="/downloads"]',
    "gift": 'a[href="/gift"]',
    "logout": 'a[href="/logout"]',
}


# =============================================================================
# SETTINGS PAGE (/settings/*)
# =============================================================================

SETTINGS_NAV = 'nav[aria-label="Settings"]'

SETTINGS_NAV_ITEMS = {
    "general": 'a[href="/settings/general"]',
    "account": 'a[href="/settings/account"]',
    "privacy": 'a[href="/settings/data-privacy-controls"]',
    "billing": 'a[href="/settings/billing"]',
    "usage": 'a[href="/settings/usage"]',
    "capabilities": 'a[href="/settings/capabilities"]',
    "connectors": 'a[href="/settings/connectors"]',
    "claude_code": 'a[href="/settings/claude-code"]',
    "chrome_ext": 'a[href="/settings/browser-extension"]',
}

# Settings form fields (by ID)
SETTINGS_FULL_NAME = "input#full-name"
SETTINGS_DISPLAY_NAME = "input#displayname"
SETTINGS_WORK_FUNCTION = "button#work-function-select"
SETTINGS_CONVERSATION_PREFS = "textarea#conversation-preferences"

# Appearance buttons (aria-pressed="true" = selected)
APPEARANCE = {
    "light_mode": 'button[aria-label="Light color mode"]',
    "auto_mode": 'button[aria-label="Auto color mode"]',
    "dark_mode": 'button[aria-label="Dark color mode"]',
    "anim_enabled": 'button[aria-label="Enabled background animation"]',
    "anim_auto": 'button[aria-label="Auto background animation"]',
    "anim_disabled": 'button[aria-label="Disabled background animation"]',
    "font_default": 'button[aria-label="Default chat font"]',
    "font_sans": 'button[aria-label="Sans chat font"]',
    "font_system": 'button[aria-label="System chat font"]',
    "font_dyslexic": 'button[aria-label="Dyslexic friendly chat font"]',
}


# =============================================================================
# PROJECTS & RECENTS PAGES
# =============================================================================

PROJECTS_SEARCH = 'input[aria-label="Search projects..."]'
PROJECTS_SORT = 'button[aria-label="Sort projects"]'
RECENTS_SEARCH = 'input[aria-label="Search your chats"]'
RECENTS_RESULTS = 'div[role="listbox"][aria-label="Chat search results"]'


# =============================================================================
# STATIC IDS
# =============================================================================

APP_ROOT = "#root"
MAIN_CONTENT = "#main-content"
INTERCOM_FRAME = "#intercom-frame"


# =============================================================================
# DATA ATTRIBUTES (for state detection, not direct targeting)
# =============================================================================

# data-state="open" / "closed" — dropdowns, popovers, toggles
# data-is-streaming="true" / "false" — AI message streaming state
# data-open="" — menu is currently open (presence = open)
# data-checked="" / data-unchecked="" — menuitemcheckbox state
# data-highlighted="" — currently focused/hovered menu item
# data-nested="" — nested submenu indicator
# data-side="bottom" / "top" — popover positioning
# data-align="start" / "end" / "center" — popover alignment
# data-orientation="horizontal" / "vertical" — separators, menus
# data-dd-action-name="..." — DataDog tracking (sidebar-new-item, sidebar-nav-item)
# data-radix-collection-item="" — Radix UI collection item marker
# aria-pressed="true" / "false" — toggle buttons (appearance settings)
# aria-expanded="true" / "false" — expandable triggers
# aria-checked="true" / "false" — checkbox menu items


# =============================================================================
# KEYBOARD SHORTCUTS
# =============================================================================

SHORTCUTS = {
    "new_chat": "Control+Shift+o",
    "search": "Control+k",
    "upload_files": "Control+u",
    "settings": "Shift+Control+,",
    "notifications": "F8",
}
