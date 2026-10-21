// --- DOM elements ---
const loginView = document.getElementById("loginView");
const registerView = document.getElementById("registerView");
const mainView = document.getElementById("mainView");

const loginBtn = document.getElementById("loginBtn");
const loginEmail = document.getElementById("loginEmail");
const loginPassword = document.getElementById("loginPassword");
const loginStatus = document.getElementById("loginStatus");
const showRegister = document.getElementById("showRegister");

const registerBtn = document.getElementById("registerBtn");
const regFirstName = document.getElementById("regFirstName");
const regLastName = document.getElementById("regLastName");
const regEmail = document.getElementById("regEmail");
const regPassword = document.getElementById("regPassword");
const regStatus = document.getElementById("regStatus");
const showLogin = document.getElementById("showLogin");

const statusEl = document.getElementById("status");
const fieldsEl = document.getElementById("fields");
const extractBtn = document.getElementById("extractBtn");
const fillBtn = document.getElementById("fillBtn");
const logoutBtn = document.getElementById("logoutBtn");
const backendUrlInput = document.getElementById("backendUrl");
const userEmailEl = document.getElementById("userEmail");

// --- State ---
let authToken = null;

// --- View switching ---
function showView(view) {
  loginView.classList.add("hidden");
  registerView.classList.add("hidden");
  mainView.classList.add("hidden");
  view.classList.remove("hidden");
}

showRegister.addEventListener("click", () => showView(registerView));
showLogin.addEventListener("click", () => showView(loginView));

// --- Init: check stored token ---
chrome.storage.local.get(["authToken", "userEmail", "backendUrl"], async (data) => {
  if (data.backendUrl) backendUrlInput.value = data.backendUrl;

  if (data.authToken) {
    authToken = data.authToken;
    if (data.userEmail) userEmailEl.textContent = data.userEmail;
    showView(mainView);
  } else {
    showView(loginView);
  }
});

backendUrlInput.addEventListener("change", () => {
  chrome.storage.local.set({ backendUrl: backendUrlInput.value });
});

// --- Helper: get backend URL ---
function getBackendUrl() {
  return backendUrlInput.value.replace(/\/$/, "");
}

// --- Login ---
loginBtn.addEventListener("click", async () => {
  loginBtn.disabled = true;
  loginStatus.textContent = "";

  const email = loginEmail.value.trim();
  const password = loginPassword.value;

  if (!email || !password) {
    loginStatus.textContent = "Email and password required.";
    loginStatus.className = "status error";
    loginBtn.disabled = false;
    return;
  }

  try {
    const backendUrl = getBackendUrl();
    const res = await fetch(`${backendUrl}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      loginStatus.textContent = err.detail || `Login failed (${res.status})`;
      loginStatus.className = "status error";
      loginBtn.disabled = false;
      return;
    }

    const data = await res.json();
    authToken = data.access_token;
    const userEmail = data.user.email;

    chrome.storage.local.set({ authToken, userEmail });
    userEmailEl.textContent = userEmail;
    showView(mainView);
  } catch (err) {
    loginStatus.textContent = "Connection error: " + err.message;
    loginStatus.className = "status error";
  }
  loginBtn.disabled = false;
});

// --- Register ---
registerBtn.addEventListener("click", async () => {
  registerBtn.disabled = true;
  regStatus.textContent = "";

  const email = regEmail.value.trim();
  const password = regPassword.value;
  const first_name = regFirstName.value.trim() || null;
  const last_name = regLastName.value.trim() || null;

  if (!email || !password) {
    regStatus.textContent = "Email and password required.";
    regStatus.className = "status error";
    registerBtn.disabled = false;
    return;
  }
  if (password.length < 8) {
    regStatus.textContent = "Password must be at least 8 characters.";
    regStatus.className = "status error";
    registerBtn.disabled = false;
    return;
  }

  try {
    const backendUrl = getBackendUrl();
    const res = await fetch(`${backendUrl}/api/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, first_name, last_name }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      regStatus.textContent = err.detail || `Registration failed (${res.status})`;
      regStatus.className = "status error";
      registerBtn.disabled = false;
      return;
    }

    const data = await res.json();
    authToken = data.access_token;
    const userEmail = data.user.email;

    chrome.storage.local.set({ authToken, userEmail });
    userEmailEl.textContent = userEmail;
    showView(mainView);
  } catch (err) {
    regStatus.textContent = "Connection error: " + err.message;
    regStatus.className = "status error";
  }
  registerBtn.disabled = false;
});

