import base64

from fastapi import APIRouter

from app.browser.browser_manager import browser_manager
from app.browser.session_manager import session_manager
from app.browser.form_extractor import extract_form, is_google_form
from app.browser.schemas import BrowserOpenRequest, BrowserResponse, BrowserError
from app.logging import get_logger

router = APIRouter()
logger = get_logger("routes_browser")


@router.post("/open", response_model=BrowserResponse)
async def open_browser(request: BrowserOpenRequest):
    try:
        session = await session_manager.create_session(request.task_id)
        await session.page.goto(request.url, wait_until="domcontentloaded")

        title = await session.page.title()

        logger.info("browser_opened", task_id=request.task_id, url=request.url, title=title)

        return BrowserResponse(
            success=True,
            task_id=request.task_id,
            data={
                "session_id": request.task_id,
                "url": request.url,
                "page_title": title,
                "status": "ready",
            },
        )
    except Exception as e:
        await session_manager.close_session(request.task_id)
        logger.error("browser_open_failed", task_id=request.task_id, error=str(e))
        return BrowserResponse(
            success=False,
            task_id=request.task_id,
            error=BrowserError(code="PAGE_LOAD_FAILED", message=str(e)),
        )


@router.get("/{task_id}/state", response_model=BrowserResponse)
async def get_page_state(task_id: str):
    session = session_manager.get_session(task_id)
    if not session:
        return BrowserResponse(
            success=False,
            task_id=task_id,
            error=BrowserError(code="SESSION_NOT_FOUND", message=f"No session for task {task_id}"),
        )

    url = session.page.url
    title = await session.page.title()

    return BrowserResponse(
        success=True,
        task_id=task_id,
        data={
            "url": url,
            "title": title,
            "status": session.status,
        },
    )


@router.get("/{task_id}/screenshot", response_model=BrowserResponse)
async def take_screenshot(task_id: str):
    session = session_manager.get_session(task_id)
    if not session:
        return BrowserResponse(
            success=False,
            task_id=task_id,
            error=BrowserError(code="SESSION_NOT_FOUND", message=f"No session for task {task_id}"),
        )

    try:
        screenshot_bytes = await session.page.screenshot(full_page=True)
        image_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")

        return BrowserResponse(
            success=True,
            task_id=task_id,
            data={
                "image": image_b64,
                "format": "png",
            },
        )
    except Exception as e:
        logger.error("screenshot_failed", task_id=task_id, error=str(e))
        return BrowserResponse(
            success=False,
            task_id=task_id,
            error=BrowserError(code="SCREENSHOT_FAILED", message=str(e)),
        )


@router.post("/{task_id}/extract", response_model=BrowserResponse)
async def extract_form_fields(task_id: str):
    session = session_manager.get_session(task_id)
    if not session:
        return BrowserResponse(
            success=False,
            task_id=task_id,
            error=BrowserError(code="SESSION_NOT_FOUND", message=f"No session for task {task_id}"),
        )

    if not is_google_form(session.page.url):
        return BrowserResponse(
            success=False,
            task_id=task_id,
            error=BrowserError(code="NOT_GOOGLE_FORM", message="Current page is not a Google Form"),
        )

    try:
        form_data = await extract_form(session.page)

        logger.info("form_extracted", task_id=task_id, total_fields=form_data.total_fields)

        return BrowserResponse(
            success=True,
            task_id=task_id,
            data=form_data.model_dump(),
        )
    except Exception as e:
        logger.error("form_extraction_failed", task_id=task_id, error=str(e))
        return BrowserResponse(
            success=False,
            task_id=task_id,
            error=BrowserError(code="EXTRACTION_FAILED", message=str(e)),
        )


@router.post("/{task_id}/close", response_model=BrowserResponse)
async def close_browser_session(task_id: str):
    closed = await session_manager.close_session(task_id)
    if not closed:
        return BrowserResponse(
            success=False,
            task_id=task_id,
            error=BrowserError(code="SESSION_NOT_FOUND", message=f"No session for task {task_id}"),
        )

    return BrowserResponse(
        success=True,
        task_id=task_id,
        data={"status": "closed"},
    )


@router.get("/status")
async def browser_status():
    return BrowserResponse(
        success=True,
        task_id="system",
        data={
            "browser_running": browser_manager.is_running(),
            "active_sessions": session_manager.active_count,
        },
    )
