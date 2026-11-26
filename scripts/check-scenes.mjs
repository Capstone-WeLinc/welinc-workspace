#!/usr/bin/env node
// VRMS spec 0028, AC-1 and AC-2: web-vrms and the portal hold the same scene kit, byte for byte.
// The kit is every .ts and .tsx file under src/components/brand/scenes/ (subfolders too) plus
// src/styles/scenes.css. Before comparing, CRLF becomes LF, a leading BOM goes and a missing final
// newline is ignored. A kit file may import only `react`, `@/lib/utils` and other kit files by a
// relative path, so a copy that compiles in one app compiles in the other. Exit 0 passes.
//
//   node scripts/check-scenes.mjs [vrms root] [portal root]
//
// With no arguments it compares welinc-web-vrms and welinc-web-portal beside this script's folder.

import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const [vrmsArg, portalArg] = process.argv.slice(2);
const apps = [
  { name: 'web-vrms', dir: path.resolve(vrmsArg ?? path.join(root, 'welinc-web-vrms')) },
  { name: 'portal', dir: path.resolve(portalArg ?? path.join(root, 'welinc-web-portal')) },
];

const SCENES = 'src/components/brand/scenes';
const CSS = 'src/styles/scenes.css';
const ALLOWED = new Set(['react', '@/lib/utils']);
const EXTENSIONS = ['', '.ts', '.tsx', '.js'];
const problems = [];

/** The kit's files of one app, as paths relative to the app root with forward slashes. */
function kitFiles(dir) {
  const files = [];
  const walk = (rel) => {
    const abs = path.join(dir, rel);
    if (!existsSync(abs)) return;
    for (const entry of readdirSync(abs)) {
      const child = `${rel}/${entry}`;
      if (statSync(path.join(dir, child)).isDirectory()) walk(child);
      else if (/\.tsx?$/.test(entry)) files.push(child);
    }
  };
  walk(SCENES);
  if (existsSync(path.join(dir, CSS))) files.push(CSS);
  return files.sort();
}

const normalize = (text) => text.replace(/^﻿/, '').replace(/\r\n/g, '\n').replace(/\n$/, '');

/** Every module a file imports, in every form: from, type, bare, export from, dynamic, CSS @import. */
function importsOf(file, text) {
  const found = [];
  const add = (re) => {
    for (const m of text.matchAll(re)) found.push(m[1]);
  };
  if (file.endsWith('.css')) {
    add(/@import\s+(?:url\(\s*)?['"]([^'"]+)['"]/g);
    return found;
  }
  add(/\bimport\s+(?:type\s+)?[^'"()]*?\bfrom\s*['"]([^'"]+)['"]/g);
  add(/\bimport\s*['"]([^'"]+)['"]/g);
  add(/\bexport\s+(?:type\s+)?[^'"()]*?\bfrom\s*['"]([^'"]+)['"]/g);
  add(/\bimport\s*\(\s*['"]([^'"]+)['"]\s*\)/g);
  return found;
}

/** A relative import is fine when it lands on a kit file, with or without its extension. */
function resolvesToKit(from, spec, kit) {
  const base = path.posix.normalize(path.posix.join(path.posix.dirname(from), spec));
  return EXTENSIONS.some((ext) => kit.has(base + ext));
}

const kits = apps.map((app) => {
  if (!existsSync(app.dir)) problems.push(`${app.name}: no folder at ${app.dir}`);
  const files = existsSync(app.dir) ? kitFiles(app.dir) : [];
  if (existsSync(app.dir) && files.length === 0) problems.push(`${app.name}: no scene kit under ${SCENES}`);
  return { ...app, files, set: new Set(files) };
});

// The import rule, checked in each app (the copies should match, but say where a stray one is)
for (const kit of kits) {
  for (const file of kit.files) {
    const text = readFileSync(path.join(kit.dir, file), 'utf8');
    for (const spec of importsOf(file, text)) {
      const relative = spec.startsWith('./') || spec.startsWith('../');
      if (relative ? resolvesToKit(file, spec, kit.set) : ALLOWED.has(spec)) continue;
      problems.push(`${kit.name}: ${file} imports '${spec}' (a kit file may import only react, @/lib/utils and other kit files)`);
    }
  }
}

// The two copies, file by file
const [a, b] = kits;
if (a.files.length && b.files.length) {
  for (const file of new Set([...a.files, ...b.files])) {
    if (!b.set.has(file)) {
      problems.push(`${file}: only in ${a.name}`);
      continue;
    }
    if (!a.set.has(file)) {
      problems.push(`${file}: only in ${b.name}`);
      continue;
    }
    const left = normalize(readFileSync(path.join(a.dir, file), 'utf8')).split('\n');
    const right = normalize(readFileSync(path.join(b.dir, file), 'utf8')).split('\n');
    const n = Math.max(left.length, right.length);
    for (let i = 0; i < n; i += 1) {
      if (left[i] !== right[i]) {
        problems.push(`${file}: differs from line ${i + 1}\n    ${a.name}: ${left[i] ?? '(end of file)'}\n    ${b.name}: ${right[i] ?? '(end of file)'}`);
        break;
      }
    }
  }
}

if (problems.length) {
  console.error(`Scene kit check failed (VRMS spec 0028):\n- ${problems.join('\n- ')}`);
  console.error('\nEdit the kit in both apps on the same day: copy the changed files across.');
  process.exit(1);
}
console.log(`Scene kit matches: ${a.files.length} files in ${a.name} and ${b.name}.`);
