const $ = (id) => document.getElementById(id);
const send = (msg) => chrome.runtime.sendMessage(msg);

const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
let info = null;

async function refresh() {
  info = await send({ type: 'tabInfo', tabId: tab.id });
  $('global').checked = !info.paused;
  $('host').textContent = info.host || 'Keine Webseite';
  $('blocked').textContent = info.blocked.toLocaleString('de-DE');
  $('footer').textContent = `${info.popups.toLocaleString('de-DE')} Pop-ups insgesamt geschlossen`;

  const status = $('status');
  const toggle = $('siteToggle');
  if (!info.host) {
    status.textContent = 'Auf dieser Seite nicht verfügbar';
    status.className = 'status';
    toggle.disabled = true;
    $('picker').disabled = true;
  } else if (info.paused) {
    status.textContent = 'Schild ist überall pausiert';
    status.className = 'status off';
    toggle.disabled = true;
  } else if (info.allowlisted) {
    status.textContent = 'Schutz auf dieser Seite deaktiviert';
    status.className = 'status off';
    toggle.disabled = false;
    toggle.textContent = 'Auf dieser Seite aktivieren';
    toggle.classList.add('enable');
  } else {
    status.textContent = 'Schutz aktiv';
    status.className = 'status on';
    toggle.disabled = false;
    toggle.textContent = 'Auf dieser Seite deaktivieren';
    toggle.classList.remove('enable');
  }
}

$('global').addEventListener('change', async (e) => {
  await send({ type: 'setPaused', paused: !e.target.checked });
  $('reload').hidden = false;
  refresh();
});

$('siteToggle').addEventListener('click', async () => {
  await send({ type: 'setAllowlisted', host: info.host, allow: !info.allowlisted });
  $('reload').hidden = false;
  refresh();
});

$('reloadBtn').addEventListener('click', () => {
  chrome.tabs.reload(tab.id);
  window.close();
});

$('picker').addEventListener('click', async () => {
  await send({ type: 'startPicker', tabId: tab.id });
  window.close();
});

$('options').addEventListener('click', () => {
  chrome.runtime.openOptionsPage();
  window.close();
});

refresh();
