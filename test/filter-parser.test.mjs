import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  ALLOW_ID_OFFSET, parseCosmeticFilter, parseFilterList, parseNetworkFilter, patternToRegExpSource, selectorsForHost,
} from '../extension/lib/filter-parser.js';

const rule = (line) => parseNetworkFilter(line)?.rule;

test('domain anchor block filter', () => {
  assert.deepEqual(rule('||ads.example.com^'), {
    priority: 1, action: { type: 'block' }, condition: { urlFilter: '||ads.example.com^' },
  });
});

test('options: types, third-party, domains', () => {
  const r = rule('/banner/*$script,image,third-party,domain=a.com|~b.a.com');
  assert.equal(r.condition.urlFilter, '/banner/');
  assert.deepEqual(r.condition.resourceTypes, ['image', 'script']);
  assert.equal(r.condition.domainType, 'thirdParty');
  assert.deepEqual(r.condition.initiatorDomains, ['a.com']);
  assert.deepEqual(r.condition.excludedInitiatorDomains, ['b.a.com']);
});

test('negated types', () => {
  const r = rule('||x.com^$~script,~image');
  assert.deepEqual(r.condition.excludedResourceTypes, ['image', 'script']);
});

test('exceptions and document exceptions', () => {
  assert.equal(rule('@@||cdn.com/ads.js').action.type, 'allow');
  assert.equal(rule('@@||cdn.com/ads.js').priority, 2);
  assert.equal(rule('@@||site.com^$document').action.type, 'allowAllRequests');
  assert.equal(rule('||x.com^$important').priority, 3);
});

test('unsupported options are skipped', () => {
  assert.equal(parseNetworkFilter('||x.com^$redirect=noop.js'), null);
  assert.equal(parseNetworkFilter('||x.com^$csp=script-src none'), null);
  assert.equal(parseNetworkFilter('||x.com^$unknownoption'), null);
  assert.equal(parseNetworkFilter('/^https?:\\/\\/[a-z]+/$script'), null);
});

test('match-everything filters are rejected', () => {
  assert.equal(parseNetworkFilter('*'), null);
  assert.equal(parseNetworkFilter('$script'), null);
  // ...but fine when limited to a site
  assert.deepEqual(rule('$websocket,domain=foo.com').condition, { initiatorDomains: ['foo.com'], resourceTypes: ['websocket'] });
});

test('cosmetic exception options', () => {
  const r = parseNetworkFilter('@@||news.com^$generichide');
  assert.deepEqual(r.cosmeticException, { kinds: ['genericHide'], hosts: ['news.com'] });
  assert.equal(r.rule, null);
  const r2 = parseNetworkFilter('@@$generichide,domain=a.com|b.com');
  assert.deepEqual(r2.cosmeticException.hosts, ['a.com', 'b.com']);
});

test('popup filters become matchers', () => {
  const p = parseNetworkFilter('||popads.net^$popup,third-party').popup;
  assert.equal(p.tp, true);
  const re = new RegExp(p.re, 'i');
  assert.ok(re.test('https://www.popads.net/click?x=1'));
  assert.ok(!re.test('https://notpopads.net/'));
  assert.ok(new RegExp(patternToRegExpSource('&adb=y^')).test('https://x.com/?a=1&adb=y&z'));
});

test('cosmetic filter parsing', () => {
  assert.deepEqual(parseCosmeticFilter('##.ad'), { selector: '.ad', include: [], exclude: [], exception: false });
  assert.deepEqual(parseCosmeticFilter('a.com,~b.a.com##.ad').include, ['a.com']);
  assert.equal(parseCosmeticFilter('a.com#@#.ad').exception, true);
  assert.equal(parseCosmeticFilter('a.com##.ad:has-text(Werbung)'), null);
  assert.equal(parseCosmeticFilter('a.com##+js(set, x, 1)'), null);
  assert.equal(parseCosmeticFilter('a.com##.x {color:red}'), null);
});

