#!/usr/bin/env node
// Downloads the filter lists and converts them into
//   extension/rules/<id>.json     (declarativeNetRequest static rulesets)
//   extension/cosmetic/<id>.json  (element hiding data)
// Usage: node tools/build-rules.mjs [--offline]   (--offline uses cached lists)

import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseFilterList } from '../extension/lib/filter-parser.js';
import { LISTS } from '../extension/lib/lists.js';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const cacheDir = join(root, '.cache', 'lists');
const offline = process.argv.includes('--offline');

// Chrome guarantees 30,000 enabled static rules per extension (more come
// from a shared global pool). Keep the default-enabled lists below that.
const GUARANTEED_STATIC_RULES = 30000;

async function fetchList(list) {
  const cacheFile = join(cacheDir, `${list.id}.txt`);
  if (offline) return readFile(cacheFile, 'utf8');
  let lastError;
  for (const url of [list.url, ...(list.mirrors || [])]) {
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const text = await res.text();
      if (!/^\s*\[Adblock|^! Title:/m.test(text.slice(0, 2000))) throw new Error('not a filter list');
      await mkdir(cacheDir, { recursive: true });
      await writeFile(cacheFile, text);
      return text;
    } catch (err) {
      lastError = err;
      console.warn(`  ${url}: ${err.message}`);
    }
  }
  throw new Error(`Could not download ${list.id}: ${lastError?.message}`);
}

const summary = [];
let defaultEnabledRules = 0;
await mkdir(join(root, 'extension', 'rules'), { recursive: true });
await mkdir(join(root, 'extension', 'cosmetic'), { recursive: true });

for (const list of LISTS) {
  console.log(`> ${list.id}`);
  const text = await fetchList(list);
  const { rules, cosmetic, popup, stats } = parseFilterList(text);
  cosmetic.popup = popup;
  await writeFile(join(root, 'extension', 'rules', `${list.id}.json`), JSON.stringify(rules));
  await writeFile(join(root, 'extension', 'cosmetic', `${list.id}.json`), JSON.stringify(cosmetic));
  const specificCount = Object.values(cosmetic.specific).reduce((n, s) => n + s.length, 0);
  summary.push({
    list: list.id,
    filters: stats.lines,
    dnrRules: rules.length,
    genericCss: cosmetic.generic.length,
    siteCss: specificCount,
    popup: popup.length,
    skipped: stats.skipped,
  });
  if (list.defaultEnabled) defaultEnabledRules += rules.length;
}

console.table(summary);
console.log(`Static rules enabled by default: ${defaultEnabledRules}`);
if (defaultEnabledRules > GUARANTEED_STATIC_RULES) {
  console.warn(`WARNING: more than ${GUARANTEED_STATIC_RULES} default rules; relies on the global pool.`);
}
