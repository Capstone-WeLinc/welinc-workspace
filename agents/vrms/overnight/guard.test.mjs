// Tests for the overnight guard. Run: node --test agents/vrms/overnight/guard.test.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { checkBash, checkFile } from './guard.mjs';

const GUARD = path.join(path.dirname(fileURLToPath(import.meta.url)), 'guard.mjs');
const ROOT = '/ws';
const onFeature = () => 'feat/x';
const onMain = () => 'main';
const bash = (cmd, branchOf = onFeature) => checkBash(cmd, ROOT, branchOf);

test('blocks every way of pushing', () => {
  for (const cmd of [
    'git push',
    'git push -u origin feat/x',
    'git -C welinc-backend-vrms push origin HEAD',
    'git -c push.default=current push',
    'cd welinc-web-vrms && git push',
    'npm run lint && git push --force',
    'echo ok; git push',
    'FOO=1 git push',
    'git push --dry-run origin HEAD:refs/heads/overnight-guard-check',
  ]) assert.ok(bash(cmd), cmd);
});

test('allows normal local git work', () => {
  for (const cmd of [
    'git status --short',
    'git fetch --quiet origin',
    'git log --oneline -5',
    'git diff --stat',
    'git add src/a.ts src/b.ts',
    'git commit -m "feat(repairs): add checklist edit"',
    'git switch -c feat/security-checks origin/development',
    'git checkout -b docs/overnight-2026-11-24 origin/main',
    'git checkout feat/security-checks',
    'git stash push -u -m "overnight 2026-11-24 feature 69"',
    'git stash list',
    'git branch --show-current',
    'git -C welinc-backend-vrms rev-parse --abbrev-ref HEAD',
    'git pull --ff-only',
  ]) assert.equal(bash(cmd), null, cmd);
});

test('blocks commits on protected branches and history rewrites', () => {
  assert.ok(bash('git commit -m x', onMain));
  assert.ok(bash('git commit -m x', () => 'development'));
  for (const cmd of [
    'git commit --amend --no-edit',
    'git commit -n -m x',
    'git merge origin/development',
    'git rebase origin/development',
    'git reset --hard HEAD~1',
    'git clean -fd',
    'git branch -D feat/x',
    'git checkout development',
    'git switch main',
    'git checkout -- src/a.ts',
    'git restore src/a.ts',
    'git stash drop',
    'git pull',
    'git remote set-url origin x',
    'git config user.name x',
  ]) assert.ok(bash(cmd), cmd);
});

test('gh: reads pass, writes are blocked', () => {
  for (const cmd of ['gh pr view 12', 'gh pr list --state open', 'gh run list -L 5', 'gh api repos/o/r/pulls', 'gh search prs foo']) {
    assert.equal(bash(cmd), null, cmd);
  }
  for (const cmd of [
    'gh pr create --fill',
    'gh pr merge 3 --squash',
    'gh pr comment 3 -b hi',
    'gh run rerun 99',
    'gh workflow run ci.yml',
    'gh secret set X',
    'gh api -X POST repos/o/r/issues',
    'gh api repos/o/r/issues -f title=x',
    'gh api graphql -f query=x',
    'gh repo edit --visibility private',
    'gh auth token',
  ]) assert.ok(bash(cmd), cmd);
});

test('blocks Azure, 1Password, staging changes and outside writes', () => {
  for (const cmd of [
    '~/.local/bin/az containerapp list',
    'PATH="$HOME/.local/bin:$PATH" bash infra/scripts/apply.sh staging --domains',
    'op read "op://WeLinc/x/y"',
    'curl -X POST https://staging-api.welinc.app/vrms/repairs -d {}',
    'curl --json {} https://example.com/hook',
    'ssh user@host',
  ]) assert.ok(bash(cmd), cmd);
  for (const cmd of [
    'curl -s https://staging-api.welinc.app/vrms/health',
    'curl -s -X POST http://localhost:3000/auth/login -d {}',
    'curl -X PATCH http://127.0.0.1:3002/repairs/1 --json {}',
  ]) assert.equal(bash(cmd), null, cmd);
});

test('blocks secrets and local data loss', () => {
  for (const cmd of [
    'cat welinc-backend-vrms/.env',
    'grep DATABASE welinc-auth/.env.local',
    'cat infra/private/staging.json',
    'docker compose -f docker-compose.vrms.yml down -v',
    'docker volume rm welinc_vrms_db',
    'docker exec welinc_vrms_backend npx prisma migrate reset --force',
    'npm publish',
  ]) assert.ok(bash(cmd), cmd);
  for (const cmd of [
    'cat welinc-backend-vrms/.env.example',
    'docker compose -f docker-compose.vrms.yml restart',
    'docker exec welinc_vrms_backend npx prisma generate',
    'npm run lint && npm run build',
  ]) assert.equal(bash(cmd), null, cmd);
});

