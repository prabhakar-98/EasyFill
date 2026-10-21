function extractFields() {
  const fields = [];
  const questions = document.querySelectorAll('[role="listitem"]');

  questions.forEach((question, index) => {
    const field = { index, label: "", type: "unknown", required: false, options: [] };

    const labelEl = question.querySelector('[role="heading"]');
    if (labelEl) {
      field.label = labelEl.textContent.trim().replace(/\s*\*$/, "");
    }

    const requiredEl = question.querySelector('[aria-label*="Required"]') ||
                       question.querySelector('[data-required="true"]');
    if (requiredEl || (labelEl && labelEl.textContent.includes("*"))) {
      field.required = true;
    }

    const descEl = question.querySelector('[role="heading"] + div');
    if (descEl && descEl.textContent.trim()) {
      field.description = descEl.textContent.trim();
    }

    const shortText = question.querySelector('input[type="text"]:not([aria-label*="Hour"]):not([aria-label*="Minute"])');
    const longText = question.querySelector('textarea');
    const radios = question.querySelectorAll('[role="radio"]');
    const checkboxes = question.querySelectorAll('[role="checkbox"]');
    const dropdown = question.querySelector('[role="listbox"]');
    const dateInputs = question.querySelectorAll('input[type="date"], input[aria-label*="Month"], input[aria-label*="Day"], input[aria-label*="Year"]');
    const hourInput = question.querySelector('input[aria-label*="Hour"]');
    const fileUpload = question.querySelector('[aria-label*="upload"], [aria-label*="file"], button[aria-label*="Add file"]');
    const gridRows = question.querySelectorAll('[role="radiogroup"]');

    if (gridRows.length > 1) {
      field.type = "grid";
      field.rows = [];
      field.columns = [];
      gridRows.forEach(row => {
        const rowLabel = row.getAttribute("aria-label") || row.closest("[data-row-label]")?.getAttribute("data-row-label") || "";
        if (rowLabel) field.rows.push(rowLabel);
        if (field.columns.length === 0) {
          row.querySelectorAll('[role="radio"]').forEach(r => {
            const col = r.getAttribute("aria-label") || r.closest("[data-value]")?.getAttribute("data-value") || "";
            if (col) field.columns.push(col);
          });
        }
      });
    } else if (shortText && !hourInput) {
      field.type = "short_text";
      field.element = shortText;
    } else if (longText) {
      field.type = "long_text";
      field.element = longText;
    } else if (radios.length > 0) {
      field.type = "multiple_choice";
      radios.forEach(r => {
        const labelText = r.closest("[data-value]")?.getAttribute("data-value") ||
                          r.parentElement?.textContent?.trim() || "";
        if (labelText) field.options.push(labelText);
      });
    } else if (checkboxes.length > 0) {
      field.type = "checkbox";
      checkboxes.forEach(cb => {
        const labelText = cb.closest("[data-answer-value]")?.getAttribute("data-answer-value") ||
                          cb.parentElement?.textContent?.trim() || "";
        if (labelText) field.options.push(labelText);
      });
    } else if (dateInputs.length > 0) {
      field.type = "date";
    } else if (hourInput) {
      field.type = "time";
    } else if (dropdown || question.querySelector('select')) {
      field.type = "dropdown";
      const nativeSelect = question.querySelector('select');
      if (nativeSelect) {
        [...nativeSelect.options].forEach(o => {
          const text = o.text.trim();
          if (text && text.toLowerCase() !== "choose") field.options.push(text);
        });
      } else {
        const opts = question.querySelectorAll('[role="option"]');
        opts.forEach(o => {
          const text = o.textContent.trim();
          if (text && text.toLowerCase() !== "choose") field.options.push(text);
        });
      }
    } else if (fileUpload) {
      field.type = "file_upload";
    }

    if (field.label) {
      fields.push(field);
    }
  });

  return fields;
}

