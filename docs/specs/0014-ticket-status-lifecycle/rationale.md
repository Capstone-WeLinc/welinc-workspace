# 0014. Ticket status lifecycle: rationale

Build spec: [index.md](index.md).

## Context

Spec 0010 fixed nine ticket status names, but the moves between them are still the interim rule in `updateStatus` (`repairs.service.ts`): `ASSIGNED` to `IN_PROGRESS` to `FOR_VERIFICATION` to `CLOSED`, plus cancel from any open status. Two small lists hold that rule (`FORWARD_MOVES`, `MECHANIC_ALLOWED_TRANSITIONS`), and web-vrms copies it a third time in `nextAction.ts`. Four of the nine statuses (`OPEN`, `ON_HOLD`, `OUTSOURCED`, `PENDING_APPROVAL`) can't be reached at all.

Jira WL-200 (VRMS-55) asks for one official list of statuses and role based moves, enforced by the backend, with clear errors and no data loss. At least nine later features change status: verification (23), holds (31), outsourcing and approval (37 to 39), assignment (18, 53, 57), mechanic updates (19), proof (22) and the admin override (33). Without one list, each would add its own moves.

Forces:
- **Backward moves are new.** Reject (WL-212) sends work from For verification back to In progress. Spec 0007 saves ticked steps and "What fixed it" notes on the way forward, so a backward move must say what happens to them.
- **Verification belongs to the Chief Mechanic** (WL-212, WL-107), but closing is Admin only through `ticket.administer`, which also carries cancel.
- **Concurrency gaps.** `lastUpdatedAt` is optional on the status body, the stale check runs before the transaction, and the vehicle is freed before the status write, so a failed write can leave a truck marked Available on an open ticket.
- **Team and timeline.** A small capstone team, deployed by the end of November 2026; changes must be cheap to build and easy to reason about.

## Options considered

### Option 1: Fix in place

Add the new moves to `FORWARD_MOVES` and extra role lists beside it, keep the web copy, and patch the lock.

**Pros**: smallest diff; no new concepts.
**Cons**: one map can't hold several moves from one status or moves owned by other features; rights stay spread across lists; the web copy keeps drifting.

### Option 2: A transition table in code, with triggers and rights (chosen)

One typed list of moves, each with from, to, the feature that triggers it, the right it needs and what it needs. One helper applies every move; the server sends allowed moves to the web.

**Pros**: one source of truth, unit testable; later features plug in by trigger; the web stops guessing; same pattern as the permission catalog (spec 0011).
**Cons**: lifecycle changes need a deploy; a little more structure than today.

### Option 3: A database table that Admin edits

Store moves in a `TicketTransition` table with a Settings screen.

**Pros**: lifecycle changes without a deploy.
**Cons**: moves are tied to code effects (verifier, vehicle, notes); an Admin could delete Verify and no ticket could close; needs a seed, a migration and a screen. Admin already controls who may move through the matrix.

### Option 4: A state machine library (for example XState)

Model the lifecycle as a statechart in a library.

**Pros**: visual tooling; formal guards.
**Cons**: a new dependency and concept for one flat machine of 14 moves; guards still need CASL and Prisma; the team would maintain two mental models.

## Rationale

Option 2 fits the forces. The interim rule can't express several moves from one status or moves owned by other features (Option 1 fails there), and making moves Admin editable (Option 3) hands out a way to break code paths that depend on them, while the right to move is already Admin editable through the matrix. A library (Option 4) solves a bigger problem than 14 moves.

Sub decisions:
- **Owner features switch on their own moves.** Declaring M1, M2 and M7 to M13 now keeps the whole lifecycle in one reviewed place, while the status endpoint refuses them, so no ticket enters On hold or Outsourced without the hold or job record that explains it.
- **A new `ticket.verify` key** gives the Chief Mechanic exactly verification. Granting `ticket.administer` would also give cancel and any ticket work moves.
- **No self verification by anyone assigned.** The verifier name is only worth recording if the verifier is independent. Feature 33 remains the escape for very small shifts.
- **Keep ticks and notes, clear `resolvedAt`.** Most rejected work needs one fix, not a rewrite; clearing `resolvedAt` stops the issue counting as resolved until it is sent again, and the prefilled dialog makes the resend quick.
- **Unlock stays costs only.** Reopening changes reports, the verifier and truck availability, so it belongs to the audited override (feature 33), not a second door.
- **400 for an invalid move, not 409.** The detail page treats any 409 on a move as stale and reloads with "This ticket changed since you opened it"; reusing 409 would show that message for a different cause. Every other rule failure in backend-vrms is 400. Runner up: 409 with a code the page checks.
- **Reuse `remarks` for the Send back comment.** The web already sends a move's note as `remarks` and shows it as "Latest remark"; a second note field would split one idea in two. Runner up: a dedicated `comment` field.
- **Reject comment in the audit row.** The `STATUS_CHANGE` row already holds a note; `lastRejection` reads it, so there is no copy to keep in step.
- **Server sends `moves`.** It follows the `can` flags pattern from spec 0011 and removes the third copy of the rule.
- **Lock inside the transaction, truck inside too.** The rewrite touches exactly this code, so closing both gaps now costs little and removes a known data bug before features 23 and 25 build on it.
