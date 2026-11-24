# 0012. Predictive maintenance readiness: rationale

Decision record for [index.md](index.md).

## Context

Vehicle master-reading changes already refresh eligible odometer schedules
transactionally. A second polling job would duplicate that authority and could
make displayed status lag behind the source update. Vehicle odometer audit
records provide a history from which conservative Operations-facing estimates
can be derived without changing current schedules.

The schedule form currently asks for both Start Date and Due Date, and
time-triggered schedules additionally use an internal start reference for
recurrence. Operations selected Due Date as the only user-entered schedule
date, while retaining internal lifecycle dates.

The seed currently has cleanup and update behavior that is unsuitable for
repeatable use against a populated development database. The approved seed
approach is synthetic and non-destructive; existing model relationships are
retained for this slice.

## Options considered

### Add a polling odometer status job

**Rejected**: master-odometer writes already refresh schedule status in the
same transaction. A second job would duplicate the write path and create
avoidable status races.

### Generate predictions from the latest reading only

**Rejected**: a single reading provides no usage rate and cannot support an
estimated due date.

### Predict from all-time average odometer usage

**Rejected**: old operating patterns can mislead estimates when a vehicle's
usage has changed.

### Conservative recent-history estimate (chosen)

Use valid audit readings in a 90-day lookback, require at least three
increasing readings spanning 30 days, use the median per-day rate, and show
only estimates within a 30-day horizon.

**Advantages**:
- Makes the estimate explainable and bounded by recent usage.
- Avoids presenting a prediction when the vehicle has insufficient or
  inconsistent history.
- Keeps Operations as the decision maker; no work-order is created or changed.

**Tradeoff**: vehicles with sparse odometer updates will have no prediction
until enough history exists.

## Smaller decisions

- Use the vehicle master odometer and its append-only audit history as the
  only prediction inputs; schedule reference readings remain interval anchors.
- Require the latest audit value to match the master reading, rather than
  silently extrapolating from stale data.
- Keep seed fixtures synthetic and non-destructive. Existing identities and
  relational keys are reused only as references; fixture records do not
  overwrite populated business data.
- Shift the maintenance demo timeline to the current Manila seed day on an
  empty database, anchored to stable fixture identities. This keeps upcoming
  and historical examples useful without accumulating a new fixture per seed
  date.
- Derive schedule garage values from the vehicle's registered garage rather
  than duplicating manually chosen branch values in each fixture.
- Seed recurrence from the same submitted completion timestamp and service
  odometer used by the live approval flow; do not generate a successor from a
  cancelled schedule.
- Keep Due Date user-entered. Use Manila creation day for internal `startDate`
  and derive a time-trigger reference from Due Date and its interval.
- Keep predictive values ephemeral and read-only; do not add a stored
  forecast, a new notification type, or a work-order creation path.
