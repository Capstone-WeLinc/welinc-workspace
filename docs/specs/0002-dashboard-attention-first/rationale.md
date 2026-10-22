# 0002. Attention first dashboard: decision history

Build spec: [index.md](index.md).

## Context

The dashboard is the first page every user lands on, and `design.md` says every screen must answer "what needs my attention?" first. Today it doesn't. The admin view (`AdminDashboard.tsx`) opens with a pipeline bar, then spend cards and two export buttons, so an overdue ticket or one waiting for sign off is never surfaced. The mechanic view (`MechanicDashboard.tsx`) has status tiles and a list, but overdue tickets show only as a banner and the list is sorted by last update, not urgency. Both views are built from inline styles and legacy classes (`premium-card`, `summary-card`, `timeframe-pill`) that the UI refresh is retiring.

Scope feature 10 asks for "open, overdue and waiting tickets up top", but "waiting" was never defined, and `/develop` stopped on it. The data puts limits on the answer. `GET /vrms/repairs` returns the active statuses (`PENDING`, `IN_PROGRESS`, `FOR_VERIFICATION`), scoped to the mechanic's own tickets for a mechanic. `GET /vrms/repairs/history` returns `COMPLETED` and `CANCELLED`. `targetDueDate` is a nullable `timestamptz` column. Priority is **not** stored in the database (it exists only as a frontend type), and no column records when a ticket entered `FOR_VERIFICATION`. Costs are returned to non mechanics only.

The UI refresh phase is built `· Facade`: pages restyle on the data they already have, with no backend change. Other forces: the admin dashboard pulls every active and history ticket (limit 10000) plus the audit log every 15 seconds, and the audit log is never shown. The spend timeframe switch labels its `1y` option "6M". The role type also holds `CUSTOMER_SUPPORT` and `OPERATIONS`, who fall into the admin view by default, and who may see costs is feature 5's decision (permission matrix), not this one.

## Options considered

### Option 1: Fix in place, restyle only

Swap the legacy styles for spec 0001 components and keep the current layout and content: pipeline first, spend, exports; mechanic tiles as today.

**Pros**:
- Smallest change; no new behavior to verify.
- Nothing users rely on moves.

**Cons**:
- The admin page still never answers "what needs my attention?", which is the reason feature 10 exists.
- Overdue stays a banner for mechanics and absent for admins.

### Option 2: Attention first rework on existing data (Facade)

Put attention tiles and a Needs attention list at the top of both views, derived on the client from the lists the page already loads. Keep the pipeline and spend below for admins, drop the exports and the unused audit fetch. No backend change.

**Pros**:
- Answers the design principle directly, with the data on hand.
- Fits the UI refresh's Facade approach and needs no migration.
- Removes dead traffic (the audit log) and duplicate report paths.

**Cons**:
- Counts are computed in the browser from up to 10000 rows per list, which won't scale forever.
- "Waiting since" is approximated by `updatedAt`.

### Option 3: Backend summary endpoint plus rework

Add `GET /vrms/repairs/summary` that returns the counts and the attention list, and a `verificationRequestedAt` column for exact waiting times.

**Pros**:
- Exact waiting times, cheap payloads, counts that scale.
- One source of truth for counts other pages could reuse.

**Cons**:
- Breaks the Facade approach: a migration, a new endpoint and a cross repo change, which `AGENTS.md` says needs its own spec.
- Delays a UI feature on backend work, with no measured performance problem yet.

## Rationale

The forces are a design principle the current page breaks, a phase approach that forbids backend work, and data that already contains every value the attention section needs. Option 1 restyles a page that answers the wrong question. Option 3 gives exact numbers but turns a UI feature into a cross repo change with a migration, to fix a scale problem nobody has measured. Option 2 puts the urgent work first using `status`, `targetDueDate`, `updatedAt` and `completedAt`, which both endpoints already return.

"Waiting" is `FOR_VERIFICATION` because it is the only queue that only the admin can clear, and the app already calls it "Awaiting admin sign-off". Using one meaning in both views keeps the word honest. The waiting order uses `updatedAt` because a ticket in `FOR_VERIFICATION` rarely changes until sign off. The row says "Updated N days ago", so it never claims a precision it doesn't have. Overdue and waiting count independently because each tile states one rule. The list shows each ticket once, under overdue, the more urgent fact.

Several smaller calls were made here. **List cap**: 8 rows for admins, since the list is a triage view, not the repair list; the runner up was 5, too few on a desktop. Mechanics get no cap, because their list is their whole workload. **Due date math**: whole days, rounded down, from `targetDueDate` against now in local time; the runner up was hours, which is noise on a repair that takes days. **Refresh**: keep 15 seconds and the existing two fetches, so behavior doesn't change, and only make staleness visible. **Pipeline colors**: the `status-*-fg` tokens for segments, because the `-bg` tints are too pale to read as a bar; the runner up was the `chart-*` tokens, which would give the same status two colors in the app.
