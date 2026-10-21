// --- Open side panel when extension icon is clicked ---
chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true });

// --- Enable side panel only on Google Form tabs ---
function updateSidePanel(tabId, url) {
  if (url && url.includes("docs.google.com/forms")) {
    chrome.sidePanel.setOptions({ tabId, path: "sidepanel.html", enabled: true });
    chrome.action.setBadgeText({ text: "Fill", tabId });
    chrome.action.setBadgeBackgroundColor({ color: "#2563eb", tabId });
  } else {
    chrome.sidePanel.setOptions({ tabId, enabled: false });
    chrome.action.setBadgeText({ text: "", tabId });
  }
}

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (tab.url) updateSidePanel(tabId, tab.url);
});

chrome.tabs.onActivated.addListener(async ({ tabId }) => {
  try {
    const tab = await chrome.tabs.get(tabId);
    updateSidePanel(tabId, tab.url);
  } catch {}
});

chrome.sidePanel.setOptions({ enabled: false });

// --- Submit capture listener ---
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === "submit_capture") {
    fetch(`${msg.backendUrl}/api/workflow/submit-capture`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${msg.authToken}`,
      },
      body: JSON.stringify({
        task_id: msg.taskId,
        final_values: msg.finalValues,
      }),
    })
      .then(res => res.json())
      .then(data => {
        console.log("Submit capture:", data);
      })
      .catch(err => {
        console.warn("Submit capture failed:", err);
      });
  }
});
