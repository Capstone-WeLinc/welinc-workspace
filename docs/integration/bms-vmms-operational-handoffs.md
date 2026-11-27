# BMS–VMMS operational handoffs

BMS owns trips, dispatch, and driver activity; VMMS owns vehicle master odometers and maintenance plans. These proposed one-way flows let BMS provide operational evidence without writing VMMS data directly. The VMMS-owned design contract is [spec 0031](../specs/vmms/0031-bms-vmms-operational-handoffs/index.md). This is a design document only: none of the routes, grants, or implementations below is approved for build yet.

Three flows are covered:

- **D. Trip odometer evidence** — BMS → VMMS; Operations reviews before the master odometer changes.
- **E. Utilization summaries** — BMS → VMMS; VMMS presents suggestions and Operations decides whether to adjust maintenance.
- **F. Pre-trip defects** — BMS → VMMS; the driver completes the full inspection in BMS, and failed-item evidence enters VMMS for Operations review.

## Feasibility

| Flow | Feasibility | Existing VMMS capability | Required before implementation |
|---|---|---|---|
| D. Trip odometer | Doable; fits an existing ownership rule | Operations owns `Vehicle.odometer`; master updates already audit and refresh eligible schedules. VMMS also has a pending-review precedent for VRMS repair readings. | BMS service grant, inbound event/idempotency persistence, Operations review UI, and BMS/VMMS verification |
| E. Utilization | Doable as a non-mutating planning signal | VMMS already estimates due windows from audited odometer history and leaves schedule creation to Operations. | Agree summary period/version rules, thresholds, suggestion lifecycle and Operations surface |
| F. Pre-trip defects | Doable as a review-only handoff | BMS owns trips and driver checks; VMMS owns maintenance decisions and work orders. | Agree checklist versioning, failed-item codes/severity, dispatch blocking/override policy, service scope, and Operations review behavior |

These are API integrations, not shared-database access. All three are BMS-to-VMMS only; VMMS remains authoritative for its records and workflows.

## BMS checklist

