#!/usr/bin/env node
// VRMS spec 0008 AC-23: every Container App and job name, with its environment ending, fits
// Azure's rule (2 to 32 characters, lowercase letters, digits and single dashes, starting with a
// letter). Reads the base names from infra/env.bicep (coreApps, coreJobs and every name in
// groupDefs), adds each ending, and fails on any name that breaks the rule. Exit 0 passes.
//
//   node scripts/check-names.mjs [path/to/env.bicep]

import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const file = process.argv[2] ?? path.join(root, 'infra', 'env.bicep');
const bicep = readFileSync(file, 'utf8');

const endings = ['-staging', '-prod'];
const MAX = 32;
const RULE = /^[a-z](?:[a-z0-9]|-(?!-))*[a-z0-9]$/;

function arrayVar(name) {
  const m = bicep.match(new RegExp(`^var ${name} = \\[([^\\]]*)\\]`, 'm'));
  if (!m) throw new Error(`var ${name} not found in ${file}`);
  return [...m[1].matchAll(/'([^']+)'/g)].map((x) => x[1]);
}

function groupNames() {
  const start = bicep.indexOf('var groupDefs = {');
  if (start < 0) throw new Error(`var groupDefs not found in ${file}`);
  // The block ends at the first line that is exactly "}"
  const end = bicep.indexOf('\n}\n', start);
  const block = bicep.slice(start, end);
  return [...block.matchAll(/\bname: '([^']+)'/g)].map((x) => x[1]);
}

const bases = [...new Set([...arrayVar('coreApps'), ...arrayVar('coreJobs'), ...groupNames()])];
if (bases.length < 7) throw new Error(`only ${bases.length} base names found; the parser is out of date with ${file}`);

let failed = 0;
let longest = '';
for (const base of bases) {
  for (const ending of endings) {
    const name = `${base}${ending}`;
    if (name.length > longest.length) longest = name;
    if (name.length > MAX || !RULE.test(name)) {
      failed++;
      console.error(`bad name: ${name} (${name.length} characters; Azure allows ${MAX}, lowercase letters, digits and single dashes)`);
    }
  }
}

if (failed) {
  console.error(`${failed} app or job name(s) break Azure's naming rule.`);
  process.exit(1);
}
console.log(`ok: ${bases.length * endings.length} app and job names; the longest is ${longest} (${longest.length} of ${MAX}).`);
