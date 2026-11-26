// covers: VRMS spec 0028 AC-1, AC-2. Run: node --test scripts/test/check-scenes.test.mjs
// check-scenes.mjs runs when it is loaded, so each case runs it as a command on two small apps.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const SCRIPT = fileURLToPath(new URL('../check-scenes.mjs', import.meta.url));

const KIT = {
  'src/components/brand/scenes/SceneSvg.tsx': "import type { ReactNode } from 'react';\nexport function SceneSvg() {\n  return null;\n}\n",
  'src/components/brand/scenes/CrashScene.tsx': "import { useId } from 'react';\nimport { SceneSvg } from './SceneSvg';\nimport { cn } from '@/lib/utils';\nexport const x = 1;\n",
  'src/components/brand/scenes/parts/Wheel.tsx': "import { SceneSvg } from '../SceneSvg';\nexport const w = 1;\n",
  'src/styles/scenes.css': ':root {\n  --scene-road: #0a0d36;\n}\n',
};

/** Writes two apps (each a map of path to text, null to leave a file out) and runs the check. */
function run(vrms = KIT, portal = KIT) {
  const dir = mkdtempSync(join(tmpdir(), 'check-scenes-'));
  try {
    const write = (app, files) => {
      for (const [file, text] of Object.entries(files)) {
        if (text === null) continue;
        const abs = join(dir, app, file);
        mkdirSync(dirname(abs), { recursive: true });
        writeFileSync(abs, text);
      }
    };
    write('vrms', vrms);
    write('portal', portal);
    const r = spawnSync(process.execPath, [SCRIPT, join(dir, 'vrms'), join(dir, 'portal')], { encoding: 'utf8' });
    return { code: r.status, out: r.stdout + r.stderr };
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

const withFile = (file, text) => ({ ...KIT, [file]: text });

test('passes when both kits match', () => {
  const r = run();
  assert.equal(r.code, 0, r.out);
  assert.match(r.out, /4 files/);
});

test('fails on a file in only one app, naming it', () => {
  const r = run(KIT, withFile('src/components/brand/scenes/CrashScene.tsx', null));
  assert.equal(r.code, 1, r.out);
  assert.match(r.out, /CrashScene\.tsx: only in web-vrms/);
});

test('fails on a missing scenes.css', () => {
  const r = run(withFile('src/styles/scenes.css', null), KIT);
  assert.equal(r.code, 1, r.out);
  assert.match(r.out, /scenes\.css: only in portal/);
});

test('fails on a changed byte, naming the first differing line', () => {
  const r = run(KIT, withFile('src/styles/scenes.css', ':root {\n  --scene-road: #0a0d37;\n}\n'));
  assert.equal(r.code, 1, r.out);
  assert.match(r.out, /scenes\.css: differs from line 2/);
  assert.match(r.out, /#0a0d37/);
});

test('passes when only line endings, a BOM or the final newline differ', () => {
  const crlf = Object.fromEntries(Object.entries(KIT).map(([f, t]) => [f, t.replace(/\n/g, '\r\n')]));
  assert.equal(run(KIT, crlf).code, 0);
  const bom = Object.fromEntries(Object.entries(KIT).map(([f, t]) => [f, `﻿${t}`]));
  assert.equal(run(KIT, bom).code, 0);
  const noFinal = Object.fromEntries(Object.entries(KIT).map(([f, t]) => [f, t.replace(/\n$/, '')]));
  assert.equal(run(KIT, noFinal).code, 0);
});

test('fails when a kit file sits only in a subfolder of one app', () => {
  const r = run(withFile('src/components/brand/scenes/parts/Extra.ts', 'export const e = 1;\n'), KIT);
  assert.equal(r.code, 1, r.out);
  assert.match(r.out, /parts\/Extra\.ts: only in web-vrms/);
});

const BAD = 'src/components/brand/scenes/Bad.tsx';
for (const [form, line] of [
  ['import from', "import { Button } from '@/components/ui/button';"],
  ['import type', "import type { TicketCan } from '@/lib/api/repairsApi';"],
  ['multi line import', "import {\n  Button,\n} from '../../ui/button';"],
  ['bare import', "import './side-effect.css';"],
  ['export from', "export { thing } from '@/lib/thing';"],
  ['export type from', "export type { Thing } from 'lodash';"],
  ['dynamic import', "const m = import('@/lib/heavy');"],
  ['relative path out of the kit', "import { x } from '../BrandMark';"],
]) {
  test(`fails on a bad import: ${form}`, () => {
    const files = withFile(BAD, `${line}\nexport const b = 1;\n`);
    const r = run(files, files);
    assert.equal(r.code, 1, r.out);
    assert.match(r.out, /Bad\.tsx imports '/);
  });
}

test('fails on a CSS @import in scenes.css', () => {
  const files = withFile('src/styles/scenes.css', "@import './more.css';\n:root {\n  --scene-road: #0a0d36;\n}\n");
  const r = run(files, files);
  assert.equal(r.code, 1, r.out);
  assert.match(r.out, /scenes\.css imports '\.\/more\.css'/);
});

test('allows react, @/lib/utils and kit files by relative path, with or without the extension', () => {
  const files = withFile('src/components/brand/scenes/Ok.tsx', "import { SceneSvg } from './SceneSvg.tsx';\nimport { w } from './parts/Wheel';\nexport const o = 1;\n");
  const r = run(files, files);
  assert.equal(r.code, 0, r.out);
});
