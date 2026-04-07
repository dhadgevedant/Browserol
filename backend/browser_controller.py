import asyncio
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright, Browser, Page, Playwright

# Fallback selectors for common sites
YOUTUBE_SELECTORS = [
    "ytd-video-renderer a#thumbnail",
    "a#video-title",
    "ytd-rich-item-renderer a#thumbnail"
]

GOOGLE_SELECTORS = [
    "h3",
    "a h3"
]

AMAZON_SELECTORS = [
    "div.s-main-slot a",
    "h2 a"
]

AMAZON_INPUT_SELECTORS = [
    "input#twotabsearchtextbox",
    "input[name='field-keywords']",
    "input[name='q']",
    "input[type='search']"
]


class BrowserController:
    """Wraps Playwright browser and page operations for automation."""

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        """Start Playwright and open a browser page."""
        async with self._lock:
            if self.page is not None:
                return
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=self.headless)
            self.page = await self.browser.new_page()

    async def close(self) -> None:
        """Close the browser and shutdown Playwright."""
        async with self._lock:
            if self.browser is not None:
                await self.browser.close()
            if self.playwright is not None:
                await self.playwright.stop()
            self.browser = None
            self.page = None
            self.playwright = None

    async def open_url(self, url: str) -> dict:
        """Navigate the browser to the requested URL."""
        assert self.page is not None, "Browser page is not initialized."
        await self.page.goto(url, wait_until="domcontentloaded")
        return {"action": "open_url", "url": url}

    async def click(self, selector: str) -> dict:
        """Click on an element by selector with fallbacks."""
        assert self.page is not None, "Browser page is not initialized."
        try:
            locator = self.page.locator(selector)
            await locator.first.wait_for(state="visible", timeout=8000)
            await locator.first.click()
            return {"action": "click", "selector": selector, "method": "primary"}
        except Exception as e:
            # Try fallback selectors based on current URL
            current_url = self.page.url
            if "youtube.com" in current_url:
                fallbacks = YOUTUBE_SELECTORS
            elif "google.com" in current_url:
                fallbacks = GOOGLE_SELECTORS
            elif "amazon.com" in current_url:
                fallbacks = AMAZON_SELECTORS
            else:
                fallbacks = []

            if fallbacks:
                return await self.click_first_available(fallbacks)
            else:
                raise e

    async def click_first_available(self, selectors: list) -> dict:
        """Click the first available element from a list of selectors."""
        assert self.page is not None, "Browser page is not initialized."
        for sel in selectors:
            try:
                locator = self.page.locator(sel)
                count = await locator.count()
                if count > 0:
                    await locator.first.wait_for(state="visible", timeout=5000)
                    await locator.first.click()
                    return {"action": "click", "selector": sel, "method": "fallback"}
            except Exception:
                continue
        raise ValueError(f"No clickable elements found for selectors: {selectors}")

    async def type(self, selector: str, text: str) -> dict:
        """Type text into an input field with fallback selectors."""
        assert self.page is not None, "Browser page is not initialized."
        try:
            locator = self.page.locator(selector)
            await locator.first.wait_for(state="visible", timeout=8000)
            await locator.first.fill(text)
            return {"action": "type", "selector": selector, "value": text, "method": "primary"}
        except Exception as e:
            current_url = self.page.url
            if "amazon.com" in current_url or "amazon.co" in current_url:
                return await self.type_first_available(AMAZON_INPUT_SELECTORS, text)
            raise e

    async def type_first_available(self, selectors: list, text: str) -> dict:
        """Type into the first available input field from a list of selectors."""
        assert self.page is not None, "Browser page is not initialized."
        for sel in selectors:
            try:
                locator = self.page.locator(sel)
                count = await locator.count()
                if count > 0:
                    await locator.first.wait_for(state="visible", timeout=5000)
                    await locator.first.fill(text)
                    return {"action": "type", "selector": sel, "value": text, "method": "fallback"}
            except Exception:
                continue
        raise ValueError(f"No input field found for selectors: {selectors}")

    async def press(self, key: str) -> dict:
        """Press a key on the page."""
        assert self.page is not None, "Browser page is not initialized."
        await self.page.keyboard.press(key)
        return {"action": "press", "key": key}

    async def scroll(self, direction: str = "down", amount: int = 300) -> dict:
        """Scroll the viewport up or down."""
        assert self.page is not None, "Browser page is not initialized."
        if direction.lower() == "down":
            script = f"window.scrollBy(0, {amount});"
        else:
            script = f"window.scrollBy(0, -{amount});"
        await self.page.evaluate(script)
        return {"action": "scroll", "direction": direction, "amount": amount}

    async def wait(self, seconds: float) -> dict:
        """Wait for a number of seconds."""
        await asyncio.sleep(seconds)
        return {"action": "wait", "seconds": seconds}

    async def screenshot(self, path: Optional[str] = None) -> str:
        """Capture a screenshot and return the path."""
        assert self.page is not None, "Browser page is not initialized."
        output_dir = Path("backend").resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        screenshot_path = output_dir / (path or "screenshot.png")
        await self.page.screenshot(path=str(screenshot_path), full_page=True)
        return str(screenshot_path)

    async def navigate_back(self) -> dict:
        """Navigate browser backwards."""
        assert self.page is not None, "Browser page is not initialized."
        await self.page.go_back()
        return {"action": "navigate_back"}

    async def navigate_forward(self) -> dict:
        """Navigate browser forwards."""
        assert self.page is not None, "Browser page is not initialized."
        await self.page.go_forward()
        return {"action": "navigate_forward"}
