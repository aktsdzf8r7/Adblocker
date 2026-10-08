import { LISTS } from './lib/lists.js';
import { ALLOW_ID_OFFSET, PRIORITY, normalizeDomain, parseFilterList, selectorsForHost } from './lib/filter-parser.js';

const DEFAULTS = {
  enabledLists: LISTS.filter((l) => l.defaultEnabled).map((l) => l.id),
  allowlist: [],
  customFilters: '',
  paused: false,
  youtube: true,
  popupBlocking: true,
  stats: { popups: 0 },
};

// Custom user filters get a priority bonus so they win over list filters.
const USER_PRIORITY_BONUS = 10;
const ALLOWLIST_RULE_IDS = [ALLOW_ID_OFFSET + 1, ALLOW_ID_OFFSET + 2];
const CUSTOM_START_ID = 100;
const CUSTOM_ALLOW_START_ID = ALLOW_ID_OFFSET + 100;
const YT_SCRIPT_IDS = ['yt-main', 'yt-skip'];

// ---------------------------------------------------------------- settings

async function getSettings() {
  return chrome.storage.local.get(DEFAULTS);
}

function hostOf(url) {
  try {
    const u = new URL(url);
    return /^https?:$/.test(u.protocol) ? u.hostname.toLowerCase() : null;
  } catch {
    return null;
  }
}

function matchesDomainList(host, list) {
  if (!host) return false;
  return list.some((d) => host === d || host.endsWith(`.${d}`));
}

function isAllowlisted(settings, host) {
  return matchesDomainList(host, settings.allowlist);
}

// ------------------------------------------------------------ apply rules

let applying = Promise.resolve();
function applySettings() {
  applying = applying.then(doApplySettings).catch((err) => console.error('applySettings', err));
  return applying;
}

async function doApplySettings() {
  const settings = await getSettings();
  cosmeticCache.clear();
  popupMatchers = null;
  customParsed = null;

  // 1. Static rulesets (filter lists)
  const enable = settings.paused ? [] : settings.enabledLists.filter((id) => LISTS.some((l) => l.id === id));
  const disable = LISTS.map((l) => l.id).filter((id) => !enable.includes(id));
  try {
    await chrome.declarativeNetRequest.updateEnabledRulesets({ enableRulesetIds: enable, disableRulesetIds: disable });
  } catch (err) {
    // E.g. too many static rules enabled at once: fall back to the defaults.
    console.error('updateEnabledRulesets', err);
    await chrome.storage.local.set({ lastError: `Filterlisten konnten nicht aktiviert werden: ${err.message}` });
  }

  // 2. Dynamic rules: allowlist + custom filters
  const rules = [];
  if (settings.allowlist.length) {
    rules.push({
      id: ALLOWLIST_RULE_IDS[0],
      priority: PRIORITY.userAllow,
      action: { type: 'allowAllRequests' },
      condition: { requestDomains: settings.allowlist, resourceTypes: ['main_frame', 'sub_frame'] },
    });
    rules.push({
      id: ALLOWLIST_RULE_IDS[1],
      priority: PRIORITY.userAllow,
      action: { type: 'allow' },
      condition: { initiatorDomains: settings.allowlist },
    });
  }
  const custom = getCustomParsed(settings);
  if (!settings.paused) {
    for (const rule of custom.rules) {
      rules.push({ ...rule, priority: rule.priority + USER_PRIORITY_BONUS });
    }
  }
  const customErrors = await replaceDynamicRules(rules);

  // 3. YouTube helper scripts
  await updateYoutubeScripts(settings);

  // 4. Badge
  await updateBadge(settings);

  await chrome.storage.local.set({ customErrors, lastApplied: Date.now() });
}

