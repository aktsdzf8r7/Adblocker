// End-to-end test: loads the extension into a real Chromium and checks that
// ads/trackers/pop-ups are blocked. All hostnames are resolved to a local
// test server, so real ad domains can be used without internet access.
import http from 'node:http';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const extPath = join(dirname(fileURLToPath(import.meta.url)), '..', 'extension');
const requests = [];

const testPage = (port) => `<!doctype html><html><head><title>Testseite</title>
<script src="http://pagead2.googlesyndication.com:${port}/pagead/js/adsbygoogle.js"></script>
<script src="http://www.google-analytics.com:${port}/analytics.js"></script>
<script src="http://popads.net:${port}/pop.js"></script>
<script src="http://cdn.schild-safe.com:${port}/app.js"></script>
</head><body>
<div id="content">Artikeltext</div>
<div id="AD_300">Werbung 300</div>
<div id="AdSense1">AdSense</div>
<div class="custom-box">Eigener Filter</div>
<button id="pop" onclick="window.open('http://www.popads.net:${port}/landing?x=1')">Pop</button>
<button id="okpop" onclick="window.open('http://news.schild-test.com:${port}/other')">OK-Pop</button>
</body></html>`;

const server = http.createServer((req, res) => {
  const host = (req.headers.host || '').replace(/:\d+$/, '');
  requests.push(`${host}${req.url}`);
  if (req.url.endsWith('.js')) {
    const name = host.split('.').slice(-2, -1)[0];
    res.writeHead(200, { 'content-type': 'application/javascript' });
    res.end(`window.loaded = (window.loaded || []).concat(${JSON.stringify(name)});`);
    return;
  }
  res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
  res.end(testPage(server.address().port));
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const port = server.address().port;
const url = (u) => u.replace(/^http:\/\/([^/]+)/, `http://$1:${port}`);


const userDataDir = await mkdtemp(join(tmpdir(), 'schild-e2e-'));
const context = await chromium.launchPersistentContext(userDataDir, {
  channel: 'chromium',
  headless: true,
  args: [
    `--disable-extensions-except=${extPath}`,
    `--load-extension=${extPath}`,
    '--host-resolver-rules=MAP * 127.0.0.1',
    '--no-proxy-server',
  ],
});

let failures = 0;
async function check(name, fn) {
  try {
    await fn();
    console.log(`  ✓ ${name}`);
  } catch (err) {
    failures++;
    console.log(`  ✗ ${name}\n    ${err.message.split('\n').join('\n    ')}`);
  }
}

try {
  let [sw] = context.serviceWorkers();
  if (!sw) sw = await context.waitForEvent('serviceworker');
  const extId = new URL(sw.url()).host;
  const errors = [];
  sw.on('console', (m) => m.type() === 'error' && errors.push(m.text()));

  // Wait until the background has applied its settings.
  for (let i = 0; i < 50; i++) {
    const done = await sw.evaluate(() => !!chrome.storage
      && chrome.storage.local.get('lastApplied').then((s) => !!s.lastApplied));
    if (done) break;
    await new Promise((r) => setTimeout(r, 200));
  }

  const ext = await context.newPage();
  await ext.goto(`chrome-extension://${extId}/options/options.html`);
  const send = (msg) => ext.evaluate((m) => chrome.runtime.sendMessage(m), msg);

  console.log('Standardeinstellungen');
  const page = await context.newPage();
  const pageErrors = [];
  page.on('pageerror', (e) => pageErrors.push(e.message));
  await page.goto(url('http://news.schild-test.com/'));
  await page.waitForTimeout(800);

  await check('Rulesets aktiv', async () => {
    const ids = await ext.evaluate(() => chrome.declarativeNetRequest.getEnabledRulesets());
    assert.deepEqual(ids.sort(), ['easylist', 'easylist_germany', 'easyprivacy']);
  });
  await check('Werbeskript (googlesyndication) blockiert', () => {
    assert.ok(!requests.some((r) => r.startsWith('pagead2.googlesyndication.com')), requests.join(', '));
  });
  await check('Tracker (google-analytics) blockiert', () => {
    assert.ok(!requests.some((r) => r.startsWith('www.google-analytics.com')));
  });
  await check('popads.net blockiert', () => {
    assert.ok(!requests.some((r) => r.startsWith('popads.net')));
  });
  await check('Normales Skript lädt weiterhin', async () => {
    assert.deepEqual(await page.evaluate(() => window.loaded), ['schild-safe']);
  });
  await check('Werbeelemente ausgeblendet', async () => {
    assert.equal(await page.locator('#AD_300').isVisible(), false);
    assert.equal(await page.locator('#AdSense1').isVisible(), false);
    assert.equal(await page.locator('#content').isVisible(), true);
  });
  await check('Seite kann Ausblendung nicht überschreiben (user-origin CSS)', async () => {
    await page.addStyleTag({ content: '#AD_300{display:block!important}' });
    assert.equal(await page.locator('#AD_300').isVisible(), false);
  });
  await check('Zähler im Popup/Badge > 0', async () => {
    const pageTabId = await sw.evaluate(async () => (await chrome.tabs.query({ url: '*://news.schild-test.com/*' }))[0].id);
    const info = await send({ type: 'tabInfo', tabId: pageTabId });
    assert.ok(info.blocked >= 3, JSON.stringify(info));
    assert.equal(info.host, 'news.schild-test.com');
  });
  await check('Werbe-Pop-up wird geschlossen', async () => {
    const before = context.pages().length;
    await page.click('#pop');
    await page.waitForTimeout(1500);
    assert.equal(context.pages().length, before);
  });
  await check('Normales Pop-up bleibt offen', async () => {
    const before = context.pages().length;
    const popupPromise = context.waitForEvent('page');
    await page.click('#okpop');
    const popup = await popupPromise;
    await page.waitForTimeout(1200);
    assert.equal(context.pages().length, before + 1);
    await popup.close();
  });
  await check('YouTube-Skripte registriert', async () => {
    const scripts = await ext.evaluate(() => chrome.scripting.getRegisteredContentScripts());
    assert.deepEqual(scripts.map((s) => s.id).sort(), ['yt-main', 'yt-skip']);
  });
  await check('Element-Picker startet', async () => {
    const pageTabId = await sw.evaluate(async () => (await chrome.tabs.query({ url: '*://news.schild-test.com/*' }))[0].id);
    const res = await send({ type: 'startPicker', tabId: pageTabId });
    assert.equal(res.ok, true);
    assert.equal(await page.locator('schild-picker').count(), 1);
    await page.keyboard.press('Escape');
    assert.equal(await page.locator('schild-picker').count(), 0);
  });

  console.log('Seite auf Ausnahmeliste');
  await send({ type: 'setAllowlisted', host: 'news.schild-test.com', allow: true });
  requests.length = 0;
  await page.reload();
  await page.waitForTimeout(800);
  await check('Alles lädt auf erlaubter Seite', async () => {
    const loaded = await page.evaluate(() => window.loaded);
    assert.ok(loaded.includes('googlesyndication') && loaded.includes('google-analytics'), String(loaded));
    assert.equal(await page.locator('#AD_300').isVisible(), true);
  });
  await send({ type: 'setAllowlisted', host: 'news.schild-test.com', allow: false });

  console.log('Eigene Filter');
  await ext.evaluate(() => chrome.storage.local.set({
    customFilters: '! Test\n||cdn.schild-safe.com^\nschild-test.com##.custom-box',
  }));
  await send({ type: 'apply' });
  requests.length = 0;
  await page.reload();
  await page.waitForTimeout(800);
  await check('Eigener Netzwerkfilter blockiert', () => {
    assert.ok(!requests.some((r) => r.startsWith('cdn.schild-safe.com')), requests.join(', '));
  });
  await check('Eigener Ausblendfilter wirkt', async () => {
    assert.equal(await page.locator('.custom-box').isVisible(), false);
    assert.equal(await page.locator('#AD_300').isVisible(), false);
  });
  await check('Keine Fehler bei eigenen Filtern', async () => {
    const { customErrors } = await ext.evaluate(() => chrome.storage.local.get('customErrors'));
    assert.deepEqual(customErrors, []);
  });

  console.log('Komplett pausiert');
  await send({ type: 'setPaused', paused: true });
  requests.length = 0;
  await page.reload();
  await page.waitForTimeout(800);
  await check('Pausiert: nichts wird blockiert', async () => {
    const loaded = await page.evaluate(() => window.loaded);
    assert.equal(loaded.length, 4, String(loaded));
    assert.equal(await page.locator('#AD_300').isVisible(), true);
  });
  await send({ type: 'setPaused', paused: false });
  requests.length = 0;
  await page.reload();
  await page.waitForTimeout(800);
  await check('Wieder aktiv: Blockieren funktioniert', () => {
    assert.ok(!requests.some((r) => r.startsWith('pagead2.googlesyndication.com')));
  });

  console.log('Filterlisten umschalten');
  await ext.evaluate(() => chrome.storage.local.set({ enabledLists: ['easylist', 'easyprivacy', 'easylist_germany', 'easylist_cookie', 'fanboy_annoyance'] }));
  await send({ type: 'apply' });
  await check('Alle Listen gleichzeitig aktivierbar', async () => {
    const ids = await ext.evaluate(() => chrome.declarativeNetRequest.getEnabledRulesets());
    assert.equal(ids.length, 5);
    const { lastError } = await ext.evaluate(() => chrome.storage.local.get('lastError'));
    assert.ok(!lastError, lastError);
  });

  await check('Popup-Seite rendert', async () => {
    const p = await context.newPage();
    const errs = [];
    p.on('pageerror', (e) => errs.push(e.message));
    await p.goto(`chrome-extension://${extId}/popup/popup.html`);
    await p.waitForTimeout(500);
    assert.deepEqual(errs, []);
    await p.close();
  });
  await check('Keine Fehler im Hintergrundskript / auf der Seite', () => {
    assert.deepEqual(errors, []);
    assert.deepEqual(pageErrors, []);
  });
} finally {
  await context.close();
  server.close();
  await rm(userDataDir, { recursive: true, force: true });
}

console.log(failures ? `\n${failures} Test(s) fehlgeschlagen` : '\nAlle E2E-Tests bestanden');
process.exit(failures ? 1 : 0);
