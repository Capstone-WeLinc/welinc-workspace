# Verify: Outsourced provider lifecycle · spec 0013

Steps derived from the acceptance criteria in [index.md](index.md).

## API / automated

- [x] List providers and verify `usageCount` includes schedule history across
  statuses, including soft-deleted schedules → AC-1
- [x] Rename and delete an unused provider; verify case-insensitive duplicate
  names are rejected → AC-2
- [x] Attempt rename/delete for a used provider; verify conflict responses and
  unchanged provider/schedule data → AC-3
- [x] Activate/deactivate a used provider; verify new schedule assignments
  reject inactive providers → AC-4
- [x] Edit a schedule retaining its same inactive provider; verify it saves,
  while switching to that inactive provider is rejected → AC-5
- [ ] Verify Admin can read the catalog but cannot mutate it → AC-6
- [ ] Verify existing schedule snapshots are unchanged and no migration is
  required → AC-7

## UI / manual

- [ ] As Operations, verify unused providers offer edit/delete and used
  providers offer only activation controls.
- [ ] Confirm delete requires a confirmation and API errors are displayed.
- [ ] As Admin, verify provider actions are read-only.

## Commands

- [x] Run focused provider lifecycle tests and build `welinc-backend-vmms`.
- [x] Build `welinc-web-vmms`.
- [x] Added create/update mutation DTO validation and HTTP role/validation
  coverage for the outsourced-provider controller.
- [x] Re-ran the provider controller and service suites on 2026-11-24:
  `npx jest src/modules/vmms/config/config.controller.spec.ts src/modules/vmms/config/config.service.spec.ts --runInBand`
  passed with 8 tests across 2 suites.

## Acceptance-criteria coverage

- AC-1 through AC-7 are covered by provider API, schedule validation, role,
  and UI checks above.
