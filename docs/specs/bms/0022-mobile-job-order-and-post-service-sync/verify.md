# Verify: mobile job order and post-service sync · spec 0022

Steps derived from [spec 0022 acceptance criteria](index.md). The backend has unit tests and local build checks; the mobile app has a type-check and a bundle build (the repo has no tests yet). Nothing has been run against a database, the gateway or a phone yet.

## Build

- [x] `npm run typecheck`, `npm run lint:ci`, `npm run build` and `npm test` pass in `welinc-backend-bms` locally (2026-11-28).
- [ ] Backend CI is green on the pull request.
- [x] `npx tsc --noEmit` passes in `welinc-mobile-bms` (2026-11-28).
- [x] `npx expo export --platform android` bundles the app, NetInfo included (2026-11-28).
- [ ] A new development build installs and starts on a phone (NetInfo is a native module).
- [x] `prisma validate` accepts the completion schema with the five new columns.
- [ ] The completion migration applies on a fresh database and on one with existing work outcomes.

## Unit tests (in-memory, no database)

- [x] Dispatch, `team-job-orders.spec.ts`: a driver gets only their active, confirmed, not cancelled job orders; a helper gets theirs, newest first; unknown logins get an empty list; cards still load when other system is down; times read as HH:mm; charge lines add up to the amount; statuses map as in AC-2; team bookings split by role.
- [x] Completion, `team-submission.spec.ts`: assigned driver saves and completes the booking with `submittedBy`, no `finalizedBy`, payment mapped (Bank transfer to BDO, COD to Cash); draft when not completed; other drivers and other bookings get 403; invalid details get 400; resubmission with the given version is saved; own retry with an old version is saved; resubmission older than a web edit gets `POST_SERVICE_CHANGED` with `current` and the web edit stays; finalized gets `POST_SERVICE_FINALIZED`; a save landing between check and write gets `POST_SERVICE_CHANGED`; status list per driver; web save still rejects payment and still sets the finalizer and `lastEditedBy`; Daily Sales accepts only its own method names.

## Job orders (AC-1, AC-2)

- [ ] A seeded driver's `bms-mobile` token through the gateway gets their assigned job orders as `{ jobOrders }`.
- [ ] A seeded helper gets the job orders they are a helper on.
- [ ] A team member with no assignments, or no active record, gets `{ jobOrders: [] }`.
- [ ] Another team member's job orders are never returned.
- [ ] Not distributed is `PENDING`, distributed is `ONGOING`, completed booking is `COMPLETED`.
- [ ] A cancelled booking or superseded job order is not returned.
- [ ] `GET /bms/job-order/:id` still works for Admin and Operations and still refuses drivers.

## Driver submission (AC-3, AC-4, AC-5)

- [ ] The assigned driver's submission is saved, the booking becomes Completed and it appears on the web Post-Service page.
- [ ] `serviceCompleted: false` without an issue saves a draft and doesn't complete the booking.
- [ ] A helper on the job order gets 403; a driver not on it gets 403.
- [ ] A job order not yet distributed gets 409 and nothing is saved.
- [ ] `submittedBy` is the driver; `finalizedBy` and `finalizedAt` stay empty.
- [ ] Sending the same form twice gives the same result.

## Payment report and Daily Sales (AC-5, AC-6)

- [ ] A driver-submitted booking shows in Daily Sales drafts for every Customer Support user.
- [ ] Its suggested method is the one the driver reported; Bank transfer shows as BDO.
- [ ] A booking without a driver report still gets the method from the booking request.
- [ ] No collection is created by a driver submission.
- [ ] The web's `PUT /bms/post-service/:id` still rejects payment fields.
- [ ] Admin Retry on a stuck driver submission leaves `finalizedBy` empty, and the booking stays in every Customer Support user's drafts.

## Office edits and finalize (AC-7, AC-8)

- [ ] `GET /bms/post-service/mine` with a driver's token lists their bookings with `submitted`, `finalized` and `version`; a helper's token gets 403.

- [ ] Every answer has `version`; a resubmission with that `version` as `baseVersion` is saved.
- [ ] Customer Support saves on the web (not finalized), then the driver resubmits with the older `baseVersion`: 409 `POST_SERVICE_CHANGED` with `current`, and the web changes are still there.
- [ ] The driver resubmits with an older `baseVersion` when the last save was their own: saved.
- [ ] Web saves set `lastEditedBy` to the Customer Support user.
- [ ] After Finalize Booking on the web, a driver submission gets 409 `POST_SERVICE_FINALIZED`.

## Phone sync (AC-9, AC-10)

- [ ] A real driver sign-in shows their job orders after the first sync.
- [ ] A job order assigned on the web appears within about 45 seconds while the app is open.
- [ ] A job order cancelled on the web disappears at the next sync.
- [ ] Offline: the last downloaded job orders stay.
- [ ] Online: a submitted form reaches the web within a few seconds.
- [ ] Airplane mode: submit; the form shows as waiting and the card stays Completed.
- [ ] Turning airplane mode off with the app open sends the form without any tap.
- [ ] Closing the app while offline, then opening it online, sends the form.

## Phone failure handling (AC-8, AC-11)

- [ ] A submitted job shows "Record submitted · Job done" with Edit Record; editing and submitting again reaches the web.
- [ ] A submitted form waiting offline shows "Waiting to be sent" on its card.
- [ ] A rejected form (400) shows the message and isn't retried until submitted again.
- [ ] After the office finalizes, the card shows "Finalized by office" with View Record, and the form opens read-only with no Submit button.
- [ ] After a web edit, a driver resubmit shows "The office updated this record…" with the web's values; submitting again is accepted.
- [ ] Same as above, with the resubmit queued offline and sent when the internet returns.

## Roles and seeder mode (AC-12)

- [ ] Helpers never see the post-service form.
- [ ] Payment method choices read Cash, GCash, BDO, Xendit.
- [ ] Seeder mode still shows the seeder job orders without the backend.
- [ ] An app with the version 4 database opens without errors (upgrade to version 5).
