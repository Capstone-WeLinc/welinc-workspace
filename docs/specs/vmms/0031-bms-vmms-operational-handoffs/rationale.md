# Rationale: BMS–VMMS operational handoffs

Decision record for [index.md](index.md).

## Context

BMS owns completed trips, trip dispatch, and driver activity. VMMS owns vehicle master odometers, maintenance decisions, schedules, and maintenance work orders. Suite rules require inter-system API calls and prohibit cross-system database reads.

VMMS checklist templates are attached to maintenance work orders. A pre-trip inspection is a different workflow: it happens before a BMS trip, is performed by the assigned driver, and contributes to BMS's dispatch-readiness decision. Reusing the maintenance checklist or placing the inspection in VMMS Scheduling would couple trip execution to the wrong system.

The user requested replacing the proposed BMS fuel-purchase handoff with a pre-trip checklist flow. Checklist ownership, the failed-item payload, and dispatch-blocking policy remain proposed pending BMS/VMMS review.

## Options considered

### Put the entire inspection in VMMS Scheduling

**Rejected.** VMMS Scheduling manages planned maintenance, and its checklists are work-order templates. BMS owns trip dispatch and should retain the full pre-trip inspection and driver attestation.

### Let BMS update VMMS-owned maintenance records directly

**Rejected.** It bypasses VMMS authorization, validation, audit, workflow, and data ownership.

### Read BMS databases from VMMS

**Rejected.** It violates the suite's API boundary and couples deployments and schemas.

### Keep the inspection in BMS and submit failed-item evidence to VMMS

BMS stores the complete, versioned checklist and dispatch result. When any item fails, BMS sends only the minimum defect evidence through an authenticated API. VMMS stores it idempotently for Operations review; Operations can use the existing maintenance workflow if action is warranted.

## Decisions and tradeoffs

- **Trip odometer:** the reading is evidence, not a master update. Operations confirmation preserves VMMS ownership and reuses the existing audit/schedule-refresh path, at the cost of a review queue and delayed schedule recalculation.
- **Utilization:** BMS summaries can inform review-only suggestions under a VMMS-approved policy. Thresholds are set during implementation; no summary may write the master odometer or automatically change maintenance.
- **Pre-trip inspection:** the assigned BMS driver completes the checklist before departure. BMS remains the source of the full inspection, actor identity, and attachments; VMMS receives only failed-item evidence.
- **Dispatch readiness:** BMS owns the decision to start or block a trip. Whether critical failures block dispatch and who can override them must be agreed before implementation; VMMS cannot make this decision by changing vehicle status from an inbound report.
- **VMMS follow-up:** a reported failure is pending evidence, not a schedule or work order. Operations reviews it and uses existing maintenance workflows when appropriate.
- **Odometer:** a pre-trip reading is not a master-odometer update. Completed-trip readings remain in Flow D and require Operations review before application.
- **Identity and payload:** BMS retains driver identity and full item responses. Stable event IDs support retries; VMMS records BMS as the source and does not accept a client-selected VMMS actor. Failed-item codes, severity mapping, retention, and response contract require partner agreement.
- **Service grants:** candidate grants remain proposals. Shared-auth ownership and exact scopes must be reviewed before implementation.

## Why BMS retains the full inspection

The checklist is part of the driver's trip workflow, so BMS owns the full record, attestation, and dispatch outcome. Sending only failed-item evidence to VMMS minimizes cross-system data and keeps Operations focused on issues that may require maintenance. VMMS never treats a driver response as a maintenance decision: Operations reviews the report and may create work through the existing VMMS workflow.

The recommended critical-failure dispatch block remains an open policy decision for both system owners. The pre-trip flow does not change existing VMMS fuel entry or the separately proposed completed-trip odometer review.