function setNativeValue(el, value) {
  el.focus();
  const proto = Object.getPrototypeOf(el);
  const setter = Object.getOwnPropertyDescriptor(proto, "value")?.set ||
                 Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value")?.set;
  if (setter) {
    setter.call(el, value);
  } else {
    el.value = value;
  }
  el.dispatchEvent(new Event("input", { bubbles: true }));
  el.dispatchEvent(new Event("change", { bubbles: true }));
}

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function simulateClick(el) {
  const rect = el.getBoundingClientRect();
  const x = rect.left + rect.width / 2;
  const y = rect.top + rect.height / 2;
  const evtOpts = { bubbles: true, cancelable: true, clientX: x, clientY: y, view: window };
  el.dispatchEvent(new PointerEvent('pointerdown', { ...evtOpts, pointerId: 1, pointerType: 'mouse' }));
  el.dispatchEvent(new MouseEvent('mousedown', { ...evtOpts, button: 0 }));
  el.dispatchEvent(new PointerEvent('pointerup', { ...evtOpts, pointerId: 1, pointerType: 'mouse' }));
  el.dispatchEvent(new MouseEvent('mouseup', { ...evtOpts, button: 0 }));
  el.dispatchEvent(new MouseEvent('click', { ...evtOpts, button: 0 }));
}

async function extractFieldsWithOptions() {
  const fields = extractFields();
  for (const field of fields) {
    if (field.type === "dropdown" && field.options.length === 0) {
      const question = document.querySelectorAll('[role="listitem"]')[field.index];
      if (!question) continue;

      const nativeSelect = question.querySelector('select');
      if (nativeSelect) {
        [...nativeSelect.options].forEach(o => {
          const text = o.text.trim();
          if (text && text.toLowerCase() !== "choose") field.options.push(text);
        });
        continue;
      }

      const dropdown = question.querySelector('[role="listbox"]');
      if (!dropdown) continue;

      dropdown.scrollIntoView({ block: 'center' });
      await delay(100);
      simulateClick(dropdown);

      let opts = [];
      for (let attempt = 0; attempt < 20; attempt++) {
        await delay(150);
        opts = [...question.querySelectorAll('[role="option"]')];
        if (opts.length <= 1) {
          opts = [...document.querySelectorAll('[role="option"]')];
        }
        if (opts.length > 1) break;
      }

      opts.forEach(o => {
        const text = o.textContent.trim();
        if (text && text.toLowerCase() !== "choose") field.options.push(text);
      });

      document.body.click();
      await delay(300);
    }
  }
  return fields;
}

