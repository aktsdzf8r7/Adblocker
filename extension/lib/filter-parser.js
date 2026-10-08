// Converts Adblock Plus / EasyList filter syntax into
//  - declarativeNetRequest (DNR) rules for network blocking
//  - cosmetic (element hiding) data for the content side
// Pure ES module without dependencies: used by the build script (Node)
// and by the background service worker (custom user filters).

export const PRIORITY = {
  block: 1,
  allow: 2,
  importantBlock: 3,
  // Per-site allowlist / custom user exceptions beat everything from lists.
  userAllow: 100,
};

// Rule IDs >= this value are exceptions. Used to tell blocks from allows
// when counting matched rules.
export const ALLOW_ID_OFFSET = 5_000_000;

const TYPE_MAP = {
  script: ['script'],
  image: ['image'],
  stylesheet: ['stylesheet'],
  css: ['stylesheet'],
  object: ['object'],
  'object-subrequest': ['object'],
  xmlhttprequest: ['xmlhttprequest'],
  xhr: ['xmlhttprequest'],
  subdocument: ['sub_frame'],
  frame: ['sub_frame'],
  ping: ['ping'],
  beacon: ['ping'],
  media: ['media'],
  font: ['font'],
  websocket: ['websocket'],
  other: ['other'],
  webtransport: ['webtransport'],
  document: ['main_frame', 'sub_frame'],
  doc: ['main_frame', 'sub_frame'],
};

const ALL_TYPES = [
  'main_frame', 'sub_frame', 'stylesheet', 'script', 'image', 'font', 'object',
  'xmlhttprequest', 'ping', 'media', 'websocket', 'webtransport', 'other',
];

// Options that change behaviour in ways DNR cannot express: skip the filter.
const UNSUPPORTED_OPTIONS = new Set([
  'redirect', 'redirect-rule', 'rewrite', 'csp', 'removeparam', 'queryprune',
  'sitekey', 'header', 'permissions', 'replace', 'urltransform', 'urlskip',
  'genericblock', 'empty', 'mp4', 'inline-script', 'inline-font', 'cname',
  'strict1p', 'strict3p', 'strict-first-party', 'strict-third-party', 'to',
  'app', 'webrtc', 'jsonprune', 'uritransform', 'ipaddress',
  'requestheader', 'responseheader', 'reason',
]);

const COSMETIC_EXCEPTION_OPTIONS = {
  elemhide: 'elemHide',
  ehide: 'elemHide',
  generichide: 'genericHide',
  ghide: 'genericHide',
  specifichide: 'specificHide',
  shide: 'specificHide',
};

const METHODS = new Set(['connect', 'delete', 'get', 'head', 'options', 'patch', 'post', 'put']);

// Extended (procedural) selectors that are not plain CSS.
const UNSUPPORTED_SELECTOR = /:(-abp-|has-text|contains|xpath|matches-css|matches-path|matches-attr|matches-prop|matches-media|upward|remove|style|min-text-length|watch-attr|others|if\(|if-not|nth-ancestor|shadow|properties)/;

const HOST_RE = /^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9_-]*[a-z0-9])?)*$/;

export function normalizeDomain(domain) {
  let d = domain.trim().toLowerCase();
  if (!d) return null;
  if (d.endsWith('.')) d = d.slice(0, -1);
  // Entity domains (example.*) cannot be expressed in DNR.
  if (d.includes('*')) return null;
  if (!HOST_RE.test(d)) {
    try {
      d = new URL(`http://${d}/`).hostname;
    } catch {
      return null;
    }
    if (!HOST_RE.test(d)) return null;
  }
  return d;
}

function parseDomainList(value, separator) {
  const include = [];
  const exclude = [];
  for (const raw of value.split(separator)) {
    const negated = raw.startsWith('~');
    const d = normalizeDomain(negated ? raw.slice(1) : raw);
    if (!d) continue;
    (negated ? exclude : include).push(d);
  }
  return { include, exclude };
}

