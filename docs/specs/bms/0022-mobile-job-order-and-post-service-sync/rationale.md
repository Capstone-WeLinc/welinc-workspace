# 0022. Rationale: mobile job order and post-service sync

Decision record for [index.md](index.md).

## Context

Spec 0010 shipped the mobile app with an offline SQLite cache and a sync service, but left the sync off (`TEAM_JOB_ORDER_ROUTES_READY = false`) because the BMS backend had no routes for drivers and helpers. A real driver signing in sees no job orders, and post-service forms never leave the phone.

Several facts in the current BMS code shape the design:
- The gateway route table sends `/bms/job-order/...` (singular) to dispatch and `/bms/post-service/...` to completion.
- Assignments store team member record ids (`drivers.id`, `helpers.id`). The login is linked through `user_id`, as for self-service leave (spec 0005).
- The completion save sets `finalizedBy` to whoever saves. Daily Sales drafts show a booking only to the Customer Support user in `finalizedBy`, or to everyone when it is empty.
- The completion save rejects payment fields on purpose: money is recorded by Customer Support and verified by Admin. The web's methods are Cash, BDO, GCash and Xendit.
- The web's Post-Service page saves the whole record each time and finalizes with `postServiceStatus = 'Finalized'`.

## Options considered

### Route paths

**`/bms/job-orders/mine` and `/bms/job-orders/:id/post-service`: rejected.** The gateway doesn't route `/bms/job-orders/`, so both would answer 404. Fixing that means splitting one URL prefix across two services in `routes.ts`.

**One route per owning service, under existing prefixes: chosen.** Job orders live in dispatch (`/bms/job-order/mine`) and post-service in completion (`/bms/post-service/mine/:bookingUuid`). The gateway needs no change.

### Who is recorded on a driver's submission

**Keep setting `finalizedBy` to the driver: rejected.** Daily Sales would show the booking only to a Customer Support user whose id equals the driver's, which is none, so the booking disappears from every draft list.

**A separate `submittedBy`: chosen.** The driver route never touches `finalizedBy`, which keeps its meaning (the office user who finalized). The web's save is unchanged.

### The payment method the driver reports

**Drop payment from the app: rejected.** It is the simplest option, but it throws away what the driver saw at the client, and Customer Support would have to ask for it again.

**Let the driver create a collection: rejected.** It breaks the rule that Customer Support records money and Admin verifies it.

**Store it as a report that pre-fills Daily Sales: chosen.** `reportedPaymentMethod` and `reportedAddOnPayment` are kept apart from collections and used only as the suggested method. Customer Support still adds the reference and submits.

### When the form locks

**As soon as the driver's submission is accepted: rejected.** A driver who notices a mistake could not correct it.

**When the office finalizes: chosen.** The driver can correct and resubmit until `postServiceStatus = 'Finalized'`. After that, the office's record is final.

### A driver resubmitting over the office's edits

Locking only at finalize allows a case where Customer Support corrects the record on the web, and the driver then resubmits the whole form from an older copy. A form queued offline could do this hours later.

**Last save wins: rejected.** Simple, but office corrections disappear with no warning.

**Lock the form as soon as Customer Support first saves: rejected.** Safe, but the driver can no longer fix a typo once the office has opened the record. This partly undoes the "lock at finalize" choice.

**Refuse saves made from an outdated copy: chosen.** The phone sends the version it last saw (`baseVersion`). If the record changed after that, the server refuses and returns the office's version, which the phone shows to the driver. This is the same idea as the VMMS backend, which only saves a work order while `updatedAt` is unchanged since it was read.

### When the app syncs

**Only on sign-in, foreground, pull to refresh and submit (the 0010 behavior): rejected.** A form waits even after signal comes back while the app stays open, and new job orders appear only when the driver does something.

**Background sending while the app is closed: rejected for now.** Android and iOS decide when background tasks run, often minutes to hours later, so it adds complexity without a reliable result.

**Add a reconnect listener and a foreground timer: chosen.** NetInfo sends waiting forms as soon as the phone is online, as the VMMS app does. A timer keeps job orders close to live while the app is open.

## Decisions and tradeoffs

- **`PUT` rather than `POST`.** The app sends the whole form, and a weak signal can send it twice. `PUT` saves the same result each time and matches what the app already sends.
- **Booking UUID as the phone's job order id.** Dispatch and completion both key by booking UUID, so the upload needs no id lookup. Real sign-ins had no cached job orders before this, so nothing on phones needs converting.
- **Driver check in dispatch.** Completion doesn't know who is assigned. It asks dispatch through a service-key route, as it already does for post-service readiness. One route (`team-bookings`) serves both the check and the driver's status list.
- **Post-service status from completion, not inside the job order route.** The first design had dispatch call completion to put the submitted and locked flags on each job order card. Dispatch has no `COMPLETION_API_URL` in Docker Compose or staging, so that would have added a new setting in two places, and a missing setting would only show up as a failing route in staging. Completion already calls dispatch, so the phone reads the flags from `GET /bms/post-service/mine` instead. The cost is one extra request per sync, for drivers only.
- **Charge lines add up to the booking amount.** The app shows the sum of the lines as the total, and the booking amount already includes the add-ons. Listing the full amount plus each add-on would have counted them twice, so the service line carries the amount minus the priced add-ons.
- **Names don't block the sync.** Driver, helper and vehicle names come from Auth and VMMS. When either is down, the cards load with placeholder names rather than failing, so a driver still sees the trip.
- **Admin Retry keeps the finalizer.** Retry used to go through the web save and make the Admin the finalizer. On a driver's submission that would hide the booking from every Customer Support user's drafts, the same problem `submittedBy` solves. Retry re-sends the same content, so it now changes no owner.
- **Guarded write.** The version check reads the record and then writes. The driver's write only applies while `updatedAt` is unchanged, so a web save landing between the two is not overwritten.
- **`lastEditedBy` in the version check.** A plain `updatedAt` comparison would also refuse a driver's own retry when the save succeeded but the reply was lost. Refusing only when someone else saved last avoids false warnings, at the cost of one more column.
- **Web save not version-checked.** Customer Support edits a page it just loaded and is the one who finalizes. Checking it too would add a conflict path to the web for little benefit.
- **Bank transfer relabelled BDO.** Drivers and Customer Support see the same method name. The stored app value stays `BANK_TRANSFER`, so saved records need no migration.
- **45-second refresh.** Short enough that a new assignment appears almost live, long enough to keep load low. It runs only in the foreground.
- **Stop retrying on some errors.** The VMMS app retries every failed upload forever. A 400 or a finalized record will never succeed by retrying, so those stop until the driver acts. Offline, not-ready (409) and 5xx keep retrying.
- **Real sign-in shows the downloaded list as is.** The screens filtered job orders by comparing their ids with `TeamMember.teamMemberId`. A real sign-in never fills it, and the server now sends team member record ids, so every real job order would have been hidden. Filling it would need another route. The server already sends only the caller's own job orders, and the cache is cleared when another user signs in, so the filter is kept only for seeder data.
- **Submitted jobs can be opened again.** The Post Service list only let ongoing jobs open the form. With the lock at finalize, the driver needs a way back in after submitting, so a submitted job shows Edit Record and a finalized one View Record.
- **403 stops retrying.** A form for a job the person isn't the driver of will never be accepted, so it is treated like a 400. A 404 keeps retrying, because it is what the app gets while the backend isn't deployed yet.
- **No web change.** The web Post-Service page already lists completed records with an arrival time, and Daily Sales already shows a suggested method. Only the order in which that suggestion is chosen changes, on the backend.
