# System overview

> Source: workspace suite architecture, VMMS scope, and current repositories;
> checked 2026-11-22. The code is the source of truth for current service
> boundaries; the VMMS scope records requirement and acceptance status.

## What VMMS does

VMMS maintains fleet maintenance schedules and work orders, supports assigned
mechanic execution and Chief Mechanic review, retains maintenance history,
records fuel transactions, and provides maintenance/fuel reports and analytics.
The VMMS web app serves Admin and Operations. Mechanics use the shared
VRMS/VMMS mobile app for VMMS-assigned work.

## Repositories and local ports

| Repository | Responsibility | Local port |
|---|---|---:|
| `welinc-backend-vmms` | Core operational API, PostgreSQL persistence, migrations, and private VMMS file storage | 3010 |
| `welinc-backend-vmms-analytics-ai` | Separate VMMS analytics/AI API and reporting data | 3011 |
| `welinc-web-vmms` | Admin and Operations web application | 8002 |
| `welinc-mobile-vrms_vmms` | Shared mobile app; VMMS work is limited to VMMS flows | Expo |

The browser and mobile clients use the suite gateway at port 3000. The portal
is at port 8000 and shared auth is at port 3001. See the [suite overview](../suite-overview.md)
and workspace README for shared-service details.

## Architecture

- VMMS is a modular monolith in the core service, with a separate analytics
  service and independent frontend/mobile clients.
- VMMS owns its PostgreSQL database. The analytics service reads VMMS
  operational data for its reporting data mart; the core API remains the
  authority for operational state. This is an internal VMMS service boundary,
  not cross-system database access.
- Private file storage is accessed by the core VMMS backend. Clients do not
  receive public storage URLs.
- Authentication and per-system role assignments are owned by `welinc-auth`.
  VMMS validates the VMMS roles required for each protected operation.
- Other systems integrate through documented service APIs and the gateway.
  Cross-system database reads are not part of the architecture.

## Core domain boundaries

- `VehicleStatus` represents fleet availability (`AVAILABLE`,
  `UNDER_MAINTENANCE`, `UNDER_REPAIR`). VMMS preserves an existing
  `UNDER_REPAIR` state.
- `MaintenanceStatus` represents a VMMS schedule/work-order lifecycle.
  Approval state is stored separately.
- Fuel and maintenance costing are VMMS domains. Repair-ticket management and
  repair cost ownership remain outside VMMS.
- The full requirements reconciliation, conflicts, and provisional feature
  states are in the [VMMS scope](../../scope/vmms/index.md).