// Splits "pattern$options" -> [pattern, options]. Handles "$" inside
// regex patterns and patterns that legitimately contain "$" in a URL.
function splitOptions(filter) {
  const idx = filter.lastIndexOf('$');
  if (idx < 0) return [filter, ''];
  const opts = filter.slice(idx + 1);
  // Options are a comma-separated list of known-shaped tokens.
  if (!/^~?[a-z0-9_-]+(=[^,]*)?(,~?[a-z0-9_-]+(=[^,]*)?)*$/i.test(opts)) {
    return [filter, ''];
  }
  return [filter.slice(0, idx), opts];
}

// ABP pattern -> RegExp source (used for pop-up matching in JS).
export function patternToRegExpSource(pattern) {
  let p = pattern;
  let start = '';
  let end = '';
  if (p.startsWith('||')) {
    start = '^[a-z][a-z0-9+.-]*:\\/\\/(?:[^/?#]*\\.)?';
    p = p.slice(2);
  } else if (p.startsWith('|')) {
    start = '^';
    p = p.slice(1);
  }
  if (p.endsWith('|')) {
    end = '$';
    p = p.slice(0, -1);
  }
  p = p.replace(/^\*+|\*+$/g, '');
  if (!p && !start) return null;
  const body = p
    .split('')
    .map((ch) => {
      if (ch === '*') return '.*';
      if (ch === '^') return '(?:[^\\w.%-]|$)';
      return /[\\^$.*+?()[\]{}|/-]/.test(ch) ? `\\${ch}` : ch;
    })
    .join('');
  return start + body + end;
}

function isAscii(str) {
  return /^[\x20-\x7e]*$/.test(str);
}

// Normalises a filter pattern into a DNR urlFilter. Returns
// undefined for "match everything", null if the pattern is unusable.
function toUrlFilter(pattern) {
  let p = pattern;
  if (!isAscii(p)) return null;
  // Regex filters are mostly not RE2 compatible and are limited to 1000
  // rules in DNR. They are very rare in the lists we use, so skip them.
  if (p.length > 2 && p.startsWith('/') && p.endsWith('/')) return null;

  let prefix = '';
  if (p.startsWith('||')) {
    prefix = '||';
    p = p.slice(2);
  } else if (p.startsWith('|')) {
    prefix = '|';
    p = p.slice(1);
  }
  let suffix = '';
  if (p.endsWith('|')) {
    suffix = '|';
    p = p.slice(0, -1);
  }
  // Leading/trailing wildcards are implicit.
  if (!prefix) p = p.replace(/^\*+/, '');
  if (!suffix) p = p.replace(/\*+$/, '');
  if (prefix === '||') p = p.replace(/^\*+/, '');
  if (p.includes('|')) return null;
  if (!p) return prefix || suffix ? null : undefined;
  if (p === '^') return undefined;
  if (prefix === '||' && /^[.^/]/.test(p)) return null;
  return (prefix + p + suffix).toLowerCase();
}