// --- Logout ---
logoutBtn.addEventListener("click", () => {
  authToken = null;
  chrome.storage.local.remove(["authToken", "userEmail"]);
  loginEmail.value = "";
  loginPassword.value = "";
  loginStatus.textContent = "";
  showView(loginView);
});

// --- Status + rendering (same as before) ---
function setStatus(text, type) {
  statusEl.textContent = text;
  statusEl.className = "status" + (type ? " " + type : "");
}

function renderResults(results, needsReview = [], taskId = null) {
  const reviewMap = {};
  needsReview.forEach((r) => { reviewMap[r.label] = r; });

  fieldsEl.innerHTML = "";
  const reviewInputs = [];

  results.forEach((r) => {
    const div = document.createElement("div");
    let statusText;
    const reviewInfo = reviewMap[r.label];

    if (r.reason === "file_upload_manual") {
      div.className = "field result-warn";
      statusText = "File upload — please fill manually (highlighted on page)";
      div.innerHTML = `
        <div class="field-label">${r.label}</div>
        <div class="field-meta">${statusText}</div>
      `;
    } else if (reviewInfo) {
      div.className = "field result-review";
      const currentVal = r.value || reviewInfo.value || "";
      const reason = reviewInfo.reason || "needs review";
      div.innerHTML = `
        <div class="field-label">${r.label}</div>
        <div class="field-meta">${reason}</div>
        <div class="review-actions">
          <input type="text" class="review-input" value="${currentVal}" data-label="${r.label}" />
          <div class="review-btns">
            <button class="btn-approve" data-label="${r.label}">Approve</button>
            <button class="btn-skip" data-label="${r.label}">Skip</button>
          </div>
        </div>
      `;
      reviewInputs.push({ label: r.label, div });
    } else if (r.success) {
      div.className = "field result-ok";
      const display = typeof r.value === "object" ? JSON.stringify(r.value) : r.value;
      statusText = "Filled: " + display;
      div.innerHTML = `
        <div class="field-label">${r.label}</div>
        <div class="field-meta">${statusText}</div>
      `;
    } else {
      div.className = "field result-fail";
      statusText = "No match found";
      div.innerHTML = `
        <div class="field-label">${r.label}</div>
        <div class="field-meta">${statusText}</div>
      `;
    }
    fieldsEl.appendChild(div);
  });

  if (reviewInputs.length > 0 && taskId) {
    const submitDiv = document.createElement("div");
    submitDiv.className = "review-submit-wrap";
    submitDiv.innerHTML = `<button id="submitReviewsBtn" class="btn-primary">Submit Reviews</button>`;
    fieldsEl.appendChild(submitDiv);

    document.getElementById("submitReviewsBtn").addEventListener("click", async () => {
      await submitReviews(taskId);
    });

    fieldsEl.querySelectorAll(".btn-approve").forEach(btn => {
      btn.addEventListener("click", () => {
        const label = btn.dataset.label;
        const field = btn.closest(".field");
        field.className = "field result-ok";
        const input = field.querySelector(".review-input");
        field.innerHTML = `
          <div class="field-label">${label}</div>
          <div class="field-meta">Approved: ${input.value}</div>
        `;
        field.dataset.action = "approve";
        field.dataset.value = input.value;
      });
    });

    fieldsEl.querySelectorAll(".btn-skip").forEach(btn => {
      btn.addEventListener("click", () => {
        const label = btn.dataset.label;
        const field = btn.closest(".field");
        field.className = "field result-fail";
        field.innerHTML = `
          <div class="field-label">${label}</div>
          <div class="field-meta">Skipped</div>
        `;
        field.dataset.action = "reject";
      });
    });
  }
}

