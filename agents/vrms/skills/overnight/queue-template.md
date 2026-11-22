# Bedtime queue shape

The user writes `docs/_private/vrms/overnight/queue.md` before leaving. Everything in it is optional. Plain words are fine; the run reads intent, not syntax. Example:

```markdown
# Tonight

1. 69 verify, skip the GitHub checks, only the local ones
2. 54 account changes view: put it in the Users page side panel, not a new page; newest first; 20 per page
3. 58 tests

After these: checks and tests
Until: 07:00
```

Rules the run applies:
- Each numbered line is one item, run in that order. A feature number alone (`69`, or `S19` for a suite row) means "its next open box".
- Text after the feature is the user's answers and limits for that item. Follow it, and don't park a question it already answers.
- `After these:` says what happens when the list is done:
  - `stop`: close out and finish.
  - `checks and tests` (the default when the line is missing): keep going with eligible `Verify it` and `Test it` boxes from the scope, no new builds.
  - `anything eligible`: keep going with every eligible scope box, builds included.
- `Until:` is the same as `--until`; the command line wins if both are given.
- At close out the run rewrites this file to only what is left (unfinished lines keep their notes; parked items come back as "carried from <date>: <what it needs>"), and deletes it when nothing is left.
