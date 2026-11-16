// covers: VRMS spec 0026 AC-10. Run: node --test scripts/test/check-contract-routes.test.mjs
import { test, describe } from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { compare, readRouteIndex } from '../check-contract-routes.mjs';

const SCRIPT = fileURLToPath(new URL('../check-contract-routes.mjs', import.meta.url));

const CONTRACT = [
  '# Contract',
  '### 15. Something else',
  '| GET | `/auth/not-an-index-row` | none | 1 | yes |',
  '### 16. Route index',
  'Some prose that mentions | GET | but is not a row.',
  '',
  '| Method | Path | Security | Section | Reply schema |',
  '|---|---|---|---|---|',
  '| GET | `/auth/health` | none | 3 | |',
  '| GET | `/auth/directory/users/:id` | serviceToken | 8 | Yes |',
  '| POST | `/auth/token` | clientAssertion | 5 | yes |',
  '',
  '### 17. After the index',
  '| GET | `/auth/after` | none | 1 | yes |',
].join('\n');

function ok(schema = true) {
  return { content: { 'application/json': schema ? { schema: { type: 'object' } } : {} } };
}

describe('readRouteIndex', () => {
  test('reads method, path and the reply schema flag of each row', () => {
    const rows = readRouteIndex(CONTRACT);
    assert.equal(rows.length, 3);
    assert.deepEqual(rows[0], { method: 'GET', path: '/auth/health', replySchema: false });
    assert.deepEqual(rows[2], { method: 'POST', path: '/auth/token', replySchema: true });
  });

  test('turns :param into {param} so it matches the document', () => {
    const rows = readRouteIndex(CONTRACT);
    assert.equal(rows[1].path, '/auth/directory/users/{id}');
  });

  test('treats the word yes as a flag whatever its case', () => {
    assert.equal(readRouteIndex(CONTRACT)[1].replySchema, true);
  });

  test('ignores table rows before and after section 16', () => {
    const paths = readRouteIndex(CONTRACT).map((r) => r.path);
    assert.ok(!paths.includes('/auth/not-an-index-row'));
    assert.ok(!paths.includes('/auth/after'));
  });

  test('throws when the section is missing', () => {
    assert.throws(() => readRouteIndex('# nothing here'), /no "### 16. Route index" section/);
  });

  test('throws when the section has no route rows', () => {
    assert.throws(
      () => readRouteIndex('### 16. Route index\n\njust prose\n'),
      /has no route rows/,
    );
  });
});

describe('compare', () => {
  const rows = [
    { method: 'GET', path: '/auth/health', replySchema: false },
    { method: 'POST', path: '/auth/token', replySchema: true },
  ];

  test('passes when every row is documented and the yes rows have a schema', () => {
    const doc = {
      paths: {
        '/auth/health': { get: { responses: { 200: ok(false) } } },
        '/auth/token': { post: { responses: { 200: ok() } } },
      },
    };
    assert.deepEqual(compare(rows, doc), { missing: [], noSchema: [], unlisted: [] });
  });

  test('names a row whose method and path are not in the document', () => {
    const doc = { paths: { '/auth/token': { post: { responses: { 200: ok() } } } } };
    assert.deepEqual(compare(rows, doc).missing, ['GET /auth/health']);
  });

  test('a path documented under another method counts as missing', () => {
    const doc = {
      paths: {
        '/auth/health': { post: { responses: { 200: ok(false) } } },
        '/auth/token': { post: { responses: { 200: ok() } } },
      },
    };
    assert.deepEqual(compare(rows, doc).missing, ['GET /auth/health']);
  });

  test('names a yes row whose 200 reply has no schema', () => {
    const doc = {
      paths: {
        '/auth/health': { get: { responses: { 200: ok(false) } } },
        '/auth/token': { post: { responses: { 200: ok(false) } } },
      },
    };
    assert.deepEqual(compare(rows, doc).noSchema, ['POST /auth/token']);
  });

  test('a 201 reply schema is enough', () => {
    const doc = {
      paths: {
        '/auth/health': { get: { responses: { 200: ok(false) } } },
        '/auth/token': { post: { responses: { 201: ok() } } },
      },
    };
    assert.deepEqual(compare(rows, doc).noSchema, []);
  });

  test('a yes row with no responses at all has no schema', () => {
    const doc = {
      paths: {
        '/auth/health': { get: {} },
        '/auth/token': { post: {} },
      },
    };
    assert.deepEqual(compare(rows, doc).noSchema, ['POST /auth/token']);
  });

  test('a no row is not held to a schema', () => {
    const doc = {
      paths: {
        '/auth/health': { get: { responses: { 200: ok(false) } } },
        '/auth/token': { post: { responses: { 200: ok() } } },
      },
    };
    assert.deepEqual(compare(rows, doc).noSchema, []);
  });

  test('lists documented /auth routes with no row as unlisted, and only those', () => {
    const doc = {
      paths: {
        '/auth/health': { get: { responses: { 200: ok(false) } } },
        '/auth/token': { post: { responses: { 200: ok() } } },
        '/auth/extra': { get: {}, parameters: [] },
        '/vrms/other': { get: {} },
      },
    };
    assert.deepEqual(compare(rows, doc).unlisted, ['GET /auth/extra']);
  });

  test('an empty document reports every row missing without throwing', () => {
    assert.deepEqual(compare(rows, {}).missing, ['GET /auth/health', 'POST /auth/token']);
  });
});

describe('command line', () => {
  function run(doc, args) {
    const dir = mkdtempSync(join(tmpdir(), 'contract-routes-'));
    try {
      const file = join(dir, 'openapi.json');
      writeFileSync(file, typeof doc === 'string' ? doc : JSON.stringify(doc));
      return spawnSync(process.execPath, [SCRIPT, ...(args ?? [file])], { encoding: 'utf8' });
    } finally {
      rmSync(dir, { recursive: true, force: true });
    }
  }

  test('exits 1 with a usage line when no file is given', () => {
    const result = run({}, []);
    assert.equal(result.status, 1);
    assert.match(result.stderr, /usage:/);
  });

  test('exits 1 and names the missing rows against the real contract', () => {
    const result = run({ paths: {} });
    assert.equal(result.status, 1);
    assert.match(result.stderr, /missing: GET \/auth\/health/);
    assert.match(result.stderr, /\d+ missing, 0 without a reply schema/);
  });

  test('exits 1 with a message when the file is not JSON', () => {
    const result = run('not json');
    assert.equal(result.status, 1);
    assert.match(result.stderr, /check-contract-routes:/);
  });
});
