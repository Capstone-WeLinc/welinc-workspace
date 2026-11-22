#!/usr/bin/env node
// Overnight guard for unattended Claude Code runs (loaded only by agents/vrms/overnight/settings.json).
//   node guard.mjs pre    PreToolUse hook: blocks anything that leaves this machine or needs a person
//   node guard.mjs stop   Stop hook: keeps the session working while the overnight queue has items
// Exit 2 with a reason on stderr blocks the call; exit 0 with no output lets the normal permission rules decide.
// Pure node, no packages, so it runs the same on macOS and Windows (Git Bash or PowerShell).

import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import path from 'node:path';

const PROTECTED_BRANCHES = new Set(['main', 'master', 'development']);
const MAX_STOP_CONTINUATIONS = 40;

// ---------- shared helpers ----------

function block(reason) {
  process.stderr.write(`Overnight guard: ${reason}\n`);
  process.exit(2);
}

function projectDir(input) {
  return process.env.CLAUDE_PROJECT_DIR || input.cwd || process.cwd();
}

function statePath(input) {
  return path.join(projectDir(input), 'docs', '_private', 'vrms', 'overnight', 'state.json');
}

// Split a shell command into simple segments at ; && || | newlines and $( ` boundaries.
export function segments(command) {
  return command
    .split(/\r?\n|;|&&|\|\||\||\$\(|`|\)/)
    .map((s) => s.trim())
    .filter(Boolean);
}

// Very small shell word splitter: honours single and double quotes, enough for guard checks.
export function words(segment) {
  const out = [];
  const re = /"((?:\\.|[^"\\])*)"|'([^']*)'|(\S+)/g;
  let m;
  while ((m = re.exec(segment))) out.push(m[1] ?? m[2] ?? m[3]);
  return out;
}

// Drop leading env assignments and wrappers so the real program is first.
function program(ws) {
  let i = 0;
  while (i < ws.length && /^[A-Za-z_][A-Za-z0-9_]*=/.test(ws[i])) i++;
  while (i < ws.length && ['sudo', 'command', 'exec', 'time', 'nohup', 'env', 'xargs'].includes(ws[i])) i++;
  return ws.slice(i);
}

const base = (w) => (w || '').split(/[\\/]/).pop();

// ---------- git ----------

// Options of `git` itself that take a separate value.
const GIT_VALUE_OPTS = new Set(['-C', '-c', '--git-dir', '--work-tree', '--namespace', '--exec-path', '--config-env']);

export function gitParts(ws) {
  let dir = null;
  let i = 1;
  while (i < ws.length && ws[i].startsWith('-')) {
    if (ws[i] === '-C') dir = ws[i + 1];
    if (GIT_VALUE_OPTS.has(ws[i])) i += 2;
    else i += 1;
  }
  return { dir, sub: ws[i], args: ws.slice(i + 1) };
}

function currentBranch(dir) {
  try {
    return execFileSync('git', ['-C', dir, 'rev-parse', '--abbrev-ref', 'HEAD'], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
  } catch {
    return null;
  }
}

export function checkGit(ws, cwd, branchOf = currentBranch) {
  const { dir, sub, args } = gitParts(ws);
  const where = dir ? path.resolve(cwd, dir) : cwd;
  const has = (...flags) => args.some((a) => flags.includes(a) || flags.some((f) => f.endsWith('=') && a.startsWith(f)));

  switch (sub) {
    case 'push':
      return 'no git push overnight. Leave the branch local and list it under "Ready to push" in the report.';
    case 'pull':
      if (!has('--ff-only')) return 'only `git pull --ff-only` is allowed overnight.';
      return null;
    case 'merge':
      if (has('--abort')) return null;
      return 'no merges overnight. Branch from the up to date remote branch instead (`git switch -c <branch> origin/development`).';
    case 'rebase':
      if (has('--abort')) return null;
      return 'no rebase overnight.';
    case 'reset':
      if (has('--hard', '--merge', '--keep')) return 'no `git reset --hard` overnight. Stash instead (`git stash push -u -m "overnight ..."`).';
      return null;
    case 'clean':
      return 'no `git clean` overnight; it deletes files for good. Stash instead.';
    case 'branch':
      if (has('-D', '--delete', '-d', '-M', '-m', '--move', '-f', '--force', '-u', '--set-upstream-to=', '--unset-upstream')) return 'no deleting, renaming or retargeting branches overnight.';
      return null;
    case 'remote':
      if (args[0] && !['-v', 'show', 'get-url'].includes(args[0])) return 'no changes to git remotes overnight.';
      return null;
    case 'tag':
      if (args.length && !has('-l', '--list')) return 'no tags overnight.';
      return null;
    case 'config':
      if (!has('--get', '--get-all', '--list', '-l', '--get-regexp')) return 'no git config changes overnight.';
      return null;
    case 'filter-branch':
    case 'filter-repo':
    case 'update-ref':
    case 'replace':
    case 'gc':
    case 'prune':
    case 'reflog':
      if (sub === 'reflog' && (!args[0] || args[0] === 'show')) return null;
      return `no \`git ${sub}\` overnight.`;
    case 'worktree':
      if (args[0] === 'remove' || args[0] === 'prune') return 'no removing worktrees overnight.';
      return null;
    case 'stash':
      if (['drop', 'clear', 'pop'].includes(args[0])) return 'stashes stay as they are overnight (no drop, clear or pop); the user reviews them in the morning.';
      return null;
    case 'checkout':
    case 'switch': {
      const target = args.filter((a) => !a.startsWith('-')).at(0);
      const creates = has('-b', '-B', '-c', '-C', '--create', '--orphan');
      if (sub === 'checkout' && (has('--') || target === '.')) return 'no `git checkout -- <file>` overnight; it throws away changes. Stash instead.';
      if (!creates && target && PROTECTED_BRANCHES.has(target)) {
        return `do not check out \`${target}\` overnight. Create your branch straight from the remote: \`git switch -c <branch> origin/${target}\`.`;
      }
      if (has('-f', '--force', '--discard-changes')) return 'no forced checkout overnight; it throws away changes.';
      return null;
    }
    case 'restore':
      if (!has('--staged', '-S')) return 'no `git restore` of working files overnight; it throws away changes. Stash instead.';
      return null;
    case 'commit': {
      const branch = branchOf(where);
      if (branch && PROTECTED_BRANCHES.has(branch)) return `never commit on \`${branch}\`. Create a feat/, docs/ or chore/ branch first.`;
      if (has('--amend')) return 'no amending overnight; make a new commit.';
      if (has('--no-verify', '-n')) return 'no skipping commit hooks overnight.';
      return null;
    }
    default:
      return null;
  }
}

// ---------- gh ----------

const GH_READ = {
  pr: ['view', 'list', 'status', 'diff', 'checks'],
  run: ['view', 'list', 'watch'],
  issue: ['view', 'list', 'status'],
  repo: ['view', 'list'],
  release: ['view', 'list'],
  workflow: ['view', 'list'],
  search: null, // every search subcommand reads
  status: null,
};

export function checkGh(ws) {
  const [, group, sub, ...rest] = ws;
  if (group === 'api') {
    const all = ws.slice(2);
    const method = (() => {
      const i = all.findIndex((a) => a === '-X' || a === '--method');
      if (i >= 0) return (all[i + 1] || '').toUpperCase();
      const eq = all.find((a) => a.startsWith('--method=') || a.startsWith('-X'));
      if (eq && eq !== '-X') return eq.replace(/^--method=|^-X/, '').toUpperCase();
      return 'GET';
    })();
    const sendsBody = all.some((a) => ['-f', '-F', '--field', '--raw-field', '--input'].includes(a) || /^--(raw-)?field=/.test(a));
    if (method !== 'GET' || sendsBody) return 'only read only `gh api` calls (GET, no fields) are allowed overnight.';
    if (all.some((a) => /graphql/.test(a))) return 'no `gh api graphql` overnight (it can write).';
    return null;
  }
  if (!(group in GH_READ)) return `\`gh ${group ?? ''}\` is not allowed overnight; only read only gh commands are.`;
  const allowed = GH_READ[group];
  if (allowed && !allowed.includes(sub)) return `\`gh ${group} ${sub ?? ''}\` is not allowed overnight. No PRs, comments, reruns, merges or settings changes.`;
  void rest;
  return null;
}

// ---------- other commands ----------

const BANNED_PROGRAMS = {
  az: 'no Azure CLI overnight; staging is never touched unattended.',
  op: 'no 1Password CLI overnight.',
  terraform: 'no infrastructure changes overnight.',
  bicep: 'no infrastructure changes overnight.',
  azd: 'no infrastructure changes overnight.',
  ssh: 'no remote shells overnight.',
  scp: 'no copying files to other machines overnight.',
  ngrok: 'no tunnels overnight.',
  'apply.sh': 'no `apply.sh` overnight; staging is never touched unattended.',
};

const LOCAL_HOST = /^(https?:\/\/)?(localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\]|host\.docker\.internal|welinc[_-][a-z0-9_-]+)(:\d+)?(\/|$)/i;

