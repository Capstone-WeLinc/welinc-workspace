# 0008. Maintenance status lifecycle: rationale

Decision record for [index.md](index.md). The index is the build contract.

## Context

Maintenance status is changed by schedule create/edit, mechanic workflow,
chief-mechanic review, a daily overdue job, odometer refresh, cancellation and
recurrence. `OVERDUE` can wrap an in-progress job, while `DONE` is pending
review and `COMPLETED` is approved. A status enum alone does not explain the
allowed actor or trigger.

## Options considered

### One generic status update

Allow clients or a shared state endpoint to assign any enum value.

**Rejected**: it bypasses checklist, assignment, approval, cancellation, and
audit rules.

### Document and test the existing lifecycle (chosen)

Keep all existing routes and guards, publish the allowed transitions and
automated triggers, and add tests that bind the table to implementation.

**Advantages**:
- Makes system-derived and role-driven changes reviewable.
- Avoids changing user-visible workflow or historical data.
- Preserves the overdue-in-progress marker and separate approval axis.

**Tradeoff**: this slice does not redesign the underlying schedule service
into one central transition function.

## Smaller decisions

- Keep `OVERDUE` as a schedule status and retain the prior execution phase in
  `workOrderProgress`; do not add an enum value.
- Treat cancellation requests and maintenance-log voids as distinct from
  routine scheduling edits.
- Do not infer a new time-based `DUE` transition; the current daily process
  changes eligible past-due schedules to `OVERDUE`.
