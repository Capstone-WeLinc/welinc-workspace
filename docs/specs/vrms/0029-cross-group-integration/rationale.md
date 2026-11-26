# 0029. Cross group integration: rationale

The decision record for [index.md](index.md). `/develop` skips this file.

## Context

The three WeLinc systems went separate ways after Capstone 1. Each now has its own containers, database and deployment behind one gateway and one login, and staging runs all three. What they don't do yet is work together. A truck found faulty in a VMMS inspection never reaches a VRMS repair ticket. VMMS sets truck status without knowing a repair started. BMS dispatches against a status that says nothing about when a truck in repair comes back. The integration defense is judged on exactly these handoffs, and the panel will call plain reads "simple".

Ownership was settled in the 2026-11-20 and 2026-11-21 talks:

- VMMS owns trucks, garages and outside shops.
- VRMS owns repairs.
- BMS owns bookings and dispatch.
- Each system keeps its own notifications.
- Seven flows were listed, with VRMS in flows 1 to 3 as the defense's main thread.

VMMS has since merged its half of flows 1 and 2 (specs vmms/0023 to vmms/0026): a strict receiver for repair events, a referral sender with a 24 hour retry, and screens that read VRMS. All of it fails today, because VRMS has none of the routes and welinc-auth grants none of the scopes. BMS has built nothing for its Flow C, but it has empty columns waiting for an expected return date.

VRMS today has no route that accepts a service token, no outbound message of any kind, no queue or outbox, and its own `Vehicle` and `Garage` tables, which nobody keeps in step with VMMS. Its `Vehicle.status` is written by VRMS itself, which clashes with VMMS being the one writer of truck status. Its tickets require a driver, which a referral doesn't have.

The forces:

- **Time.** The final defense is by Dec 20 and the Azure credit ends Dec 18.
- **People.** There are three student groups, each owning its own repos.
- **Infrastructure.** Nothing new should be added that the groups must learn or pay for.
- **Failure.** Any one system will be down at some point, and a lost handoff is worse than a late one.

## Options considered

### Option 1: Direct synchronous calls only

When something changes, the changing system calls the other system's API in the same request and fails or logs if it can't.

**Pros**:
- The least code: no table, no job.
- Easy to explain.

**Cons**:
- An outage in VMMS or BMS either blocks a VRMS save or silently loses the message.
- VMMS's own sender already shows the cost: their Chief Mechanic waits up to 5 s on VRMS.
- No record of what was sent, so nothing to retry and nothing to show at the defense.

### Option 2: Transactional outbox with service token HTTP calls, plus live reads (chosen)

Each change writes a message row in the same transaction, and a worker sends it with retries over the existing gateway and service tokens. Facts needed only at display time are read live.

**Pros**:
- A change and its message are atomic, and an outage only delays the message.
- It matches the retry rule VMMS already built, so both groups explain one rule.
- It uses only what the suite already runs (PostgreSQL, the gateway, welinc-auth service tokens, `@nestjs/schedule`).
- Every message is visible and retryable by a person.

**Cons**:
- Each system builds its own outbox and worker (VRMS, VMMS and BMS each own one).
- Messages arrive seconds late, not instantly.
- A failed message needs someone to look at the Deliveries tab.

### Option 3: A shared message broker (Azure Service Bus)

Systems publish events to topics and subscribe to the ones they need, and the broker stores and retries.

**Pros**:
- Retrying, ordering and dead letters come built in.
- Systems don't need each other's addresses.
- The industry answer at larger scale.

**Cons**:
- A new paid Azure resource and a new local emulator for three groups to learn weeks before the defense.
- Each group still needs an outbox to publish atomically.
- Debugging moves out of each team's own database.
- VMMS's merged HTTP receiver would have to be rebuilt.

### Option 4: Shared database views

Each system exposes read only views of its tables to the others.

**Pros**:
- No API code for reads.

**Cons**:
- It breaks the suite rule that no system reads another system's database.
- It couples schemas across groups.
- It can't carry commands or events at all.

## Rationale