function checkHttp(prog, ws) {
  const args = ws.slice(1);
  const url = args.find((a) => /^(https?:\/\/|[a-z0-9.-]+\.[a-z]{2,}(:\d+)?\/)/i.test(a) || LOCAL_HOST.test(a));
  if (!url || LOCAL_HOST.test(url)) return null;
  if (prog === 'curl') {
    const i = args.findIndex((a) => a === '-X' || a === '--request');
    const method = i >= 0 ? (args[i + 1] || '').toUpperCase() : (args.find((a) => /^-X[A-Z]+$/.test(a)) || '').slice(2);
    const sends = args.some((a) => /^(-d|--data.*|-F|--form.*|-T|--upload-file|--json)$/.test(a) || /^--(data|form|json)/.test(a));
    if ((method && method !== 'GET' && method !== 'HEAD') || sends) return 'no requests that send data to outside hosts overnight (only GET, or anything to localhost).';
  }
  if (prog === 'wget' && args.some((a) => /^--(post|method|body)/.test(a))) return 'no requests that send data to outside hosts overnight.';
  return null;
}

const ENV_FILE = /(^|[\\/])\.env(\.[A-Za-z0-9_-]+)?$/;
const isSecretFile = (p) => (ENV_FILE.test(p) && !/\.env\.example$/.test(p)) || /(^|[\\/])infra[\\/]private([\\/]|$)/.test(p);
const READERS = new Set(['cat', 'less', 'more', 'head', 'tail', 'grep', 'rg', 'egrep', 'sed', 'awk', 'bat', 'strings', 'xxd', 'od', 'base64', 'cp', 'mv', 'source', '.', 'diff', 'sort', 'uniq', 'cut', 'jq', 'tee', 'nl', 'wc']);