// Parse a single network filter. Returns
// { rule, cosmeticException } or null when it cannot be converted.
export function parseNetworkFilter(line) {
  let text = line;
  const isException = text.startsWith('@@');
  if (isException) text = text.slice(2);

  const [pattern, optionText] = splitOptions(text);

  const types = new Set();
  const excludedTypes = new Set();
  let domainType;
  let initiatorDomains = [];
  let excludedInitiatorDomains = [];
  let excludedRequestDomains = [];
  let requestMethods;
  let excludedRequestMethods;
  let important = false;
  let caseSensitive = false;
  let popupOnly = false;
  const cosmetic = [];

  if (optionText) {
    for (const rawOpt of optionText.split(',')) {
      const opt = rawOpt.trim();
      if (!opt) continue;
      const eq = opt.indexOf('=');
      const nameRaw = (eq === -1 ? opt : opt.slice(0, eq)).toLowerCase();
      const value = eq === -1 ? '' : opt.slice(eq + 1);
      const negated = nameRaw.startsWith('~');
      const name = negated ? nameRaw.slice(1) : nameRaw;

      if (UNSUPPORTED_OPTIONS.has(name) || name === 'badfilter') return null;

      if (name in COSMETIC_EXCEPTION_OPTIONS) {
        if (!isException) return null;
        cosmetic.push(COSMETIC_EXCEPTION_OPTIONS[name]);
        continue;
      }
      if (name === 'third-party' || name === '3p') {
        domainType = negated ? 'firstParty' : 'thirdParty';
      } else if (name === 'first-party' || name === '1p') {
        domainType = negated ? 'thirdParty' : 'firstParty';
      } else if (name === 'domain' || name === 'from') {
        const { include, exclude } = parseDomainList(value, '|');
        if (!include.length && !exclude.length) return null;
        initiatorDomains = include;
        excludedInitiatorDomains = exclude;
      } else if (name === 'denyallow') {
        const { include } = parseDomainList(value, '|');
        excludedRequestDomains = include;
      } else if (name === 'method') {
        const { include, exclude } = parseDomainList(value, '|');
        const inc = include.filter((m) => METHODS.has(m));
        const exc = exclude.filter((m) => METHODS.has(m));
        if (inc.length) requestMethods = inc;
        if (exc.length) excludedRequestMethods = exc;
      } else if (name === 'important') {
        important = true;
      } else if (name === 'match-case') {
        caseSensitive = true;
      } else if (name === 'popup') {
        if (negated) continue;
        popupOnly = true;
      } else if (name === 'all') {
        ALL_TYPES.forEach((t) => types.add(t));
      } else if (name in TYPE_MAP) {
        for (const t of TYPE_MAP[name]) (negated ? excludedTypes : types).add(t);
      } else {
        // Unknown option: be conservative.
        return null;
      }
    }
  }

  let cosmeticException = null;
  if (cosmetic.length) {
    // @@||example.com^$generichide -> disable generic hiding on example.com
    const m = /^\|\|([a-z0-9.-]+)\^?$/i.exec(pattern) || /^\|?https?:\/\/([a-z0-9.-]+)\/?\^?$/i.exec(pattern);
    const hosts = [];
    const host = m && normalizeDomain(m[1]);
    if (host) hosts.push(host);
    hosts.push(...initiatorDomains);
    if (hosts.length) cosmeticException = { kinds: cosmetic, hosts };
    // Only a network rule as well if it also has resource types (e.g. $document).
    if (!types.size) return cosmeticException ? { rule: null, cosmeticException } : null;
  }

  // Pop-ups cannot be blocked by DNR; they are handled by the background
  // script (closes the new tab), so return a matcher description instead.
  if (popupOnly && !types.size) {
    if (!isAscii(pattern) || (pattern.startsWith('/') && pattern.endsWith('/') && pattern.length > 2)) return null;
    const re = patternToRegExpSource(pattern);
    if (re === null) return null;
    const popup = { re, ex: isException };
    if (initiatorDomains.length) popup.d = initiatorDomains;
    if (excludedInitiatorDomains.length) popup.nd = excludedInitiatorDomains;
    if (domainType) popup.tp = domainType === 'thirdParty';
    return { rule: null, cosmeticException: null, popup };
  }

  const urlFilter = toUrlFilter(pattern);
  if (urlFilter === null) return null;
  if (urlFilter === undefined && !initiatorDomains.length && !types.has('main_frame')) {
    // A filter that matches everything everywhere would break the web.
    if (!isException) return null;
  }

  let resourceTypes = types.size ? [...types].filter((t) => !excludedTypes.has(t)) : undefined;
  if (resourceTypes && !resourceTypes.length) return null;
  const excludedResourceTypes = !resourceTypes && excludedTypes.size ? [...excludedTypes] : undefined;

  let actionType = isException ? 'allow' : 'block';
  if (isException && resourceTypes && resourceTypes.every((t) => t === 'main_frame' || t === 'sub_frame')
      && resourceTypes.includes('main_frame')) {
    // @@...$document -> allow everything on matching pages.
    actionType = 'allowAllRequests';
  }

  const condition = {};
  if (urlFilter !== undefined) condition.urlFilter = urlFilter;
  if (caseSensitive) condition.isUrlFilterCaseSensitive = true;
  if (domainType) condition.domainType = domainType;
  if (initiatorDomains.length) condition.initiatorDomains = initiatorDomains;
  if (excludedInitiatorDomains.length) condition.excludedInitiatorDomains = excludedInitiatorDomains;
  if (excludedRequestDomains.length) condition.excludedRequestDomains = excludedRequestDomains;
  if (requestMethods) condition.requestMethods = requestMethods;
  if (excludedRequestMethods) condition.excludedRequestMethods = excludedRequestMethods;
  if (resourceTypes) condition.resourceTypes = resourceTypes.sort();
  if (excludedResourceTypes) condition.excludedResourceTypes = excludedResourceTypes.sort();

  let priority = PRIORITY.block;
  if (isException) priority = PRIORITY.allow;
  else if (important) priority = PRIORITY.importantBlock;

  return { rule: { priority, action: { type: actionType }, condition }, cosmeticException };
}

