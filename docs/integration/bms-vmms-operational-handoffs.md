# BMS–VMMS operational handoffs

BMS owns trips and delivery activity; VMMS owns vehicle master odometers, maintenance plans, fuel records, and fuel reports. These proposed one-way flows let BMS provide operational evidence without writing VMMS data directly. The VMMS-owned design contract is [spec 0031](../specs/vmms/0031-bms-vmms-operational-handoffs/index.md). This is a design document only: none of the routes, grants, or implementations below is approved for build yet.

Three flows are covered:

- **D. Trip odometer evidence** — BMS → VMMS; Operations reviews before the master odometer changes.
- **E. Utilization summaries** — BMS → VMMS; VMMS presents suggestions and Operations decides whether to adjust maintenance.
- **F. Fuel purchases** — BMS → VMMS; every accepted purchase waits for Operations approval before it enters the confirmed VMMS fuel ledger.

## Feasibility

| Flow | Feasibility | Existing VMMS capability | Required before implementation |
|---|---|---|---|
| D. Trip odometer | Doable; fits an existing ownership rule | Operations owns `Vehicle.odometer`; master updates already audit and refresh eligible schedules. VMMS also has a pending-review precedent for VRMS repair readings. | BMS service grant, inbound event/idempotency persistence, Operations review UI, and BMS/VMMS verification |
| E. Utilization | Doable as a non-mutating planning signal | VMMS already estimates due windows from audited odometer history and leaves schedule creation to Operations. | Agree summary period/version rules, thresholds, suggestion lifecycle and Operations surface |
| F. Fuel purchase | Doable, with the most domain work | VMMS validates fuel values, active stations, odometers, audits transactions, derives anomalies and owns reports. | Add pending-review intake, Operations approval, explicit station mapping, idempotency, and additive persistence |

These are API integrations, not shared-database access. All three are BMS-to-VMMS only; VMMS remains authoritative for its records and workflows.

## BMS checklist

