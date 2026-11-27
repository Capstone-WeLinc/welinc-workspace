# 0021. Notifications from the backend, Booking view-only actions, History details fix, Approvals panel note: rationale

Decision record for [index.md](index.md). The index is the build contract.

## Context

The BMS bell had no backend of its own. The web app polled the ordinary list endpoints every 15 seconds, compared each answer with a snapshot in `localStorage`, and turned the differences into notifications. That meant:

- read and unread lived in one browser, and a new browser started empty;
- nothing was recorded while the app was closed;
- two changes between polls looked like one;
- every open tab downloaded three or four full lists every 15 seconds;
- who gets notified about what was decided in the web app;
- drivers and helpers had nothing real.

Customer emails were sent once, inside the request, and a failed send was only logged.

BMS runs as separate services with their own databases (booking, dispatch, completion). Events that deserve a notification happen in all three.

Two smaller requests came with this one: the Admin Booking page should only view bookings, and Approvals → History failed to open some rows.

## Options considered

### Where notifications live

#### Option 1: Keep the browser-side bell, improve the diffing

**Pros**:
- No backend or database change.

**Cons**:
- Read state still stays in one browser, and nothing is recorded while the app is closed.
- The load on the list endpoints stays.
- Drivers and helpers still get nothing.

#### Option 2: A notifications table in each service, combined by the gateway

**Pros**:
- Each service writes its own rows in its own transaction.

**Cons**:
- Read state is spread over three databases.
- The gateway has to merge and sort three lists on every poll, and mark-all-read touches three services.

#### Option 3: Booking owns all notifications; Dispatch and Completion deliver through an outbox (chosen)

Booking writes its notifications directly in the same transaction as the change. Dispatch and Completion write theirs to a local `notification_outbox` in the same transaction, and a timer posts them to Booking's internal route with retries.

**Pros**:
- One list and one read state per person, served by one cheap endpoint.
- No lost notifications: the outbox row exists exactly when the change does, and survives Booking being down.
- The same pattern as the existing `approval_outbox`, so the team already knows it.

**Cons**:
- A Dispatch or Completion notification appears up to a few seconds late.
- The outbox file is copied in two services (as `auth/verify` already is) and must be changed in both.

### How the browser learns about new notifications

#### Option A: Poll one small endpoint every 15 seconds (chosen)

**Pros**:
- Simple. Works through the existing gateway, auth and CORS with no new infrastructure.
- Far lighter than before: one indexed query instead of three or four full lists.

**Cons**:
- Up to 15 seconds late.

#### Option B: Server-sent events or WebSockets

**Pros**:
- Instant.

**Cons**:
- Long-lived connections through nginx and Azure Container Apps need extra configuration and session handling. Too much for this change; it can be added later on top of the same table.

### Customer emails

#### Option 1: Retry inline a few times

**Pros**:
- No table.

**Cons**:
- Slows the request.
- Still loses the email if SMTP is down for longer than the retries.

#### Option 2: Queue table plus a sending timer, with a lease (chosen)

**Pros**:
- The request no longer waits on SMTP.
- Retries for hours with a growing wait.
- The lease stops two replicas sending the same email.
- A failure is recorded with its error, instead of only being logged.

**Cons**:
- One more table, and a small delay (the timer tries straight away and then every 30 s).

### Mobile

The user chose to build the backend and the web bell now and leave the mobile app for later. The backend already writes notifications for drivers and helpers, and the notifications routes accept the Driver and Helper roles. The mobile app's job-order sync calls `/bms/job-orders/mine`, which doesn't exist, so the app runs on sample data. Phone push needs an Expo/EAS project and Firebase credentials, and can only be tested on a development build on a real phone.

### Admin Booking actions

Only View remains, so the row shows the single eye button with no ⋮ menu, as spec bms/0016 decided for one-action rows. The Edit, Reschedule and Cancel dialogs and their code were removed rather than hidden, so nothing unreachable is left on the page.

### History details

The backend refused any Admin view of a booking request whose booking is Cancelled. The rule matches the Needs action list, which hides pending requests on cancelled bookings, but approving a cancellation cancels the booking, so every approved cancellation became unopenable. The rule now applies only to pending requests.

### Approvals panel note

The user asked to remove the note above the decision buttons. It's removed for all three request types that had one, not only collections, so the panel looks the same whatever is selected. What each decision does is unchanged.

## Rationale

Option 3 with polling gives one reliable source of truth with per-person read state, at the cost of a few seconds' delay that a bell doesn't need to beat. It reuses patterns the codebase already has (the approval outbox, the service key, the gateway routing), adds no new infrastructure or settings, and leaves a clean path to mobile and push later.
