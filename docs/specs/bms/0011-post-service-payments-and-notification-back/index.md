# 0011. Post-service payment summary, Xendit and notification back navigation

**Status**: Implemented in `welinc-mobile-bms` (branch `feature/bms-mobile-app`,
commit `0438c04`); device-level acceptance pending  
**Scope**: BMS mobile app, follow-up to
[0010. Mobile app first version](../0010-mobile-app-first-version/index.md)

Decision history: [rationale.md](rationale.md). Verification: [verify.md](verify.md).

## Summary

Three changes to the driver/helper mobile app:

1. The Post Service form shows the full payment breakdown: Total Service
   Amount, Down Payment and Remaining Balance.
2. Xendit is added as a payment option, both for the booking's **Payment
   method** and for the **Add-ons payment**.
3. A job order or post-service form opened by tapping a notification goes
   back to Notifications. Opened any other way, Back works as before.

Touches only `welinc-mobile-bms`. No change to `welinc-backend-bms`,
`welinc-web-bms`, shared auth, portal or the suite gateway.

## Sources and decisions

- User request to show the total, down payment and remaining balance on the
  Post Service page, add Xendit as a payment method, and return to
  Notifications when a page was opened from one.
- The BMS booking service already stores a booking's down payment
  (`bookings.downpayment`, decimal, nullable, never above the booking amount).
- The BMS completion service already treats Xendit as a collection method
  (`Cash`, `BDO`, `GCash`, `Xendit`).

## Behavior and controls

### Payment summary (Post Service form)

The old "Estimated Total" line is replaced by three rows, always shown:

| Row | Value |
|---|---|
| Total Service Amount | Booking charges + add-ons ticked on the form |
| Down Payment | The booking's down payment; `₱0.00` when there is none |
| Remaining Balance | Total − Down Payment, never below `₱0.00` |

- Amounts use peso format with centavos, e.g. `₱10,000.00`.
- The calculation (`getPaymentBreakdown` in `utils/money.ts`) works in
  centavos, so there are no rounding errors. A missing, negative or non-numeric
  down payment counts as `₱0.00`.
- Remaining Balance reads "Fully paid" at `₱0.00`, otherwise "Still to be paid
  by the client".
- The total updates as add-ons are ticked or unticked.
- Job orders now carry `downPayment` (pesos, `0` when none). The sync reads
  the server's `downPayment` or `downpayment` field, as a number or decimal
  text. Seeder mode has sample values: the ongoing Santos Trading job is
  ₱8,790.00 total with a ₱3,000.00 down payment.

### Xendit payment

| Picker | Options |
|---|---|
| Payment method | Cash, GCash, Bank Transfer, **Xendit** |
| Add-ons payment | Paid on delivery (COD), Paid via GCash, Paid via Bank Transfer, **Paid via Xendit**, Not yet paid |

- Existing options are unchanged. Xendit uses the same picker and selection
  style.
- The value saved and sent with the post-service record is `XENDIT`.
- A job order booked as "Xendit" now pre-selects Xendit, the same way GCash
  and the other methods already do.

### Back from a notification

- Tapping a notification still marks it read first, then opens the job order
  (Job Orders) or, for a driver's reminder, the post-service form.
- The app passes `fromNotification` to the screen it opens. Only that job
  order or form goes back to Notifications, through both the on-screen Back
  button and Android's back key. Its screen reader label becomes "Back to
  notifications".
- Anything opened from a list, from Home or after switching tabs keeps its
  normal Back behavior. Switching tabs clears the notification context.
- Submitting a form opened from a notification still shows the Post Service
  list with the success message, as before.
- Returning to Notifications resets its All/Unread filter to All.

### Offline database

`bms_mobile.db` goes from version 1 to version 3. Phones upgrade on the next
app start and keep their saved records:

| Version | Change |
|---|---|
| 2 | `job_orders.downPayment` (REAL, default 0, never negative); `post_service_records.addOnPayment` accepts `XENDIT` |
| 3 | `post_service_records.paymentMethod` accepts `XENDIT` |

- SQLite can't change a CHECK rule in place, so `post_service_records` is
  rebuilt with its rows copied over in one transaction. The rebuild only runs
  when the table's stored definition differs from the current one, so fresh
  installs and repeat runs skip it.
- Fixes an existing bug: the old `addOnPayment IN (..., NULL)` rule never
  rejected anything, because SQLite treats a comparison with NULL as unknown
  and a CHECK passes on unknown. It is now
  `addOnPayment IS NULL OR addOnPayment IN (...)`.

## Acceptance criteria

1. The Post Service form shows Total Service Amount, Down Payment and
   Remaining Balance, in that order, in `₱0,000.00` format.
2. No down payment shows `₱0.00`, and the remaining balance equals the total.
3. A partial down payment gives total minus down payment. A full or larger
   down payment gives `₱0.00`. The balance is never negative.
4. The values come from the job order and the ticked add-ons, not hard-coded
   amounts.
5. Xendit appears in both pickers, can be selected, and is saved and sent as
   `XENDIT`. The existing options still work.
6. Notifications → notification → target page → Back returns to
   Notifications.
7. Opening the same page normally (list, Home) keeps the existing Back
   behavior.
8. After leaving the notification-opened page (switching tabs, or opening
   another item from the list), Back does not jump to Notifications.
9. Tapping a notification still marks it read.
10. Phones on database version 1 or 2 upgrade without losing saved
    post-service records.

## Impact

- `welinc-mobile-bms`: `App.tsx`, `screens/PostServiceFormScreen.tsx`,
  `screens/PostServiceScreen.tsx`, `screens/JobOrdersScreen.tsx`,
  `screens/JobOrderDetailsScreen.tsx`, `database/tables.ts`,
  `database/database.ts`, `repositories/JobOrderRepository.ts`,
  `services/SyncService.ts`, `seeders/payments.ts`, `seeders/jobOrders.ts`,
  `types/bms.ts`, `utils/money.ts`.
- No backend, web, shared auth, gateway or API change.

## Follow-up for the backend

The BMS backend still has no driver/helper routes for job orders and
post-service (see spec 0010), so these values are not sent or downloaded yet.
When the routes are built:

- `GET /bms/job-orders/mine` should include the booking's down payment
  (`downPayment` or `downpayment`).
- `POST /bms/job-orders/:id/post-service` must accept `XENDIT` for both
  `paymentMethod` and `addOnPayment`.

## Implementation and verification status

The mobile implementation is complete and type-checks. The payment calculation
and the database upgrade were checked with scripts. Checking the screens and
navigation flows on a device is still pending. See [verify.md](verify.md).
