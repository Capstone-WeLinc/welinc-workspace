# 0011. Post-service payment summary, Xendit and notification back navigation: rationale

Decision record for [index.md](index.md). The index is the build contract.

## Context

The Post Service form showed one "Estimated Total" (booking charges plus
add-ons), with no sign of what the client had already paid. Payment methods
were Cash, GCash and Bank Transfer, while the BMS completion service already
records Xendit collections. The app has no navigation library: `App.tsx`
switches tabs and remounts the tab's screen. Tapping a notification switched
to Job Orders or Post Service, so Back there went to that tab's list, not to
Notifications.

## Payment summary

### Total includes add-ons (chosen)

Total Service Amount = booking charges + add-ons ticked on the form, the same
amount the old "Estimated Total" showed. The add-ons are part of what the
service costs the client.

Alternative: booking charges only, since the backend checks the down payment
against the booking amount. Not chosen, because the total would then leave out
add-ons the client still owes. Changing this is one line in
`PostServiceFormScreen.tsx`.

### Smaller decisions

- The calculation is in a small shared helper (`getPaymentBreakdown`), not in
  the screen, so it can be checked on its own.
- It works in centavos, so e.g. ₱10,000.10 − ₱3,000.20 is exactly ₱6,999.90.
- A missing, negative or non-numeric down payment counts as `₱0.00` instead
  of failing, and the down payment row is always shown, as requested.
- The sync accepts `downPayment` and `downpayment`, because the booking
  service names the column `downpayment` and the mobile route doesn't exist
  yet.

## Xendit

- Added as a new option in both pickers. No existing option was removed,
  renamed or reordered.
- Booking payment method `Xendit` (label) maps to `XENDIT` (stored value)
  through the existing label lookup, so bookings made with Xendit pre-select
  it.
- Allowing `XENDIT` in SQLite needed a table rebuild. The first version of
  this change added Xendit to the add-ons payment only (database version 2).
  Xendit for the booking payment method followed as version 3. Version 3
  rebuilds whenever the stored definition differs from the current one, so
  version 1 phones, version 2 phones and fresh installs all end up with the
  same table.

## Notification back navigation

### Pass a notification flag to the opened screen (chosen)

`App.tsx` keeps `fromNotification` next to the job order it opens. The Job
Orders and Post Service screens remember which job order the notification
opened. Only that one goes back to Notifications.

### Rejected alternatives

- **Always go back to Notifications from these pages.** This would break
  Home → job order → Back, and list → job order → Back. The request asked not
  to change Back globally.
- **Add a navigation library with a back stack.** Too big a change for one
  behavior, and it would change how every tab works.
- **A separate screen for notification-opened pages.** It would duplicate the
  details and form screens.

### Smaller decisions

- Switching tabs clears the notification context, so a later normal visit is
  unaffected.
- Opening another job order from the list clears it too. Back then goes to
  the list even if the user reopens the same job order.
- Submitting a form opened from a notification keeps the existing result: the
  Post Service list with the success message.
- Returning to Notifications remounts it, like any tab switch, so its filter
  resets to All. Keeping the filter would mean lifting that state into
  `App.tsx`. Not done in this change.
