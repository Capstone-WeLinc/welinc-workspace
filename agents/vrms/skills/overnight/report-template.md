# Overnight report shape

Write the report in this order. Leave out a section that has nothing in it, except **Needs you** and **Ready to push**, which always appear (say "Nothing" when empty). Keep it short enough to read on a phone over breakfast.

```markdown
# Overnight run · <date> · <start> to <end>

<Artifact link, once published>

**<N> done · <N> need you · <N> failed · <N> skipped** <· halted: reason> <· paused N times (usage limit or crash), resumed>
<Defense warning if a defense is within 24 hours.>

## Needs you
One block per parked item, proposed doc edit or blocked action, most important first:

### <feature number and name>: <the question in one line>
<Two or three lines of context: what the skill was doing, what it found, why this is your call.>
1. **<option> (recommended)**: <one line why>
2. **<option>**: <one line trade off>
To resume, add to `queue.md`: `<feature> <the answer in plain words>`

## Ready to push
Branches with green commits whose local CI passed. Nothing has been pushed.

| Repo | Branch | Commits | Local CI | Read closely |
|---|---|---|---|---|
| welinc-backend-vrms | feat/<slug> | 3 | lint · build · 42 tests · audit ok (gitleaks: CI only) | `prisma/schema.prisma`, new migration |

Branches with no risk flags are safe to skim. For each one you're happy with:
1. Optional: `/code-review high` on the branch for a fresh look (start with the flagged ones).
2. `git -C <repo> push -u origin <branch>`
3. `/document pr` (it opens the PR into `development`).

## Not ready yet
Branches with commits whose local CI went red: the step, its last relevant lines, and what to try.

## Drift found
- **Fixed** (proof included): <box ticked> because <merged commit or file>.
- **Proposed** (your call): <file and line> says <x>, but <evidence>. Suggested edit: <new wording>.
- **Handoff**: item <N> looks done (<evidence>). Suggested edit: <strike it / new wording>.

## What happened
One short block per item, in run order:

### <item id> · <done | parked | failed | skipped> · <minutes> · from <queue.md | command line | carried | scope>
- Box: `<the scope box>` → <ticked | still open>
- Did: <one or two lines>
- Evidence: <commands and counts; for verify, each acceptance criterion with pass or fail>
- <For failed: the last relevant lines of output and the stash name.>

## Decided for you
Small choices taken on your behalf, each easy to undo:
- <item>: chose <option> over <option> because <why>. Undo: <how>.

## Sync edits
What `/sync` changed and which branch each line describes, so you can drop the lines for a branch you reject:
- `<file>`: <line> → describes <repo> `<branch>`.

## Left for you
Steps the run could not do by design (staging, another group, a real sign in, a dated box, a design), with the file and line they come from.

## Stashed work
- `<stash name>` in <repo>: <what is in it>. Look with `git -C <repo> stash show -p 'stash^{/<item id>}'`.

## Uncommitted
Edits left uncommitted because a repo was dirty when the run started, with the paths.

## Queue for next time
What `queue.md` holds now (or "queue.md deleted, nothing left").

## Suggested order this morning
1. Answer **Needs you** by adding lines to `queue.md`.
2. Accept or reject the **Proposed** drift edits.
3. Check **Not ready yet** and the stashes.
4. Push the **Ready to push** branches you're happy with, flagged ones after a close read, then `/document pr`.
```
