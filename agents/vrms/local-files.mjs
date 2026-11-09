#!/usr/bin/env node
// Moves the files git doesn't carry between your machines (VRMS group, personal use).
//
//   node agents/vrms/local-files.mjs pack            writes ~/welinc-local-YYYY-MM-DD.tar.gz
//   node agents/vrms/local-files.mjs unpack <file>   puts every file back on this machine
//
// What travels: CLAUDE.local.md, docs/_private/, docs/_source/, and Claude Code's memory for this
// workspace (~/.claude/projects/<workspace path>/memory/). Never a .env file: those hold signing
// keys and the team SMTP password, so make them on each machine (npm run keys:dev in welinc-auth).
// Not needed either: what `node scripts/use-agents.mjs vrms` writes (skills, .mcp.json, settings,
// test-preferences.json). Run that script after unpacking.
//
// Move the archive by USB, AirDrop or a private drive folder, then delete it: it holds your notes.

import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const ITEMS = ['CLAUDE.local.md', 'docs/_private', 'docs/_source'];
const MEMORY = 'claude-memory';

/** Claude Code names a project folder after its path, every other character turned into `-`. */
const projectsDir = path.join(os.homedir(), '.claude', 'projects');
const slug = root.replace(/[^a-zA-Z0-9]/g, '-');

function memoryDir() {
  const exact = path.join(projectsDir, slug, 'memory');
  if (fs.existsSync(path.dirname(exact))) return exact;
  // Fall back to the one project folder for a workspace of this name, if there is exactly one
  const name = path.basename(root).replace(/[^a-zA-Z0-9]/g, '-');
  const matches = fs.existsSync(projectsDir)
    ? fs.readdirSync(projectsDir).filter((d) => d.endsWith(`-${name}`))
    : [];
  return matches.length === 1 ? path.join(projectsDir, matches[0], 'memory') : exact;
}

function tar(args) {
  const run = spawnSync('tar', args, { stdio: 'inherit' });
  if (run.status !== 0) {
    console.error('tar failed. It ships with macOS and with Windows 10 or later.');
    process.exit(1);
  }
}

function copyTree(from, to, backups) {
  for (const entry of fs.readdirSync(from, { withFileTypes: true })) {
    const src = path.join(from, entry.name);
    const dest = path.join(to, entry.name);
    if (entry.isDirectory()) {
      copyTree(src, dest, backups);
      continue;
    }
    if (/^\.env/.test(entry.name) || entry.name === '.DS_Store' || entry.name === 'Thumbs.db') continue;
    fs.mkdirSync(to, { recursive: true });
    if (fs.existsSync(dest) && !fs.readFileSync(dest).equals(fs.readFileSync(src))) {
      fs.copyFileSync(dest, `${dest}.bak`);
      backups.push(dest);
    }
    fs.copyFileSync(src, dest);
  }
}

function pack() {
  const stage = fs.mkdtempSync(path.join(os.tmpdir(), 'welinc-local-'));
  const packed = [];
  for (const item of ITEMS) {
    const src = path.join(root, item);
    if (!fs.existsSync(src)) continue;
    if (fs.statSync(src).isDirectory()) copyTree(src, path.join(stage, item), []);
    else {
      fs.mkdirSync(path.dirname(path.join(stage, item)), { recursive: true });
      fs.copyFileSync(src, path.join(stage, item));
    }
    packed.push(item);
  }
  const memory = memoryDir();
  if (fs.existsSync(memory)) {
    copyTree(memory, path.join(stage, MEMORY), []);
    packed.push(`Claude memory (${fs.readdirSync(memory).length} files)`);
  }
  const now = new Date();
  const day = [now.getFullYear(), now.getMonth() + 1, now.getDate()]
    .map((n) => String(n).padStart(2, '0'))
    .join('-');
  const out = path.join(os.homedir(), `welinc-local-${day}.tar.gz`);
  tar(['-czf', out, '-C', stage, '.']);
  fs.rmSync(stage, { recursive: true, force: true });
  console.log(`Packed: ${packed.join(', ')}\n-> ${out}\nNo .env files were included.`);
}

function unpack(file) {
  if (!file || !fs.existsSync(file)) {
    console.error('Usage: node agents/vrms/local-files.mjs unpack <welinc-local-....tar.gz>');
    process.exit(1);
  }
  const stage = fs.mkdtempSync(path.join(os.tmpdir(), 'welinc-local-'));
  tar(['-xzf', path.resolve(file), '-C', stage]);
  const backups = [];
  for (const item of ITEMS) {
    const src = path.join(stage, item);
    if (!fs.existsSync(src)) continue;
    if (fs.statSync(src).isDirectory()) copyTree(src, path.join(root, item), backups);
    else copyTree(path.dirname(src), path.dirname(path.join(root, item)), backups);
  }
  const memory = memoryDir();
  if (fs.existsSync(path.join(stage, MEMORY))) copyTree(path.join(stage, MEMORY), memory, backups);
  fs.rmSync(stage, { recursive: true, force: true });
  console.log(`Unpacked into ${root}\nClaude memory -> ${memory}`);
  if (backups.length) console.log(`Kept your old version as .bak for:\n  ${backups.join('\n  ')}`);
  console.log('Next: node scripts/use-agents.mjs vrms, and make the .env files on this machine if they are missing.');
}

const [command, file] = process.argv.slice(2);
if (command === 'pack') pack();
else if (command === 'unpack') unpack(file);
else {
  console.error('Usage: node agents/vrms/local-files.mjs pack | unpack <file>');
  process.exit(1);
}
