# Verify: Post-service payment summary, Xendit and notification back navigation · spec 0011

Steps derived from the acceptance criteria in [index.md](index.md).

## Automated

The repo has no test runner yet. These checks were run as one-off Node
scripts (Node 24, `node:sqlite`) against the real `utils/money.ts` and
`database/tables.ts`. They are not committed to the repo.

- [x] Payment breakdown: no down payment (₱10,000.00 → ₱10,000.00), partial
  (₱10,000.00 − ₱3,000.00 → ₱7,000.00), full (→ ₱0.00), overpaid (→ ₱0.00,
  never negative), seeder job (₱8,790.00 − ₱3,000.00 → ₱5,790.00), centavos
  (₱10,000.10 − ₱3,000.20 → ₱6,999.90), invalid or negative down payment
  (→ ₱0.00), and comma grouping (₱1,234,567.50) → AC-1, AC-2, AC-3
- [x] Database version 1 → current: saved records kept, `downPayment` added
  with default 0 and negatives rejected, `XENDIT` accepted for both
  `paymentMethod` and `addOnPayment`, unknown values rejected, index
  recreated, running again changes nothing → AC-5, AC-10
- [x] Database version 2 → current: saved records kept, `XENDIT` payment
  method rejected before and accepted after → AC-5, AC-10
- [x] Fresh install: tables already current, no rebuild, `XENDIT` accepted
  → AC-5

## Device / manual

Run in seeder mode (`EXPO_PUBLIC_USE_SEEDER_AUTH="true"`) as the driver
account, after `npx expo start -c`.

- [ ] Post Service → Santos Trading (ongoing) → Edit: Total Service Amount
  ₱8,790.00, Down Payment ₱3,000.00, Remaining Balance ₱5,790.00 → AC-1, AC-3,
  AC-4
- [ ] Tick add-ons: the total and remaining balance go up by the add-ons'
  prices → AC-4
- [ ] Payment method picker shows Cash, GCash, Bank Transfer, Xendit; select
  Xendit → AC-5
- [ ] Tick an add-on; the Add-ons payment picker shows Paid via Xendit; select
  it and submit. The record saves and the job shows as done → AC-5
- [ ] Each existing payment option can still be selected and submitted → AC-5
- [ ] **Test 1**: Notifications → tap a job order notification → Job Order
  Details → Back (button, and Android back key) → Notifications. The
  notification is now read → AC-6, AC-9
- [ ] As the driver, tap a post-service reminder → form → Back →
  Notifications → AC-6
- [ ] **Test 2**: Job Orders → job order → Back → Job Orders list. Home →
  booking → Back → Job Orders list → AC-7
- [ ] **Test 3**: open a job order from a notification, switch to another tab,
  then open a job order normally → Back goes to the list, not Notifications
  → AC-8
- [ ] **Test 4**: Post Service → Edit → Back → Post Service list → AC-7
- [ ] Install the previous build, submit a form, update to this build:
  the form is still there and the app opens normally → AC-10

## Commands

- [x] `npx tsc --noEmit` (in `welinc-mobile-bms`): passed
- [x] Payment breakdown script: 9 cases passed
- [x] Database migration script: version 1, version 2 and fresh install cases
  passed

## Acceptance-criteria coverage

- Scripts cover the calculation (AC-1 to AC-3) and the database side of
  Xendit and the upgrade (AC-5, AC-10).
- The screens and navigation (AC-4, AC-6 to AC-9) were checked by reading
  the code only. They still need the device steps above.