async function submitReviews(taskId) {
  const backendUrl = getBackendUrl();

  try {
    const res = await fetch(`${backendUrl}/api/approvals?task_id=${taskId}`, {
      headers: { "Authorization": `Bearer ${authToken}` },
    });
    if (!res.ok) { setStatus("Failed to load approvals", "error"); return; }

    const approvals = await res.json();
    const approvalMap = {};
    approvals.forEach(a => { approvalMap[a.label] = a.id; });

    const reviewFields = fieldsEl.querySelectorAll(".field[data-action], .field.result-review");
    let submitted = 0;

    for (const field of reviewFields) {
      const label = field.querySelector(".field-label")?.textContent?.trim();
      const approvalId = approvalMap[label];
      if (!approvalId) continue;

      let action = field.dataset.action;
      let value = field.dataset.value;

      if (!action) {
        const input = field.querySelector(".review-input");
        if (input) {
          const originalVal = input.defaultValue;
          if (input.value !== originalVal) {
            action = "modify";
            value = input.value;
          } else {
            action = "approve";
            value = input.value;
          }
        }
      }

      if (!action) continue;

      const body = { action };
      if (action === "modify") body.value = value;

      await fetch(`${backendUrl}/api/approvals/${approvalId}/respond`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${authToken}`,
        },
        body: JSON.stringify(body),
      });
      submitted++;
    }

    setStatus(`Reviews submitted (${submitted} fields).`, "success");

    // Re-fill corrected values on the form
    const correctedValues = {};
    for (const field of reviewFields) {
      const label = field.querySelector(".field-label")?.textContent?.trim();
      const val = field.dataset.value;
      if (field.dataset.action !== "reject" && val) {
        correctedValues[label] = val;
      }
    }

    if (Object.keys(correctedValues).length > 0) {
      const [tab] = await getActiveTab();
      await sendToContent(tab.id, { action: "fill", values: correctedValues });
    }
  } catch (err) {
    setStatus("Error submitting reviews: " + err.message, "error");
  }
}

function renderFields(fields) {
  fieldsEl.innerHTML = "";
  fields.forEach((f) => {
    const div = document.createElement("div");
    div.className = "field";
    let meta = f.type;
    if (f.required) meta += " • required";
    if (f.options && f.options.length > 0) meta += " • " + f.options.join(", ");
    if (f.rows && f.rows.length > 0) meta += " • rows: " + f.rows.join(", ");
    if (f.columns && f.columns.length > 0) meta += " • cols: " + f.columns.join(", ");
    div.innerHTML = `
      <div class="field-label">${f.label} ${f.required ? '<span class="required">*</span>' : ""}</div>
      <div class="field-meta">${meta}</div>
    `;
    fieldsEl.appendChild(div);
  });
}

function getActiveTab() {
  return chrome.tabs.query({ active: true, currentWindow: true });
}

function sendToContent(tabId, message) {
  return new Promise((resolve, reject) => {
    chrome.tabs.sendMessage(tabId, message, (response) => {
      if (chrome.runtime.lastError) {
        reject(new Error(chrome.runtime.lastError.message));
      } else {
        resolve(response);
      }
    });
  });
}

// --- Handle 401: redirect to login ---
function handleUnauthorized() {
  authToken = null;
  chrome.storage.local.remove(["authToken", "userEmail"]);
  setStatus("Session expired. Please log in again.", "error");
  showView(loginView);
}

// --- Extract ---
extractBtn.addEventListener("click", async () => {
  extractBtn.disabled = true;
  setStatus("Extracting fields...");

  try {
    const [tab] = await getActiveTab();
    if (!tab.url || !tab.url.includes("docs.google.com/forms")) {
      setStatus("Not a Google Form. Open a Google Form first.", "error");
      extractBtn.disabled = false;
      return;
    }

    const response = await sendToContent(tab.id, { action: "extract" });
    extractBtn.disabled = false;

    if (response && response.fields) {
      renderFields(response.fields);
      setStatus(`Found ${response.fields.length} fields.`, "success");
    } else {
      setStatus("No fields found.", "error");
    }
  } catch (err) {
    setStatus("Error: " + err.message + ". Reload the form.", "error");
    extractBtn.disabled = false;
  }
});

// --- Fill ---
fillBtn.addEventListener("click", async () => {
  fillBtn.disabled = true;
  setStatus("Extracting fields...");

  try {
    const [tab] = await getActiveTab();
    if (!tab.url || !tab.url.includes("docs.google.com/forms")) {
      setStatus("Not a Google Form. Open a Google Form first.", "error");
      fillBtn.disabled = false;
      return;
    }

    const extractResponse = await sendToContent(tab.id, { action: "extract" });
    if (!extractResponse || !extractResponse.fields || extractResponse.fields.length === 0) {
      setStatus("No fields found on this form.", "error");
      fillBtn.disabled = false;
      return;
    }

    const fields = extractResponse.fields;
    setStatus(`Found ${fields.length} fields. Asking backend...`);

    const backendUrl = getBackendUrl();
    const apiResponse = await fetch(`${backendUrl}/api/workflow/start`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${authToken}`,
      },
      body: JSON.stringify({ url: tab.url, fields }),
    });

    if (apiResponse.status === 401 || apiResponse.status === 403) {
      handleUnauthorized();
      fillBtn.disabled = false;
      return;
    }

    if (!apiResponse.ok) {
      setStatus(`Backend error: ${apiResponse.status}`, "error");
      fillBtn.disabled = false;
      return;
    }

    const data = await apiResponse.json();
    const reviewCount = data.needs_review ? data.needs_review.length : 0;
    setStatus(`Matched ${data.matched}/${data.total} fields. Filling...`);

    const reviewLabels = (data.needs_review || []).map(r => r.label);
    const fillResponse = await sendToContent(tab.id, {
      action: "fill",
      values: data.values,
      needs_review: reviewLabels,
    });

    // Tell content script about autofill for submit capture
    if (data.task_id) {
      await sendToContent(tab.id, {
        action: "set_autofill_state",
        taskId: data.task_id,
        backendUrl: backendUrl,
        authToken: authToken,
      });
    }

    fillBtn.disabled = false;

    if (fillResponse && fillResponse.results) {
      renderResults(fillResponse.results, data.needs_review || [], data.task_id);
      const ok = fillResponse.results.filter((r) => r.success).length;
      const reviewMsg = reviewCount > 0 ? ` ${reviewCount} need review.` : "";
      setStatus(`Done. Filled ${ok}/${fillResponse.results.length} fields.${reviewMsg}`, ok > 0 ? "success" : "error");
    }
  } catch (err) {
    setStatus("Error: " + err.message, "error");
    fillBtn.disabled = false;
  }
});

