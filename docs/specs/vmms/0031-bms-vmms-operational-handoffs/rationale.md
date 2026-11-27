# Rationale: BMS–VMMS operational handoffs

Decision record for [index.md](index.md).

## Context

BMS owns completed trips, delivery refuelling records, and trip aggregates. VMMS owns vehicle master odometers, maintenance decisions and schedules, fuel transactions, anomaly decisions, and fuel reporting. Suite rules require inter-system API calls and prohibit cross-system database reads.

VMMS assigns master-odometer writes to Operations and already supports pending odometer evidence from VRMS repair completion. This is a workflow precedent, not authorization for BMS access. VMMS maintenance predictions use audited master-odometer history; BMS utilization must remain supplemental evidence rather than a second odometer authority. VMMS fuel creation validates active registered stations, odometer, liters, unit price, dates, and audit/report behavior. Its existing Operations-only fuel-station management and submission flow provide the review boundary for BMS-originated purchases.

## Options considered

### Let BMS update VMMS-owned records directly

**Rejected.** It bypasses VMMS authorization, validation, audit, workflow, and data ownership.

### Read BMS databases from VMMS

**Rejected.** It violates the suite's API boundary and couples deployments and schemas.

### Submit authenticated events to VMMS for domain-owned processing

BMS sends minimum necessary events through the gateway. VMMS authenticates and validates the message, persists its receipt idempotently, and applies VMMS-owned review and decision workflows. This preserves ownership and reuses the service-event/outbox pattern documented by the BMS and repair integrations.

## Decisions and tradeoffs

- **Trip odometer:** the reading is evidence, not a master update. Operations confirmation preserves VMMS ownership and reuses the existing audit/schedule-refresh path, at the cost of a review queue and delayed schedule recalculation.
- **Utilization:** BMS summaries can inform review-only suggestions under a VMMS-approved policy. Thresholds are set during implementation; no summary may write the master odometer or automatically change maintenance.
- **Fuel purchase:** every valid BMS purchase is held for Operations approval before it creates a confirmed fuel transaction. This was selected over automatic recording of apparently safe purchases. It adds review effort but keeps VMMS's existing human approval and fuel-entry boundary intact.
- **Fuel station:** Operations resolves BMS station IDs through an explicit VMMS mapping to an active station. Name matching alone is insufficient and an unmapped purchase remains pending.
- **Fuel amounts:** the contract currency is PHP, consistent with the VMMS fuel module. VMMS calculates the total from submitted liters and unit price. If BMS omits full-tank state, VMMS treats it as false; it never infers a full tank.
- **Receipt:** BMS receipt references stay opaque identifiers. This avoids arbitrary URL and direct file-storage risks; viewing the receipt would require a separately scoped BMS API.
- **Identity:** stable business/event IDs support retries and duplicate detection. Changed content under a reused idempotency key is a conflict, not a correction. Corrections need an explicit versioned event rule.
- **Service grants:** candidate grants remain proposals. Shared-auth ownership and exact scopes must be reviewed before implementation.

## Why all BMS fuel purchases require review

The user selected review for every BMS-originated purchase, rather than automatic confirmation based on an initial suspicious-value check. VMMS first stores a valid submission as pending review. Operations can confirm or reject it after checking the purchase and resolving its station mapping. Only a confirmed entry is created through the VMMS fuel service and included in confirmed reports and efficiency calculations. Invalid fields are rejected; unresolved station mappings stay pending.

This decision does not change manual fuel entry, which remains an Operations-owned VMMS flow.
