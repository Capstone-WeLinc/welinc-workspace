# 0012. Predictive maintenance readiness

**Status**: Implementation complete; runtime verification pending
**Scope**: [Maintenance scheduling and alerts](../../../scope/vmms/index.md#3-maintenance-scheduling-and-alerts)

Decision history: [rationale.md](rationale.md). Verification: [verify.md](verify.md).

## Summary

Use the existing vehicle odometer audit history to show Operations conservative
predictions for eligible odometer-based schedules expected to reach their due
reading within 30 days. Predictions are advisory only; they never create or
change work orders automatically.

Prepare the feature for local and staging use with synthetic, repeatable seed
data whose vehicle, garage, mechanic, checklist, schedule, and work-order
references agree with the existing schema. Make Due Date the only user-entered
schedule date while retaining internal dates needed by recurrence and audit.

## Sources and decisions

- VMMS requirements FR-07.* and FR-09.*.
- [Spec 0004](../0004-bulk-odometer-updates/index.md): the Operations-owned
  master odometer is authoritative; its update transaction already refreshes
  eligible schedules. Do not add a competing polling job.
- [Spec 0008](../0008-maintenance-status-lifecycle/index.md): preserve
  Operations schedule ownership, workflow states, and recurrence behavior.
- User-approved decisions:
  - Predictions are Operations-facing suggestions only. Do not create a work
    order, send a new notification, or modify a schedule from a prediction.
  - Use audit readings from the prior 90 days. Require at least three
    increasing readings spanning at least 30 days. Use the median daily
    distance rate and report a prediction only when the due reading is
    projected within the next 30 days.
  - Schedule create/edit forms accept Due Date as the only user-entered
    schedule date. On create, store `startDate` as the Manila creation day;
    preserve it on edits. For time triggers, derive the internal
    `startReferenceDate` by subtracting the selected interval from Due Date
    using calendar-day/month arithmetic.
  - Keep the existing schema and its current relation semantics. Use
    synthetic seed data, preserve populated records, and do not add database
    foreign keys or migrations in this slice.

## Behavior

### Due-date-first schedule form

- Keep `targetDueDate` as the required user-entered schedule date.
- Hide the top-level Start Date input. New schedules use the Manila current
  date for the internal `startDate`; edits retain the stored value.
- For a time-triggered schedule, derive `startReferenceDate` from Due Date
  minus the selected interval. Odometer and manual triggers do not receive a
  time reference date.
- Preserve existing validation, Operations authorization, and schedule
  reschedule auditing. The due date cannot precede the internal schedule
  start date. Do not change completion-based recurrence.

### Predictions

- Add an Operations-only, read-only API and web panel for projected odometer
  due dates.
- Consider only active vehicles and non-deleted odometer schedules in
  `PENDING` or `DUE` state with a valid future `dueOdometer`.
- Use only valid `ODOMETER_UPDATED` audit records within the preceding 90
  days. Require at least three strictly increasing readings, at least 30 days
  between the earliest and latest, and a latest audited reading equal to the
  vehicle's current master reading. If data is insufficient, stale, or
  inconsistent, omit predictions rather than inventing a rate.
- Calculate each consecutive interval's distance per day, use the median
  rate, and estimate the Manila calendar date the current odometer will reach
  the schedule's due reading. Return only estimates zero to 30 days ahead.
- Show the vehicle, schedule, current and due odometers, remaining distance,
  estimated due date, and sample span. Provide a link to the existing
  schedule; do not create or edit it from the prediction panel.
- Keep the existing transaction-driven status refresh and notifications.
  Predictions are not a second status authority.

### Seed data

- Seed only clearly synthetic demonstration records and resolve references
  through the current registered garages, vehicles, mechanics, templates,
  and work-order records.
- Preserve the current schema: `MaintenanceSchedule.vehicleId` remains the
  vehicle plate-number value and schedule garage remains the current
  denormalized value; ensure both match the selected vehicle's records.
- Make the seed repeatable and non-destructive. Do not delete existing
  schedules or checklist items, overwrite existing vehicles, or reactivate
  soft-deleted reference records. Use stable fixture identities and skip
  conflicts rather than mutating existing operational records.
- On an empty development database, shift the synthetic maintenance fixture
  timeline relative to the Manila seed day while keeping fixture identities
  stable. Resolve every seeded schedule's garage from its vehicle's current
  registered garage assignment.
- Seed completed-to-successor examples using the same completion timestamp,
  submitted service odometer, and recurrence rules as the live flow. A
  cancelled occurrence has no successor.
- Include synthetic odometer audit history sufficient to demonstrate a
  prediction, ending at the seeded vehicle's master odometer. Do not add
  real operational or personal data to source-controlled fixtures.

## API, data, and security impact

- Add `GET /maintenance-schedules/predictions`, protected by VMMS
  authentication and the Operations role.
- Read `Vehicle`, `VehicleAuditLog`, and eligible `MaintenanceSchedule` rows;
  persist no prediction or derived status.
- No migration, shared-service, analytics, or mobile write-path change is
  required.
- Return no mechanic identity, email, or audit actor details in predictions.

## Acceptance criteria

1. A new schedule form exposes Due Date but no editable Start Date. Its
   internal start date is the Manila creation day and remains unchanged on
   edits.
2. Time-triggered schedules derive their internal reference date from Due
   Date and the selected interval; recurrence and existing date audit behavior
   remain intact.
3. Only Operations can retrieve predictions. The endpoint is read-only and
   returns only active, eligible schedules with valid predictions.
4. Estimates use the approved 90-day, three-reading, 30-day-span, median-rate,
   30-day-horizon rules. Insufficient, stale, non-increasing, or inconsistent
   history yields no estimate.
5. The web panel displays predictions as suggestions linking to the existing
   schedule; it never creates schedules, changes statuses, or sends
   notifications.
6. Synthetic seed fixtures are repeatable, relationally consistent with the
   existing schema, use current relative dates, and do not delete or overwrite
   populated records.
7. Seeded audit history supports at least one visible prediction without using
   real operational or personal data.
8. Existing vehicle odometer updates continue to refresh eligible schedules
   transactionally; no duplicate polling-based odometer refresh is added.
9. Seeded schedule garages match each vehicle assignment, recurring successors
   match live completion-based recurrence, and cancelled occurrences stop the
   chain.

## Affected repositories

- `welinc-backend-vmms`: read-only prediction service/route and safe,
  relationship-consistent synthetic seed behavior.
- `welinc-web-vmms`: due-date-first schedule form and Operations prediction
  panel.

## Delivery status

Design decisions are approved, and backend, seed, and web implementation is
complete. Build and seed type checks pass. Database-seed, authenticated browser,
and integrated API verification remain pending; see [verify.md](verify.md).
