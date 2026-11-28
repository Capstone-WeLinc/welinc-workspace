# 0022. Mobile job order and post-service sync for team members

**Date**: 2026-11-28
**Status**: Backend and mobile app implemented, not yet in pull requests; not yet tested on a phone
**Scope**: `welinc-backend-bms` (dispatch, completion) and `welinc-mobile-bms`. No change to `welinc-web-bms`, shared auth, portal or the suite gateway (Nginx).

Decision history: [rationale.md](rationale.md). Verification plan: [verify.md](verify.md).

Follow-up to [0010. Mobile app first version](../0010-mobile-app-first-version/index.md), which left `TEAM_JOB_ORDER_ROUTES_READY = false` until these routes existed. The sync pattern follows the VMMS mobile backend and app (`welinc-backend-vmms-mobile_development`, `welinc-mobile-vrms_vmms`), used as a read-only reference.

## Summary

Drivers and helpers see the job orders assigned to them in the mobile app, and a driver's post-service form reaches the web. Three new team member routes carry the data: `GET /bms/job-order/mine` in dispatch, and `GET /bms/post-service/mine` and `PUT /bms/post-service/mine/:bookingUuid` in completion. The app keeps working offline. Forms wait on the phone and are sent when the internet returns, and the app refreshes on its own every 45 seconds while open. A driver's submission never hides a booking from Customer Support, and never silently replaces an edit the office made on the web. The payment method the driver reports pre-fills Daily Sales, but money is still recorded only by Customer Support and verified by Admin.

## Requirements

**User stories**:
- As a driver or helper, I want to see the job orders I am assigned to, so that I know my trips without asking the office.
- As a driver, I want to submit the post-service form from the phone, even without signal, so that the office gets it as soon as I am online.
- As Customer Support, I want a driver's submission to show in Post-Service and Daily Sales with the reported payment method, so that I only add the reference and submit.
- As Customer Support, I want my corrections on the web to stay, even if the driver submits again from an older copy.
- As a driver, I want the form to stop accepting changes once the office finalizes it, so that I know the record is closed.

