#!/usr/bin/env node
// Builds installable packages:
//   dist/schild-chrome.zip   (Chrome, Edge, Brave, Opera, Vivaldi)
//   dist/schild-firefox.zip  (Firefox 128+, also as .xpi)
import { cp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const src = join(root, 'extension');
const dist = join(root, 'dist');

await rm(dist, { recursive: true, force: true });
await mkdir(dist, { recursive: true });

const manifest = JSON.parse(await readFile(join(src, 'manifest.json'), 'utf8'));

async function build(name, transform) {
  const dir = join(dist, name);
  await cp(src, dir, { recursive: true, filter: (p) => !p.includes('_metadata') });
  await writeFile(join(dir, 'manifest.json'), `${JSON.stringify(transform(structuredClone(manifest)), null, 2)}\n`);
  const zip = join(dist, `schild-${name}.zip`);
  execFileSync('zip', ['-r', '-q', '-X', zip, '.'], { cwd: dir });
  console.log(`  ${zip}`);
}

await build('chrome', (m) => m);
await build('firefox', (m) => {
  delete m.minimum_chrome_version;
  m.background = { scripts: ['background.js'], type: 'module' };
  m.browser_specific_settings = {
    gecko: {
      id: 'schild-adblocker@example.org',
      strict_min_version: '128.0',
      data_collection_permissions: { required: ['none'] },
    },
  };
  return m;
});
await cp(join(dist, 'schild-firefox.zip'), join(dist, 'schild-firefox.xpi'));
console.log('Fertig.');
