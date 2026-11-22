---
name: overnight
allowed-tools: Bash, Read, Grep, Glob, Write, Edit, Agent, Skill, PushNotification, Artifact
argument-hint: "[feature numbers...] [--until HH:MM] [--plan] [--prepare | --one | --close | --watch]"
description: "Unattended overnight run for VRMS. Works through your bedtime queue and the scope's open build, verify and test boxes with /develop, /check verify, /test and /sync while you are away: local branches and commits only, never a push or PR. Finds stale docs, parks anything that needs your decision, runs each branch's CI locally, and ends with a morning report. Start it with agents/vrms/overnight/start.sh, never by hand in a normal session."
disable-model-invocation: true
---

## Output style (plain words, no dashes, no hyphens)

<!-- OUTPUT-STYLE:START -->
Write everything this skill produces, files and messages alike, in plain simple language. Talk to the reader as `you`, warm and direct like a colleague, and present every step as a recommendation they may run or skip, never an order. Keep technical terms that carry real meaning; explain each in plain words. Never use a dash or a hyphen as punctuation: no em dash, no en dash, and no hyphenated compounds. Write `read only`, not `read-only`. Say it in simple words, or reword the sentence. Code, file paths, command flags, and values other skills match on keep their hyphens. Use short sentences, commas, or parentheses. Clear beats clever.
<!-- OUTPUT-STYLE:END -->

## What this skill does

Runs the VRMS pipeline unattended, item by item, and leaves a morning report. The user started it on purpose and is away. Say "Using skill: overnight" once at the start.

The run is the user's standing approval for **local** git work only: create branches, stage, commit green work, stash. Everything outward stays off: no push, no PR, no merge, no Jira or Sentry writes, no Azure, no 1Password, no email to real people. The guard (`agents/vrms/overnight/guard.mjs`, loaded by `start.sh`) enforces this; treat every guard block as a rule, never work around it (no other spelling, no script that does the same thing). A blocked action means: write it in the report and move on.

