// --- DOM elements ---
const loginView = document.getElementById("loginView");
const idleView = document.getElementById("idleView");
const formView = document.getElementById("formView");

const connectWebBtn = document.getElementById("connectWebBtn");
const showLoginFormBtn = document.getElementById("showLoginForm");
const loginForm = document.getElementById("loginForm");
const loginBtn = document.getElementById("loginBtn");
const loginEmail = document.getElementById("loginEmail");
const loginPassword = document.getElementById("loginPassword");
const loginStatus = document.getElementById("loginStatus");

const settingsToggle = document.getElementById("settingsToggle");
const settingsPanel = document.getElementById("settingsPanel");
const backendUrlInput = document.getElementById("backendUrl");

const fillBtn = document.getElementById("fillBtn");
const statusEl = document.getElementById("status");
const resultsEl = document.getElementById("results");

const logoutBtnIdle = document.getElementById("logoutBtnIdle");
const logoutBtnForm = document.getElementById("logoutBtnForm");

// --- State ---
let authToken = null;
let isOnGoogleForm = false;

// --- View switching ---
function showView(view) {
  loginView.classList.add("hidden");
  idleView.classList.add("hidden");
  formView.classList.add("hidden");
  view.classList.remove("hidden");

  // Show settings gear only when logged in
  if (view === idleView || view === formView) {
    settingsToggle.classList.remove("hidden");
  } else {
    settingsToggle.classList.add("hidden");
    settingsPanel.classList.add("hidden");
  }
}

// --- Settings toggle ---
settingsToggle.addEventListener("click", () => {
  settingsPanel.classList.toggle("hidden");
});

backendUrlInput.addEventListener("change", () => {
  chrome.storage.local.set({ backendUrl: backendUrlInput.value.trim() });
});

// --- Helper: get backend URL ---
function getBackendUrl() {
  return backendUrlInput.value.trim().replace(/\/$/, "");
}

// --- Tab helpers ---
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

async function ensureContentScript(tabId) {
  try {
    await sendToContent(tabId, { action: "ping" });
  } catch {
    await chrome.scripting.executeScript({
      target: { tabId },
      files: ["content.js"],
    });
    await new Promise((r) => setTimeout(r, 300));
  }
}

// --- Check if current tab is a Google Form ---
async function checkCurrentTab() {
  try {
    const [tab] = await getActiveTab();
    if (tab && tab.url && tab.url.includes("docs.google.com/forms")) {
      isOnGoogleForm = true;
      if (authToken) showView(formView);
    } else {
      isOnGoogleForm = false;
      if (authToken) showView(idleView);
    }
  } catch (e) {
    isOnGoogleForm = false;
    if (authToken) showView(idleView);
  }
}

// --- Listen for tab changes ---
chrome.tabs.onActivated.addListener(() => {
  if (authToken) checkCurrentTab();
});

chrome.tabs.onUpdated.addListener((tabId, changeInfo) => {
  if ((changeInfo.url || changeInfo.status === "complete") && authToken) {
    checkCurrentTab();
  }
});

// --- Init: check stored token ---
chrome.storage.local.get(["authToken", "backendUrl"], async (data) => {
  if (data.backendUrl) backendUrlInput.value = data.backendUrl;

  if (data.authToken) {
    authToken = data.authToken;
    await checkCurrentTab();
  } else {
    showView(loginView);
  }
});

// --- Listen for token changes from connect.js ---
chrome.storage.onChanged.addListener((changes, area) => {
  if (area === "local" && changes.authToken) {
    if (changes.authToken.newValue) {
      authToken = changes.authToken.newValue;
      checkCurrentTab();
    } else {
      authToken = null;
      showView(loginView);
    }
  }
});

// --- Connect via Web ---
connectWebBtn.addEventListener("click", () => {
  chrome.tabs.create({ url: "http://localhost:5173/connect" });
});

// --- Toggle manual login form ---
showLoginFormBtn.addEventListener("click", () => {
  const isExpanded = loginForm.classList.contains("expanded");
  if (isExpanded) {
    loginForm.classList.remove("expanded");
    showLoginFormBtn.textContent = "Log in manually";
  } else {
    loginForm.classList.add("expanded");
    showLoginFormBtn.textContent = "Hide login form";
  }
});

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
    await checkCurrentTab();
  } catch (err) {
    loginStatus.textContent = "Connection error: " + err.message;
    loginStatus.className = "status error";
  }
  loginBtn.disabled = false;
});

