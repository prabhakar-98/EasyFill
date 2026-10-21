from app.logging import get_logger
from app.tools.base import ToolContext, ToolOutput

logger = get_logger("browser_tools")

FIND_FIELD_JS = """
(fieldId) => {
    // Extract numeric ID from "entry.123456"
    const numId = fieldId.replace('entry.', '');

    // Strategy 1: Find by input/textarea name attribute
    let input = document.querySelector(`input[name="${fieldId}"], textarea[name="${fieldId}"]`);
    if (input) return { found: true, strategy: 'name' };

    // Strategy 2: Find container with data-params containing the entry ID
    const containers = document.querySelectorAll('[data-params]');
    for (const container of containers) {
        const params = container.getAttribute('data-params');
        if (params && params.includes(numId)) {
            input = container.querySelector('input[type="text"], input:not([type]), textarea');
            if (input) return { found: true, strategy: 'data-params' };
        }
    }

    // Strategy 3: Find by aria attributes
    const allInputs = document.querySelectorAll('input, textarea');
    for (const el of allInputs) {
        const name = el.getAttribute('name') || '';
        const ariaDesc = el.getAttribute('aria-describedby') || '';
        if (name.includes(numId) || ariaDesc.includes(numId)) {
            return { found: true, strategy: 'aria' };
        }
    }

    return { found: false, strategy: null };
}
"""

FILL_BY_ENTRY_JS = """
(args) => {
    const { fieldId, value } = args;
    const numId = fieldId.replace('entry.', '');

    // Strategy 1: name attribute
    let input = document.querySelector(`input[name="${fieldId}"], textarea[name="${fieldId}"]`);

    // Strategy 2: data-params container
    if (!input) {
        const containers = document.querySelectorAll('[data-params]');
        for (const container of containers) {
            const params = container.getAttribute('data-params');
            if (params && params.includes(numId)) {
                input = container.querySelector('input[type="text"], input:not([type]), textarea');
                if (input) break;
            }
        }
    }

    if (!input) return { filled: false, error: 'Input not found' };

    // Focus and fill
    input.focus();
    input.value = value;
    input.dispatchEvent(new Event('input', { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));

    return { filled: true, error: null };
}
"""

GET_VALUE_BY_ENTRY_JS = """
(fieldId) => {
    const numId = fieldId.replace('entry.', '');

    let input = document.querySelector(`input[name="${fieldId}"], textarea[name="${fieldId}"]`);

    if (!input) {
        const containers = document.querySelectorAll('[data-params]');
        for (const container of containers) {
            const params = container.getAttribute('data-params');
            if (params && params.includes(numId)) {
                input = container.querySelector('input[type="text"], input:not([type]), textarea');
                if (input) break;
            }
        }
    }

    if (!input) return { found: false, value: null };
    return { found: true, value: input.value };
}
"""


async def fill_field(context: ToolContext, field_id: str, value: str) -> ToolOutput:
    """Fill a text or textarea field by its entry ID."""
    try:
        page = context.page

        result = await page.evaluate(FILL_BY_ENTRY_JS, {"fieldId": field_id, "value": value})

        if not result.get("filled"):
            return ToolOutput(success=False, error=f"Field not found: {field_id}")

        logger.info("field_filled", task_id=context.task_id, field_id=field_id)
        return ToolOutput(success=True, data={"field_id": field_id, "value": value})
    except Exception as e:
        logger.error("fill_field_failed", task_id=context.task_id, field_id=field_id, error=str(e))
        return ToolOutput(success=False, error=str(e))


async def select_radio(context: ToolContext, field_id: str, option: str) -> ToolOutput:
    """Select a radio button option within a specific field container."""
    try:
        page = context.page
        num_id = field_id.replace("entry.", "")

        clicked = await page.evaluate("""
            (args) => {
                const { numId, option } = args;
                const containers = document.querySelectorAll('[data-params]');
                for (const container of containers) {
                    const params = container.getAttribute('data-params');
                    if (params && params.includes(numId)) {
                        const radios = container.querySelectorAll('[role="radio"]');
                        for (const radio of radios) {
                            const label = radio.getAttribute('aria-label')
                                || radio.querySelector('[dir="auto"]')?.textContent?.trim()
                                || radio.textContent.trim();
                            if (label === option) {
                                radio.click();
                                return true;
                            }
                        }
                    }
                }
                return false;
            }
        """, {"numId": num_id, "option": option})

        if not clicked:
            return ToolOutput(success=False, error=f"Radio option not found: {option}")

        logger.info("radio_selected", task_id=context.task_id, field_id=field_id, option=option)
        return ToolOutput(success=True, data={"field_id": field_id, "option": option})
    except Exception as e:
        logger.error("select_radio_failed", task_id=context.task_id, field_id=field_id, error=str(e))
        return ToolOutput(success=False, error=str(e))