// Parse a single cosmetic filter line. Returns
// { selector, include: [...], exclude: [...], exception } or null.
export function parseCosmeticFilter(line) {
  const m = /^([^#]*)(#@?#)(.+)$/.exec(line);
  if (!m) return null;
  const [, domainPart, sep, selectorRaw] = m;
  const selector = selectorRaw.trim();
  // Scriptlets (##+js), HTML filters (##^) and procedural selectors.
  if (selector.startsWith('+js') || selector.startsWith('^') || selector.startsWith('%')) return null;
  if (/[{}]/.test(selector) || selector.includes('/*')) return null;
  if (UNSUPPORTED_SELECTOR.test(selector)) return null;
  const include = [];
  const exclude = [];
  if (domainPart) {
    for (const raw of domainPart.split(',')) {
      const negated = raw.startsWith('~');
      const name = (negated ? raw.slice(1) : raw).trim().toLowerCase();
      if (!name) continue;
      // Allow entity domains like "google.*" for cosmetic filters.
      const d = name.endsWith('.*') ? (normalizeDomain(name.slice(0, -2)) && name) : normalizeDomain(name);
      if (!d) continue;
      (negated ? exclude : include).push(d);
    }
    if (!include.length && !exclude.length) return null;
  }
  return { selector, include, exclude, exception: sep === '#@#' };
}

export function createCosmeticData() {
  return { generic: [], specific: {}, exceptions: {}, elemHide: [], genericHide: [], specificHide: [] };
}

function pushMap(map, key, value) {
  (map[key] ||= []).push(value);
}

// Parses a full filter list text.
// Returns { rules: [DNR rules with ids], cosmetic, popup, stats }.
export function parseFilterList(text, { startId = 1, allowStartId = ALLOW_ID_OFFSET, groupDomains = true } = {}) {
  const lines = text.split(/\r?\n/);
  const badfilters = new Set();
  for (const raw of lines) {
    const line = raw.trim();
    const m = /^(.*)\$(.*)$/.exec(line);
    if (!m || line.startsWith('!')) continue;
    const opts = m[2].split(',');
    if (opts.includes('badfilter')) {
      badfilters.add(`${m[1]}$${opts.filter((o) => o !== 'badfilter').join(',')}`.replace(/\$$/, ''));
    }
  }

  const stats = { lines: 0, network: 0, cosmetic: 0, skipped: 0 };
  const rawRules = [];
  const cosmetic = createCosmeticData();
  const globalCosmeticExceptions = new Set();
  const seenRules = new Set();
  const popup = [];

  for (const raw of lines) {
    const line = raw.trim();
    if (!line || line.startsWith('!') || line.startsWith('[')) continue;
    stats.lines++;

    if (/#@?#|#[?$%]#|#@[?$%]#|\$\$|\$@\$/.test(line) && !line.startsWith('@@') && !/^[|/]/.test(line)) {
      if (/#[?$%]#|#@[?$%]#|\$\$|\$@\$/.test(line)) { stats.skipped++; continue; }
      const c = parseCosmeticFilter(line);
      if (!c) { stats.skipped++; continue; }
      stats.cosmetic++;
      if (c.exception) {
        if (!c.include.length) globalCosmeticExceptions.add(c.selector);
        for (const d of c.include) pushMap(cosmetic.exceptions, d, c.selector);
      } else if (!c.include.length) {
        cosmetic.generic.push(c.selector);
        for (const d of c.exclude) pushMap(cosmetic.exceptions, d, c.selector);
      } else {
        for (const d of c.include) pushMap(cosmetic.specific, d, c.selector);
        for (const d of c.exclude) pushMap(cosmetic.exceptions, d, c.selector);
      }
      continue;
    }

    if (badfilters.has(line) || line.includes('$badfilter') || line.includes(',badfilter')) {
      stats.skipped++;
      continue;
    }
    const parsed = parseNetworkFilter(line);
    if (!parsed) { stats.skipped++; continue; }
    if (parsed.popup) {
      popup.push(parsed.popup);
      stats.network++;
      continue;
    }
    if (parsed.cosmeticException) {
      for (const kind of parsed.cosmeticException.kinds) {
        cosmetic[kind].push(...parsed.cosmeticException.hosts);
      }
    }
    if (!parsed.rule) continue;
    const key = JSON.stringify(parsed.rule);
    if (seenRules.has(key)) continue;
    seenRules.add(key);
    rawRules.push(parsed.rule);
    stats.network++;
  }

  if (globalCosmeticExceptions.size) {
    cosmetic.generic = cosmetic.generic.filter((s) => !globalCosmeticExceptions.has(s));
    for (const d of Object.keys(cosmetic.specific)) {
      cosmetic.specific[d] = cosmetic.specific[d].filter((s) => !globalCosmeticExceptions.has(s));
      if (!cosmetic.specific[d].length) delete cosmetic.specific[d];
    }
  }
  cosmetic.generic = [...new Set(cosmetic.generic)];
  for (const key of ['specific', 'exceptions']) {
    for (const d of Object.keys(cosmetic[key])) cosmetic[key][d] = [...new Set(cosmetic[key][d])];
  }
  for (const key of ['elemHide', 'genericHide', 'specificHide']) cosmetic[key] = [...new Set(cosmetic[key])];

  const rules = groupDomains ? groupDomainRules(rawRules) : rawRules;
  let nextBlock = startId;
  let nextAllow = allowStartId;
  for (const rule of rules) {
    rule.id = rule.action.type === 'block' ? nextBlock++ : nextAllow++;
  }
  // Put "id" first for readability of the generated JSON.
  const ordered = rules.map(({ id, ...rest }) => ({ id, ...rest }));
  return { rules: ordered, cosmetic, popup, stats };
}

// Merges "||example.com^" style rules with otherwise identical conditions
// into one rule with a requestDomains list (much fewer rules, faster).
function groupDomainRules(rules) {
  const groups = new Map();
  const out = [];
  for (const rule of rules) {
    const uf = rule.condition.urlFilter;
    const m = uf && /^\|\|([a-z0-9.-]+)\^$/.exec(uf);
    const host = m && normalizeDomain(m[1]);
    if (!host || rule.condition.isUrlFilterCaseSensitive) {
      out.push(rule);
      continue;
    }
    const { urlFilter, ...restCondition } = rule.condition;
    const key = JSON.stringify([rule.priority, rule.action, restCondition]);
    let group = groups.get(key);
    if (!group) {
      group = { priority: rule.priority, action: rule.action, condition: { requestDomains: [], ...restCondition } };
      groups.set(key, group);
      out.push(group);
    }
    group.condition.requestDomains.push(host);
  }
  for (const group of groups.values()) {
    group.condition.requestDomains = [...new Set(group.condition.requestDomains)].sort();
  }
  return out;
}

// Returns the CSS selectors to hide for a hostname.
export function selectorsForHost(data, hostname) {
  const candidates = hostCandidates(hostname);
  const has = (list) => candidates.some((c) => list.includes(c));
  if (has(data.elemHide)) return [];
  const exceptions = new Set();
  for (const c of candidates) for (const s of data.exceptions[c] || []) exceptions.add(s);
  const result = [];
  if (!has(data.genericHide)) {
    for (const s of data.generic) if (!exceptions.has(s)) result.push(s);
  }
  if (!has(data.specificHide)) {
    for (const c of candidates) {
      for (const s of data.specific[c] || []) if (!exceptions.has(s)) result.push(s);
    }
  }
  return result;
}

// "a.b.example.co.uk" -> itself, its parent domains and entity forms
// ("example.co.*", "example.*").
export function hostCandidates(hostname) {
  const labels = hostname.toLowerCase().split('.').filter(Boolean);
  const out = [];
  for (let i = 0; i < labels.length; i++) {
    const suffix = labels.slice(i);
    out.push(suffix.join('.'));
    if (suffix.length >= 2) out.push(`${suffix.slice(0, -1).join('.')}.*`);
    if (suffix.length >= 3) out.push(`${suffix.slice(0, -2).join('.')}.*`);
  }
  return out;
}
