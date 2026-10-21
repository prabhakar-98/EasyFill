function tryConnect() {
  const tokenEl = document.getElementById("easyfill-token");
  if (!tokenEl) return false;

  const token = tokenEl.dataset.token;
  const email = tokenEl.dataset.email;

  if (token) {
    chrome.storage.local.set({ authToken: token, userEmail: email }, () => {
      window.dispatchEvent(new CustomEvent("easyfill-connected"));
    });
    return true;
  }
  return false;
}

if (!tryConnect()) {
  const observer = new MutationObserver(() => {
    if (tryConnect()) observer.disconnect();
  });
  observer.observe(document.body, { childList: true, subtree: true });

  setTimeout(() => observer.disconnect(), 15000);
}