async def check_checkbox(context: ToolContext, field_id: str, option: str, checked: bool = True) -> ToolOutput:
    """Check or uncheck a checkbox option within a specific field container."""
    try:
        page = context.page
        num_id = field_id.replace("entry.", "")

        result = await page.evaluate("""
            (args) => {
                const { numId, option, checked } = args;
                const containers = document.querySelectorAll('[data-params]');
                for (const container of containers) {
                    const params = container.getAttribute('data-params');
                    if (params && params.includes(numId)) {
                        const checkboxes = container.querySelectorAll('[role="checkbox"]');
                        for (const cb of checkboxes) {
                            const label = cb.getAttribute('aria-label')
                                || cb.querySelector('[dir="auto"]')?.textContent?.trim()
                                || cb.textContent.trim();
                            if (label === option) {
                                const isChecked = cb.getAttribute('aria-checked') === 'true';
                                if (checked !== isChecked) {
                                    cb.click();
                                }
                                return { found: true };
                            }
                        }
                    }
                }
                return { found: false };
            }
        """, {"numId": num_id, "option": option, "checked": checked})

        if not result.get("found"):
            return ToolOutput(success=False, error=f"Checkbox option not found: {option}")

        logger.info("checkbox_toggled", task_id=context.task_id, field_id=field_id, option=option, checked=checked)
        return ToolOutput(success=True, data={"field_id": field_id, "option": option, "checked": checked})
    except Exception as e:
        logger.error("check_checkbox_failed", task_id=context.task_id, field_id=field_id, error=str(e))
        return ToolOutput(success=False, error=str(e))


async def select_dropdown(context: ToolContext, field_id: str, option: str) -> ToolOutput:
    """Select a dropdown option within a specific field container."""
    try:
        page = context.page
        num_id = field_id.replace("entry.", "")

        # Find and click the dropdown in the right container
        opened = await page.evaluate("""
            (numId) => {
                const containers = document.querySelectorAll('[data-params]');
                for (const container of containers) {
                    const params = container.getAttribute('data-params');
                    if (params && params.includes(numId)) {
                        const dropdown = container.querySelector('[role="listbox"]');
                        if (dropdown) {
                            dropdown.click();
                            return true;
                        }
                    }
                }
                return false;
            }
        """, num_id)

        if not opened:
            return ToolOutput(success=False, error="Dropdown not found")

        await page.wait_for_timeout(300)

        option_el = page.locator('[role="option"]').filter(has_text=option)

        if await option_el.count() == 0:
            return ToolOutput(success=False, error=f"Dropdown option not found: {option}")

        await option_el.first.click()

        logger.info("dropdown_selected", task_id=context.task_id, field_id=field_id, option=option)
        return ToolOutput(success=True, data={"field_id": field_id, "option": option})
    except Exception as e:
        logger.error("select_dropdown_failed", task_id=context.task_id, field_id=field_id, error=str(e))
        return ToolOutput(success=False, error=str(e))


async def fill_date(context: ToolContext, field_id: str, day: str, month: str, year: str) -> ToolOutput:
    """Fill a date field with day, month, year values."""
    try:
        page = context.page
        num_id = field_id.replace("entry.", "")

        result = await page.evaluate("""
            (args) => {
                const { numId, day, month, year } = args;
                const containers = document.querySelectorAll('[data-params]');
                for (const container of containers) {
                    const params = container.getAttribute('data-params');
                    if (params && params.includes(numId)) {
                        const dayInput = container.querySelector('input[aria-label*="Day"]');
                        const monthInput = container.querySelector('input[aria-label*="Month"]');
                        const yearInput = container.querySelector('input[aria-label*="Year"]');

                        const fill = (el, val) => {
                            if (!el) return;
                            el.focus();
                            el.value = val;
                            el.dispatchEvent(new Event('input', { bubbles: true }));
                            el.dispatchEvent(new Event('change', { bubbles: true }));
                        };

                        fill(dayInput, day);
                        fill(monthInput, month);
                        fill(yearInput, year);
                        return { found: true };
                    }
                }
                return { found: false };
            }
        """, {"numId": num_id, "day": day, "month": month, "year": year})

        if not result.get("found"):
            return ToolOutput(success=False, error=f"Date field not found: {field_id}")

        logger.info("date_filled", task_id=context.task_id, field_id=field_id)
        return ToolOutput(success=True, data={"field_id": field_id, "day": day, "month": month, "year": year})
    except Exception as e:
        logger.error("fill_date_failed", task_id=context.task_id, field_id=field_id, error=str(e))
        return ToolOutput(success=False, error=str(e))


