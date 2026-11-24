# Verify: Append-only business audit · spec 0010

Steps derived from the acceptance criteria in [index.md](index.md).

## Database / API

- [ ] Apply migration to a disposable PostgreSQL database; insert one row in
  every protected table → AC-1
- [ ] Attempt `UPDATE` and `DELETE` against each protected table directly and
  through Prisma; confirm database rejection → AC-2
- [ ] Run identity erasure; confirm only actor name/email markers change and
  event details remain intact; attempt any additional column change → AC-3
- [ ] Attempt hard deletion of referenced work-order/vehicle parents; confirm
  explicit restriction, then verify ordinary soft deletes work → AC-4
- [ ] Verify Admin feed order/limit/contents, category values, Admin
  authorization, and `Cache-Control: no-store` → AC-5, AC-6
- [ ] Exercise cancellation review and edit-unlock lifecycle after the
  migration and check their workflow category → AC-7

## UI / manual

- [ ] Inspect each event category in the Audit Logs table and filter by
  category; confirm event details still render

## Commands

- [ ] Run focused audit feed, erasure, cancellation, and edit-unlock tests
- [ ] Validate Prisma schema and build `welinc-backend-vmms`

## Acceptance-criteria coverage

- AC-1 through AC-7 are covered by migration, database enforcement,
  authorization, erasure, lifecycle, and UI checks above.

## Implementation evidence

- Added a forward-only PostgreSQL trigger migration for the seven protected
  immutable audit tables, with identity-erasure-only updates permitted.
- Changed cascading audit foreign keys for work-order and vehicle history to
  `RESTRICT` in Prisma and migration metadata.
- Added stable `category` values to every unified business-audit record.
- Added the Audit Logs category filter and category display in VMMS web.
- Migration application, direct SQL mutation checks, erasure behavior,
  browser filtering, and lifecycle runtime checks remain pending.
