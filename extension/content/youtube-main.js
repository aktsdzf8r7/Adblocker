// Runs in the page context of YouTube at document_start. Removes the ad
// definitions from the player data before the player reads them, so video
// ads are never scheduled (same idea as uBlock Origin's "json-prune").
(() => {
  if (window.__schildYT) return;
  window.__schildYT = true;

  const AD_KEYS = ['adPlacements', 'adSlots', 'playerAds', 'adBreakHeartbeatParams'];

  function prune(obj) {
    if (!obj || typeof obj !== 'object') return obj;
    try {
      for (const key of AD_KEYS) if (key in obj) delete obj[key];
      // Nested player responses (e.g. /player and /next responses)
      for (const nested of ['playerResponse', 'response']) {
        if (obj[nested] && typeof obj[nested] === 'object') {
          for (const key of AD_KEYS) if (key in obj[nested]) delete obj[nested][key];
        }
      }
    } catch {
      // never break the page
    }
    return obj;
  }

  const looksLikePlayerData = (o) => o && typeof o === 'object'
    && (AD_KEYS.some((k) => k in o) || (o.playerResponse && typeof o.playerResponse === 'object'));

  // 1. JSON.parse
  const origParse = JSON.parse;
  JSON.parse = new Proxy(origParse, {
    apply(target, thisArg, args) {
      const result = Reflect.apply(target, thisArg, args);
      return looksLikePlayerData(result) ? prune(result) : result;
    },
  });

  // 2. fetch().json() for /youtubei/v1/player and /next
  const origJson = Response.prototype.json;
  Response.prototype.json = new Proxy(origJson, {
    apply(target, thisArg, args) {
      return Reflect.apply(target, thisArg, args).then((r) => (looksLikePlayerData(r) ? prune(r) : r));
    },
  });

  // 3. Inline globals set by the server-rendered page
  for (const name of ['ytInitialPlayerResponse', 'playerResponse']) {
    let value = window[name];
    try {
      Object.defineProperty(window, name, {
        configurable: true,
        get: () => value,
        set: (v) => { value = prune(v); },
      });
    } catch {
      // property not configurable
    }
  }
})();
