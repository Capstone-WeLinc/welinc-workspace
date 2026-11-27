# 0018. Rationale: Roles page and custom roles

## Context

The portal's Permissions page (`welinc-web-portal/src/pages/admin/permissions/PermissionsView.tsx`) shows one system's matrix as a grid: 27 VRMS permissions down, the roles across, a checkbox per cell, a sticky "N changes not saved" bar, a review dialog listing gains and losses per role (a note required when anything is taken away), and the matrix history under the grid. It works for three roles, but you have to scan 81 cells to answer "what can a Chief mechanic do?", and it stops being readable once roles grow. The S18 design rounds (Nov 18) settled a replacement on boards `Roles9`, `DraftMarks`, `SaveBar9`, `Picks8` and `Confirm6`, but left open: saving changes across several roles, the compare view (round 8 dropped "Who can do what"), permission descriptions, a search inside a role, and the flows behind New role, Duplicate, Rename, Edit description and Add people.

Roles are fixed today. Each system's roles live in `welinc-auth/prisma/catalog/<system>.ts`, and `catalog:sync` makes `system_roles` match the files exactly. It deletes a role missing from the file, or refuses (failing `db:deploy`) when someone holds it. No route creates a role. The access token, `/auth/me` and the directory feed carry role codes, and only `/auth/systems` carries names.

Only VRMS has permission keys (`system_permissions`). A map of every role code check across the suite (gathered for this spec) found:
- VMMS gates about 70 handlers with `@Roles(...)` and its web app routes by fixed codes.
- BMS gates its services with fixed role unions (about 76 literals), and its web app maps unknown codes to "Customer Service".
- The shared mobile app branches on `CHIEF_MECHANIC`, and its OAuth client allows only VRMS MECHANIC and CHIEF_MECHANIC.
- VRMS itself filters synced permissions to three fixed roles (`MATRIX_ROLES`), builds its mechanic roster from the codes MECHANIC and CHIEF_MECHANIC (with a database CHECK), labels the chief by code, and falls back to MECHANIC in the web session.

A custom role that nothing downstream understands would sign in and then fail on every screen.

Forces: the deadline (final defense by Dec 20, the Azure credit ends Dec 18); repos owned by other groups that we may only read; your wish for "as much configurable as makes sense" and capstone worthy depth; one save model across the suite (spec 0016: the save bar for changing what exists, a Save button for making something new).

## Options considered

### Option 1: The page only, fixed roles

Build `Roles9` on the three built in roles and leave S21 for later.

**Pros**:
- Smallest change: the portal plus one read route.
- No risk to tokens, VRMS or the other systems.

**Cons**:
- `Roles9`'s Custom section, New role and Duplicate would be dead UI, or redrawn later.
- S21 is a planned GA row; deferring it means designing the page twice.

### Option 2: Custom roles in every system

Let suite admins add roles to VRMS, VMMS and BMS alike.

**Pros**:
- One rule for every system; the page treats all systems the same.

**Cons**:
- VMMS and BMS gate everything by fixed codes, so a custom role there could sign in and do nothing. Fixing that means about 150 changes in repos we don't own.
- No permission keys in those systems means nothing on the page to configure for a custom role anyway.

### Option 3: Custom roles where permissions exist, behaviour by permission (chosen)

Offer custom roles only for systems with permission keys (VRMS today). Move VRMS's role code checks (roster, chief label, audit role, the session fallback) to permissions, with a new key "Can be assigned tickets". Built in roles stay owned by the catalog.

**Pros**:
- A custom role works end to end in VRMS: token, permissions, roster (the mobile app stays for Mechanics and Chief mechanics).
- The VRMS changes are few (about 15 sites) and inside our own repos.
- VMMS and BMS get custom roles for free the day they adopt permission keys.
- "What can this role do?" has one answer, its permissions.

**Cons**:
- The page differs by system (VMMS and BMS read only, People only).
- A roster rewrite in VRMS that must match today's behaviour exactly.

### Option 4: Custom roles that act as their source role

Each custom role remembers the built in role it was copied from, and every system treats it as that role wherever a code is checked.

**Pros**:
- Works in VMMS and BMS without their code changing, if the token carried the base role.
- Little VRMS code to change.

**Cons**:
- Behaviour and permissions disagree: a "Parts clerk" copied from Mechanic would be in the mechanic roster with ticket work switched off.
- Needs a new token field every system must read, a contract change for the other groups.
- Hides the real rule behind an alias that confuses auditors and the papers.

## Rationale

Option 3 fits the forces. Custom roles are only meaningful where a role's permissions are the whole truth, and the role usage map shows that's achievable in VRMS (a handful of checks we own) and not in VMMS or BMS before Dec 20. Option 4 looks cheaper, but it bakes in exactly the problem custom roles should solve: a role whose name says one thing while its switches say another. Option 1 would leave half of `Roles9` drawn but unbuilt and push the hard part past the deadline.

Inside the page, the open board items were settled with you:
- Several roles save in one review, because the API already takes cells for several roles and a related change should land together.
- Descriptions sit under each label (picked on the mockup).
- A small permission filter, because the list will grow.
- The spreadsheet download replaces the compare view you dropped.
- The note stays required on removals and opens itself then, so RC's folded note holds in the common case without weakening the audit rule.

For custom roles:
- Copy from a role, because almost every custom role is a tweak of one.
- Archive on delete, so history keeps a name and no code is reused.
- 20 custom roles per system with unique names, enough for a garage and a guard against near duplicates.
- Suite admins only, the same as permission edits today.
- Built in roles keep their catalog names, so the sync, seeds, papers and other systems never drift.
- Chief mechanic stays built in: it is the one floor lead every garage needs, and with behaviour by permission, built in only means "always exists".
- Add people moves only people already in the system, so it never duplicates S19's Add person.

What we accept: VMMS and BMS see a read only page; built in names can't be changed; four deploys in order. The roster switch is guarded by a parity test.

### Update 2026-11-27: where the Delete dialog's grace count comes from

`/develop` found that AC-25's line "[k] people waiting for deletion keep it" had no source: `peopleCount` leaves deleted people out, the 409 counts only live holders, and the People list never shows soft deleted accounts. Chosen: a `graceCount` on each `roles[]` entry of the roles read, counted the same way as `peopleCount` with the deleted filter flipped. The dialog needs the number before you press Delete, so it can't come from the Delete answer or its 409 (the runner up). A separate route for one number would cost a call and a contract row for nothing. The count holds no names, so it adds nothing a system admin shouldn't see. The same update fixes the `peopleCount` line, which still said Delete counts people in the grace period; AC-25 and the rules line say they don't block, and the built route follows those.