// --- Logout ---
function logout() {
  authToken = null;
  chrome.storage.local.remove(["authToken", "userEmail"]);
  loginEmail.value = "";
  loginPassword.value = "";
  loginStatus.textContent = "";
  loginForm.classList.remove("expanded");
  showLoginFormBtn.textContent = "Log in manually";
  statusEl.textContent = "";
  resultsEl.innerHTML = "";
  showView(loginView);
}

logoutBtnIdle.addEventListener("click", logout);
logoutBtnForm.addEventListener("click", logout);

// --- Status helper ---
function setStatus(text, type) {
  statusEl.textContent = text;
  statusEl.className = "status" + (type ? " " + type : "");
}

// --- Handle 401: redirect to login ---
function handleUnauthorized() {
  authToken = null;
  chrome.storage.local.remove(["authToken", "userEmail"]);
  setStatus("Session expired. Please log in again.", "error");
  showView(loginView);
}

// --- Render results ---
function renderResults(results, needsReview = [], taskId = null) {
  const reviewMap = {};
  needsReview.forEach((r) => { reviewMap[r.label] = r; });

  resultsEl.innerHTML = "";
  const reviewInputs = [];

  results.forEach((r) => {
    const div = document.createElement("div");
    let statusText;
    const reviewInfo = reviewMap[r.label];

    if (r.reason === "file_upload_manual") {
      div.className = "field result-warn";
      statusText = "File upload -- fill manually";
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
    resultsEl.appendChild(div);
  });

  if (reviewInputs.length > 0 && taskId) {
    const submitDiv = document.createElement("div");
    submitDiv.className = "review-submit-wrap";
    submitDiv.innerHTML = `<button id="submitReviewsBtn" class="btn-primary">Submit Reviews</button>`;
    resultsEl.appendChild(submitDiv);

    document.getElementById("submitReviewsBtn").addEventListener("click", async () => {
      await submitReviews(taskId);
    });

    resultsEl.querySelectorAll(".btn-approve").forEach((btn) => {
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

    resultsEl.querySelectorAll(".btn-skip").forEach((btn) => {
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

// --- Submit reviews ---
async function submitReviews(taskId) {
  const backendUrl = getBackendUrl();

  try {
    const res = await fetch(`${backendUrl}/api/approvals?task_id=${taskId}`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    if (!res.ok) {
      setStatus("Failed to load approvals", "error");
      return;
    }

    const approvals = await res.json();
    const approvalMap = {};
    approvals.forEach((a) => { approvalMap[a.label] = a.id; });

    const reviewFields = resultsEl.querySelectorAll(".field[data-action], .field.result-review");
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
          Authorization: `Bearer ${authToken}`,
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

// --- Fill ---
fillBtn.addEventListener("click", async () => {
  fillBtn.disabled = true;
  resultsEl.innerHTML = "";
  setStatus("Extracting fields...");

  try {
    const [tab] = await getActiveTab();
    if (!tab.url || !tab.url.includes("docs.google.com/forms")) {
      setStatus("Not a Google Form. Open a Google Form first.", "error");
      fillBtn.disabled = false;
      return;
    }

    await ensureContentScript(tab.id);

    const extractResponse = await sendToContent(tab.id, { action: "extract" });
    if (!extractResponse || !extractResponse.fields || extractResponse.fields.length === 0) {
      setStatus("No fields found on this form.", "error");
      fillBtn.disabled = false;
      return;
    }

    const fields = extractResponse.fields;
    const formTitle = extractResponse.form_title || null;
    const formDescription = extractResponse.form_description || null;
    setStatus(`Found ${fields.length} fields. Asking backend...`);

    const backendUrl = getBackendUrl();
    const apiResponse = await fetch(`${backendUrl}/api/workflow/start`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${authToken}`,
      },
      body: JSON.stringify({
        url: tab.url,
        form_title: formTitle,
        form_description: formDescription,
        fields,
      }),
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

    const reviewLabels = (data.needs_review || []).map((r) => r.label);
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
      setStatus(
        `Done. Filled ${ok}/${fillResponse.results.length} fields.${reviewMsg}`,
        ok > 0 ? "success" : "error"
      );
    }
  } catch (err) {
    setStatus("Error: " + err.message, "error");
    fillBtn.disabled = false;
  }
});
