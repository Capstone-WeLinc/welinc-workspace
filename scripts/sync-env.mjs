#!/usr/bin/env node
// Tops up an existing .env with the names its .env.example gained since it was made (spec 0010,
// AC-12). For every repo holding both files, each name set in .env.example but absent from .env is
// appended with the example's value, under one dated comment. It never edits or removes a line,
// and it prints names only, never values.
//
// Usage (from the workspace root; scripts/setup.sh runs it for you):
//   node scripts/sync-env.mjs              every welinc-* repo in the workspace
//   node scripts/sync-env.mjs <dir> ...    only these folders
import { existsSync, readdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

/** `NAME=` or `# NAME=` (a commented name counts as present in .env: someone turned it off). */
const NAME = /^#?\s*([A-Z][A-Z0-9_]*)=/;
/** Only live example lines are copied; a commented example name is optional by design. */
const LIVE = /^([A-Z][A-Z0-9_]*)=(.*)$/;

/**
 * Appends the missing names to `<dir>/.env` and returns them (empty when nothing was missing or
 * either file is absent). `today` is injectable for tests.
 */
export function syncEnv(dir, today = new Date().toISOString().slice(0, 10)) {
  const envPath = join(dir, '.env');
  const examplePath = join(dir, '.env.example');
  if (!existsSync(envPath) || !existsSync(examplePath)) return [];

  const env = readFileSync(envPath, 'utf8');
  const present = new Set(
    env.split(/\r?\n/).map((line) => NAME.exec(line)?.[1]).filter(Boolean),
  );

  const missing = [];
  for (const line of readFileSync(examplePath, 'utf8').split(/\r?\n/)) {
    const match = LIVE.exec(line);
    if (match && !present.has(match[1])) {
      missing.push(line);
      present.add(match[1]);
    }
  }
  if (!missing.length) return [];

  const eol = env.includes('\r\n') ? '\r\n' : '\n';
  const lead = env === '' || env.endsWith('\n') ? '' : eol;
  const block = [`# Added by sync-env on ${today}`, ...missing].join(eol);
  writeFileSync(envPath, `${env}${lead}${block}${eol}`);
  return missing.map((line) => LIVE.exec(line)[1]);
}

function main(args) {
  const root = resolve(fileURLToPath(import.meta.url), '..', '..');
  const dirs = args.length
    ? args
    : readdirSync(root, { withFileTypes: true })
        .filter((entry) => entry.isDirectory() && entry.name.startsWith('welinc-'))
        .map((entry) => join(root, entry.name));

  let any = false;
  for (const dir of dirs) {
    const added = syncEnv(dir);
    if (added.length) {
      any = true;
      console.log(`added ${dir.split(/[\\/]/).pop()}: ${added.join(', ')}`);
    }
  }
  if (!any) console.log('ok    every .env has the names its .env.example lists');
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main(process.argv.slice(2));
}
