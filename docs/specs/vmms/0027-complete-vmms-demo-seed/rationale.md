# 0027. Complete VMMS development seed: rationale

Decision record for [index.md](index.md).

## Context

The current VMMS seed focuses on maintenance schedules and a small set of
related records. The Prisma schema also contains fuel, costing, report,
identity-snapshot, workflow-history, audit, and integration-event models.
Representative local testing needs realistic relationships across these
domains, not rows with arbitrary IDs or broken blob references.

The seed may be run against a populated local database. Replacing entire
tables would erase operational work, append-only history, and manually
uploaded attachment metadata. Stable deterministic IDs let the seed refresh
its own mutable fixtures without treating unrelated records as seed-owned.

## Options considered

### Populate only maintenance schedules

**Rejected for this request**: it leaves the user-requested fuel, costing,
report, and integration model coverage absent.

### Reset all VMMS tables before inserting fixtures

**Rejected**: it would delete user data, immutable audit evidence, settings,
integration state, and may make background delivery repeat external events.

### Refresh seed fixtures and reset demo thresholds (chosen)

Create or update mutable fixture rows only when their deterministic IDs match
the seed's identities. Reset the two global thresholds to representative demo
values on each development seed run, auditing only real value changes. Leave
other singleton configuration and append-only audit history intact, and avoid
deleting parent rows that may have manual-upload metadata. Leave the six
VRMS/BMS integration models to the existing manual tests, and create
attachment records through the application upload flows.

**Advantages**:

- Re-running the seed refreshes stale mutable synthetic fixtures without
  wiping unrelated operational data.
- Settings consistently demonstrate both their configured values and
  downstream behavior.
- Append-only audit history and manually uploaded attachments remain intact.
- Existing service flows retain ownership of uploads and append-only audit
  enforcement.

**Tradeoffs**:

- Other settings, directory-sync state, and maintenance defaults remain
  untouched to avoid replacing unrelated configured values.
- The two global demo thresholds intentionally reset Admin changes made in
  the development database; threshold changes are recorded in existing audit
  tables.
- A different row that conflicts with a fixture's natural unique key causes
  an error rather than being adopted or overwritten.
- Integration and attachment model coverage depends on the existing manual
  test and upload workflows.
- Attachment table coverage requires a manual upload after seeding.
- Synthetic audit and integration records are local fixtures, not proof of
  real user actions or partner-system delivery.

## Smaller decisions

- Use deterministic `seedId` values to identify mutable synthetic fixtures.
- Reset demo thresholds to a 20% fuel anomaly deviation and PHP 4,000
  maintenance cost limit. Use the persisted fuel setting when deciding
  whether to create the synthetic anomaly.
- Use the two global thresholds from spec 0009; fuel anomaly comparisons
  already use each vehicle's rolling efficiency baseline. Do not add
  per-vehicle threshold overrides in this seed.
- Keep other singleton/configuration records and directory-sync state
  unchanged.
- Keep audit fixtures idempotent and immutable. Never delete or update audit
  history, even when it was originally added by the seed. Add a threshold
  audit event only when the seed actually changes a setting.
- Resolve VMMS people from the current repository fixture source. Do not
  create accounts in shared auth or use identities from another system's
  database.
- Do not create VRMS/BMS integration state, receipts, referrals, or outbox
  fixtures from this seed. The existing manual integration tests own them.
- Do not call VRMS, BMS, Azure Blob Storage, OCR, or any other external
  service from the seed.
- Supply one synthetic PNG with explicit demo markings for manual receipt and
  anomaly-attachment upload at
  [synthetic-demo-fuel-receipt.png](synthetic-demo-fuel-receipt.png). Until
  those uploads are completed, the two attachment tables are intentionally not
  populated by the seed.
- Preserve the current schema and reuse existing business helpers where
  practical. Attachment behavior remains owned by the authorized upload flows;
  do not add migrations just to simplify fixture generation.
- Refresh deterministic maintenance schedule and recurrence fixtures in
  `vmms.seed.ts` and relational demo fixtures in `relational-demo.seed.ts`.
  Preserve generated work-order and log numbers as stable identifiers.
- Base fleet, directory, and configuration data retain their existing seeder
  behavior.
- Mark seeded completed maintenance records as verified so their costs are
  eligible for the costing dashboard.
