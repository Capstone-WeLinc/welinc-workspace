# Verify: Fuel station management · spec 0007

Steps derived from the acceptance criteria in [index.md](index.md).

## API / security

- [ ] Sign in as Operations and list active/inactive stations from the
  management endpoint
- [ ] Confirm Admin and other roles cannot list or mutate stations through
  management endpoints
- [ ] Add a station and confirm it appears in active fuel-entry and import
  selectors
- [ ] Rename a station and confirm future entries use the new name while an
  existing fill-up keeps its station-name snapshot
- [ ] Deactivate and reactivate a station; confirm active selectors exclude the
  inactive station and the management list retains it
- [ ] Test trimmed/duplicate names, empty updates, invalid booleans, unknown IDs,
  and unauthorized requests

## UI / manual

- [ ] Open Configure fuel stations in Fuel Management
- [ ] Confirm active and inactive stations are visible with clear status
- [ ] Rename, deactivate, and reactivate rows and confirm dialog data refreshes
  after successful changes
- [ ] Confirm deactivation requires/communicates that existing fill-ups remain
  available
- [ ] Confirm failures show the API error and do not optimistically report
  success

## Database / compatibility

- [ ] Apply the additive station-name snapshot migration
- [ ] Confirm existing fill-ups are backfilled from their related station names
- [ ] Confirm every new JSON, receipt, and statement-import entry stores the
  station snapshot
- [ ] Confirm active-only station selectors and fuel history remain compatible

## Commands

- [ ] Build and test `welinc-backend-vmms`
- [ ] Build and test `welinc-web-vmms`
- [ ] Run focused station management and migration tests

## Acceptance-criteria coverage

- AC-1 through AC-7 by the role, station list, mutation, snapshot, migration,
  and compatibility checks above.