**Acceptance criteria**:
- **AC-1**: `GET /bms/job-order/mine` (roles `DRIVER`, `HELPER`) returns `{ jobOrders }` with every active job order whose confirmed assignment has the caller as driver or helper, found through `drivers.user_id` / `helpers.user_id`. Other team members' job orders, cancelled bookings and superseded job orders are never returned. A caller with no active team member record gets an empty list.
- **AC-2**: Each job order has the shape the app stores (section "Job order card"). `id` is the booking UUID. Status is `PENDING` (generated, not distributed), `ONGOING` (distributed) or `COMPLETED` (booking completed).
- **AC-3**: `PUT /bms/post-service/mine/:bookingUuid` accepts a submission only from the job order's assigned driver. Helpers, other drivers and other roles get 403. The existing checks apply: the job order is distributed and ready, the booking isn't cancelled, and times and text are valid.
- **AC-4**: `serviceCompleted: true` (or a reported issue) completes the work through the same booking completion step as the web form. `serviceCompleted: false` without an issue saves a draft.
- **AC-5**: The driver is stored in `submittedBy`. The driver route never sets `finalizedBy` or `finalizedAt`, so the booking shows in Daily Sales drafts for every Customer Support user.
- **AC-6**: The driver's payment report is stored as `reportedPaymentMethod` and `reportedAddOnPayment` in web method names (Cash, BDO, GCash, Xendit, and Unpaid for add-ons). Daily Sales drafts suggest `reportedPaymentMethod` first, else the method guessed from the booking. No collection is created from the app. The web's `PUT /bms/post-service/:id` still rejects payment fields.
- **AC-7**: Each answer carries `version` (the record's `updatedAt`). A driver submission whose `baseVersion` differs from the saved record, when the last save was by someone else (`lastEditedBy`), gets 409 `POST_SERVICE_CHANGED` with `current` and saves nothing. A retry of the driver's own last save is accepted.
- **AC-8**: A submission for a record with `postServiceStatus = 'Finalized'` gets 409 `POST_SERVICE_FINALIZED` and saves nothing. `GET /bms/post-service/mine` (role `DRIVER`) lists, for each of the driver's bookings, whether a form was sent, whether it is finalized, and its `version`. The app shows a finalized form read-only with "Finalized by office".
- **AC-9**: The app uploads waiting forms first, then downloads job orders and replaces its cache in one SQLite transaction. A failed download keeps the last good cache. A job order whose form is still waiting keeps the phone's status.
- **AC-10**: The app syncs on sign-in, app open, return to the foreground, pull to refresh, submit, when the phone gets internet back, and every 45 seconds while in the foreground. Concurrent syncs share one run.
- **AC-11**: Failed uploads follow the table in "Upload failures". 400 and `POST_SERVICE_FINALIZED` stop retrying until the driver submits again. `POST_SERVICE_CHANGED` replaces the phone's copy with `current`. Offline, 409 (not ready) and 5xx keep the form queued.
- **AC-12**: Helpers never see the post-service form. Seeder mode keeps working without the backend.

## Decision

Follow the VMMS pattern: ordinary routes that return only the caller's records, with the app doing the sync. Each route lives in the service that owns its data, under a path the gateway already routes. The driver route records `submittedBy` and reported payment fields separately from the office's fields. It refuses saves made from an outdated copy only when someone else changed the record. See [rationale.md](rationale.md) for the options considered.

## Feature design

### Sync on the phone

Screens always read from SQLite, so the app works the same online and offline. One sync does, in order:

1. **Upload.** Every post-service record waiting on the phone (`syncPending = 1`, not `syncBlocked`) is sent with its `baseVersion`.
2. **Download.** `GET /bms/job-order/mine`, and for drivers `GET /bms/post-service/mine` for the submitted and finalized flags.
3. **Replace the cache.** In one transaction, job orders received are added or updated and job orders no longer sent are deleted. The flags from step 2 fill `postServiceFormSubmitted` and `postServiceLocked`. If either download fails, nothing in the cache changes.

| Trigger | Before | Now |
|---|---|---|
| Sign-in, app opened, back in the foreground, pull to refresh, submit | Yes | Yes |
| Phone gets internet back (mobile data or Wi-Fi) | No | Yes, through `@react-native-community/netinfo` |
| While the app is open and in the foreground | No | Every 45 seconds |

Nothing is sent while the app is fully closed. A waiting form is sent the next time the app is opened.

### Upload failures

| Server answer | The record | The driver sees |
|---|---|---|
| No connection, timeout | Stays queued | "Saved on this phone. It will be sent when you're online." on the form; "Waiting to be sent" on the card |
| 409 (job order not ready), 404 (backend not deployed yet), 5xx | Stays queued with the reason, retried on the next sync | "Not sent yet: (server's message) It will be retried automatically." |
| 409 `POST_SERVICE_FINALIZED` | Blocked; the office's version is kept | "Finalized by office. This record can no longer be changed.", form read-only |
| 409 `POST_SERVICE_CHANGED` | Replaced by `current`, `syncPending = 0` | "The office updated this record. Check it and submit again if needed." Form stays editable |
| 400, 403 (not this driver's job) | Blocked until the driver submits again | "Not sent: (server's message). Fix it and submit again."; "Not sent" on the card |
| 401 after token refresh | Stays queued | Signed out, as today |

### `GET /bms/job-order/mine` (dispatch)

- Declared before `GET /job-order/:id` so `mine` isn't read as an id. The method-level roles override the controller's `ADMIN`, `OPERATIONS`.
- The caller's team member record is found by `user_id`, as `crew-leave/self` does.
- Answer: `{ jobOrders: JobOrder[] }`.

#### Job order card

| App field | Source |
|---|---|
| `id` | Booking UUID (`dispatch_job_orders.booking_uuid`) |
| `jobOrderNumber`, `bookingNumber` | `job_order_no`, booking `bookingNo` |
| `status` | See AC-2 |
| `clientName`, `contactNumber` | Booking `client`, `contact` |
| `date`, `pickupTime`, `dispatchTime` | Booking `date`, `preferredTime` (as HH:mm when it parses), assignment `dispatch_time` |
| `driverId`, `driverName`, `helperIds`, `helperNames` | Assignment `driver_id`, `helper_ids` (team member record ids) and names from the team roster |
| `garage`, `vehicle` | Assignment `garage`, vehicle plate and alias |
| `pickupAddress`, `deliveryAddress`, `pickupArea`, `deliveryArea` | Booking addresses; area is the landmark when present, else empty |
| `estimatedItems`, `itemDescription`, `customerInstruction` | Booking `estimatedItems`, `itemDetails`, `specialInstructions` |
| `insured`, `paymentMethod`, `downPayment` | Booking `hasInsurance`, `requestedPaymentMethod`, `downpayment` |
| `charges` | One line per priced add-on in `additionalServicesAvailed`, and the service for the rest of the booking amount, so the lines add up to the amount. If the add-ons alone exceed it, one line with the amount |
| `postServiceFormSubmitted` | Always `false` from dispatch; the app fills it from `GET /bms/post-service/mine` and its own records |

- Cancelled bookings and superseded job orders are left out, so the phone deletes them on the next sync.
- Names of the driver, helpers and vehicle come from Auth and VMMS. If either is down, the cards still load with "Assigned driver", "Assigned helper" and the job order's truck, instead of failing the sync.
- Sorted by service date, newest first.

### `GET /bms/post-service/mine` (completion)

- Role: `DRIVER`. Declared before `GET /post-service/:id`.
- Answer: `{ items: [{ bookingUuid, submitted, finalized, version }] }` for every booking the caller is the assigned driver of. `submitted` is true once a form was sent (not a draft), `finalized` when `postServiceStatus = 'Finalized'`, and `version` is null until a record exists.
- Lives in completion rather than in the job order route, because dispatch has no address for completion (`COMPLETION_API_URL`) while completion already calls dispatch.

### `PUT /bms/post-service/mine/:bookingUuid` (completion)

- `mine/:bookingUuid` has two path segments, so it doesn't clash with the web's `PUT /post-service/:id`.
- The driver check asks dispatch: `GET /internal/dispatch/team-bookings?userId=…` answers `{ driver: [bookingUuid…], helper: [bookingUuid…] }` from the confirmed assignments. The booking must be in `driver`.

| App field | Saved as |
|---|---|
| `serviceCompleted` | `status: 'Completed'` when true (AC-4) |
| `arrivalTime` (HH:mm) | `arrivalTime` |
| `addOns` (names) | `additionalMaterials` |
| `completionNotes`, `issueReported`, `issueDetails` | Same names |
| `paymentMethod` | `reportedPaymentMethod` (mapping below) |
| `addOnPayment` | `reportedAddOnPayment` (mapping below) |
| `submittedAt` | `submittedAt` |
| `baseVersion` | Not saved; used for AC-7 |

Answer: the record as the web's `GET /post-service/:id` returns it, plus `postServiceLocked` and `version`.

#### Edits from the office

The phone always sends the whole form. The save is refused (AC-7) when **all** of these hold:

1. a work outcome already exists,
2. its `updatedAt` is not the `baseVersion` sent,
3. `lastEditedBy` is not this driver.

Rule 3 lets a retry through when the driver's save succeeded but the reply was lost on a weak signal. The web's save is not checked, and it sets `lastEditedBy`.

The check is repeated at the moment of writing: the update only applies while `updatedAt` is still the value just read. If someone saved in between, the answer is also `POST_SERVICE_CHANGED`.

Admin's **Retry** of a stuck completion (`POST /post-service/:id/retry`) changes neither `finalizedBy` nor `lastEditedBy`. Before this change it made the Admin the finalizer, which would also have hidden a driver's submission from Customer Support's Daily Sales drafts.

Example: the driver submits at 9:00. Customer Support corrects the arrival time on the web at 10:00 without finalizing. At 11:00 the driver resubmits a notes fix from the 9:00 copy. The answer is `POST_SERVICE_CHANGED` with the 10:00 record, so the phone shows the correction. The driver re-enters the notes fix and submits again with the 10:00 version.

#### Payment methods

| App | Web |
|---|---|
| `CASH` (Payment method), `COD` (Add-ons payment) | `Cash` |
| `BANK_TRANSFER` | `BDO` |
| `GCASH` | `GCash` |
| `XENDIT` | `Xendit` |
| `UNPAID` (Add-ons payment) | `Unpaid` |

The app's "Bank transfer" option is relabelled **BDO** so drivers and Customer Support see the same name. The stored value stays `BANK_TRANSFER`.

### Mobile app

- The `TEAM_JOB_ORDER_ROUTES_READY` switch is removed; the sync always calls the three routes above (`PUT`, as today). Helpers skip the upload and the post-service status call.
- NetInfo listener: offline to online starts a sync. A 45-second timer runs only in the foreground with a user signed in. Neither runs in seeder mode.
- Every update to a record after an upload is matched on its `submittedAt`, so a form submitted again while the upload was running stays queued.
- On `POST_SERVICE_CHANGED`, `current` is mapped back to the app's fields (`additionalMaterials` to add-on keys, `reported…` methods to app values, a "2:30 PM" arrival time to "14:30"), and `baseVersion` becomes `current.version`.
- A job order with a record on the phone shows as submitted (and Done when the service was completed), whatever the snapshot says, as before.
- **Which job orders are shown.** A real sign-in shows the downloaded list as it is: the server only sends the caller's own job orders, and the cache is cleared when a different user signs in. Seeder mode still filters by account. Before, the filter compared the job order's ids with `TeamMember.teamMemberId`, which a real sign-in never fills, so every real job order would have been hidden.
- `types/bms.ts`: `driverId` and `helperIds` are team member record ids (not login ids).
- **Post Service list.** A submitted job shows "Record submitted · Job done" with **Edit Record**, so the driver can correct it until the office finalizes. A finalized one shows "Finalized by office" with **View Record**. An unsent record adds "Waiting to be sent" or "Not sent" under it. Before, a submitted job could not be opened again.
- **Payment choices.** "Bank Transfer" reads **BDO** ("Paid via BDO" for add-ons). The booked method pre-selects the matching choice from text such as "GCash", "Bank Transfer", "BDO" or "COD", the same way the web suggests one.

## API and data impact

| Service | Change |
|---|---|
| dispatch | `GET /job-order/mine` (DRIVER, HELPER); internal `GET /internal/dispatch/team-bookings?userId=…` |
| completion | `GET /post-service/mine` and `PUT /post-service/mine/:bookingUuid` (DRIVER); Daily Sales suggestion order; Retry keeps the finalizer |
| gateway | No change: `/bms/job-order/...` already goes to dispatch and `/bms/post-service/...` to completion. The gateway only checks the sign-in; roles are checked by each service |

**Completion database** (one migration, all columns nullable on `work_outcomes`):

| Column | Type | Meaning |
|---|---|---|
| `submitted_by` | uuid | Driver who sent the form from the app |
| `submitted_at` | timestamptz | When the driver tapped Submit (phone time) |
| `reported_payment_method` | varchar(20) | `Cash`, `BDO`, `GCash` or `Xendit` |
| `reported_add_on_payment` | varchar(20) | Same, or `Unpaid`; null when no add-ons |
| `last_edited_by` | uuid | Who saved last, driver or web; empty on older records, which counts as "not this driver" |

**Phone database**: `DATABASE_VERSION` 4 to 5. `post_service_records` gets `lastError` (text), `syncBlocked` (0/1) and `baseVersion` (text). `job_orders` gets `postServiceLocked` (0/1).

## Security and failure behavior

- Both team member routes take the caller only from the verified token (`bmsIdentity.sub`); no id in the body or query selects the person.
- Internal routes use the existing `BMS_INTERNAL_SERVICE_KEY`, compared in constant time like the other internal routes.
- A failed or partial download never replaces the phone's cache.
- A refused save (403, 409, 400) writes nothing on the server.
- A record waiting on a phone when a different user signs in on it is discarded, as today (spec 0010).

## Affected repositories

| Repo | File | Change |
|---|---|---|
| backend | `bms-dispatch-service/src/dispatch/job-order.controller.ts` | `GET mine` |
| backend | `bms-dispatch-service/src/dispatch/team-job-orders.ts` | New: finds the team member, builds the job order cards, lists team bookings |
| backend | `bms-dispatch-service/src/dispatch/team-job-orders.spec.ts` | New: card fields, times, charges, statuses, who sees what |
| backend | `bms-dispatch-service/src/dispatch/internal-dispatch.controller.ts` | `GET team-bookings` |
| backend | `bms-dispatch-service/src/booking-client.service.ts` | `BookingRecord` lists the fields the cards use |
| backend | `bms-dispatch-service/src/app.module.ts` | Registers `TeamJobOrdersService` |
| backend | `bms-completion-service/src/work/work.controller.ts` | `GET mine`, `PUT mine/:bookingUuid` |
| backend | `bms-completion-service/src/work/work.service.ts` | Driver submission: driver check, mapping, `submittedBy`, finalized lock, version check, guarded write. Web save sets `lastEditedBy`; Retry keeps the finalizer |
| backend | `bms-completion-service/src/work/team-submission.spec.ts` | New: driver submission, roles, validation, version check, finalized lock, web save |
| backend | `bms-completion-service/src/completion-auth.guard.ts` | `DRIVER` role |
| backend | `bms-completion-service/src/dispatch-client.service.ts` | `driverBookingUuids` |
| backend | `bms-completion-service/src/collections/collections.service.ts` | Drafts suggest `reportedPaymentMethod` first |
| backend | `bms-completion-service/prisma/schema.prisma`, `prisma/migrations/20261128090000_team_post_service` | Five `work_outcomes` columns |
| mobile | `services/SyncService.ts` | Routes on, post-service status for drivers, failure table, `baseVersion`, office version mapping |
| mobile | `App.tsx` | NetInfo listener and 45-second timer |
| mobile | `repositories/PostServiceRepository.ts` | `syncBlocked`, `lastError`, `baseVersion`; updates matched on `submittedAt` |
| mobile | `repositories/JobOrderRepository.ts` | `postServiceLocked` |
| mobile | `database/tables.ts`, `database/database.ts` | Database version 5 (migration 5) |
| mobile | `screens/PostServiceFormScreen.tsx` | Status notice, read-only when finalized |
| mobile | `screens/PostServiceScreen.tsx` | Edit Record / View Record on submitted and finalized jobs, unsent state |
| mobile | `stores/jobOrdersStore.ts`, `stores/userStore.ts` | Sync knows whether the signed-in person is a driver; real sign-in shows the downloaded list as is |
| mobile | `seeders/payments.ts`, `seeders/jobOrders.ts`, `types/bms.ts` | "BDO" labels and web name mapping; `postServiceLocked`; id comments |
| mobile | `package.json`, `package-lock.json`, `OFFLINE_DATABASE.md` | `@react-native-community/netinfo` 12.0.1; describe the sync |

## Deploy notes

- Merge and deploy the backend first. Until it is live, the app gets 404 on the new routes, keeps forms queued and shows the error.
- Run the completion migration (`prisma migrate deploy`) before starting the new completion service.
- No new environment variables: completion already has `DISPATCH_API_URL`.
- After NetInfo is installed, the app needs a new development build (`npx expo run:android` or EAS), not only a Metro reload.
- Phones upgrade their local database to version 5 on the next start. Nothing is lost.
