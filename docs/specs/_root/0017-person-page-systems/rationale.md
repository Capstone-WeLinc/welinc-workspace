# 0017. Person page shows the whole person: rationale

The decision record behind [index.md](index.md). `/develop` doesn't read this file.

## Context

- **The problem.** The portal's person page (`welinc-web-portal/src/pages/admin/people/PersonPage.tsx`) loads a person for one system (`GET /auth/admin/users/:id?system=`). When the person isn't in that system, welinc-auth answers 404 and the page shows "This person isn't in VRMS, or the account no longer exists." with no name or email. It happens when a suite admin opens a person with no role from All people (the page falls back to VRMS), switches the toolbar dropdown to another system, or follows an old link, and when an admin of two or more systems (seed `multi.admin@welinc.com`, VRMS and VMMS admin) switches to a system the person isn't in.
- **What welinc-auth allows today.** A suite admin may leave out `system` and gets every role (spec 0013 AC-17). A system admin must pass a system, and gets only that system's roles plus `otherSystems` codes (spec 0011). There is no last sign in column, the list sorts by name only and filters by one status.
- **The forces.** The design is already approved: the S18 rounds produced `People8` (Round 8), the People page as a list beside the person with section tabs, and your picks are recorded (Nov 18 handoff). S18's shell (sidebar, app shell, base components) isn't built yet. welinc-auth is shared with VMMS and BMS, so its changes must stay additive. The defenses are close (final by Dec 20).
- **What not deciding costs.** The dead end stays, and S19 would be built on a "pick a system first" page that the approved design has already replaced.

## Options considered

### Option 1: System tabs on the person page

Keep the person page, replace the toolbar dropdown with one tab per system the person is in, and open on a system they're in. This was the scope row's first wording and the first draft of this interview.

**Pros**: smallest change to today's page; no new list.
**Cons**: still "a person inside one system": account wide facts and actions repeat per tab; contradicts the approved `People8`; admins of two systems still get two separate lists.

### Option 2: The approved `People8` page (chosen)

The list beside the person; section tabs (Overview, Access, Signed in devices, Activity); every system a row in Access; one welinc-auth read scope for "every system you admin".

**Pros**: removes the dead end by design; matches what you approved on Nov 18; one list across an admin's systems; shares the app shell with S20 and S21.
**Cons**: a large portal change; waits on S18's shell; welinc-auth gains a third scope kind.

### Option 3: Fix in place

Keep today's page and dropdown, but on a 404 jump to a system the person is in.

**Pros**: a day of work.
**Cons**: hides the problem instead of removing it; a no role person still has no system to jump to; nothing of the approved design ships.

## Rationale

- **Why Option 2.** The dead end comes from making the system the first thing you choose; `People8` removes that choice, so the bug can't come back on a later page. It is also the design you already approved, so building anything else would be rework before the defense.
- **Why a read scope and not merging in the browser.** One rule on three read routes ("no system means every system you admin") keeps paging, sorting and grouping on the server. Merging per system pages in the browser breaks keyset paging and sorts. The cross check showed it is simpler as one `systems` list in the scope (one system is a list of one, the suite is null) than as a third scope kind.
- **Why a `group` on the list, decided by the server.** Status filters overlap (an active account can also have a pending deletion), so three status filtered calls would show the same person twice and could not count a group past its first page. The server assigns each person one group and returns the counts.
- **Why committed board copies.** The canvas opens only from one account; copies of the three boards in `boards/` let `/develop` and `/check verify` work from any account. The canvas stays the place to change a design.
- **Why writes still name one system (AC-16).** Every per system safety rule in spec 0013 (last admin, shared account, reauth) keys on the system named. Picking the first shared system keeps all of them working with no auth change; an account scope on writes would reopen them.
- **Why `created_at` at milliseconds (2026-11-23, your pick during `/develop`).** The "Newest first" keyset cursor carries the last row's `created_at` through JavaScript, which drops microseconds, so the next page could skip rows made later in that same millisecond. Rounding the column to milliseconds, as `last_signed_in_at` already is, makes the cursor exact with one `ALTER`. Runner up: page that sort with raw SQL that reads the time as exact text, which keeps the column but adds a second query path for one sort.
- **Why a column for last sign in.** You picked a "Last signed in" sort; sorting a long list by the newest event per person is slow and awkward to page. A nullable column written in the sign in transaction is cheap and keeps the event log as the history.
- **Why role names for systems you don't run.** You chose to see the whole person; the person is already in one of the admin's systems, and `otherSystems` already reveals the system codes, so the extra detail is small and read only.
- **Why build after S18's shell.** Building `People8` on today's components means building it twice; the shell is S18's milestone 3, which S19 needs anyway.
- **Why Needs attention is Locked, Pending, Pending deletion.** Your pick: things an admin can act on now. Inactive gets its own group at the bottom because the board's two groups had nowhere for it.
