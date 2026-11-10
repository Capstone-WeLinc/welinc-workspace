// covers: spec 0010 AC-12. Run: node --test scripts/test/sync-env.test.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { syncEnv } from '../sync-env.mjs';

const SCRIPT = fileURLToPath(new URL('../sync-env.mjs', import.meta.url));

function fixture(env, example) {
  const dir = mkdtempSync(join(tmpdir(), 'sync-env-'));
  if (env !== null) writeFileSync(join(dir, '.env'), env);
  writeFileSync(join(dir, '.env.example'), example);
  return dir;
}

const EXAMPLE = [
  '# Server',
  'PORT=3001',
  'PORTAL_URL=http://localhost:8000',
  '# A commented example name is optional',
  '# SEED_ALLOW=',
  'CORS_ORIGINS=http://localhost:8000,http://localhost:8001',
  'SECRET_KEY=',
  '',
].join('\n');

test('appends each missing name with the example value and leaves other lines byte for byte', () => {
  const before = 'PORT=4000\n# my note\nSECRET_KEY=SENTINEL-1\n';
  const dir = fixture(before, EXAMPLE);
  try {
    assert.deepEqual(syncEnv(dir, '2026-11-11'), ['PORTAL_URL', 'CORS_ORIGINS']);
    const after = readFileSync(join(dir, '.env'), 'utf8');
    assert.ok(after.startsWith(before));
    assert.equal(
      after.slice(before.length),
      '# Added by sync-env on 2026-11-11\nPORTAL_URL=http://localhost:8000\nCORS_ORIGINS=http://localhost:8000,http://localhost:8001\n',
    );
  } finally {
    rmSync(dir, { recursive: true });
  }
});

test('changes nothing when nothing is missing, and counts a commented name as present', () => {
  const before = 'PORT=1\nPORTAL_URL=x\n# CORS_ORIGINS=off\nSECRET_KEY=\n';
  const dir = fixture(before, EXAMPLE);
  try {
    assert.deepEqual(syncEnv(dir), []);
    assert.equal(readFileSync(join(dir, '.env'), 'utf8'), before);
  } finally {
    rmSync(dir, { recursive: true });
  }
});

test('keeps Windows line endings and a missing final newline intact', () => {
  const before = 'PORT=1\r\nPORTAL_URL=x\r\nSECRET_KEY=s';
  const dir = fixture(before, EXAMPLE);
  try {
    syncEnv(dir, '2026-11-11');
    assert.equal(
      readFileSync(join(dir, '.env'), 'utf8'),
      `${before}\r\n# Added by sync-env on 2026-11-11\r\nCORS_ORIGINS=http://localhost:8000,http://localhost:8001\r\n`,
    );
  } finally {
    rmSync(dir, { recursive: true });
  }
});

test('skips a folder with no .env (setup makes it from the example first)', () => {
  const dir = fixture(null, EXAMPLE);
  try {
    assert.deepEqual(syncEnv(dir), []);
  } finally {
    rmSync(dir, { recursive: true });
  }
});

test('the command prints names only, never values', () => {
  const dir = fixture('PORT=1\nSECRET_KEY=SENTINEL-2\n', EXAMPLE.replace('SECRET_KEY=', 'SECRET_KEY=SENTINEL-3'));
  try {
    const out = execFileSync(process.execPath, [SCRIPT, dir], { encoding: 'utf8' });
    assert.match(out, /^added sync-env-\w+: PORTAL_URL, CORS_ORIGINS\n$/);
    assert.doesNotMatch(out, /SENTINEL|localhost/);
  } finally {
    rmSync(dir, { recursive: true });
  }
});
