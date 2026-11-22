// covers: VRMS spec 0008 AC-23. Run: node --test scripts/test/check-names.test.mjs
// check-names.mjs runs when it is loaded, so each case runs it as a command on a small bicep file.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const SCRIPT = fileURLToPath(new URL('../check-names.mjs', import.meta.url));
const REAL_BICEP = fileURLToPath(new URL('../../infra/env.bicep', import.meta.url));

// A bicep file shaped like infra/env.bicep: two array variables and the groupDefs block.
// The defaults give seven different base names, the smallest set the script accepts.
function bicep({
  coreApps = ['api-gateway', 'auth-service', 'vrms-backend'],
  coreJobs = ['auth-migrate', 'vrms-migrate'],
  groups = ['bms-gateway', 'vmms-backend'],
} = {}) {
  const list = (names) => names.map((n) => `'${n}'`).join(', ');
  const apps = groups.map((n) => `      { name: '${n}' }`).join('\n');
  return [
    `var coreApps = [${list(coreApps)}]`,
    `var coreJobs = [${list(coreJobs)}]`,
    'var groupDefs = {',
    '  demo: {',
    '    apps: [',
    apps,
    '    ]',
    '  }',
    '}',
    '',
  ].join('\n');
}

function run(content) {
  const dir = mkdtempSync(join(tmpdir(), 'check-names-'));
  try {
    const file = join(dir, 'env.bicep');
    writeFileSync(file, content);
    const r = spawnSync(process.execPath, [SCRIPT, file], { encoding: 'utf8' });
    return { status: r.status, out: r.stdout, err: r.stderr };
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

test('passes on the real infra/env.bicep, so no live app or job name is over 32 characters', () => {
  const r = spawnSync(process.execPath, [SCRIPT, REAL_BICEP], { encoding: 'utf8' });
  assert.equal(r.status, 0, r.stderr);
  assert.match(r.stdout, /^ok: \d+ app and job names; the longest is \S+ \(\d+ of 32\)\./);
});

test('passes when every name fits, and counts each base name once per ending', () => {
  const r = run(bicep());
  assert.equal(r.status, 0, r.err);
  assert.match(r.out, /ok: 14 app and job names/);
});

test('counts a name used in both the apps and the groups only once', () => {
  // 3 apps + 2 jobs + 3 group names, one of them a repeat of api-gateway: 7 different bases, 14 names
  const r = run(bicep({ groups: ['api-gateway', 'vmms-backend', 'bms-gateway'] }));
  assert.equal(r.status, 0, r.err);
  assert.match(r.out, /ok: 14 app and job names/);
});

test('accepts a name that is exactly 32 characters with its ending', () => {
  const base = 'a'.repeat(24); // 24 + "-staging" (8) = 32
  const r = run(bicep({ coreApps: [base, 'auth-service', 'vrms-backend'] }));
  assert.equal(r.status, 0, r.err);
  assert.match(r.out, /\(32 of 32\)/);
});

test('fails on a name of 33 characters with its ending, and says which one', () => {
  const base = 'a'.repeat(25); // 25 + "-staging" = 33
  const r = run(bicep({ coreApps: [base, 'auth-service', 'vrms-backend'] }));
  assert.equal(r.status, 1);
  assert.match(r.err, new RegExp(`bad name: ${base}-staging \\(33 characters; Azure allows 32`));
  assert.match(r.err, /1 app or job name\(s\) break Azure's naming rule\./);
});

test('checks a base name against the -prod ending too', () => {
  // 25 + "-prod" (5) = 30 fits, 25 + "-staging" = 33 does not: only the staging name is reported
  const base = 'b'.repeat(25);
  const r = run(bicep({ coreJobs: [base, 'vrms-migrate'] }));
  assert.equal(r.status, 1);
  assert.match(r.err, /-staging \(33 characters/);
  assert.doesNotMatch(r.err, /-prod \(/);
});

test('fails on a name from the group definitions, not only the core lists', () => {
  const r = run(bicep({ groups: ['c'.repeat(30), 'vmms-backend'] }));
  assert.equal(r.status, 1);
  assert.match(r.err, /bad name: c{30}-staging/);
  assert.match(r.err, /bad name: c{30}-prod/);
  assert.match(r.err, /2 app or job name\(s\) break/);
});

test('fails on every bad name in one run, not just the first', () => {
  const r = run(bicep({ coreApps: ['x'.repeat(26), 'y'.repeat(27), 'vrms-backend'] }));
  assert.equal(r.status, 1);
  assert.match(r.err, /bad name: x{26}-staging/);
  assert.match(r.err, /bad name: y{27}-staging/);
});

for (const [why, name] of [
  ['an uppercase letter', 'Api-gateway'],
  ['a double dash', 'api--gateway'],
  ['a leading digit', '1api-gateway'],
  ['a trailing dash', 'api-gateway-'],
  ['an underscore', 'api_gateway'],
]) {
  test(`fails on a base name with ${why}`, () => {
    const r = run(bicep({ coreApps: [name, 'auth-service', 'vrms-backend'] }));
    assert.equal(r.status, 1);
    assert.match(r.err, /bad name:/);
  });
}

test('stops with a clear error when coreApps is missing, instead of passing', () => {
  const r = run(bicep().replace(/^var coreApps.*\n/m, ''));
  assert.notEqual(r.status, 0);
  assert.match(r.err, /var coreApps not found/);
});

test('stops with a clear error when groupDefs is missing, instead of passing', () => {
  const content = bicep().slice(0, bicep().indexOf('var groupDefs'));
  const r = run(content);
  assert.notEqual(r.status, 0);
  assert.match(r.err, /var groupDefs not found/);
});

test('refuses to pass when it finds fewer than 7 base names, a sign the parser is out of date', () => {
  const r = run(bicep({ coreApps: ['api-gateway'], coreJobs: ['auth-migrate'], groups: ['bms-gateway'] }));
  assert.notEqual(r.status, 0);
  assert.match(r.err, /only 3 base names found; the parser is out of date/);
});
