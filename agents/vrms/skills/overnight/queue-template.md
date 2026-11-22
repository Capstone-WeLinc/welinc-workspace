# Bedtime queue shape

The user writes `docs/_private/vrms/overnight/queue.md` before leaving. Everything in it is optional. Plain words are fine; the run reads intent, not syntax. Example:

```markdown
# Tonight

1. 69 verify [sonnet], skip the GitHub checks, only the local ones
2. 54 account changes view [opus high]: put it in the Users page side panel, not a new page; newest first; 20 per page
3. 58 tests
4. Paper diagrams [sonnet]
   Goal: the chapter 4 diagrams, for the capstone panel (not developers).
   Done when: each has its source and a PNG, and the panel can read it in 30 seconds.
   Rules: plain names (no class or file names), at most 12 arrows, one sequence per flow, at most 15 steps each.
   You may decide: file names, layout, colors. Park: anything that changes what the system does.

After these: checks and tests
Until: 07:00
```

A short line is enough for a feature whose spec says it all. For anything else (docs, diagrams, a page with taste involved), the four lines under item 4 make the difference between a first try you keep and one you redo: what it is for and who reads it, how you'll judge it done, the rules, and what it may decide.

Rules the run applies:
- Each numbered line is one item, run in that order. A feature number alone (`69`, or `S19` for a suite row) means "its next open box".
- A tag in square brackets picks the model and effort for that item: `[sonnet]`, `[opus high]`, `[haiku low]`. Without one, building (`/develop`) runs on Opus at medium effort and everything else on Sonnet at medium effort. Sonnet is plenty for verify, tests, docs and diagrams; save Opus for builds and tricky debugging.
- Text after the feature is the user's answers and limits for that item. Follow it, and don't park a question it already answers.
- `After these:` says what happens when the list is done:
  - `stop`: close out and finish.
  - `checks and tests` (the default when the line is missing): keep going with eligible `Verify it` and `Test it` boxes from the scope, no new builds.
  - `anything eligible`: keep going with every eligible scope box, builds included.
- `Until:` is the same as `--until`; the command line wins if both are given.
- At close out the run rewrites this file to only what is left (unfinished lines keep their notes; parked items come back as "carried from <date>: <what it needs>"), and deletes it when nothing is left.
