#!/usr/bin/env node
// Checks welinc-auth's generated OpenAPI document against contract 0001 section 16, the route index
// (VRMS spec 0026, AC-10). Usage: node scripts/check-contract-routes.mjs <path to openapi.json>
//
// Fails (exit 1) and names:
//   - every index row whose method and path the document doesn't have
//   - every row marked `yes` under Reply schema whose operation has no 200 or 201 reply schema
// Prints, without failing, every documented /auth/* route that has no index row.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const CONTRACT = fileURLToPath(
  new URL('../docs/specs/_root/0001-shared-services-contract/index.md', import.meta.url),
);
const METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'];

/** Reads the section 16 table: [{ method, path, replySchema }], path written as `{param}`. */
export function readRouteIndex(markdown) {
  const start = markdown.indexOf('### 16. Route index');
  if (start === -1) throw new Error('contract 0001 has no "### 16. Route index" section');
  const rest = markdown.slice(start + 1);
  const end = rest.search(/\n##+ /);
  const section = end === -1 ? rest : rest.slice(0, end);

  const rows = [];
  for (const line of section.split('\n')) {
    const cells = line.split('|').map((c) => c.trim());
    // a table row splits into ['', method, path, security, section, reply schema, '']
    if (cells.length < 7 || !METHODS.includes(cells[1])) continue;
    const path = cells[2].replace(/`/g, '').replace(/:(\w+)/g, '{$1}');
    rows.push({ method: cells[1], path, replySchema: cells[5].toLowerCase() === 'yes' });
  }
  if (rows.length === 0) throw new Error('contract 0001 section 16 has no route rows');
  return rows;
}

function hasReplySchema(operation) {
  for (const status of ['200', '201']) {
    const content = operation?.responses?.[status]?.content;
    if (content && Object.values(content).some((media) => media?.schema)) return true;
  }
  return false;
}

/** Compares the index with the document: { missing, noSchema, unlisted }, each a list of "METHOD path". */
export function compare(rows, doc) {
  const documented = new Map();
  for (const [path, item] of Object.entries(doc.paths ?? {})) {
    for (const [method, operation] of Object.entries(item ?? {})) {
      if (METHODS.includes(method.toUpperCase())) {
        documented.set(`${method.toUpperCase()} ${path}`, operation);
      }
    }
  }

  const listed = new Set();
  const missing = [];
  const noSchema = [];
  for (const row of rows) {
    const key = `${row.method} ${row.path}`;
    listed.add(key);
    const operation = documented.get(key);
    if (!operation) missing.push(key);
    else if (row.replySchema && !hasReplySchema(operation)) noSchema.push(key);
  }
  const unlisted = [...documented.keys()].filter(
    (key) => !listed.has(key) && key.split(' ')[1].startsWith('/auth/'),
  );
  return { missing, noSchema, unlisted };
}

function main(argv) {
  const file = argv[2];
  if (!file) {
    console.error('usage: node scripts/check-contract-routes.mjs <path to openapi.json>');
    return 1;
  }

  const rows = readRouteIndex(readFileSync(CONTRACT, 'utf8'));
  const doc = JSON.parse(readFileSync(file, 'utf8'));
  const { missing, noSchema, unlisted } = compare(rows, doc);

  for (const key of unlisted) {
    console.log(`note: ${key} is documented but has no row in contract 0001 section 16`);
  }
  for (const key of missing) {
    console.error(`missing: ${key} is in contract 0001 section 16 but not in ${file}`);
  }
  for (const key of noSchema) {
    console.error(`no reply schema: ${key} is marked yes under Reply schema but has no 200 or 201 schema`);
  }

  if (missing.length || noSchema.length) {
    console.error(
      `\n${missing.length} missing, ${noSchema.length} without a reply schema, out of ${rows.length} index rows`,
    );
    return 1;
  }
  console.log(`ok: all ${rows.length} rows of contract 0001 section 16 are documented`);
  return 0;
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  try {
    process.exitCode = main(process.argv);
  } catch (err) {
    console.error(`check-contract-routes: ${err.message}`);
    process.exitCode = 1;
  }
}