test('full list: grouping, ids, badfilter, cosmetics', () => {
  const list = [
    '[Adblock Plus 2.0]',
    '! comment',
    '||a.com^',
    '||b.com^',
    '||c.com^$third-party',
    '||d.com^',
    '||d.com^$badfilter',
    '@@||a.com/ok.js',
    '/adframe.',
    '##.ad-banner',
    '##.everywhere',
    '#@#.everywhere',
    'site.com##.site-ad',
    'site.com#@#.ad-banner',
    '~other.com##.not-on-other',
    '@@||nogeneric.com^$generichide',
    'google.*##.g-ad',
  ].join('\n');
  const { rules, cosmetic } = parseFilterList(list);
  const grouped = rules.find((r) => r.condition.requestDomains?.includes('a.com'));
  assert.deepEqual(grouped.condition.requestDomains, ['a.com', 'b.com']);
  assert.ok(!rules.some((r) => JSON.stringify(r).includes('d.com')), 'badfilter removes d.com');
  const ids = rules.map((r) => r.id);
  assert.equal(new Set(ids).size, ids.length, 'unique ids');
  const allow = rules.find((r) => r.action.type === 'allow');
  assert.ok(allow.id >= ALLOW_ID_OFFSET);
  assert.ok(rules.filter((r) => r.action.type === 'block').every((r) => r.id < ALLOW_ID_OFFSET));

  assert.deepEqual(selectorsForHost(cosmetic, 'example.org').sort(), ['.ad-banner', '.not-on-other']);
  assert.deepEqual(selectorsForHost(cosmetic, 'www.site.com').sort(), ['.not-on-other', '.site-ad']);
  assert.deepEqual(selectorsForHost(cosmetic, 'other.com'), ['.ad-banner']);
  assert.deepEqual(selectorsForHost(cosmetic, 'nogeneric.com'), []);
  assert.ok(selectorsForHost(cosmetic, 'www.google.de').includes('.g-ad'));
  assert.ok(selectorsForHost(cosmetic, 'www.google.co.uk').includes('.g-ad'));
});

test('generated rulesets are valid DNR', async () => {
  const { readFile } = await import('node:fs/promises');
  const { LISTS } = await import('../extension/lib/lists.js');
  const types = new Set(['main_frame', 'sub_frame', 'stylesheet', 'script', 'image', 'font', 'object',
    'xmlhttprequest', 'ping', 'csp_report', 'media', 'websocket', 'webtransport', 'webbundle', 'other']);
  for (const list of LISTS) {
    const rules = JSON.parse(await readFile(new URL(`../extension/rules/${list.id}.json`, import.meta.url), 'utf8'));
    const ids = new Set();
    for (const r of rules) {
      assert.ok(Number.isInteger(r.id) && r.id > 0 && !ids.has(r.id), `id ${r.id}`);
      ids.add(r.id);
      const c = r.condition;
      if (c.urlFilter !== undefined) {
        assert.ok(c.urlFilter.length > 0 && /^[\x20-\x7e]+$/.test(c.urlFilter), c.urlFilter);
        assert.ok(!c.urlFilter.slice(2).includes('||'), c.urlFilter);
        assert.ok(!/^\|\|\*/.test(c.urlFilter), c.urlFilter);
      }
      for (const key of ['requestDomains', 'initiatorDomains', 'excludedInitiatorDomains', 'excludedRequestDomains']) {
        if (c[key]) {
          assert.ok(c[key].length > 0);
          for (const d of c[key]) assert.match(d, /^[a-z0-9._-]+$/);
        }
      }
      for (const t of [...(c.resourceTypes || []), ...(c.excludedResourceTypes || [])]) assert.ok(types.has(t), t);
      if (r.action.type === 'allowAllRequests') {
        assert.ok(c.resourceTypes.every((t) => t === 'main_frame' || t === 'sub_frame'));
      }
      if (c.resourceTypes && c.excludedResourceTypes) assert.fail('both resourceTypes and excludedResourceTypes');
    }
  }
});