export function checkSegment(seg, cwd, branchOf) {
  const ws = program(words(seg));
  if (!ws.length) return null;
  const prog = base(ws[0]);

  if (prog === 'git') return checkGit(ws, cwd, branchOf);
  if (prog === 'gh') return checkGh(ws);
  if (BANNED_PROGRAMS[prog]) return BANNED_PROGRAMS[prog];
  if (ws.some((w) => base(w) === 'apply.sh')) return BANNED_PROGRAMS['apply.sh'];
  if (prog === 'curl' || prog === 'wget') return checkHttp(prog, ws);

  if (READERS.has(prog) && ws.slice(1).some((w) => isSecretFile(w))) return 'never read or copy `.env` or `infra/private/` files. Use `.env.example` for names only.';

  const joined = ws.join(' ');
  if (/^(npm|pnpm|yarn)$/.test(prog) && /\bpublish\b/.test(joined)) return 'no publishing packages overnight.';
  if (/\bprisma\b/.test(joined) && /\b(migrate reset|--force-reset|--accept-data-loss)\b/.test(joined)) return 'no resets that wipe a local database overnight. Report the migration problem instead.';
  if (prog === 'docker') {
    if (/\b(volume (rm|prune)|system prune|image prune -a)\b/.test(joined)) return 'no deleting Docker volumes or pruning overnight; that destroys local data.';
    if (/\bcompose\b.*\bdown\b/.test(joined) && /(\s-v\b|--volumes)/.test(joined)) return 'no `docker compose down -v` overnight; it deletes the database volumes. Use `stop` or `restart`.';
  }
  if (prog === 'rm' && ws.some((w) => /^\/?$|^~\/?$|^\.\.?\/?$/.test(w))) return 'no removing the home, root or current folder.';
  return null;
}

