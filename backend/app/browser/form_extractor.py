from playwright.async_api import Page

from app.browser.schemas import FormField, FormData
from app.logging import get_logger

logger = get_logger("form_extractor")

GOOGLE_FORMS_JS = """
() => {
    const result = {
        form_title: '',
        form_description: null,
        fields: []
    };

    // Extract form title
    const titleEl = document.querySelector('[role="heading"][aria-level="1"]')
        || document.querySelector('.freebirdFormviewerViewHeaderTitle');
    if (titleEl) {
        result.form_title = titleEl.textContent.trim();
    }

    // Extract form description
    const descEl = document.querySelector('.freebirdFormviewerViewHeaderDescription');
    if (descEl && descEl.textContent.trim()) {
        result.form_description = descEl.textContent.trim();
    }

    // Find all question containers
    const questions = document.querySelectorAll('[role="listitem"]');

    questions.forEach((q, index) => {
        const field = {
            field_id: '',
            label: '',
            description: null,
            placeholder: null,
            validation: null,
            type: 'text',
            required: false,
            value: null,
            options: null,
            section: 0
        };

        // Extract label
        const labelEl = q.querySelector('[role="heading"]')
            || q.querySelector('.freebirdFormviewerComponentsQuestionBaseTitle');
        if (labelEl) {
            field.label = labelEl.textContent.trim().replace(/\\s*\\*$/, '');
        }

        // Check required (asterisk indicator)
        const requiredEl = q.querySelector('[aria-label="Required question"]')
            || q.querySelector('.freebirdFormviewerComponentsQuestionBaseRequiredAsterisk');
        field.required = !!requiredEl;

        // Extract description/help text
        const descEl = q.querySelector('.freebirdFormviewerComponentsQuestionBaseDescription');
        if (descEl && descEl.textContent.trim()) {
            field.description = descEl.textContent.trim();
        }

        // Extract field_id from data-params or input name
        const dataParamsEl = q.querySelector('[data-params]');
        if (dataParamsEl) {
            const params = dataParamsEl.getAttribute('data-params');
            const match = params.match(/\\[\\s*(\\d+)/);
            if (match) {
                field.field_id = 'entry.' + match[1];
            }
        }
        // Fallback: find from input name
        if (!field.field_id) {
            const inputEl = q.querySelector('input[name^="entry."], textarea[name^="entry."]');
            if (inputEl) {
                field.field_id = inputEl.getAttribute('name');
            }
        }
        // Fallback: generate from index
        if (!field.field_id) {
            field.field_id = 'field_' + index;
        }

        // Detect field type and extract options
        const textInput = q.querySelector('input[type="text"], input:not([type])');
        const textArea = q.querySelector('textarea');
        const radios = q.querySelectorAll('[role="radio"]');
        const checkboxes = q.querySelectorAll('[role="checkbox"]');
        const dropdown = q.querySelector('[role="listbox"]');
        const dateInputs = q.querySelectorAll('input[type="date"], input[aria-label*="Day"], input[aria-label*="Month"], input[aria-label*="Year"]');
        const timeInputs = q.querySelectorAll('input[type="time"], input[aria-label*="Hour"], input[aria-label*="Minute"]');
        const fileInput = q.querySelector('input[type="file"]');

        if (fileInput) {
            field.type = 'file';
        } else if (dateInputs.length > 0) {
            field.type = 'date';
        } else if (timeInputs.length > 0) {
            field.type = 'time';
        } else if (radios.length > 0) {
            const opts = [];
            let allNumeric = true;
            radios.forEach(r => {
                const label = r.getAttribute('aria-label')
                    || r.querySelector('[dir="auto"]')?.textContent?.trim()
                    || r.textContent.trim();
                if (label) {
                    opts.push(label);
                    if (isNaN(Number(label))) allNumeric = false;
                }
            });
            field.options = opts;
            field.type = (allNumeric && opts.length >= 2) ? 'scale' : 'radio';
        } else if (checkboxes.length > 0) {
            field.type = 'checkbox';
            const opts = [];
            checkboxes.forEach(c => {
                const label = c.getAttribute('aria-label')
                    || c.querySelector('[dir="auto"]')?.textContent?.trim()
                    || c.textContent.trim();
                if (label) opts.push(label);
            });
            field.options = opts;
        } else if (dropdown) {
            field.type = 'dropdown';
            const opts = [];
            dropdown.querySelectorAll('[role="option"]').forEach(o => {
                const text = o.textContent.trim();
                if (text && text !== 'Choose') opts.push(text);
            });
            field.options = opts;
        } else if (textArea) {
            field.type = 'textarea';
            if (textArea.placeholder) {
                field.placeholder = textArea.placeholder;
            }
        } else if (textInput) {
            field.type = 'text';
            if (textInput.placeholder) {
                field.placeholder = textInput.placeholder;
            }
        }

        // Extract validation hint
        const validationEl = q.querySelector('.freebirdFormviewerComponentsQuestionBaseValidationError')
            || q.querySelector('[role="alert"]');
        if (validationEl && validationEl.textContent.trim()) {
            field.validation = validationEl.textContent.trim();
        }

        // Only add if we found a label (skip empty containers)
        if (field.label) {
            result.fields.push(field);
        }
    });

    return result;
}
"""


def is_google_form(url: str) -> bool:
    return "docs.google.com/forms" in url


async def extract_form(page: Page) -> FormData:
    url = page.url
    if not is_google_form(url):
        raise ValueError(f"Not a Google Form: {url}")

    await page.wait_for_load_state("networkidle")

    raw = await page.evaluate(GOOGLE_FORMS_JS)

    fields = [FormField(**f) for f in raw.get("fields", [])]
    required_count = sum(1 for f in fields if f.required)

    form_data = FormData(
        form_title=raw.get("form_title", "Untitled Form"),
        form_description=raw.get("form_description"),
        total_fields=len(fields),
        required_fields=required_count,
        fields=fields,
    )

    logger.info(
        "form_extracted",
        url=url,
        title=form_data.form_title,
        total_fields=form_data.total_fields,
        required_fields=form_data.required_fields,
    )

    return form_data
