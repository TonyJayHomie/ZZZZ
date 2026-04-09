"""
Claude Web Wrapper — Entry Point

DOM automation bridge for claude.ai → OpenAI-compatible API.
Zero credentials. Uses Playwright persistent browser context.
Browser runs HEADED (minimized) — Cloudflare blocks headless.

Usage:
  First run (login):  python main.py --login
  Normal run:         python main.py
  Custom port:        python main.py --port 3967
"""

import argparse
import asyncio
import logging
import signal
import sys

import uvicorn

import config
from browser import BrowserManager
from server import app, set_browser


def setup_logging(verbose: bool = True):
    """Configure terminal logging with colored prefixes."""
    level = logging.DEBUG if verbose else logging.INFO

    formatter = logging.Formatter(
        fmt="%(asctime)s %(message)s",
        datefmt="%H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Root logger
    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)

    # Quiet down noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("playwright").setLevel(logging.WARNING)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Claude Web Wrapper — OpenAI-compatible API via DOM automation",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=config.PORT,
        help=f"Server port (default: {config.PORT})",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=config.HOST,
        help=f"Server host (default: {config.HOST})",
    )
    parser.add_argument(
        "--login",
        action="store_true",
        help="Open visible browser window for first-time login",
    )
    parser.add_argument(
        "--user-data-dir",
        type=str,
        default=config.USER_DATA_DIR,
        help=f"Browser profile directory (default: {config.USER_DATA_DIR})",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=config.VERBOSE,
        help="Enable verbose debug logging",
    )
    return parser.parse_args()


async def main():
    args = parse_args()
    setup_logging(args.verbose)

    log = logging.getLogger("cww.main")

    log.info("=" * 60)
    log.info("  Claude Web Wrapper")
    log.info("  OpenAI-compatible API via DOM automation")
    log.info("  Zero credentials — pure browser automation")
    log.info("=" * 60)
    log.info("")
    log.info("  Port:      %d", args.port)
    log.info("  Host:      %s", args.host)
    log.info("  Mode:      %s", "LOGIN (visible browser)" if args.login else "BACKGROUND (minimized)")
    log.info("  Data dir:  %s", args.user_data_dir)
    log.info("")

    # Launch browser — always headed (Cloudflare blocks headless)
    browser = BrowserManager(
        login_mode=args.login,
        user_data_dir=args.user_data_dir,
    )

    try:
        page = await browser.start()

        # Check login status
        logged_in = await browser.is_logged_in()
        if logged_in:
            log.info("[OK] Logged into claude.ai — ready to serve")
        else:
            if args.login:
                log.info("")
                log.info("  [LOGIN] Browser is open — log into claude.ai now")
                log.info("  [LOGIN] Server starts automatically after login")
                log.info("  [LOGIN] Press Ctrl+C to cancel")
                log.info("")
                # Wait for login (poll every 2s)
                while not await browser.is_logged_in():
                    await asyncio.sleep(2)
                log.info("[OK] Login detected — starting server")
            else:
                log.warning("")
                log.warning("  [WARN] Not logged in!")
                log.warning("  Run login.bat first to log into claude.ai.")
                log.warning("  Your session persists in: %s", args.user_data_dir)
                log.warning("  After login, run start.bat to serve.")
                log.warning("")
                log.warning("  Starting server anyway (will fail on requests)...")

        # Wire up the browser to the FastAPI server
        set_browser(browser)

        log.info("")
        log.info("  API endpoint: http://%s:%d/v1/chat/completions", args.host, args.port)
        log.info("  Models list:  http://%s:%d/v1/models", args.host, args.port)
        log.info("  Health check: http://%s:%d/health", args.host, args.port)
        log.info("")

        # Start the FastAPI server
        server_config = uvicorn.Config(
            app=app,
            host=args.host,
            port=args.port,
            log_level="warning",
            access_log=False,
        )
        server = uvicorn.Server(server_config)

        # Handle graceful shutdown
        loop = asyncio.get_event_loop()

        def shutdown_handler():
            log.info("[SHUTDOWN] Received shutdown signal")
            server.should_exit = True

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, shutdown_handler)
            except NotImplementedError:
                # Windows doesn't support add_signal_handler
                pass

        await server.serve()

    except KeyboardInterrupt:
        log.info("[SHUTDOWN] Keyboard interrupt")
    finally:
        log.info("[SHUTDOWN] Cleaning up browser...")
        await browser.close()
        log.info("[SHUTDOWN] Done")


if __name__ == "__main__":
    asyncio.run(main())