export function checkBash(command, cwd, branchOf) {
  // Track `cd <dir> &&` so a later git commit is checked in the right repo.
  let where = cwd;
  for (const seg of segments(command)) {
    const ws = words(seg);
    if (ws[0] === 'cd' && ws[1]) {
      where = path.resolve(where, ws[1].replace(/^~(?=$|\/)/, process.env.HOME || '~'));
      continue;
    }
    const reason = checkSegment(seg, where, branchOf);
    if (reason) return reason;
  }
  return null;
}

// ---------- files ----------

export function checkFile(toolName, filePath, root) {
  if (!filePath) return null;
  const abs = path.resolve(root, filePath);
  const rel = path.relative(root, abs).split(path.sep).join('/');

  if (isSecretFile(abs)) return 'never read or change `.env` or `infra/private/` files. Use `.env.example` for names only.';
  if (toolName === 'Read') return null;

  if (rel.startsWith('agents/vrms/overnight/')) return 'the overnight guard and its settings are off limits during a run.';
  if (/(^|\/)\.claude\/settings(\.local)?\.json$/.test(rel) || /[\\/]\.claude[\\/]settings(\.local)?\.json$/.test(abs)) {
    return 'no changing Claude Code settings during an overnight run.';
  }
  if (/^\.claude\/skills\//.test(rel)) return 'no changing skills during an overnight run.';
  if (/^welinc-[^/]*(vmms|bms)[^/]*\//.test(rel) && !rel.startsWith('welinc-mobile-vrms_vmms/')) return 'VMMS and BMS repos belong to the other groups; never edit them.';
  if (rel.startsWith('..')) return 'stay inside the workspace overnight.';
  return null;
}

// ---------- hook entry points ----------

const ASK_REASON =
  'nobody is awake to answer. If the choice is small and easy to undo (a name, a file layout, a default the skill marks recommended), take the recommended option and add it to "Decided for you" in the report. If it is load bearing (a design or product decision, a spec change, anything /architect would own), park this item: write the question with its options into "Needs you" in the report, mark the item parked in state.json, and move to the next item.';

const OUTWARD_MCP = /^mcp__(atlassian|sentry)__(create|update|edit|delete|add|transition|link|unlink|submit|onboarding|analyze)/;

function pre(input) {
  const tool = input.tool_name || '';
  const ti = input.tool_input || {};
  const root = projectDir(input);
  const cwd = input.cwd || root;

  if (tool === 'Bash') {
    const reason = checkBash(String(ti.command || ''), cwd);
    if (reason) block(reason);
    return;
  }
  if (tool === 'AskUserQuestion') block(ASK_REASON);
  if (tool === 'ExitPlanMode' || tool === 'EnterPlanMode') block('no plan mode overnight; plan in the report and keep working.');
  if (['SendMessage', 'SendToProject', 'SendToProjectContext', 'RemoteTrigger', 'CronCreate'].includes(tool)) block('no messages to other sessions or scheduled jobs overnight.');
  if (OUTWARD_MCP.test(tool)) block('no writes to Jira or Sentry overnight; list what you would change in the report.');
  if (['Edit', 'Write', 'NotebookEdit', 'Read'].includes(tool)) {
    const reason = checkFile(tool, ti.file_path || ti.notebook_path, root);
    if (reason) block(reason);
  }
}

function readState(input) {
  const file = statePath(input);
  if (!existsSync(file)) return { file, state: null };
  try {
    return { file, state: JSON.parse(readFileSync(file, 'utf8')) };
  } catch {
    return { file, state: null };
  }
}

const OPEN = (q) => !['done', 'parked', 'skipped', 'failed'].includes(q.status);

// Model and effort for an item: its own `model` and `effort` (from a [sonnet] or [opus high] tag in
// queue.md) win; otherwise building uses Opus and everything else (verify, test, docs, diagrams) Sonnet.
const MODELS = new Set(['opus', 'sonnet', 'haiku', 'fable']);
const EFFORTS = new Set(['low', 'medium', 'high', 'xhigh', 'max']);
export function pick(item = {}) {
  const building = /^\/develop\b/.test(String(item.command || '').trim());
  const model = MODELS.has(item.model) ? item.model : building ? 'opus' : 'sonnet';
  const effort = EFFORTS.has(item.effort) ? item.effort : 'medium';
  return { model, effort };
}

// Exit 0 when the run is still going and has an item left (used by start.sh between sessions).
// Prints: <items left> <model> <effort>, the last two for the item the next session takes.
function next(input) {
  const { state } = readState(input);
  const left = state && state.status === 'running' ? (state.queue || []).filter(OPEN) : [];
  const first = left.find((q) => q.status === 'running') || left[0];
  const { model, effort } = pick(first);
  process.stdout.write(`${left.length} ${model} ${effort}\n`);
  process.exit(left.length ? 0 : 1);
}

function stop(input) {
  const { file, state } = readState(input);
  if (!state) return; // not an overnight run, or not started yet
  if (state.status !== 'running') return;

  // Fresh mode: each headless session does one step and exits. Let it exit unless an item is half done.
  const mode = process.env.OVERNIGHT_MODE || 'session';
  if (mode === 'prepare' || mode === 'close') return;
  if (mode === 'one' && !(state.queue || []).some((q) => q.status === 'running')) return;

  state.stopContinuations = (state.stopContinuations || 0) + 1;
  if (state.stopContinuations > MAX_STOP_CONTINUATIONS) {
    state.status = 'halted';
    state.haltReason = `stopped after ${MAX_STOP_CONTINUATIONS} automatic continuations`;
    writeFileSync(file, JSON.stringify(state, null, 2));
    return;
  }
  writeFileSync(file, JSON.stringify(state, null, 2));

  const left = (state.queue || []).filter(OPEN);
  const names = left.length ? left.map((q) => q.id).join(', ') : 'none (close out now: sync, local CI, report)';
  const reason =
    mode === 'one'
      ? `An overnight item is still marked running in state.json. Finish it (or park or fail it with the reason), save state.json, then stop.`
      : `Overnight run is still going (state.json status "running"). Items left: ${names}. Continue the /overnight skill from state.json. If an item is stuck, park it with the reason and move on. When the queue is empty, run Step 3 (sync, local CI, queue file, report, publish, push notification) and set status to "finished".`;
  process.stdout.write(JSON.stringify({ decision: 'block', reason }));
}

// Run only when executed directly (the tests import the helpers).
if (import.meta.url === `file://${process.argv[1]}` || process.argv[1]?.endsWith('guard.mjs')) {
  const mode = process.argv[2];
  let raw = '';
  try {
    raw = readFileSync(0, 'utf8');
  } catch {
    raw = '';
  }
  let input;
  try {
    input = raw ? JSON.parse(raw) : {};
  } catch {
    if (mode === 'pre') block('could not read the hook input, so the call is blocked to be safe.');
    process.exit(0);
  }
  if (mode === 'pre') pre(input);
  else if (mode === 'stop') stop(input);
  else if (mode === 'next') next(input);
  process.exit(0);
}