async function replaceDynamicRules(rules) {
  const existing = await chrome.declarativeNetRequest.getDynamicRules();
  const removeRuleIds = existing.map((r) => r.id);
  try {
    await chrome.declarativeNetRequest.updateDynamicRules({ removeRuleIds, addRules: rules });
    return [];
  } catch (err) {
    // One bad rule rejects the whole batch: add them one by one.
    await chrome.declarativeNetRequest.updateDynamicRules({ removeRuleIds });
    const errors = [];
    for (const rule of rules) {
      try {
        await chrome.declarativeNetRequest.updateDynamicRules({ addRules: [rule] });
      } catch (e) {
        errors.push(`${rule.condition.urlFilter || rule.condition.requestDomains?.join(',') || 'Regel'}: ${e.message}`);
      }
    }
    return errors.length ? errors : [err.message];
  }
}

let customParsed = null;
function getCustomParsed(settings) {
  if (!customParsed) {
    customParsed = parseFilterList(settings.customFilters || '', {
      startId: CUSTOM_START_ID,
      allowStartId: CUSTOM_ALLOW_START_ID,
    });
  }
  return customParsed;
}

async function updateBadge(settings) {
  try {
    await chrome.declarativeNetRequest.setExtensionActionOptions({ displayActionCountAsBadgeText: !settings.paused });
  } catch {
    // Not supported by every browser.
  }
  await chrome.action.setBadgeBackgroundColor({ color: settings.paused ? '#888888' : '#d93025' });
  await chrome.action.setBadgeText({ text: settings.paused ? 'AUS' : '' });
}

async function updateYoutubeScripts(settings) {
  if (!chrome.scripting?.registerContentScripts) return;
  try {
    const registered = await chrome.scripting.getRegisteredContentScripts({ ids: YT_SCRIPT_IDS });
    if (registered.length) await chrome.scripting.unregisterContentScripts({ ids: registered.map((s) => s.id) });
    const active = settings.youtube && !settings.paused && !isAllowlisted(settings, 'www.youtube.com');
    if (!active) return;
    const matches = ['https://www.youtube.com/*', 'https://m.youtube.com/*', 'https://music.youtube.com/*',
      'https://www.youtube-nocookie.com/*'];
    await chrome.scripting.registerContentScripts([
      { id: 'yt-main', matches, js: ['content/youtube-main.js'], runAt: 'document_start', world: 'MAIN', allFrames: true },
      { id: 'yt-skip', matches, js: ['content/youtube-skip.js'], runAt: 'document_start', allFrames: true },
    ]);
  } catch (err) {
    console.warn('YouTube scripts', err);
  }
}

// --------------------------------------------------------- cosmetic hiding

const cosmeticData = new Map();
async function loadCosmetic(id) {
  if (!cosmeticData.has(id)) {
    cosmeticData.set(id, fetch(chrome.runtime.getURL(`cosmetic/${id}.json`)).then((r) => r.json()));
  }
  return cosmeticData.get(id);
}

const cosmeticCache = new Map();
async function cssForHost(settings, host) {
  const key = host;
  if (cosmeticCache.has(key)) return cosmeticCache.get(key);
  const selectors = new Set();
  for (const id of settings.enabledLists) {
    if (!LISTS.some((l) => l.id === id)) continue;
    for (const s of selectorsForHost(await loadCosmetic(id), host)) selectors.add(s);
  }
  for (const s of selectorsForHost(getCustomParsed(settings).cosmetic, host)) selectors.add(s);
  // One rule per selector: an invalid selector then only drops itself.
  let css = '';
  for (const s of selectors) css += `${s}{display:none!important}\n`;
  if (cosmeticCache.size > 200) cosmeticCache.clear();
  cosmeticCache.set(key, css);
  return css;
}

async function injectCosmetics(sender) {
  const tabId = sender.tab?.id;
  if (tabId === undefined || tabId < 0) return { ok: false };
  const settings = await getSettings();
  if (settings.paused) return { ok: false };
  const topHost = hostOf(sender.tab.url || '');
  if (isAllowlisted(settings, topHost)) return { ok: false };
  const host = hostOf(sender.url || '') || topHost;
  if (!host) return { ok: false };
  const css = await cssForHost(settings, host);
  if (!css) return { ok: true };
  await chrome.scripting.insertCSS({
    target: { tabId, frameIds: [sender.frameId ?? 0] },
    css,
    origin: 'USER',
  });
  return { ok: true };
}

