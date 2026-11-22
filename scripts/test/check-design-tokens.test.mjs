// covers: suite spec 0016 AC-2. Run: node --test scripts/test/check-design-tokens.test.mjs
// check-design-tokens.mjs runs when it is loaded, so each case runs it as a command on small files.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const SCRIPT = fileURLToPath(new URL('../check-design-tokens.mjs', import.meta.url));

const TABLE = [
  '# Design',
  '',
  '## Color tokens',
  '',
  'Intro line.',
  '',
  '| Token | Value | Use |',
  '|---|---|---|',
  '| `primary` | `#1a1f6e` | Buttons |',
  '| `sidebar-idle` | `rgba(255,255,255,0.72)` | Idle pages |',
  '',
  '## Typography',
  '',
  '| Utility | Size |',
  '|---|---|',
  '| `text-body` | `14px` |',
  '',
].join('\n');

const GOOD_CSS = `
@theme inline { --color-primary: var(--primary); }
:root {
  --primary: #1A1F6E;
  --sidebar-idle: rgba(255, 255, 255, 0.72);
  --status-pending: #92400e; /* system token, not in the table */
}`;

function run({ design = TABLE, css = [GOOD_CSS] } = {}) {
  const dir = mkdtempSync(join(tmpdir(), 'check-design-tokens-'));
  try {
    const designFile = join(dir, 'design.md');
    writeFileSync(designFile, design);
    const cssFiles = css.map((content, i) => {
      const file = join(dir, `app${i}.css`);
      if (content !== null) writeFileSync(file, content);
      return file;
    });
    const r = spawnSync(process.execPath, [SCRIPT, designFile, ...cssFiles], { encoding: 'utf8' });
    return { code: r.status, out: r.stdout + r.stderr };
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

test('passes when every token matches, ignoring case, spaces and extra system tokens', () => {
  const r = run({ css: [GOOD_CSS, GOOD_CSS] });
  assert.equal(r.code, 0, r.out);
  assert.match(r.out, /2 tokens match in 2 file/);
});

test('reads only the color token table, not later tables', () => {
  const r = run();
  assert.equal(r.code, 0, r.out);
  assert.doesNotMatch(r.out, /text-body/);
});

test('fails and names the token, the file and both values when a value differs', () => {
  const r = run({ css: [GOOD_CSS.replace('#1A1F6E', '#123456')] });
  assert.equal(r.code, 1);
  assert.match(r.out, /app0\.css: --primary is #123456, design\.md has #1a1f6e/);
});

test('fails when a token is missing from an app', () => {
  const r = run({ css: [':root { --primary: #1a1f6e; }'] });
  assert.equal(r.code, 1);
  assert.match(r.out, /--sidebar-idle is missing/);
});

test('fails when an app defines a token twice, even across two :root blocks', () => {
  const r = run({ css: [`${GOOD_CSS}\n:root { --primary: #1a1f6e; }`] });
  assert.equal(r.code, 1);
  assert.match(r.out, /--primary is defined 2 times/);
});

test('ignores definitions outside :root and inside comments', () => {
  const css = `${GOOD_CSS}\n.dark { --primary: #000; }\n/* :root { --primary: #000; } */`;
  const r = run({ css: [css] });
  assert.equal(r.code, 0, r.out);
});

test('does not confuse a token with a longer name that starts the same', () => {
  const css = ':root { --primary-foreground: #fff; --sidebar-idle: rgba(255,255,255,0.72); }';
  const r = run({ css: [css] });
  assert.equal(r.code, 1);
  assert.match(r.out, /--primary is missing/);
});

test('fails when a table row does not parse', () => {
  const design = TABLE.replace('| `primary` | `#1a1f6e` |', '| primary | #1a1f6e |');
  const r = run({ design });
  assert.equal(r.code, 1);
  assert.match(r.out, /row doesn't parse/);
});

test('fails when design.md has no color token section', () => {
  const r = run({ design: '# Design\n\nNothing here.\n' });
  assert.equal(r.code, 1);
  assert.match(r.out, /no "## Color tokens" section/);
});

test('fails when an app file is missing', () => {
  const r = run({ css: [GOOD_CSS, null] });
  assert.equal(r.code, 1);
  assert.match(r.out, /app1\.css: file not found/);
});