- [ ] Agree the payload, stable identifiers, correction/version behavior, and field ownership for D–F with VMMS.
- [ ] Produce the D odometer message only after a trip is completed and its reading is final.
- [ ] Produce bounded E summaries without customer, route, or booking detail.
- [ ] Keep the full pre-trip inspection, driver identity, and attachments in BMS. Send F only when an item fails, with stable inspection/event and trip IDs, VMMS vehicle ID, checklist version, completion time, and the agreed failed-item fields.
- [ ] Apply the jointly approved critical-failure dispatch and override policy in BMS; do not infer it from VMMS response status.
- [ ] Use a durable outbox, persist delivery outcomes, and follow the agreed retry behavior.
- [ ] Obtain BMS/VMMS and shared-auth owner approval for the receiver contract and scopes before implementation.
- [ ] Run the joint acceptance scenarios in [When you can test](#when-you-can-test) after both systems are implemented.

## VMMS checklist

- [ ] Add service-only receivers that require audience `VMMS`, exact client ID `bms`, and the approved per-flow scope.
- [ ] Store D as pending evidence only. Provide an Operations review action; confirmation must invoke the existing master-odometer service so audit and schedule recalculation remain canonical.
- [ ] Store E as BMS-source aggregates and expose an explainable, review-only utilization suggestion. Never use the summary to write the master odometer or automatically create/change a schedule.
- [ ] Store F failed-item evidence as pending Operations review. Confirmation may lead Operations to use the normal maintenance workflow; it does not automatically create a schedule/work order or change vehicle status.
- [ ] Preserve event idempotency and source metadata transactionally; never accept a VMMS user ID from BMS.
- [ ] Keep manual odometer updates, manual fuel entry, reports, and maintenance workflows compatible.
- [ ] Do not add a direct BMS database read or fetch/copy BMS checklist attachments.

## Shared-auth/gateway checklist

- [ ] Review candidate client `bms`, audience `VMMS`, and the flow-specific scopes below.
- [ ] Add the scopes and route through the suite gateway only after both system owners agree payloads and security requirements.
- [ ] Verify wrong client, audience, token use, or missing scope is denied.

## How calls and retries work

Use the established service-to-service pattern in [repair integration](repair-integration.md#how-every-call-works): client-credentials service token, VMMS audience, gateway address, and receiver checks for audience, scope, and exact client ID. No user JWT may impersonate BMS.

Proposed delivery behavior follows the retry guidance in [BMS integration](bms-integration.md#the-retry-rule):

| Response | Sender behavior |
|---|---|
| 2xx | Mark delivered and retain the result |
| 401, 403, 408, 429, 5xx, network error, or 5-second timeout | Retry after 30 seconds, doubling up to a 1-hour maximum; stop after 24 hours |
| Other 4xx | Mark failed and surface the response to an Admin; do not retry an invalid message forever |
| Duplicate D/E/F event ID with identical body | Return the existing intake state as a duplicate |
| Same idempotency ID with different body | Return 409; require the agreed correction flow |

A failed delivery is exposed to a BMS Admin for manual retry; retry restarts the 24-hour window. Agree rate and payload limits before implementation. Receivers use database transactions to store the idempotency record with the accepted domain state.

## Proposed routes and grants

| Flow | Caller → receiver | Proposed VMMS route | Candidate scope | Status |
|---|---|---|---|---|
| D | BMS → VMMS | `POST /vmms/integrations/bms/trip-odometer-readings` | `vehicle.odometer.evidence.write` | Proposal |
| E | BMS → VMMS | `POST /vmms/integrations/bms/utilization-summaries` | `maintenance.utilization.write` | Proposal |
| F | BMS → VMMS | `POST /vmms/integrations/bms/pre-trip-inspections` | `maintenance.inspection-defect.write` | Proposal |

Candidate names are not auth grants. Shared-auth and both system owners must approve exact names and scopes.

Proposed successful intake responses are `202 Accepted`: D returns its review ID with `PENDING`, E returns the summary ID and accepted revision, and F returns its inspection-defect review ID with `PENDING_REVIEW`. A 2xx response means VMMS durably accepted the message, not that Operations applied an odometer, approved a suggestion, resolved a defect, or changed trip readiness. D/E/F use stable `eventId` values for delivery idempotency; Flow E corrections use its agreed summary revision. Identical retries return the existing intake state; reused IDs with changed bodies receive 409. Invalid payloads receive an explicit 4xx.

## Flow D: completed-trip odometer evidence

1. A BMS trip is completed and its closing odometer is available.
2. BMS queues one event per trip and posts the evidence to the proposed route.
3. VMMS authenticates BMS, verifies the vehicle and payload, and stores the evidence as **Pending Operations review**. Receipt does not update `Vehicle.odometer`, schedule state, or vehicle status.
4. Operations compares the evidence with the current master reading and trip context available in the handoff. Operations confirms or dismisses it with a recorded decision.
5. On confirmation, VMMS revalidates against the latest master reading, then uses its existing Operations-owned master update path. The current master audit and eligible schedule refresh occur through that path.
6. If the evidence is stale, lower than the master, for an unknown/inactive vehicle, or otherwise inconsistent, it is not applied. Operations can reject it with a reason; the system must not silently lower the master.

Proposed payload:

```ts
{
  eventId: string;          // stable delivery id
  tripId: string;           // BMS-owned opaque trip id
  vmmsVehicleId: string;    // VMMS vehicle UUID
  odometerKm: number;       // completed-trip reading
  completedAt: string;      // UTC ISO-8601
}
```

One final reading per trip is the initial proposal. A correction after submission needs an explicit version/correction contract; do not treat a changed retry body as a correction. The VMMS review record retains only the agreed trip ID, vehicle ID, reading, completion time, source/event ID, status, and Operations decision metadata.

## Flow E: utilization-based maintenance suggestions

1. BMS periodically summarizes completed trips by VMMS vehicle and an agreed time window.
2. BMS sends trip frequency and total distance aggregates, with a stable summary identity and revision.
3. VMMS validates the period and vehicle, stores the summary, and evaluates it under VMMS-approved utilization policy.
4. VMMS may display a suggestion such as **Review maintenance timing** with the measured period, distance, trip count/frequency, and reason it crossed the agreed signal.
5. Operations can inspect the suggestion and use the existing schedule create/edit workflow if a change is warranted. Dismissing or snoozing a suggestion does not modify a schedule.

Proposed payload:

```ts
{
  eventId: string;
  summaryId: string;        // stable BMS identity for vehicle + period
  revision: number;         // higher revision corrects the same period
  vmmsVehicleId: string;
  periodStart: string;      // YYYY-MM-DD, Asia/Manila
  periodEnd: string;        // YYYY-MM-DD, inclusive
  completedTripCount: number;
  totalDistanceKm: number;
  generatedAt: string;      // UTC ISO-8601
}
```

No individual trip, booking, customer, route, or driver data is needed. The utilization summary is not a master odometer reading and must not be added to `Vehicle.odometer` or `VehicleAuditLog` as if Operations entered it. Period length, threshold/baseline, revision ordering, retention, and suggestion lifecycle are open for joint design.

## Flow F: pre-trip inspection defect handoff

1. BMS assigns a VMMS vehicle to a trip. Immediately before dispatch, the assigned driver completes a short, versioned pre-trip checklist. A dispatcher can see the completion state but does not attest on the driver's behalf.
2. BMS stores the full inspection, driver identity, answers, completion time, attachments, and trip-readiness decision. BMS applies the critical-failure and override policy approved by both system owners.
3. If all checklist items pass, BMS keeps the inspection record and sends no event to VMMS.
4. If an item fails, BMS sends one immutable defect event through its durable outbox. The event contains stable event, inspection, and trip IDs; VMMS vehicle ID; checklist version; completion time; and only the failed item codes, agreed severity, and bounded notes. It excludes customer, booking, route, driver identity, and attachment content.
5. VMMS authenticates the BMS service, validates the vehicle and payload, and stores the report idempotently as **Pending Operations review**. A `202 Accepted` response confirms durable receipt only; it does not resolve the defect or determine whether the trip can depart.
6. Operations confirms or dismisses the reported defect with a reason. If confirmed, Operations may use the existing VMMS maintenance workflow to create work. No schedule/work order or vehicle-status change occurs automatically.
7. Any pre-trip odometer remains BMS data and does not update `Vehicle.odometer`. Completed-trip odometer evidence continues through Flow D.
8. Photos and other attachments remain in BMS. VMMS does not fetch files or follow URLs.

Proposed payload:

```ts
{
  eventId: string;          // stable delivery id
  inspectionId: string;     // BMS-owned inspection id
  tripId: string;           // BMS-owned trip id
  vmmsVehicleId: string;    // VMMS vehicle UUID
  checklistVersion: string;
  completedAt: string;      // UTC ISO-8601
  failedItems: Array<{
    itemCode: string;       // stable code from the checklist version
    severity: 'LOW' | 'HIGH' | 'CRITICAL'; // mapping requires agreement
    note?: string;          // bounded, no customer or route details
  }>;
}
```

The proposed event contains no driver identity: BMS retains the actor audit, while VMMS records the BMS service as its source. Critical-failure dispatch blocking, severity definitions, and authorized override behavior remain open for joint approval. A proposed safety default is to block dispatch for a critical failure and audit any authorized override. The initial flow does not transfer inspection photos or pre-trip odometer readings.

## When you can test

Only after the proposal is approved, both implementations and grants are present, and migrations are applied to an authorized test environment:

**Flow D**
1. Complete a BMS trip on a seeded VMMS vehicle and send a closing odometer.
2. Verify it appears in VMMS as pending and that the vehicle master and schedules are unchanged.
3. Confirm it as Operations; verify the master reading, audit, and eligible schedule refresh.
4. Submit a stale/lower reading and verify it cannot overwrite the master.
5. Retry the same event, then try the same ID with changed body; verify duplicate success then 409 respectively.

**Flow E**
1. Send a valid summary and verify it is associated with only the identified VMMS vehicle and period.
2. Verify the suggestion displays its evidence and remains a recommendation.
3. Verify vehicle master, work orders, and schedules do not change until Operations explicitly edits a schedule.
4. Retry and revise a period using the approved revision rule; verify no duplicate suggestions.

**Flow F**
1. Complete an all-pass inspection and verify the full record is in BMS and no VMMS event is sent.
2. Complete an inspection with failed items; verify only the agreed failed-item payload is accepted as pending Operations review in VMMS.
3. Verify identical event retries are idempotent and changed content under the same event ID is rejected.
4. Confirm and dismiss defects as Operations; verify the audit reason and that no schedule, work order, or vehicle-status change happens automatically.
5. After owners agree dispatch policy, verify critical-failure blocking and authorized overrides are enforced and recorded by BMS.
6. Verify driver identity, full answers, and attachments stay in BMS; VMMS does not access BMS storage.

## Implementation gates

1. Agree stable identifiers, correction/version rules, retention, payload bounds, exact routes, and response schemas between BMS and VMMS.
2. Define the VMMS utilization policy, threshold values, review surface, and suggestion lifecycle before enabling computed suggestions.
3. Agree BMS checklist ownership, template versioning, failure codes/severity, retention, payload bounds, critical-failure behavior, and override authority.
4. Approve exact service scopes, rate limits, and failure notifications with the shared-auth owner. Delivery retry timing follows the retry rule above.
5. Attachment viewing is out of scope; any future viewer needs a separate authenticated BMS API and cannot use a caller-provided URL.

## Boundary

This document proposes an integration contract only. It does not add BMS or VMMS routes, database fields, auth grants, gateway configuration, or UI. Do not begin implementation until the user authorizes it and both system owners/shared-auth reviewers approve the contract.
