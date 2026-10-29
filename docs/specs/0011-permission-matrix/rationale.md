# 0011. Permission matrix: rationale

The decision record for [index.md](index.md). `/develop` builds from the index; this file explains why.

## Context

VRMS has roles but no single place that says what each role may do. Rights are scattered: 30 routes in backend-vrms carry their own `@Roles()` lists, the knowledge base has its own `KNOWLEDGE_READERS` and `KNOWLEDGE_EDITORS` (spec 0007, marked as interim), and `RepairsService.isMechanic()` decides nine different things at once (which tickets you see, whether costs show, which status moves you may make, whether you may unlock). web-vrms repeats these as `RequireRole`, `KNOWLEDGE_EDITOR_ROLES`, `isMechanicRole` and a role switch in the nav, in 18 files. The two sides drift independently, and any new role (Chief Mechanic already exposed this) means touching every list.

Jira WL-109 asks for one matrix of role against action, enforced on every protected endpoint with 403, mirrored in the UI, defined in one place so roles can change without code rewrites, with allowed and denied tests per role. The team chose on 2026-10-29 that an Admin edits the matrix from the Settings hub (feature 52), that the roles stay fixed, that some rights are locked so nobody locks themselves out, and that every change is logged. Many later stories depend on it: Chief Mechanic oversight (WL-104), mechanic status updates, verification, Admin override, transfers.

Forces: backend-vrms runs up to 2 replicas on Azure Container Apps (spec 0008), so anything cached in memory is per replica. Accounts and roles live in welinc-auth (spec 0009), which is shared with the VMMS and BMS groups; VRMS can't make welinc-auth read its tables. One welinc-auth account can hold roles in several systems, and deactivate, delete and passwords act on the whole account. Spec 0009 left two items here: welinc-auth's user list and change record let any Admin of any system read any user, and the unused `RefreshToken` table. The deadline is the end of November 2026, and the team is a student capstone team, so the design must be learnable and testable.

Not deciding means each new Slice 1 feature invents its own role check, the UI keeps showing buttons the server refuses, and Chief Mechanic rights stay hardcoded.

## Options considered

### Option 1: Constant matrix in code

A typed matrix object in backend-vrms, shared with the web app by copy, checked by a guard.

**Pros**:
- Simplest to build and test; no tables, no cache.
- Meets WL-109's "one place".

**Cons**:
- Contradicts the team's choice of an Admin editable matrix: every change needs a deploy.
- The web copy can drift from the server copy.

### Option 2: Code catalog, database grants, own small guard

Keys, labels, locks and defaults in `catalog.ts`; each role's on or off in `role_permissions`; a `@RequirePermission` decorator, a global guard and a `can(user, key)` helper. Ownership and hidden fields stay as hand written code in services.

**Pros**:
- About 150 lines, no new dependency, fits on/off cells exactly.
- Typos in keys fail the build; Admin edits need no deploy.

**Cons**:
- Ownership ("assigned to me"), hidden fields and every later conditional rule stay as scattered `if` blocks, so the `isMechanic` pattern survives under a new name.
- The web app gets only a key list, so conditional buttons (Start work only on my ticket) are copied by hand.

### Option 3: Code catalog, database grants, enforced through CASL

The same catalog and grants as option 2, but each key maps to CASL rules. The server builds an ability per user, uses `accessibleBy` for scoped queries and `permittedFieldsOf` for hidden fields, and returns per ticket answers (`can.work` and so on); the browser builds a CASL ability from the granted keys and uses it with `@casl/react`.

**Pros**:
- Ownership and hidden fields become rule conditions, read from one factory, replacing four copies of the `isMechanic` branch.
- The browser never guesses: it reads the server's keys and the server's per ticket answers.
- Later features (19, 21, 23, 30) are one rule each; separation of duties for verification is expressible.
- A known library the other groups can adopt by copying the pattern, without depending on us.

**Cons**:
- A new library and concepts to learn (rule order, subjects, field rules).
- `@casl/prisma` with Prisma 7 must be proven first.
- More moving parts than a plain key check.

