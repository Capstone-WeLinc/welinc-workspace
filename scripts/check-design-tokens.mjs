#!/usr/bin/env node
// Suite spec 0016 AC-2: every token in the color token table of design.md is defined once, with the
// same value, in :root of each app's src/index.css. Reads only that table (token in column 1,
// value in column 2, both in backticks). Values compare in lower case with spaces removed.
// Tokens an app defines that are not in the table are allowed (system tokens). Exit 0 passes.
//
//   node scripts/check-design-tokens.mjs [design.md] [app.css ...]
//
// With no arguments it checks design.md against welinc-web-portal and welinc-web-vrms.

import { existsSync, readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const [designArg, ...cssArgs] = process.argv.slice(2);
const designFile = designArg ?? path.join(root, 'design.md');
const cssFiles = cssArgs.length
  ? cssArgs
  : ['welinc-web-portal', 'welinc-web-vrms'].map((repo) => path.join(root, repo, 'src', 'index.css'));

const normalize = (v) => v.toLowerCase().replace(/\s+/g, '');
const rel = (f) => path.relative(process.cwd(), f) || f;
const problems = [];

// The rows of the table under "## Color tokens", up to the first line that isn't a table row.
function readTable(file) {
  const lines = readFileSync(file, 'utf8').split(/\r?\n/);
  const start = lines.findIndex((l) => /^##\s+Color tokens\s*$/.test(l));
  if (start < 0) {
    problems.push(`${rel(file)}: no "## Color tokens" section`);
    return [];
  }
  let i = start + 1;
  while (i < lines.length && !lines[i].startsWith('|')) {
    if (lines[i].startsWith('## ')) break;
    i += 1;
  }
  const rows = [];
  // Skip the header row and the |---| line
  for (i += 2; i < lines.length && lines[i].startsWith('|'); i += 1) {
    const cells = lines[i].split('|').slice(1, -1).map((c) => c.trim());
    const token = cells[0]?.match(/^`([a-z0-9-]+)`$/)?.[1];
    const value = cells[1]?.match(/^`([^`]+)`$/)?.[1];
    if (!token || !value) {
      problems.push(`${rel(file)} line ${i + 1}: row doesn't parse (want \`token\` | \`value\`): ${lines[i]}`);
      continue;
    }
    rows.push({ token, value });
  }
  if (!rows.length && !problems.length) problems.push(`${rel(file)}: the color token table has no rows`);
  return rows;
}

// The bodies of every top level :root { ... } block, with comments removed.
function rootBlocks(css) {
  const text = css.replace(/\/\*[\s\S]*?\*\//g, '');
  const blocks = [];
  const re = /(^|[}\s;])(:root)\s*\{/g;
  let m;
  while ((m = re.exec(text))) {
    let depth = 1;
    let j = re.lastIndex;
    const from = j;
    while (j < text.length && depth > 0) {
      if (text[j] === '{') depth += 1;
      else if (text[j] === '}') depth -= 1;
      j += 1;
    }
    blocks.push(text.slice(from, j - 1));
    re.lastIndex = j;
  }
  return blocks;
}

const table = readTable(designFile);
const seen = new Set();
for (const { token } of table) {
  if (seen.has(token)) problems.push(`${rel(designFile)}: token ${token} is in the table twice`);
  seen.add(token);
}

for (const cssFile of cssFiles) {
  if (!existsSync(cssFile)) {
    problems.push(`${rel(cssFile)}: file not found`);
    continue;
  }
  const body = rootBlocks(readFileSync(cssFile, 'utf8')).join('\n');
  for (const { token, value } of table) {
    const defs = [...body.matchAll(new RegExp(`(?:^|[\\s;{])--${token}\\s*:\\s*([^;]+);`, 'g'))].map((x) => x[1].trim());
    if (defs.length === 0) problems.push(`${rel(cssFile)}: --${token} is missing (design.md has ${value})`);
    else if (defs.length > 1) problems.push(`${rel(cssFile)}: --${token} is defined ${defs.length} times (${defs.join(', ')})`);
    else if (normalize(defs[0]) !== normalize(value))
      problems.push(`${rel(cssFile)}: --${token} is ${defs[0]}, design.md has ${value}`);
  }
}

if (problems.length) {
  for (const p of problems) console.error(`✗ ${p}`);
  console.error(`\n${problems.length} problem(s). Fix the app's src/index.css or the design.md table.`);
  process.exit(1);
}
console.log(`✓ ${table.length} tokens match in ${cssFiles.length} file(s)`);