async function fillField(field, value) {
  if (!value && value !== 0) return false;

  const question = document.querySelectorAll('[role="listitem"]')[field.index];
  if (!question) return false;

  if (field.type === "short_text" || field.type === "long_text") {
    const el = field.type === "short_text"
      ? question.querySelector('input[type="text"]:not([aria-label*="Hour"]):not([aria-label*="Minute"])')
      : question.querySelector("textarea");
    if (!el) return false;
    setNativeValue(el, value);
    return true;
  }

  if (field.type === "date") {
    const parts = String(value).match(/(\d{4})-(\d{1,2})-(\d{1,2})/);
    if (!parts) return false;
    const [, year, month, day] = parts;

    const dateInput = question.querySelector('input[type="date"]');
    if (dateInput) {
      setNativeValue(dateInput, value);
      return true;
    }

    const monthEl = question.querySelector('input[aria-label*="Month"]');
    const dayEl = question.querySelector('input[aria-label*="Day"]');
    const yearEl = question.querySelector('input[aria-label*="Year"]');

    if (monthEl) setNativeValue(monthEl, String(parseInt(month)));
    if (dayEl) setNativeValue(dayEl, String(parseInt(day)));
    if (yearEl) setNativeValue(yearEl, year);

    return !!(monthEl && dayEl);
  }

  if (field.type === "time") {
    let hours, minutes;
    const match24 = String(value).match(/^(\d{1,2}):(\d{2})$/);
    const match12 = String(value).match(/^(\d{1,2}):(\d{2})\s*(AM|PM)$/i);

    if (match12) {
      hours = parseInt(match12[1]);
      minutes = match12[2];
      const period = match12[3].toUpperCase();

      const hourEl = question.querySelector('input[aria-label*="Hour"]');
      const minEl = question.querySelector('input[aria-label*="Minute"]');
      if (hourEl) setNativeValue(hourEl, String(hours));
      if (minEl) setNativeValue(minEl, minutes);

      const ampmOptions = question.querySelectorAll('[role="option"], [role="listbox"] [data-value]');
      for (const opt of ampmOptions) {
        if (opt.textContent.trim().toUpperCase() === period) {
          opt.click();
          break;
        }
      }

      const ampmListbox = question.querySelector('[role="listbox"]');
      if (ampmListbox) {
        ampmListbox.click();
        await delay(200);
        const options = document.querySelectorAll('[role="option"]');
        for (const opt of options) {
          if (opt.textContent.trim().toUpperCase() === period) {
            opt.click();
            break;
          }
        }
      }

      return !!(hourEl && minEl);
    } else if (match24) {
      hours = parseInt(match24[1]);
      minutes = match24[2];
      const hourEl = question.querySelector('input[aria-label*="Hour"]');
      const minEl = question.querySelector('input[aria-label*="Minute"]');
      if (hourEl) setNativeValue(hourEl, String(hours));
      if (minEl) setNativeValue(minEl, minutes);
      return !!(hourEl && minEl);
    }

    return false;
  }

  if (field.type === "multiple_choice") {
    const radios = question.querySelectorAll('[role="radio"]');
    for (const radio of radios) {
      const radioValue = radio.closest("[data-value]")?.getAttribute("data-value") ||
                         radio.parentElement?.textContent?.trim();
      if (radioValue && radioValue.toLowerCase().includes(String(value).toLowerCase())) {
        radio.click();
        return true;
      }
    }
    return false;
  }

  if (field.type === "linear_scale") {
    const target = String(value);
    const radios = question.querySelectorAll('[role="radio"]');
    for (const radio of radios) {
      const dataVal = radio.closest("[data-value]")?.getAttribute("data-value");
      if (dataVal === target) {
        radio.click();
        return true;
      }
    }
    return false;
  }

  if (field.type === "checkbox") {
    const checkboxes = question.querySelectorAll('[role="checkbox"]');
    const values = Array.isArray(value) ? value : [value];
    let filled = false;
    for (const cb of checkboxes) {
      const cbValue = cb.closest("[data-answer-value]")?.getAttribute("data-answer-value") ||
                      cb.parentElement?.textContent?.trim();
      for (const v of values) {
        if (cbValue && cbValue.toLowerCase().includes(String(v).toLowerCase())) {
          cb.click();
          filled = true;
        }
      }
    }
    return filled;
  }

  if (field.type === "dropdown") {
    const target = String(value).toLowerCase().trim();

    // Native <select> dropdown
    const select = question.querySelector('select');
    if (select) {
      for (const opt of select.options) {
        if (opt.text.toLowerCase().trim() === target || opt.value.toLowerCase().trim() === target) {
          select.value = opt.value;
          select.dispatchEvent(new Event('input', { bubbles: true }));
          select.dispatchEvent(new Event('change', { bubbles: true }));
          return true;
        }
      }
    }

    const listbox = question.querySelector('[role="listbox"]');
    if (!listbox) return false;

    // Match helper: exact match first, then partial
    function matchesTarget(el) {
      const t = (el.textContent || '').trim().toLowerCase();
      const d = (el.getAttribute('data-value') || '').toLowerCase();
      if (t === 'choose' || t === '') return false;
      return t === target || d === target;
    }
    function partialMatchesTarget(el) {
      const t = (el.textContent || '').trim().toLowerCase();
      const d = (el.getAttribute('data-value') || '').toLowerCase();
      if (t === 'choose' || t === '') return false;
      return t.includes(target) || target.includes(t) || (d && (d.includes(target) || target.includes(d)));
    }

    // Find a pre-rendered option to open the dropdown
    const preOptions = [...question.querySelectorAll('[role="option"]')];
    const opener = preOptions.find(matchesTarget) || preOptions.find(partialMatchesTarget);
    if (!opener) return false;

    // Open the dropdown
    listbox.scrollIntoView({ block: 'center' });
    await delay(200);

    // Try multiple ways to open
    const openers = [
      () => opener.click(),
      () => listbox.click(),
      () => simulateClick(listbox),
    ];
    for (const fn of openers) {
      if (listbox.getAttribute('aria-expanded') === 'true') break;
      fn();
      for (let i = 0; i < 10; i++) {
        await delay(200);
        if (listbox.getAttribute('aria-expanded') === 'true') break;
      }
    }
    if (listbox.getAttribute('aria-expanded') !== 'true') return false;
    await delay(300);

    // After opening, find ALL visible elements with [data-value] matching the target
    // Google Forms creates a second set of visible options in the popup
    const allDataOpts = [...question.querySelectorAll('[data-value]')];
    const visibleMatch = allDataOpts.find(el => el.getBoundingClientRect().height > 0 && matchesTarget(el))
                      || allDataOpts.find(el => el.getBoundingClientRect().height > 0 && partialMatchesTarget(el));

    if (visibleMatch) {
      visibleMatch.click();
      await delay(300);
      if (listbox.getAttribute('aria-expanded') !== 'true') return true;
    }

    // Fallback: positional scan — find clickable element matching target text below the listbox
    if (listbox.getAttribute('aria-expanded') === 'true') {
      const lbRect = listbox.getBoundingClientRect();
      for (let dy = 5; dy <= 400; dy += 8) {
        const el = document.elementFromPoint(lbRect.left + lbRect.width / 2, lbRect.bottom + dy);
        if (!el) continue;
        const txt = el.textContent.trim().toLowerCase();
        const dv = (el.getAttribute('data-value') || '').toLowerCase();
        if (txt === target || dv === target) {
          el.click();
          await delay(300);
          if (listbox.getAttribute('aria-expanded') !== 'true') return true;
          break;
        }
      }
    }

    // Fallback: keyboard navigation
    if (listbox.getAttribute('aria-expanded') === 'true') {
      const idx = preOptions.findIndex(matchesTarget) || preOptions.findIndex(partialMatchesTarget);
      if (idx > 0) {
        listbox.focus();
        for (let i = 0; i < idx; i++) {
          listbox.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown', code: 'ArrowDown', keyCode: 40, bubbles: true }));
        }
        listbox.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true }));
        await delay(300);
        if (listbox.getAttribute('aria-expanded') !== 'true') return true;
      }
    }

    // Close dropdown if still open
    if (listbox.getAttribute('aria-expanded') === 'true') {
      document.body.click();
      await delay(200);
    }
    return false;
  }

  if (field.type === "grid") {
    const gridRows = question.querySelectorAll('[role="radiogroup"]');
    const valMap = typeof value === "object" ? value : {};
    let filled = false;

    for (const row of gridRows) {
      const rowLabel = row.getAttribute("aria-label") || "";
      const targetCol = valMap[rowLabel];
      if (!targetCol) continue;

      const radios = row.querySelectorAll('[role="radio"]');
      for (const radio of radios) {
        const colLabel = radio.getAttribute("aria-label") ||
                         radio.closest("[data-value]")?.getAttribute("data-value") || "";
        if (colLabel.toLowerCase().includes(String(targetCol).toLowerCase())) {
          radio.click();
          filled = true;
          break;
        }
      }
    }
    return filled;
  }

  if (field.type === "file_upload") {
    question.scrollIntoView({ behavior: "smooth", block: "center" });
    question.style.outline = "3px solid #f59e0b";
    question.style.outlineOffset = "4px";
    question.style.borderRadius = "8px";
    return "manual";
  }

  return false;
}