Option 2 fits the forces. Loss is the failure that matters here: a referral that vanishes during a VRMS restart, or a "repair finished" that never reaches VMMS, leaves a truck wrongly parked or wrongly dispatched. An outbox written in the same transaction makes that impossible without new infrastructure, and VMMS already built the other end of it with the same retry shape. Option 3 is what this would grow into at real scale, but it costs a paid resource and a rebuild of VMMS's merged work for no gain at three systems and a few hundred messages a day. Option 1 is cheaper only until the first outage at the defense.

Within Option 2, the smaller calls follow the same reasoning:

- **Build to VMMS's shapes and send eight behavioural asks, not a redesign.** VMMS's payloads are sound. What needs changing is how their sender and receiver behave under failure: strict +1 versions block a ticket, a send inside the Chief's request couples them to VRMS, and a 401 is never retried. Those are one or two line changes for them.
- **Fleet copy by change messages plus an hourly full read.** The copy has to be fast enough that a ticket shows the right truck, and self healing when a message is lost. VMMS's existing `fleet-changes` sender gives the speed for one added recipient, the full read gives the healing, and reading the record fresh (instead of trusting the message) makes reordering harmless.
- **Refuse unknown trucks now, register request later.** A WeLinc truck missing from the fleet registry is a data entry gap. Letting VRMS create trucks would put half filled trucks into BMS's dispatch list. A request that VMMS Operations complete keeps one owner, and it waits for slice 2 because VMMS must build its receiver.
- **The BMS schedule is read live, not copied.** Dispatch changes all day, and a stale trip list misleads more than "BMS can't be reached".
- **Repair updates to BMS carry category names only.** BMS staff and their clients see that text, so mechanic notes and costs must never cross.
- **Archive unmatched VRMS trucks, don't delete them.** The engineer first chose deletion, since all current VRMS data is demo data and the realistic reseed (feature 47) follows. The cross check found that deleting tickets means deleting audit rows, which VRMS's append only rule (spec 0021) refuses by design. Opening a hole in that rule for a cleanup is worse than a few hidden rows, so archiving was chosen on review: the trucks lose their place in pickers, and the reseed gives the clean data.
- **Pick the outside shop from VMMS's list now.** VMMS refuses an outsourced repair event without a shop it knows, and VRMS had no shop field. Sending a softer status would hide outsourcing from VMMS. Reading VMMS's provider list keeps one owner for shops (the 2026-11-20 call) and gives features 36 to 39 their foundation early, at the cost of one more ask for VMMS.
- **One permission, `integration.respond`.** Accepting a referral, answering an expedite and resending a failed message are all "answering another system". One grant in Settings is easier to reason about than three, and it can still go to a Chief Mechanic without code.

## Evidence: what each side had on 2026-11-26

Read only scans of `development` in every repo on 2026-11-26:

- **VMMS built:**
  - The `POST /vmms/integrations/vrms/repair-events` receiver. It requires `repairTicketNumber` and `repairStatus`, `OPENED` must carry `OPEN` and `COMPLETED` must carry `CLOSED`, versions go up by exactly 1, the id sets are cumulative, and a shop name must match an active provider.
  - The `POST /vmms/integrations/vrms/referral-events` receiver, `REJECTED` only.
  - The referral sender: `202` expected, 30 s doubling to 1 h, 24 h window, 401 not retried, sent inside the Chief's request.
  - The status and history read clients and their screens.
  - The BMS availability and fleet change senders, which have no grants and no BMS receivers.
  - Their old repair tables are dropped (spec vmms/0022).
- **BMS built:**
  - Nothing for VRMS.
  - A truck's trips live on `DispatchAssignment.vehicleId`, with JO numbers on `DispatchJobOrder`.
  - `VehicleDispatchProfile.expectedBackAt`, `statusReason` and `statusRemarks` exist but nothing writes them.
  - The only trips read by truck accepts people, not services.
  - Their gateway has no `/bms/integrations/vmms` or `/vrms` routes.
- **welinc-auth:** `vrms` holds only `directory.read` and `permissions.read`, `vmms` holds only directory scopes, and `bms` holds directory scopes plus VMMS `fleet.read`.
- **VRMS:**
  - No integration code.
  - `@ServiceRoute` exists but is unused.
  - `Vehicle` is keyed by plate only, with no VMMS id.
  - `RepairTicket.driverId` is required.
  - `dueAt` exists, but nothing writes it.