All the project rules still apply (root `AGENTS.md`, `agents/vrms/AGENTS.md`, each repo's `AGENTS.md`, `CLAUDE.local.md`), except where this file overrides how to handle questions and git.

Files, all under `docs/_private/vrms/overnight/` (git ignores it):
- `queue.md`: the user's bedtime queue (shape in `queue-template.md`). Optional. It works like the handoff: one file, read first, rewritten at the end to only what is left, deleted when nothing is left.
- `state.json`: the run's memory (queue, progress, findings). The Stop hook reads it and keeps the session working while `status` is `running`. Everything you need to continue lives here, so a fresh context (or a restart after a crash or a usage limit) resumes from it. `start.sh` files a finished one under `runs/<id>/` before the next run starts.
- `<run id>.md`: the morning report (shape in `report-template.md`). The run id is in `$OVERNIGHT_RUN_ID` (for example `2026-11-24-2310`), so a second run the same night gets its own report and never writes over the first. `start.sh` prunes old runs; never delete a report yourself.
- `runs/<run id>/`: this run's folder: `notes.md` (what each session learned, for the next one), `usage.jsonl` (the usage meter), `changes.md` (what changed, built from git), `runner.log`, and `shots/` for screenshots.

The helper `node agents/vrms/overnight/runner.mjs` does the bookkeeping without model usage: `changes` writes `runs/<id>/changes.md`, `usage` prints the usage table.

## Modes

- `--prepare`, `--one`, `--close` (**fresh mode**, the default, driven by `start.sh`): each is its own headless session with a clean context, on the model `start.sh` picked for it (the item's `model` and `effort`, else Opus for `/develop` and Sonnet for everything else). `--prepare` runs Steps 0 and 1 and exits. `--one` takes the next `pending` item from `state.json`, runs Step 2 for it alone, saves, and exits. `--close` runs Step 3. In every mode, read `state.json` first and trust it over your memory.
- No mode flag (**session mode**, `start.sh --watch`): one long session does preflight, every item, and close out, so the user can follow it from the Claude app.
- `--plan`: Steps 0 and 1 only, then the report's Plan and Drift sections, `status` set to `finished`. A dry run.

## Step 0: Preflight (stop the run if a safety check fails)

1. `echo $OVERNIGHT_RUN` prints `1`. If not, the session was not started through `start.sh`: tell the user to use `bash agents/vrms/overnight/start.sh` and stop. Never run unattended without the guard.
2. Prove the guard is wired: run `git push --dry-run origin HEAD:refs/heads/overnight-guard-check` in the workspace. It must be **blocked**. If it runs, stop at once and report that the guard is not loaded.
3. Read, in this order: `queue.md` if present, the previous run's report (the newest `<run id>.md` in `docs/_private/vrms/overnight/`, or an older `YYYY-MM-DD.md`) for parked and failed items, the newest `docs/context/vrms/handoff-*.md`, then the scopes: VRMS (`docs/scope/vrms/index.md` and its epic files) and the suite (`docs/scope/_root/`, rows S1 and up: the shared services the user owns: welinc-auth, welinc-web-portal, the gateway). Note any defense within 24 hours for a warning at the top of the report.
4. Docker: `docker ps` shows the shared and VRMS stacks (`welinc_*`). If not, start them (shared first, then VRMS) and wait for the backends' health routes on localhost. Still down after 10 minutes: stop the run (nothing can be verified).
5. For each repo you may touch (the workspace, `welinc-backend-vrms`, `welinc-web-vrms`, `welinc-auth`, `welinc-web-portal`, `welinc-mobile-vrms_vmms`): `git fetch --quiet --prune` (stale refs make deleted branches look alive), note the branch and `git status --short`. A repo with uncommitted changes that are not from this run is **dirty**: never switch its branch, never commit in it, and skip items that need it. The user's own work always wins.
6. **Drift check.** Compare the docs against reality before trusting them:
   - Handoff: for each "Still open" item, look for evidence it is already done (merged PRs with `gh pr list --state merged`, branches, commits, files). Never edit the handoff (it is the user's note between machines); list each stale item under `drift` with the evidence and a suggested edit.
   - Scope: an unticked box whose work is plainly finished (merged commits for a milestone, a verify report or passing test files that match it) gets ticked on the workspace branch, with the proof recorded in `drift` as `fixed`. That is the only kind of doc edit the run makes on its own.
   - Anything that needs judgment (a row whose intent a later note changed, a note that contradicts code, a spec that disagrees with the scope, code with no scope row): don't edit it; record a proposed edit in `drift` as `proposed`, and keep that feature out of tonight's queue.

Logins: use the seeded accounts in `docs/integration/seed-accounts.md` (never `.env`). An emailed code for an `@welinc.com` seed account prints in the auth container's log (`docker logs welinc_auth --since 5m`). No step needs the user's own passwords, 1Password or an Azure login; anything that would is "left for you".

## Step 1: Build the queue

Sources, in order:
1. **`queue.md`**, when present: the user's items, in their order. Their notes on an item are the user's answers: follow them, and don't park a question they already answered. A queued item that is not runnable (needs `/architect`, is dated, touches staging) is not skipped silently: record why in the plan and, for a design item, write the questions it would need into `needsYou` so the user can answer them in the next `queue.md`.
   A tag in square brackets on a line sets that item's model and effort: `[sonnet]`, `[opus high]`, `[haiku low]`. Save them as the item's `model` and `effort`; leave both out when there is no tag (the defaults apply).
2. **Command line feature numbers** (`start.sh 69 58 S19`): same as queue lines with no notes.
3. **Carried over:** items parked or failed last night whose blocker is now resolved (the user answered in `queue.md`, or the fix landed). Otherwise they stay in the report's carried list, not the queue.
4. **The scope fill**, only as the `queue.md` "After these" line allows (default: checks and tests). When there is no `queue.md` and no feature numbers, the fill is the whole queue.

Scope fill (both scopes; suite rows are named by their id, `S19`, VRMS rows by their number): take every `in-progress` feature, plus `planned` features whose `Design it (spec)` box is ticked, and for each its **first unticked box**. A `planned` feature with no spec joins only when the user names it (its row can carry stale intent). The box is eligible only when all of these hold:
- It is a `Build it` milestone, `Verify it` or `Test it` box (commands `/develop`, `/check verify`, `/test`). With "After these: checks and tests", only `Verify it` and `Test it`.
- The feature's `Design it (spec)` box is ticked, or the feature has no decision box and no `needs a decision` tag.
- No note anywhere in the scope says a later decision changes this feature (search for its number, for example "features 36 to 39"), and the drift check raised nothing on it.
- The box is not deferred, dated or waiting on someone or on the user's go ("deferred", "the day before", "after the final defense", "waits for", "wait for", "BMS", "VMMS", "staging", "Azure", "sign off", "when you say go", "your go"). A box held for the user's go runs only when `queue.md` or the command line names it and says go.
- When a `Build it` box or its note says only some milestones can start now (for example "the welinc-auth milestone can start now; the portal milestones wait for S18"), queue only those milestones; the rest stay for a later night.
- A suite row's work in a shared repo follows the same git rules (a `feat/` branch from `origin/development`), and its spec's contract changes are part of the milestone, never a separate push.
- It is not an `Extra skills` or `Polish it` box.

Items named in `queue.md` or on the command line skip the eligibility list above (the words "waits for", "VMMS", "BMS" and the like are for the scope fill only): queue every milestone they name, and only the dependency check at each one's turn decides whether it runs.

Never queue: `/architect`, `/scope` planning, `/check review`, `/document`, `/audit`, any ask first or Azure skill, anything on staging.

**One milestone per item.** A session's context grows with everything it does, so a whole feature in one session gets as slow and costly as one long night. When a queued `Build it` has several unticked milestones (the queue line says "every milestone", names more than one, or names the feature alone), add one queue item per milestone, in scope order: ids like `S19-m1`, `S19-m2`, `box` set to that milestone's line, the queue line's notes, `model` and `effort` copied to each. A milestone whose note says it waits on something that is not done tonight (another milestone, another item) still goes in the queue; at its turn, check whether its dependency finished, and skip it with the reason if not.

Order: `queue.md` and command line items first, then carried items, then the fill (features already `in-progress` before new ones, then scope order). After an item finishes, the feature's next box may join the end of the queue if it is eligible under the same rules.

Write `state.json`, with `runId` set to `$OVERNIGHT_RUN_ID`:

```json
{
  "runId": "2026-11-24-2310",
  "date": "2026-11-24",
  "startedAt": "23:10",
  "until": "07:00",
  "after": "checks and tests",
  "status": "running",
  "queue": [
    { "id": "69-verify", "feature": 69, "box": "Verify it", "command": "/check verify security checks", "source": "queue.md", "notes": "", "model": "sonnet", "effort": "medium", "status": "pending", "repos": [], "branches": [], "commits": [], "ci": [], "risk": [], "result": "", "explain": null }
  ],
  "drift": [],
  "decidedForYou": [],
  "needsYou": [],
  "blocked": [],
  "stashes": [],
  "syncEdits": [],
  "pauses": []
}
```

Item `status`, exactly one of: `pending`, `running`, `done`, `parked` (needs the user), `failed` (red after one `/debug` pass), `skipped` (dirty repo, out of time, not eligible). No other words: `start.sh` treats anything else as finished, and marks an item it finds still `pending` or `running` after its session as `failed`. Save `state.json` after every item and every notable event. If `state.json` exists with `status` `running`, it is this run cut off mid way (`start.sh` files older ones as halted): resume it instead of building a new queue. An item found `running` at start was cut off (crash or usage limit): add a `pauses` entry and redo it from the top, reusing its branch.

Start `runs/<id>/notes.md` with what preflight found that the item sessions need: which stacks were up, which repos were dirty and skipped, the branches that already exist for tonight's features.

Then write the report's header, **Plan** and **Drift** sections right away, so a run that dies early still leaves something to read.

## Step 2: Work each item

For each `pending` item, in order:

1. Check the time against `until`. Past it: mark the rest `skipped` ("out of time") and go to Step 3. In `--one` mode, mark them skipped, save `state.json` and exit; the close out runs in its own session.
2. Read `runs/<id>/notes.md` first if it exists: earlier sessions tonight left what they learned there (slow commands, a container that needed a restart, which branch a later item builds on, a test that is flaky). Trust it over rediscovering.
3. Set the item `running` and save. Invoke its skill with the Skill tool (`develop`, `check` with `verify ...`, `test`) and follow it fully, with the overrides below and the user's notes from `queue.md`.
4. Before calling it done: `npm run lint` and the build in every repo it touched (`build:local` in the two frontends, plus `npm run typecheck` in web-vrms). For backend changes, restart the container first; after a Prisma schema change, run `docker exec welinc_vrms_backend npx prisma generate` and restart.
5. Green: commit (see Git), tick the box in the scope the way the skill says, set the item `done`, and record branches, commits and the checks that passed with counts ("lint ok, build ok, 42 tests passed").
6. **Explain it** for the morning, in the item's `explain` (for every item that changed anything, done, parked or failed). The reader is the user over breakfast: a lead dev who did not watch, wants to know what changed and why, and will check it before pushing. Plain words, no jargon without a short gloss:
   - `did`: 3 to 6 sentences: what you built or checked, how it works now, and what is different for someone using the app.
   - `why`: the spec, acceptance criterion or note that drove each main choice.
   - `readFirst`: the 2 to 4 files that matter most, each with one line on what to look for.
   - `howToCheck`: 2 to 4 steps the user can follow in a couple of minutes (a page and what they should see, or a command and its expected output).
   - `screenshots`: paths of any screenshots worth seeing (in `runs/<id>/shots/`).
7. Red: run `/debug` once on the failure. Still red: don't commit. `git stash push -u -m "overnight <date> <item id>"`, record the stash, set the item `failed` with the last 20 relevant lines of output, and move on.
8. **Risk flags** for each branch touched, recorded in the item's `risk`: changes in `welinc-auth` or `welinc-web-portal` (shared), `schema.prisma` or a migration, auth, sessions, roles, permissions, guards, uploads or storage code, `.github/workflows/`, Dockerfiles or compose files, `infra/`, new or upgraded dependencies, or a feature tagged `· GA`. Each flag names the files. These are the diffs the user should read closely.
9. **Leave notes** for the sessions after you: append at most 5 lines to `runs/<id>/notes.md` under `## <item id>`, only facts a later item can use (a command and how long it takes, a fix for the environment, the branch and base you created, a file the next milestone must extend, a check that needs a restarted container). No diary, no summary of the work (that goes in `explain`). Facts that would help every future run too, add to `drift` as `proposed` with "AGENTS.md candidate" so `/sync` or the user can keep them.

**Questions (overrides every skill's "ask the engineer"):** nobody can answer, and `AskUserQuestion` is blocked.
- Answered in `queue.md`: use that answer.
- Small and easy to undo (a name, a test file layout, a default the skill itself marks recommended, which seed account to use): take the recommended option and add it to `decidedForYou` with how to undo it.
- Load bearing (anything `/develop` would route to `/architect`, a spec or scope change beyond ticking boxes, a product or UX direction, a cross repo contract, a new dependency, a security trade off): **park** the item. Write the question into `needsYou` as a decision panel (2 to 4 options, one marked recommended with a one line why) plus the `queue.md` line that would resume it with that answer. Leave no uncommitted work behind: commit what is green, stash the rest (`git stash push -u -m "overnight <date> <item id> parked"`, recorded in `stashes`). Then set the item `parked` and move on. Never decide these for the user.

**Git (overrides "ask before any git write" for local operations only):**
- Service repos: work on `feat/<feature-slug>` (or reuse the feature's existing local branch), created from the up to date remote: `git switch -c feat/<slug> origin/development`. When the queue line names another base (a local branch this work builds on, such as an unmerged feature it needs), branch from that instead and record the base in the item's `branches` and the report, because its PR has to wait for that branch's. Tests for code that is already merged go on `chore/test-<slug>` the same way. Never check out or commit on `development` or `main`.
- Workspace repo (scope ticks, drift fixes, `verify.md` ticks, `/sync` edits): one branch for the night, `docs/overnight-<date>`, created with `git switch -c docs/overnight-<date> origin/main` the first time; later sessions switch to it (`git switch docs/overnight-<date>`). If the workspace is dirty, don't branch or commit there: leave the edits uncommitted and list them in the report.
- Commit only what landed green, by explicit path (never `git add -A` in a repo that had other changes). One line Conventional Commit subject, no body, **no** `Co-Authored-By` trailer (project rule: attribution none).
- Never: push, pull without `--ff-only`, merge, rebase, reset `--hard`, amend, delete branches, drop stashes. The guard blocks them anyway.

**Running the app:** use `browser_snapshot` to check structure and text; take a screenshot when the look matters (layout, colors, a phone width), saved to `runs/<id>/shots/<item id>-<page>-<width>.png`. Look at as many as you need to get it right; you are in a fresh session per item, so they don't pile up.

**Diagrams and images:** export PNG only (no SVG, no DBML); the sources (`.puml`, `.drawio`) can export SVG later. Sign in only with seeded `@welinc.com` accounts; never type a real email address anywhere (local auth sends real mail). Steps in a `verify.md` that need staging, another group, a real person or a real device: mark them "left for you" and verify the local steps.

**Usage:** `start.sh` checks your usage before every step and waits while the 5 hour window is at 95% or more, so never stop or slow down on your own because of usage.

**Halt the whole run** (set `status` to `halted`, write `haltReason`, go to Step 3) when: auto mode stops allowing actions (several blocks in a row, or Claude Code starts asking for permission), three items in a row fail for the same cause (usually the environment, not the code), Docker or the databases go down and won't come back, or you are about to do something the overrides forbid.

## Step 3: Close out

1. **Sync.** If any item is `done`: run `/sync` once for the night's changes and commit its edits on the workspace branch (or leave them uncommitted if the workspace is dirty). Record in `syncEdits` which file and line each edit touched and which branch it describes, so the user can drop the lines for a branch they reject.
2. **Local CI.** For every branch with green commits, read that repo's `.github/workflows/ci.yml` and run each `run:` step of the jobs that would run on a PR into `development` (lint, typecheck, build, tests, `audit-ci`, and the like), in the order CI runs them. Skip `npm ci` (the packages are installed already; say so) and steps that need secrets, a GitHub only action (gitleaks, uploads) or a service you don't have locally: list those as "CI only". Record each step's result in the item's `ci`. A red step moves the branch from **Ready to push** to **Not ready yet**, with the output.
3. **Queue file.** Rewrite `queue.md` to only what is left, like the handoff: keep the user's unfinished lines with their notes, add parked items with "carried from <date>: <what it needs>", drop finished ones. Nothing left: delete `queue.md`.
4. **Report.** Read `runs/<id>/notes.md`. Run `node agents/vrms/overnight/runner.mjs changes` and `node agents/vrms/overnight/runner.mjs usage` first. Then write the report from `report-template.md` into `docs/_private/vrms/overnight/$OVERNIGHT_RUN_ID.md`: each item's **What changed** block comes from its `explain` plus its commits and files in `runs/<id>/changes.md` (git is the truth: if they disagree, say so), and the **Usage** section is the table as printed. Facts only: every "passed" comes with the command and its count; say plainly what failed or was skipped.
5. **Publish** it as a private Artifact page for the phone: load the `artifact-design` skill first, build a simple HTML page from the report (each item a card you can open for its What changed block and screenshots), publish it, and put the link at the top of the markdown report. If the publish is refused or fails, the markdown file is the report; say so in the notification.
6. Set `status` to `finished` (or keep `halted`) in `state.json`.
7. Send one `PushNotification`: "Overnight run finished: N done, N need you, N failed. Report: <link or path>". This is the only notification of the night, except a halt, which also sends one.
8. Finish with a short message: the counts, the report path and link, and the first thing to look at in the morning. In session mode the session then stays open and idle; that is the end of the run.