async function fillForm(fieldValues, reviewLabels = []) {
  const fields = extractFields();
  const results = [];
  const reviewSet = new Set(reviewLabels);

  for (const field of fields) {
    const value = fieldValues[field.label];
    if (value !== undefined && value !== null) {
      const success = await fillField(field, value);
      if (success === "manual") {
        results.push({ label: field.label, success: false, value: null, reason: "file_upload_manual" });
      } else {
        results.push({ label: field.label, success: !!success, value });
      }
    } else {
      results.push({ label: field.label, success: false, value: null, reason: "no value provided" });
    }

    if (reviewSet.has(field.label)) {
      const question = document.querySelectorAll('[role="listitem"]')[field.index];
      if (question) {
        question.style.outline = "3px solid #f97316";
        question.style.outlineOffset = "4px";
        question.style.borderRadius = "8px";
      }
    }
  }

  return results;
}

let autofillState = { used: false, taskId: null, backendUrl: null, authToken: null };

function extractCurrentValues() {
  const fields = extractFields();
  const values = {};
  const questions = document.querySelectorAll('[role="listitem"]');

  fields.forEach((field, i) => {
    const question = questions[field.index];
    if (!question) return;

    if (field.type === "short_text") {
      const el = question.querySelector('input[type="text"]:not([aria-label*="Hour"]):not([aria-label*="Minute"])');
      if (el && el.value) values[field.label] = el.value;
    } else if (field.type === "long_text") {
      const el = question.querySelector("textarea");
      if (el && el.value) values[field.label] = el.value;
    } else if (field.type === "multiple_choice" || field.type === "linear_scale") {
      const selected = question.querySelector('[role="radio"][aria-checked="true"]');
      if (selected) {
        const val = selected.closest("[data-value]")?.getAttribute("data-value") ||
                    selected.parentElement?.textContent?.trim();
        if (val) values[field.label] = val;
      }
    } else if (field.type === "checkbox") {
      const checked = question.querySelectorAll('[role="checkbox"][aria-checked="true"]');
      const vals = [];
      checked.forEach(cb => {
        const val = cb.closest("[data-answer-value]")?.getAttribute("data-answer-value") ||
                    cb.parentElement?.textContent?.trim();
        if (val) vals.push(val);
      });
      if (vals.length > 0) values[field.label] = vals.join(", ");
    } else if (field.type === "dropdown") {
      const listbox = question.querySelector('[role="listbox"]');
      if (listbox) {
        const text = listbox.textContent.trim();
        if (text && text !== "Choose") values[field.label] = text;
      }
    } else if (field.type === "date") {
      const dateInput = question.querySelector('input[type="date"]');
      if (dateInput && dateInput.value) {
        values[field.label] = dateInput.value;
      } else {
        const m = question.querySelector('input[aria-label*="Month"]');
        const d = question.querySelector('input[aria-label*="Day"]');
        const y = question.querySelector('input[aria-label*="Year"]');
        if (m?.value && d?.value && y?.value) {
          values[field.label] = `${y.value}-${m.value.padStart(2, "0")}-${d.value.padStart(2, "0")}`;
        }
      }
    } else if (field.type === "time") {
      const h = question.querySelector('input[aria-label*="Hour"]');
      const min = question.querySelector('input[aria-label*="Minute"]');
      if (h?.value && min?.value) values[field.label] = `${h.value}:${min.value}`;
    }
  });

  return values;
}

