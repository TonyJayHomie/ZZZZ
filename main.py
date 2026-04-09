"""
Claude Web Wrapper — Entry Point

DOM automation bridge for claude.ai → OpenAI-compatible API.
Zero credentials. Uses Playwright persistent browser context.

Usage:
  First run (login):  python main.py --headed
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
        "--headed",
        action="store_true",
        help="Run browser in headed mode (for first-time login)",
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
    log.info("  Headless:  %s", not args.headed)
    log.info("  Data dir:  %s", args.user_data_dir)
    log.info("")

    # Launch browser
    browser = BrowserManager(
        headless=not args.headed,
        user_data_dir=args.user_data_dir,
    )

    try:
        page = await browser.start()

        # Check login status
        logged_in = await browser.is_logged_in()
        if logged_in:
            log.info("[OK] Logged into claude.ai — ready to serve")
        else:
            if args.headed:
                log.info(
                    "[LOGIN] Browser is open — please log into claude.ai manually"
                )
                log.info("[LOGIN] The server will start once you're logged in")
                log.info("[LOGIN] Press Ctrl+C to stop")
                # Wait for login
                while not await browser.is_logged_in():
                    await asyncio.sleep(2)
                log.info("[OK] Login detected — starting server")
            else:
                log.warning(
                    "[WARN] Not logged in. Restart with --headed to log in:"
                )
                log.warning("       python main.py --headed")
                log.warning("")
                log.warning("  The browser will open. Log into claude.ai.")
                log.warning("  Your session persists in: %s", args.user_data_dir)
                log.warning("  After login, restart without --headed.")

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
