# Glossary

> Terms reflect current VMMS code and the VMMS scope as checked 2026-11-22.
> Where a requirement conflicts with implementation or suite ownership, the
> [scope reconciliation](../../scope/vmms/index.md) records the conflict.

| Term | Meaning |
|---|---|
| **VMMS** | Vehicle Maintenance Management System; planned and preventive fleet maintenance. |
| **VRMS** | Vehicle Repair Management System; repair tickets and repair workflow. A separate system. |
| **BMS** | Booking Management System; bookings, trips, and job orders. A separate system. |
| **Admin** | VMMS system role `ADMIN`, assigned and managed by shared auth. |
| **Operations** | VMMS system role `OPERATIONS`; owns designated fleet and operational writes. |
| **Chief Mechanic** | VMMS system role `CHIEF_MECHANIC`; reviews work submitted by assigned mechanics where permitted. |
| **Mechanic** | VMMS system role `MECHANIC`; performs work on assigned maintenance orders. |
| **Vehicle status** | Fleet status: `AVAILABLE`, `UNDER_MAINTENANCE`, or `UNDER_REPAIR`. Existing `UNDER_REPAIR` status takes precedence over VMMS maintenance status. |
| **Maintenance schedule / work order** | A VMMS maintenance task for a vehicle, with trigger, assignment, checklist, lifecycle status, and work progress. In the core schema it is represented by `MaintenanceSchedule`. |
| **Maintenance status** | Schedule/work-order lifecycle: `PENDING`, `DUE`, `IN_PROGRESS`, `DONE`, `COMPLETED`, `OVERDUE`, or `CANCELLED`. |
| **Approval status** | Separate review state (`UNVERIFIED`, `VERIFIED`, `REJECTED`, or `FOR_REPAIR`); it is not the schedule lifecycle status. |
| **Maintenance trigger** | Schedule trigger type: `MANUAL`, `ODOMETER`, or `TIME`; a schedule may also carry interval and due data. |
| **Maintenance log** | Persisted record of performed maintenance, linked to the maintenance schedule/work-order history. |
| **Vehicle maintenance default** | Per-vehicle and checklist-template interval/buffer data. It is structured operational data, not a global setting. |
| **Fuel fill-up** | A VMMS fuel transaction associated with a vehicle and registered fuel station, including date, liters, price, odometer, and submitter. |
| **Fuel anomaly** | A fuel-efficiency result flagged against the configured threshold and handled through VMMS's anomaly workflow. |
| **Business audit log** | VMMS operational history for business changes. The Admin business-audit feed aggregates existing domain audit sources. |
| **Shared auth** | `welinc-auth`, which owns accounts, credentials, sessions, and per-system role assignments for the suite. |
| **Gateway** | Shared Nginx entry point at port 3000, routing `/vmms/` to the VMMS core API and `/vmms/analytics/` to the separate analytics service. |