### Option 4: Everything in the database, including the catalog

Keys, labels and groups in a `Permission` table, grants in a join table.

**Pros**:
- Fully data driven; labels editable without a deploy.

**Cons**:
- A typo in a route's key fails only at runtime, as a wrong deny or allow.
- Pays off only with custom roles or plugins, which the team ruled out.

## Rationale

Option 3 is chosen. The forces that decide it are the scattered ownership checks and the drift between server and UI. Option 2 would centralize the yes or no, but the hard part of VRMS authorization is not "may a Mechanic change status" but "may this Mechanic change this ticket", and "which fields may this role see". Those are conditions, and under option 2 they stay as hand written branches in services and as hand copied checks in the web app, which is exactly what WL-109 is meant to end. CASL turns them into data next to the keys, and the browser reads the server's own answers (keys, plus per ticket flags) rather than a hand copied check, so "the UI hides what the server blocks" holds by construction instead of by discipline. The rules themselves stay on the server because their conditions are written against Prisma relations, which the ticket JSON in the browser doesn't match; the cross check caught that sending them would make buttons silently wrong. The engineer also wanted the library to carry later rules (photos, verification, transfers), and every one of those is a condition CASL expresses directly. The cost is a learning curve and one compatibility check, both bounded: the first build step proves `@casl/prisma` on Prisma 7, with plain `@casl/ability` as the fallback.

The catalog stays in code (option 4 rejected) because a key is useless until code checks it, so its label and default belong with that code, and a typed list turns a misspelled key into a build error instead of a silent wrong answer in production. The database holds only what the Admin changes. A startup backfill that only inserts and deletes delivers new keys without ever overwriting an edit, which the team confirmed was the safety concern. Locks are limited to `users.manage` and `permissions.manage` because those are the two rights whose loss can't be undone from the UI; the team chose to leave the BRD's "mechanics never see costs" as an editable default, and the change log is its guard.

For freshness, each checked request reads a one row version counter (a primary key lookup) and reloads the grants when it moved. That costs one tiny query, works across 2 replicas with no new infrastructure, and means a revoked right stops working on the next request, which a time based cache could not promise. The counter also makes the PATCH conflict check exact, which the newest `updatedAt` could not (millisecond ties, and it moves backwards on deletes). Startup only inserts, so an old and a new image running side by side during a deploy never undo each other. Failing to a last known matrix, never to "allow", keeps a database blip from either opening the API or taking it fully down. On welinc-auth, scoping admin endpoints by the caller's system closes spec 0009's gap with the smallest change to the shared repo. The shared account rules came from the engineer's own reasoning: deactivate stays available because WeLinc is one company and urgent lockouts must not wait on another group's admin, while delete (no undo) is blocked. Setting a password and changing the email stay allowed for any account in the VRMS scope, per the engineer, except an account that is an admin in another system: there the cross check showed it would let a VRMS admin take over another group's admin, so those two answer 403 and a reset code (which only the owner can use) is the way. Releasing open tickets on deactivate replaces spec 0006's hard block, because the engineer wanted fast lockouts, and the "Inactive mechanic" badge covers deactivations VRMS never sees.

### Current checks this replaces (inventory, 2026-10-29)

| Where | What | Count |
|---|---|---|
| backend-vrms controllers | `@Roles()` on repairs, config and knowledge routes | 30 routes |
| `knowledge-actor.ts` | `KNOWLEDGE_READERS`, `KNOWLEDGE_EDITORS`, `isKnowledgeEditor()` | used in 3 services, 8 calls |
| `repairs.service.ts` | `isMechanic()` | 9 calls: list, summary, detail, status, steps, costs, unlock |
| web-vrms | `RequireRole`, `KNOWLEDGE_EDITOR_ROLES`, `isKnowledgeEditor`, `isMechanicRole`, role switch in `navItems.ts` | 18 files |
| welinc-auth | `@Roles(ADMIN)` on user endpoints, not scoped by system | 9 routes |
| web-vrms `useUserActions.ts` | deactivate blocked while a mechanic has open tickets (spec 0006 AC-16) | 1 flow |
