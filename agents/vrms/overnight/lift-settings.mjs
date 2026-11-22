// Lifts the shared project's routine "ask" rules for an overnight run, and puts them back after.
// In Claude Code an ask rule beats every allow rule, and the overnight settings turn each ask into a
// refusal, so `git switch -c` and `git commit` could never run unattended. start.sh calls:
//   node agents/vrms/overnight/lift-settings.mjs lift      before Claude starts
//   node agents/vrms/overnight/lift-settings.mjs restore   when the run ends (and first, after a crash)
//   node agents/vrms/overnight/lift-settings.mjs restore-if-stale   a SessionStart hook in normal sessions:
//        puts the settings back when the run that lifted them is gone (the terminal was closed mid run)
// The original is kept in the git ignored overnight folder, and git is told to ignore the edit while
// it lasts, so the workspace still counts as clean. Push, merge, rebase, PRs and the deny list stay.
import { execFileSync } from 'node:child_process';
import { existsSync, readFileSync, rmSync, statSync, writeFileSync, copyFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..', '..', '..');
const FILE = join(ROOT, '.claude', 'settings.json');
const BACKUP = join(ROOT, 'docs', '_private', 'vrms', 'overnight', 'project-settings.backup.json');
const PID = join(ROOT, 'docs', '_private', 'vrms', 'overnight', 'lift.pid');
const REL = '.claude/settings.json';

// Routine local work the overnight run must do; everything else in the ask list stays.
export const LIFTED = [
  'Bash(git commit*)',
  'Bash(git checkout -b*)',
  'Bash(git switch -c*)',
  'Bash(npm install*)',
  'Bash(npm uninstall*)',
  'Bash(docker compose up*)',
  'Bash(npx prisma migrate dev*)',
];

const git = (...args) => execFileSync('git', ['-C', ROOT, ...args], { stdio: 'ignore' });

function restore() {
  if (!existsSync(BACKUP)) return false;
  copyFileSync(BACKUP, FILE);
  rmSync(BACKUP);
  rmSync(PID, { force: true });
  git('update-index', '--no-assume-unchanged', REL);
  return true;
}

function lift() {
  restore(); // a leftover from a run that died
  const settings = JSON.parse(readFileSync(FILE, 'utf8'));
  const ask = settings.permissions?.ask ?? [];
  const kept = ask.filter((rule) => !LIFTED.includes(rule));
  if (kept.length === ask.length) return false;
  if (process.argv[3]) writeFileSync(PID, process.argv[3]); // first, so a session starting now sees an owner
  copyFileSync(FILE, BACKUP);
  git('update-index', '--assume-unchanged', REL);
  settings.permissions.ask = kept;
  writeFileSync(FILE, `${JSON.stringify(settings, null, 2)}\n`);
  return true;
}

function alive(pid) {
  try {
    process.kill(Number(pid), 0);
    return true;
  } catch (err) {
    return err.code === 'EPERM';
  }
}

// Restore only when no run owns the lift any more, so a normal session opened mid run leaves it alone.
function restoreIfStale() {
  if (!existsSync(BACKUP)) return false;
  // A lift older than 20 hours belongs to no run (none lasts that long), even if its process id was reused.
  const fresh = existsSync(PID) && Date.now() - statSync(PID).mtimeMs < 20 * 3600 * 1000;
  if (fresh && alive(readFileSync(PID, 'utf8').trim())) return false;
  return restore();
}

const cmd = process.argv[2];
if (cmd === 'lift') console.log(lift() ? 'Lifted the routine ask rules for this run.' : 'Nothing to lift.');
else if (cmd === 'restore') console.log(restore() ? 'Restored .claude/settings.json.' : 'Nothing to restore.');
else if (cmd === 'restore-if-stale') {
  if (restoreIfStale()) console.log('An overnight run ended without putting .claude/settings.json back; restored it.');
}
else {
  console.error('Usage: node lift-settings.mjs lift [pid]|restore|restore-if-stale');
  process.exit(2);
}
