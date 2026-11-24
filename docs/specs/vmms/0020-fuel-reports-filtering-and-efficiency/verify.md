# Verification — 0020 Fuel reports filtering and efficiency

All checks are pending approval and implementation. They are derived from the
acceptance criteria in [index.md](index.md).

## Period and anomaly filtering

- [ ] Use fill-ups at the start/end boundaries of Manila date ranges and
  confirm fleet-wide, per-vehicle, anomaly, and export membership → AC-1, AC-2,
  AC-4
- [ ] Include anomalies detected inside the period but linked to fill-ups
  outside it, and the reverse; confirm approved linked-fill-up date behavior
  → AC-2
- [ ] Confirm preset periods send/record their effective dates just like custom
  ranges → AC-1, AC-5

## Efficiency and export parity

- [ ] Verify voided and partial-tank entries are excluded from eligible
  efficiency calculations → AC-3
- [ ] With known valid cycle distances and liters, verify fleet efficiency is
  total valid distance divided by total valid fuel → AC-3
- [ ] Verify insufficient full-tank history displays `Insufficient Data` and
  does not produce a misleading zero → AC-3
- [ ] Export CSV/PDF/Excel for each supported view and compare rows and totals
  with the on-screen filtered report → AC-4
- [ ] Confirm audit metadata contains actor, view, format, and effective dates
  but not report contents → AC-5

## States, roles, and regression

- [ ] Distinguish loading, empty, failed request, and invalid range states;
  confirm failed requests never fall back to all-time results → AC-6
- [ ] Verify Admin/Operations report access and existing fuel-entry,
  voiding, anomaly, and escalation permissions → AC-7

## Acceptance-criteria coverage

| AC | Planned evidence |
| --- | --- |
| AC-1–AC-2 | Manila date boundaries and anomaly membership |
| AC-3 | Valid-cycle efficiency and void/insufficient-data cases |
| AC-4–AC-5 | Export parity and audit metadata checks |
| AC-6–AC-7 | Failure-state and role/regression checks |

## Implementation evidence

No implementation or verification has been performed for this proposal.
