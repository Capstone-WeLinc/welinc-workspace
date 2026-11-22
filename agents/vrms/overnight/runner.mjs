#!/usr/bin/env node
// Helpers start.sh and the /overnight skill call, so the bookkeeping never costs model usage.
//   node runner.mjs runid               prints this run's id (the running one to resume, or a new <date>-<HHMM>)
//   node runner.mjs archive             files a finished state.json under runs/<id>/ and keeps the newest 14 runs
//   node runner.mjs refs                saves every repo's branch tips at the start (for `changes`)
//   node runner.mjs probe               one tiny Haiku call that reads your usage (5 hour and 7 day windows)
//   claude -p ... --output-format stream-json --verbose | node runner.mjs log <label> <model> <effort>
//                                       prints the step's final text and records its usage
//   node runner.mjs room [limit]        exit 0 when the 5 hour window is under limit% (default 95), else
//                                       prints the seconds until it resets and exits 1 (3 when the week is full)
//   node runner.mjs usage               the usage table (markdown) for the report
//   node runner.mjs changes             writes runs/<id>/changes.md: every commit tonight, per repo and branch
//   node runner.mjs status <item id>    prints that item's status in state.json
//   node runner.mjs fail <item id> <why>   marks an item still pending or running as failed (start.sh, so it can't spin)
//   node runner.mjs halt <why>          a run that is still `running` becomes `halted` (start.sh, after close out)
// Pure node, no packages. Files live in docs/_private/vrms/overnight/ (git ignored).
import { execFileSync, spawnSync } from 'node:child_process';
import { appendFileSync, existsSync, mkdirSync, readdirSync, readFileSync, renameSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..', '..', '..');
const DIR = join(ROOT, 'docs', '_private', 'vrms', 'overnight');
const STATE = join(DIR, 'state.json');
const RUNS = join(DIR, 'runs');
const KEEP = 14;

const pad = (n) => String(n).padStart(2, '0');
const hhmm = (d = new Date()) => `${pad(d.getHours())}:${pad(d.getMinutes())}`;
const today = (d = new Date()) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const readJson = (f, fallback = null) => {
  try {
    return JSON.parse(readFileSync(f, 'utf8'));
  } catch {
    return fallback;
  }
};
const state = () => readJson(STATE);

export function runId() {
  if (process.env.OVERNIGHT_RUN_ID) return process.env.OVERNIGHT_RUN_ID;
  const s = state();
  if (s?.status === 'running' && s.runId) return s.runId;
  const d = new Date();
  return `${today(d)}-${pad(d.getHours())}${pad(d.getMinutes())}`;
}
const runDir = () => {
  const d = join(RUNS, runId());
  mkdirSync(d, { recursive: true });
  return d;
};

// A finished (or halted) run moves to runs/<its id>/ so the next run never writes over it.
function archive() {
  const s = state();
  // A run still `running` whose state has not changed for 6 hours was cut off (a crash, a reboot): file
  // it as halted instead of letting tonight's run resume an old night.
  if (s?.status === 'running' && Date.now() - statSync(STATE).mtimeMs > 6 * 3600 * 1000) {
    s.status = 'halted';
    s.haltReason = s.haltReason || 'cut off: the state was not touched for 6 hours';
    writeFileSync(STATE, JSON.stringify(s, null, 2));
  }
  if (s && s.status !== 'running') {
    const id = s.runId || `${s.date || today()}-${String(s.startedAt || '0000').replace(':', '')}`;
    const d = join(RUNS, id);
    mkdirSync(d, { recursive: true });
    renameSync(STATE, join(d, 'state.json'));
    console.log(`Filed the last run (${id}) under runs/${id}/.`);
  }
  if (!existsSync(RUNS)) return;
  const ids = readdirSync(RUNS).filter((n) => statSync(join(RUNS, n)).isDirectory()).sort();
  for (const old of ids.slice(0, Math.max(0, ids.length - (KEEP - 1)))) { // the new run makes it KEEP
    rmSync(join(RUNS, old), { recursive: true, force: true });
    rmSync(join(DIR, `${old}.md`), { force: true });
  }
}

// ---------- git: what changed ----------

function repos() {
  const list = [['workspace', ROOT]];
  for (const name of readdirSync(ROOT).sort()) {
    if (!name.startsWith('welinc-') || !existsSync(join(ROOT, name, '.git'))) continue;
    if (/(vmms|bms)/.test(name) && name !== 'welinc-mobile-vrms_vmms') continue;
    list.push([name, join(ROOT, name)]);
  }
  return list;
}
const git = (cwd, ...args) => {
  try {
    return execFileSync('git', ['-C', cwd, ...args], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
  } catch {
    return '';
  }
};
const tips = (cwd) =>
  Object.fromEntries(
    git(cwd, 'for-each-ref', '--format=%(refname:short) %(objectname)', 'refs/heads')
      .split('\n')
      .filter(Boolean)
      .map((l) => l.split(' ')),
  );

function refs() {
  const file = join(runDir(), 'refs-start.json');
  if (existsSync(file)) return; // a resumed run keeps its first snapshot
  writeFileSync(file, JSON.stringify(Object.fromEntries(repos().map(([n, p]) => [n, tips(p)])), null, 2));
}

const isAncestor = (cwd, a, b) => spawnSync('git', ['-C', cwd, 'merge-base', '--is-ancestor', a, b]).status === 0;

// A branch created tonight started from the closest commit among the start of night tips (a local
// feature branch it builds on) and the remote base, so its list never repeats another branch's commits.
function startingPoint(cwd, branch, startTips, name) {
  const remote = name === 'workspace' ? 'origin/main' : 'origin/development';
  let best = remote;
  let fewest = Infinity;
  for (const c of [remote, ...startTips]) {
    const n = Number(git(cwd, 'rev-list', '--count', `${c}..${branch}`) || NaN);
    if (Number.isFinite(n) && n < fewest && isAncestor(cwd, c, branch)) {
      fewest = n;
      best = c.length === 40 ? c.slice(0, 7) : c;
    }
  }
  return best;
}

function changes() {
  const start = readJson(join(runDir(), 'refs-start.json'), {});
  let out = `# What changed · run ${runId()}\n\nBuilt from git, not from the model: every commit made tonight, per repo and branch. Nothing is pushed.\n`;
  let any = false;
  for (const [name, p] of repos()) {
    const before = start[name] || {};
    for (const [branch, tip] of Object.entries(tips(p))) {
      if (before[branch] === tip) continue;
      const base = before[branch] || startingPoint(p, branch, Object.values(before), name);
      const range = `${base}..${branch}`;
      const log = git(p, 'log', '--reverse', '--format=%h %s', range);
      if (!log) {
        if (git(p, 'rev-parse', '--verify', '--quiet', base) === '') out += `\n## ${name} · \`${branch}\`\n\nMoved tonight, but its base \`${base}\` is missing here, so the commits could not be listed. Look with \`git -C ${name === 'workspace' ? '.' : name} log ${branch}\`.\n`;
        continue;
      }
      any = true;
      out += `\n## ${name} · \`${branch}\`\n\n`;
      for (const line of log.split('\n')) {
        const [sha, ...subject] = line.split(' ');
        out += `### ${sha} ${subject.join(' ')}\n\n`;
        const stat = git(p, 'show', '--format=', '--numstat', sha)
          .split('\n')
          .filter(Boolean)
          .map((l) => {
            const [add, del, file] = l.split('\t');
            return add === '-' ? `- \`${file}\` (picture or other binary file)` : `- \`${file}\` +${add} −${del}`;
          });
        out += `${stat.join('\n')}\n\n`;
      }
      out += `See the whole diff: \`git -C ${name === 'workspace' ? '.' : name} diff ${base}...${branch}\`\n`;
    }
  }
  if (!any) out += '\nNo commits tonight.\n';
  const file = join(runDir(), 'changes.md');
  writeFileSync(file, out);
  console.log(file);
}

// ---------- usage ----------

const usageFile = () => join(runDir(), 'usage.jsonl');
const pct = (u) => (typeof u === 'number' ? Math.round(u * 100) : null);

function limits(event) {
  const w = event?.rate_limit_info?.unifiedWindows || {};
  return {
    five: pct(w.five_hour?.utilization),
    fiveReset: w.five_hour?.resetsAt ?? null,
    week: pct(w.seven_day?.utilization),
    weekReset: w.seven_day?.resetsAt ?? null,
  };
}

function record(entry) {
  appendFileSync(usageFile(), `${JSON.stringify({ at: hhmm(), ...entry })}\n`);
}

// Reads a stream-json step from stdin, passes its final text through, and records turns, cost and limits.
async function log(label, model, effort) {
  let buf = '';
  let lim = {};
  let result = null;
  process.stdin.setEncoding('utf8');
  const handle = (line) => {
    let j;
    try {
      j = JSON.parse(line);
    } catch {
      if (line.trim()) console.log(line);
      return;
    }
    if (j.type === 'rate_limit_event') lim = limits(j);
    if (j.type === 'result') result = j;
    // One line per tool call, so `tail -f runner.log` shows progress while a step runs.
    if (j.type === 'assistant') {
      for (const c of j.message?.content || []) {
        if (c.type !== 'tool_use') continue;
        const what = c.input?.command || c.input?.file_path || c.input?.skill || c.input?.description || '';
        console.log(`  ${hhmm()} ${c.name} ${String(what).replace(/\s+/g, ' ').slice(0, 100)}`);
      }
    }
  };
  for await (const chunk of process.stdin) {
    buf += chunk;
    let i;
    while ((i = buf.indexOf('\n')) >= 0) {
      handle(buf.slice(0, i));
      buf = buf.slice(i + 1);
    }
  }
  if (buf) handle(buf);
  if (result?.result) console.log(result.result);
  const u = result?.usage || {};
  record({
    label,
    model,
    effort,
    turns: result?.num_turns ?? null,
    minutes: result?.duration_ms ? Math.round(result.duration_ms / 60000) : null,
    costUsd: result?.total_cost_usd ?? null,
    outTokens: u.output_tokens ?? null,
    ...lim,
  });
  console.log(`[usage] ${label}: ${result?.num_turns ?? '?'} turns, 5 hour ${lim.five ?? '?'}%, week ${lim.week ?? '?'}%`);
}

function probe() {
  const bin = process.env.CLAUDE_BIN || 'claude';
  const r = spawnSync(bin, ['-p', 'Reply with ok.', '--model', 'haiku', '--output-format', 'stream-json', '--verbose', '--max-turns', '1', '--setting-sources', 'user'], {
    encoding: 'utf8',
    cwd: tmpdir(), // outside the workspace, so no CLAUDE.md or AGENTS.md loads into the check
    timeout: 120000,
  });
  const event = (r.stdout || '')
    .split('\n')
    .map((l) => {
      try {
        return JSON.parse(l);
      } catch {
        return null;
      }
    })
    .find((j) => j?.type === 'rate_limit_event');
  const lim = limits(event);
  record({ label: `usage check${process.argv[3] ? ` (${process.argv[3]})` : ''}`, ...lim });
  console.log(`Usage: 5 hour window ${lim.five ?? '?'}%, week ${lim.week ?? '?'}%.`);
}

const entries = () =>
  existsSync(usageFile())
    ? readFileSync(usageFile(), 'utf8').split('\n').filter(Boolean).map((l) => JSON.parse(l))
    : [];

function room(limit = 95) {
  const last = [...entries()].reverse().find((e) => e.five != null);
  if (!last) process.exit(0);
  const now = Date.now() / 1000;
  if (last.week != null && last.week >= limit && last.weekReset > now) {
    console.log(Math.ceil(last.weekReset - now));
    process.exit(3);
  }
  if (last.five >= limit && last.fiveReset > now) {
    console.log(Math.ceil(last.fiveReset - now) + 60);
    process.exit(1);
  }
  process.exit(0);
}

function usage() {
  const rows = entries();
  if (!rows.length) return console.log('No usage readings for this run.');
  const at = (s) => (s ? hhmm(new Date(s * 1000)) : '');
  let out = '| Time | Step | Model | Turns | Minutes | 5 hour | Week |\n|---|---|---|---|---|---|---|\n';
  for (const r of rows) {
    const model = [r.model, r.effort].filter(Boolean).join(' ');
    out += `| ${r.at} | ${r.label} | ${model} | ${r.turns ?? ''} | ${r.minutes ?? ''} | ${r.five ?? '?'}% | ${r.week ?? '?'}% |\n`;
  }
  const last = rows[rows.length - 1];
  out += `\nThe 5 hour window resets at ${at(last.fiveReset) || '?'}, the week at ${last.weekReset ? new Date(last.weekReset * 1000).toLocaleString('en-GB', { weekday: 'short', hour: '2-digit', minute: '2-digit' }) : '?'}.\n`;
  console.log(out);
}

function setItem(id, why) {
  const s = state();
  const q = s?.queue?.find((x) => x.id === id);
  if (!q || !['pending', 'running'].includes(q.status)) return;
  q.status = 'failed';
  q.result = q.result ? `${q.result} · ${why}` : why;
  writeFileSync(STATE, JSON.stringify(s, null, 2));
  console.log(`Marked ${id} failed: ${why}`);
}

function halt(why) {
  const s = state();
  if (s?.status !== 'running') return;
  s.status = 'halted';
  s.haltReason = why;
  writeFileSync(STATE, JSON.stringify(s, null, 2));
  console.log(`Run halted: ${why}`);
}

const [cmd, ...args] = process.argv.slice(2);
if (cmd === 'runid') console.log(runId());
else if (cmd === 'archive') archive();
else if (cmd === 'refs') refs();
else if (cmd === 'changes') changes();
else if (cmd === 'probe') probe();
else if (cmd === 'log') await log(args[0] || 'step', args[1] || '', args[2] || '');
else if (cmd === 'room') room(Number(args[0]) || 95);
else if (cmd === 'usage') usage();
else if (cmd === 'status') console.log(state()?.queue?.find((x) => x.id === args[0])?.status ?? 'missing');
else if (cmd === 'fail') setItem(args[0], args.slice(1).join(' ') || 'failed');
else if (cmd === 'halt') halt(args.join(' ') || 'the run ended before close out finished');
else {
  console.error('Usage: node runner.mjs runid|archive|refs|probe|log|room|usage|changes|status|fail|halt');
  process.exit(2);
}
