# Verify: Configurable settings catalog · spec 0009

Steps derived from the acceptance criteria in [index.md](index.md).

## API / automated

- [ ] Test Admin and Operations catalog reads, including defaults and saved
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
- [ ] Open Settings as Operations and confirm values are read-only

## Commands

- [ ] Run focused backend catalog, fuel-threshold, and costing-threshold tests
- [ ] Build `welinc-backend-vmms` and `welinc-web-vmms`

## Acceptance-criteria coverage

- AC-1 through AC-7 are covered by role, validation, compatibility,
  persistence, and UI checks above.