async def fill_time(context: ToolContext, field_id: str, hour: str, minute: str) -> ToolOutput:
    """Fill a time field with hour and minute values."""
    try:
        page = context.page
        num_id = field_id.replace("entry.", "")

        result = await page.evaluate("""
            (args) => {
                const { numId, hour, minute } = args;
                const containers = document.querySelectorAll('[data-params]');
                for (const container of containers) {
                    const params = container.getAttribute('data-params');
                    if (params && params.includes(numId)) {
                        const hourInput = container.querySelector('input[aria-label*="Hour"]');
                        const minuteInput = container.querySelector('input[aria-label*="Minute"]');

                        const fill = (el, val) => {
                            if (!el) return;
                            el.focus();
                            el.value = val;
                            el.dispatchEvent(new Event('input', { bubbles: true }));
                            el.dispatchEvent(new Event('change', { bubbles: true }));
                        };

                        fill(hourInput, hour);
                        fill(minuteInput, minute);
                        return { found: true };
                    }
                }
                return { found: false };
            }
        """, {"numId": num_id, "hour": hour, "minute": minute})

        if not result.get("found"):
            return ToolOutput(success=False, error=f"Time field not found: {field_id}")

        logger.info("time_filled", task_id=context.task_id, field_id=field_id)
        return ToolOutput(success=True, data={"field_id": field_id, "hour": hour, "minute": minute})
    except Exception as e:
        logger.error("fill_time_failed", task_id=context.task_id, field_id=field_id, error=str(e))
        return ToolOutput(success=False, error=str(e))


async def upload_file(context: ToolContext, field_id: str, file_path: str) -> ToolOutput:
    """Upload a file to a file upload field."""
    try:
        page = context.page

        file_input = page.locator('input[type="file"]')

        if await file_input.count() == 0:
            return ToolOutput(success=False, error="File upload field not found")

        await file_input.first.set_input_files(file_path)

        logger.info("file_uploaded", task_id=context.task_id, field_id=field_id, file=file_path)
        return ToolOutput(success=True, data={"field_id": field_id, "file": file_path})
    except Exception as e:
        logger.error("upload_file_failed", task_id=context.task_id, field_id=field_id, error=str(e))
        return ToolOutput(success=False, error=str(e))


async def select_scale(context: ToolContext, field_id: str, value: str) -> ToolOutput:
    """Select a value on a linear scale (1-5, 1-10, etc.)."""
    try:
        page = context.page
        num_id = field_id.replace("entry.", "")

        clicked = await page.evaluate("""
            (args) => {
                const { numId, value } = args;
                const containers = document.querySelectorAll('[data-params]');
                for (const container of containers) {
                    const params = container.getAttribute('data-params');
                    if (params && params.includes(numId)) {
                        const radios = container.querySelectorAll('[role="radio"]');
                        for (const radio of radios) {
                            const label = radio.getAttribute('aria-label')
                                || radio.textContent.trim();
                            if (label === value) {
                                radio.click();
                                return true;
                            }
                        }
                    }
                }
                return false;
            }
        """, {"numId": num_id, "value": value})

        if not clicked:
            return ToolOutput(success=False, error=f"Scale value not found: {value}")

        logger.info("scale_selected", task_id=context.task_id, field_id=field_id, value=value)
        return ToolOutput(success=True, data={"field_id": field_id, "value": value})
    except Exception as e:
        logger.error("select_scale_failed", task_id=context.task_id, field_id=field_id, error=str(e))
        return ToolOutput(success=False, error=str(e))


async def click_element(context: ToolContext, selector: str) -> ToolOutput:
    """Click an element by CSS selector or text."""
    try:
        page = context.page

        element = page.locator(selector)

        if await element.count() == 0:
            element = page.get_by_text(selector)

        if await element.count() == 0:
            return ToolOutput(success=False, error=f"Element not found: {selector}")

        await element.first.click()

        logger.info("element_clicked", task_id=context.task_id, selector=selector)
        return ToolOutput(success=True, data={"selector": selector})
    except Exception as e:
        logger.error("click_element_failed", task_id=context.task_id, selector=selector, error=str(e))
        return ToolOutput(success=False, error=str(e))


async def get_field_value(context: ToolContext, field_id: str) -> ToolOutput:
    """Read the current value of a field."""
    try:
        page = context.page

        result = await page.evaluate(GET_VALUE_BY_ENTRY_JS, field_id)

        if not result.get("found"):
            return ToolOutput(success=False, error=f"Field not found: {field_id}")

        return ToolOutput(success=True, data={"field_id": field_id, "value": result["value"]})
    except Exception as e:
        logger.error("get_field_value_failed", task_id=context.task_id, field_id=field_id, error=str(e))
        return ToolOutput(success=False, error=str(e))


async def submit_form(context: ToolContext) -> ToolOutput:
    """Click the form's submit button."""
    try:
        page = context.page

        submit_btn = page.locator('[role="button"]').filter(has_text="Submit")

        if await submit_btn.count() == 0:
            submit_btn = page.locator('button').filter(has_text="Submit")

        if await submit_btn.count() == 0:
            return ToolOutput(success=False, error="Submit button not found")

        await submit_btn.first.click()

        await page.wait_for_load_state("networkidle")

        logger.info("form_submitted", task_id=context.task_id)
        return ToolOutput(success=True, data={"status": "submitted"})
    except Exception as e:
        logger.error("submit_form_failed", task_id=context.task_id, error=str(e))
        return ToolOutput(success=False, error=str(e))