- [ ] Agree the payload, stable identifiers, correction/version behavior, and field ownership for D–F with VMMS.
- [ ] Produce the D odometer message only after a trip is completed and its reading is final.
- [ ] Produce bounded E summaries without customer, route, or booking detail.
- [ ] Produce F only for a completed purchase; provide an immutable purchase ID, VMMS vehicle ID, purchase timestamp, required PHP amounts and a stable BMS station ID. Unmapped stations remain pending for Operations rather than being inferred from a name.
- [ ] Use a durable outbox, persist delivery outcomes, and follow the agreed retry behavior.
- [ ] Obtain BMS/VMMS and shared-auth owner approval for the receiver contract and scopes before implementation.
- [ ] Run the joint acceptance scenarios in [When you can test](#when-you-can-test) after both systems are implemented.

## VMMS checklist

- [ ] Add service-only receivers that require audience `VMMS`, exact client ID `bms`, and the approved per-flow scope.
- [ ] Store D as pending evidence only. Provide an Operations review action; confirmation must invoke the existing master-odometer service so audit and schedule recalculation remain canonical.
- [ ] Store E as BMS-source aggregates and expose an explainable, review-only utilization suggestion. Never use the summary to write the master odometer or automatically create/change a schedule.
- [ ] Store every accepted F submission as pending review. Operations approval is required before creating a fuel transaction; keep pending and rejected items out of confirmed reports and fuel-efficiency calculations.
- [ ] Preserve event/purchase idempotency and source metadata transactionally; never accept a VMMS user ID from BMS.
- [ ] Keep manual odometer updates, manual fuel entry, reports, and maintenance workflows compatible.
- [ ] Do not add a direct BMS database read, fetch a receipt URL, or copy a BMS receipt file.

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
| Duplicate D/E event ID or F purchase ID with identical body | Return the existing intake state as a duplicate |
| Same idempotency ID with different body | Return 409; require the agreed correction flow |

A failed delivery is exposed to a BMS Admin for manual retry; retry restarts the 24-hour window. Agree rate and payload limits before implementation. Receivers use database transactions to store the idempotency record with the accepted domain state.

## Proposed routes and grants

| Flow | Caller → receiver | Proposed VMMS route | Candidate scope | Status |
|---|---|---|---|---|
| D | BMS → VMMS | `POST /vmms/integrations/bms/trip-odometer-readings` | `vehicle.odometer.evidence.write` | Proposal |
| E | BMS → VMMS | `POST /vmms/integrations/bms/utilization-summaries` | `maintenance.utilization.write` | Proposal |
| F | BMS → VMMS | `POST /vmms/integrations/bms/fuel-purchases` | `fuel.purchase.write` | Proposal |

Candidate names are not auth grants. Shared-auth and both system owners must approve exact names and scopes.

Proposed successful intake responses are `202 Accepted`: D returns its review ID with `PENDING`, E returns the summary ID and accepted revision, and F returns its purchase-review ID with `PENDING_REVIEW`. A 2xx response means VMMS durably accepted the message, not that Operations approved it or that a fuel transaction was created. D/E use `eventId` for delivery idempotency; F uses `purchaseId` as the business idempotency key. Identical retries return the existing intake state; reused IDs with changed bodies receive 409. Invalid payloads receive an explicit 4xx.

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

## Flow F: delivery fuel-purchase handoff

1. BMS records a refuelling purchase made during a delivery and queues it using an immutable BMS purchase ID.
2. BMS submits the VMMS vehicle ID, delivery trip ID, purchase timestamp, odometer, liters, unit price/currency, station identifier, and opaque receipt reference.
3. VMMS authenticates the message and checks field constraints, vehicle, station mapping, existing fuel history, and possible duplicate manual entries. It never trusts a sender-computed total.
4. Every valid purchase is stored as pending Operations review; no BMS purchase is automatically entered into the confirmed VMMS fuel ledger. Possible manual duplicates and suspicious values remain visible to the reviewer.
5. Operations resolves the BMS station ID through an explicit VMMS mapping to an active station. Unmapped station IDs remain pending; name similarity alone is not a mapping.
6. When Operations approves the submission, VMMS revalidates it and creates the fuel transaction through its existing fuel domain path. VMMS calculates total cost and audits the actual Operations actor. Pending or rejected purchases are excluded from confirmed reports and efficiency calculations. Hard-invalid values receive an explicit 4xx response.
7. The pending integration record retains BMS source and purchase/trip IDs; VMMS does not fabricate a human submitter identity for the service submission.
8. The receipt reference stays an opaque BMS identifier. VMMS neither dereferences it as a URL nor copies the receipt. An in-app receipt viewer would require a separately agreed authenticated BMS read API.

Proposed payload:

```ts
{
  eventId: string;
  purchaseId: string;       // unique BMS transaction identity
  tripId: string;           // BMS delivery identity
  vmmsVehicleId: string;
  purchasedAt: string;      // UTC ISO-8601
  odometerKm: number;
  liters: number;
  pricePerLiter: number;
  currency: 'PHP';
  station: {
    bmsStationId: string;
    name: string;
  };
  receiptReference: string; // opaque BMS ID, never a URL
  isFullTank?: boolean;     // omitted means false; never infer a full tank
}
```

VMMS requires an active registered fuel station and uses full-tank state in efficiency calculations. Therefore, Operations maintains an explicit mapping from stable BMS station IDs to active VMMS stations; do not resolve stations by name alone. The payload uses PHP, and omitted `isFullTank` means false. Suspect odometer order and possible manual duplicates stay in the Operations review queue. All BMS fuel submissions require Operations approval before they enter the confirmed ledger.

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
1. Send a valid, mapped purchase; verify it is pending and excluded from reports/efficiency.
2. Approve it as Operations; verify server-calculated total, audit, source link, and report inclusion exactly once.
3. Send an unknown station, possible duplicate, and odometer-order anomaly; verify each remains reviewable and excluded before approval. Reject one and approve another to confirm both outcomes.
4. Send malformed amounts or changed content under a reused purchase ID; verify explicit rejection or conflict as appropriate.
5. Verify no receipt URL is followed and manual VMMS fuel entry remains unchanged.

## Implementation gates

1. Agree stable identifiers, correction/version rules, retention, payload bounds, exact routes, and response schemas between BMS and VMMS.
2. Define the VMMS utilization policy, threshold values, review surface, and suggestion lifecycle before enabling computed suggestions.
3. Confirm BMS can provide the purchase timestamp and PHP amounts; if full-tank state is absent, VMMS treats it as false.
4. Approve exact service scopes, rate limits, and failure notifications with the shared-auth owner. Delivery retry timing follows the retry rule above.
5. Receipt viewing is out of scope; any future viewer needs a separate authenticated BMS API and cannot use a caller-provided URL.

## Boundary

This document proposes an integration contract only. It does not add BMS or VMMS routes, database fields, auth grants, gateway configuration, or UI. Do not begin implementation until the user authorizes it and both system owners/shared-auth reviewers approve the contract.
