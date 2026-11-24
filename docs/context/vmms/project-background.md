# Project background

> Source: VMMS scope reconciliation, the workspace suite overview, and the
> current VMMS repositories; checked 2026-11-22. The original BRD and RTM were
> supplied by the project owner and are not checked into this workspace.

## System purpose

The Vehicle Maintenance Management System (VMMS) supports planned and
preventive maintenance for WeLinc Logistics' fleet. It provides operational
records for vehicles, schedules, work orders, checklists, service history,
fuel, maintenance costs, and management reporting.

## Users

- **Admin** manages system-level operational configuration and reviews
  management information.
- **Operations** manages fleet and maintenance records, fuel entries,
  schedules, reports, and related workflows.
- **Chief Mechanic** reviews mechanic-submitted work and performs mechanic
  workflow responsibilities.
- **Mechanic** works on assigned maintenance jobs and records execution
  evidence.

Account creation, role assignment, sign-in, and shared account activity belong
to the shared auth and portal services, not to VMMS.

## Operating constraints

- Mechanics use the shared VRMS/VMMS mobile application; Admin and Operations
  use the VMMS web application.
- VMMS owns its operational API and database. Other systems must use an
  approved API rather than read the VMMS database.
- The suite uses a shared auth service and gateway, while each system retains
  its own application data and deployment boundary.
- Vehicle status is shared fleet context. `UNDER_REPAIR` takes precedence over
  VMMS maintenance status and must not be overwritten by VMMS.
- Scope exclusions and unresolved BRD/RTM conflicts are recorded in the
  [VMMS scope](../../scope/vmms/index.md), which is the requirements
  reconciliation source.
