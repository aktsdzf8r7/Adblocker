#!/usr/bin/env node
// Renders the shield icon as PNGs (no dependencies).
import { writeFileSync } from 'node:fs';
import { deflateSync } from 'node:zlib';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const out = join(dirname(fileURLToPath(import.meta.url)), '..', 'extension', 'icons');

function crc32(buf) {
  let c;
  let crc = 0xffffffff;
  for (const b of buf) {
    c = (crc ^ b) & 0xff;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    crc = (crc >>> 8) ^ c;
  }
  return (crc ^ 0xffffffff) >>> 0;
}

function chunk(type, data) {
  const len = Buffer.alloc(4);
  len.writeUInt32BE(data.length);
  const td = Buffer.concat([Buffer.from(type), data]);
  const crc = Buffer.alloc(4);
  crc.writeUInt32BE(crc32(td));
  return Buffer.concat([len, td, crc]);
}

function png(size, pixel) {
  const raw = Buffer.alloc(size * (size * 4 + 1));
  for (let y = 0; y < size; y++) {
    raw[y * (size * 4 + 1)] = 0;
    for (let x = 0; x < size; x++) {
      const [r, g, b, a] = pixel(x, y);
      const o = y * (size * 4 + 1) + 1 + x * 4;
      raw[o] = r; raw[o + 1] = g; raw[o + 2] = b; raw[o + 3] = a;
    }
  }
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(size, 0);
  ihdr.writeUInt32BE(size, 4);
  ihdr[8] = 8; ihdr[9] = 6; ihdr[10] = 0; ihdr[11] = 0; ihdr[12] = 0;
  return Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    chunk('IHDR', ihdr),
    chunk('IDAT', deflateSync(raw)),
    chunk('IEND', Buffer.alloc(0)),
  ]);
}

// Shape in unit coordinates (0..1).
function inShield(x, y) {
  const top = 0.08;
  const bottom = 0.94;
  const half = 0.4;
  if (y < top || y > bottom) return false;
  const dx = Math.abs(x - 0.5);
  if (y < 0.5) {
    // slight inward curve at the top corners
    const t = (y - top) / (0.5 - top);
    return dx <= half - 0.06 * (1 - t) ** 3;
  }
  const t = (y - 0.5) / (bottom - 0.5);
  return dx <= half * (1 - t ** 1.8) ** 0.9;
}

function inBar(x, y) {
  // white "blocked" bar
  const w = 0.44;
  const h = 0.13;
  const cx = 0.5;
  const cy = 0.47;
  const dx = Math.abs(x - cx) - (w / 2 - h / 2);
  const dy = Math.abs(y - cy);
  if (dx <= 0) return dy <= h / 2;
  return dx * dx + dy * dy <= (h / 2) ** 2;
}

for (const size of [16, 32, 48, 128]) {
  const ss = 4;
  const buf = png(size, (px, py) => {
    let shield = 0;
    let bar = 0;
    for (let i = 0; i < ss; i++) {
      for (let j = 0; j < ss; j++) {
        const x = (px + (i + 0.5) / ss) / size;
        const y = (py + (j + 0.5) / ss) / size;
        if (inShield(x, y)) {
          if (inBar(x, y)) bar++;
          else shield++;
        }
      }
    }
    const n = ss * ss;
    const a = (shield + bar) / n;
    if (!a) return [0, 0, 0, 0];
    // Mix red (#d93025, darker towards the bottom) and white
    const shade = 1 - 0.18 * (py / size);
    const red = [217 * shade, 48 * shade, 37 * shade];
    const wb = bar / (shield + bar);
    const c = red.map((v) => Math.round(v * (1 - wb) + 255 * wb));
    return [...c, Math.round(a * 255)];
  });
  writeFileSync(join(out, `icon${size}.png`), buf);
}
console.log('icons written to', out);
