# 0009. Configurable settings catalog

**Status**: Backend and web implementation complete; runtime verification pending
**Scope**: [Fuel expenses and anomaly handling](../../../scope/vmms/index.md#5-fuel-expenses-and-anomaly-handling); [Maintenance costing](../../../scope/vmms/index.md#6-maintenance-costing)

Decision history: [rationale.md](rationale.md). Verification: [verify.md](verify.md).

## Summary

Provide a typed, Admin-managed catalog for the two existing global VMMS
thresholds: fuel anomaly percentage and maintenance costing amount. Keep their
current persistence, audit records, and domain APIs. Vehicle/category
maintenance defaults remain structured operational records, not global
settings.

## Sources and decisions

- Current VMMS fuel anomaly setting and maintenance costing threshold
  implementations and audit tables.
- User selected cataloging the existing global thresholds only, preserving
  vehicle-specific defaults separately.
- This is an approved VMMS extension; the source BRD/RTM does not define a
  general-purpose settings catalog.

Catalog entries expose a stable key, label, description, unit, value type,
default/current value, constraints, effective value, update timestamp, and
whether the actor may edit it. The initial keys are:

| Key | Type / unit | Default | Validation | Editable by |
|---|---|---:|---|---|
| `fuel_anomaly_threshold_percent` | decimal percent | 20 | 1–99, up to 2 decimal places | Admin |
| `maintenance_cost_threshold` | positive decimal currency amount | unset | greater than 0, up to 2 decimal places; nullable until first set | Admin |

## Behavior and API

- Add authenticated, Admin-only `GET /settings/catalog`. Return
  only the two allowlisted entries and their effective values.
- Add Admin-only `PATCH /settings/catalog/:key` with a typed value. Validate
  against the registry before delegating to the existing domain service.
- Existing fuel and maintenance-costing read/update routes remain supported
  and retain their current response contracts.
- Updates continue to write their existing domain-specific setting rows and
  audit history in the same transaction. The catalog does not become a second
  source of truth.
- Unknown keys and malformed values return explicit validation errors and
  cause no persistence changes.
- Add an Admin-only Settings web page backed by the catalog API. Operations
  and other web roles cannot access it or its API. Do not expose vehicle/category maintenance
  defaults on this page.

## Acceptance criteria

1. Admin receives exactly the two catalog entries with the
   configured/default values, metadata, constraints, and editable state.
2. Admin can update each setting through the catalog; Operations and all other
   roles cannot mutate either value.
3. Updates preserve existing validation, persistence tables, audit attribution,
   and behavior of fuel anomalies and maintenance-costing reports.
4. Existing setting routes and consumers remain compatible.
5. Unknown keys, invalid bounds/precision, malformed bodies, and unexpected
   properties are rejected without a partial update.
6. The Admin-only Settings page displays both entries, validates inputs, and
   reports save failures.
7. Vehicle/category maintenance defaults and checklist templates remain
   independent and unchanged.

## Data, migration, and security

- No new settings table or migration; the existing domain tables remain
  authoritative.
- The catalog metadata is a typed code registry, not client-supplied policy.
- All API routes remain VMMS-authenticated and system/role guarded; do not
  return actor emails beyond fields already disclosed by existing APIs.
- No shared auth, portal, gateway, analytics, or other-system changes.

## Affected repositories

- `welinc-backend-vmms`: registry, catalog controller/service, DTOs, and
  guarded tests.
- `welinc-web-vmms`: Admin settings page, navigation/route, and API client.

## Delivery status

The two existing settings, their defaults, and their separate audit paths were
confirmed during design. Catalog API and UI implementation and verification
remain.