function setupSubmitCapture() {
  const submitBtns = document.querySelectorAll('[role="button"]');
  for (const btn of submitBtns) {
    const text = btn.textContent.trim().toLowerCase();
    if (text === "submit" || text === "send") {
      btn.addEventListener("click", () => {
        if (!autofillState.used || !autofillState.taskId) return;

        const finalValues = extractCurrentValues();
        if (Object.keys(finalValues).length === 0) return;

        chrome.runtime.sendMessage({
          action: "submit_capture",
          taskId: autofillState.taskId,
          backendUrl: autofillState.backendUrl,
          authToken: autofillState.authToken,
          finalValues: finalValues,
        });

        autofillState.used = false;
        autofillState.taskId = null;
      }, { once: true });
    }
  }
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === "ping") {
    sendResponse({ ok: true });
    return;
  }

  if (msg.action === "extract") {
    extractFieldsWithOptions().then(fields => {
      const clean = fields.map(f => ({
        index: f.index,
        label: f.label,
        type: f.type,
        required: f.required,
        description: f.description || null,
        options: f.options,
        rows: f.rows || [],
        columns: f.columns || [],
      }));

      const titleEl = document.querySelector('.freebirdFormviewerViewHeaderTitle')
        || document.querySelector('h1')
        || document.querySelector('title');
      const descEl = document.querySelector('.freebirdFormviewerViewHeaderDescription');

      sendResponse({
        fields: clean,
        form_title: titleEl ? titleEl.textContent.trim() : null,
        form_description: descEl ? descEl.textContent.trim() : null,
      });
    });
    return true;
  }

  if (msg.action === "fill") {
    fillForm(msg.values, msg.needs_review || []).then(results => {
      sendResponse({ results });
    });
    return true;
  }

  if (msg.action === "test_dropdown") {
    testDropdownFill(msg.value).then(result => {
      sendResponse(result);
    });
    return true;
  }

  if (msg.action === "set_autofill_state") {
    autofillState.used = true;
    autofillState.taskId = msg.taskId;
    autofillState.backendUrl = msg.backendUrl;
    autofillState.authToken = msg.authToken;
    setupSubmitCapture();
    sendResponse({ ok: true });
  }

  return true;
});