// ------------------------------------------------------------- pop-ups

let popupMatchers = null;
async function getPopupMatchers(settings) {
  if (popupMatchers) return popupMatchers;
  const block = [];
  const allow = [];
  const sources = [];
  for (const id of settings.enabledLists) {
    if (LISTS.some((l) => l.id === id)) sources.push((await loadCosmetic(id)).popup || []);
  }
  for (const list of sources) {
    for (const p of list) {
      try {
        const m = { re: new RegExp(p.re, 'i'), d: p.d, nd: p.nd, tp: p.tp };
        (p.ex ? allow : block).push(m);
      } catch {
        // ignore invalid patterns
      }
    }
  }
  popupMatchers = { block, allow };
  return popupMatchers;
}

function baseDomain(host) {
  const parts = host.split('.');
  if (parts.length <= 2) return host;
  const sld = parts[parts.length - 2];
  const tld = parts[parts.length - 1];
  const n = tld.length === 2 && sld.length <= 3 ? 3 : 2;
  return parts.slice(-n).join('.');
}

function popupMatch(m, url, sourceHost, targetHost) {
  if (m.d && !matchesDomainList(sourceHost, m.d)) return false;
  if (m.nd && matchesDomainList(sourceHost, m.nd)) return false;
  if (m.tp !== undefined) {
    const third = baseDomain(sourceHost) !== baseDomain(targetHost || '');
    if (m.tp !== third) return false;
  }
  return m.re.test(url);
}

// Tabs opened by a page, watched for a few seconds (pop-unders often
// open about:blank first and navigate afterwards).
const popupCandidates = new Map();

async function checkPopup(tabId, url) {
  const candidate = popupCandidates.get(tabId);
  if (!candidate || Date.now() - candidate.created > 5000) {
    popupCandidates.delete(tabId);
    return;
  }
  const targetHost = hostOf(url);
  if (!targetHost) return;
  const settings = await getSettings();
  if (settings.paused || !settings.popupBlocking || isAllowlisted(settings, candidate.sourceHost)) return;
  const { block, allow } = await getPopupMatchers(settings);
  const blocked = block.some((m) => popupMatch(m, url, candidate.sourceHost, targetHost))
    && !allow.some((m) => popupMatch(m, url, candidate.sourceHost, targetHost));
  if (!blocked) return;
  popupCandidates.delete(tabId);
  try {
    await chrome.tabs.remove(tabId);
    const { stats } = await getSettings();
    await chrome.storage.local.set({ stats: { ...stats, popups: (stats.popups || 0) + 1 } });
  } catch {
    // tab already gone
  }
}

chrome.webNavigation.onCreatedNavigationTarget.addListener(async (details) => {
  try {
    const source = await chrome.tabs.get(details.sourceTabId);
    const sourceHost = hostOf(source.url || '');
    if (!sourceHost) return;
    popupCandidates.set(details.tabId, { sourceHost, created: Date.now() });
    await checkPopup(details.tabId, details.url);
  } catch {
    // source tab vanished
  }
});

chrome.webNavigation.onBeforeNavigate.addListener((details) => {
  if (details.frameId === 0 && popupCandidates.has(details.tabId)) checkPopup(details.tabId, details.url);
});

chrome.tabs.onRemoved.addListener((tabId) => popupCandidates.delete(tabId));

// ------------------------------------------------------------ messaging

async function blockedCount(tabId) {
  try {
    const { rulesMatchedInfo } = await chrome.declarativeNetRequest.getMatchedRules({ tabId });
    return rulesMatchedInfo.filter((i) => i.rule.ruleId < ALLOW_ID_OFFSET).length;
  } catch {
    try {
      const text = await chrome.action.getBadgeText({ tabId });
      return Number.parseInt(text, 10) || 0;
    } catch {
      return 0;
    }
  }
}

