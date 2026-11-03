#!/usr/bin/env node
// Turns on one group's AI setup (skills, MCP servers, settings, rules) for you only.
//
//   node scripts/use-agents.mjs vrms          install agents/vrms into the local, git ignored spots
//   node scripts/use-agents.mjs vrms --save   copy skill changes you made locally back into agents/vrms
//
// Each group keeps its setup in agents/<system>/. Nothing this script writes is committed
// (see .gitignore), so another group's AI never loads it. Run it again after a pull that
// changes agents/<system>/, then restart your AI tool.

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const at = (...p) => path.join(root, ...p);

const [system, flag] = process.argv.slice(2);
const systems = fs.existsSync(at('agents'))
  ? fs.readdirSync(at('agents')).filter((d) => fs.statSync(at('agents', d)).isDirectory())
  : [];

if (!system || !systems.includes(system)) {
  console.error(`Usage: node scripts/use-agents.mjs <system> [--save]\nSystems with a setup: ${systems.join(', ') || 'none yet'}`);
  process.exit(1);
}

const src = (...p) => at('agents', system, ...p);
const STATE = at('.claude', 'agents-installed.json');
const SKILL_DIRS = [at('.claude', 'skills')];
const ROOT_FILES = [
  ['mcp.json', '.mcp.json'],
  ['skills-lock.json', 'skills-lock.json'],
  ['test-preferences.json', 'test-preferences.json'],
];

const readJson = (file, fallback) => (fs.existsSync(file) ? JSON.parse(fs.readFileSync(file, 'utf8')) : fallback);
const writeJson = (file, data) => {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(data, null, 2) + '\n');
};
const copyDir = (from, to) => {
  fs.rmSync(to, { recursive: true, force: true });
  fs.mkdirSync(path.dirname(to), { recursive: true });
  fs.cpSync(from, to, { recursive: true, dereference: true });
};

if (flag === '--save') {
  // Never replace the committed skills with nothing.
  if (!fs.existsSync(SKILL_DIRS[0]) || fs.readdirSync(SKILL_DIRS[0]).length === 0) {
    console.error('Nothing to save: .claude/skills is missing or empty. Run the install first.');
    process.exit(1);
  }
  copyDir(SKILL_DIRS[0], src('skills'));
  for (const [inAgents, atRoot] of ROOT_FILES.slice(1)) {
    if (fs.existsSync(at(atRoot))) fs.copyFileSync(at(atRoot), src(inAgents));
  }
  console.log(`Saved .claude/skills, skills-lock.json and test-preferences.json into agents/${system}/. Commit them so your group gets them.`);
  process.exit(0);
}

// 1. Skills: replace the local skill folder with this group's skills.
for (const dir of SKILL_DIRS) {
  if (fs.existsSync(src('skills'))) copyDir(src('skills'), dir);
  else fs.rmSync(dir, { recursive: true, force: true });
}

// 2. Root files the tools and skills read (MCP servers, skills lock, test preferences).
for (const [inAgents, atRoot] of ROOT_FILES) {
  if (fs.existsSync(src(inAgents))) fs.copyFileSync(src(inAgents), at(atRoot));
  else fs.rmSync(at(atRoot), { force: true });
}

// 3. Settings: merge into .claude/settings.local.json, replacing what an earlier run added
//    and keeping anything you put there yourself.
const local = readJson(at('.claude', 'settings.local.json'), {});
const previous = readJson(STATE, { permissions: {}, lists: {}, objects: {}, scalars: [] });
const wanted = readJson(src('settings.json'), {});

local.permissions ??= {};
for (const [kind, entries] of Object.entries(previous.permissions)) {
  local.permissions[kind] = (local.permissions[kind] ?? []).filter((e) => !entries.includes(e));
}
for (const [key, entries] of Object.entries(previous.lists)) {
  if (Array.isArray(local[key])) local[key] = local[key].filter((e) => !entries.includes(e));
}
for (const [key, names] of Object.entries(previous.objects)) {
  if (local[key]) for (const n of names) delete local[key][n];
}
for (const key of previous.scalars) delete local[key];

const added = { permissions: {}, lists: {}, objects: {}, scalars: [] };
for (const [key, value] of Object.entries(wanted)) {
  if (key === 'permissions') {
    for (const [kind, entries] of Object.entries(value)) {
      const have = local.permissions[kind] ?? [];
      const fresh = entries.filter((e) => !have.includes(e));
      local.permissions[kind] = [...have, ...fresh];
      added.permissions[kind] = fresh;
    }
  } else if (Array.isArray(value)) {
    const have = Array.isArray(local[key]) ? local[key] : [];
    const fresh = value.filter((e) => !have.includes(e));
    local[key] = [...have, ...fresh];
    added.lists[key] = fresh;
  } else if (value && typeof value === 'object') {
    local[key] = { ...(local[key] ?? {}) };
    added.objects[key] = Object.keys(value).filter((n) => !(n in local[key]));
    Object.assign(local[key], value);
  } else if (!(key in local)) {
    local[key] = value;
    added.scalars.push(key);
  }
}
for (const kind of Object.keys(local.permissions)) {
  if (local.permissions[kind].length === 0) delete local.permissions[kind];
}
writeJson(at('.claude', 'settings.local.json'), local);
writeJson(STATE, { system, ...added });

// 4. Rules: CLAUDE.local.md imports this group's AGENTS.md, inside a block this script owns.
const START = '<!-- use-agents:start -->';
const END = '<!-- use-agents:end -->';
const block = fs.existsSync(src('AGENTS.md')) ? `${START}\n@agents/${system}/AGENTS.md\n${END}` : '';
const localMd = at('CLAUDE.local.md');
const current = fs.existsSync(localMd) ? fs.readFileSync(localMd, 'utf8') : '';
const pattern = new RegExp(`${START}[\\s\\S]*?${END}`);
const next = pattern.test(current) ? current.replace(pattern, block) : [block, current].filter(Boolean).join('\n\n');
if (next.trim()) fs.writeFileSync(localMd, next.trimEnd() + '\n');
else fs.rmSync(localMd, { force: true });

const parts = [];
if (fs.existsSync(src('skills'))) parts.push(`${fs.readdirSync(src('skills')).length} skills`);
if (fs.existsSync(src('mcp.json'))) parts.push('MCP servers');
if (fs.existsSync(src('settings.json'))) parts.push('settings');
if (fs.existsSync(src('AGENTS.md'))) parts.push(`agents/${system}/AGENTS.md`);
console.log(`Turned on the ${system.toUpperCase()} AI setup: ${parts.join(', ') || 'nothing to install yet'}.`);
console.log('Restart your AI tool so it picks them up. None of these files are committed.');
