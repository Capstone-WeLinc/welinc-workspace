# 0007. Fuel station management

**Status**: Implemented; runtime and browser acceptance pending
**Scope**: [Module 5: Fuel expenses and anomaly handling](../../../scope/vmms/index.md)

Decision history (context, options, rationale): [rationale.md](rationale.md). Verification steps: [verify.md](verify.md).

## Summary

Operations can add and rename registered fuel stations, and deactivate or
reactivate them from Fuel Management. Deactivation prevents new fuel entries
and statement imports from using a station; it does not delete the station or
its history.

## Decisions

- Only Operations can add, rename, deactivate, or reactivate fuel stations.
- Keep the existing active-only `GET /fuel/stations` contract for fuel-entry
  and statement-import selectors.
- Add an Operations-only management endpoint that lists active and inactive
  stations, so deactivated stations can be reactivated.
- Use the existing station ID for renamed stations. New entries use the
  current station name.
- Store the station name on each fill-up when it is created. A later station
  rename must not change the station label shown on historical fill-ups.
- Backfill existing fill-ups from their currently associated station name.
  Earlier names cannot be recovered because they were not previously stored.
- Removal means deactivation. Do not hard-delete stations because fill-ups
  reference them and the history must remain available.
- Keep fuel analytics and VMMS mobile behavior unchanged; existing fuel
  responses continue to expose a station name, now from the fill-up snapshot.

## Flow

1. Operations opens Configure fuel stations from Fuel Management.
2. The dialog lists all stations, including inactive ones, and their status.
3. Operations adds a station, edits a station name, deactivates an active
   station, or reactivates an inactive station.
4. The UI refreshes its station lists after each successful change. Fuel
   entry and import selectors contain active stations only.
5. Deactivation requires confirmation that the station will no longer be
   available for new entries while existing fuel records remain.

## API and data impact

- Preserve `GET /fuel/stations` for Admin and Operations, returning active
  stations only.
- Add `GET /fuel/stations/management` for Operations, returning all stations
  with `id`, `name`, and `isActive`, sorted by name.
- Extend the Operations-only `PATCH /fuel/stations/:id` contract to accept
  `name`, `isActive`, or both. Require at least one field; trim and validate
  names to 1–100 characters and validate `isActive` as a boolean.
- Keep `POST /fuel/stations` Operations-only and validate names to 1–100
  trimmed characters. Respect the existing unique station-name constraint.
- Add a non-null station-name snapshot column to `fuel_fill_ups`. Backfill
  existing records from their related station names in an additive migration.
- All fuel-entry creation paths, including statement import, record the
  station's current name in the snapshot. Fuel responses use the snapshot for
  historical display.
- No hard-delete API, analytics API, mobile contract, shared auth, portal,
  gateway, or cross-system change is in scope.

## Security and failure behavior

- Enforce Operations authorization for station management endpoints at the
  API boundary.
- Reject invalid names, empty updates, invalid activation values, duplicate
  names, and unknown station IDs with explicit errors.
- Preserve existing fill-ups and fuel audit records when a station is
  deactivated or renamed.
- If an update fails, retain the prior row and show the API error in the
  management dialog; do not optimistically report success.

## Acceptance criteria

1. Operations can view active and inactive stations; Admin and other roles
   cannot use the management endpoint.
2. Operations can add a station and see it appear in active station selectors.
3. Operations can rename a station; the new name is used for future entries,
   while historical fill-ups continue to display their saved station name.
4. Operations can deactivate and reactivate a station. Inactive stations are
   excluded from fuel-entry and import selectors and remain available in the
   management list for reactivation.
5. Deactivation never deletes or changes existing fill-ups.
6. Invalid, duplicate, or unauthorized changes return visible errors and do
   not produce success-shaped UI state.
7. Existing active-only station selectors and fuel history remain compatible.

## Affected repositories

- `welinc-backend-vmms`: management list and update validation, additive
  snapshot migration, and snapshot writes/responses.
- `welinc-web-vmms`: station management dialog, inline rename and status
  actions, and synchronization with active station selectors.

## Verification plan

- Verify Operations-only access for listing and mutation; verify other roles
  cannot manage stations.
- Verify trimmed and duplicate name validation, empty updates, invalid status
  values, and unknown IDs.
- Verify active/inactive list behavior, rename, deactivate, and reactivate.
- Verify the migration backfills existing station names and all new fuel-entry
  paths store snapshots.
- Verify a rename does not change station labels on historical fuel entries,
  while new entries and imports use the renamed station.
- Verify active-only fuel log and statement-import selectors update after
  management actions.
