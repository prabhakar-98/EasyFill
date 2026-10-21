from playwright.async_api import async_playwright, Browser, Playwright

from app.config.settings import settings
from app.logging import get_logger

logger = get_logger("browser_manager")


class BrowserManager:
    def __init__(self):
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None

    async def start(self) -> None:
        if self._browser:
            logger.warning("browser_already_running")
            return

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=settings.browser_headless,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        )
        logger.info("browser_started", headless=settings.browser_headless)

    async def stop(self) -> None:
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        logger.info("browser_stopped")

    def is_running(self) -> bool:
        return self._browser is not None and self._browser.is_connected()

    async def ensure_running(self) -> None:
        if not self.is_running():
            await self.start()

    def get_browser(self) -> Browser:
        if not self._browser or not self._browser.is_connected():
            raise RuntimeError("Browser not running. Call start() first.")
        return self._browser


browser_manager = BrowserManager()
