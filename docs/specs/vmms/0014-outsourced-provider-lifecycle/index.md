# 0013. Outsourced provider lifecycle

**Status**: Implementation complete; controller and browser runtime verification pending
**Scope**: [Vehicle management](../../../scope/vmms/index.md#2-fleet-vehicle-management); [Maintenance scheduling and alerts](../../../scope/vmms/index.md#3-maintenance-scheduling-and-alerts)

Decision history: [rationale.md](rationale.md). Verification: [verify.md](verify.md).

## Summary

Complete Operations' outsourced-provider catalog actions without changing how
maintenance schedules store provider names or how new schedules select active
providers.

## Sources and decisions

- VMMS BRD/RTM FR-06.1 and FR-11.4.
- Existing Operations-managed provider catalog and
  `MaintenanceSchedule.outsourcedProvider` historical snapshot.
- User decision: an unused provider can be renamed or deleted; once any
  schedule references it, only active/inactive status may change.

## Behavior and API

- Define a provider as used when any maintenance schedule references its name,
  case-insensitively. Include all schedule states and soft-deleted schedules
  so retained history is protected.
- Include `usageCount` in the provider list response for the Operations UI.
- Operations may rename and delete providers with a zero usage count.
- Return a conflict when attempting to rename or delete a used provider.
  Operations may still activate or deactivate it.
- Add `DELETE /config/outsourced-providers/:id`; it physically deletes only an
  unused provider.
- Active providers remain required for new outsourced schedules. An existing
  schedule may retain its same provider after that provider is deactivated,
  but inactive providers are not valid for new assignments or replacements.
- Admin retains read-only access. All mutations remain Operations-only.

## Acceptance criteria

1. Provider list entries include the number of schedules referencing each
   provider, including completed, cancelled, and soft-deleted schedules.
2. Operations can rename or delete a provider with no references; names remain
   unique case-insensitively.
3. Rename and delete of a referenced provider return a conflict and leave
   provider data unchanged.
4. Operations can activate/deactivate referenced providers; inactive
   providers are excluded from new schedule assignments.
5. Editing an existing schedule can preserve its same inactive provider.
6. Admin can list providers but cannot create, edit, toggle, or delete them.
7. Existing historical schedules and their provider-name snapshots remain
   unchanged; no migration is required.

## Data, migration, and security

- No schema or migration change. Provider usage is derived from existing
  schedule name snapshots and includes soft-deleted schedule rows.
- Preserve existing case-insensitive duplicate-name validation.
- Enforce usage restrictions and Operations role authorization in the API;
  UI controls are not an authorization boundary.
- No shared auth, gateway, analytics, or other-system changes.

## Affected repositories

- `welinc-backend-vmms`: provider usage, rename/delete guards, and guarded
  delete route.
- `welinc-web-vmms`: usage display and conditional edit/delete controls.

## Delivery status

The API and web lifecycle controls are implemented. The focused provider and
schedule regression tests pass (22 tests); backend and web builds pass.
Interactive browser acceptance remains pending.
