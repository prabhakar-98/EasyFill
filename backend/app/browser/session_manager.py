from dataclasses import dataclass, field
from datetime import datetime, timezone

from playwright.async_api import BrowserContext, Page

from app.browser.browser_manager import browser_manager
from app.config.settings import settings
from app.logging import get_logger

logger = get_logger("session_manager")


@dataclass
class BrowserSession:
    task_id: str
    context: BrowserContext
    page: Page
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "active"


class SessionManager:
    def __init__(self):
        self._sessions: dict[str, BrowserSession] = {}

    async def create_session(self, task_id: str) -> BrowserSession:
        if task_id in self._sessions:
            logger.warning("session_already_exists", task_id=task_id)
            return self._sessions[task_id]

        if len(self._sessions) >= settings.browser_max_sessions:
            raise RuntimeError(
                f"Max sessions reached ({settings.browser_max_sessions}). Close a session first."
            )

        await browser_manager.ensure_running()
        browser = browser_manager.get_browser()

        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="en-US",
        )
        context.set_default_timeout(settings.browser_timeout)

        page = await context.new_page()

        session = BrowserSession(
            task_id=task_id,
            context=context,
            page=page,
        )
        self._sessions[task_id] = session

        logger.info("session_created", task_id=task_id)
        return session

    def get_session(self, task_id: str) -> BrowserSession | None:
        return self._sessions.get(task_id)

    async def close_session(self, task_id: str) -> bool:
        session = self._sessions.pop(task_id, None)
        if not session:
            return False

        session.status = "closed"
        await session.page.close()
        await session.context.close()

        logger.info("session_closed", task_id=task_id)
        return True

    async def close_all(self) -> None:
        task_ids = list(self._sessions.keys())
        for task_id in task_ids:
            await self.close_session(task_id)
        logger.info("all_sessions_closed", count=len(task_ids))

    @property
    def active_count(self) -> int:
        return len(self._sessions)


session_manager = SessionManager()
