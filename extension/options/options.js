import { LISTS } from '../lib/lists.js';

const $ = (id) => document.getElementById(id);
const send = (msg) => chrome.runtime.sendMessage(msg);
const get = (keys) => chrome.storage.local.get(keys);
const set = async (values) => {
  await chrome.storage.local.set(values);
  await send({ type: 'apply' });
  await render();
};

function flash(id) {
  $(id).hidden = false;
  setTimeout(() => { $(id).hidden = true; }, 2000);
}

async function ruleCount(id) {
  try {
    const res = await fetch(`../rules/${id}.json`);
    return (await res.json()).length;
  } catch {
    return 0;
  }
}

async function renderLists(enabledLists) {
  const box = $('lists');
  if (!box.childElementCount) {
    for (const list of LISTS) {
      const label = document.createElement('label');
      label.className = 'row';
      const input = document.createElement('input');
      input.type = 'checkbox';
      input.dataset.list = list.id;
      const text = document.createElement('span');
      const name = document.createElement('b');
      name.textContent = list.name;
      const desc = document.createElement('small');
      desc.textContent = list.description;
      const meta = document.createElement('span');
      meta.className = 'meta';
      text.append(name, desc, meta);
      label.append(input, ' ', text);
      ruleCount(list.id).then((n) => {
        meta.textContent = `${n.toLocaleString('de-DE')} Netzwerkregeln`;
      });
      input.addEventListener('change', async () => {
        const checked = [...box.querySelectorAll('input:checked')].map((i) => i.dataset.list);
        await set({ enabledLists: checked });
      });
      box.append(label);
    }
  }
  for (const input of box.querySelectorAll('input')) input.checked = enabledLists.includes(input.dataset.list);
}

async function render() {
  const s = await get(['enabledLists', 'allowlist', 'customFilters', 'paused', 'youtube', 'popupBlocking',
    'customErrors', 'lastError', 'stats']);
  $('enabled').checked = !s.paused;
  $('youtube').checked = s.youtube !== false;
  $('popupBlocking').checked = s.popupBlocking !== false;
  await renderLists(s.enabledLists || []);
  if (document.activeElement !== $('allowlist')) $('allowlist').value = (s.allowlist || []).join('\n');
  if (document.activeElement !== $('customFilters')) $('customFilters').value = s.customFilters || '';

  const errors = $('filterErrors');
  errors.replaceChildren();
  for (const e of s.customErrors || []) {
    const li = document.createElement('li');
    li.textContent = e;
    errors.append(li);
  }
  $('errorBox').hidden = !s.lastError;
  $('errorText').textContent = s.lastError || '';

  let available = '';
  try {
    const n = await chrome.declarativeNetRequest.getAvailableStaticRuleCount();
    available = ` · noch ${n.toLocaleString('de-DE')} Regeln für weitere Listen frei`;
  } catch {
    // not supported
  }
  const enabledRulesets = await chrome.declarativeNetRequest.getEnabledRulesets();
  $('stats').textContent = `${enabledRulesets.length} Filterlisten aktiv · ${(s.stats?.popups || 0).toLocaleString('de-DE')} Pop-ups geschlossen${available}`;

  const granted = await chrome.permissions.contains({ origins: ['<all_urls>'] });
  $('permissionBox').hidden = granted;
}

$('enabled').addEventListener('change', (e) => set({ paused: !e.target.checked }));
$('youtube').addEventListener('change', (e) => set({ youtube: e.target.checked }));
$('popupBlocking').addEventListener('change', (e) => set({ popupBlocking: e.target.checked }));

$('saveAllowlist').addEventListener('click', async () => {
  const domains = $('allowlist').value.split(/[\s,]+/)
    .map((d) => d.trim().toLowerCase().replace(/^https?:\/\//, '').replace(/\/.*$/, '').replace(/^www\./, ''))
    .filter((d) => /^[a-z0-9.-]+\.[a-z0-9-]+$/.test(d));
  $('allowlist').blur();
  await set({ allowlist: [...new Set(domains)].sort() });
  flash('allowlistSaved');
});

$('saveFilters').addEventListener('click', async () => {
  $('customFilters').blur();
  await set({ customFilters: $('customFilters').value });
  flash('filtersSaved');
});

$('grant').addEventListener('click', async () => {
  await chrome.permissions.request({ origins: ['<all_urls>'] });
  render();
});

$('export').addEventListener('click', async () => {
  const data = await get(['enabledLists', 'allowlist', 'customFilters', 'youtube', 'popupBlocking']);
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'schild-einstellungen.json';
  a.click();
  URL.revokeObjectURL(a.href);
});

$('import').addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  try {
    const data = JSON.parse(await file.text());
    const clean = {};
    if (Array.isArray(data.enabledLists)) clean.enabledLists = data.enabledLists.filter((id) => LISTS.some((l) => l.id === id));
    if (Array.isArray(data.allowlist)) clean.allowlist = data.allowlist.filter((d) => typeof d === 'string');
    if (typeof data.customFilters === 'string') clean.customFilters = data.customFilters;
    if (typeof data.youtube === 'boolean') clean.youtube = data.youtube;
    if (typeof data.popupBlocking === 'boolean') clean.popupBlocking = data.popupBlocking;
    await set(clean);
    alert('Einstellungen importiert.');
  } catch (err) {
    alert(`Import fehlgeschlagen: ${err.message}`);
  }
  e.target.value = '';
});

chrome.storage.onChanged.addListener(() => render());
render();
