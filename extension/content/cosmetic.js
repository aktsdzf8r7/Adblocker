// Asks the background script to inject the element hiding CSS for this
// frame. The CSS is inserted with "user" origin, so pages cannot override it.
(() => {
  if (globalThis.__schildCosmetic) return;
  globalThis.__schildCosmetic = true;
  try {
    chrome.runtime.sendMessage({ type: 'cosmetic' }).catch(() => {});
  } catch {
    // Extension was reloaded; the old content script is orphaned.
  }
})();
