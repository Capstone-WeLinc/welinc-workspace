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

## Update 2026-11-06: refinements after the first build

Seen on the built page at 1280px, the open issue still carried two lines of controls under its checklist, the photos strip opened on its own whenever a photo blocked the next move (two empty groups above the work), and the Details card mixed vehicle, urgency and record fields in one grid of twelve, two of them repeating the title. Agreed with the engineer in chat:

- Issue actions go into a row `⋮` menu, matching the ticket's own `⋮`; the known fix name already sits on the row header, so its separate line goes. One quiet Edit steps stays visible, since editing steps is the common action.
- Hide done steps becomes one switch for the ticket. Per issue switches repeated the same control on every open row, and people hide done steps for the whole job, not one issue at a time.
- The photos line stays folded until a photo exists and names what is missing instead. The Status card's reason link still opens it, so nothing is lost.
- Priority and due date are urgency, so they sit with the status in the Status card; the rest of Details splits into Vehicle and Record, so each group reads at a glance.
- Hierarchy: the issue title one step larger and semibold leads the row; step rows go to 36px on desktop and keep 44px for thumbs on phones.

## Update 2026-11-07: second refinements after the refinements build

Seen on the built page by the engineer: the photos area offered two add buttons (Add photos on the line, Choose photos under the groups) and neither said which group a photo lands in; the summary line carried three controls; and text joined by a dot read as generated, not designed. Decided in conversation, recommended picks taken:

- **Rows stay foldable, no popup.** A popup (Option 2 above) hides the other issues while you work, adds an open and a close per issue, and breaks `#issue-N` links and the per issue progress you scan down the list. Popups suit short focused edits, which is why Edit steps is already a dialog. Shop work order tools keep jobs inline for the same reason. Option 1 holds.
- **Photos become their own card after Issues** (chosen over keeping them inside Issues always open, and over a folded line whose hint is the button). One add tile sits in the group photos land in, so the control itself says where the photo goes, and there is never a second add button. Placing it after Issues follows the work: steps first, then the after photo, and on phones the issues stay first. One row per group with "+N more" keeps the card a fixed height however many photos there are. The tile drops `capture`, so one control reaches both the camera and the gallery through the phone's own picker; this replaces spec 0017's separate Take photo button on this page.
- **Only Hide done steps stays on the summary line** (chosen over moving Expand all and Collapse all into a menu). Each row's header already opens and closes it, the page remembers what was opened, and most tickets carry 1 to 3 issues; a menu would hide two rarely used actions behind an extra tap.
- **No dot separators.** Counts read as sentences with commas, the parts of a row's line 2 are split by space with the known fix labelled ("Known fix: name"), and the overdue text gets its own line. Words and layout carry the structure instead of a symbol.
- **Hover labels** on the status and priority badges and on both `⋮` menus, so a badge or an icon button says what it is. Built during the refinements run (`6e19286`) and recorded here.

Root cause found on the way: the local seed never set `workStartedAt`, so seeded started tickets uploaded every photo into Before. Fixed in the seed (`9e28684` in welinc-backend-vrms), outside this spec.