async function addCustomFilter(filter) {
  const settings = await getSettings();
  const lines = (settings.customFilters || '').split('\n').filter((l) => l.trim());
  if (!lines.includes(filter)) lines.push(filter);
  await chrome.storage.local.set({ customFilters: lines.join('\n') });
  await applySettings();
}

async function setAllowlisted(host, allow) {
  const settings = await getSettings();
  const domain = normalizeDomain(host.replace(/^www\./, ''));
  if (!domain) return;
  const list = allow
    ? [...settings.allowlist, domain]
    : settings.allowlist.filter((d) => !matchesDomainList(host, [d]) && d !== domain);
  await chrome.storage.local.set({ allowlist: [...new Set(list)].sort() });
  await applySettings();
}

async function startPicker(tabId) {
  await chrome.scripting.executeScript({ target: { tabId, frameIds: [0] }, files: ['content/picker.js'] });
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  const handle = async () => {
    switch (msg?.type) {
      case 'cosmetic':
        return injectCosmetics(sender);
      case 'tabInfo': {
        const settings = await getSettings();
        const tab = await chrome.tabs.get(msg.tabId);
        const host = hostOf(tab.url || '');
        return {
          host,
          paused: settings.paused,
          allowlisted: isAllowlisted(settings, host),
          blocked: await blockedCount(msg.tabId),
          popups: settings.stats.popups || 0,
        };
      }
      case 'setAllowlisted':
        await setAllowlisted(msg.host, msg.allow);
        return { ok: true };
      case 'setPaused':
        await chrome.storage.local.set({ paused: !!msg.paused });
        await applySettings();
        return { ok: true };
      case 'startPicker':
        await startPicker(msg.tabId);
        return { ok: true };
      case 'addFilter': {
        if (typeof msg.filter !== 'string' || !msg.filter.includes('##')) return { ok: false };
        await addCustomFilter(msg.filter.trim());
        // Hide the element right away without reloading.
        if (sender.tab?.id !== undefined) {
          const selector = msg.filter.slice(msg.filter.indexOf('##') + 2);
          await chrome.scripting.insertCSS({
            target: { tabId: sender.tab.id, allFrames: true },
            css: `${selector}{display:none!important}`,
            origin: 'USER',
          }).catch(() => {});
        }
        return { ok: true };
      }
      case 'apply':
        await applySettings();
        return { ok: true };
      default:
        return undefined;
    }
  };
  handle().then(sendResponse, (err) => sendResponse({ ok: false, error: String(err?.message || err) }));
  return true;
});

// ------------------------------------------------------------ lifecycle

function setupContextMenu() {
  chrome.contextMenus.removeAll(() => {
    chrome.contextMenus.create({
      id: 'hide-element',
      title: 'Element mit Schild ausblenden …',
      contexts: ['page', 'image', 'frame', 'link', 'video'],
    });
  });
}

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'hide-element' && tab?.id !== undefined) startPicker(tab.id).catch(() => {});
});

chrome.runtime.onInstalled.addListener(async (details) => {
  const current = await chrome.storage.local.get(null);
  const missing = Object.fromEntries(Object.entries(DEFAULTS).filter(([k]) => !(k in current)));
  if (Object.keys(missing).length) await chrome.storage.local.set(missing);
  setupContextMenu();
  await applySettings();
  // Firefox asks for host permissions separately; the options page explains it.
  const granted = await chrome.permissions.contains({ origins: ['<all_urls>'] }).catch(() => true);
  if (details.reason === 'install' && !granted) chrome.runtime.openOptionsPage();
});

chrome.runtime.onStartup.addListener(() => {
  applySettings();
});

chrome.storage.onChanged.addListener((changes, area) => {
  if (area !== 'local') return;
  const relevant = ['enabledLists', 'allowlist', 'customFilters', 'paused', 'youtube'];
  if (relevant.some((k) => k in changes)) {
    cosmeticCache.clear();
    popupMatchers = null;
    customParsed = null;
  }
});
