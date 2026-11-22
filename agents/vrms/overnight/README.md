# Overnight runs

Lets Claude Code keep working through the VRMS scope while you sleep or are out, then leaves you a morning report. It builds, verifies, tests and commits on local branches. It never pushes, opens a PR, touches Azure or staging, or sends anything outside this machine. It needs none of your passwords: it signs in with the seed accounts in `docs/integration/seed-accounts.md`.

## Before you leave

1. Plug the machine in, start Docker Desktop, and run the shared and VRMS stacks if they aren't up.
2. Commit or stash your own work. The run leaves a repo alone if it has changes that aren't its own.
3. Optional: write `docs/_private/vrms/overnight/queue.md` with what you want done and any answers up front (shape in `.claude/skills/overnight/queue-template.md`). Without it, the run picks from the scope.
4. Once: in Claude Code's `/config`, turn on **Push when actions required** and **Push when Claude decides**, so the Claude app on your phone can reach you.
5. Start it from a terminal (Git Bash on Windows) and leave it open:

```bash
bash agents/vrms/overnight/start.sh                  # queue.md first, then checks and tests from the scope
bash agents/vrms/overnight/start.sh 69 65 58         # only these features
bash agents/vrms/overnight/start.sh --until 07:00    # no new item after 7 am
bash agents/vrms/overnight/start.sh --plan           # dry run: shows the queue and drift, does nothing else
bash agents/vrms/overnight/start.sh --fresh          # a clean session per item, waits out usage limits (no phone view)
```

Session mode (the default) is one long session you can watch and stop from the Claude app. `--fresh` runs each item in its own headless session, which keeps item 6 as sharp as item 1 and retries after a usage limit, but you can't watch it from the phone; progress goes to `runner-<date>.log`.

## In the morning

Read `docs/_private/vrms/overnight/<date>.md` (the run also publishes it as a private page and sends a push with the link):
1. **Needs you**: answer by adding lines to `queue.md`; the next run picks them up.
2. **Drift found**: accept or reject the proposed doc edits.
3. **Ready to push**: local CI already passed; read the flagged files closely, then push and run `/document pr`.

`queue.md` works like the handoff: one file, rewritten at the end of each run to only what is left, deleted when nothing is.

## What keeps it safe

- `settings.json` (loaded only by `start.sh`, never in your normal sessions): auto mode, deny rules for push, PRs, Azure and 1Password, extra auto mode rules, and `denyInsteadOfPrompting`, so a permission prompt turns into a "no" instead of a wait.
- `guard.mjs`: a hook that checks every tool call. It blocks every form of `git push` (including `git -C dir push`, which a deny rule misses), commits on `main` or `development`, history rewrites, writes to GitHub, outside hosts and staging, reads of `.env` and `infra/private/`, edits to the VMMS and BMS repos and to its own files, and questions to you (the run decides small things and parks big ones). Its Stop hook keeps the session going while the queue in `state.json` has items, up to 40 times.
- `guard.test.mjs`: `start.sh` refuses to start unless these pass (`node --test agents/vrms/overnight/guard.test.mjs`).

Change these files only in a normal session, then run the tests again.