test('file rules', () => {
  assert.ok(checkFile('Read', 'welinc-auth/.env', ROOT));
  assert.equal(checkFile('Read', 'welinc-auth/.env.example', ROOT), null);
  assert.ok(checkFile('Edit', 'agents/vrms/overnight/guard.mjs', ROOT));
  assert.ok(checkFile('Write', '.claude/settings.local.json', ROOT));
  assert.ok(checkFile('Edit', '.claude/skills/develop/SKILL.md', ROOT));
  assert.ok(checkFile('Edit', 'welinc-backend-vmms/src/a.ts', ROOT));
  assert.ok(checkFile('Edit', 'welinc-web-bms/src/a.tsx', ROOT));
  assert.ok(checkFile('Write', '/etc/hosts', ROOT));
  assert.equal(checkFile('Edit', 'welinc-backend-vrms/src/a.ts', ROOT), null);
  assert.equal(checkFile('Edit', 'welinc-mobile-vrms_vmms/app/a.tsx', ROOT), null);
  assert.equal(checkFile('Edit', 'docs/scope/vrms/platform.md', ROOT), null);
  assert.equal(checkFile('Write', 'docs/_private/vrms/overnight/2026-11-24.md', ROOT), null);
});

function run(mode, input, env = {}) {
  return spawnSync('node', [GUARD, mode], { input: JSON.stringify(input), encoding: 'utf8', env: { ...process.env, ...env } });
}

test('pre hook: exit 2 with a reason, or exit 0 silently', () => {
  const blocked = run('pre', { tool_name: 'Bash', tool_input: { command: 'git push' }, cwd: ROOT });
  assert.equal(blocked.status, 2);
  assert.match(blocked.stderr, /no git push/);
  const asked = run('pre', { tool_name: 'AskUserQuestion', tool_input: {} });
  assert.equal(asked.status, 2);
  assert.match(asked.stderr, /nobody is awake/);
  const ok = run('pre', { tool_name: 'Bash', tool_input: { command: 'git status' }, cwd: ROOT });
  assert.equal(ok.status, 0);
  assert.equal(ok.stdout, '');
  const bad = spawnSync('node', [GUARD, 'pre'], { input: 'not json', encoding: 'utf8' });
  assert.equal(bad.status, 2);
});

test('stop hook keeps a running queue going, then gives up after the cap', () => {
  const dir = mkdtempSync(path.join(tmpdir(), 'overnight-'));
  const stateDir = path.join(dir, 'docs', '_private', 'vrms', 'overnight');
  mkdirSync(stateDir, { recursive: true });
  const file = path.join(stateDir, 'state.json');
  const env = { CLAUDE_PROJECT_DIR: dir };

  assert.equal(run('stop', {}, env).stdout, '', 'no state file: no opinion');

  writeFileSync(file, JSON.stringify({ status: 'running', queue: [{ id: '69-verify', status: 'pending' }, { id: '58-test', status: 'done' }] }));
  const out = JSON.parse(run('stop', {}, env).stdout);
  assert.equal(out.decision, 'block');
  assert.match(out.reason, /69-verify/);
  assert.doesNotMatch(out.reason, /58-test/);

  writeFileSync(file, JSON.stringify({ status: 'finished', queue: [] }));
  assert.equal(run('stop', {}, env).stdout, '');

  writeFileSync(file, JSON.stringify({ status: 'running', stopContinuations: 40, queue: [] }));
  assert.equal(run('stop', {}, env).stdout, '');
  assert.equal(JSON.parse(readFileSync(file, 'utf8')).status, 'halted');
});

test('fresh mode: sessions exit between items, and next reports what is left', () => {
  const dir = mkdtempSync(path.join(tmpdir(), 'overnight-'));
  const stateDir = path.join(dir, 'docs', '_private', 'vrms', 'overnight');
  mkdirSync(stateDir, { recursive: true });
  const file = path.join(stateDir, 'state.json');
  const env = (mode) => ({ CLAUDE_PROJECT_DIR: dir, OVERNIGHT_MODE: mode });

  writeFileSync(file, JSON.stringify({ status: 'running', queue: [{ id: 'a', status: 'done' }, { id: 'b', status: 'pending' }] }));
  assert.equal(run('stop', {}, env('one')).stdout, '', 'one mode, nothing running: may exit');
  assert.equal(run('stop', {}, env('prepare')).stdout, '');
  assert.equal(run('stop', {}, env('close')).stdout, '');
  const n = run('next', {}, env('session'));
  assert.equal(n.status, 0);
  assert.equal(n.stdout.trim(), '1');

  writeFileSync(file, JSON.stringify({ status: 'running', queue: [{ id: 'b', status: 'running' }] }));
  assert.equal(JSON.parse(run('stop', {}, env('one')).stdout).decision, 'block', 'one mode, item half done: keep going');

  writeFileSync(file, JSON.stringify({ status: 'running', queue: [{ id: 'b', status: 'parked' }] }));
  assert.equal(run('next', {}, env('session')).status, 1);
  writeFileSync(file, JSON.stringify({ status: 'halted', queue: [{ id: 'b', status: 'pending' }] }));
  assert.equal(run('next', {}, env('session')).status, 1, 'a halted run has nothing next');
});
