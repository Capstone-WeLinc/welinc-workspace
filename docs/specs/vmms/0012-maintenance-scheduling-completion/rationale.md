# 0011. Maintenance scheduling completion: rationale

Decision record for [index.md](index.md). The index is the build contract.

## Context

The Module 3 audit found no schedule-extension request/review workflow, no
dedicated date-change audit trail, inconsistent urgency colors, and
inconsistent searchable selectors. Existing schedule creation, cancellation,
overdue evaluation, in-app notifications, and escalation behavior already
have owners and contracts.

## Options considered

### Let a Mechanic edit the due date directly

**Rejected**: bypasses Admin approval and does not preserve the request,
decision, and date-change history.

### Admin-reviewed extension requests (chosen)

Keep the current target date until an Admin approves a request. Persist the
request and review state, and append request/decision events and a reschedule
event in the same transactions as their business changes.

**Advantages**:
- Enforces the user-approved role boundary at the API.
- Keeps the prior date until approval and makes each decision traceable.
- Reuses the existing schedule and overdue lifecycle rather than creating a
  replacement schedule.

**Tradeoff**: request, review, and reschedule history require additive
persistence and a migration.

### Store only mutable extension rows as audit

**Rejected**: a mutable review-status row is workflow state, not immutable
event evidence under Spec 0010. Keep request state and append-only audit
events separate.

## Smaller decisions

- Count all submitted requests, including rejected requests, toward the
  two-request lifetime limit. Do not provide request withdrawal in this
  slice.
- Require a later date than the current target date, but do not add an
  arbitrary maximum or a separate future-date restriction.
- Permit an overdue extension only when the lifecycle explicitly preserves
  `IN_PROGRESS` as its prior state. Restore that state only if the approved
  target is no longer past due in Manila time.
- Keep the lifecycle status enum and Spec 0008 transition contract unchanged.
- Derive the schedule garage from the selected vehicle's garage assignment;
  a separate schedule-level garage choice could contradict the vehicle
  record.
- Use status colors consistently across applicable web and VMMS mobile
  surfaces; keep Done, In Progress, and closed states visually distinct from
  the urgency legend.
- Search existing options in applicable selectors without changing their
  data source, authorization, or active-only rules.
- Use prior entered Parts Used values as suggestions only. Do not create a
  managed parts catalog or restrict new values.
- Leave Semaphore SMS delivery out of scope; preserve and verify current
  in-app notification and escalation behavior.