// --- Test Dropdown (no backend) ---
document.getElementById("testDropdownBtn").addEventListener("click", async () => {
  const testValue = document.getElementById("testValue").value.trim();
  if (!testValue) { setStatus("Enter a value to test.", "error"); return; }

  setStatus("Running dropdown test...");
  fieldsEl.innerHTML = "";

  try {
    const [tab] = await getActiveTab();
    if (!tab.url || !tab.url.includes("docs.google.com/forms")) {
      setStatus("Not a Google Form.", "error");
      return;
    }

    const response = await sendToContent(tab.id, { action: "test_dropdown", value: testValue });

    if (!response || !response.logs) {
      setStatus("No response from content script. Reload the form.", "error");
      return;
    }

    // Show logs in the fields area
    response.logs.forEach(entry => {
      const div = document.createElement("div");
      div.className = "field";
      if (entry.type === "ok") div.className += " result-ok";
      else if (entry.type === "fail") div.className += " result-fail";
      else if (entry.type === "step") div.style.borderLeft = "3px solid #2563eb";
      div.innerHTML = `<div class="field-meta" style="font-family:monospace;white-space:pre-wrap;color:${
        entry.type === 'ok' ? '#16a34a' : entry.type === 'fail' ? '#dc2626' : entry.type === 'step' ? '#2563eb' : '#555'
      }">${entry.msg}</div>`;
      fieldsEl.appendChild(div);
    });

    setStatus(response.success ? "Test PASSED" : "Test FAILED — see logs below",
              response.success ? "success" : "error");
  } catch (err) {
    setStatus("Error: " + err.message, "error");
  }
});
