# 0004. Deliveries: the outbox, the worker and the retry rule

Child of [0029](index.md). Acceptance criteria AC-21 to AC-25 live in the umbrella.

## Summary

Every message VRMS sends to VMMS or BMS is first written as a row in a `Delivery` table, in the same database save as the change it reports (a transactional outbox). So the change and the message either both happen or neither does. A background job sends due rows, retries failures with growing waits for 24 hours, and then marks them failed. People see every delivery on a Deliveries tab of the Audit Logs page and can retry or dismiss a failed one. Messages coming in are made safe to resend by their own ids.

## Writing a delivery

`enqueueDelivery(tx, { target, kind, payload, repairTicketId?, referralId?, expediteRequestId? })` is the only insert. It sets `id` (uuid, also the payload's `eventId`), `status: PENDING`, `attempts: 0`, `nextAttemptAt: now`, `manualRetryCount: 0`. It is always called with the transaction of the change. Kinds in slice 1: `REPAIR_EVENT`, `REFERRAL_REJECTED` (VMMS), `REPAIR_UPDATE`, `EXPEDITE_ANSWER` (BMS).

Each kind knows its path, audience and scope:

| Kind | Path | Audience, scope |
|---|---|---|
| `REPAIR_EVENT` | `/vmms/integrations/vrms/repair-events` | `VMMS`, `fleet.repair-status.write` |
| `REFERRAL_REJECTED` | `/vmms/integrations/vrms/referral-events` | `VMMS`, `repair.referral-status.write` |
| `REPAIR_UPDATE` | `/bms/integrations/vrms/repair-updates` | `BMS`, `repair.update.write` |
| `EXPEDITE_ANSWER` | `/bms/integrations/vrms/expedite-answers` | `BMS`, `repair.update.write` |

## The worker (`DeliveryWorker`, `@Interval(15_000)`)

1. Claim up to 50 rows in one transaction:
   - **Heads:** for rows with a ticket, take only the head of each (`target`, `repairTicketId`) line, `SELECT DISTINCT ON (target, repair_ticket_id) … WHERE status IN ('PENDING','FAILED') ORDER BY target, repair_ticket_id, seq`. Keep the heads that are `PENDING` and due (`nextAttemptAt <= now()`). A `FAILED` head blocks its line until it is retried or dismissed.
   - **Unordered rows:** rows with no ticket (`REFERRAL_REJECTED`) are claimed directly when due.
   - **Lock and lease:** lock the chosen rows with `FOR UPDATE SKIP LOCKED` and set `nextAttemptAt = now + 60 s` as a lease, so a crashed worker's rows come back. A lease that runs out counts as one attempt (`attempts + 1`, `lastError: 'lease_expired'`) when the row is claimed again.
2. For a `REPAIR_EVENT` or `REPAIR_UPDATE`, fill in `eventVersion` from the ticket's `vmmsEventVersion` or `bmsEventVersion` + 1. Then post each claimed row (`SUITE_GATEWAY_INTERNAL_URL` + path, bearer service token, JSON payload, 5 s timeout). Rows for different lines go in parallel, up to 5 at a time. A row sent twice after a lease ran out is safe only because its `eventId` stays the same: VMMS and BMS treat a repeated `eventId` as a duplicate.
3. On success (any 2xx): `SENT`, set `sentAt`, `lastStatusCode`. For a versioned kind, save that version on the ticket in the same statement.
4. On a retryable answer (401, 403, 408, 429, 5xx, network error, timeout): `attempts + 1`, set `firstAttemptAt` if null, and set `lastAttemptAt`, `lastStatusCode`, and `lastError` (the answer body's `code` or `error`, or the network error name; up to 500 characters). If `now - firstAttemptAt >= integration.retryWindowHours`, set `FAILED`. Otherwise set `nextAttemptAt = now + min(30 s × 2^(attempts − 1), 1 h)`.
5. Any other 4xx: `FAILED` at once with the code and error.
6. A failure of the job itself calls `reportJobFailure('delivery-worker', error)` and never rethrows.

Before a send, the token client fetches or reuses the service token. A token error counts as a retryable failure.

## People actions

| Route | Method | Inputs | Auth | Errors |
|---|---|---|---|---|
| `/vrms/deliveries?status&target&kind&cursor&limit` | GET | filters; limit 1 to 100 (default 25) | `audit.view` | 403 |
| `/vrms/deliveries/:id` | GET | | `audit.view` | 404 |
| `/vrms/deliveries/:id/retry` | POST | | `integration.respond` | 409 `NOT_FAILED` |
| `/vrms/deliveries/:id/dismiss` | POST | `reason` 5 to 500 | `integration.respond` | 409 `NOT_FAILED` |

Retry: `PENDING`, `attempts 0`, `firstAttemptAt null`, `nextAttemptAt now`, `manualRetryCount + 1`. Dismiss: `DISMISSED` with `dismissReason`, which also unblocks later rows for that ticket. No version number is used up, since numbers are assigned at send. Dismissing a `REPAIR_UPDATE` also queues a fresh update with the ticket's current state (child 0003). Both write an audit row (actions `DELIVERY_RETRIED`, `DELIVERY_DISMISSED`, actor the person, ticket set when the row has one).

**Web**: on the Audit Logs page, the tabs are Activity (today's log) and Deliveries. Deliveries is a table (created, target, kind, ticket number, status, attempts, last error) with filters for status, target and kind, and failed rows first. A `PENDING` row with 3 or more attempts shows a warning with its last status code, so a missing grant (a retried 401 or 403) is seen within minutes, not after 24 hours. A side panel holds the payload (pretty JSON), the attempt facts, and the Retry and Dismiss buttons. The tab label shows the failed count when it is above 0.

**Retention** (`DeliveryRetentionJob`, `@Cron('0 30 3 * * *', { timeZone: 'Asia/Manila' })`): delete `SENT` and `DISMISSED` rows with `createdAt` older than `integration.deliveryRetentionDays`.

## Incoming messages

No shared receipt table. Each inbound write route uses the other system's id as its primary key (`Referral.id`, `ExpediteRequest.id`) and stores a `payloadHash`. The same body is a duplicate that answers the first answer again, and a different body is a 409. The fleet change receiver needs neither, because applying a fresh read twice changes nothing.

System actors in the audit log: `actorUserId` null, `actorRole 'SYSTEM'`, `actorName` `VMMS`, `BMS` or `VRMS` (for VRMS's own automatic declines). New audit actions: `REFERRAL_OPENED_TICKET`, `REFERRAL_ADDED`, `REFERRAL_REJECTED`, `EXPEDITE_REQUESTED`, `EXPEDITE_ACCEPTED`, `EXPEDITE_DECLINED`, `DELIVERY_RETRIED`, `DELIVERY_DISMISSED`, in `AUDIT_ACTIONS`.

## Invariants

- No message leaves VRMS except through a `Delivery` row written in the change's transaction.
- For one ticket and one target, rows are sent in `seq` order, and a later row never overtakes an earlier unsent or failed one.
- `eventVersion` is assigned only at send, so sent versions per ticket and target are always 1, 2, 3 with no gaps.
- `PENDING` and `FAILED` rows are never deleted by the retention job.

## Critical test scenarios

- Retry: VMMS answers 503 three times, then 201. The row ends `SENT` after waits of 30, 60 and 120 seconds. Verifies **AC-21**.
- Window: VMMS is down for 25 hours, the row is `FAILED`, and the Admin retries it and it sends. Verifies **AC-21**, **AC-22**.
- Ordering: the third event for a ticket fails with a 409, the fourth waits, the Admin dismisses the third, and the fourth is sent as version 3, which VMMS accepts. Verifies **AC-21**, **AC-22**.
- Atomic: a ticket save that rolls back leaves no delivery. Verifies **AC-21**.

**Inline rationale**: the outbox is the standard answer to "change my database and tell another system" without a distributed transaction. The retry rule matches VMMS's built sender (30 s doubling, 1 hour cap, 24 hour window), so both groups explain one rule at the defense. A message broker (Azure Service Bus) would do the retrying for us, but it adds a paid resource, a new local emulator, and a new failure mode for three small systems that already share a gateway.
