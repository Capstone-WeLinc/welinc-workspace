# Verify: Configurable settings catalog · spec 0009

Steps derived from the acceptance criteria in [index.md](index.md).

## API / automated

- [ ] Test Admin catalog reads, including defaults and saved
  values; assert exactly the allowlisted keys and metadata → AC-1
- [ ] Test Admin updates through each catalog key and verify the existing
  domain tables and audit rows change atomically → AC-2, AC-3
- [ ] Verify Operations and non-VMMS roles cannot update values; verify
  unknown keys, invalid ranges/precision, extra properties, and malformed
  values fail without writes → AC-2, AC-5
- [ ] Exercise legacy fuel and costing endpoints after catalog updates →
  AC-3, AC-4
- [ ] Confirm vehicle defaults/checklist data are not included or modified →
  AC-7

## UI / manual

- [ ] Open Settings as Admin, update each value, reload, and confirm persisted
  values and actionable error messaging
- [ ] Open Settings as Operations and confirm the route is denied and there is
  no Settings navigation entry

## Commands

- [ ] Run focused backend catalog, fuel-threshold, and costing-threshold tests
- [ ] Build `welinc-backend-vmms` and `welinc-web-vmms`

## Acceptance-criteria coverage

- AC-1 through AC-7 are covered by role, validation, compatibility,
  persistence, and UI checks above.

## Implementation evidence

- Added authenticated `GET /settings/catalog` and Admin-only
  `PATCH /settings/catalog/:key` routes in `welinc-backend-vmms`.
- Catalog reads preserve the fuel 20-percent default and an unset maintenance
  threshold until the existing domain setting is configured.
- Catalog updates delegate to the existing fuel and maintenance-costing
  domain services, preserving their tables and audit records.
- Added an Admin-only Settings page backed by the catalog API. Operations
  cannot see the navigation entry, open the route, or call the catalog API.
- Runtime API, role, validation, legacy compatibility, and browser acceptance
  checks remain pending.