// === Test Dropdown handler (called from popup, no backend needed) ===
async function testDropdownFill(value) {
  const logs = [];
  function log(msg, type) { logs.push({ msg, type: type || '' }); }

  const fields = extractFields();
  const ddField = fields.find(f => f.type === 'dropdown');
  if (!ddField) { log('No dropdown field found on this form', 'fail'); return { logs, success: false }; }

  const question = document.querySelectorAll('[role="listitem"]')[ddField.index];
  const listbox = question.querySelector('[role="listbox"]');
  const allOptions = [...question.querySelectorAll('[role="option"]')];
  const target = String(value).toLowerCase().trim();

  log('Field: ' + ddField.label, 'step');
  log('Target: "' + target + '"');
  log('Options in DOM: ' + allOptions.length);
  allOptions.forEach((o, i) => {
    const r = o.getBoundingClientRect();
    log('  [' + i + '] "' + o.textContent.trim() + '" data-value="' + (o.getAttribute('data-value') || '') + '" h=' + r.height + ' selected=' + o.getAttribute('aria-selected'));
  });

  let matched = allOptions.find(o => {
    const t = o.textContent.trim().toLowerCase();
    const d = (o.getAttribute('data-value') || '').toLowerCase();
    return (t === target || d === target) && t !== 'choose';
  });
  if (!matched) {
    matched = allOptions.find(o => {
      const t = o.textContent.trim().toLowerCase();
      return t !== 'choose' && (t.includes(target) || target.includes(t));
    });
  }
  if (!matched) { log('No matching option found!', 'fail'); return { logs, success: false }; }
  log('Matched: "' + matched.textContent.trim() + '"', 'ok');

  let el = matched;
  while (el && el !== document.body) {
    const ja = el.getAttribute('jsaction');
    if (ja) log('jsaction <' + el.tagName + ' ' + (el.getAttribute('role') || '') + '>: ' + ja);
    el = el.parentElement;
  }

  log('outerHTML: ' + matched.outerHTML.substring(0, 250));
  log('Children: ' + [...matched.children].map(c => '<' + c.tagName + '>').join(', '));

  // === OPEN ===
  log('--- OPENING ---', 'step');
  log('aria-expanded before: ' + listbox.getAttribute('aria-expanded'));

  async function tryOpen(label, fn) {
    if (listbox.getAttribute('aria-expanded') === 'true') return true;
    log('  Try: ' + label);
    fn();
    await delay(500);
    const ok = listbox.getAttribute('aria-expanded') === 'true';
    log('  expanded=' + ok, ok ? 'ok' : 'fail');
    return ok;
  }

  listbox.scrollIntoView({ block: 'center' });
  await delay(200);

  const opened =
    await tryOpen('listbox.click()', () => listbox.click()) ||
    await tryOpen('matched.click()', () => matched.click()) ||
    await tryOpen('simulateClick(listbox)', () => simulateClick(listbox)) ||
    await tryOpen('simulateClick(matched)', () => simulateClick(matched));

  if (!opened) { log('FAILED to open dropdown', 'fail'); return { logs, success: false }; }

  await delay(500);

  // === RE-QUERY OPTIONS AFTER OPENING (they may now be visible) ===
  log('--- OPTIONS AFTER OPENING ---', 'step');
  const freshOptions = [...question.querySelectorAll('[data-value]')];
  freshOptions.forEach((el, i) => {
    const r = el.getBoundingClientRect();
    log('  [' + i + '] dv="' + el.getAttribute('data-value') + '" id="' + (el.id || '') + '" h=' + r.height + ' tag=' + el.tagName + ' role=' + (el.getAttribute('role') || ''));
  });

  // Find the visible option matching target by data-value
  const visibleOpt = freshOptions.find(el => {
    const dv = (el.getAttribute('data-value') || '').toLowerCase();
    return dv === target && el.getBoundingClientRect().height > 0;
  });

  // Also scan positionally for the matching element
  const listboxRect = listbox.getBoundingClientRect();
  let positionalEl = null;
  for (let dy = 5; dy <= 300; dy += 8) {
    const px = listboxRect.left + listboxRect.width / 2;
    const py = listboxRect.bottom + dy;
    const el = document.elementFromPoint(px, py);
    if (!el) continue;
    const txt = el.textContent.trim().toLowerCase();
    const dv = (el.getAttribute('data-value') || '').toLowerCase();
    if ((txt === target || dv === target) && el.children.length === 0) {
      positionalEl = el;
      log('Positional leaf match at y+' + dy + ': <' + el.tagName + '> "' + el.textContent.trim() + '" id="' + (el.id || '') + '"', 'ok');
      break;
    }
  }

  // === TRY SELECTING ===
  log('--- SELECTING ---', 'step');

  async function trySelect(label, fn) {
    if (listbox.getAttribute('aria-expanded') !== 'true') return 'closed';
    log('  Try: ' + label);
    fn();
    await delay(500);
    const expanded = listbox.getAttribute('aria-expanded');
    const selEl = question.querySelector('[aria-selected="true"]');
    const selText = selEl ? selEl.textContent.trim() : '';
    log('  expanded=' + expanded + ' selected="' + selText + '"', expanded !== 'true' ? 'ok' : 'fail');
    return expanded !== 'true' ? 'closed' : 'open';
  }

  let done = false;

  // 1. Click the visible [data-value] option
  if (visibleOpt && !done) {
    log('Found visible option: dv="' + visibleOpt.getAttribute('data-value') + '" h=' + visibleOpt.getBoundingClientRect().height, 'ok');
    const r = await trySelect('visibleOpt.click()', () => visibleOpt.click());
    if (r === 'closed') done = true;
  }

  // 2. Click positional leaf element
  if (positionalEl && !done) {
    if (listbox.getAttribute('aria-expanded') !== 'true') { listbox.click(); await delay(500); }
    const r = await trySelect('positionalEl.click()', () => positionalEl.click());
    if (r === 'closed') done = true;
  }

  // 3. Try clicking parent of positional element (the [role="option"] div)
  if (positionalEl && !done) {
    if (listbox.getAttribute('aria-expanded') !== 'true') { listbox.click(); await delay(500); }
    const parent = positionalEl.closest('[data-value]') || positionalEl.parentElement;
    if (parent && parent !== positionalEl) {
      log('  Parent: <' + parent.tagName + '> dv="' + (parent.getAttribute('data-value') || '') + '" h=' + parent.getBoundingClientRect().height);
      const r = await trySelect('parent.click()', () => parent.click());
      if (r === 'closed') done = true;
    }
  }

  // 4. Keyboard: ArrowDown + Enter
  if (!done) {
    if (listbox.getAttribute('aria-expanded') !== 'true') { listbox.click(); await delay(500); }
    const optIdx = allOptions.findIndex(o => {
      const t = o.textContent.trim().toLowerCase();
      const d = (o.getAttribute('data-value') || '').toLowerCase();
      return (t === target || d === target) && t !== 'choose';
    });
    if (optIdx > 0) {
      const r = await trySelect('keyboard ArrowDown x' + optIdx + ' + Enter', () => {
        listbox.focus();
        for (let i = 0; i < optIdx; i++) {
          listbox.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown', code: 'ArrowDown', keyCode: 40, bubbles: true, cancelable: true }));
        }
        listbox.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true, cancelable: true }));
      });
      if (r === 'closed') done = true;
    }
  }

  // 5. Last resort: pre-rendered matched.click()
  if (!done) {
    if (listbox.getAttribute('aria-expanded') !== 'true') { listbox.click(); await delay(500); }
    const r = await trySelect('matched.click() (pre-rendered)', () => matched.click());
    if (r === 'closed') done = true;
  }

  log('--- RESULT ---', 'step');
  const finalSel = question.querySelector('[aria-selected="true"]');
  const finalText = finalSel ? finalSel.textContent.trim() : '';
  log('Currently selected: "' + finalText + '"');
  const success = finalText.toLowerCase() === target;
  log(success ? 'VALUE SELECTED: "' + finalText + '"' : 'FAILED — displayed "' + finalText + '" expected "' + target + '"', success ? 'ok' : 'fail');

  return { logs, success };
}
