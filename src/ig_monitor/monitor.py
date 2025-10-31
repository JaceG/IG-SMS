import asyncio
import gc
import hashlib
import os
import random
from datetime import datetime, timezone
from typing import Optional

from playwright.async_api import async_playwright, Browser, Page

from ig_monitor.config import get_settings
from ig_monitor.state import (
    get_last_seen_id,
    set_last_seen_id,
    is_running,
    set_running,
    set_last_login_ts,
)
from ig_monitor.sms import send_sms


settings = get_settings()


_monitor_task: Optional[asyncio.Task] = None
_browser: Optional[Browser] = None
_page: Optional[Page] = None


def _data_paths() -> tuple[str, str]:
    os.makedirs(settings.data_dir, exist_ok=True)
    user_data_dir = os.path.join(settings.data_dir, settings.user_data_dir_name)
    os.makedirs(user_data_dir, exist_ok=True)
    return user_data_dir, settings.ig_thread_url


async def _ensure_browser() -> Page:
    global _browser, _page
    if _page is not None:
        return _page

    user_data_dir, _ = _data_paths()
    pw = await async_playwright().start()
    
    # Check if we should run headless (default True for Render, False for local with visible browser)
    # Set HEADLESS_BROWSER=false to see the browser locally
    headless = os.getenv("HEADLESS_BROWSER", "true").lower() != "false"
    
    _browser = await pw.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        headless=headless,
        args=[
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--disable-gpu",
            # Memory optimization flags
            "--disable-background-networking",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-breakpad",
            "--disable-client-side-phishing-detection",
            "--disable-component-extensions-with-background-pages",
            "--disable-default-apps",
            "--disable-extensions",
            "--disable-features=TranslateUI",
            "--disable-hang-monitor",
            "--disable-ipc-flooding-protection",
            "--disable-notifications",
            "--disable-offer-store-unmasked-wallet-cards",
            "--disable-popup-blocking",
            "--disable-prompt-on-repost",
            "--disable-renderer-backgrounding",
            "--disable-setuid-sandbox",
            "--disable-sync",
            "--disable-web-resources",
            "--enable-features=NetworkService,NetworkServiceLogging",
            "--force-color-profile=srgb",
            "--hide-scrollbars",
            "--ignore-gpu-blacklist",
            "--metrics-recording-only",
            "--mute-audio",
            "--no-first-run",
            "--no-default-browser-check",
            "--no-pings",
            "--no-zygote",
            "--use-mock-keychain",
            # JavaScript memory limits (for Chromium's V8 engine)
            "--js-flags=--max-old-space-size=256",
        ],
        viewport={"width": 800, "height": 600},  # Smaller viewport saves memory
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        ),
    )

    _page = await _browser.new_page()
    return _page


async def is_logged_in(page: Page) -> bool:
    """Check if currently logged into Instagram"""
    # Heuristic: presence of the DM thread container vs login form
    if "login" in page.url.lower():
        return False
    try:
        # Typical IG app container when logged in
        await page.wait_for_selector("[role='main']", timeout=1500)
        return True
    except Exception:
        return False


# Backward compatibility alias - use is_logged_in instead
_is_logged_in = is_logged_in


async def open_thread_and_wait_ready(page: Page) -> None:
    _, thread_url = _data_paths()
    await page.goto(thread_url, wait_until="domcontentloaded")
    # Give time for React app to render
    await page.wait_for_timeout(1500)

    if not await is_logged_in(page):
        # Notify and rely on user to log in manually (first run)
        send_sms(settings.owner_phone, "IG Monitor: login required. Please log in via the hosted session.")
        # Keep page open for manual login window
        # Poll until logged in or timeout (~10 minutes)
        for _ in range(120):
            if await is_logged_in(page):
                await set_last_login_ts(datetime.now(timezone.utc).isoformat())
                break
            await page.wait_for_timeout(5000)

    # Wait for messages area heuristically
    # We target generic message bubble selectors to be resilient
    await page.wait_for_selector("[role='main']", timeout=30000)


async def _extract_latest_message_id_and_text(page: Page) -> Optional[tuple[str, str]]:
    # Try to query message bubbles and take the last one
    # We use a generic approach due to frequent DOM changes, fallback by hashing text+time
    elements = await page.query_selector_all("[role='main'] div:has-text('\n')")
    if not elements:
        return None

    # Scan last N elements to find a plausible message node with visible text
    # Reduced from 30 to 10 to save memory
    for el in reversed(elements[-10:]):
        try:
            txt = (await el.inner_text()).strip()
            if not txt:
                continue
            # Create a synthetic id from text and position/time; IG may not expose stable ids in DOM
            synthetic = hashlib.sha1((txt[:200]).encode("utf-8")).hexdigest()
            return synthetic, txt
        except Exception:
            continue
    return None


async def _monitor_loop() -> None:
    try:
        page = await _ensure_browser()
        await open_thread_and_wait_ready(page)

        while await is_running():
            # Jittered sleep to avoid regular pattern
            base = max(10, settings.poll_seconds)
            jitter = random.uniform(-0.2, 0.2) * base
            sleep_for = int(base + jitter)

            try:
                latest = await _extract_latest_message_id_and_text(page)
                if latest:
                    latest_id, latest_text = latest
                    last_seen = await get_last_seen_id()
                    if last_seen != latest_id:
                        await set_last_seen_id(latest_id)
                        preview = latest_text if len(latest_text) <= 300 else latest_text[:297] + "..."
                        send_sms(settings.owner_phone, f"IG: {preview}")
            except Exception as e:
                send_sms(settings.owner_phone, f"IG Monitor error: {e}")

            await asyncio.sleep(sleep_for)
            
            # Periodic garbage collection to free memory (every 10 iterations)
            if random.randint(1, 10) == 1:
                gc.collect()
    finally:
        # Do not close persistent context to preserve session across runs
        pass


def is_monitor_running() -> bool:
    return _monitor_task is not None and not _monitor_task.done()


async def start_monitor() -> str:
    global _monitor_task
    if is_monitor_running():
        return "already_running"
    await set_running(True)
    loop = asyncio.get_running_loop()
    _monitor_task = loop.create_task(_monitor_loop(), name="ig-monitor")
    return "started"


async def stop_monitor() -> str:
    global _monitor_task
    await set_running(False)
    if _monitor_task and not _monitor_task.done():
        _monitor_task.cancel()
        try:
            await _monitor_task
        except asyncio.CancelledError:
            pass
    _monitor_task = None
    return "stopped"


async def get_browser_page() -> Page:
    """Get the browser page for remote interaction"""
    return await _ensure_browser()


