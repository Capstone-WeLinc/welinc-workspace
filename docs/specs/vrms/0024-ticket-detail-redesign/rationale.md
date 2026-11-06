# 0024. Rationale: ticket detail page around foldable issue rows

## Context

A repair ticket can hold up to 10 issues (`MAX_ISSUES`), and since spec 0023 each issue can hold up to 20 checklist steps. The detail page shows every issue fully open: the issue text, a bordered known fix box, a large safety callout, every step, typical parts, typical hours and the resolution. On a seeded ticket one issue fills a laptop screen, so a full ticket is a very long scroll on the phones mechanics work from.

The page also drifts from its own design file (`docs/context/vrms/design.md`): the title is the ticket ID instead of the plate and main issue, the sidebar stacks above the issues on phones, Cancel ticket is a full width red button under the main action, and the known fix is a box inside the Issues card. The category shows twice because the stored description keeps a `[System] ` prefix while a badge also shows it.

Typical parts and hours come from the knowledge entry, not from this truck, so on the ticket they read like instructions and can mislead. Verification is per ticket: Send for verification needs "What fixed it" for every issue, and Return to mechanic sends the whole ticket back.

The engineer asked for a page that looks like a well made shop work order: not plain, not decorated, nothing that reads as generated.

## Options considered

### Option 1: Foldable issue rows (accordion) on the existing page

Each issue becomes a row that opens and closes, with progress and a derived state on the closed row. Side sections move to follow the design file. No backend change.

**Pros**:
- Works the same at 375px and 1280px.
- Ticks stay in place; the rest of the ticket stays in view.
- Built on data the page already has.

**Cons**:
- One tap to see a closed issue's steps.
- The open and closed state needs a memory rule so the refresh never fights the user.

### Option 2: Issue popup (a dialog or sheet per issue)

A compact list of issues; tapping one opens it in a dialog, a bottom sheet on phones.

**Pros**:
- The list is always short.
- A focused view of one issue.

**Cons**:
- Open, tick, close for every issue while working.
- Edit steps is already a dialog, so it would stack a dialog on a dialog.
- The verifier cannot compare two issues.

### Option 3: List and detail split

A narrow list of issues on the left and the chosen issue on the right, inside the main column.

**Pros**:
- Fast switching on wide screens.

**Cons**:
- Cramped beside the existing sidebar at 1280px.
- Needs a different phone layout, so two designs to keep in step.

### Option 4: Keep everything open, trim the clutter

Remove parts and hours, shrink the safety box, keep every issue open.

**Pros**:
- Smallest change.

**Cons**:
- Long tickets stay long; it does not solve the 10 by 20 case.

## Rationale

Option 1 fits the job on the floor: a mechanic ticks steps on one issue at a time and needs the next issue and the status close by, which a fold gives and a popup takes away (Option 2). It is the only option that behaves the same on a phone and a laptop without a second layout (Option 3), and it actually solves the long ticket case that Option 4 leaves alone.

The state is derived from ticks (Done means all steps ticked), not a new "mark done" field, because the engineer chose to keep this a web only change and the tick data already exists. Rows open by the ticket's status (first unfinished issue while work is ongoing, all closed once it is with the verifier or finished) because those two stages read the page differently, and status is a fact the page already has where role would need its own rule; the closed row carries "What fixed it" so sign off needs no clicks.

Small calls made in the spec: the shadcn Accordion in `multiple` mode (keyboard and ARIA built in, matching the shadcn setup; runner up, a hand rolled disclosure per row); Edit issue and Remove issue inside the open row (keeps the closed row for reading; runner up, an icon on the header, which brings back clutter); the refresh never opens or closes a row and a new issue starts closed (the user stays in control; runner up, re-running the open rule on each refresh, which would fold rows under someone's thumb); `sessionStorage` per tab (survives the refresh and a reload without surprising someone next week).

The look follows the engineer's brief and the two design files: hierarchy from type, colour only where it carries meaning, and the plate chip as the signature, which reads as considered rather than generated.
