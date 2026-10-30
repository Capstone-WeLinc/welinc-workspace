# 0012. Rationale: configurable settings and modules

The decision record for [index.md](index.md). `/develop` does not read this file.

## Context

VRMS tunables live in code. Spec 0007 gathered the knowledge base's seven numbers into one `KNOWLEDGE_SETTINGS` object in backend-vrms on purpose, so a settings feature could replace a single file. Every change today needs a developer, a build and a deploy, and nobody can tell afterwards who changed a value or why. Features 42 (deadlines) and 43 (stuck and stale alerts) each bring more Admin configurable values, and feature 40 brings Admin managed lookup lists.

Some parts of VRMS should also be optional. Jira calls AI suggestions optional, AI costs Gemini calls, and the Python analytics and AI service (retired later by feature 3) can be unreliable. The web app calls that service directly through the gateway, the service checks no JWT, and its sync re-embeds every issue every 30 seconds. So hiding a button would not stop the spend. The knowledge base (spec 0007) is woven into the repair flow: the form's picker and auto fill, the "What fixed it" rule on the move to For verification, and issue categories, which double as the form's System list.

Spec 0011 just built an Admin editable permission matrix: a code catalog, stored rows, a version row each replica compares on every checked request, and a change table. It left its editing screen to this feature, and the scope decided on one Settings hub holding lookup lists, thresholds, modules and role permissions. VRMS runs one or two backend replicas on Azure Container Apps against one shared Postgres server (spec 0008), with a deadline at the end of November 2026.

## Options considered

### Storage

**Option 1: code catalog plus key and value rows holding only changed values (chosen).** The catalog defines each key's type, default, range and unit; `app_settings` stores a row only when an Admin changes a value.
- Pros: a new setting is one catalog line with no migration; a better default in code reaches every untouched install; "reset to default" is a row delete; same shape as the matrix.
- Cons: Json values, so Postgres can't check types; the service is the only gate.

**Option 2: one wide row, a typed column per setting.**
- Pros: Postgres enforces types and checks; easy to read in Studio.
- Cons: every new setting (features 42, 43 and later) needs a migration; defaults live in two places (column default and code).

**Option 3: one Json document row.**
- Pros: one read loads everything; trivial schema.
- Cons: two edits to different keys collide; the change log has to diff a blob; no per key history.

**Option 4: a feature flag service (self hosted Unleash or Flagsmith).**
- Pros: mature UI, SDKs, streaming updates, per user targeting.
- Cons: another container and database to run and secure; it covers flags, not typed thresholds or lookup lists; no link to the CASL permission matrix; far more than three switches need.

### Smaller calls made in the interview

- **Row per key with startup backfill** (the matrix way) vs **changed values only**: changed values only, because a backfilled row freezes the first default forever, while settings should follow better defaults.
- **Propagation**: a version row read in the same query as the matrix version, vs Postgres `LISTEN/NOTIFY` (real time, but a second database client and reconnect handling next to Prisma), vs a 30 second in memory cache (what flag SDKs do by default, but an Admin turns AI off and it keeps working for half a minute). The guard already pays one read per request, so instant propagation adds no round trip.
- **Module gating**: removing a module's permission keys vs a separate `@RequireModule` guard. Removing keys reuses the guards, `<Can>`, nav and the 403 refetch that spec 0011 built; a separate guard means tagging every route and screen twice.
- **Change log**: a new `SettingChange` table vs generalising `AuditLog` (its `repairTicketId` is required and the ticket timeline reads it) vs folding `PermissionChange` into a shared table (reworks a just shipped table and endpoint). The hub merges the two tables at read time instead.
- **Python service**: reading the switch from Postgres vs leaving it to feature 3. The read is about 30 lines on a connection the service already has, and it is the only way the AI switch actually stops Gemini spend before feature 3.
- **Issue categories**: reading on `config.read` and writing on a new `lookups.manage`, vs reusing `settings.manage` (Chief Mechanics would lose category editing) vs exempting category routes from the module check (the keys would then lie about what they gate).
- **Thresholds**: only the four business values are editable. The similarity scores and the candidate limit are tuning knobs an Admin can't judge and can break search, so they stay code constants.
- **Dependencies**: built now, unused, so feature 3 only declares AI requires the knowledge base, instead of building the save rule, cascade and dialog inside an already large feature.
- **Thresholds after a change**: nothing to recompute. Typical costs, repeats and suggestion groups are all computed when read (`knowledge-suggestions.service.ts` groups inside `list()`), so a new value shows on the next page load.
- **AI date range on resume**: raised during the interview. It belongs to feature 3's embedding pipeline (incremental embedding plus a catch up window), not to a sync that feature 3 replaces; recorded as a follow-up in index.md.

## Rationale

The matrix pattern from spec 0011 is the deciding force. The team just built and verified a catalog, stored values, a per request version check and a change table, and the settings problem has the same shape: a few dozen typed values, changed rarely, read on almost every request, needing an audit trail and instant effect on one or two replicas. Copying that shape costs nothing to learn or operate, and with a five week deadline that beats any option bringing new infrastructure. A flag service would be the right call with many teams, per user rollouts or experiments. VRMS has none of these, and it would still leave thresholds and lookup lists to build by hand.

Storing only changed values is where this departs from the matrix, on purpose. Permission defaults are a security posture, and freezing them is a feature. Threshold defaults are best guesses that will improve, and a row per key would pin every install to the first guess. Json values give up database type checks, but the catalog check on save plus "ignore and warn" on read covers the hand edit case, and avoiding a migration per setting matters with features 42 and 43 queued right behind this one.

Gating modules through permission keys makes "off" real at almost no cost: the server refuses through the same guard, the web hides through the same `<Can>` and nav, and an open tab learns about it through the same refetch. Reaching into the Python service is the one place that crosses repos. It is justified because the AI switch is mostly about spend, the spend happens in that service, and feature 3 removes the coupling when it retires the service.
