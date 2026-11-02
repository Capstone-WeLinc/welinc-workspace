# 0018. Rationale: before and after photos

## Context

WL-211 says no ticket is marked done without evidence. Spec 0017 built the private upload service with four file kinds, including `PROOF`, but no screen uploads proof, proof has no cap, and nothing in the status flow (spec 0014) asks for it. A mechanic can send a ticket for verification with no evidence, and the Chief verifies from words alone.

Forces:
- **Mechanics work on phones, often with dirty hands.** Every extra choice at upload time is friction, and friction means skipped photos or wrong labels.
- **Two different photos matter.** The truck's condition on arrival protects the garage in disputes. Photos after the fix are what the Chief verifies. Mixing them weakens both.
- **Garages differ.** The team wants the rules configurable, like spec 0015's "Require costs before closing", without new UI for each switch (spec 0012's catalog drives the hub).
- **Evidence can be faked cheaply,** by uploading an old gallery photo as proof. Spec 0017 strips photo metadata for privacy, and the browser shrink drops it before upload.
- **No stakeholder input:** the team decides, aiming for capstone worthy depth without bloat.

## Options considered

### Option 1: Separate sections, one per kind

A Vehicle photos section and a Proof section on the ticket, each with its own add button, and an optional issue picker per upload.

**Pros**: explicit; matches the four kinds one to one.
**Cons**: three upload decisions on a phone; easy to put a photo in the wrong section; a crowded screen.

### Option 2: One strip, labelled by status (chosen)

One add control. Before work starts photos are Before, after they are After. A viewer action fixes a mislabel.

**Pros**: zero choices at upload; the label can't be spoofed; the before and after story reads naturally.
**Cons**: the label follows timing, not intent, so a late Before photo needs a manual move.

### Option 3: One strip with a Before or After switch

The same single control, plus a switch on each upload, preset by status.

**Pros**: the person states intent.
**Cons**: one more tap that most people leave on the preset; the client chooses the label, so it can be wrong on purpose.

### Option 4: Proof only

Drop vehicle photos and keep only proof.

**Pros**: simplest.
**Cons**: loses the arrival record, which is what settles "that dent was already there".

## Rationale

The phone force decides it: Option 2 is the only design with no choice at upload, and the status is a fact the server already holds under the lock, so the label is right and trustworthy by default. The one weakness, a late Before photo, is rare and is handled two ways: the Start work rule (default on) makes forgetting unlikely, and the viewer's Move action fixes the rest without cluttering the strip. Option 3 buys intent at the cost of a tap on every upload, to fix a case the rule already prevents.

Configurability follows the existing pattern instead of inventing one: catalog switches (spec 0012) for the rules, and the existing `ticket.files.remove_any` permission for who may touch protected Before photos, so the Admin gets two levers with no new permission key. The two send and close switches were chosen over one "where" setting, so a garage can require proof at the handoff, at close, or both.

The flag reads the time in the browser because spec 0017's shrink drops metadata before the server sees it. exifr was chosen over a hand written reader because most iPhone photos are HEIC. The flag goes to verifiers only, because showing it to mechanics teaches them what avoids it (a screenshot carries no time). It never blocks, because the time is client supplied and can be forged.

"Send back" was renamed "Return to mechanic": it says what happens with no judgment, and "Added after return" pairs with it. Industry terms ("rework", "failed inspection") were considered and turned down as harsh.

Outsourced moves are left alone: their evidence is the shop's receipt, owned by features 37 and 38.

### Decisions settled in the conversation

- Rules: switches, defaults Start on, Send on, Close off. Before protection: switch on, plus `remove_any`.
- Only `PROOF` (After) photos satisfy the send and close rules; After is photos only.
- Caps: Before 5 (existing), After 10 (new, 1 to 30). A move into a full group is blocked.
- Removal is never blocked by the move rules; rules check only at the move.
- Return to mechanic keeps old proof; new photos are marked.
- Old tickets follow the rules from release.
- No issue picker on upload.
- Flag for the verify right only; exifr in the browser; its Agent Skill search declined.

### Changes from the cross check (2026-11-02, applied on the engineer's pick)

- "Work started" is a stored `workStartedAt`, set once on M3 or M9, not the current status: a release back to Open or Assigned must not turn After photos back into Before or lift the protection. It also replaces an audit scan per list read.
- Before and After share one duplicate pool, so the same file can't sit in both groups and a move can't hit an unhandled unique index error.
- Start work waits for the upload queue, so a photo picked before the start can't land in After and be flagged by mistake.
- The flag uses the verify permission, not the per ticket rule that blocks a mechanic verifying their own ticket, and allows 5 minutes of clock drift.
- The existing `resolutions` and `COSTS_REQUIRED` checks keep winning on the server; the button shows the photo reason first because it can't be fixed in the dialog.
- Considered and turned down: dropping the Move action to simplify. The engineer chose it, and the Start rule alone doesn't cover a mislabel after the start.
